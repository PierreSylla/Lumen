"""CLIP-side control of Hue Entertainment configurations.

An entertainment configuration groups lights into positioned 'channels' that can
be driven at high frame rate over the DTLS stream. Before streaming we must set
the configuration's action to 'start'; when done, to 'stop'.
"""


def list_configs(bridge):
    return bridge.get("entertainment_configuration")


def config_name(config):
    return (config.get("metadata") or {}).get("name", "?")


def channel_ids(config):
    """Ordered list of channel ids in the configuration."""
    return sorted(c["channel_id"] for c in config.get("channels", []))


def channel_count(config):
    return len(config.get("channels", []))


def channel_positions(config):
    """[(channel_id, x, y, z)] ordered like channel_ids.

    Hue places channels in a cube around the viewer: x runs left (-1) to right
    (+1), y back to front, z bottom to top. Only x is reliable across setups -
    people lay their lamps out horizontally and leave z at 0.
    """
    out = []
    for c in config.get("channels", []):
        p = c.get("position") or {}
        out.append((c["channel_id"], p.get("x", 0.0),
                    p.get("y", 0.0), p.get("z", 0.0)))
    return sorted(out)


def start(bridge, config_id):
    return bridge.put("entertainment_configuration", config_id,
                      {"action": "start"})


def stop(bridge, config_id):
    return bridge.put("entertainment_configuration", config_id,
                      {"action": "stop"})


def pick_config(bridge, config_id=None):
    """Return an entertainment configuration dict, or None.

    If config_id is given, return that one; otherwise return the first available.
    """
    configs = list_configs(bridge)
    if not configs:
        return None
    if config_id:
        return next((c for c in configs if c["id"] == config_id), None)
    return configs[0]
