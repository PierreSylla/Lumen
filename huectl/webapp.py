"""Vue web UI entry point: pywebview shell around webui/dist.

Backend GUI (huectl/window.py, PySide6) stays untouched and launchable via
hue-gui until the web UI reaches parity (see CLAUDE.md / handoff.md).
"""

import os
import sys
from pathlib import Path

# WebKitGTK's DMABUF renderer crashes on load (Wayland protocol error) on
# hybrid Intel+NVIDIA setups under Hyprland - confirmed on the dev machine.
# Must be set before `webview` (and the GTK/WebKit libs it loads) import.
os.environ.setdefault("WEBKIT_DISABLE_DMABUF_RENDERER", "1")

import webview  # noqa: E402

from .bridge import load_bridge  # noqa: E402

DIST_INDEX = Path(__file__).resolve().parent.parent / "webui" / "dist" / "index.html"

# Set by `npm run dev` workflow to point at the Vite dev server for hot-reload
# instead of the built dist/, e.g. LUMEN_WEBUI_DEV_URL=http://localhost:5173
DEV_SERVER_URL = os.environ.get("LUMEN_WEBUI_DEV_URL")


class Api:
    """Methods exposed to the Vue app as window.pywebview.api.*"""

    def ping(self):
        return "pong"

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


def main():
    url = DEV_SERVER_URL or str(DIST_INDEX)
    if not DEV_SERVER_URL and not DIST_INDEX.exists():
        sys.exit(
            f"{DIST_INDEX} not found - run `npm run build` in webui/, "
            "or set LUMEN_WEBUI_DEV_URL to a running `npm run dev` server."
        )
    webview.create_window("Lumen", url, width=560, height=720, js_api=Api())
    webview.start()


if __name__ == "__main__":
    main()
