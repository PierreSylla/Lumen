"""Main window: per room/zone cards, scenes, light tiles, settings."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QSlider, QCheckBox, QScrollArea, QGroupBox, QFrame,
    QToolButton, QComboBox, QDialog, QLineEdit, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer, QSize

from .config import load_config, save_config
from .bridge import Bridge
from .color import scene_colors, light_to_action, name_of
from .icons import make_icon, icon_plus, icon_gear, icon_refresh, icon_edit, icon_trash
from . import i18n
from .i18n import t, set_lang
from .theme import ACCENT
from .workers import Task
from .sse import EventStream
from .widgets import SceneTile, LightTile
from .dialogs import SceneEditor, GroupEditor

MAX_COLUMNS = 8
# a light tile spends ~128px on icon, switch and margins; the rest is the name
TILE_MIN_W = 230
# card badge colors: rooms are physical, zones are free-form
BADGE_COLORS = {"room": "#7aa2f7", "zone": "#bb9af7"}


class HueWindow(QMainWindow):
    def __init__(self, bridge, controller=None):
        super().__init__()
        self.bridge = bridge
        self.controller = controller
        self.data = {}
        self._threads = set()
        self._light_tiles = {}
        self.columns = int(load_config().get("columns", 2))
        self.setWindowTitle("Lumen")
        self.setWindowIcon(make_icon())
        self.resize(560, 720)
        self.setMinimumWidth(420)      # keeps the card action row on screen
        self._cols = self.columns
        self._sse = None
        self._reload_timer = QTimer(self)
        self._reload_timer.setSingleShot(True)
        self._reload_timer.setInterval(700)
        self._reload_timer.timeout.connect(self.reload)
        self._relayout_timer = QTimer(self)
        self._relayout_timer.setSingleShot(True)
        self._relayout_timer.setInterval(150)
        self._relayout_timer.timeout.connect(lambda: self._build(self.data))
        self._rebuild()
        self.start_events()

    # -- real-time event stream -------------------------------------------
    def start_events(self):
        self._stop_events()
        self._sse = EventStream(self.bridge)
        self._sse.updated.connect(self._apply_light_updates)
        self._sse.changed.connect(self._schedule_reload)
        self._sse.start()

    def _stop_events(self):
        if getattr(self, "_sse", None):
            self._sse.stop()
            self._sse.wait(1500)
            self._sse = None

    def set_bridge(self, bridge):
        """Switch bridge (IP change / re-pair): restart stream and reload."""
        self.bridge = bridge
        self.start_events()
        self.reload()

    def _apply_light_updates(self, frags):
        for frag in frags:
            tile = self._light_tiles.get(frag.get("id"))
            if tile is None:
                continue
            for k in ("on", "dimming", "color", "color_temperature"):
                if k in frag:
                    tile.light[k] = frag[k]
            tile.refresh()

    def _schedule_reload(self):
        self._reload_timer.start()

    def _rebuild(self):
        self.columns = int(load_config().get("columns", 2))
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        top = QHBoxLayout()
        top.setContentsMargins(12, 10, 12, 4)
        self.status = QLabel("")
        self.status.setStyleSheet("color:#888;")
        top.addWidget(self.status, 1)
        # labelled add buttons: an icon-only '+' left the user unable to tell
        # (or even find) how to create a room versus a zone
        for label, tip, rtype in (
                (t("add_room"), t("add_room_tt"), "room"),
                (t("add_zone"), t("add_zone_tt"), "zone")):
            b = QPushButton(label)
            b.setIcon(icon_plus())
            b.setIconSize(QSize(15, 15))
            b.setToolTip(tip)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, r=rtype: self._new_group(r))
            top.addWidget(b)
        for ic, tip, slot in (
                (icon_gear(), t("settings_tt"), self._open_settings),
                (icon_refresh(), t("refresh_tt"), self.reload)):
            b = QPushButton()
            b.setIcon(ic)
            b.setIconSize(QSize(18, 18))
            b.setFixedWidth(40)
            b.setToolTip(tip)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(slot)
            top.addWidget(b)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        outer.addLayout(top)
        outer.addWidget(self.scroll, 1)
        self.reload()

    # -- network -----------------------------------------------------------
    def _run(self, fn, on_done=None):
        tk = Task(fn)
        if on_done:
            tk.done.connect(on_done)
        tk.failed.connect(self._error)
        tk.finished.connect(lambda: self._threads.discard(tk))
        self._threads.add(tk)
        tk.start()

    def _error(self, msg):
        self.status.setText(f"! {msg}")

    def reload(self):
        self.status.setText(t("loading"))
        self._run(self.bridge.snapshot, self._build)

    def _act(self, rtype, rid, payload):
        self.status.setText("")
        self._run(lambda: self.bridge.put(rtype, rid, payload))

    # -- helpers -----------------------------------------------------------
    def _grouped_light_id(self, res):
        return next((s["rid"] for s in res.get("services", [])
                     if s["rtype"] == "grouped_light"), None)

    def _lights_of_group(self, rid, rtype):
        by_id = {l["id"]: l for l in self.data["light"]}
        by_owner = {}
        for l in self.data["light"]:
            by_owner.setdefault((l.get("owner") or {}).get("rid"), []).append(l)
        res = next((x for x in self.data.get(rtype, []) if x["id"] == rid), None)
        if not res:
            return []
        out = []
        for child in res.get("children", []):
            if child["rtype"] == "light" and child["rid"] in by_id:
                out.append(by_id[child["rid"]])
            elif child["rtype"] == "device":
                out.extend(by_owner.get(child["rid"], []))
        return out

    def _scenes_for(self, gid):
        return [s for s in self.data["scene"]
                if s.get("group", {}).get("rid") == gid]

    def _fit_columns(self):
        """Columns that actually fit: the setting is a maximum, not a promise.

        Honouring it literally on a narrow window makes the cards wider than
        the viewport, which pushes the right-aligned card actions off screen.

        Measured on the scroll area, not its viewport: the viewport width moves
        with the scrollbar, and a re-flow that toggles the scrollbar would flip
        the count back and turn this into an endless rebuild loop.
        """
        avail = self.scroll.width() - 44     # card padding, margins, scrollbar
        return max(1, min(self.columns, avail // TILE_MIN_W))

    def _tile_grid(self):
        grid = QGridLayout()
        grid.setSpacing(8)
        for c in range(self._cols):
            grid.setColumnStretch(c, 1)
        return grid

    def _sublabel(self, text):
        lab = QLabel(text.upper())
        lab.setStyleSheet("color:#7d828c;font-size:11px;font-weight:700;")
        return lab

    # -- build -------------------------------------------------------------
    def _build(self, data):
        self.data = data
        self._cols = self._fit_columns()
        self._light_tiles = {}
        self.status.setText("")
        body = QWidget()
        lay = QVBoxLayout(body)
        lay.setContentsMargins(12, 4, 12, 14)
        lay.setSpacing(12)

        assigned = set()
        rooms = sorted(self.data["room"], key=name_of)
        zones = sorted(self.data["zone"], key=name_of)
        known = {r["id"] for r in rooms} | {z["id"] for z in zones}
        in_zone = set()
        for z in zones:
            for l in self._lights_of_group(z["id"], "zone"):
                in_zone.add(l["id"])

        for room in rooms:
            lights = self._lights_of_group(room["id"], "room")
            for l in lights:
                assigned.add(l["id"])
            lay.addWidget(self._make_card(
                name_of(room), self._grouped_light_id(room),
                self._scenes_for(room["id"]), lights,
                group_ref=(room["id"], "room", name_of(room)),
                res=room, rtype="room"))

        for zone in zones:
            lay.addWidget(self._make_card(
                name_of(zone), self._grouped_light_id(zone),
                self._scenes_for(zone["id"]),
                self._lights_of_group(zone["id"], "zone"),
                group_ref=(zone["id"], "zone", name_of(zone)),
                res=zone, rtype="zone"))

        orphan_lights = [l for l in self.data["light"]
                         if l["id"] not in assigned and l["id"] not in in_zone]
        if orphan_lights:
            lay.addWidget(self._make_card(t("others"), None, [], orphan_lights))

        orphan_scenes = [s for s in self.data["scene"]
                         if s.get("group", {}).get("rid") not in known]
        if orphan_scenes:
            lay.addWidget(self._make_card(t("other_scenes"), None, orphan_scenes, []))

        lay.addStretch(1)
        self.scroll.setWidget(body)

    def _make_card(self, title, gl_id, scenes, lights, group_ref=None,
                   res=None, rtype=None):
        box = QGroupBox(title)
        v = QVBoxLayout(box)
        v.setSpacing(8)
        if res is not None:
            v.addLayout(self._group_actions(res, rtype))
        if gl_id:
            v.addWidget(self._group_header(gl_id))
        if group_ref or scenes:
            head = QHBoxLayout()
            head.addWidget(self._sublabel(t("scenes")), 1)
            if group_ref:
                add = QToolButton()
                add.setText("+")
                add.setToolTip(t("new_scene_tt"))
                add.setCursor(Qt.PointingHandCursor)
                add.setStyleSheet(
                    "QToolButton{background:#262a31;border:1px solid #313742;"
                    "border-radius:6px;padding:2px 8px;font-weight:700;}"
                    "QToolButton:hover{background:#2f343d;}")
                add.clicked.connect(lambda _=False, g=group_ref: self._new_scene_for(*g))
                head.addWidget(add)
            v.addLayout(head)
            if scenes:
                grid = self._tile_grid()
                cb = {"activate": self._activate_scene,
                      "edit": self._edit_scene, "delete": self._delete_scene}
                for i, s in enumerate(sorted(scenes, key=name_of)):
                    grid.addWidget(SceneTile(s, scene_colors(s), cb),
                                   i // self._cols, i % self._cols)
                v.addLayout(grid)
        if lights:
            v.addWidget(self._sublabel(t("lights")))
            grid = self._tile_grid()
            for i, l in enumerate(sorted(lights, key=name_of)):
                tile = LightTile(l, self)
                self._light_tiles[l["id"]] = tile
                grid.addWidget(tile, i // self._cols, i % self._cols)
            v.addLayout(grid)
        return box

    def _badge(self, rtype):
        """Small ROOM / ZONE tag - the two are easy to mix up, so label them."""
        col = BADGE_COLORS[rtype]
        lab = QLabel(t("badge_room") if rtype == "room" else t("badge_zone"))
        lab.setStyleSheet(
            f"color:{col};border:1px solid {col};border-radius:4px;"
            "padding:1px 6px;font-size:10px;font-weight:700;")
        return lab

    def _group_actions(self, res, rtype):
        """Type badge + Edit/Delete, identical for rooms and zones.

        Its own row with text labels on purpose: these actions must not depend
        on a symbol font, nor share space with the group slider.
        """
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 2)
        row.setSpacing(6)
        row.addWidget(self._badge(rtype))
        row.addStretch(1)
        base = ("QPushButton{{background:#22262e;border:1px solid #2f3540;"
                "border-radius:6px;padding:3px 10px;font-size:12px;color:{c};}}"
                "QPushButton:hover{{background:{bg};color:{hc};}}")
        for label, ic, slot, style in (
                (t("edit_btn"), icon_edit(),
                 lambda: self._edit_group(res, rtype),
                 base.format(c="#aab0ba", bg="#2b3039", hc="#e6e6e6")),
                (t("delete_btn"), icon_trash(),
                 lambda: self._delete_group(res, rtype),
                 base.format(c="#c9737c", bg="#3a1f22", hc="#e06c75"))):
            b = QPushButton(label)
            b.setIcon(ic)
            b.setIconSize(QSize(14, 14))
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(style)
            b.clicked.connect(slot)
            row.addWidget(b)
        return row

    def _group_header(self, gl_id):
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 4)
        chk = QCheckBox(t("all_group"))
        chk.setStyleSheet("font-weight:600;color:#cfd3da;")
        chk.clicked.connect(
            lambda on, i=gl_id: self._act("grouped_light", i, {"on": {"on": on}}))
        h.addWidget(chk, 1)
        sl = QSlider(Qt.Horizontal)
        sl.setRange(0, 100)
        sl.setFixedWidth(130)
        sl.sliderReleased.connect(
            lambda s=sl, i=gl_id: self._act(
                "grouped_light", i, {"on": {"on": s.value() > 0},
                                     "dimming": {"brightness": float(s.value())}}))
        h.addWidget(sl)
        return row

    # -- scenes ------------------------------------------------------------
    def _activate_scene(self, scene):
        sid = scene["id"]
        self.status.setText(t("scene_activated", name=name_of(scene)))
        # only refresh the light states (no rebuild -> no scroll jump)
        self._run(lambda: self.bridge.put("scene", sid, {"recall": {"action": "active"}}),
                  lambda _r: QTimer.singleShot(600, self._refresh_lights_only))

    def _refresh_lights_only(self):
        self._run(lambda: self.bridge.get("light"), self._apply_light_states)

    def _apply_light_states(self, lights):
        self.data["light"] = lights
        for l in lights:
            tile = self._light_tiles.get(l["id"])
            if tile is not None:
                tile.light = l
                tile.refresh()

    def _all_groups(self):
        g = [(name_of(r), r["id"], "room") for r in self.data["room"]]
        g += [(name_of(z), z["id"], "zone") for z in self.data["zone"]]
        return g

    def _new_scene_for(self, rid, rtype, label):
        dlg = SceneEditor([(label, rid, rtype)], parent=self)
        if dlg.exec():
            self._save_scene(None, dlg.values())

    def _edit_scene(self, scene):
        dlg = SceneEditor(self._all_groups(), scene=scene, parent=self)
        if dlg.exec():
            self._save_scene(scene, dlg.values())

    def _delete_scene(self, scene):
        if QMessageBox.question(self, t("del_scene_title"),
                                t("del_scene_msg", name=name_of(scene))) \
                == QMessageBox.StandardButton.Yes:
            sid = scene["id"]
            self.status.setText(t("deleting"))
            self._run(lambda: self.bridge.delete("scene", sid),
                      lambda _r: self.reload())

    def _save_scene(self, scene, vals):
        if scene is None:
            rid, rtype = vals["group_rid"], vals["group_rtype"]
        else:
            g = scene.get("group", {})
            rid, rtype = g.get("rid"), g.get("rtype")
        actions = None
        if scene is None or vals["capture"]:
            actions = [light_to_action(l) for l in self._lights_of_group(rid, rtype)]
            if not actions:
                self.status.setText(t("no_lamp_group"))
                return
        if scene is None:
            payload = {"type": "scene", "metadata": {"name": vals["name"]},
                       "group": {"rid": rid, "rtype": rtype}, "actions": actions}
            fn = lambda: self.bridge.post("scene", payload)  # noqa: E731
        else:
            payload = {"metadata": {"name": vals["name"]}}
            if actions is not None:
                payload["actions"] = actions
            sid = scene["id"]
            fn = lambda: self.bridge.put("scene", sid, payload)  # noqa: E731
        self.status.setText(t("saving"))
        self._run(fn, lambda _r: self.reload())

    # -- rooms and zones ---------------------------------------------------
    def _members_for(self, rtype):
        """(rid, label) pairs a group of this kind may contain.

        Zones take lights; rooms take devices, and since the bridge allows a
        device in only one room, the label says which room already holds it.
        """
        if rtype == "zone":
            return [(l["id"], name_of(l))
                    for l in sorted(self.data.get("light", []), key=name_of)]
        home = {c["rid"]: name_of(r) for r in self.data.get("room", [])
                for c in r.get("children", []) if c["rtype"] == "device"}
        out = []
        for d in sorted(self.data.get("device", []), key=name_of):
            if not any(s["rtype"] == "light" for s in d.get("services", [])):
                continue        # bridge, dimmer switch, sensors: not lamps
            room = home.get(d["id"])
            out.append((d["id"], t("member_in_room", name=name_of(d), room=room)
                        if room else name_of(d)))
        return out

    def _new_group(self, rtype):
        dlg = GroupEditor(self._members_for(rtype), rtype, parent=self)
        if dlg.exec():
            self._save_group(None, rtype, dlg.values())

    def _edit_group(self, res, rtype):
        dlg = GroupEditor(self._members_for(rtype), rtype, group=res, parent=self)
        if dlg.exec():
            self._save_group(res, rtype, dlg.values())

    def _delete_group(self, res, rtype):
        room = rtype == "room"
        title = t("del_room_title") if room else t("del_zone_title")
        msg = (t("del_room_msg", name=name_of(res)) if room
               else t("del_zone_msg", name=name_of(res)))
        if QMessageBox.question(self, title, msg) \
                == QMessageBox.StandardButton.Yes:
            rid = res["id"]
            self.status.setText(t("deleting"))
            self._run(lambda: self.bridge.delete(rtype, rid),
                      lambda _r: self.reload())

    def _save_group(self, res, rtype, vals):
        child_rtype = "device" if rtype == "room" else "light"
        children = [{"rid": i, "rtype": child_rtype} for i in vals["member_ids"]]
        if res is None:
            payload = {"type": rtype,
                       "metadata": {"name": vals["name"], "archetype": "other"},
                       "children": children}
            fn = lambda: self.bridge.post(rtype, payload)  # noqa: E731
        else:
            rid = res["id"]
            payload = {"metadata": {"name": vals["name"]}, "children": children}
            fn = lambda: self.bridge.put(rtype, rid, payload)  # noqa: E731
        self.status.setText(t("saving"))
        self._run(fn, lambda _r: self.reload())

    # -- settings ----------------------------------------------------------
    def _open_settings(self):
        cfg = load_config()
        dlg = QDialog(self)
        dlg.setWindowTitle(t("settings_title"))
        dlg.setMinimumWidth(400)
        v = QVBoxLayout(dlg)
        v.setSpacing(10)

        hdr = QLabel(t("bridge_hdr"))
        hdr.setStyleSheet("font-size:15px;font-weight:600;")
        v.addWidget(hdr)
        info = QLabel(t("ip_info"))
        info.setWordWrap(True)
        info.setStyleSheet("color:#888;")
        v.addWidget(info)
        row = QHBoxLayout()
        ip = QLineEdit(cfg.get("bridge_ip", ""))
        save_ip = QPushButton(t("save"))
        save_ip.clicked.connect(lambda: (self.controller.set_ip(ip.text()), dlg.accept()))
        row.addWidget(ip, 1)
        row.addWidget(save_ip)
        v.addLayout(row)
        repair = QPushButton(t("repair_btn"))
        repair.clicked.connect(lambda: (dlg.accept(), self.controller.repair()))
        v.addWidget(repair)
        disc = QPushButton(t("disconnect_btn"))
        disc.setStyleSheet("background:#3a1f22;border-color:#5a2a2f;")

        def _disc():
            if QMessageBox.question(dlg, t("disconnect_title"), t("disconnect_msg")) \
                    == QMessageBox.StandardButton.Yes:
                dlg.accept()
                self.controller.disconnect_bridge()
        disc.clicked.connect(_disc)
        v.addWidget(disc)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color:#2a2f38;")
        v.addWidget(sep)
        ah = QLabel(t("appearance_hdr"))
        ah.setStyleSheet("font-size:15px;font-weight:600;")
        v.addWidget(ah)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel(t("columns_label")), 1)
        cols = QComboBox()
        for n in range(1, MAX_COLUMNS + 1):
            cols.addItem(str(n), n)
        cols.setCurrentText(str(cfg.get("columns", 2)))
        r2.addWidget(cols)
        v.addLayout(r2)

        r3 = QHBoxLayout()
        r3.addWidget(QLabel(t("language_label")), 1)
        lang = QComboBox()
        lang.addItem("English", "en")
        lang.addItem("Francais", "fr")
        lang.setCurrentIndex(0 if i18n.LANG == "en" else 1)
        r3.addWidget(lang)
        v.addLayout(r3)

        startmin = QCheckBox(t("start_min_label"))
        startmin.setChecked(bool(cfg.get("start_minimized", False)))
        v.addWidget(startmin)

        def _apply():
            save_config({"columns": cols.currentData(),
                         "language": lang.currentData(),
                         "start_minimized": startmin.isChecked()})
            set_lang(lang.currentData())
            dlg.accept()
            self._rebuild()
        ok = QPushButton(t("save"))
        ok.setStyleSheet(f"background:{ACCENT};color:#16181d;font-weight:700;")
        ok.clicked.connect(_apply)
        v.addWidget(ok, 0, Qt.AlignRight)
        dlg.exec()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # re-flow only when the fitting column count actually changed
        if self.data and self._fit_columns() != self._cols:
            self._relayout_timer.start()

    def closeEvent(self, event):
        if getattr(self, "_has_tray", False):
            event.ignore()
            self.hide()
        else:
            event.accept()
