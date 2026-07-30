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
    "ability", "sprint_skill", "dash_skill", "extra_life", "npc", "teleport",
})
TEXTUREABLE_KINDS = frozenset({"platform", "wall", "object"})
