#!/usr/bin/env python3
"""hue - command-line control for Philips Hue (shares the GUI config)."""

import sys
import time
import json
import argparse

import requests

from .config import APP_NAME, load_config, save_config
from .bridge import Bridge, discover_bridge_ip


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def _bridge():
    cfg = load_config()
    if not cfg.get("bridge_ip") or not cfg.get("app_key"):
        die("not configured. Run:  hue discover  then  hue auth")
    return Bridge(cfg["bridge_ip"], cfg["app_key"])


def _name(res):
    return (res.get("metadata") or {}).get("name", "?")


def _match(items, query, kind):
    q = query.lower()
    exact = [i for i in items if _name(i).lower() == q]
    if len(exact) == 1:
        return exact[0]
    partial = [i for i in items if q in _name(i).lower()] or \
        [i for i in items if i.get("id") == query]
    if len(partial) == 1:
        return partial[0]
    if not partial:
        die(f"no {kind} named '{query}'")
    die(f"ambiguous '{query}': " + ", ".join(f"'{_name(i)}'" for i in partial))


def _grouped_light(res):
    return next((s["rid"] for s in res.get("services", [])
                 if s["rtype"] == "grouped_light"), None)


def resolve_target(bridge, query):
    for rtype in ("room", "zone"):
        for res in bridge.get(rtype):
            if _name(res).lower() == query.lower():
                gl = _grouped_light(res)
                if gl:
                    return "grouped_light", gl, _name(res)
    light = _match(bridge.get("light"), query, "light")
    return "light", light["id"], _name(light)


# -- conversions -------------------------------------------------------------
def hex_to_xy(hexstr):
    h = hexstr.lstrip("#")
    if len(h) != 6:
        die("color expected as #rrggbb")
    r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))

    def gm(c):
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    r, g, b = gm(r), gm(g), gm(b)
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    s = x + y + z
    return (round(x / s, 4), round(y / s, 4)) if s else (0.0, 0.0)


def kelvin_to_mirek(k):
    presets = {"warm": 2700, "neutral": 4000, "cool": 6500}
    if isinstance(k, str) and k.lower() in presets:
        k = presets[k.lower()]
    return max(153, min(500, round(1_000_000 / int(k))))


# -- commands ----------------------------------------------------------------
def cmd_discover(_a):
    try:
        ip = discover_bridge_ip()
    except Exception as e:  # noqa: BLE001
        die(f"discovery failed ({e}). Use  hue auth --ip <IP>")
    if not ip:
        die("no bridge found. Use  hue auth --ip <IP>")
    save_config({"bridge_ip": ip})
    print(f"bridge: {ip}  (saved)\nNow run:  hue auth")


def cmd_auth(a):
    cfg = load_config()
    ip = a.ip or cfg.get("bridge_ip")
    if not ip:
        die("no IP. Run  hue discover  or  hue auth --ip <IP>")
    print(f"Press the bridge button ({ip})...")
    payload = {"devicetype": APP_NAME, "generateclientkey": True}
    for _ in range(30):
        try:
            res = requests.post(f"https://{ip}/api", json=payload,
                                verify=False, timeout=5).json()
        except Exception as e:  # noqa: BLE001
            die(f"bridge unreachable ({e})")
        if isinstance(res, list) and res:
            item = res[0]
            if "success" in item:
                s = item["success"]
                save_config({"bridge_ip": ip, "app_key": s["username"],
                             "client_key": s.get("clientkey")})
                print("OK, paired.")
                return
            if str(item.get("error", {}).get("type")) != "101":
                die(item["error"].get("description", "failed"))
        time.sleep(1)
    die("timed out - button not pressed in time")


def cmd_lights(_a):
    for l in sorted(_bridge().get("light"), key=_name):
        on = "ON " if l.get("on", {}).get("on") else "off"
        bri = l.get("dimming", {}).get("brightness")
        bri = f"{bri:>3.0f}%" if bri is not None else "  - "
        print(f"[{on}] {bri}  {_name(l)}")


def cmd_rooms(_a):
    b = _bridge()
    for rtype, label in (("room", "room"), ("zone", "zone")):
        for res in sorted(b.get(rtype), key=_name):
            print(f"{label:<5}  {_name(res)}  ({len(res.get('children', []))})")


def cmd_scenes(_a):
    b = _bridge()
    gname = {}
    for rtype in ("room", "zone"):
        for res in b.get(rtype):
            gname[res["id"]] = _name(res)
    for s in sorted(b.get("scene"), key=_name):
        where = gname.get(s.get("group", {}).get("rid"), "?")
        print(f"{_name(s):<28}  ({where})")


def _set(query, payload):
    b = _bridge()
    rtype, rid, name = resolve_target(b, query)
    b.put(rtype, rid, payload)
    return name


def cmd_on(a):
    print("on:", _set(a.target, {"on": {"on": True}}))


def cmd_off(a):
    print("off:", _set(a.target, {"on": {"on": False}}))


def cmd_toggle(a):
    b = _bridge()
    rtype, rid, name = resolve_target(b, a.target)
    cur = next((r for r in b.get(rtype) if r["id"] == rid), None)
    is_on = cur.get("on", {}).get("on", False) if cur else False
    b.put(rtype, rid, {"on": {"on": not is_on}})
    print(("off" if is_on else "on") + ": " + name)


def cmd_bri(a):
    val = a.value
    b = _bridge()
    rtype, rid, name = resolve_target(b, a.target)
    if val.startswith(("+", "-")):
        cur = next((r for r in b.get(rtype) if r["id"] == rid), None)
        base = (cur or {}).get("dimming", {}).get("brightness", 0)
        target = max(0, min(100, base + float(val)))
    else:
        target = max(0.0, min(100.0, float(val)))
    b.put(rtype, rid, {"on": {"on": target > 0}, "dimming": {"brightness": target}})
    print(f"brightness {name}: {target:.0f}%")


def cmd_color(a):
    x, y = hex_to_xy(a.hex)
    print("color:", _set(a.target,
          {"on": {"on": True}, "color": {"xy": {"x": x, "y": y}}}))


def cmd_ct(a):
    print("temperature:", _set(a.target,
          {"on": {"on": True}, "color_temperature": {"mirek": kelvin_to_mirek(a.value)}}))


def cmd_scene(a):
    b = _bridge()
    scene = _match(b.get("scene"), a.name, "scene")
    b.put("scene", scene["id"], {"recall": {"action": "active"}})
    print("scene:", _name(scene))


def cmd_raw(a):
    b = _bridge()
    payload = json.loads(a.body) if a.body else None
    print(json.dumps(b._req(a.method.upper(), a.path, payload),
                     indent=2, ensure_ascii=False))


def build_parser():
    p = argparse.ArgumentParser(prog="hue", description="Philips Hue control (CLIP v2)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("discover").set_defaults(func=cmd_discover)
    pa = sub.add_parser("auth")
    pa.add_argument("--ip")
    pa.set_defaults(func=cmd_auth)
    sub.add_parser("lights").set_defaults(func=cmd_lights)
    sub.add_parser("rooms").set_defaults(func=cmd_rooms)
    sub.add_parser("scenes").set_defaults(func=cmd_scenes)
    for name, fn in (("on", cmd_on), ("off", cmd_off), ("toggle", cmd_toggle)):
        sp = sub.add_parser(name)
        sp.add_argument("target")
        sp.set_defaults(func=fn)
    sp = sub.add_parser("bri")
    sp.add_argument("target")
    sp.add_argument("value")
    sp.set_defaults(func=cmd_bri)
    sp = sub.add_parser("color")
    sp.add_argument("target")
    sp.add_argument("hex")
    sp.set_defaults(func=cmd_color)
    sp = sub.add_parser("ct")
    sp.add_argument("target")
    sp.add_argument("value")
    sp.set_defaults(func=cmd_ct)
    sp = sub.add_parser("scene")
    sp.add_argument("name")
    sp.set_defaults(func=cmd_scene)
    sp = sub.add_parser("raw")
    sp.add_argument("method")
    sp.add_argument("path")
    sp.add_argument("body", nargs="?")
    sp.set_defaults(func=cmd_raw)
    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
