# Lumen

Desktop control for **Philips Hue** lights, built for Linux/Wayland (Hyprland,
but it runs anywhere Qt runs). Everything goes through the bridge's **local API**
(CLIP v2): no cloud, and no dependency on the mobile app once paired.

Two interfaces sharing the same configuration:

- **`hue-gui`** - graphical app (PySide6) with a system-tray icon.
- **`hue`** - command-line client, ideal for keyboard shortcuts.

## Features

- Bridge pairing directly in the app (auto-detection + button).
- Rooms and zones as cards: group control (on/off + brightness).
- Light tiles with the **background set to the light's real color**, an icon
  per device type (strip, spot, ceiling, table...), and a toggle. Clicking a
  tile opens color + brightness controls.
- Scenes **grouped by room/zone**, with a thumbnail generated from the scene's
  real colors. Create, edit and delete scenes (captures the current light state).
- Create, edit and delete **zones**.
- **Real-time updates**: the UI reflects changes made elsewhere (phone, wall
  switch, another app) live, via the bridge event stream (SSE).
- Adjustable number of columns (1 to 8), **multilingual** UI (English default,
  French available), optional start-minimized.
- Bridge settings: change the IP, re-pair, disconnect.

## Installation

Requires Python >= 3.10.

```bash
# from the project directory
pipx install .            # recommended (isolated environment)
# or
pip install --user .
```

This installs two commands: `hue` and `hue-gui`.

On Arch/CachyOS you can install Qt from the system instead of via pip:

```bash
sudo pacman -S pyside6 python-requests
python -m huectl          # run the GUI without installing the package
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
  icons.py         light-type icons, gradients
  i18n.py          English/French strings
  theme.py         Qt theme
  workers.py       network threads (snapshot, pairing)
  sse.py           real-time event stream (SSE)
  widgets.py       toggle switch, scene/light tiles
  dialogs.py       light control, scene/zone editors
  window.py        main window
  setup_window.py  pairing screen
  app.py           orchestration + system tray (GUI entry point)
  cli.py           command-line interface
```

## Technical notes

- The bridge exposes its API over HTTPS with a self-signed certificate
  (`verify=False`); authentication uses the `hue-application-key` header.
- Colors are converted in sRGB both ways (RGB<->xy) to stay faithful to the
  picked color.
- The Philips mobile app's real product photos are not available through the
  bridge; Lumen uses tinted vector illustrations instead.
- The `client_key` obtained at pairing is kept for a future screen-sync mode
  (Entertainment/DTLS).

## Ideas for later

- Screen sync (ambilight) via the Entertainment API (DTLS). The `client_key`
  obtained at pairing is already stored for this.

## License

MIT.
