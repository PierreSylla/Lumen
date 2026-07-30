"""Dialogs: light control, scene editor, room/zone editor."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QSlider, QScrollArea, QWidget, QFrame,
    QColorDialog,
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt

from .color import rgb_to_xy, base_light_color, mirek_to_qcolor, name_of
from .i18n import t
from .theme import ACCENT

# color swatches (vivid hues)
SWATCHES = ["#ff3b30", "#ff9500", "#ffcc00", "#34c759", "#00c7be",
            "#0a84ff", "#5e5ce6", "#bf5af2", "#ff2d92", "#ffffff"]
# white swatches: warmest to coolest (in mirek)
CT_MIREKS = [500, 400, 346, 286, 233, 182, 153]


def _ok_cancel(dlg):
    row = QHBoxLayout()
    row.addStretch(1)
    cancel = QPushButton(t("cancel"))
    cancel.clicked.connect(dlg.reject)
    ok = QPushButton(t("save"))
    ok.setStyleSheet(f"background:{ACCENT};color:#16181d;font-weight:700;")
    ok.clicked.connect(dlg.accept)
    row.addWidget(cancel)
    row.addWidget(ok)
    return row


class LightControlDialog(QDialog):
    def __init__(self, light, win, on_change, parent=None):
        super().__init__(parent)
        self.light = light
        self.win = win
        self.on_change = on_change
        self.setWindowTitle(name_of(light))
        self.setMinimumWidth(320)

        v = QVBoxLayout(self)
        v.setSpacing(10)
        self.preview = QFrame()
        self.preview.setFixedHeight(48)
        v.addWidget(self.preview)

        if "dimming" in light:
            v.addWidget(QLabel(t("brightness")))
            self.bri = QSlider(Qt.Horizontal)
            self.bri.setRange(0, 100)
            self.bri.setValue(int(light["dimming"].get("brightness", 100)))
            self.bri.valueChanged.connect(self._update_preview)
            self.bri.sliderReleased.connect(self._apply_bri)
            v.addWidget(self.bri)
        else:
            self.bri = None

        if "color" in light:
            v.addWidget(QLabel(t("color")))
            v.addLayout(self._swatch_grid(SWATCHES, self._apply_hex, is_hex=True))
            more = QPushButton(t("more_colors"))
            more.clicked.connect(self._more_colors)
            v.addWidget(more)

        if "color_temperature" in light:
            v.addWidget(QLabel(t("white")))
            hexes = [mirek_to_qcolor(m, 100).name() for m in CT_MIREKS]
            v.addLayout(self._swatch_grid(list(zip(hexes, CT_MIREKS)),
                                          self._apply_ct, is_hex=False))

        close = QPushButton(t("close"))
        close.clicked.connect(self.accept)
        v.addWidget(close, 0, Qt.AlignRight)
        self._update_preview()

    def _swatch_grid(self, items, handler, is_hex):
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, item in enumerate(items):
            hexcol = item if is_hex else item[0]
            arg = item if is_hex else item[1]
            b = QPushButton()
            b.setFixedSize(30, 30)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(
                f"background:{hexcol};border:1px solid #555;border-radius:15px;")
            b.clicked.connect(lambda _=False, a=arg: handler(a))
            grid.addWidget(b, i // 6, i % 6)
        return grid

    def _update_preview(self):
        base = base_light_color(self.light)
        bri = self.bri.value() if self.bri else 100
        dim = 0.4 + 0.6 * (bri / 100.0)
        col = QColor(int(base.red() * dim), int(base.green() * dim),
                     int(base.blue() * dim))
        self.preview.setStyleSheet(
            f"background:{col.name()};border-radius:8px;border:1px solid #555;")

    def _apply_bri(self):
        val = self.bri.value()
        self.light.setdefault("dimming", {})["brightness"] = float(val)
        self.light.setdefault("on", {})["on"] = val > 0
        self.win._act("light", self.light["id"],
                      {"on": {"on": val > 0}, "dimming": {"brightness": float(val)}})
        self._changed()

    def _apply_hex(self, hexcol):
        c = QColor(hexcol)
        x, y = rgb_to_xy(c.red(), c.green(), c.blue())
        self.light.setdefault("color", {})["xy"] = {"x": round(x, 4), "y": round(y, 4)}
        self.light.pop("color_temperature", None)
        self.light.setdefault("on", {})["on"] = True
        self.win._act("light", self.light["id"],
                      {"on": {"on": True},
                       "color": {"xy": {"x": round(x, 4), "y": round(y, 4)}}})
        self._update_preview()
        self._changed()

    def _apply_ct(self, mirek):
        self.light.setdefault("color_temperature", {})["mirek"] = mirek
        self.light.pop("color", None)
        self.light.setdefault("on", {})["on"] = True
        self.win._act("light", self.light["id"],
                      {"on": {"on": True}, "color_temperature": {"mirek": mirek}})
        self._update_preview()
        self._changed()

    def _more_colors(self):
        col = QColorDialog.getColor(parent=self, title=t("color"))
        if col.isValid():
            self._apply_hex(col.name())

    def _changed(self):
        if self.on_change:
            self.on_change()


class SceneEditor(QDialog):
    def __init__(self, groups, scene=None, parent=None):
        super().__init__(parent)
        self.scene = scene
        editing = scene is not None
        self.setWindowTitle(t("title_edit_scene") if editing else t("title_new_scene"))
        self.setMinimumWidth(360)
        v = QVBoxLayout(self)
        v.setSpacing(8)
        v.addWidget(QLabel(t("name")))
        self.name = QLineEdit(name_of(scene) if editing else "")
        v.addWidget(self.name)
        v.addWidget(QLabel(t("room_zone")))
        self.group = QComboBox()
        for label, rid, rtype in groups:
            self.group.addItem(label, (rid, rtype))
        if editing:
            gid = scene.get("group", {}).get("rid")
            for i in range(self.group.count()):
                if self.group.itemData(i)[0] == gid:
                    self.group.setCurrentIndex(i)
                    break
        self.group.setEnabled(not editing and self.group.count() > 1)
        v.addWidget(self.group)
        self.capture = QCheckBox(t("capture_edit") if editing else t("capture_new"))
        if not editing:
            self.capture.setChecked(True)
            self.capture.setEnabled(False)
        v.addWidget(self.capture)
        tip = QLabel(t("editor_tip"))
        tip.setWordWrap(True)
        tip.setStyleSheet("color:#888;")
        v.addWidget(tip)
        v.addLayout(_ok_cancel(self))

    def values(self):
        rid, rtype = self.group.currentData()
        return {"name": self.name.text().strip() or t("scene_default"),
                "group_rid": rid, "group_rtype": rtype,
                "capture": self.capture.isChecked()}


class GroupEditor(QDialog):
    """Create or edit a room or a zone.

    Both are CLIP group resources and differ only in what they hold: a room
    holds devices and mirrors the physical setup (a lamp is in exactly one
    room), a zone holds individual lights and zones may overlap. Same dialog,
    different member list - the hint spells the difference out, because
    confusing the two is the easiest mistake to make here.

    members: (rid, label) pairs the group may contain, already ordered.
    """

    def __init__(self, members, rtype, group=None, parent=None):
        super().__init__(parent)
        self.rtype = rtype
        room = rtype == "room"
        editing = group is not None
        if editing:
            self.setWindowTitle(t("title_edit_room") if room else t("title_edit_zone"))
        else:
            self.setWindowTitle(t("title_new_room") if room else t("title_new_zone"))
        self.setMinimumWidth(360)
        self.resize(360, 480)
        v = QVBoxLayout(self)
        v.setSpacing(8)

        hint = QLabel(t("room_hint") if room else t("zone_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#8b909a;")
        v.addWidget(hint)

        v.addWidget(QLabel(t("name")))
        self.name = QLineEdit(name_of(group) if editing else "")
        v.addWidget(self.name)
        v.addWidget(QLabel(t("room_devices") if room else t("zone_lights")))

        # a room lists its devices, a zone its lights
        child_rtype = "device" if room else "light"
        member_ids = {c["rid"] for c in (group or {}).get("children", [])
                      if c["rtype"] == child_rtype}
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        holder = QWidget()
        hv = QVBoxLayout(holder)
        hv.setSpacing(4)
        self.checks = []
        for rid, label in members:
            cb = QCheckBox(label)
            cb.setChecked(rid in member_ids)
            cb._rid = rid
            hv.addWidget(cb)
            self.checks.append(cb)
        if not self.checks:
            empty = QLabel(t("no_members"))
            empty.setStyleSheet("color:#8b909a;")
            hv.addWidget(empty)
        hv.addStretch(1)
        scroll.setWidget(holder)
        v.addWidget(scroll, 1)
        v.addLayout(_ok_cancel(self))

    def values(self):
        default = t("room_default") if self.rtype == "room" else t("zone_default")
        return {"name": self.name.text().strip() or default,
                "member_ids": [c._rid for c in self.checks if c.isChecked()]}
