"""Real-time updates from the bridge event stream (SSE /eventstream/clip/v2).

The bridge pushes Server-Sent Events whenever a resource changes (a lamp toggled
from the phone, a scene recalled, etc.). We keep a long-lived connection and emit
Qt signals so the UI updates without polling.
"""

import json

import requests
import urllib3
from PySide6.QtCore import QThread, Signal

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def process_events(events):
    """Split a list of SSE event objects into (light updates, structural change).

    - light updates: resource fragments of type 'light' from 'update' events.
    - structural: True if any 'add' or 'delete' event occurred (needs a reload).
    """
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


class EventStream(QThread):
    updated = Signal(list)   # list of 'light' resource fragments
    changed = Signal()       # structural change (add/delete) -> reload

    def __init__(self, bridge):
        super().__init__()
        self.bridge = bridge
        self._stop = False
        self._resp = None

    def run(self):
        url = self.bridge.base + "/eventstream/clip/v2"
        headers = dict(self.bridge.headers)
        headers["Accept"] = "text/event-stream"
        while not self._stop:
            try:
                self._resp = requests.get(url, headers=headers, stream=True,
                                          verify=False, timeout=(5, 90))
                self._read(self._resp)
            except Exception:  # noqa: BLE001
                pass          # network hiccup / read timeout -> reconnect
            finally:
                self._close()
            if not self._stop:
                self.msleep(1500)   # small backoff before reconnecting

    def _read(self, resp):
        buffer = []
        for raw in resp.iter_lines(decode_unicode=True):
            if self._stop:
                return
            line = raw if raw is not None else ""
            if line == "":                     # blank line ends an SSE block
                if buffer:
                    self._dispatch("\n".join(buffer))
                    buffer = []
                continue
            if line.startswith(":"):           # comment / keep-alive
                continue
            if line.startswith("data:"):
                buffer.append(line[5:].lstrip())
            # other fields (id:, event:) are ignored

    def _dispatch(self, payload):
        try:
            events = json.loads(payload)
        except ValueError:
            return
        lights, structural = process_events(events)
        if lights:
            self.updated.emit(lights)
        if structural:
            self.changed.emit()

    def _close(self):
        try:
            if self._resp is not None:
                self._resp.close()
        except Exception:  # noqa: BLE001
            pass
        self._resp = None

    def stop(self):
        self._stop = True
        self._close()
