# platforms.py
from config import WALL_W, WALL_H


class Platform:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.shir = 105

    def pup(self, px, py, ground_y):
        if self.x - 50 <= px <= self.x + self.shir and self.y - 50 > py > self.y - 100:
            return self.y - 70
        else:
            return ground_y


class Wall:
    """Вертикальная стена — повёрнутая платформа, сквозь которую нельзя пройти."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = WALL_W
        self.h = WALL_H

    def rect(self):
        return (self.x, self.y, self.w, self.h)

    def stand_y(self):
        """Y игрока, если стоит на верхней грани стены."""
        return self.y - 50

    def pup(self, px, py, ground_y):
        """Поверхность сверху стены — как узкая платформа."""
        if self.x - 35 <= px <= self.x + self.w - 5:
            top = self.y
            if top - 55 < py + 50 <= top + 8 and py < top:
                return self.stand_y()
        return ground_y


def _row(x_start, x_end, y, step=105):
    return [Platform(x, y) for x in range(x_start, x_end + 1, step)]


def _col(x, y_start, y_end, step=85):
    if y_start <= y_end:
        ys = range(y_start, y_end + 1, step)
    else:
        ys = range(y_start, y_end - 1, -step)
    return [Platform(x, y) for y in ys]


def create_platforms_fallback():
    """Старый хардкод — используется только если JSON уровня не найден."""
    pls = []
    pls += _row(0, 840, 710)
    pls += _col(840, 625, 285, 90)
    pls.append(Platform(630, 560))
    pls.append(Platform(420, 475))
    pls.append(Platform(210, 390))
    pls.append(Platform(420, 305))
    pls.append(Platform(630, 220))
    pls.append(Platform(210, 220))
    pls.append(Platform(105, 170))
    pls += _col(105, 170, 80, 45)
    pls += _row(945, 2520, 285)
    pls.append(Platform(1260, 400))
    pls.append(Platform(1575, 340))
    pls.append(Platform(1890, 400))
    pls.append(Platform(2205, 340))
    pls += _col(2520, 370, 625, 90)
    pls += _row(2520, 5800, 710)
    pls.append(Platform(3000, 560))
    pls.append(Platform(3400, 490))
    pls.append(Platform(3800, 560))
    pls.append(Platform(4200, 490))
    pls.append(Platform(4600, 560))
    pls += _row(5600, 5800, 450)
    return pls


def create_platforms(level=None):
    if level is not None:
        from level_loader import platforms_from_level
        pls = platforms_from_level(level)
        if pls:
            return pls
    return create_platforms_fallback()


def create_walls(level=None):
    if level is None:
        return []
    from level_loader import walls_from_level
    return walls_from_level(level)
