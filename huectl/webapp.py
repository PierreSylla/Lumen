"""Vue web UI entry point: pywebview shell around webui/dist.

Backend GUI (huectl/window.py, PySide6) stays untouched and launchable via
hue-gui until the web UI reaches parity (see CLAUDE.md / handoff.md).
"""

import json
import os
import sys
import threading
import time
from pathlib import Path

import requests
import urllib3

# WebKitGTK's DMABUF renderer crashes on load (Wayland protocol error) on
# hybrid Intel+NVIDIA setups under Hyprland - confirmed on the dev machine.
# Must be set before `webview` (and the GTK/WebKit libs it loads) import.
os.environ.setdefault("WEBKIT_DISABLE_DMABUF_RENDERER", "1")

import webview  # noqa: E402

from .bridge import discover_bridge_ip, load_bridge  # noqa: E402
from .config import CONFIG_PATH, APP_NAME, load_config, save_config  # noqa: E402

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DIST_INDEX = Path(__file__).resolve().parent.parent / "webui" / "dist" / "index.html"

# Set by `npm run dev` workflow to point at the Vite dev server for hot-reload
# instead of the built dist/, e.g. LUMEN_WEBUI_DEV_URL=http://localhost:5173
DEV_SERVER_URL = os.environ.get("LUMEN_WEBUI_DEV_URL")


class Api:
    """Methods exposed to the Vue app as window.pywebview.api.*"""

    def __init__(self):
        self._pair_state = {"status": "idle"}
        self._pair_lock = threading.Lock()

    def ping(self):
        return "pong"

    def get_config(self):
        """Sanitized config for the Setup page - never the secrets themselves."""
        cfg = load_config()
        return {
            "bridge_ip": cfg.get("bridge_ip"),
            "has_client_key": bool(cfg.get("client_key")),
            "columns": cfg.get("columns", 2),
            "language": cfg.get("language", "en"),
            "start_minimized": cfg.get("start_minimized", False),
        }

    def save_settings(self, patch):
        allowed = {"columns", "language", "start_minimized"}
        save_config({k: v for k, v in patch.items() if k in allowed})
        return {"ok": True}

    def set_bridge_ip(self, ip):
        """Change IP only - same physical bridge, keeps app_key/client_key
        (matches huectl/app.py's set_ip: a DHCP lease change, not a re-pair)."""
        save_config({"bridge_ip": ip})
        return {"ok": True}

    def disconnect(self):
        try:
            os.remove(CONFIG_PATH)
        except OSError:
            pass
        return {"ok": True}

    def discover_bridge(self):
        try:
            return {"ip": discover_bridge_ip()}
        except Exception as e:
            return {"error": str(e)}

    def start_pairing(self, ip):
        """Kicks off a background poll loop (mirrors huectl/workers.py's
        PairTask) and returns immediately; the Vue side polls pair_status()
        once a second for the live countdown, since a js_api call is a
        request/response round trip, not a stream."""
        with self._pair_lock:
            if self._pair_state.get("status") == "waiting":
                return {"error": "already_pairing"}
            self._pair_state = {"status": "waiting", "seconds_left": 30}
        threading.Thread(target=self._pair_worker, args=(ip,), daemon=True).start()
        return {"ok": True}

    def _pair_worker(self, ip):
        payload = {"devicetype": APP_NAME, "generateclientkey": True}
        for i in range(30):
            try:
                r = requests.post(f"https://{ip}/api", json=payload, verify=False, timeout=5)
                res = r.json()
            except Exception as e:
                with self._pair_lock:
                    self._pair_state = {"status": "error", "message": str(e)}
                return
            if isinstance(res, list) and res:
                item = res[0]
                if "success" in item:
                    s = item["success"]
                    cfg = {"bridge_ip": ip, "app_key": s["username"], "client_key": s.get("clientkey")}
                    save_config(cfg)
                    with self._pair_lock:
                        self._pair_state = {"status": "success"}
                    return
                err = item.get("error", {})
                if str(err.get("type")) != "101":  # 101 = button not pressed yet
                    with self._pair_lock:
                        self._pair_state = {"status": "error", "message": err.get("description", "?")}
                    return
            with self._pair_lock:
                self._pair_state = {"status": "waiting", "seconds_left": 30 - i - 1}
            time.sleep(1)
        with self._pair_lock:
            self._pair_state = {"status": "error", "message": "Timed out waiting for the button press."}

    def pair_status(self):
        with self._pair_lock:
            return dict(self._pair_state)

    def get_snapshot(self):
        """Read-only bridge snapshot for the Vue store. Runs on pywebview's
        own worker thread (js_api calls are already off the UI thread), so no
        extra Task/QThread wrapping is needed here unlike the PySide6 GUI."""
        bridge = load_bridge()
        if bridge is None:
            return {"error": "not_configured"}
        try:
            return {"data": bridge.snapshot()}
        except Exception as e:
            return {"error": str(e)}

    def _write(self, fn):
        bridge = load_bridge()
        if bridge is None:
            return {"error": "not_configured"}
        try:
            fn(bridge)
            return {"ok": True}
        except Exception as e:
            return {"error": str(e)}

    def put_light(self, light_id, payload):
        """payload is a raw CLIP v2 body, e.g. {"on": {"on": true}} or
        {"color": {"xy": {"x": ..., "y": ...}}} - the Vue store builds it."""
        return self._write(lambda b: b.put("light", light_id, payload))

    def put_grouped_light(self, grouped_light_id, payload):
        return self._write(lambda b: b.put("grouped_light", grouped_light_id, payload))

    def recall_scene(self, scene_id):
        return self._write(lambda b: b.put("scene", scene_id, {"recall": {"action": "active"}}))


def _process_events(events):
    """Mirrors huectl/sse.py's process_events - duplicated rather than
    imported so hue-webui doesn't pull PySide6 into a Qt-less process just
    for this pure-Python parsing (sse.py's EventStream subclasses QThread)."""
    light_updates = []
    structural = False
    for ev in events:
        etype = ev.get("type")
        data = ev.get("data", [])
        if etype in ("add", "delete"):
            structural = True
        if etype == "update":
            for res in data:
                if res.get("type") == "light":
                    light_updates.append(res)
    return light_updates, structural


class WebSSE(threading.Thread):
    """Bridge event stream (SSE) for the web UI. Same protocol handling as
    huectl/sse.py's EventStream, as a plain daemon thread calling plain
    callbacks instead of a QThread emitting Qt signals - this process has no
    Qt event loop.

    Re-reads load_bridge() on every reconnect attempt instead of binding to a
    fixed Bridge at construction time, so it survives (and picks up) a
    disconnect/re-pair/change-IP happening in the same running process - the
    Setup page's job, this step - without needing to be torn down and
    recreated."""

    def __init__(self, on_update, on_change):
        super().__init__(daemon=True)
        self.on_update = on_update
        self.on_change = on_change
        self._stop = False
        self._resp = None

    def run(self):
        while not self._stop:
            bridge = load_bridge()
            if bridge is None:
                time.sleep(1.5)
                continue
            url = bridge.base + "/eventstream/clip/v2"
            headers = dict(bridge.headers)
            headers["Accept"] = "text/event-stream"
            try:
                self._resp = requests.get(url, headers=headers, stream=True, verify=False, timeout=(5, 90))
                self._read(self._resp)
            except Exception:
                pass  # network hiccup / read timeout -> reconnect
            finally:
                self._close()
            if not self._stop:
                time.sleep(1.5)  # small backoff before reconnecting

    def _read(self, resp):
        buffer = []
        for raw in resp.iter_lines(decode_unicode=True):
            if self._stop:
                return
            line = raw if raw is not None else ""
            if line == "":  # blank line ends an SSE block
                if buffer:
                    self._dispatch("\n".join(buffer))
                    buffer = []
                continue
            if line.startswith(":"):  # comment / keep-alive
                continue
            if line.startswith("data:"):
                buffer.append(line[5:].lstrip())

    def _dispatch(self, payload):
        try:
            events = json.loads(payload)
        except ValueError:
            return
        lights, structural = _process_events(events)
        if lights:
            self.on_update(lights)
        if structural:
            self.on_change()

    def _close(self):
        try:
            if self._resp is not None:
                self._resp.close()
        except Exception:
            pass
        self._resp = None

    def stop(self):
        self._stop = True
        self._close()


def _push(window, payload):
    window.evaluate_js(f"window.__lumenSSE && window.__lumenSSE({json.dumps(payload)})")


def _start_sse(window):
    """Runs in a background thread once the window is ready (webview.start's
    func/args). One WebSSE for the whole process lifetime: it idles (and
    retries) whenever there's no bridge configured yet, so this starts
    correctly even before first-run pairing completes."""
    WebSSE(
        on_update=lambda lights: _push(window, {"type": "update", "lights": lights}),
        on_change=lambda: _push(window, {"type": "change"}),
    ).start()


def main():
    url = DEV_SERVER_URL or str(DIST_INDEX)
    if not DEV_SERVER_URL and not DIST_INDEX.exists():
        sys.exit(
            f"{DIST_INDEX} not found - run `npm run build` in webui/, "
            "or set LUMEN_WEBUI_DEV_URL to a running `npm run dev` server."
        )
    window = webview.create_window("Lumen", url, width=560, height=720, js_api=Api())
    webview.start(_start_sse, (window,))


if __name__ == "__main__":
    main()
