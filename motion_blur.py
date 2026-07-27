# motion_blur.py
import pygame


class MotionBlur:
    """Простой motion blur: полупрозрачный шлейф спрайта."""

    def __init__(self, length=8):
        self.length = length
        self.trail = []

    def update(self, x, y, image, strong=False):
        self.trail.append((x, y, image, strong))
        limit = self.length if strong else max(3, self.length // 2)
        while len(self.trail) > limit:
            self.trail.pop(0)
        if not strong and len(self.trail) > 3:
            # в обычном движении шлейф короче
            while len(self.trail) > 3:
                self.trail.pop(0)

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
            ghost = image.convert_alpha()
            ghost.set_alpha(alpha)
            screen.blit(ghost, (x - cam_x, y - cam_y))

    def clear(self):
        self.trail.clear()
