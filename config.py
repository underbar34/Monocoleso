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

# Рывок (dash)
DASH_DURATION = int(FPS * 0.3)   # 0.3 секунды
DASH_SPEED = 22.0
DASH_COOLDOWN = int(FPS * 0.85)

# Отбрасывание при попадании по боссу
KNOCKBACK_SIDE = 6.5
KNOCKBACK_VERTICAL = 3.0
KNOCKBACK_UP = 2.0
KNOCKBACK_UP_MULT = 1.0
KNOCKBACK_BLEND = 0.28
KNOCKBACK_DECAY = 0.87
KNOCKBACK_RISE_MAX = -2.8

# Таймер прыжка в кадрах
JUMP_TIMER_MAX = 30

# Длительность анимации атаки в кадрах
ATAKA_KADRY = 10

# Земля по умолчанию
GROUND_Y = 726

# Размер мира
WORLD_WIDTH = 6200
WORLD_HEIGHT = 2000
WORLD_TOP = -400

# Стена (повёрнутая платформа)
WALL_W = 20
WALL_H = 116
PLAYER_W = 40
PLAYER_H = 50

# Босс — холодос
BOSS_MAX_HP = 600
BOSS_DAMAGE = 30
BOSS_X = 3800
BOSS_Y = 233
BOSS_W = 423
BOSS_H = 477
BOSS_ARENA_X = 2500
BOSS_ARENA_Y = 900
BOSS_MIN_X = 2700
BOSS_MAX_X = 5000
BOSS_SPEED = 1.8
BOSS_SPEED_PHASE2 = 2.5
BOSS_SPEED_PHASE3 = 3.4
BOSS_HIT_COOLDOWN = 15
BOSS_CONTACT_DAMAGE = 1

# Здоровье
HEALTH_MAX = 5

# Неуязвимость
NEUYAZVIMOST_MAX = 60

# Камера
CAM_FOLLOW_LERP = 0.16
CAM_ARENA_LERP = 0.10

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
    images['wall'] = pygame.transform.rotate(images['platform'], 90)
    images['inventory'] = pygame.image.load("Assets/bg/inventory.png")

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

    def _load_holodos(name, key, max_h=None, max_w=None):
        raw = pygame.image.load(f"Assets/holodos/{name}.png")
        w, h = raw.get_size()
        if max_h and h > max_h:
            w = int(w * max_h / h)
            h = max_h
        if max_w and w > max_w:
            h = int(h * max_w / w)
            w = max_w
        images[key] = pygame.transform.scale(raw, (w, h))

    _load_holodos("atakauslevy1", "holodos_atk_left1", max_h=320)
    _load_holodos("atakauslevy2", "holodos_atk_left2", max_h=400)
    _load_holodos("atakauspravy1", "holodos_atk_right1", max_h=320)
    _load_holodos("atakauspravy2", "holodos_atk_right2", max_h=400)
    _load_holodos("prostouslevy", "holodos_slash_left", max_h=60, max_w=200)
    _load_holodos("prostouspravy", "holodos_slash_right", max_h=60, max_w=200)
    _load_holodos("ledholodosnis", "holodos_ice", max_h=48, max_w=320)
    _load_holodos("boegolovka", "boegolovka", max_h=90)

    extra_life = pygame.image.load("Assets/bg/hilka.png")
    images['extra_life'] = extra_life

    sprint_skill = pygame.image.load("Assets/bg/uskorenie.png")
    images['sprint_skill'] = sprint_skill

    try:
        dash_skill = pygame.image.load("Assets/bg/polotense.png")
    except pygame.error:
        dash_skill = pygame.Surface((28, 28))
        dash_skill.fill((255, 87, 34))
    images['dash_skill'] = dash_skill

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
    def __init__(self, images, level=None):
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
        self.akumpower = 0
        self.akum = images['akum0']
        self.images = images
        self.lookdir = 1
        self.texture_cache = {}
        self.texture_overrides = {}
        self.cam_x = None
        self.cam_y = None
        self.current_level_path = None
        self.pending_level = None  # {"path", "spawn_x", "spawn_y"}
        self.level_name = "level"

        # Пикапы с уровня (extra_life / ability)
        self.level_pickups = []

        # Совместимость со старым кодом доп. жизни
        self.extra_life_podobran = True
        self.extra_lifex = -9999
        self.extra_lifey = -9999

        # Абилки (спринт / рывок; спринт также падает с босса)
        self.sprint_unlocked = False
        self.sprint_podobran = False
        self.sprint_pickup = None
        self.boss_loot = []
        self.dash_unlocked = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_dir = 1

        # Босс
        self.boss_alive = False
        self.boss_id = "holodos"
        self.boss_x = BOSS_X
        self.boss_y = BOSS_Y
        self.boss_arena_x = BOSS_ARENA_X
        self.boss_arena_y = BOSS_ARENA_Y
        self.boss_min_x = BOSS_MIN_X
        self.boss_max_x = BOSS_MAX_X
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
        self.boss_arena_locked = False
        self.boss_moveset = None
        self.boss_sprite_mode = "idle"
        self.boss_shake_timer = 0
        self.boss_melee = None
        self.boss_projectiles = []
        self.snowflakes = []  # legacy alias, cleared each frame
        self.coins = []
        self.loot_spawned = False

        # NPC / телепорты / диалог
        self.npcs = []
        self.teleports = []
        self.checkpoints = []
        self.enemies = []
        self.teleport_cooldown = 0
        self.dialog = None  # {"name", "lines", "index"}
        self.interact_hint = None
        self.checkpoint = None  # последнее сохранение (dict)
        self.save_flash = 0  # кадры подсказки «Сохранено!»
        self.pending_respawn = None  # {"path","spawn_x","spawn_y"} | None
        self.inventory = []
        self.inventory_open = False

        self.world_width = WORLD_WIDTH
        self.world_height = WORLD_HEIGHT
        self.world_top = WORLD_TOP
        self.ground_y_default = GROUND_Y

        if level is not None:
            self.apply_level(level)

    def apply_level(self, level, spawn_xy=None, level_path=None):
        """Загружает геометрию уровня. Прогресс игрока (HP, абилки) не сбрасывается.
        spawn_xy=(x,y) — точка появления; иначе player_spawn уровня.
        """
        if level_path:
            self.current_level_path = level_path
        from level_loader import level_display_name
        self.level_name = level.get("name") or level_display_name(self.current_level_path)
        spawn = level.get("player_spawn", {"x": 120, "y": 640})
        if spawn_xy is not None:
            self.playerx = float(spawn_xy[0])
            self.playery = float(spawn_xy[1])
        else:
            self.playerx = spawn.get("x", 120)
            self.playery = spawn.get("y", 640)
        self.cam_x = None
        self.cam_y = None
        self.x_vel = 0
        self.playermovey = 0
        self.y_vel = 0
        self.kb_vx = 0.0
        self.kb_vy = 0.0
        self.dialog = None
        self.interact_hint = None
        self.teleport_cooldown = 30
        self.pending_level = None
        self.coins = []
        self.boss_loot = []
        self.sprint_pickup = None
        self.world_width = level.get("world_width", WORLD_WIDTH)
        self.world_height = level.get("world_height", WORLD_HEIGHT)
        self.world_top = level.get("world_top", WORLD_TOP)
        self.ground_y_default = level.get("ground_y", GROUND_Y)

        self.level_pickups = []
        self.npcs = []
        self.teleports = []
        self.checkpoints = []
        self.enemies = []
        self.boss_alive = False
        self.boss_dying = False
        self.boss_arena_locked = False
        self.boss_melee = None
        self.boss_projectiles = []
        self.boss_shake_timer = 0
        self.loot_spawned = False
        if hasattr(self, "_boss_base_y"):
            del self._boss_base_y
        self.texture_overrides = dict(level.get("texture_overrides") or {})

        for obj in level.get("objects", []):
            t = obj.get("type")
            if t == "boss":
                from boss_moves import resolve_moveset, default_holodos_moveset
                from level_loader import BOSS_CATALOG
                self.boss_alive = True
                self.boss_id = obj.get("id", "holodos")
                self.boss_x = obj.get("x", BOSS_X)
                self.boss_y = obj.get("y", BOSS_Y)
                self.boss_arena_x = obj.get("arena_x", BOSS_ARENA_X)
                self.boss_arena_y = obj.get(
                    "arena_y",
                    obj.get("y", BOSS_Y) + 500,
                )
                self.boss_min_x = obj.get("min_x", BOSS_MIN_X)
                self.boss_max_x = obj.get("max_x", BOSS_MAX_X)
                self.boss_hp = BOSS_MAX_HP
                self.boss_phase = 1
                self.boss_dying = False
                self.boss_arena_locked = False
                self.boss_sprite_mode = "idle"
                self.boss_melee = None
                self.boss_projectiles = []
                self.boss_shake_timer = 0
                catalog_ms = (BOSS_CATALOG.get(self.boss_id) or {}).get("moveset")
                if catalog_ms is None and self.boss_id == "holodos":
                    catalog_ms = default_holodos_moveset()
                self.boss_moveset = resolve_moveset(obj, catalog_ms)
                idle0 = 90
                phases = self.boss_moveset.get("phases") or []
                if phases:
                    idle0 = int(phases[0].get("idle", 90))
                self.boss_idle_timer = idle0
                self.loot_spawned = False
            elif t == "ability":
                aid = obj.get("id", "sprint")
                tex = obj.get("texture") or self.texture_overrides.get(f"ability:{aid}")
                self.level_pickups.append({
                    "type": "ability",
                    "id": aid,
                    "x": obj["x"],
                    "y": obj["y"],
                    "texture": tex,
                    "collected": False,
                })
            elif t == "extra_life":
                tex = obj.get("texture") or self.texture_overrides.get("extra_life")
                self.level_pickups.append({
                    "type": "extra_life",
                    "x": obj["x"],
                    "y": obj["y"],
                    "texture": tex,
                    "collected": False,
                })
            elif t == "npc":
                tex = obj.get("texture") or self.texture_overrides.get("npc")
                self.npcs.append({
                    "x": obj["x"],
                    "y": obj["y"],
                    "name": obj.get("name", "NPC"),
                    "dialog": list(obj.get("dialog") or ["..."]),
                    "texture": tex,
                })
            elif t == "teleport":
                tex = obj.get("texture") or self.texture_overrides.get("teleport")
                self.teleports.append({
                    "x": obj["x"],
                    "y": obj["y"],
                    "target_x": obj.get("target_x", obj["x"] + 200),
                    "target_y": obj.get("target_y", obj["y"]),
                    "target_level": (obj.get("target_level") or "").strip(),
                    "texture": tex,
                })
            elif t == "checkpoint":
                tex = obj.get("texture") or self.texture_overrides.get("checkpoint")
                self.checkpoints.append({
                    "x": obj["x"],
                    "y": obj["y"],
                    "texture": tex,
                })
            elif t == "enemy":
                from enemies import make_enemy_from_object
                e = make_enemy_from_object(obj)
                tex = obj.get("texture") or self.texture_overrides.get("enemy")
                e["texture"] = tex
                self.enemies.append(e)

        lives = [p for p in self.level_pickups if p["type"] == "extra_life"]
        if lives:
            self.extra_life_podobran = False
            self.extra_lifex = lives[0]["x"]
            self.extra_lifey = lives[0]["y"]
        else:
            self.extra_life_podobran = True
