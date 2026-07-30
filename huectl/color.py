"""Color conversions (consistent sRGB matrices both ways) and helpers."""

from PySide6.QtGui import QColor


def rgb_to_xy(r, g, b):
    def gamma(c):
        c /= 255.0
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    r, g, b = gamma(r), gamma(g), gamma(b)
    x = r * 0.4124 + g * 0.3576 + b * 0.1805
    y = r * 0.2126 + g * 0.7152 + b * 0.0722
    z = r * 0.0193 + g * 0.1192 + b * 0.9505
    s = x + y + z
    return (x / s, y / s) if s else (0.0, 0.0)


def xy_to_qcolor(x, y, bri=100):
    """xy -> QColor. Hue normalized (full), dimmed by brightness."""
    if y <= 0:
        return QColor(255, 255, 255)
    Y = 1.0
    X = (Y / y) * x
    Z = (Y / y) * (1.0 - x - y)
    r = 3.2406 * X - 1.5372 * Y - 0.4986 * Z
    g = -0.9689 * X + 1.8758 * Y + 0.0415 * Z
    b = 0.0557 * X - 0.2040 * Y + 1.0570 * Z
    r, g, b = max(0.0, r), max(0.0, g), max(0.0, b)
    m = max(r, g, b) or 1.0
    r, g, b = r / m, g / m, b / m

    def gm(c):
        return 1.055 * (c ** (1 / 2.4)) - 0.055 if c > 0.0031308 else 12.92 * c
    f = max(0.25, (bri or 100) / 100.0)
    return QColor(int(gm(r) * 255 * f), int(gm(g) * 255 * f), int(gm(b) * 255 * f))


def mirek_to_qcolor(mirek, bri=100):
    m = max(153, min(500, mirek or 366))
    tt = (m - 153) / (500 - 153)
    cool, warm = (200, 220, 255), (255, 165, 70)
    f = max(0.3, (bri or 100) / 100.0)
    rgb = [int((cool[i] + (warm[i] - cool[i]) * tt) * f) for i in range(3)]
    return QColor(*[min(255, c) for c in rgb])


def contrast_color(bg):
    lum = 0.299 * bg.red() + 0.587 * bg.green() + 0.114 * bg.blue()
    return QColor(24, 24, 28) if lum > 150 else QColor(245, 245, 245)


def base_light_color(light):
    """Full hue of the light (no dimming applied)."""
    xy = light.get("color", {}).get("xy")
    ct = light.get("color_temperature", {}).get("mirek")
    if xy:
        return xy_to_qcolor(xy.get("x", 0.33), xy.get("y", 0.33), 100)
    if ct:
        return mirek_to_qcolor(ct, 100)
    return QColor(255, 214, 140)


def scene_colors(scene):
    """List of QColor representing a scene, extracted from its actions."""
    cols = []
    for a in scene.get("actions", []):
        act = a.get("action", {})
        if act.get("on", {}).get("on") is False:
            continue
        bri = act.get("dimming", {}).get("brightness", 100)
        xy = act.get("color", {}).get("xy")
        ct = act.get("color_temperature", {}).get("mirek")
        if xy:
            cols.append(xy_to_qcolor(xy.get("x", 0.33), xy.get("y", 0.33), bri))
        elif ct:
            cols.append(mirek_to_qcolor(ct, bri))
        else:
            cols.append(mirek_to_qcolor(366, bri))
    return cols


def light_to_action(light):
    """Current state of a light -> scene action."""
    act = {"on": {"on": bool(light.get("on", {}).get("on"))}}
    if "dimming" in light and light["dimming"].get("brightness") is not None:
        act["dimming"] = {"brightness": light["dimming"]["brightness"]}
    xy = light.get("color", {}).get("xy")
    ct = light.get("color_temperature", {}).get("mirek")
    if xy:
        act["color"] = {"xy": xy}
    elif ct:
        act["color_temperature"] = {"mirek": ct}
    return {"target": {"rid": light["id"], "rtype": "light"}, "action": act}


def name_of(res):
    return (res.get("metadata") or {}).get("name", "?")
