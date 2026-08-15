import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "cps_delay": 0.1,
    "jump_tick": 0.05,
    "jump_hold": 0.05,
    "rest_interval": 60,
    "rest_duration": 10,
    "build_delay": 0.05,
    "f12_before_rest": True,
    "hotkeys": {
        "left": "U",
        "right": "I",
        "jump": "X",
        "dig": "Y",
        "run": "GRAVE",
        "build": "F6",
        "master": "F7",
    },
}


def load_config():
    cfg = {}
    for key, value in DEFAULT_CONFIG.items():
        cfg[key] = dict(value) if isinstance(value, dict) else value

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if "hotkeys" in saved and isinstance(saved["hotkeys"], dict):
                merged = dict(DEFAULT_CONFIG["hotkeys"])
                merged.update(saved["hotkeys"])
                saved["hotkeys"] = merged
            for key, value in saved.items():
                if key in cfg:
                    cfg[key] = value
        except Exception:
            pass
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass