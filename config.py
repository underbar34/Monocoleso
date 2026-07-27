# config.py
import pygame

# Размеры окна
WIDTH = 1560
HEIGHT = 800

# FPS
FPS = 60

# Задержка атаки (1/3 секунды)
ATAKA_ZADERZHKA = FPS // 3

# Гравитация
GRAVITI = 1.3

# Скорости
SPEED_PLAYER = 5.5
SPEED_PLAYER_Y = 6.5
JUMP_FORCE = -2.4
JUMP_HOLD_MAX = 17
JUMP_HOLD_BOOST = 0.085
JUMP_CUT_MULT = 0.4
GRAVITY_AIR = 0.14
FALL_SPEED_MAX = 1.6
PLAYER_ACCEL = 1.0
PLAYER_FRICTION = 0.78
SPRINT_MULT = 2.0

# Отбрасывание при попадании по боссу
KNOCKBACK_SIDE = 6.5
KNOCKBACK_VERTICAL = 3.0
KNOCKBACK_UP = 3.0
KNOCKBACK_UP_MULT = 1.3
KNOCKBACK_BLEND = 0.28
KNOCKBACK_DECAY = 0.87

# Таймер прыжка в кадрах
JUMP_TIMER_MAX = 30

# Длительность анимации атаки в кадрах
ATAKA_KADRY = 10

# Земля по умолчанию
GROUND_Y = 726

# Размер мира
WORLD_WIDTH = 6200

# Босс — холодос
BOSS_MAX_HP = 600
BOSS_DAMAGE = 30
BOSS_X = 3800
BOSS_Y = 233
BOSS_W = 423
BOSS_H = 477
BOSS_ARENA_X = 2500
BOSS_MIN_X = 2700
BOSS_MAX_X = 5000
BOSS_SPEED = 1.8
BOSS_SPEED_PHASE2 = 3.2
BOSS_HIT_COOLDOWN = 15
BOSS_CONTACT_DAMAGE = 1

# Здоровье
HEALTH_MAX = 5

# Неуязвимость
NEUYAZVIMOST_MAX = 60

# Акум
MAX_AKUM_POWER = 5


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

    for i in range(1, 5):
        raw = pygame.image.load(f"Assets/holodos/holodos{i}.png")
        h = 477
        w = int(raw.get_width() * h / raw.get_height())
        images[f"holodos{i}"] = pygame.transform.scale(raw, (w, h))

    for i in range(1, 4):
        raw = pygame.image.load(f"Assets/holodos/holodosymer{i}.png")
        h = 477
        w = int(raw.get_width() * h / raw.get_height())
        images[f"holodos_dead{i}"] = pygame.transform.scale(raw, (w, h))

    extra_life = pygame.Surface((28, 28))
    extra_life.fill((76, 175, 80))
    images['extra_life'] = extra_life

    sprint_skill = pygame.Surface((28, 28))
    sprint_skill.fill((156, 39, 176))
    images['sprint_skill'] = sprint_skill

    coin = pygame.Surface((20, 20), pygame.SRCALPHA)
    pygame.draw.circle(coin, (255, 215, 0), (10, 10), 10)
    pygame.draw.circle(coin, (255, 180, 0), (10, 10), 7)
    images['coin'] = coin

    snowflake = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.circle(snowflake, (200, 230, 255), (8, 8), 7)
    pygame.draw.circle(snowflake, (255, 255, 255), (8, 8), 4)
    images['snowflake'] = snowflake

    return images


class GameState:
    def __init__(self, images):
        self.player = images['player']
        self.playerx = 120
        self.playery = 640
        self.y_vel = 0
        self.y_veling = 0
        self.opuskatsa = 0
        self.isjump = False
        self.mognovnis = False
        self.timer = 0
        self.otpuskal = True
        self.playermovex = 0
        self.playermovey = 0
        self.x_vel = 0
        self.kb_vx = 0.0
        self.kb_vy = 0.0
        self.prev_space = False
        self.jump_holding = False
        self.jump_hold_timer = 0
        self.health = 4
        self.neuyazvimost = NEUYAZVIMOST_MAX
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

        # Доп. жизнь
        self.extra_life_podobran = False
        self.extra_lifex = 125
        self.extra_lifey = 10

        # Абилка спринта (выпадает с босса)
        self.sprint_unlocked = False
        self.sprint_podobran = False
        self.sprint_pickup = None

        # Босс
        self.boss_alive = True
        self.boss_x = BOSS_X
        self.boss_y = BOSS_Y
        self.boss_hp = BOSS_MAX_HP
        self.boss_phase = 1
        self.boss_anim = 0
        self.boss_move = None
        self.boss_move_timer = 0
        self.boss_idle_timer = 90
        self.boss_last_move = -1
        self.boss_shake = 0
        self.boss_dying = False
        self.boss_death_timer = 0
        self.boss_hit_cooldown = 0
        self.boss_attack_hit = False
        self.snowflakes = []
        self.coins = []
        self.loot_spawned = False
