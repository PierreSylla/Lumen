# Handoff - Lumen

State of the project so another session can pick it up. Pair this with
`CLAUDE.md` (conventions, architecture, build/test).

## Snapshot

- **Project**: Lumen - desktop Philips Hue control via the local CLIP v2 API.
- **Version**: 0.8.0. **License**: GPL-3.0-or-later.
- **Stack**: Python >= 3.10 backend + Vue 3/Vite UI in a `pywebview`
  (GTK/WebKit) window. `requests` for HTTP; `openssl` binary for sync;
  `pystray`+`pillow` for the tray. `PySide6` survives only for
  `portal.py`'s QtDBus screen-capture fallback - there is no Qt GUI left.
- **Entry points**: `hue-webui` (the app), `hue` (CLI), `hue-sync` (screen sync).
- **Config**: `~/.config/huectl/config.json` (bridge_ip, app_key, client_key,
  columns, language, start_minimized, sync_output, sync_saturation,
  sync_fps), shared by all entry points.
- **User environment**: CachyOS (Arch), Hyprland/Wayland, Noctalia shell,
  NVIDIA+Intel hybrid GPU. Real bridge + lamps; every step of this migration
  was verified against them directly (screenshots via `grim`, live bridge
  writes with before/after restores) - see "Lessons from the migration"
  below for what that caught that a clean build alone would have missed.

## The PySide6 -> Vue/pywebview migration is done

All 9 planned steps landed: scaffold, design system, live snapshot render,
write path (toggles/brightness/colour/scenes), SSE, pairing/setup, settings
+ i18n, screen-sync page + tray, PyInstaller packaging, and finally this
cleanup step (PySide6 GUI removed, docs rewritten). Feature parity with the
old Qt app was confirmed **before** removing it, including two things the
first pass of the migration had explicitly deferred:

- **Scene create/edit/delete** now works (`SceneEditorSheet.vue`,
  `Api.save_scene`/`delete_scene`). The bridge requires a scene's actions to
  cover every light currently in its group - not a subset - confirmed by a
  live 400 error ("Light action targets not matching lights in referenced
  group") when only 4 of 5 room lights were included. The editor has no
  per-lamp picker for this reason; it always re-captures the whole group.
- **Room/zone create/edit now actually persist** (`Api.save_group`,
  `POST`/`PUT` on `room`/`zone`) and **delete** works too
  (`Api.delete_group`). The editor UI already existed from step 1 but its
  Save button was a no-op until this step.

## Architecture at a glance

See `CLAUDE.md` for the full module table. The shape worth remembering:

- `huectl/webapp.py` is the whole pywebview side: one `Api` class (every
  `window.pywebview.api.*` method the UI calls), `WebSSE` (bridge event
  stream, daemon thread), `WebSync` (screen-sync session, daemon thread
  wrapping `sync.run_stream` unmodified), the pairing worker, and the tray
  (`_setup_tray`, `pystray` + a drawn PIL icon).
- `webui/src/store/index.js` is the only place that calls into `Api`. Every
  component reads/writes through it - there is no second source of truth.
- `webui/src/lib/snapshot.js` + `huecolor.js` port `window.py`'s old
  membership-resolution logic and `color.py`'s xy/mirek math into JS,
  because neither could be imported without dragging PySide6 into the
  Qt-less webview process (`color.py` does `from PySide6.QtGui import
  QColor` at module level). Small, stable, pure-logic functions
  (`_process_events` for SSE, `_light_to_action`/`_lights_of_group` for
  scenes) are likewise **duplicated** in `webapp.py` rather than imported,
  each with a comment saying why.

## Lessons from the migration (read before assuming a clean build = working)

Every one of these was caught by actually launching `hue-webui` against the
real bridge and looking at a screenshot or a follow-up bridge read - never
by the build succeeding or the code reading correctly on its own:

- **pywebview readiness race.** `window.pywebview` exists before
  `window.pywebview.api` is actually attached, and on this GTK
  backend/version even the `'pywebviewready'` event fired before `.api` was
  populated. Two different screens (Setup, Pairing) shipped this bug before
  it was extracted into a shared, polling `apiReady()` - a screenshot showing
  a blank IP field on a bridge that was very much paired is what caught it.
- **Substring, not exact, archetype matching.** Real Hue archetypes are
  product names ("hue_play", "table_shade"), not the enum-looking strings
  you'd guess from the redesign doc's own table. Exact-key lookup made every
  lamp render as a generic bulb; only a live screenshot against real lights
  showed it.
- **Stale "first card expanded" id.** The default-expand logic captured
  sample data's id at mount; once the real snapshot replaced sample data
  wholesale, nothing matched and nothing was expanded. Fixed by re-deriving
  the default whenever the group list changes wholesale, not just once.
- **`WebSync` hang with no explicit monitor.** Passing `output=None` on this
  multi-monitor Hyprland setup makes `capture.py`'s `wlroots` backend fail
  outright, falling through to the Qt/D-Bus-dependent `portal` backend -
  which this Qt-less process can never satisfy, so the thread hung forever
  and never responded to `stop()`. Fixed by always resolving "Automatic" to
  a concrete `hyprctl`-derived output before starting. See `CLAUDE.md`.
- **PyInstaller bloat, found only by actually measuring the output.** First
  build was 515MB - `pywebview` ships an alternate PyQt6 backend (separate
  from PySide6) that pulled in this machine's unrelated PyQt6 install and
  its whole numpy/scipy/matplotlib/liblapack chain, and a GTK hook bundled
  KDE's entire Breeze icon theme regardless of `excludes=`. Final size: 168MB,
  genuinely dominated by GTK/WebKit/Python, matching what was expected going
  in. The lesson isn't the specific fix, it's that `du -a | sort -rh` on the
  actual output is the only way this kind of thing surfaces.
- **A "communication issues" bridge warning does not mean the write failed.**
  A real PUT during write-path testing returned that warning on a light and
  the change still landed (verified by a follow-up GET). The UI doesn't
  currently surface these warnings at all (see Known issues).
- **A build artifact outside the package tree is invisible to `pip`/`pipx
  install`.** `webui/dist/` sat next to `huectl/`, not inside it; every
  in-repo test this migration ran (`python -m huectl.webapp` from the
  checkout, and a PyInstaller build with its own explicit `datas=` entry)
  happened to resolve it correctly, so this shipped all the way through
  step 8's "packaging" step before a real `pipx install .` on the user's
  machine hit `.../site-packages/webui/dist/index.html not found` - pipx
  only packages what setuptools is told belongs to the package. Fixed by
  moving the Vite build output to `huectl/webui_dist/` (declared in
  `pyproject.toml`'s `package-data`) so it's part of the package for real,
  not just reachable by coincidence from a specific working directory.
  Caught only because the user actually ran the documented install command,
  not `python -m huectl.webapp` from the repo - a reminder that "verified
  end to end" still means verified from the paths *this session* tried, not
  every path a real install can take.
- **`pipx`'s isolation hides system-installed `gi` (PyGObject) entirely.**
  `pywebview`'s GTK backend and `pystray`'s tray both need it, and it has no
  working pip equivalent here (it's the `python-gobject` system package,
  binding to the system's actual GTK). A `pipx install .` with no extra flag
  produces a `hue-webui` that crashes immediately on launch
  ("`ModuleNotFoundError: No module named 'gi'`", then pywebview's "You must
  have either QT or GTK with Python extensions installed"). Fixed with
  `pipx install --system-site-packages`. Confirmed by hand that `--force`
  alone (no `--system-site-packages`) does *not* retroactively fix an
  already-broken venv - only recreating it (which `--force` combined *with*
  the flag does do, verified) actually applies the setting, so re-running
  `install.sh` after this fix landed was enough to self-heal an existing
  broken install, not just fresh ones. `pip install --user` never had this
  problem - no isolation to hide anything behind.

Older lessons, still true, from the Qt-app era (kept for the pattern, not
the specific fix - the buggy code itself is gone): a four-round debugging
loop on a "broken" zone edit button turned out to be two *environment*
facts (zero zones existed; a columns setting made cards overflow) rather
than the button's own code, which was correct throughout. When several
plausible fixes in a row do nothing, suspect the diagnosis, not the next
fix - reproduce against real data first.

## Known issues / possible follow-ups

- **No toast/error UI.** Failed writes (bridge unreachable, a rejected PUT)
  currently fail silently from the user's point of view - the store methods
  return `{error}` but nothing displays it except the Pairing screen's own
  inline error text. Worth adding once a design exists for it (nothing in
  `redesign/README.md` currently specs one - don't invent a pattern
  unprompted).
- **"Tiles per row" has no effect.** The setting persists to config (parity
  with the old app's field) but the redesign's Rooms/Zones/Scenes pages are
  a single-column card list, not a tile grid - there is currently nothing
  for this setting to control. Flagged, not silently wired to something
  invented.
- **Close-to-tray wasn't live-clicked.** The `window.events.closing` handler
  matches pywebview's documented contract (verified by reading the GTK
  backend's source directly - returning `True` cancels the close), but this
  environment's customized Hyprland build only offered a Lua dispatch API
  (`hl.dsp.window.close()`) that turned out to bypass graceful close
  negotiation entirely rather than simulate a real titlebar click. Worth a
  manual click-test on a normal setup.
- **Windows packaging is a stub.** `packaging/lumen-webui.spec` is Linux
  only (GTK/WebKit and `hyprctl` are Linux-specific dependencies here).
- No automated test suite in-repo; testing is manual, against a real bridge
  and a real launched window (see `CLAUDE.md`'s Build/run/test section).

## How to resume quickly

1. Read `CLAUDE.md`, then this file.
2. `python -m compileall -q huectl` and `cd webui && npm run build` to
   confirm a clean baseline.
3. Launch `python -m huectl.webapp` for real and look at it - see
   `CLAUDE.md`'s Build/run/test section for why a passing build alone isn't
   evidence of anything, per the lessons above.
4. Pick up at one of the Known issues above, or ask what the next design
   priority is - there's no single "next step" the way there was mid-migration.
