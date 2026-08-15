import threading
import time
import platform
from PySide6.QtCore import QObject, Signal

SYSTEM = platform.system()

MODE_LABELS = {
    "left": "ЛКМ",
    "right": "ПКМ",
    "jump": "Jump+Click",
    "dig": "Копание",
    "run": "Автобег",
    "build": "Стройка",
}


class ClickerBackend(QObject):
    state_changed = Signal(str, bool)
    timer_updated = Signal(str)
    master_changed = Signal(bool)
    log_message = Signal(str)

    MODES = ["left", "right", "jump", "dig", "run", "build"]

    def __init__(self, config):
        super().__init__()
        self.cfg = config
        self.state = {m: False for m in self.MODES}
        self.lock = threading.Lock()
        self.running = True
        self.master_on = True

        self.api = None
        self.con = None
        self.mouse_ui = None
        self.kbd_ui = None
        self.ecodes = None

        if SYSTEM == "Windows":
            import win32api
            import win32con
            self.api = win32api
            self.con = win32con
        elif SYSTEM == "Linux":
            from evdev import UInput, ecodes
            self.ecodes = ecodes
            try:
                mouse_caps = {ecodes.EV_KEY: [
                    ecodes.BTN_LEFT, ecodes.BTN_RIGHT, ecodes.BTN_MIDDLE
                ]}
                self.mouse_ui = UInput(mouse_caps, name="mcsoft-mouse")
            except Exception:
                self.mouse_ui = None
            try:
                kbd_caps = {ecodes.EV_KEY: [
                    ecodes.KEY_SPACE, ecodes.KEY_W,
                    ecodes.KEY_LEFTCTRL, ecodes.KEY_F12
                ]}
                self.kbd_ui = UInput(kbd_caps, name="mcsoft-keyboard")
            except Exception:
                self.kbd_ui = None

    def _click(self, button):
        try:
            if SYSTEM == "Windows":
                if button == "left":
                    self.api.mouse_event(self.con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                    time.sleep(0.02)
                    self.api.mouse_event(self.con.MOUSEEVENTF_LEFTUP, 0, 0)
                else:
                    self.api.mouse_event(self.con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                    time.sleep(0.02)
                    self.api.mouse_event(self.con.MOUSEEVENTF_RIGHTUP, 0, 0)
            elif SYSTEM == "Linux" and self.mouse_ui is not None:
                ec = self.ecodes
                btn = ec.BTN_LEFT if button == "left" else ec.BTN_RIGHT
                self.mouse_ui.write(ec.EV_KEY, btn, 1)
                self.mouse_ui.syn()
                time.sleep(0.02)
                self.mouse_ui.write(ec.EV_KEY, btn, 0)
                self.mouse_ui.syn()
        except Exception:
            pass

    def _press_key(self, vk_win, ec_linux):
        try:
            if SYSTEM == "Windows":
                self.api.keybd_event(vk_win, 0, 0, 0)
                time.sleep(self.cfg.get("jump_hold", 0.05))
                self.api.keybd_event(vk_win, 0, self.con.KEYEVENTF_KEYUP, 0)
            elif SYSTEM == "Linux" and self.kbd_ui is not None:
                ec = self.ecodes
                self.kbd_ui.write(ec.EV_KEY, ec_linux, 1)
                self.kbd_ui.syn()
                time.sleep(self.cfg.get("jump_hold", 0.05))
                self.kbd_ui.write(ec.EV_KEY, ec_linux, 0)
                self.kbd_ui.syn()
        except Exception:
            pass

    def _hold_key(self, vk_win, ec_linux, active):
        try:
            if SYSTEM == "Windows":
                if active:
                    self.api.keybd_event(vk_win, 0, 0, 0)
                else:
                    self.api.keybd_event(vk_win, 0, self.con.KEYEVENTF_KEYUP, 0)
            elif SYSTEM == "Linux" and self.kbd_ui is not None:
                ec = self.ecodes
                self.kbd_ui.write(ec.EV_KEY, ec_linux, 1 if active else 0)
                self.kbd_ui.syn()
        except Exception:
            pass

    def _hold_mouse(self, button, active):
        try:
            if SYSTEM == "Windows":
                if button == "left":
                    flag = self.con.MOUSEEVENTF_LEFTDOWN if active else self.con.MOUSEEVENTF_LEFTUP
                else:
                    flag = self.con.MOUSEEVENTF_RIGHTDOWN if active else self.con.MOUSEEVENTF_RIGHTUP
                self.api.mouse_event(flag, 0, 0)
            elif SYSTEM == "Linux" and self.mouse_ui is not None:
                ec = self.ecodes
                btn = ec.BTN_LEFT if button == "left" else ec.BTN_RIGHT
                self.mouse_ui.write(ec.EV_KEY, btn, 1 if active else 0)
                self.mouse_ui.syn()
        except Exception:
            pass

    def toggle(self, mode):
        if not self.master_on:
            return self.state.get(mode, False)
        with self.lock:
            self.state[mode] = not self.state[mode]
            s = self.state[mode]
        self.state_changed.emit(mode, s)
        label = MODE_LABELS.get(mode, mode)
        status = "ВКЛ" if s else "ВЫКЛ"
        self.log_message.emit(f"{label}: {status}")
        return s

    def toggle_master(self):
        self.master_on = not self.master_on
        self.master_changed.emit(self.master_on)
        status = "ВКЛ" if self.master_on else "ВЫКЛ"
        self.log_message.emit(f"Мастер: {status}")
        return self.master_on

    def dual_loop(self):
        right_start = time.time()
        resting = False
        while self.running:
            if not self.master_on:
                self.timer_updated.emit("")
                time.sleep(0.1)
                continue
            with self.lock:
                dl = self.state["left"]
                dr = self.state["right"]
            clicked = False
            if dl:
                self._click("left")
                clicked = True
            if dr:
                now = time.time()
                if not resting:
                    rem = self.cfg.get("rest_interval", 60) - (now - right_start)
                    if rem <= 0:
                        if self.cfg.get("f12_before_rest", True):
                            if SYSTEM == "Windows":
                                self._press_key(0x7B, None)
                            else:
                                self._press_key(None, self.ecodes.KEY_F12)
                        resting = True
                        right_start = now
                        self.timer_updated.emit("Отдых...")
                    else:
                        self._click("right")
                        clicked = True
                        self.timer_updated.emit(f"Работа: {int(rem)}с")
                else:
                    rem = self.cfg.get("rest_duration", 10) - (now - right_start)
                    if rem <= 0:
                        resting = False
                        right_start = now
                        self.timer_updated.emit("")
                    else:
                        self.timer_updated.emit(f"Отдых: {int(rem)}с")
            else:
                if not resting:
                    self.timer_updated.emit("")
            time.sleep(self.cfg.get("cps_delay", 0.1) if clicked else 0.05)

    def jump_loop(self):
        ec = self.ecodes
        while self.running:
            if not self.master_on:
                time.sleep(0.1)
                continue
            with self.lock:
                do = self.state["jump"]
            if do:
                if SYSTEM == "Windows":
                    self._press_key(0x20, None)
                else:
                    self._press_key(None, ec.KEY_SPACE)
                time.sleep(self.cfg.get("jump_tick", 0.05))
                self._click("left")
                time.sleep(0.1)
            else:
                time.sleep(0.05)

    def dig_loop(self):
        was_digging = False
        while self.running:
            if not self.master_on:
                if was_digging:
                    self._hold_mouse("left", False)
                    was_digging = False
                time.sleep(0.1)
                continue
            with self.lock:
                do = self.state["dig"]
            if do and not was_digging:
                self._hold_mouse("left", True)
                was_digging = True
            elif not do and was_digging:
                self._hold_mouse("left", False)
                was_digging = False
            time.sleep(0.02)
        if was_digging:
            self._hold_mouse("left", False)

    def run_loop(self):
        ec = self.ecodes
        was_running = False
        VK_W, VK_CTRL = 0x57, 0xA2
        while self.running:
            if not self.master_on:
                if was_running:
                    if SYSTEM == "Windows":
                        self._hold_key(VK_W, None, False)
                        self._hold_key(VK_CTRL, None, False)
                    else:
                        self._hold_key(None, ec.KEY_W, False)
                        self._hold_key(None, ec.KEY_LEFTCTRL, False)
                    was_running = False
                time.sleep(0.1)
                continue
            with self.lock:
                do = self.state["run"]
            if do and not was_running:
                if SYSTEM == "Windows":
                    self._hold_key(VK_CTRL, None, True)
                    time.sleep(0.02)
                    self._hold_key(VK_W, None, True)
                else:
                    self._hold_key(None, ec.KEY_LEFTCTRL, True)
                    time.sleep(0.02)
                    self._hold_key(None, ec.KEY_W, True)
                was_running = True
            elif not do and was_running:
                if SYSTEM == "Windows":
                    self._hold_key(VK_W, None, False)
                    time.sleep(0.02)
                    self._hold_key(VK_CTRL, None, False)
                else:
                    self._hold_key(None, ec.KEY_W, False)
                    time.sleep(0.02)
                    self._hold_key(None, ec.KEY_LEFTCTRL, False)
                was_running = False
            time.sleep(0.02)
        if was_running:
            if SYSTEM == "Windows":
                self._hold_key(VK_W, None, False)
                self._hold_key(VK_CTRL, None, False)
            else:
                self._hold_key(None, ec.KEY_W, False)
                self._hold_key(None, ec.KEY_LEFTCTRL, False)

    def build_loop(self):
        ec = self.ecodes
        while self.running:
            if not self.master_on:
                time.sleep(0.1)
                continue
            with self.lock:
                do = self.state["build"]
            if do:
                if SYSTEM == "Windows":
                    self._press_key(0x20, None)
                else:
                    self._press_key(None, ec.KEY_SPACE)
                time.sleep(self.cfg.get("build_delay", 0.05))
                self._click("right")
                time.sleep(0.1)
            else:
                time.sleep(0.05)

    def start(self):
        loops = [
            self.dual_loop,
            self.jump_loop,
            self.dig_loop,
            self.run_loop,
            self.build_loop,
        ]
        for loop in loops:
            threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
        if SYSTEM == "Linux":
            if self.mouse_ui is not None:
                try:
                    self.mouse_ui.close()
                except Exception:
                    pass
            if self.kbd_ui is not None:
                try:
                    self.kbd_ui.close()
                except Exception:
                    pass