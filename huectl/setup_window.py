"""Bridge pairing screen (discovery + waiting for the button press)."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
)
from PySide6.QtCore import Signal, QTimer

from .config import save_config
from .bridge import discover_bridge_ip
from .icons import make_icon
from .i18n import t
from .theme import ACCENT
from .workers import Task, PairTask


class SetupWindow(QWidget):
    paired = Signal(dict)
    cancelled = Signal()

    def __init__(self):
        super().__init__()
        self._done = False
        self._tasks = set()
        self._pair_task = None
        self.setWindowTitle(t("setup_title"))
        self.setWindowIcon(make_icon())
        self.setMinimumWidth(400)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)
        title = QLabel(t("setup_hdr"))
        title.setStyleSheet("font-size:15px;font-weight:600;")
        v.addWidget(title)
        steps = QLabel(t("setup_steps"))
        steps.setWordWrap(True)
        steps.setStyleSheet("color:#aaa;")
        v.addWidget(steps)
        row = QHBoxLayout()
        self.ip_edit = QLineEdit()
        self.ip_edit.setPlaceholderText("192.168.x.x")
        detect = QPushButton(t("detect"))
        detect.clicked.connect(self._detect)
        row.addWidget(self.ip_edit, 1)
        row.addWidget(detect)
        v.addLayout(row)
        self.pair_btn = QPushButton(t("pair"))
        self.pair_btn.setStyleSheet(
            f"background:{ACCENT};color:#16181d;font-weight:700;padding:7px;")
        self.pair_btn.clicked.connect(self._start_pairing)
        v.addWidget(self.pair_btn)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        self.status.setStyleSheet("color:#888;")
        v.addWidget(self.status)
        QTimer.singleShot(150, self._detect)

    def _keep(self, tk):
        self._tasks.add(tk)
        tk.finished.connect(lambda: self._tasks.discard(tk))

    def _detect(self):
        self.status.setText(t("searching"))
        tk = Task(discover_bridge_ip)
        tk.done.connect(self._detected)
        tk.failed.connect(lambda _e: self.status.setText(t("detect_fail")))
        self._keep(tk)
        tk.start()

    def _detected(self, ip):
        if ip:
            self.ip_edit.setText(ip)
            self.status.setText(t("found", ip=ip))
        else:
            self.status.setText(t("none_found"))

    def _start_pairing(self):
        ip = self.ip_edit.text().strip()
        if not ip:
            self.status.setText(t("enter_ip"))
            return
        self.pair_btn.setEnabled(False)
        self.status.setText(t("press_now"))
        self._pair_task = PairTask(ip)
        self._pair_task.progress.connect(lambda s: self.status.setText(t("waiting", s=s)))
        self._pair_task.paired.connect(self._ok)
        self._pair_task.failed.connect(self._fail)
        self._pair_task.start()

    def _ok(self, cfg):
        self._done = True
        save_config(cfg)
        self.paired.emit(cfg)

    def _fail(self, msg):
        self.pair_btn.setEnabled(True)
        self.status.setText(t("pair_fail", msg=msg))

    def closeEvent(self, event):
        if not self._done:
            self.cancelled.emit()
        event.accept()
