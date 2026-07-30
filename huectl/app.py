"""Application orchestration: window, system tray, pairing, settings."""

import os
import sys

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QAction

from .config import CONFIG_PATH, load_config, save_config
from .bridge import Bridge, load_bridge
from .icons import make_icon
from .i18n import t, set_lang
from .theme import theme
from .window import HueWindow
from .setup_window import SetupWindow


class HueApp:
    def __init__(self, start_hidden=False):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("lumen")
        cfg = load_config()
        set_lang(cfg.get("language", "en"))  # English by default
        self.app.setStyleSheet(theme())
        self.app.setQuitOnLastWindowClosed(False)
        self.app.aboutToQuit.connect(self._cleanup)
        # normal launch -> UI shown + tray ; --tray or setting -> minimized
        self.start_hidden = start_hidden or bool(cfg.get("start_minimized", False))
        self.win = None
        self.tray = None
        self.setup = None
        bridge = load_bridge()
        if bridge is None:
            self._show_setup()
        else:
            self._start_main(bridge)

    # -- pairing -----------------------------------------------------------
    def _show_setup(self):
        self.setup = SetupWindow()
        self.setup.paired.connect(self._on_paired)
        self.setup.cancelled.connect(self._on_setup_cancelled)
        self.setup.show()

    def _on_setup_cancelled(self):
        self.setup = None
        if self.win is None:
            self.app.quit()

    def _on_paired(self, cfg):
        bridge = Bridge(cfg["bridge_ip"], cfg["app_key"])
        if self.setup:
            self.setup.close()
            self.setup = None
        if self.win is None:
            self._start_main(bridge, show=True)
        else:
            self.win.set_bridge(bridge)
            if not self.win.isVisible():
                self._toggle_window()

    def _start_main(self, bridge, show=False):
        self.win = HueWindow(bridge, controller=self)
        self._setup_tray()
        if show or not self.start_hidden or not self.win._has_tray:
            self.win.show()

    # -- settings actions --------------------------------------------------
    def set_ip(self, ip):
        ip = (ip or "").strip()
        if not ip or self.win is None:
            return
        save_config({"bridge_ip": ip})
        self.win.set_bridge(Bridge(ip, load_config().get("app_key")))

    def repair(self):
        self._reconfigure()

    def disconnect_bridge(self):
        try:
            os.remove(CONFIG_PATH)
        except OSError:
            pass
        if self.tray:
            self.tray.hide()
            self.tray = None
        if self.win:
            self.win._stop_events()
            self.win._has_tray = False
            self.win.hide()
            self.win.deleteLater()
            self.win = None
        self._show_setup()

    # -- tray --------------------------------------------------------------
    def _setup_tray(self):
        self.win._has_tray = QSystemTrayIcon.isSystemTrayAvailable()
        if not self.win._has_tray:
            return
        self.tray = QSystemTrayIcon(make_icon(), self.app)
        self.tray.setToolTip(t("tray_tt"))
        menu = QMenu()
        a_open = QAction(t("tray_open"), self.app)
        a_open.triggered.connect(self._toggle_window)
        a_ref = QAction(t("tray_refresh"), self.app)
        a_ref.triggered.connect(lambda: self.win.reload())
        a_cfg = QAction(t("tray_config"), self.app)
        a_cfg.triggered.connect(lambda: self.win._open_settings())
        a_quit = QAction(t("tray_quit"), self.app)
        a_quit.triggered.connect(self.app.quit)
        for a in (a_open, a_ref):
            menu.addAction(a)
        menu.addSeparator()
        for a in (a_cfg, a_quit):
            menu.addAction(a)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray)
        self.tray.show()

    def _on_tray(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._toggle_window()

    def _toggle_window(self):
        if self.win.isVisible():
            self.win.hide()
        else:
            self.win.show()
            self.win.raise_()
            self.win.activateWindow()

    def _reconfigure(self):
        if self.setup is None:
            self.setup = SetupWindow()
            self.setup.paired.connect(self._on_paired)
            self.setup.cancelled.connect(self._on_setup_cancelled)
        self.setup.show()
        self.setup.raise_()
        self.setup.activateWindow()

    def _cleanup(self):
        if self.win:
            self.win._stop_events()
        threads = set()
        if self.win:
            threads |= set(self.win._threads)
        if self.setup:
            threads |= set(self.setup._tasks)
            if self.setup._pair_task:
                threads.add(self.setup._pair_task)
        for tk in threads:
            if tk.isRunning() and not tk.wait(1000):
                tk.terminate()
                tk.wait(500)

    def run(self):
        if self.win is None and self.setup is None:
            return 0
        return self.app.exec()


def main():
    # normal launch: UI shown + tray ; --tray: start minimized
    return HueApp(start_hidden="--tray" in sys.argv).run()


if __name__ == "__main__":
    sys.exit(main())
