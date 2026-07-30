# savegame.py
"""Сохранение прогресса у чекпоинта (файл save.json)."""
import json
import os

SAVE_PATH = "save.json"


def read_save(path=SAVE_PATH):
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if "x" not in data or "y" not in data:
        return None
    return data


def write_save(data, path=SAVE_PATH):
    payload = {
        "level_path": data.get("level_path") or "levels/level1.json",
        "x": float(data["x"]),
        "y": float(data["y"]),
        "health": int(data.get("health", 4)),
        "sprint_unlocked": bool(data.get("sprint_unlocked", False)),
        "dash_unlocked": bool(data.get("dash_unlocked", False)),
        "akumpower": int(data.get("akumpower", 0)),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return payload


def clear_save(path=SAVE_PATH):
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass
