# motion_blur.py
import pygame


class MotionBlur:
    """Простой motion blur: полупрозрачный шлейф спрайта."""

    def __init__(self, length=8):
        self.length = length
        self.trail = []
        self._ghost_cache = {}  # (id(image), alpha) -> Surface

    def update(self, x, y, image, strong=False):
        self.trail.append((x, y, image, strong))
        limit = self.length if strong else 3
        while len(self.trail) > limit:
            self.trail.pop(0)

    def _ghost(self, image, alpha):
        key = (id(image), alpha)
        cached = self._ghost_cache.get(key)
        if cached is not None:
            return cached
        ghost = image.convert_alpha()
        ghost.set_alpha(alpha)
        # ограничиваем кэш
        if len(self._ghost_cache) > 48:
            self._ghost_cache.clear()
        self._ghost_cache[key] = ghost
        return ghost

    def draw(self, screen, cam_x=0, cam_y=0):
        total = len(self.trail)
        if total < 2:
            return
        for i, (x, y, image, strong) in enumerate(self.trail[:-1]):
            t = (i + 1) / total
            if strong:
                alpha = int(35 + 90 * t)
            else:
                alpha = int(20 + 40 * t)
            screen.blit(self._ghost(image, alpha), (x - cam_x, y - cam_y))

    def clear(self):
        self.trail.clear()
        self._ghost_cache.clear()
