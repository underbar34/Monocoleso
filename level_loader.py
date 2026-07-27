# level_loader.py
"""Загрузка / сохранение уровней из JSON. Каталоги боссов и абилок."""
import json
import os
from platforms import Platform

DEFAULT_LEVEL_PATH = os.path.join("levels", "level1.json")

# --- каталоги (расширяются здесь) ---

BOSS_CATALOG = {
    "holodos": {
        "label": "Холодос",
        "color": (80, 160, 220),
        "sprite": "holodos1",
        "defaults": {
            "arena_x_offset": -1300,
            "min_x_offset": -1100,
            "max_x_offset": 1200,
        },
    },
}

ABILITY_CATALOG = {
    "sprint": {
        "label": "Спринт",
        "color": (156, 39, 176),
        "image": "sprint_skill",
        "key_hint": "F",
    },
    "dash": {
        "label": "Рывок",
        "color": (255, 87, 34),
        "image": "dash_skill",
        "key_hint": "R",
    },
}

# Инструменты верхнего уровня в редакторе
TOOL_CATEGORIES = (
    "platform",
    "player_spawn",
    "boss",
    "ability",
    "extra_life",
    "teleport",
    "npc",
)

OBJECT_COLORS = {
    "boss": (80, 160, 220),
    "ability": (156, 39, 176),
    "extra_life": (76, 175, 80),
    "sprint_skill": (156, 39, 176),  # legacy
    "dash_skill": (255, 87, 34),     # legacy alias
    "teleport": (0, 188, 212),
    "npc": (255, 152, 0),
    "player_spawn": (244, 67, 54),
    "platform": (120, 120, 120),
}

OBJECT_LABELS = {
    "boss": "Боссы",
    "ability": "Абилки",
    "extra_life": "Доп. жизнь",
    "sprint_skill": "Спринт",
    "dash_skill": "Рывок",
    "teleport": "Телепорт",
    "npc": "NPC",
    "player_spawn": "Спавн",
    "platform": "Платформа",
}

# Старые типы абилок → id
_LEGACY_ABILITY = {
    "sprint_skill": "sprint",
    "dash_skill": "dash",
}


def normalize_object(obj):
    """Приводит объект уровня к актуальной схеме (ability/boss с id)."""
    o = dict(obj)
    t = o.get("type")
    if t in _LEGACY_ABILITY:
        o = {
            "type": "ability",
            "id": _LEGACY_ABILITY[t],
            "x": o["x"],
            "y": o["y"],
        }
    elif t == "ability":
        o.setdefault("id", "sprint")
        if o["id"] not in ABILITY_CATALOG:
            o["id"] = "sprint"
    elif t == "boss":
        o.setdefault("id", "holodos")
        if o["id"] not in BOSS_CATALOG:
            o["id"] = "holodos"
    return o


def default_object(category, x, y, variant_id=None):
    """Создаёт объект: category = tool, variant_id — конкретный босс/абилка."""
    if category == "boss":
        bid = variant_id or next(iter(BOSS_CATALOG))
        meta = BOSS_CATALOG[bid]
        d = meta["defaults"]
        return {
            "type": "boss",
            "id": bid,
            "x": x,
            "y": y,
            "arena_x": max(0, x + d["arena_x_offset"]),
            "min_x": max(0, x + d["min_x_offset"]),
            "max_x": x + d["max_x_offset"],
        }
    if category == "ability":
        aid = variant_id or next(iter(ABILITY_CATALOG))
        if aid not in ABILITY_CATALOG:
            aid = next(iter(ABILITY_CATALOG))
        return {"type": "ability", "id": aid, "x": x, "y": y}
    if category == "extra_life":
        return {"type": "extra_life", "x": x, "y": y}
    if category == "teleport":
        return {
            "type": "teleport",
            "x": x,
            "y": y,
            "target_x": x + 200,
            "target_y": y,
        }
    if category == "npc":
        return {
            "type": "npc",
            "x": x,
            "y": y,
            "name": "NPC",
            "dialog": ["Привет!", "Нажми E, чтобы продолжить."],
        }
    # legacy direct types
    if category in _LEGACY_ABILITY:
        return default_object("ability", x, y, _LEGACY_ABILITY[category])
    raise ValueError(f"Unknown object type: {category}")


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
    data["objects"] = [normalize_object(o) for o in data.get("objects", [])]
    return data


def save_level(data, path=DEFAULT_LEVEL_PATH):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    to_save = dict(data)
    to_save["objects"] = [normalize_object(o) for o in data.get("objects", [])]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_save, f, ensure_ascii=False, indent=2)


def platforms_from_level(level):
    return [Platform(p["x"], p["y"]) for p in level.get("platforms", [])]


def objects_of_type(level, obj_type):
    return [o for o in level.get("objects", []) if o.get("type") == obj_type]


def first_object(level, obj_type):
    for o in level.get("objects", []):
        if o.get("type") == obj_type:
            return o
    return None


def ability_label(ability_id):
    return ABILITY_CATALOG.get(ability_id, {}).get("label", ability_id)


def boss_label(boss_id):
    return BOSS_CATALOG.get(boss_id, {}).get("label", boss_id)
