import sys
import os
import platform

SYSTEM = platform.system()


def is_admin():
    if SYSTEM == "Windows":
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    elif SYSTEM == "Linux":
        try:
            return os.geteuid() == 0
        except AttributeError:
            return False
    return False


def elevate():
    if is_admin():
        return
    exe = sys.executable
    if SYSTEM == "Windows":
        import ctypes
        params = " ".join([f'"{a}"' for a in sys.argv])
        ret = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, params, None, 1
        )
        sys.exit(0 if ret > 32 else 1)
    elif SYSTEM == "Linux":
        os.execvp("sudo", ["sudo", exe] + sys.argv)


elevate()

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from config import load_config, save_config
from backend import ClickerBackend
from hotkeys import start_hotkeys
from gui.main_window import MainWindow
from gui.overlay import Overlay


def main():
    cfg = load_config()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(True)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "icon.svg")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    backend = ClickerBackend(cfg)
    backend.start()

    window = MainWindow(backend, cfg)
    overlay = Overlay(backend)

    window.show()
    overlay.show()

    try:
        start_hotkeys(backend, cfg)
    except Exception as e:
        print(f"Горячие клавиши недоступны: {e}")

    exit_code = app.exec()

    save_config(cfg)
    backend.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()