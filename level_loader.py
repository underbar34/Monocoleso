# level_loader.py
"""Загрузка / сохранение уровней из JSON."""
import json
import os
from platforms import Platform

DEFAULT_LEVEL_PATH = os.path.join("levels", "level1.json")

OBJECT_TYPES = (
    "boss",
    "extra_life",
    "sprint_skill",
    "teleport",
    "npc",
)

OBJECT_COLORS = {
    "boss": (80, 160, 220),
    "extra_life": (76, 175, 80),
    "sprint_skill": (156, 39, 176),
    "teleport": (0, 188, 212),
    "npc": (255, 152, 0),
    "player_spawn": (244, 67, 54),
    "platform": (120, 120, 120),
}

OBJECT_LABELS = {
    "boss": "Босс",
    "extra_life": "Доп. жизнь",
    "sprint_skill": "Спринт",
    "teleport": "Телепорт",
    "npc": "NPC",
    "player_spawn": "Спавн",
    "platform": "Платформа",
}


def default_object(obj_type, x, y):
    """Создаёт объект с полями по умолчанию."""
    if obj_type == "boss":
        return {
            "type": "boss",
            "x": x,
            "y": y,
            "arena_x": max(0, x - 1300),
            "min_x": max(0, x - 1100),
            "max_x": x + 1200,
        }
    if obj_type == "extra_life":
        return {"type": "extra_life", "x": x, "y": y}
    if obj_type == "sprint_skill":
        return {"type": "sprint_skill", "x": x, "y": y}
    if obj_type == "teleport":
        return {
            "type": "teleport",
            "x": x,
            "y": y,
            "target_x": x + 200,
            "target_y": y,
        }
    if obj_type == "npc":
        return {
            "type": "npc",
            "x": x,
            "y": y,
            "name": "NPC",
            "dialog": ["Привет!", "Нажми E, чтобы продолжить."],
        }
    raise ValueError(f"Unknown object type: {obj_type}")


def empty_level(name="level1", world_width=6200, ground_y=726):
    return {
        "name": name,
        "world_width": world_width,
        "ground_y": ground_y,
        "player_spawn": {"x": 120, "y": 640},
        "platforms": [],
        "objects": [],
    }


def load_level(path=DEFAULT_LEVEL_PATH):
    if not os.path.exists(path):
        return empty_level()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("name", "level")
    data.setdefault("world_width", 6200)
    data.setdefault("ground_y", 726)
    data.setdefault("player_spawn", {"x": 120, "y": 640})
    data.setdefault("platforms", [])
    data.setdefault("objects", [])
    return data


def save_level(data, path=DEFAULT_LEVEL_PATH):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def platforms_from_level(level):
    return [Platform(p["x"], p["y"]) for p in level.get("platforms", [])]


def objects_of_type(level, obj_type):
    return [o for o in level.get("objects", []) if o.get("type") == obj_type]


def first_object(level, obj_type):
    for o in level.get("objects", []):
        if o.get("type") == obj_type:
            return o
    return None
