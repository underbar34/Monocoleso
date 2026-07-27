# platforms.py
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


def _row(x_start, x_end, y, step=105):
    return [Platform(x, y) for x in range(x_start, x_end + 1, step)]


def _col(x, y_start, y_end, step=85):
    if y_start <= y_end:
        ys = range(y_start, y_end + 1, step)
    else:
        ys = range(y_start, y_end - 1, -step)
    return [Platform(x, y) for y in ys]


def create_platforms():
    pls = []

    # Стартовая зона
    pls += _row(0, 840, 710)

    # Паркур: зигзаг вверх (сложнее — узкие прыжки, смещённые платформы)
    pls += _col(840, 625, 285, 90)
    pls.append(Platform(630, 560))
    pls.append(Platform(420, 475))
    pls.append(Platform(210, 390))
    pls.append(Platform(420, 305))
    pls.append(Platform(630, 220))
    pls.append(Platform(210, 220))

    # Бонусная комната — доп. жизнь (ответвление влево)
    pls.append(Platform(105, 170))
    pls += _col(105, 170, 80, 45)

    # Верхний коридор (длинный)
    pls += _row(945, 2520, 285)
    pls.append(Platform(1260, 400))
    pls.append(Platform(1575, 340))
    pls.append(Platform(1890, 400))
    pls.append(Platform(2205, 340))

    # Спуск в арену босса
    pls += _col(2520, 370, 625, 90)

    # Пол арены босса
    pls += _row(2520, 5800, 710)

    # Платформы внутри арены
    pls.append(Platform(3000, 560))
    pls.append(Platform(3400, 490))
    pls.append(Platform(3800, 560))
    pls.append(Platform(4200, 490))
    pls.append(Platform(4600, 560))

    # Выходная зона
    pls += _row(5600, 5800, 450)

    return pls
