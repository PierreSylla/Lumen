"""Read/write the shared configuration (~/.config/huectl/config.json)."""

import os
import json

CONFIG_PATH = os.path.expanduser("~/.config/huectl/config.json")
APP_NAME = "huectl#hyprland"


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    """Merge `cfg` into the existing config and write the file (chmod 600)."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    existing = load_config()
    existing.update(cfg)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    try:
        os.chmod(CONFIG_PATH, 0o600)  # holds the clientkey (secret)
    except OSError:
        pass
