# Lumen

Desktop control for **Philips Hue** lights, built for Linux/Wayland (Hyprland,
but it runs anywhere Qt runs). Everything goes through the bridge's **local API**
(CLIP v2): no cloud, and no dependency on the mobile app once paired.

Three commands sharing the same configuration:

- **`hue-gui`** - graphical app (PySide6) with a system-tray icon.
- **`hue`** - command-line client, ideal for keyboard shortcuts.
- **`hue-sync`** - screen sync (ambilight) without the GUI.

## Features

- Bridge pairing directly in the app (auto-detection + button).
- Rooms and zones as cards: group control (on/off + brightness).
- Light tiles with the **background set to the light's real color**, an icon
  per device type (strip, spot, ceiling, table...), and a toggle. Clicking a
  tile opens color + brightness controls.
- Scenes **grouped by room/zone**, with a thumbnail generated from the scene's
  real colors. Create, edit and delete scenes (captures the current light state).
- Create, edit and delete **rooms and zones**, from one editor. A room holds
  devices and mirrors your physical setup (a lamp lives in exactly one room); a
  zone holds individual lights and zones may overlap. Every card is badged
  `ROOM` or `ZONE` so the two never get confused.
- **Screen sync / ambilight** - see below.
- **Real-time updates**: the UI reflects changes made elsewhere (phone, wall
  switch, another app) live, via the bridge event stream (SSE).
- Adjustable number of columns (1 to 8), **multilingual** UI (English default,
  French available), optional start-minimized.
- Bridge settings: change the IP, re-pair, disconnect.

## Screen sync (ambilight)

Lumen averages regions of your screen and streams them to the lamps over the
Hue **Entertainment** API, at up to 50 frames per second.

Create an Entertainment area in the official Hue app first, then press **Sync**
in the toolbar (or run `hue-sync`). Each channel's horizontal position in that
area is mapped onto the matching slice of the screen, so left lamps follow the
left of the picture.

Screen capture drives a **system binary** rather than a Python binding, and the
first backend that works is used:

| Backend | Needs | Notes |
|---|---|---|
| `wlroots` | `wf-recorder` | Hyprland, Sway. Fastest, never prompts. |
| `portal` | `gst-launch-1.0` (gst-plugin-pipewire), `pw-dump` | Universal: GNOME, KDE, wlroots. Asks which screen on every start. |
| `x11` | `ffmpeg` | Plain X11 sessions. |

Settings hold the screen to capture, a **color boost** (screen averages are
washed out; lamps need the push) and the frame rate. Screen and color boost
apply to a running sync; changing the frame rate needs a stop and start.

Pairing must have produced a `client_key` - it is the DTLS secret. Configs from
older versions may lack it, in which case re-pair once.

## Installation

Requires Python >= 3.10.

```bash
# from the project directory
pipx install .            # recommended (isolated environment)
# or
pip install --user .
```

This installs `hue`, `hue-gui` and `hue-sync`.

On Arch/CachyOS you can install Qt from the system instead of via pip:

```bash
sudo pacman -S pyside6 python-requests
python -m huectl          # run the GUI without installing the package
```

Screen sync needs `openssl` (already present on most systems) plus one capture
backend from the table above:

```bash
# Hyprland / Sway
sudo pacman -S wf-recorder
# any other compositor, through the desktop portal
sudo pacman -S gstreamer gst-plugin-pipewire pipewire-utils xdg-desktop-portal
```

### Launcher / autostart

Copy `packaging/lumen.desktop` into `~/.local/share/applications/`.
To start minimized to the tray at session login (Hyprland):

```
exec-once = hue-gui --tray
```

> The tray icon requires a tray host (Waybar's `tray` module, or your shell's
> systray). Without a host, the window simply stays visible.

## First run

```bash
hue-gui
```

On first run the pairing screen detects the bridge (or enter its IP), you press
the bridge button, then click "Pair". Keys are stored in
`~/.config/huectl/config.json` (chmod 600).

## CLI

```bash
hue discover                 # find the bridge
hue auth                     # press the bridge button
hue lights                   # list lamps
hue rooms                    # rooms and zones
hue scenes                   # scenes
hue on "Living room"         # turn a room/zone on
hue toggle "Left lamp"       # toggle a lamp
hue bri "Living room" 60     # brightness 0-100
hue bri "Living room" +10    # relative
hue color "Lamp" #ff3300     # color
hue ct "Living room" warm    # warm white (or 3000, neutral, cool)
hue scene "Relax"            # activate a scene
hue raw GET /clip/v2/resource/light   # raw API access
```

Screen sync from the terminal:

```bash
hue-sync --list              # list Entertainment areas
hue-sync                     # ambilight from the screen
hue-sync --output DP-2       # capture one monitor
hue-sync --saturation 2.0    # stronger colors
hue-sync --test              # rainbow pattern, to check the pipeline
```

Example Hyprland shortcuts:

```
bind = $mod, F1, exec, hue toggle "Living room"
bind = $mod, F2, exec, hue scene "Relax"
bind = $mod SHIFT, F1, exec, hue bri "Living room" +15
```

## Project layout

```
huectl/
  config.py        config load/save
  bridge.py        CLIP v2 HTTP client + discovery
  color.py         xy/mirek conversions, scene colors
  icons.py         drawn icons (light types, toolbar), gradients
  i18n.py          English/French strings
  theme.py         Qt theme
  workers.py       network threads (snapshot, pairing)
  sse.py           real-time event stream (SSE)
  widgets.py       toggle switch, scene/light tiles
  dialogs.py       light control, scene and room/zone editors
  window.py        main window
  setup_window.py  pairing screen
  app.py           orchestration + system tray (GUI entry point)
  cli.py           command-line interface
  huestream.py     HueStream v2 frame protocol
  entertainment.py Entertainment configurations and channels
  dtls_stream.py   DTLS-PSK transport over the system openssl
  capture.py       screen capture backends, region averaging
  portal.py        xdg-desktop-portal ScreenCast (universal capture)
  sync.py          color sources, channel mapping, hue-sync entry point
```

## Technical notes

- The bridge exposes its API over HTTPS with a self-signed certificate
  (`verify=False`); authentication uses the `hue-application-key` header.
- Colors are converted in sRGB both ways (RGB<->xy) to stay faithful to the
  picked color.
- No Unicode symbol glyphs in the interface. Minimal font setups lack characters
  like the ellipsis or gear and render them as nothing, so every icon is drawn
  with `QPainter` and every critical action also carries a text label.
- The Philips mobile app's real product photos are not available through the
  bridge; Lumen uses tinted vector illustrations instead.
- DTLS-PSK for Entertainment uses the system `openssl` binary, not a Python DTLS
  binding (`python-mbedtls` is unmaintained and does not build against
  Mbed TLS 3.x).
- Screen capture never grabs one frame at a time: a `grim` call costs about
  120 ms whatever the resolution, which caps it near 8 fps. Continuous streams
  are used instead, and only the newest frame is kept so the lamps cannot drift
  behind the screen.
- The portal backend asks which screen to share on every start. Suppressing that
  needs the portal's `persist_mode` option, which PySide6 cannot send: it
  marshals Python integers as `i` where the portal requires `u`.
- The `x11` capture backend is written but has not been exercised on a real X11
  session.

## Ideas for later

- Pick the Entertainment area from the GUI (the first one is used today).
- Per-channel vertical mapping, using the height of each lamp rather than a
  full-height average.

## License

GNU General Public License v3.0 or later (GPL-3.0-or-later). See `LICENSE`.
