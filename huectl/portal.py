"""Universal screen capture through xdg-desktop-portal ScreenCast.

This is the backend that works everywhere - GNOME, KDE, wlroots - unlike the
compositor-specific binaries in capture.py. The portal hands out a PipeWire
node, and `gst-launch-1.0 pipewiresrc` turns it into the same raw RGB pipe every
other backend produces.

D-Bus goes through PySide6's QtDBus, already a dependency, rather than adding a
D-Bus package. Two PySide6 quirks shape the code below:

  - QDBusMessage.arguments() hands back an opaque QDBusArgument for a{sv} and
    its asVariant() is broken (shiboken cannot convert the VoidPtr). Declaring
    the Response slot as (uint, QVariantMap) makes Qt demarshal for us instead.
  - PySide6 marshals Python ints as 'i', and the portal insists on 'u' for its
    integer options, with no way to build a typed variant. Every uint option is
    therefore omitted; the defaults (types=MONITOR, cursor_mode=HIDDEN) are what
    we want anyway.
    # no persist_mode, so the portal asks which screen on every start.
    # Fix needs typed-variant marshalling: a real D-Bus lib (jeepney is pure
    # Python) or PySide exposing QVariant with an explicit metatype.
"""

import json
import os
import shutil
import subprocess
import sys

from PySide6.QtCore import QCoreApplication, QEventLoop, QObject, QTimer, Slot
from PySide6.QtDBus import (QDBusConnection, QDBusInterface, QDBusMessage,
                            QDBusObjectPath)

from . import capture

BUS = "org.freedesktop.portal.Desktop"
PATH = "/org/freedesktop/portal/desktop"
SCREENCAST = "org.freedesktop.portal.ScreenCast"

_app = None          # QCoreApplication must outlive every D-Bus call


def _ensure_app():
    global _app
    if QCoreApplication.instance() is None:
        _app = QCoreApplication(sys.argv or ["lumen"])
    return QCoreApplication.instance()


class _Response(QObject):
    """Catches one org.freedesktop.portal.Request.Response signal."""

    def __init__(self):
        super().__init__()
        self.code = None
        self.results = None
        self.loop = QEventLoop()

    @Slot("uint", "QVariantMap")
    def handle(self, code, results):
        self.code, self.results = int(code), dict(results)
        self.loop.quit()


class PortalSession:
    """A ScreenCast session: create, select sources, start, open the remote."""

    def __init__(self, timeout_ms=120000):
        _ensure_app()
        self.timeout_ms = timeout_ms
        self.conn = QDBusConnection.sessionBus()
        if not self.conn.isConnected():
            raise capture.CaptureError("no D-Bus session bus")
        self.iface = QDBusInterface(BUS, PATH, SCREENCAST, self.conn)
        if not self.iface.isValid():
            raise capture.CaptureError("xdg-desktop-portal is not running")
        self.handle = None

    def _await(self, request_path):
        r = _Response()
        if not self.conn.connect(BUS, request_path,
                                 "org.freedesktop.portal.Request", "Response",
                                 r, "1handle(uint,QVariantMap)"):
            raise capture.CaptureError("cannot subscribe to the portal reply")
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(r.loop.quit)
        timer.start(self.timeout_ms)
        r.loop.exec()
        if r.code is None:
            raise capture.CaptureError("the portal did not answer in time")
        if r.code != 0:                  # 1 = user cancelled, 2 = failed
            raise capture.CaptureError(
                "screen capture was refused" if r.code == 1
                else "the portal failed to start screen capture")
        return r.results

    def _request(self, method, *args):
        reply = self.iface.call(method, *args)
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            raise capture.CaptureError(
                f"{method}: {reply.errorName()}: {reply.errorMessage()}")
        return self._await(reply.arguments()[0].path())

    def start(self):
        """Run the handshake. Returns (node_id, pipewire_fd)."""
        res = self._request("CreateSession",
                            {"handle_token": "lumen",
                             "session_handle_token": "lumensession"})
        # handed back as a plain string, wanted as an object path everywhere else
        self.handle = QDBusObjectPath(res["session_handle"])
        self._request("SelectSources", self.handle, {"multiple": False})
        res = self._request("Start", self.handle, "", {"handle_token": "lumenstart"})

        node_id = _node_from_streams(res.get("streams"))
        reply = self.iface.call("OpenPipeWireRemote", self.handle, {})
        if reply.type() == QDBusMessage.MessageType.ErrorMessage:
            raise capture.CaptureError(
                f"OpenPipeWireRemote: {reply.errorMessage()}")
        ufd = reply.arguments()[0]
        raw = ufd.fileDescriptor() if hasattr(ufd, "fileDescriptor") else int(ufd)
        if raw < 0:
            raise capture.CaptureError("the portal returned no PipeWire socket")
        # QDBusUnixFileDescriptor owns its fd and closes it when collected, which
        # can happen before the capture process is spawned. Keep our own copy.
        fd = os.dup(raw)
        if node_id is None:
            node_id = _node_from_pipewire()
        return node_id, fd

    def close(self):
        if self.handle is None:
            return
        session = QDBusInterface(BUS, self.handle.path(),
                                 "org.freedesktop.portal.Session", self.conn)
        if session.isValid():
            session.call("Close")
        self.handle = None


def _node_from_streams(streams):
    """Node id out of the Start response, if PySide6 managed to demarshal it.

    'streams' is a(ua{sv}) - an array of structs - which PySide6 usually leaves
    as an opaque QDBusArgument. Returns None when that happens, so the caller
    can ask PipeWire directly.
    """
    if not isinstance(streams, (list, tuple)) or not streams:
        return None
    first = streams[0]
    try:
        return int(first[0])
    except (TypeError, ValueError, IndexError):
        return None


def _node_from_pipewire():
    """Ask PipeWire which video source the portal just published.

    Fallback for when the Start response cannot be demarshalled. The portal node
    is the most recently created Video/Source, so the highest id wins.
    """
    if not shutil.which("pw-dump"):
        raise capture.CaptureError(
            "cannot read the PipeWire node id from the portal reply, and "
            "pw-dump is not installed to look it up")
    try:
        out = subprocess.run(["pw-dump"], capture_output=True, text=True,
                             timeout=10).stdout
        objects = json.loads(out or "[]")
    except (subprocess.SubprocessError, ValueError) as e:
        raise capture.CaptureError(f"pw-dump failed: {e}") from e
    ids = [o["id"] for o in objects
           if ((o.get("info") or {}).get("props") or {}).get("media.class")
           == "Video/Source"]
    if not ids:
        raise capture.CaptureError("no PipeWire video source to capture")
    return max(ids)


class _PortalStream(capture.FrameStream):
    """FrameStream that also tears down the portal session and the socket."""

    def __init__(self, *args, session=None, fd=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._session = session
        self._fd = fd

    def close(self):
        super().close()
        if self._session is not None:
            self._session.close()
            self._session = None
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None


def open_portal_stream(output=None, fps=30,
                       width=capture.CAPTURE_W, height=capture.CAPTURE_H):
    """Negotiate with the portal and return a started FrameStream.

    `output` is ignored: which monitor gets shared is the user's choice in the
    portal dialog, not ours.
    """
    if not shutil.which("gst-launch-1.0"):
        raise capture.CaptureError(
            "gst-launch-1.0 is needed for portal capture "
            "(install gstreamer and gst-plugins-base)")
    session = PortalSession()
    try:
        node_id, fd = session.start()
    except Exception:
        session.close()
        raise

    src = f"pipewiresrc fd={fd}" + (f" path={node_id}" if node_id else "")
    cmd = ["gst-launch-1.0", "-q", *src.split(),
           "!", "videoconvert", "!", "videoscale", "!",
           f"video/x-raw,format=RGB,width={width},height={height}", "!",
           "fdsink", "fd=1"]
    stream = _PortalStream(cmd, width, height, 3, pass_fds=(fd,),
                           session=session, fd=fd)
    try:
        stream.start()
        stream.latest(timeout=8.0)
        return stream
    except Exception:
        stream.close()
        raise
