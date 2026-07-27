# logic.py
import math
import random
import pygame
from config import (
    GROUND_Y, SPEED_PLAYER, SPEED_PLAYER_Y, ATAKA_ZADERZHKA,
    JUMP_TIMER_MAX, JUMP_FORCE, JUMP_HOLD_MAX, JUMP_HOLD_BOOST, JUMP_CUT_MULT,
    GRAVITY_AIR, FALL_SPEED_MAX, WIDTH, HEIGHT, WORLD_WIDTH, HEALTH_MAX,
    NEUYAZVIMOST_MAX, BOSS_MAX_HP, BOSS_DAMAGE, BOSS_X, BOSS_Y,
    BOSS_W, BOSS_H, BOSS_ARENA_X, BOSS_MIN_X, BOSS_MAX_X,
    BOSS_SPEED, BOSS_SPEED_PHASE2, BOSS_HIT_COOLDOWN, BOSS_CONTACT_DAMAGE,
    KNOCKBACK_SIDE, KNOCKBACK_VERTICAL, KNOCKBACK_UP, KNOCKBACK_UP_MULT,
    KNOCKBACK_BLEND, KNOCKBACK_DECAY, KNOCKBACK_RISE_MAX,
    PLAYER_ACCEL, PLAYER_FRICTION, SPRINT_MULT,
    DASH_DURATION, DASH_SPEED, DASH_COOLDOWN,
)


def get_camera_x(state):
    world_w = getattr(state, "world_width", WORLD_WIDTH)
    target = state.playerx - WIDTH // 3
    return max(0, min(target, world_w - WIDTH))


def _pickup_collision(px, py, cx, cy, size=28):
    return px < cx + size and px + 40 > cx and py < cy + size and py + 50 > cy


def _near_rect(px, py, rx, ry, rw, rh, pad=30):
    return pygame.Rect(rx - pad, ry - pad, rw + pad * 2, rh + pad * 2).colliderect(
        pygame.Rect(px, py, 40, 50)
    )


def _movement_input(keys):
    return int(bool(keys[pygame.K_d])) - int(bool(keys[pygame.K_a]))


def _on_ground(state, ground_y):
    return abs(state.playery - ground_y) < 4 and state.playermovey >= 0


def _boss_rect(state):
    shake = state.boss_shake
    return pygame.Rect(state.boss_x + shake, state.boss_y, BOSS_W, BOSS_H)


def _boss_center(state):
    return state.boss_x + BOSS_W // 2, state.boss_y + BOSS_H // 2


def _player_rect(state):
    return pygame.Rect(state.playerx, state.playery, 40, 50)


def _damage_player(state, amount=1):
    if state.neuyazvimost < NEUYAZVIMOST_MAX:
        return
    state.health = max(0, state.health - amount)
    state.neuyazvimost = 0


def _attack_rect(state):
    px, py = state.playerx, state.playery
    if state.flagatak == 1:
        img = state.images['playerataka1']
        return pygame.Rect(px + 17, py, *img.get_size())
    if state.flagatak == 2:
        img = state.images['playerataka2']
        return pygame.Rect(px - 78, py, *img.get_size())
    if state.flagatak == 3:
        img = state.images['playerataka3']
        return pygame.Rect(px + 8, py - 90, *img.get_size())
    if state.flagatak == 4:
        img = state.images['playerataka4']
        return pygame.Rect(px + 8, py + 5, *img.get_size())
    return None


def _spawn_snowflake(state, x, y, vx, vy):
    state.snowflakes.append({"x": x, "y": y, "vx": vx, "vy": vy})


def _aim_at_player(state, speed, spread=0.0):
    bx, by = _boss_center(state)
    dx = state.playerx + 20 - bx
    dy = state.playery + 25 - by
    dist = math.hypot(dx, dy) or 1
    angle = math.atan2(dy, dx) + spread
    return speed * math.cos(angle), speed * math.sin(angle)


def _boss_in_arena(state):
    arena = getattr(state, "boss_arena_x", BOSS_ARENA_X)
    return state.playerx >= arena - 200


def _boss_start_move(state, move_id):
    state.boss_move = move_id
    state.boss_move_timer = 0
    state.boss_anim = 0


def _boss_shoot_aim(state, speed=5.0):
    vx, vy = _aim_at_player(state, speed)
    bx, by = _boss_center(state)
    _spawn_snowflake(state, bx, by, vx, vy)


def _boss_shoot_spread(state, count, speed, spread_deg=30):
    bx, by = _boss_center(state)
    base = math.atan2(state.playery + 25 - by, state.playerx + 20 - bx)
    step = math.radians(spread_deg) / max(count - 1, 1)
    start = base - math.radians(spread_deg) / 2
    for i in range(count):
        a = start + step * i
        _spawn_snowflake(state, bx, by, speed * math.cos(a), speed * math.sin(a))


def _boss_shoot_rain(state, count, speed=4.0):
    for _ in range(count):
        x = state.boss_x + random.randint(40, BOSS_W - 40)
        _spawn_snowflake(state, x, state.boss_y + 20, random.uniform(-1, 1), speed)


def _boss_shoot_ring(state, count, speed):
    bx, by = _boss_center(state)
    for i in range(count):
        a = 2 * math.pi * i / count
        _spawn_snowflake(state, bx, by, speed * math.cos(a), speed * math.sin(a))


def _boss_pick_move(state):
    phase = state.boss_phase
    options = list(range(3))
    if state.boss_last_move in options and len(options) > 1:
        options.remove(state.boss_last_move)
    move = random.choice(options)
    state.boss_last_move = move
    _boss_start_move(state, move + (0 if phase == 1 else 3))


def _boss_update_move(state):
    move = state.boss_move
    if move is None:
        return

    state.boss_move_timer += 1
    state.boss_anim = (state.boss_anim + 1) % 30

    # Фаза 1
    if move == 0:
        if state.boss_move_timer == 40:
            _boss_shoot_aim(state, 5.0)
        if state.boss_move_timer >= 70:
            state.boss_move = None
            state.boss_idle_timer = 60

    elif move == 1:
        if state.boss_move_timer == 35:
            _boss_shoot_spread(state, 3, 4.5, 40)
        if state.boss_move_timer >= 75:
            state.boss_move = None
            state.boss_idle_timer = 70

    elif move == 2:
        if state.boss_move_timer in (30, 45, 60):
            _boss_shoot_rain(state, 3, 4.0)
        if state.boss_move_timer >= 90:
            state.boss_move = None
            state.boss_idle_timer = 80

    # Фаза 2
    elif move == 3:
        if state.boss_move_timer in (25, 40):
            _boss_shoot_aim(state, 7.0)
            _boss_shoot_aim(state, 6.5)
        if state.boss_move_timer >= 65:
            state.boss_move = None
            state.boss_idle_timer = 45

    elif move == 4:
        if state.boss_move_timer == 30:
            _boss_shoot_ring(state, 8, 4.5)
        if state.boss_move_timer == 50:
            _boss_shoot_ring(state, 8, 5.5)
        if state.boss_move_timer >= 85:
            state.boss_move = None
            state.boss_idle_timer = 50

    elif move == 5:
        if state.boss_move_timer < 20:
            state.boss_shake = int(math.sin(state.boss_move_timer * 0.8) * 6)
        elif state.boss_move_timer == 25:
            _boss_shoot_ring(state, 12, 5.0)
        elif state.boss_move_timer == 40:
            _boss_shoot_spread(state, 5, 6.0, 70)
        elif state.boss_move_timer >= 75:
            state.boss_shake = 0
            state.boss_move = None
            state.boss_idle_timer = 55


def _spawn_boss_loot(state):
    if state.loot_spawned:
        return
    state.loot_spawned = True
    bx, by = _boss_center(state)
    for i in range(10):
        angle = math.radians(i * 36)
        state.coins.append({
            "x": bx + math.cos(angle) * 60,
            "y": by + math.sin(angle) * 40,
            "vx": math.cos(angle) * 3,
            "vy": math.sin(angle) * 3 - 2,
            "collected": False,
        })
    state.sprint_pickup = {"x": bx - 14, "y": by - 14, "active": True}


def _update_boss_position(state):
    if not state.boss_alive or state.boss_dying:
        return
    if not _boss_in_arena(state):
        return

    speed = BOSS_SPEED_PHASE2 if state.boss_phase == 2 else BOSS_SPEED
    if state.boss_move == 5 and state.boss_move_timer < 20:
        speed *= 2.2

    target_x = state.playerx + 20 - BOSS_W // 2
    min_x = getattr(state, "boss_min_x", BOSS_MIN_X)
    max_x = getattr(state, "boss_max_x", BOSS_MAX_X)
    target_x = max(min_x, min(target_x, max_x))
    dx = target_x - state.boss_x
    if abs(dx) > speed:
        state.boss_x += speed if dx > 0 else -speed
    else:
        state.boss_x = target_x

    if not hasattr(state, "_boss_base_y"):
        state._boss_base_y = state.boss_y
    base_y = state._boss_base_y
    if state.boss_phase == 2:
        state.boss_y = base_y + int(math.sin(state.boss_anim * 0.15) * 12)
    else:
        state.boss_y = base_y


def _boss_contact_damage(state):
    if not state.boss_alive or state.boss_dying:
        return
    if not _boss_in_arena(state):
        return
    if _player_rect(state).colliderect(_boss_rect(state)):
        _damage_player(state, BOSS_CONTACT_DAMAGE)


def update_boss(state):
    if state.boss_hit_cooldown > 0:
        state.boss_hit_cooldown -= 1

    if state.boss_dying:
        state.boss_death_timer += 1
        if state.boss_death_timer >= 90:
            state.boss_alive = False
            _spawn_boss_loot(state)
        return

    if not state.boss_alive:
        return

    if not _boss_in_arena(state):
        return

    if state.boss_hp <= BOSS_MAX_HP // 2:
        state.boss_phase = 2

    if state.boss_move is None:
        state.boss_idle_timer -= 1
        if state.boss_idle_timer <= 0:
            _boss_pick_move(state)
    else:
        _boss_update_move(state)

    _update_boss_position(state)

    # Снежинки
    for sf in state.snowflakes:
        sf["x"] += sf["vx"]
        sf["y"] += sf["vy"]
    world_w = getattr(state, "world_width", WORLD_WIDTH)
    state.snowflakes = [
        sf for sf in state.snowflakes
        if -50 < sf["x"] < world_w + 50 and -50 < sf["y"] < HEIGHT + 50
    ]

    # Урон игроку от снежинок и касания босса
    if state.neuyazvimost >= NEUYAZVIMOST_MAX:
        pr = _player_rect(state)
        hit_idx = None
        for i, sf in enumerate(state.snowflakes):
            sr = pygame.Rect(sf["x"] - 8, sf["y"] - 8, 16, 16)
            if pr.colliderect(sr):
                hit_idx = i
                break
        if hit_idx is not None:
            _damage_player(state, 1)
            del state.snowflakes[hit_idx]
        else:
            _boss_contact_damage(state)


def _apply_attack_knockback(state):
    if state.flagatak == 1:
        state.kb_vx = -KNOCKBACK_SIDE
    elif state.flagatak == 2:
        state.kb_vx = KNOCKBACK_SIDE
    elif state.flagatak == 3:
        state.kb_vy = KNOCKBACK_VERTICAL
    elif state.flagatak == 4:
        state.kb_vy = -KNOCKBACK_UP * KNOCKBACK_UP_MULT


def _update_knockback(state):
    if state.kb_vx:
        state.x_vel += state.kb_vx * KNOCKBACK_BLEND
        state.kb_vx *= KNOCKBACK_DECAY
        if abs(state.kb_vx) < 0.08:
            state.kb_vx = 0

    if state.kb_vy:
        state.playermovey += state.kb_vy * KNOCKBACK_BLEND
        if state.kb_vy < 0:
            state.playermovey = max(state.playermovey, KNOCKBACK_RISE_MAX)
        state.kb_vy *= KNOCKBACK_DECAY
        if abs(state.kb_vy) < 0.06:
            state.kb_vy = 0


def update_boss_combat(state):
    if not state.boss_alive or state.boss_dying:
        return
    if not _boss_in_arena(state):
        return
    if state.boss_hit_cooldown > 0:
        return
    if not state.atakapl or state.boss_attack_hit:
        return

    atk = _attack_rect(state)
    if atk and atk.colliderect(_boss_rect(state)):
        state.boss_hp = max(0, state.boss_hp - BOSS_DAMAGE)
        state.boss_hit_cooldown = BOSS_HIT_COOLDOWN
        state.boss_attack_hit = True
        state.boss_shake = 8
        _apply_attack_knockback(state)
        if state.boss_hp <= 0:
            state.boss_dying = True
            state.boss_death_timer = 0


def update_loot(state):
    ground = getattr(state, "ground_y_default", GROUND_Y)
    for coin in state.coins:
        if coin["collected"]:
            continue
        coin["x"] += coin["vx"]
        coin["y"] += coin["vy"]
        coin["vy"] += 0.15
        if coin["y"] > ground - 20:
            coin["y"] = ground - 20
            coin["vy"] *= -0.4
            coin["vx"] *= 0.85
        if _pickup_collision(state.playerx, state.playery, coin["x"], coin["y"], 20):
            coin["collected"] = True

    state.coins = [c for c in state.coins if not c["collected"]]

    if state.sprint_pickup and state.sprint_pickup["active"]:
        p = state.sprint_pickup
        if _pickup_collision(state.playerx, state.playery, p["x"], p["y"]):
            state.sprint_podobran = True
            state.sprint_unlocked = True
            p["active"] = False


def update_akum(state):
    power = state.akumpower
    keys = ['akum0', 'akum1', 'akum2', 'akum3', 'akum4', 'akum5']
    state.akum = state.images[keys[min(power, 5)]]


def get_ground_y(pls, playerx, playery, default_ground=None):
    best = GROUND_Y if default_ground is None else default_ground
    base = best
    for pl in pls:
        gy = pl.pup(playerx, playery, base)
        if gy != base:
            best = min(best, gy)
    return best


def _collect_pickup(state, pickup):
    if pickup["type"] == "extra_life":
        if state.health < HEALTH_MAX:
            state.health += 1
        remaining = [
            p for p in state.level_pickups
            if p["type"] == "extra_life" and not p["collected"] and p is not pickup
        ]
        if not remaining:
            state.extra_life_podobran = True
    elif pickup["type"] == "ability":
        aid = pickup.get("id", "sprint")
        if aid == "sprint":
            state.sprint_podobran = True
            state.sprint_unlocked = True
        elif aid == "dash":
            state.dash_unlocked = True
    elif pickup["type"] == "sprint_skill":
        state.sprint_podobran = True
        state.sprint_unlocked = True
    elif pickup["type"] == "dash_skill":
        state.dash_unlocked = True


def update_extra_life(state):
    """Подбор пикапов, размещённых в уровне (жизни, абилки)."""
    for pickup in state.level_pickups:
        if pickup["collected"]:
            continue
        if _pickup_collision(state.playerx, state.playery, pickup["x"], pickup["y"]):
            pickup["collected"] = True
            _collect_pickup(state, pickup)


def try_start_dash(state, keys):
    """Запуск рывка по R, если абилка разблокирована."""
    if not getattr(state, "dash_unlocked", False):
        return
    if state.dash_timer > 0 or state.dash_cooldown > 0:
        return
    if state.dialog is not None:
        return
    move = _movement_input(keys)
    state.dash_dir = move if move != 0 else (1 if state.lookdir >= 0 else -1)
    state.dash_timer = DASH_DURATION
    state.kb_vx = 0
    state.kb_vy = 0
    state.playermovey = 0
    state.x_vel = state.dash_dir * DASH_SPEED
    if state.dash_dir > 0:
        state.player = state.images['playeridet1']
        state.lookdir = 1
    else:
        state.player = state.images['playeridet2']
        state.lookdir = -1


def _find_nearby_npc(state):
    for i, npc in enumerate(state.npcs):
        if _near_rect(state.playerx, state.playery, npc["x"], npc["y"], 36, 50, pad=40):
            return i, npc
    return None, None


def _find_nearby_teleport(state):
    for tp in state.teleports:
        if _near_rect(state.playerx, state.playery, tp["x"], tp["y"], 36, 36, pad=10):
            return tp
    return None


def update_interactions(state):
    """Подсказки взаимодействия и телепорт при касании метки."""
    state.interact_hint = None

    if state.dialog is not None:
        state.interact_hint = "E — дальше"
        return

    if state.teleport_cooldown > 0:
        state.teleport_cooldown -= 1

    npc_i, npc = _find_nearby_npc(state)
    if npc is not None:
        state.interact_hint = f"E — говорить ({npc['name']})"

    tp = _find_nearby_teleport(state)
    if tp is not None:
        if state.interact_hint is None:
            state.interact_hint = "Телепорт..."
        if state.teleport_cooldown <= 0:
            state.playerx = tp["target_x"]
            state.playery = tp["target_y"]
            state.teleport_cooldown = 45
            state.x_vel = 0
            state.playermovey = 0


def _advance_dialog(state):
    d = state.dialog
    if d is None:
        return
    d["index"] += 1
    if d["index"] >= len(d["lines"]):
        state.dialog = None


def _start_dialog(state, npc):
    lines = npc.get("dialog") or ["..."]
    state.dialog = {
        "name": npc.get("name", "NPC"),
        "lines": list(lines),
        "index": 0,
    }


def try_interact(state):
    """Нажатие E: диалог с NPC или лечение акумом."""
    if state.dialog is not None:
        _advance_dialog(state)
        return

    npc_i, npc = _find_nearby_npc(state)
    if npc is not None:
        _start_dialog(state, npc)
        return

    if state.akumpower == 5:
        state.akumpower = 0
        if state.health <= HEALTH_MAX:
            state.health += 1


def update_player_movement(state, keys, ground_y):
    if state.boss_shake > 0 and state.boss_move != 5:
        state.boss_shake = max(0, state.boss_shake - 1)

    if state.dash_cooldown > 0 and state.dash_timer <= 0:
        state.dash_cooldown -= 1

    if state.dialog is not None:
        state.x_vel = 0
        state.playermovex = 0
        state.kb_vx = 0
        state.kb_vy = 0
        state.dash_timer = 0
        on_ground = _on_ground(state, ground_y)
        if on_ground:
            state.playery = ground_y
            state.playermovey = 0
        return

    # Рывок: очень быстрый горизонтальный сдвиг ~0.3 с
    if state.dash_timer > 0:
        state.dash_timer -= 1
        state.x_vel = state.dash_dir * DASH_SPEED
        state.playerx += state.x_vel
        world_w = getattr(state, "world_width", WORLD_WIDTH)
        state.playerx = max(0, min(state.playerx, world_w - 40))
        on_ground = _on_ground(state, ground_y)
        if on_ground:
            state.playery = ground_y
            state.playermovey = 0
        else:
            state.playermovey = min(state.playermovey + GRAVITY_AIR * 0.35, FALL_SPEED_MAX * 0.4)
            state.playery += state.playermovey * SPEED_PLAYER_Y
            if state.playery > ground_y:
                state.playery = ground_y
                state.playermovey = 0
        if state.dash_timer <= 0:
            state.x_vel *= 0.35
            state.dash_cooldown = DASH_COOLDOWN
        return

    _update_knockback(state)

    state.playermovex = _movement_input(keys)
    speed_mult = SPRINT_MULT if state.sprint_unlocked and keys[pygame.K_f] else 1.0
    max_speed = SPEED_PLAYER * speed_mult
    target_vel = state.playermovex * max_speed

    if state.playermovex != 0:
        state.x_vel += (target_vel - state.x_vel) * min(1.0, PLAYER_ACCEL * 0.28)
    else:
        state.x_vel *= PLAYER_FRICTION
        if abs(state.x_vel) < 0.08:
            state.x_vel = 0

    state.playerx += state.x_vel
    world_w = getattr(state, "world_width", WORLD_WIDTH)
    state.playerx = max(0, min(state.playerx, world_w - 40))

    if state.playermovex == 1:
        state.player = state.images['playeridet1']
        state.lookdir = 1
    elif state.playermovex == -1:
        state.player = state.images['playeridet2']
        state.lookdir = -1
    else:
        if state.player in (state.images['playeridet1'], state.images['playerstoit1']):
            state.player = state.images['playerstoit1']
            state.lookdir = 1
        elif state.player in (state.images['playeridet2'], state.images['playerstoit2']):
            state.player = state.images['playerstoit2']
            state.lookdir = -1

    on_ground = _on_ground(state, ground_y)

    if on_ground:
        state.playery = ground_y
        if state.playermovey > 0:
            state.playermovey = 0
        state.jump_holding = False
        state.jump_hold_timer = 0

    space = keys[pygame.K_SPACE]
    space_pressed = space and not state.prev_space
    space_released = not space and state.prev_space

    if space_pressed and on_ground:
        state.playermovey = JUMP_FORCE
        state.jump_holding = True
        state.jump_hold_timer = JUMP_HOLD_MAX
        state.otpuskal = False

    if space_released and state.playermovey < 0:
        state.playermovey *= JUMP_CUT_MULT
        state.jump_holding = False
        state.jump_hold_timer = 0

    if state.jump_holding and space and state.jump_hold_timer > 0 and state.playermovey < 0:
        state.jump_hold_timer -= 1
        state.playermovey -= JUMP_HOLD_BOOST
    elif not space or state.playermovey >= 0:
        state.jump_holding = False

    state.prev_space = space

    if not on_ground:
        state.playermovey = min(state.playermovey + GRAVITY_AIR, FALL_SPEED_MAX)

    if state.playery > ground_y:
        state.playery = ground_y
        state.playermovey = 0

    state.playery += state.playermovey * SPEED_PLAYER_Y


def handle_events(state, keys, ground_y, events=()):
    if state.dialog is None and keys[pygame.K_s] and state.otpuskal and state.playermovey == 0:
        state.playery += 40

    if state.atakazaderzhka > 0:
        state.atakazaderzhka -= 1

    for event in events:
        if event.type != pygame.KEYDOWN:
            continue
        if event.key == pygame.K_e:
            try_interact(state)
            continue
        if event.key == pygame.K_r:
            try_start_dash(state, keys)
            continue
        if state.dialog is not None:
            continue
        if state.dash_timer > 0:
            continue
        if state.atakapl or state.atakazaderzhka > 0:
            continue
        if event.key == pygame.K_RIGHT:
            state.atakapl = True
            state.flagatak = 1
            state.atakazaderzhka = ATAKA_ZADERZHKA
            state.boss_attack_hit = False
        elif event.key == pygame.K_LEFT:
            state.atakapl = True
            state.flagatak = 2
            state.atakazaderzhka = ATAKA_ZADERZHKA
            state.boss_attack_hit = False
        elif event.key == pygame.K_UP:
            state.atakapl = True
            state.flagatak = 3
            state.atakazaderzhka = ATAKA_ZADERZHKA
            state.boss_attack_hit = False
        elif event.key == pygame.K_DOWN:
            state.atakapl = True
            state.flagatak = 4
            state.atakazaderzhka = ATAKA_ZADERZHKA
            state.boss_attack_hit = False

    update_boss_combat(state)
