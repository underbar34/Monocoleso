import pygame
import random

pygame.init()

# Настройки окна
WIDTH = 1060
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Контроль FPS
clock = pygame.time.Clock()
FPS = 30

# Загрузка изображений
player = pygame.image.load("Tems(stoit1).png")
playeridet1 = pygame.image.load("Tems(idet1).png")
playeridet2 = pygame.image.load("Tems(idet2).png")
playerataka1 = pygame.image.load("Tems(ataka1).png")
playerataka2 = pygame.image.load("Tems(ataka2).png")
playerstoit1 = pygame.image.load("Tems(stoit1).png")
playerstoit2 = pygame.image.load("Tems(stoit2).png")
platform = pygame.image.load("platform.png")
gizn = pygame.image.load("gizn.png")
nogizn = pygame.image.load("giznmax.png")
akum = pygame.image.load("akum0.png")
akum0 = pygame.image.load("akum0.png")
akum1 = pygame.image.load("akum1.png")
akum2 = pygame.image.load("akum2.png")
akum3 = pygame.image.load("akum3.png")
akum4 = pygame.image.load("akum4.png")
akum5 = pygame.image.load("akum5.png")

# Класс платформ
class platforms:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.shir = 105
        self.hei = 20  # Высота платформы

    def check_collision(self, px, py):
        # Проверка столкновения с платформой
        if (self.x <= px <= self.x + self.shir or 
            self.x <= px + player.get_width() <= self.x + self.shir) and \
           py + player.get_height() >= self.y - self.hei:
            return True
        return False

# Параметры игрока
playerx = 0
playery = 526
speedplaer = 5
speedplaery = 10
jump_force = -20
gravity = 1.3
is_jumping = False
playermovex = 0
playermovey = 0

# Создание платформ
pl1 = platforms(450, 510)
pl2 = platforms(900, 510)
pl3 = platforms(10, 510)
pls = [pl1, pl2, pl3]

# Остальные игровые параметры
health = 4
healthmax = 5
neuyazvimost = 0
neuyazvimostmax = 30
atakapl = False
flagatak = 0
vrematakpl = 0
akumpower = 5
maxakumpower = 5
giznx = 100
gizny = 2

# Игровой цикл
game_run = True
while game_run:
    # Обработка событий
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_s and playermovey == 0:
                playery += 40
            if event.key == pygame.K_w and not atakapl:
                atakapl = True
            if event.key == pygame.K_e and akumpower == maxakumpower:
                akumpower = 0
                if health <= healthmax:
                    health += 1

    # Обновление изображения аккумулятора
    if akumpower == 0:
        akum = akum0
    elif akumpower == 1:
        akum = akum1
    elif akumpower == 2:
        akum = akum2
    elif akumpower == 3:
        akum = akum3
    elif akumpower