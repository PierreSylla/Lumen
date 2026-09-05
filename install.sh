#!/usr/bin/env bash
# Install Lumen: system dependencies, the built web UI, and the Python
# package (hue / hue-webui / hue-sync). Run from anywhere:
#   ./install.sh          interactive (asks before anything system-wide)
#   ./install.sh -y       non-interactive (assumes yes to every prompt)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"

ASSUME_YES=0
[[ "${1:-}" == "-y" || "${1:-}" == "--yes" ]] && ASSUME_YES=1

confirm() {
    # confirm "question" -> 0 (yes) or 1 (no). Default answer is yes.
    if [[ "$ASSUME_YES" == "1" ]]; then
        return 0
    fi
    read -rp "$1 [Y/n] " reply
    [[ -z "$reply" || "$reply" =~ ^[Yy]$ ]]
}

echo "== Lumen installer =="
echo "Repository: $REPO_ROOT"

# -- 1. System dependencies (Arch/CachyOS via pacman - this project's ---------
# -- confirmed environment, see CLAUDE.md) ------------------------------------

PACMAN_PKGS=(nodejs npm python-pywebview webkit2gtk-4.1 python-gobject
             python-pystray python-pillow libayatana-appindicator)
command -v pipx >/dev/null 2>&1 || PACMAN_PKGS+=(python-pipx)

if command -v pacman >/dev/null 2>&1; then
    echo
    echo "Arch-based system detected. pacman will install (skipping anything"
    echo "already present):"
    printf '  - %s\n' "${PACMAN_PKGS[@]}"
    if confirm "Proceed with 'sudo pacman -S --needed'?"; then
        sudo pacman -S --needed "${PACMAN_PKGS[@]}"
    else
        echo "Skipped - make sure these are installed some other way first."
    fi
else
    echo
    echo "No pacman here - install these yourself before continuing (see"
    echo "README.md's Installation section for the non-Arch equivalents):"
    printf '  - %s\n' "${PACMAN_PKGS[@]}"
    confirm "Continue once done?" || exit 1
fi

# -- 2. Screen sync capture backend (optional feature, best guess from the ---
# -- current session - see README.md's Screen sync table) --------------------

if [[ -n "${HYPRLAND_INSTANCE_SIGNATURE:-}" || "${XDG_CURRENT_DESKTOP:-}" =~ [Hh]yprland|[Ss]way ]]; then
    SYNC_PKGS=(wf-recorder)
    SYNC_WHY="Hyprland/Sway detected - wlroots backend"
elif [[ "${XDG_SESSION_TYPE:-}" == "wayland" ]]; then
    SYNC_PKGS=(gstreamer gst-plugin-pipewire pipewire-utils xdg-desktop-portal)
    SYNC_WHY="other Wayland compositor detected - portal backend"
elif [[ "${XDG_SESSION_TYPE:-}" == "x11" ]]; then
    SYNC_PKGS=(ffmpeg)
    SYNC_WHY="X11 session detected"
else
    SYNC_PKGS=()
    SYNC_WHY="couldn't detect the session type"
fi

echo
echo "Screen sync (ambilight) is optional and needs one more system binary."
if [[ ${#SYNC_PKGS[@]} -gt 0 && -n "$(command -v pacman || true)" ]]; then
    echo "$SYNC_WHY: ${SYNC_PKGS[*]}"
    if confirm "Install it now?"; then
        sudo pacman -S --needed "${SYNC_PKGS[@]}"
    fi
else
    echo "$SYNC_WHY - see README.md's Screen sync table and install the"
    echo "matching backend yourself if you want ambilight."
fi

# -- 3. Build the Vue UI -------------------------------------------------------

for tool in node npm; do
    command -v "$tool" >/dev/null 2>&1 || {
        echo "error: '$tool' not found in PATH - install Node.js/npm first." >&2
        exit 1
    }
done

echo
echo "Building the web UI (webui/ -> huectl/webui_dist/)..."
(cd webui && npm install && npm run build)

# -- 4. Install the Python package --------------------------------------------

echo
if command -v pipx >/dev/null 2>&1; then
    echo "Installing with pipx (isolated environment)..."
    # --system-site-packages is required, not cosmetic: pywebview's GTK
    # backend and pystray's tray both need PyGObject (the 'gi' module),
    # which is a system package (python-gobject) with no pip equivalent
    # that works here - pipx's default full isolation hides it entirely,
    # which crashes hue-webui at startup ("You must have either QT or GTK
    # with Python extensions installed"). Confirmed by hand: --force alone
    # reinstalls packages into the existing venv but does NOT add this
    # after the fact - only recreating the venv (which --force does do,
    # verified) with the flag actually fixes an already-broken install.
    pipx install "$REPO_ROOT" --force --system-site-packages
else
    echo "pipx not found - installing with 'pip install --user' instead."
    echo "(this shares your normal Python packages, so it doesn't hit the"
    echo "pipx-isolation GTK issue below - nothing extra needed here)"
    pip install --user "$REPO_ROOT"
fi

# `pipx install --force` re-links whatever the current package declares but
# does not remove a shim for a script an older version used to declare -
# hue-gui (removed when the PySide6 GUI was) can be left behind as a symlink
# into the venv pointing at a file that no longer exists there. Confirmed by
# hand: it doesn't error until actually run. Only touch it if it's genuinely
# dangling - never remove a real command.
HUE_GUI_SHIM="$HOME/.local/bin/hue-gui"
if [[ -L "$HUE_GUI_SHIM" && ! -e "$HUE_GUI_SHIM" ]]; then
    rm -f "$HUE_GUI_SHIM"
    echo "Removed stale command: $HUE_GUI_SHIM (hue-webui replaces it)"
fi

# -- 5. Desktop launcher (optional) -------------------------------------------

echo
if confirm "Install the application-menu launcher?"; then
    mkdir -p "$HOME/.local/share/applications"
    cp packaging/lumen.desktop "$HOME/.local/share/applications/lumen.desktop"
    echo "Installed: $HOME/.local/share/applications/lumen.desktop"
fi

echo
echo "Done. Run 'hue-webui' to start - first run walks through bridge pairing."
