"""Screen-sync orchestrator (Entertainment streaming over DTLS).

This wires the pieces together: set the entertainment configuration to 'start',
open the DTLS stream, then push frames at a fixed frame rate from a color source.

A ColorSource yields one (r, g, b) per channel. Two are provided:
  - TestColorSource: a moving rainbow, to validate the pipeline end to end.
  - ScreenCapture: real ambilight, averaging screen regions mapped onto the
    Entertainment channel positions (see capture.py for the backends).

CLI:
    hue-sync --list            list entertainment configurations
    hue-sync                   ambilight from the screen
    hue-sync --test            stream the rainbow test pattern instead
    hue-sync --config <id>     choose a configuration
    hue-sync --output DP-2     capture one monitor rather than the desktop
    hue-sync --fps 40          frame rate (default 50)
"""

import sys
import time
import math
import argparse
import colorsys

from .config import load_config
from .bridge import Bridge
from . import capture, entertainment, huestream
from .dtls_stream import HueDTLS


class ColorSource:
    def configure(self, config):
        """Called once with the entertainment configuration before streaming.

        Sources that map channels onto something (the screen, say) need the
        channel positions, which only run_stream knows.
        """

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


def channel_regions(config, width, height, band=0.4):
    """Screen box each Entertainment channel should follow, ordered by channel id.

    A channel's x (-1 left .. +1 right) maps straight onto a horizontal slice of
    the screen, which is exactly what ambilight needs. y (depth) and z (height)
    are ignored on purpose: most areas leave them flat, and guessing a vertical
    split out of them looks worse than averaging the full height.

    band is the fraction of screen width each channel averages, so neighbouring
    lamps overlap slightly instead of showing hard seams.
    """
    regions = []
    half = band / 2.0
    for cid, x, _y, _z in entertainment.channel_positions(config):
        centre = (x + 1.0) / 2.0
        x0 = int(round(max(0.0, centre - half) * width))
        x1 = int(round(min(1.0, centre + half) * width))
        if x1 <= x0:                      # never hand back an empty box
            x0 = min(x0, width - 1)
            x1 = x0 + 1
        regions.append((cid, (x0, 0, x1, height)))
    return regions


class ScreenCapture(ColorSource):
    """Averages screen regions, one per Entertainment channel.

    The capture backend is picked at first sample so constructing this is cheap
    and cannot fail; a missing binary or a refused portal surfaces when
    streaming actually starts.
    """

    def __init__(self, regions=None, backend=None, output=None, fps=30,
                 saturation=1.6, gamma=1.0,
                 width=capture.CAPTURE_W, height=capture.CAPTURE_H):
        self.regions = regions or []
        self.backend = backend
        self.output = output
        self.fps = fps
        self.saturation = saturation
        self.gamma = gamma
        self.width, self.height = width, height
        self._stream = None
        self._opened_for = None

    def configure(self, config):
        if not self.regions:
            self.regions = channel_regions(config, self.width, self.height)

    def set_output(self, output):
        """Retarget the capture while streaming.

        Only records the wish - a plain attribute write, so the UI thread never
        blocks. The sampling thread owns the capture process and swaps it on its
        next frame, which keeps the Hue stream up and the lamps from blinking.
        """
        self.output = output

    def _open(self):
        if self._stream is not None and self._opened_for != self.output:
            self._stream.close()
            self._stream = None
        if self._stream is None:
            self._opened_for = self.output
            self._stream = capture.open_stream(
                self.backend, self._opened_for, self.fps, self.width, self.height)
        return self._stream

    def sample(self, n):
        stream = self._open()
        buf = stream.latest()
        out = [capture.punch(
                   capture.region_average(buf, self.width, stream.bpp, box),
                   self.saturation, self.gamma)
               for _cid, box in self.regions[:n]]
        while len(out) < n:               # more channels than mapped regions
            out.append(out[-1] if out else (0, 0, 0))
        return out

    def close(self):
        if self._stream is not None:
            self._stream.close()
            self._stream = None
        self._opened_for = None


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

    source.configure(config)
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
    p.add_argument("--test", action="store_true",
                   help="stream the rainbow test pattern instead of the screen")
    p.add_argument("--output", help="monitor to capture (e.g. DP-2)")
    p.add_argument("--backend", choices=sorted(capture.BACKENDS) + ["portal"],
                   help="force a capture backend")
    p.add_argument("--saturation", type=float, default=1.6,
                   help="color boost, screen averages look washed out (default 1.6)")
    p.add_argument("--gamma", type=float, default=1.0,
                   help="above 1 darkens dim scenes (default 1.0)")
    args = p.parse_args()

    if args.list:
        return _list_configs()

    try:
        if args.test:
            print("Streaming test pattern - press Ctrl-C to stop.")
            source = TestColorSource()
        else:
            print("Ambilight from the screen - press Ctrl-C to stop.")
            source = ScreenCapture(backend=args.backend, output=args.output,
                                   fps=args.fps, saturation=args.saturation,
                                   gamma=args.gamma)
        run_stream(source, config_id=args.config, fps=args.fps)
    except KeyboardInterrupt:
        print("\nstopped.")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
