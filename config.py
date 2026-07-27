# config.pу
import pygame

# Размеры окна
WIDTH = 1560
HEIGHT = 800

# FPS
FPS = 60

# Задержка атаки (1/3 секунды)
ATAKA_ZADERZHKA = FPS // 3

# Рывок
RYVOK_VREMYA = int(FPS * 0.3)
RYVOK_SPEED = 11
RYVOK_ZADERZHKA = int(FPS * 0.5)
RYVOK_V_VOZDUHE_MAX = 2

# Плащик: заморозка после подбора (1.2 сек)
PLASHIK_ZAMOROZKA = int(FPS * 1.2)

# Гравитация
GRAVITI = 1.3

# Скорости (подогнаны под 60 FPS, поведение как на 30)
SPEED_PLAYER = 2.5
SPEED_PLAYER_Y = 5

# Таймер прыжка в кадрах
JUMP_TIMER_MAX = 30

# Длительность анимации атаки в кадрах
ATAKA_KADRY = 10

# Земля по умолчанию
GROUND_Y = 726

# Здоровье
HEALTH_MAX = 5

# Неуязвимость
NEUYAZVIMOST_MAX = 60

# Акум
MAX_AKUM_POWER = 5

# Загрузка изображений
def load_images():
    images = {}
    images['player'] = pygame.image.load("Assets/Tems/Tems(stoit1).png")
    images['gizn'] = pygame.image.load("Assets/gizn/gizn.png")
    images['nogizn'] = pygame.image.load("Assets/gizn/giznmax.png")
    images['akum0'] = pygame.image.load("Assets/akum/akum0.png")
    images['akum1'] = pygame.image.load("Assets/akum/akum1.png")
    images['akum2'] = pygame.image.load("Assets/akum/akum2.png")
    images['akum3'] = pygame.image.load("Assets/akum/akum3.png")
    images['akum4'] = pygame.image.load("Assets/akum/akum4.png")
    images['akum5'] = pygame.image.load("Assets/akum/akum5.png")
    images['playeridet1'] = pygame.image.load("Assets/Tems/Tems(idet1).png")
    images['playeridet2'] = pygame.image.load("Assets/Tems/Tems(idet2).png")
    images['playerataka1'] = pygame.image.load("Assets/atakaTems/ataka1tems.png")
    images['playerataka2'] = pygame.image.load("Assets/atakaTems/ataka2tems.png")
    images['playerataka3'] = pygame.image.load("Assets/atakaTems/ataka3tems.png")
    images['playerataka4'] = pygame.image.load("Assets/atakaTems/ataka4tems.png")
    images['playerstoit1'] = pygame.image.load("Assets/Tems/Tems(stoit1).png")
    images['playerstoit2'] = pygame.image.load("Assets/Tems/Tems(stoit2).png")
    images['platform'] = pygame.image.load("Assets/locat/platform.png")
    # Плащик — простой квадратик
    plashik = pygame.Surface((28, 28))
    plashik.fill((40, 160, 200))
    images['plashik'] = plashik
    return images

# Игровые переменные
class GameState:
    def __init__(self, images):
        self.player = images['player']
        self.playerx = 300
        self.playery = 200
        self.y_vel = 0
        self.y_veling = 0
        self.opuskatsa = 0
        self.isjump = False
        self.mognovnis = False
        self.timer = 0
        self.otpuskal = True
        self.playermovex = 0
        self.playermovey = 0
        self.health = 4
        self.neuyazvimost = 0
        self.atakapl = False
        self.flagatak = 0
        self.vrematakpl = 0
        self.atakazaderzhka = 0
        self.atakax = -1000
        self.giznx = 100
        self.gizny = 2
        self.akumpower = 5
        self.akum = images['akum0']
        self.images = images
        self.lookdir = 1
        # Плащик на платформе справа (не стартовая)
        self.plashik_podobran = False
        self.plashikx = 930
        self.plashiky = 460
        self.plashik_zamorozka = 0
        # Рывок
        self.ryvok = False
        self.ryvok_timer = 0
        self.ryvok_dir = 1
        self.ryvok_zaderzhka = 0
        self.ryvok_vozduh = 0
        self.shift_derzali = False