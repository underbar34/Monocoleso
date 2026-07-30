# textures.py
"""Кастомные текстуры объектов уровня: скан Assets/, кэш загрузки."""
import os
import pygame

ASSETS_ROOT = "Assets"
_IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")


def list_asset_textures(root=ASSETS_ROOT):
    """Относительные пути вида Assets/foo/bar.png, отсортированные."""
    found = []
    if not os.path.isdir(root):
        return found
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if name.lower().endswith(_IMAGE_EXTS):
                full = os.path.join(dirpath, name)
                found.append(full.replace("\\", "/"))
    found.sort()
    return found


def normalize_texture_path(path):
    if not path:
        return None
    p = str(path).replace("\\", "/").strip()
    if not p:
        return None
    return p


def load_texture(path, cache=None, max_size=None, fit=None):
    """
    Загружает изображение. cache — dict path -> Surface.
    fit=(w,h) — жёсткий ресайз; max_size=(mw,mh) — вписать с сохранением пропорций.
    """
    path = normalize_texture_path(path)
    if not path:
        return None
    key = (path, fit, max_size)
    if cache is not None and key in cache:
        return cache[key]
    if not os.path.isfile(path):
        return None
    try:
        img = pygame.image.load(path)
        if pygame.display.get_surface() is not None:
            img = img.convert_alpha()
    except pygame.error:
        return None
    if fit:
        img = pygame.transform.smoothscale(img, fit)
    elif max_size:
        mw, mh = max_size
        w, h = img.get_size()
        scale = min(mw / max(w, 1), mh / max(h, 1), 1.0)
        if scale < 1.0:
            img = pygame.transform.smoothscale(
                img, (max(1, int(w * scale)), max(1, int(h * scale))),
            )
    if cache is not None:
        cache[key] = img
    return img


def texture_label(path, max_len=42):
    path = normalize_texture_path(path) or ""
    if len(path) <= max_len:
        return path
    return "…" + path[-(max_len - 1):]


# Типы, которым можно менять текстуру
TEXTUREABLE_OBJECT_TYPES = frozenset({
    "ability", "sprint_skill", "dash_skill", "extra_life", "npc", "teleport", "checkpoint",
})
TEXTUREABLE_TOOLS = frozenset({
    "platform", "wall", "ability", "extra_life", "npc", "teleport", "checkpoint",
})
TEXTUREABLE_KINDS = frozenset({"platform", "wall", "object"})


def ability_override_key(ability_id):
    return f"ability:{ability_id or 'sprint'}"


def override_key_for_object(obj):
    """Ключ texture_overrides для объекта уровня или None."""
    t = obj.get("type")
    if t in ("ability", "sprint_skill", "dash_skill"):
        if t == "ability":
            aid = obj.get("id", "sprint")
        elif t == "sprint_skill":
            aid = "sprint"
        else:
            aid = "dash"
        return ability_override_key(aid)
    if t in ("extra_life", "npc", "teleport", "checkpoint"):
        return t
    return None


def override_key_for_tool(tool, ability_variant=None):
    if tool == "ability":
        return ability_override_key(ability_variant or "sprint")
    if tool in ("platform", "wall", "extra_life", "npc", "teleport", "checkpoint"):
        return tool
    return None


def get_override(level, key):
    if not key:
        return None
    return normalize_texture_path((level.get("texture_overrides") or {}).get(key))


def set_override(level, key, path):
    level.setdefault("texture_overrides", {})
    path = normalize_texture_path(path)
    if path:
        level["texture_overrides"][key] = path
    else:
        level["texture_overrides"].pop(key, None)


def stamp_override_on_level(level, key, path):
    """Записать override и проставить texture всем объектам этого типа."""
    set_override(level, key, path)
    path = normalize_texture_path(path)

    def _apply(d):
        if path:
            d["texture"] = path
        else:
            d.pop("texture", None)

    if key == "platform":
        for p in level.get("platforms", []):
            _apply(p)
        return
    if key == "wall":
        for w in level.get("walls", []):
            _apply(w)
        return
    if key.startswith("ability:"):
        aid = key.split(":", 1)[1]
        for o in level.get("objects", []):
            t = o.get("type")
            if t == "ability" and o.get("id", "sprint") == aid:
                _apply(o)
            elif t == "sprint_skill" and aid == "sprint":
                _apply(o)
            elif t == "dash_skill" and aid == "dash":
                _apply(o)
        return
    if key in ("extra_life", "npc", "teleport", "checkpoint"):
        for o in level.get("objects", []):
            if o.get("type") == key:
                _apply(o)


def resolve_item_texture(item_texture, level_or_overrides, override_key):
    """instance texture → type override → None."""
    t = normalize_texture_path(item_texture)
    if t:
        return t
    if isinstance(level_or_overrides, dict) and "texture_overrides" in level_or_overrides:
        return get_override(level_or_overrides, override_key)
    if isinstance(level_or_overrides, dict):
        return normalize_texture_path(level_or_overrides.get(override_key))
    return None


def apply_overrides_to_level(level):
    """Подтянуть texture_overrides на объекты без своей texture."""
    ov = level.get("texture_overrides") or {}
    if not ov:
        return
    for p in level.get("platforms", []):
        if not p.get("texture") and ov.get("platform"):
            p["texture"] = ov["platform"]
    for w in level.get("walls", []):
        if not w.get("texture") and ov.get("wall"):
            w["texture"] = ov["wall"]
    for o in level.get("objects", []):
        key = override_key_for_object(o)
        if key and not o.get("texture") and ov.get(key):
            o["texture"] = ov[key]
