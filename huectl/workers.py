"""Background threads so HTTP calls don't freeze the interface."""

import requests
from PySide6.QtCore import QThread, Signal

from .config import APP_NAME
from .i18n import t


class Task(QThread):
    """Runs a function and emits its result (or the error)."""
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, fn):
        super().__init__()
        self._fn = fn

    def run(self):
        try:
            self.done.emit(self._fn())
        except Exception as e:  # noqa: BLE001
            self.failed.emit(str(e))


class PairTask(QThread):
    """Polls the bridge until its button is pressed (or timeout)."""
    progress = Signal(int)
    paired = Signal(dict)
    failed = Signal(str)

    def __init__(self, ip, timeout=30):
        super().__init__()
        self.ip = ip
        self.timeout = timeout

    def run(self):
        payload = {"devicetype": APP_NAME, "generateclientkey": True}
        for i in range(self.timeout):
            try:
                r = requests.post(f"https://{self.ip}/api", json=payload,
                                  verify=False, timeout=5)
                res = r.json()
            except Exception as e:  # noqa: BLE001
                self.failed.emit(t("unreachable", e=e))
                return
            if isinstance(res, list) and res:
                item = res[0]
                if "success" in item:
                    s = item["success"]
                    self.paired.emit({"bridge_ip": self.ip,
                                      "app_key": s["username"],
                                      "client_key": s.get("clientkey")})
                    return
                err = item.get("error", {})
                if str(err.get("type")) != "101":   # 101 = button not pressed yet
                    self.failed.emit(err.get("description", "?"))
                    return
            self.progress.emit(self.timeout - i - 1)
            self.sleep(1)
        self.failed.emit(t("pair_timeout"))
