"""Main window: per room/zone cards, scenes, light tiles, settings."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QSlider, QCheckBox, QScrollArea, QGroupBox, QFrame,
    QToolButton, QMenu, QComboBox, QDialog, QLineEdit, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer

from .config import load_config, save_config
from .bridge import Bridge
from .color import scene_colors, light_to_action, name_of
from .icons import make_icon
from . import i18n
from .i18n import t, set_lang
from .theme import ACCENT
from .workers import Task
from .sse import EventStream
from .widgets import SceneTile, LightTile
from .dialogs import SceneEditor, ZoneEditor

MAX_COLUMNS = 8


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
        self._sse = None
        self._reload_timer = QTimer(self)
        self._reload_timer.setSingleShot(True)
        self._reload_timer.setInterval(700)
        self._reload_timer.timeout.connect(self.reload)
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
        for text, tip, slot in (
                ("+", t("add_zone_tt"), self._new_zone),
                ("\u2699", t("settings_tt"), self._open_settings),
                ("\u27f3", t("refresh_tt"), self.reload)):
            b = QPushButton(text)
            b.setFixedWidth(40)
            b.setToolTip(tip)
            b.clicked.connect(slot)
            if text == "+":
                top.addWidget(self.status, 1)
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

    def _tile_grid(self):
        grid = QGridLayout()
        grid.setSpacing(8)
        for c in range(self.columns):
            grid.setColumnStretch(c, 1)
        return grid

    def _sublabel(self, text):
        lab = QLabel(text.upper())
        lab.setStyleSheet("color:#7d828c;font-size:11px;font-weight:700;")
        return lab

    # -- build -------------------------------------------------------------
    def _build(self, data):
        self.data = data
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
                group_ref=(room["id"], "room", name_of(room))))

        for zone in zones:
            lay.addWidget(self._make_card(
                name_of(zone), self._grouped_light_id(zone),
                self._scenes_for(zone["id"]),
                self._lights_of_group(zone["id"], "zone"),
                group_ref=(zone["id"], "zone", name_of(zone)), zone_res=zone))

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

    def _make_card(self, title, gl_id, scenes, lights, group_ref=None, zone_res=None):
        box = QGroupBox(title)
        v = QVBoxLayout(box)
        v.setSpacing(8)
        if gl_id:
            v.addWidget(self._group_header(gl_id, zone_res))
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
                                   i // self.columns, i % self.columns)
                v.addLayout(grid)
        if lights:
            v.addWidget(self._sublabel(t("lights")))
            grid = self._tile_grid()
            for i, l in enumerate(sorted(lights, key=name_of)):
                tile = LightTile(l, self)
                self._light_tiles[l["id"]] = tile
                grid.addWidget(tile, i // self.columns, i % self.columns)
            v.addLayout(grid)
        return box

    def _group_header(self, gl_id, zone_res=None):
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
        if zone_res is not None:
            mb = QToolButton()
            mb.setText("\u22ef")
            mb.setToolTip(t("menu_edit_zone"))
            mb.setCursor(Qt.PointingHandCursor)
            mb.setPopupMode(QToolButton.InstantPopup)
            mb.setStyleSheet(
                "QToolButton{background:#262a31;border:1px solid #313742;"
                "border-radius:6px;color:#e6e6e6;font-size:16px;font-weight:700;"
                "padding:1px 8px;margin-left:6px;}"
                "QToolButton::menu-indicator{image:none;}"
                "QToolButton:hover{background:#2f343d;color:%s;}" % ACCENT)
            m = QMenu(mb)
            m.addAction(t("menu_edit_zone"), lambda: self._edit_zone(zone_res))
            m.addAction(t("menu_delete_zone"), lambda: self._delete_zone(zone_res))
            mb.setMenu(m)
            h.addWidget(mb)
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
        g = [(f"\u2302 {name_of(r)}", r["id"], "room") for r in self.data["room"]]
        g += [(f"\u25a6 {name_of(z)}", z["id"], "zone") for z in self.data["zone"]]
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

    # -- zones -------------------------------------------------------------
    def _new_zone(self):
        dlg = ZoneEditor(self.data.get("light", []), parent=self)
        if dlg.exec():
            self._save_zone(None, dlg.values())

    def _edit_zone(self, zone):
        dlg = ZoneEditor(self.data.get("light", []), zone=zone, parent=self)
        if dlg.exec():
            self._save_zone(zone, dlg.values())

    def _delete_zone(self, zone):
        if QMessageBox.question(self, t("del_zone_title"),
                                t("del_zone_msg", name=name_of(zone))) \
                == QMessageBox.StandardButton.Yes:
            zid = zone["id"]
            self.status.setText(t("deleting"))
            self._run(lambda: self.bridge.delete("zone", zid),
                      lambda _r: self.reload())

    def _save_zone(self, zone, vals):
        children = [{"rid": lid, "rtype": "light"} for lid in vals["light_ids"]]
        if zone is None:
            payload = {"type": "zone",
                       "metadata": {"name": vals["name"], "archetype": "other"},
                       "children": children}
            fn = lambda: self.bridge.post("zone", payload)  # noqa: E731
        else:
            zid = zone["id"]
            payload = {"metadata": {"name": vals["name"]}, "children": children}
            fn = lambda: self.bridge.put("zone", zid, payload)  # noqa: E731
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

    def closeEvent(self, event):
        if getattr(self, "_has_tray", False):
            event.ignore()
            self.hide()
        else:
            event.accept()
