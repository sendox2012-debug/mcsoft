import platform
import threading

SYSTEM = platform.system()

WIN_KEY_MAP = {
    "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
    "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
    "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
    "GRAVE": 0xC0, "TILDE": 0xC0, "BACKTICK": 0xC0,
}


def _parse_win(key_str):
    if not key_str:
        return None
    upper = key_str.upper().strip()
    if upper in WIN_KEY_MAP:
        return ("vk", WIN_KEY_MAP[upper])
    if len(upper) == 1:
        return ("char", ord(upper))
    return None


def _start_windows(backend, config):
    from pynput import keyboard

    hk = config.get("hotkeys", {})
    parsed = {}
    for mode, key_str in hk.items():
        p = _parse_win(key_str)
        if p is not None:
            parsed[mode] = p

    def on_press(key):
        char = getattr(key, "char", None)
        vk = getattr(key, "vk", None)
        for mode, pair in parsed.items():
            kind, code = pair
            if mode == "master":
                matched = False
                if kind == "vk" and vk == code:
                    matched = True
                elif kind == "char" and char is not None and ord(char.upper()) == code:
                    matched = True
                if matched:
                    backend.toggle_master()
                    return
                continue
            if not backend.master_on:
                continue
            matched = False
            if kind == "vk" and vk == code:
                matched = True
            elif kind == "char" and char is not None and ord(char.upper()) == code:
                matched = True
            elif mode == "run" and char is not None and char in ("ё", "Ё", "`"):
                matched = True
            if matched:
                backend.toggle(mode)
                return

    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()
    return listener


def _start_linux(backend, config):
    from evdev import InputDevice, list_devices, ecodes

    LINUX_MAP = {
        "F1": ecodes.KEY_F1, "F2": ecodes.KEY_F2, "F3": ecodes.KEY_F3,
        "F4": ecodes.KEY_F4, "F5": ecodes.KEY_F5, "F6": ecodes.KEY_F6,
        "F7": ecodes.KEY_F7, "F8": ecodes.KEY_F8, "F9": ecodes.KEY_F9,
        "F10": ecodes.KEY_F10, "F11": ecodes.KEY_F11, "F12": ecodes.KEY_F12,
        "GRAVE": ecodes.KEY_GRAVE, "TILDE": ecodes.KEY_GRAVE,
        "A": ecodes.KEY_A, "B": ecodes.KEY_B, "C": ecodes.KEY_C,
        "D": ecodes.KEY_D, "E": ecodes.KEY_E, "F": ecodes.KEY_F,
        "G": ecodes.KEY_G, "H": ecodes.KEY_H, "I": ecodes.KEY_I,
        "J": ecodes.KEY_J, "K": ecodes.KEY_K, "L": ecodes.KEY_L,
        "M": ecodes.KEY_M, "N": ecodes.KEY_N, "O": ecodes.KEY_O,
        "P": ecodes.KEY_P, "Q": ecodes.KEY_Q, "R": ecodes.KEY_R,
        "S": ecodes.KEY_S, "T": ecodes.KEY_T, "U": ecodes.KEY_U,
        "V": ecodes.KEY_V, "W": ecodes.KEY_W, "X": ecodes.KEY_X,
        "Y": ecodes.KEY_Y, "Z": ecodes.KEY_Z,
    }

    def find_keyboard():
        for path in sorted(list_devices()):
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    if ecodes.KEY_A in keys and ecodes.KEY_SPACE in keys:
                        dev.close()
                        return path
                dev.close()
            except Exception:
                continue
        return None

    kb_path = find_keyboard()
    if kb_path is None:
        print("Клавиатура не найдена для hotkeys")
        return None

    hk = config.get("hotkeys", {})
    parsed = {}
    for mode, key_str in hk.items():
        if not key_str:
            continue
        upper = key_str.upper().strip()
        if upper in LINUX_MAP:
            parsed[mode] = LINUX_MAP[upper]

    def listener_thread():
        dev = InputDevice(kb_path)
        try:
            for event in dev.read_loop():
                if event.type == ecodes.EV_KEY and event.value == 1:
                    code = event.code
                    for mode, mapped in parsed.items():
                        if code == mapped:
                            if mode == "master":
                                backend.toggle_master()
                                break
                            if backend.master_on:
                                backend.toggle(mode)
                                break
        except Exception as e:
            print(f"Ошибка слушателя клавиатуры: {e}")

    t = threading.Thread(target=listener_thread, daemon=True)
    t.start()
    return t


def start_hotkeys(backend, config):
    if SYSTEM == "Windows":
        return _start_windows(backend, config)
    elif SYSTEM == "Linux":
        return _start_linux(backend, config)
    return None