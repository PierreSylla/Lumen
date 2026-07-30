"""Screen-sync orchestrator (Entertainment streaming over DTLS).

This wires the pieces together: set the entertainment configuration to 'start',
open the DTLS stream, then push frames at a fixed frame rate from a color source.

A ColorSource yields one (r, g, b) per channel. Two are provided:
  - TestColorSource: a moving rainbow, to validate the pipeline end to end.
  - (screen capture on Wayland is the next increment; see WaylandCapture stub.)

CLI:
    hue-sync --list            list entertainment configurations
    hue-sync                   stream the test pattern to the first config
    hue-sync --config <id>     choose a configuration
    hue-sync --fps 40          frame rate (default 50)
"""

import sys
import time
import math
import argparse
import colorsys

from .config import load_config
from .bridge import Bridge
from . import entertainment, huestream
from .dtls_stream import HueDTLS


class ColorSource:
    def sample(self, n):
        """Return a list of n (r, g, b) tuples, 8-bit."""
        raise NotImplementedError

    def close(self):
        pass


class TestColorSource(ColorSource):
    """Moving rainbow across channels - proves the whole path lights up."""

    def __init__(self, speed=0.15):
        self.speed = speed
        self._t0 = time.monotonic()

    def sample(self, n):
        t = (time.monotonic() - self._t0) * self.speed
        out = []
        for i in range(max(1, n)):
            hue = (t + i / max(1, n)) % 1.0
            r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
            out.append((int(r * 255), int(g * 255), int(b * 255)))
        return out[:n]


class WaylandCapture(ColorSource):
    """Screen capture on Wayland (PipeWire / xdg-desktop-portal). Not yet done."""

    def sample(self, n):
        raise NotImplementedError(
            "Wayland screen capture is not implemented yet - use the test source.")


def run_stream(source, config_id=None, fps=50, should_run=None):
    """Start streaming until should_run() returns False (or Ctrl-C).

    should_run: optional callable returning True while streaming should continue.
    Returns None. Raises on setup errors (no config, missing key, etc.).
    """
    cfg = load_config()
    ip, app_key = cfg.get("bridge_ip"), cfg.get("app_key")
    client_key = cfg.get("client_key")
    if not ip or not app_key:
        raise RuntimeError("bridge not paired - run the app or `hue auth` first")
    if not client_key:
        raise RuntimeError("no client_key in config - re-pair the bridge "
                           "(it is created at pairing and needed for streaming)")

    bridge = Bridge(ip, app_key)
    config = entertainment.pick_config(bridge, config_id)
    if config is None:
        raise RuntimeError("no entertainment area found - create one in the "
                           "official Hue app first")
    channels = entertainment.channel_ids(config)
    if not channels:
        raise RuntimeError("the entertainment area has no channels")

    entertainment.start(bridge, config["id"])
    dtls = HueDTLS(ip, app_key, client_key)
    period = 1.0 / max(1, fps)
    seq = 0
    try:
        dtls.connect()
        while should_run is None or should_run():
            colors = source.sample(len(channels))
            frame = huestream.build_rgb_frame(config["id"], zip(channels, colors), seq)
            dtls.send(frame)
            seq = (seq + 1) & 0xFF
            time.sleep(period)
    finally:
        dtls.close()
        source.close()
        try:
            entertainment.stop(bridge, config["id"])
        except Exception:  # noqa: BLE001
            pass


def _list_configs():
    cfg = load_config()
    if not cfg.get("bridge_ip") or not cfg.get("app_key"):
        print("bridge not paired.", file=sys.stderr)
        return 1
    bridge = Bridge(cfg["bridge_ip"], cfg["app_key"])
    configs = entertainment.list_configs(bridge)
    if not configs:
        print("no entertainment area - create one in the Hue app.")
        return 0
    for c in configs:
        print(f"{c['id']}  {entertainment.config_name(c):<24} "
              f"{entertainment.channel_count(c)} channels")
    return 0


def main():
    p = argparse.ArgumentParser(prog="hue-sync",
                                description="Philips Hue screen sync (Entertainment)")
    p.add_argument("--list", action="store_true", help="list entertainment areas")
    p.add_argument("--config", help="entertainment configuration id")
    p.add_argument("--fps", type=int, default=50, help="frame rate (default 50)")
    args = p.parse_args()

    if args.list:
        return _list_configs()

    try:
        print("Streaming test pattern - press Ctrl-C to stop.")
        run_stream(TestColorSource(), config_id=args.config, fps=args.fps)
    except KeyboardInterrupt:
        print("\nstopped.")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
