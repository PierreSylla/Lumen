"""Drawn icons: per light-type glyph, app icon, scene gradient.

All toolbar glyphs are drawn (not font characters) so they render identically
regardless of the system font - some minimal setups lack symbols like the
ellipsis, gear or reload glyphs.
"""

import math

from PySide6.QtCore import Qt, QPoint, QPointF, QRectF
from PySide6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QPainterPath,
    QLinearGradient, QPolygon, QPolygonF,
)


def _canvas(size):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    return pm, p


def icon_plus(size=22, color="#e6e6e6"):
    pm, p = _canvas(size)
    pen = QPen(QColor(color), 2.4)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    m = size * 0.28
    p.drawLine(int(size / 2), int(m), int(size / 2), int(size - m))
    p.drawLine(int(m), int(size / 2), int(size - m), int(size / 2))
    p.end()
    return QIcon(pm)


def icon_gear(size=22, color="#e6e6e6"):
    pm, p = _canvas(size)
    c = QColor(color)
    pen = QPen(c, 2.2)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.translate(size / 2, size / 2)
    r = size * 0.28
    for i in range(8):
        p.save()
        p.rotate(i * 45)
        p.drawLine(0, int(-r - size * 0.09), 0, int(-r + size * 0.01))
        p.restore()
    p.drawEllipse(QPointF(0, 0), r, r)
    p.setBrush(c)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(0, 0), size * 0.09, size * 0.09)
    p.end()
    return QIcon(pm)


def icon_refresh(size=22, color="#e6e6e6"):
    pm, p = _canvas(size)
    c = QColor(color)
    pen = QPen(c, 2.2)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.translate(size / 2, size / 2)
    r = size * 0.30
    # ~290 deg arc, leaving a gap at the top-right for the arrowhead
    rect = QRectF(-r, -r, 2 * r, 2 * r)
    p.drawArc(rect, int(75 * 16), int(290 * 16))
    # arrowhead at the arc end (~5 deg), pointing tangentially (downward)
    ang = math.radians(5)
    ex, ey = r * math.cos(ang), -r * math.sin(ang)
    p.setBrush(c)
    p.setPen(Qt.NoPen)
    a = size * 0.11
    head = QPolygonF([QPointF(ex, ey - a), QPointF(ex + a, ey + a * 0.4),
                      QPointF(ex - a, ey + a * 0.4)])
    p.drawPolygon(head)
    p.end()
    return QIcon(pm)


def icon_edit(size=22, color="#e6e6e6"):
    pm, p = _canvas(size)
    c = QColor(color)
    p.translate(size / 2, size / 2)
    p.rotate(45)                 # diagonal pencil
    w = size * 0.20
    top, bot = -size * 0.34, size * 0.32
    p.setPen(Qt.NoPen)
    p.setBrush(c)
    body_h = (bot - top) * 0.78
    p.drawRect(QRectF(-w / 2, top, w, body_h))          # shaft
    ty = top + body_h
    p.drawPolygon(QPolygonF([QPointF(-w / 2, ty), QPointF(w / 2, ty),
                             QPointF(0, bot)]))          # tip
    p.setPen(QPen(QColor(0, 0, 0, 110), 1))             # eraser line
    yy = top + (bot - top) * 0.18
    p.drawLine(QPointF(-w / 2, yy), QPointF(w / 2, yy))
    p.end()
    return QIcon(pm)


def icon_trash(size=22, color="#e06c75"):
    pm, p = _canvas(size)
    c = QColor(color)
    pen = QPen(c, 2.0)
    pen.setJoinStyle(Qt.RoundJoin)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    s = size
    p.drawLine(int(s * 0.24), int(s * 0.30), int(s * 0.76), int(s * 0.30))  # lid
    # handle
    p.drawLine(int(s * 0.40), int(s * 0.30), int(s * 0.42), int(s * 0.22))
    p.drawLine(int(s * 0.42), int(s * 0.22), int(s * 0.58), int(s * 0.22))
    p.drawLine(int(s * 0.58), int(s * 0.22), int(s * 0.60), int(s * 0.30))
    # can body
    p.drawLine(int(s * 0.31), int(s * 0.30), int(s * 0.35), int(s * 0.76))
    p.drawLine(int(s * 0.69), int(s * 0.30), int(s * 0.65), int(s * 0.76))
    p.drawLine(int(s * 0.35), int(s * 0.76), int(s * 0.65), int(s * 0.76))
    # stripes
    p.drawLine(int(s * 0.45), int(s * 0.40), int(s * 0.46), int(s * 0.66))
    p.drawLine(int(s * 0.55), int(s * 0.40), int(s * 0.54), int(s * 0.66))
    p.end()
    return QIcon(pm)


def light_kind(light):
    a = ((light.get("metadata") or {}).get("archetype") or "").lower()
    if "strip" in a or "gradient" in a:
        return "strip"
    if any(k in a for k in ("play", "bloom", "iris", "go", "signe",
                            "centris", "bar", "ensis")):
        return "bar"
    if "spot" in a or "recessed" in a:
        return "spot"
    if "ceiling" in a or "pendant" in a:
        return "ceiling"
    if "floor" in a:
        return "floor"
    if "table" in a or "desk" in a:
        return "table"
    if "plug" in a:
        return "plug"
    if "candle" in a or "luster" in a or "flood" in a or "vintage" in a:
        return "candle"
    return "bulb"


def draw_light_icon(kind, color, size=40):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setPen(QPen(QColor(color.red(), color.green(), color.blue(), 70), 1.3))
    p.setBrush(QBrush(color))
    s = size

    if kind == "strip":
        p.drawRoundedRect(3, s * 0.42, s - 6, s * 0.18, 4, 4)
        p.setPen(QPen(QColor(0, 0, 0, 60), 1))
        for i in range(1, 5):
            x = 3 + (s - 6) * i / 5
            p.drawLine(int(x), int(s * 0.44), int(x), int(s * 0.58))
    elif kind == "bar":
        p.drawRoundedRect(s * 0.40, 4, s * 0.20, s - 8, 4, 4)
    elif kind == "spot":
        p.drawEllipse(int(s * 0.32), 3, int(s * 0.36), int(s * 0.30))
        p.drawPolygon(QPolygon([QPoint(int(s * 0.34), int(s * 0.33)),
                                QPoint(int(s * 0.66), int(s * 0.33)),
                                QPoint(int(s * 0.60), int(s * 0.78)),
                                QPoint(int(s * 0.40), int(s * 0.78))]))
    elif kind == "ceiling":
        p.drawRoundedRect(s * 0.18, 3, s * 0.64, s * 0.14, 3, 3)
        p.drawPolygon(QPolygon([QPoint(int(s * 0.28), int(s * 0.17)),
                                QPoint(int(s * 0.72), int(s * 0.17)),
                                QPoint(int(s * 0.62), int(s * 0.80)),
                                QPoint(int(s * 0.38), int(s * 0.80))]))
    elif kind == "floor":
        p.drawPolygon(QPolygon([QPoint(int(s * 0.30), int(s * 0.30)),
                                QPoint(int(s * 0.70), int(s * 0.30)),
                                QPoint(int(s * 0.62), int(s * 0.10)),
                                QPoint(int(s * 0.38), int(s * 0.10))]))
        p.setPen(QPen(color, 2))
        p.drawLine(int(s * 0.5), int(s * 0.30), int(s * 0.5), int(s * 0.86))
        p.drawLine(int(s * 0.36), int(s * 0.86), int(s * 0.64), int(s * 0.86))
    elif kind == "table":
        p.drawPolygon(QPolygon([QPoint(int(s * 0.30), int(s * 0.46)),
                                QPoint(int(s * 0.70), int(s * 0.46)),
                                QPoint(int(s * 0.62), int(s * 0.24)),
                                QPoint(int(s * 0.38), int(s * 0.24))]))
        p.setPen(QPen(color, 2))
        p.drawLine(int(s * 0.5), int(s * 0.46), int(s * 0.5), int(s * 0.82))
        p.drawLine(int(s * 0.36), int(s * 0.82), int(s * 0.64), int(s * 0.82))
    elif kind == "plug":
        p.drawRoundedRect(s * 0.30, s * 0.30, s * 0.40, s * 0.44, 4, 4)
        p.setPen(QPen(color, 2))
        p.drawLine(int(s * 0.42), int(s * 0.16), int(s * 0.42), int(s * 0.32))
        p.drawLine(int(s * 0.58), int(s * 0.16), int(s * 0.58), int(s * 0.32))
    elif kind == "candle":
        flame = QPainterPath()
        flame.moveTo(s * 0.5, s * 0.12)
        flame.cubicTo(s * 0.72, s * 0.34, s * 0.66, s * 0.60, s * 0.5, s * 0.60)
        flame.cubicTo(s * 0.34, s * 0.60, s * 0.28, s * 0.34, s * 0.5, s * 0.12)
        p.drawPath(flame)
        p.drawRoundedRect(s * 0.42, s * 0.60, s * 0.16, s * 0.24, 2, 2)
    else:
        p.drawEllipse(int(s * 0.24), int(s * 0.10), int(s * 0.52), int(s * 0.52))
        p.drawRoundedRect(s * 0.38, s * 0.58, s * 0.24, s * 0.24, 3, 3)
    p.end()
    return pm


def make_icon(on=True):
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QBrush(QColor(255, 205, 70) if on else QColor(120, 120, 120)))
    p.setPen(Qt.NoPen)
    p.drawEllipse(16, 8, 32, 32)
    p.setBrush(QBrush(QColor(90, 90, 90)))
    p.drawRoundedRect(24, 40, 16, 14, 3, 3)
    p.setPen(QColor(60, 60, 60))
    for yy in (44, 48, 52):
        p.drawLine(24, yy, 40, yy)
    p.end()
    return QIcon(pm)


def paint_palette(p, w, h, colors):
    if not colors:
        p.fillRect(0, 0, w, h, QColor(46, 50, 58))
    elif len(colors) == 1:
        p.fillRect(0, 0, w, h, colors[0])
    else:
        grad = QLinearGradient(0, 0, w, 0)
        n = len(colors)
        for i, c in enumerate(colors):
            grad.setColorAt(i / (n - 1), c)
        p.fillRect(0, 0, w, h, QBrush(grad))
