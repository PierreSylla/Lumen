"""Visual components: toggle switch, scene tile, light tile."""

from PySide6.QtWidgets import (
    QFrame, QLabel, QHBoxLayout, QToolButton, QMenu, QSizePolicy, QAbstractButton,
)
from PySide6.QtGui import QPainter, QColor, QPainterPath, QFont
from PySide6.QtCore import Qt, QRect, QSize

from .color import base_light_color, contrast_color, name_of
from .icons import draw_light_icon, light_kind, paint_palette
from .i18n import t
from .theme import ACCENT


class ToggleSwitch(QAbstractButton):
    """Pill-style toggle, readable on any background."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(46, 26)

    def sizeHint(self):
        return QSize(46, 26)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        r = h / 2
        track = QColor(ACCENT) if self.isChecked() else QColor(120, 126, 138)
        p.setPen(Qt.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(0, 0, w, h, r, r)
        d = h - 6
        x = w - d - 3 if self.isChecked() else 3
        p.setBrush(QColor(255, 255, 255))
        p.drawEllipse(int(x), 3, int(d), int(d))
        p.end()


class SceneTile(QFrame):
    def __init__(self, scene, colors, callbacks):
        super().__init__()
        self.scene = scene
        self.colors = colors
        self._cb = callbacks
        self.setMinimumHeight(92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        n = len(scene.get("actions", []))
        self.setToolTip(t("tile_lamps", n=n) + (t("scene_empty") if n == 0 else ""))

        self.menu_btn = QToolButton(self)
        self.menu_btn.setText("...")
        self.menu_btn.setFixedSize(24, 22)
        self.menu_btn.setCursor(Qt.PointingHandCursor)
        self.menu_btn.setPopupMode(QToolButton.InstantPopup)
        self.menu_btn.setStyleSheet(
            "QToolButton{background:rgba(0,0,0,120);border:0;border-radius:11px;"
            "color:white;font-weight:700;font-size:15px;}"
            "QToolButton::menu-indicator{image:none;}"
            "QToolButton:hover{background:rgba(0,0,0,190);}")
        menu = QMenu(self)
        menu.addAction(t("menu_activate"), lambda: self._cb["activate"](self.scene))
        menu.addAction(t("menu_edit"), lambda: self._cb["edit"](self.scene))
        menu.addSeparator()
        menu.addAction(t("menu_delete"), lambda: self._cb["delete"](self.scene))
        self.menu_btn.setMenu(menu)

    def resizeEvent(self, _e):
        self.menu_btn.move(self.width() - 30, 6)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        path = QPainterPath()
        path.addRoundedRect(0, 0, w, h, 10, 10)
        p.setClipPath(path)
        paint_palette(p, w, h, self.colors)
        p.fillRect(0, h - 30, w, 30, QColor(0, 0, 0, 150))
        p.setPen(QColor(255, 255, 255))
        f = QFont()
        f.setPointSize(10)
        f.setBold(True)
        p.setFont(f)
        nm = p.fontMetrics().elidedText(name_of(self.scene), Qt.ElideRight, w - 16)
        p.drawText(QRect(10, h - 29, w - 16, 28), Qt.AlignVCenter | Qt.AlignLeft, nm)
        if not self.colors:
            p.setPen(QColor(150, 150, 155))
            p.drawText(QRect(0, 4, w, h - 32), Qt.AlignCenter, t("vide"))
        p.end()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self._cb["activate"](self.scene)


class LightTile(QFrame):
    """Background = the light's real color. Click = control dialog."""

    def __init__(self, light, win):
        super().__init__()
        self.setObjectName("lightTile")
        self.light = light
        self.win = win
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(78)
        self.setCursor(Qt.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 10, 10)
        lay.setSpacing(10)
        self.icon = QLabel()
        self.icon.setFixedSize(40, 40)
        self.icon.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay.addWidget(self.icon)
        self.name = QLabel(name_of(light))
        self.name.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay.addWidget(self.name, 1)
        self.toggle = ToggleSwitch()
        self.toggle.setChecked(bool(light.get("on", {}).get("on")))
        self.toggle.setToolTip(t("toggle_tt"))
        self.toggle.clicked.connect(self._toggle)  # clicked -> user action only
        lay.addWidget(self.toggle, 0, Qt.AlignVCenter)
        self.refresh()

    def _bri(self):
        return self.light.get("dimming", {}).get("brightness", 100)

    def refresh(self):
        on = bool(self.light.get("on", {}).get("on"))
        if on:
            base = base_light_color(self.light)
            dim = 0.45 + 0.55 * (self._bri() / 100.0)
            bg = QColor(int(base.red() * dim), int(base.green() * dim),
                        int(base.blue() * dim))
        else:
            bg = QColor(52, 56, 64)
        cc = contrast_color(bg)
        self.setStyleSheet(
            f"QFrame#lightTile{{background:{bg.name()};"
            f"border:1px solid rgba(0,0,0,70);border-radius:12px;}}")
        self.name.setStyleSheet(
            f"color:{cc.name()};font-weight:600;background:transparent;")
        self.icon.setPixmap(draw_light_icon(light_kind(self.light), cc, 40))
        self.toggle.setChecked(on)  # setChecked does not emit clicked

    def _toggle(self, on):
        self.light.setdefault("on", {})["on"] = on
        self.refresh()
        self.win._act("light", self.light["id"], {"on": {"on": on}})

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            from .dialogs import LightControlDialog
            LightControlDialog(self.light, self.win, self.refresh, self).exec()
