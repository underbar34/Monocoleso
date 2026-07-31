# level_loader.py
"""Загрузка / сохранение уровней из JSON. Каталоги боссов и абилок."""
import json
import os
from platforms import Platform, Wall

LEVELS_DIR = "levels"
DEFAULT_LEVEL_PATH = os.path.join(LEVELS_DIR, "level1.json")


def list_levels(directory=LEVELS_DIR):
    """Список .json уровней (имена файлов, отсортированы)."""
    if not os.path.isdir(directory):
        return []
    names = [
        f for f in os.listdir(directory)
        if f.lower().endswith(".json") and os.path.isfile(os.path.join(directory, f))
    ]
    return sorted(names)


def resolve_level_path(name_or_path, directory=LEVELS_DIR):
    """
    Нормализует ссылку на уровень:
      level2 / level2.json / levels/level2.json → levels/level2.json
    Пустая строка / None → None (телепорт в том же уровне).
    """
    if not name_or_path:
        return None
    raw = str(name_or_path).strip().replace("\\", "/")
    if not raw:
        return None
    if raw.lower().endswith(".json"):
        base = raw
    else:
        base = raw + ".json"
    if "/" in base or base.startswith(directory):
        path = base
    else:
        path = os.path.join(directory, os.path.basename(base))
    return path.replace("\\", "/")


def level_display_name(path):
    return os.path.splitext(os.path.basename(path or ""))[0] or "?"


def create_level_file(name, directory=LEVELS_DIR, **kwargs):
    """Создаёт новый пустой уровень. name без пути, с или без .json."""
    stem = os.path.splitext(os.path.basename(str(name).strip()))[0]
    if not stem:
        raise ValueError("Пустое имя уровня")
    path = os.path.join(directory, stem + ".json")
    if os.path.exists(path):
        raise FileExistsError(path)
    data = empty_level(name=stem, **kwargs)
    save_level(data, path)
    return path

# --- каталоги (расширяются здесь) ---

BOSS_CATALOG = {
    "holodos": {
        "label": "Холодос",
        "color": (80, 160, 220),
        "sprite": "holodos1",
        "defaults": {
            "arena_x_offset": -1300,
            "arena_y_offset": 500,
            "min_x_offset": -1100,
            "max_x_offset": 1200,
        },
        "drop": {
            "coins": 10,
            "abilities": ["sprint"],
        },
        # moveset подставляется в _ensure_boss_moveset() ниже
        "moveset": None,
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
    "wall",
    "player_spawn",
    "boss",
    "ability",
    "extra_life",
    "teleport",
    "npc",
    "checkpoint",
    "enemy",
)

OBJECT_COLORS = {
    "boss": (80, 160, 220),
    "ability": (156, 39, 176),
    "extra_life": (76, 175, 80),
    "sprint_skill": (156, 39, 176),  # legacy
    "dash_skill": (255, 87, 34),     # legacy alias
    "teleport": (0, 188, 212),
    "npc": (255, 152, 0),
    "checkpoint": (255, 215, 64),
    "enemy": (200, 60, 60),
    "player_spawn": (244, 67, 54),
    "platform": (120, 120, 120),
    "wall": (90, 90, 110),
}

OBJECT_LABELS = {
    "boss": "Боссы",
    "ability": "Абилки",
    "extra_life": "Доп. жизнь",
    "sprint_skill": "Спринт",
    "dash_skill": "Рывок",
    "teleport": "Телепорт",
    "npc": "NPC",
    "checkpoint": "Сохранение",
    "enemy": "Враг",
    "player_spawn": "Спавн",
    "platform": "Платформа",
    "wall": "Стена",
}

# Старые типы абилок → id
_LEGACY_ABILITY = {
    "sprint_skill": "sprint",
    "dash_skill": "dash",
}


def _ensure_catalog_movesets():
    """Лениво подставляет дефолтный moveset Холодоса в каталог."""
    from boss_moves import default_holodos_moveset
    meta = BOSS_CATALOG.get("holodos")
    if meta is not None and not meta.get("moveset"):
        meta["moveset"] = default_holodos_moveset()


def catalog_moveset(boss_id):
    _ensure_catalog_movesets()
    return (BOSS_CATALOG.get(boss_id) or {}).get("moveset")


def normalize_object(obj):
    """Приводит объект уровня к актуальной схеме (ability/boss с id)."""
    from boss_moves import resolve_moveset, deep_copy_moveset

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
        # Текстуру босса из уровня не принимаем — только каталог спрайтов
        o.pop("texture", None)
        o.setdefault("arena_x", max(0, o.get("x", 0) - 1300))
        o.setdefault("arena_y", o.get("y", 0) + 500)
        o.setdefault("min_x", max(0, o.get("x", 0) - 1100))
        o.setdefault("max_x", o.get("x", 0) + 1200)
        cat = catalog_moveset(o["id"])
        if not o.get("moveset") and cat:
            o["moveset"] = deep_copy_moveset(cat)
        elif o.get("moveset") and cat:
            o["moveset"] = resolve_moveset(o, cat)
    elif t == "teleport":
        o.setdefault("target_x", o.get("x", 0) + 200)
        o.setdefault("target_y", o.get("y", 0))
        # "" / отсутствует = тот же уровень; иначе имя/путь другого .json
        tl = o.get("target_level")
        if tl is None:
            o["target_level"] = ""
        else:
            o["target_level"] = str(tl).strip()
    elif t == "enemy":
        o.setdefault("dir", 1)
        if int(o.get("dir", 1) or 1) >= 0:
            o["dir"] = 1
        else:
            o["dir"] = -1
    return o


def default_object(category, x, y, variant_id=None):
    """Создаёт объект: category = tool, variant_id — конкретный босс/абилка."""
    from boss_moves import deep_copy_moveset

    if category == "boss":
        bid = variant_id or next(iter(BOSS_CATALOG))
        meta = BOSS_CATALOG[bid]
        d = meta["defaults"]
        ms = catalog_moveset(bid)
        obj = {
            "type": "boss",
            "id": bid,
            "x": x,
            "y": y,
            "arena_x": max(0, x + d["arena_x_offset"]),
            "arena_y": y + d.get("arena_y_offset", 500),
            "min_x": max(0, x + d["min_x_offset"]),
            "max_x": x + d["max_x_offset"],
        }
        if ms:
            obj["moveset"] = deep_copy_moveset(ms)
        return obj
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
            "target_level": "",
        }
    if category == "npc":
        return {
            "type": "npc",
            "x": x,
            "y": y,
            "name": "NPC",
            "dialog": ["Привет!", "Нажми E, чтобы продолжить."],
        }
    if category == "checkpoint":
        return {"type": "checkpoint", "x": x, "y": y}
    if category == "enemy":
        return {"type": "enemy", "x": x, "y": y, "dir": 1}
    # legacy direct types
    if category in _LEGACY_ABILITY:
        return default_object("ability", x, y, _LEGACY_ABILITY[category])
    raise ValueError(f"Unknown object type: {category}")


def empty_level(name="level1", world_width=6200, ground_y=726):
    return {
        "name": name,
        "world_width": world_width,
        "world_height": 2000,
        "world_top": -400,
        "ground_y": ground_y,
        "player_spawn": {"x": 120, "y": 640},
        "platforms": [],
        "walls": [],
        "objects": [],
        "texture_overrides": {},
    }


def load_level(path=DEFAULT_LEVEL_PATH):
    if not os.path.exists(path):
        return empty_level()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("name", "level")
    data.setdefault("world_width", 6200)
    data.setdefault("world_height", 2000)
    data.setdefault("world_top", -400)
    data.setdefault("ground_y", 726)
    data.setdefault("player_spawn", {"x": 120, "y": 640})
    data.setdefault("platforms", [])
    data.setdefault("walls", [])
    data.setdefault("texture_overrides", {})
    data["objects"] = [normalize_object(o) for o in data.get("objects", [])]
    from textures import apply_overrides_to_level
    apply_overrides_to_level(data)
    return data


def save_level(data, path=DEFAULT_LEVEL_PATH):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    to_save = dict(data)
    to_save.setdefault("walls", [])
    to_save["objects"] = [normalize_object(o) for o in data.get("objects", [])]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(to_save, f, ensure_ascii=False, indent=2)


def platforms_from_level(level):
    ov = (level.get("texture_overrides") or {}).get("platform")
    return [
        Platform(p["x"], p["y"], p.get("texture") or ov)
        for p in level.get("platforms", [])
    ]


def walls_from_level(level):
    ov = (level.get("texture_overrides") or {}).get("wall")
    return [
        Wall(w["x"], w["y"], w.get("texture") or ov)
        for w in level.get("walls", [])
    ]


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


def boss_drop(boss_id):
    """Возвращает нормализованный дроп босса или None, если дропа нет."""
    meta = BOSS_CATALOG.get(boss_id) or {}
    drop = meta.get("drop")
    if not drop:
        return None
    coins = int(drop.get("coins", 0) or 0)
    abilities = [
        aid for aid in (drop.get("abilities") or [])
        if aid in ABILITY_CATALOG
    ]
    if coins <= 0 and not abilities:
        return None
    return {"coins": max(0, coins), "abilities": abilities}
