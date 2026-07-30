# logic.py
import math
import os
import pygame
from config import (
    GROUND_Y, SPEED_PLAYER, SPEED_PLAYER_Y, ATAKA_ZADERZHKA,
    JUMP_TIMER_MAX, JUMP_FORCE, JUMP_HOLD_MAX, JUMP_HOLD_BOOST, JUMP_CUT_MULT,
    GRAVITY_AIR, FALL_SPEED_MAX, WIDTH, HEIGHT, WORLD_WIDTH, HEALTH_MAX,
    NEUYAZVIMOST_MAX, BOSS_MAX_HP, BOSS_DAMAGE, BOSS_X, BOSS_Y,
    BOSS_W, BOSS_H, BOSS_ARENA_X, BOSS_MIN_X, BOSS_MAX_X,
    BOSS_SPEED, BOSS_SPEED_PHASE2, BOSS_SPEED_PHASE3, BOSS_HIT_COOLDOWN, BOSS_CONTACT_DAMAGE,
    KNOCKBACK_SIDE, KNOCKBACK_VERTICAL, KNOCKBACK_UP, KNOCKBACK_UP_MULT,
    KNOCKBACK_BLEND, KNOCKBACK_DECAY, KNOCKBACK_RISE_MAX,
    PLAYER_ACCEL, PLAYER_FRICTION, SPRINT_MULT,
    DASH_DURATION, DASH_SPEED, DASH_COOLDOWN,
    PLAYER_W, PLAYER_H,
    MAX_AKUM_POWER,
    CAM_FOLLOW_LERP, CAM_ARENA_LERP,
)
from level_loader import boss_drop, ABILITY_CATALOG
from boss_moves import (
    apply_event, phase_index_for_hp, pick_move_name,
    default_holodos_moveset,
)


def get_camera_x(state):
    cam_x, _ = get_camera(state)
    return cam_x


def _boss_camera_locked(state):
    """Статичная камера на арене, пока босс жив и арена заблокирована."""
    return (
        getattr(state, "boss_alive", False)
        and not getattr(state, "boss_dying", False)
        and getattr(state, "boss_arena_locked", False)
    )


def get_camera(state):
    """Камера с плавным следованием; на боссфайте левый край = arena_x."""
    target_y = state.playery - HEIGHT // 2
    if _boss_camera_locked(state):
        target_x = float(getattr(state, "boss_arena_x", BOSS_ARENA_X))
        lerp = CAM_ARENA_LERP
    else:
        target_x = state.playerx - WIDTH // 3
        lerp = CAM_FOLLOW_LERP

    if getattr(state, "cam_x", None) is None:
        state.cam_x = float(target_x)
        state.cam_y = float(target_y)
    else:
        state.cam_x += (target_x - state.cam_x) * lerp
        state.cam_y += (target_y - state.cam_y) * lerp
        # дотягиваем, если почти на месте — без дрожи
        if abs(target_x - state.cam_x) < 0.35:
            state.cam_x = float(target_x)
        if abs(target_y - state.cam_y) < 0.35:
            state.cam_y = float(target_y)

    return state.cam_x, state.cam_y


def _player_hitbox(state):
    return pygame.Rect(int(state.playerx), int(state.playery), PLAYER_W, PLAYER_H)


def resolve_walls(state, walls, axis):
    """Твёрдая коллизия со стенами. axis: 'x' или 'y'."""
    if not walls:
        return
    pr = _player_hitbox(state)
    for wall in walls:
        wr = pygame.Rect(wall.x, wall.y, wall.w, wall.h)
        if not pr.colliderect(wr):
            continue
        if axis == "x":
            if state.x_vel > 0 or (state.x_vel == 0 and pr.centerx <= wr.centerx):
                state.playerx = wr.left - PLAYER_W
            else:
                state.playerx = wr.right
            state.x_vel = 0
            pr.x = int(state.playerx)
        else:
            if state.playermovey > 0 or (state.playermovey == 0 and pr.centery <= wr.centery):
                state.playery = wr.top - PLAYER_H
                state.playermovey = 0
            else:
                state.playery = wr.bottom
                state.playermovey = 0
            pr.y = int(state.playery)


def resolve_platforms(state, pls):
    """Блокирует проход сквозь платформы снизу при прыжке вверх."""
    if not pls or state.playermovey >= 0:
        return
    pr = _player_hitbox(state)
    for pl in pls:
        plr = pygame.Rect(*pl.rect())
        if not pr.colliderect(plr):
            continue
        state.playery = plr.bottom
        state.playermovey = 0
        pr.y = int(state.playery)


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
    """Legacy helper — пишет в boss_projectiles как missile."""
    state.boss_projectiles.append({
        "kind": "missile", "x": x, "y": y, "vx": vx, "vy": vy,
        "life": 300, "damage": 1, "w": 36, "h": 64, "sprite": "boegolovka",
    })


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


def _update_boss_arena_lock(state):
    if not state.boss_alive or state.boss_dying:
        state.boss_arena_locked = False
        return
    if _boss_in_arena(state):
        state.boss_arena_locked = True


def _clamp_boss_arena(state):
    """Не даёт покинуть арену, пока босс жив или умирает."""
    _update_boss_arena_lock(state)
    if not state.boss_arena_locked:
        return
    arena = getattr(state, "boss_arena_x", BOSS_ARENA_X)
    left = arena - 200
    right = getattr(state, "boss_max_x", BOSS_MAX_X) - PLAYER_W
    if state.playerx < left:
        state.playerx = left
        state.x_vel = 0
        state.kb_vx = 0
    elif state.playerx > right:
        state.playerx = right
        state.x_vel = 0
        state.kb_vx = 0


def _boss_moveset(state):
    ms = getattr(state, "boss_moveset", None)
    if not ms:
        ms = default_holodos_moveset()
        state.boss_moveset = ms
    return ms


def _boss_refresh_phase(state):
    ms = _boss_moveset(state)
    ratio = max(0.0, state.boss_hp / BOSS_MAX_HP)
    idx, ph = phase_index_for_hp(ms, ratio)
    state.boss_phase = idx + 1
    return ph


def _boss_start_move(state, move_name):
    state.boss_move = move_name
    state.boss_move_timer = 0
    state.boss_anim = 0
    state.boss_sprite_mode = "idle"


def _boss_finish_move(state):
    ph = _boss_refresh_phase(state)
    state.boss_move = None
    state.boss_idle_timer = int(ph.get("idle", 60))
    state.boss_sprite_mode = "idle"
    state.boss_shake = 0


def _boss_pick_move(state):
    ms = _boss_moveset(state)
    ph = _boss_refresh_phase(state)
    name = pick_move_name(ms, ph, state.boss_last_move)
    if name is None:
        state.boss_idle_timer = int(ph.get("idle", 60))
        return
    state.boss_last_move = name
    _boss_start_move(state, name)


def _boss_update_move(state):
    move_name = state.boss_move
    if move_name is None:
        return

    ms = _boss_moveset(state)
    move = (ms.get("moves") or {}).get(move_name)
    if not move:
        _boss_finish_move(state)
        return

    state.boss_move_timer += 1
    state.boss_anim = (state.boss_anim + 1) % 30
    t = state.boss_move_timer

    if getattr(state, "boss_shake_timer", 0) > 0:
        state.boss_shake_timer -= 1
        if state.boss_shake_timer <= 0:
            state.boss_shake = 0

    for ev in move.get("events") or []:
        if int(ev.get("frame", -1)) == t:
            if apply_event(state, ev):
                _boss_finish_move(state)
                return

    duration = int(move.get("duration", 90))
    if t >= duration:
        _boss_finish_move(state)


def _update_boss_projectiles(state):
    world_w = getattr(state, "world_width", WORLD_WIDTH)
    world_top = getattr(state, "world_top", -400)
    alive = []
    for p in getattr(state, "boss_projectiles", []) or []:
        if p["kind"] == "ice" and p.get("rising", 0) > 0:
            p["y"] -= 3
            p["rising"] -= 1
        else:
            p["x"] += p.get("vx", 0)
            p["y"] += p.get("vy", 0)
        p["life"] = p.get("life", 300) - 1
        if p["life"] <= 0:
            continue
        if p["kind"] != "ice":
            if not (-80 < p["x"] < world_w + 80 and world_top - 80 < p["y"] < HEIGHT + 400):
                continue
        alive.append(p)
    state.boss_projectiles = alive
    state.snowflakes = []  # legacy cleared


def _boss_projectile_rect(p):
    return pygame.Rect(int(p["x"]), int(p["y"]), int(p.get("w", 24)), int(p.get("h", 24)))


def _update_boss_hazards(state):
    """Урон от снарядов и melee-хитбокса."""
    if state.neuyazvimost < NEUYAZVIMOST_MAX:
        return

    pr = _player_rect(state)

    melee = getattr(state, "boss_melee", None)
    if melee:
        melee["life"] -= 1
        mr = pygame.Rect(int(melee["x"]), int(melee["y"]), int(melee["w"]), int(melee["h"]))
        if pr.colliderect(mr):
            _damage_player(state, int(melee.get("damage", 1)))
        if melee["life"] <= 0:
            state.boss_melee = None

    if state.neuyazvimost < NEUYAZVIMOST_MAX:
        return

    hit_idx = None
    for i, p in enumerate(state.boss_projectiles):
        if pr.colliderect(_boss_projectile_rect(p)):
            hit_idx = i
            dmg = int(p.get("damage", 1))
            break
    if hit_idx is not None:
        _damage_player(state, dmg)
        # лёд не удаляем сразу — зона урона; ракеты/slash — да
        if state.boss_projectiles[hit_idx]["kind"] != "ice":
            del state.boss_projectiles[hit_idx]
    else:
        _boss_contact_damage(state)


def _spawn_boss_loot(state):
    if state.loot_spawned:
        return
    state.loot_spawned = True

    drop = boss_drop(getattr(state, "boss_id", "holodos"))
    if not drop:
        return

    bx, by = _boss_center(state)
    coins = drop["coins"]
    if coins > 0:
        step = 360 / coins
        for i in range(coins):
            angle = math.radians(i * step)
            state.coins.append({
                "x": bx + math.cos(angle) * 60,
                "y": by + math.sin(angle) * 40,
                "vx": math.cos(angle) * 3,
                "vy": math.sin(angle) * 3 - 2,
                "collected": False,
            })

    state.boss_loot = []
    for i, aid in enumerate(drop["abilities"]):
        if aid not in ABILITY_CATALOG:
            continue
        state.boss_loot.append({
            "type": "ability",
            "id": aid,
            "x": bx - 14 + i * 36,
            "y": by - 14,
            "active": True,
        })
    state.sprint_pickup = None
    for item in state.boss_loot:
        if item["id"] == "sprint":
            state.sprint_pickup = item
            break


def _grant_ability(state, ability_id):
    if ability_id == "sprint":
        state.sprint_podobran = True
        state.sprint_unlocked = True
    elif ability_id == "dash":
        state.dash_unlocked = True


def _boss_speed(state):
    if state.boss_phase >= 3:
        return BOSS_SPEED_PHASE3
    if state.boss_phase >= 2:
        return BOSS_SPEED_PHASE2
    return BOSS_SPEED


def _update_boss_position(state):
    if not state.boss_alive or state.boss_dying:
        return
    if not _boss_in_arena(state):
        return

    speed = _boss_speed(state)
    if getattr(state, "boss_shake_timer", 0) > 10:
        speed *= 1.5

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
    bob = 0
    if state.boss_phase >= 2:
        bob = int(math.sin(state.boss_anim * 0.15) * (10 + 4 * (state.boss_phase - 1)))
    state.boss_y = base_y + bob


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
            state.boss_dying = False
            _spawn_boss_loot(state)
        return

    if not state.boss_alive:
        return

    if not _boss_in_arena(state):
        return

    _boss_refresh_phase(state)

    if state.boss_move is None:
        state.boss_idle_timer -= 1
        if state.boss_idle_timer <= 0:
            _boss_pick_move(state)
    else:
        _boss_update_move(state)

    _update_boss_position(state)
    _update_boss_projectiles(state)
    _update_boss_hazards(state)


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
        _charge_akum(state)


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

    for item in getattr(state, "boss_loot", []) or []:
        if not item.get("active"):
            continue
        if _pickup_collision(state.playerx, state.playery, item["x"], item["y"]):
            item["active"] = False
            _grant_ability(state, item.get("id", "sprint"))

    # legacy single sprint_pickup (если не в boss_loot)
    if state.sprint_pickup and state.sprint_pickup.get("active"):
        p = state.sprint_pickup
        if p not in (getattr(state, "boss_loot", None) or []):
            if _pickup_collision(state.playerx, state.playery, p["x"], p["y"]):
                p["active"] = False
                _grant_ability(state, "sprint")


def _charge_akum(state):
    """+1 полоска за удар (0..MAX_AKUM_POWER)."""
    if state.akumpower >= MAX_AKUM_POWER:
        return
    state.akumpower += 1


def update_akum(state):
    keys = ['akum0', 'akum1', 'akum2', 'akum3', 'akum4', 'akum5']
    state.akum = state.images[keys[min(state.akumpower, MAX_AKUM_POWER)]]


_NO_GROUND = 10 ** 9


def get_ground_y(pls, playerx, playery, default_ground=None, walls=None):
    """Y опоры под игроком или None — тогда можно провалиться в пустоту.

    default_ground больше не создаёт невидимый пол (оставлен для совместимости API).
    """
    best = None
    for pl in pls:
        gy = pl.pup(playerx, playery, _NO_GROUND)
        if gy != _NO_GROUND:
            best = gy if best is None else min(best, gy)
    if walls:
        for wall in walls:
            gy = wall.pup(playerx, playery, _NO_GROUND)
            if gy != _NO_GROUND:
                best = gy if best is None else min(best, gy)
    return best


def _apply_ground(state, ground_y):
    """Примагнитить к опоре, если она есть."""
    if ground_y is None:
        return False
    state.playery = ground_y
    state.playermovey = 0
    return True


def _fall_death(state):
    """Смерть при глубоком падении в пустоту."""
    floor_ref = getattr(state, "ground_y_default", GROUND_Y)
    if state.playery > floor_ref + 900:
        state.health = 0


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
        _grant_ability(state, pickup.get("id", "sprint"))
    elif pickup["type"] == "sprint_skill":
        _grant_ability(state, "sprint")
    elif pickup["type"] == "dash_skill":
        _grant_ability(state, "dash")


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


def _find_nearby_checkpoint(state):
    for cp in getattr(state, "checkpoints", []) or []:
        if _near_rect(state.playerx, state.playery, cp["x"], cp["y"], 36, 48, pad=16):
            return cp
    return None


def use_checkpoint(state, cp):
    """E у точки сохранения: пишет save.json и запоминает респавн."""
    from savegame import write_save

    data = {
        "level_path": getattr(state, "current_level_path", None) or "levels/level1.json",
        "x": float(cp["x"]),
        "y": float(cp["y"]),
        "health": HEALTH_MAX,
        "sprint_unlocked": bool(getattr(state, "sprint_unlocked", False)),
        "dash_unlocked": bool(getattr(state, "dash_unlocked", False)),
        "akumpower": int(getattr(state, "akumpower", 0)),
    }
    state.checkpoint = write_save(data)
    state.save_flash = 90
    state.interact_hint = "Сохранено!"


def apply_checkpoint_progress(state, data):
    """Восстанавливает прогресс из сохранения (абилки и т.п.)."""
    if not data:
        return
    state.sprint_unlocked = bool(data.get("sprint_unlocked", False))
    state.dash_unlocked = bool(data.get("dash_unlocked", False))
    state.akumpower = int(data.get("akumpower", 0))
    hp = int(data.get("health", HEALTH_MAX))
    state.health = max(1, min(HEALTH_MAX, hp))


def request_respawn_from_checkpoint(state):
    """При смерти: респавн у последнего сохранения. True если удалось."""
    from savegame import read_save
    from level_loader import resolve_level_path

    data = getattr(state, "checkpoint", None) or read_save()
    if not data:
        return False

    path = resolve_level_path(data.get("level_path")) or data.get("level_path")
    if not path or not os.path.exists(path):
        return False

    apply_checkpoint_progress(state, data)
    state.health = HEALTH_MAX
    state.neuyazvimost = 0
    state.x_vel = 0
    state.playermovey = 0
    state.y_vel = 0
    state.kb_vx = 0.0
    state.kb_vy = 0.0
    state.dialog = None
    state.atakapl = False
    state.flagatak = 0
    state.boss_arena_locked = False

    cur = getattr(state, "current_level_path", None)
    same = cur and os.path.abspath(cur) == os.path.abspath(path)
    if same:
        state.playerx = float(data["x"])
        state.playery = float(data["y"])
        state.cam_x = None
        state.cam_y = None
        state.checkpoint = data
        return True

    state.pending_respawn = {
        "path": path,
        "spawn_x": float(data["x"]),
        "spawn_y": float(data["y"]),
        "label": os.path.splitext(os.path.basename(path))[0],
        "progress": data,
    }
    state.checkpoint = data
    return True


def _request_level_transition(state, tp):
    """Ставит переход на другой уровень (обработает main после кадра)."""
    from level_loader import resolve_level_path, load_level

    path = resolve_level_path(tp.get("target_level"))
    if not path:
        return False
    if not os.path.exists(path):
        state.interact_hint = f"Нет файла: {path}"
        return False

    dest = load_level(path)
    spawn = dest.get("player_spawn") or {}
    sx = tp.get("target_x")
    sy = tp.get("target_y")
    # если цель не задана явно — спавн целевого уровня
    if sx is None:
        sx = spawn.get("x", 120)
    if sy is None:
        sy = spawn.get("y", 640)
    state.pending_level = {
        "path": path,
        "spawn_x": float(sx),
        "spawn_y": float(sy),
        "label": dest.get("name") or os.path.splitext(os.path.basename(path))[0],
    }
    return True


def update_interactions(state):
    """Подсказки взаимодействия и телепорт при касании метки."""
    if getattr(state, "save_flash", 0) > 0:
        state.save_flash -= 1
        state.interact_hint = "Сохранено!"
        if state.dialog is not None:
            state.interact_hint = "E — дальше"
        return

    state.interact_hint = None

    if state.dialog is not None:
        state.interact_hint = "E — дальше"
        return

    if getattr(state, "pending_level", None) or getattr(state, "pending_respawn", None):
        return

    if state.teleport_cooldown > 0:
        state.teleport_cooldown -= 1

    npc_i, npc = _find_nearby_npc(state)
    if npc is not None:
        state.interact_hint = f"E — говорить ({npc['name']})"

    cp = _find_nearby_checkpoint(state)
    if cp is not None and state.interact_hint is None:
        state.interact_hint = "E — сохранить"

    tp = _find_nearby_teleport(state)
    if tp is not None:
        dest = (tp.get("target_level") or "").strip()
        if state.interact_hint is None:
            if dest:
                state.interact_hint = f"Телепорт → {dest}"
            else:
                state.interact_hint = "Телепорт..."
        if state.teleport_cooldown <= 0:
            if dest:
                if _request_level_transition(state, tp):
                    state.teleport_cooldown = 45
                    state.x_vel = 0
                    state.playermovey = 0
            else:
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
    """Нажатие E: диалог, сохранение или лечение акумом."""
    if state.dialog is not None:
        _advance_dialog(state)
        return

    npc_i, npc = _find_nearby_npc(state)
    if npc is not None:
        _start_dialog(state, npc)
        return

    cp = _find_nearby_checkpoint(state)
    if cp is not None:
        use_checkpoint(state, cp)
        return

    if state.akumpower >= MAX_AKUM_POWER:
        state.akumpower = 0
        if state.health < HEALTH_MAX:
            state.health += 1


def update_player_movement(state, keys, ground_y, walls=None, pls=None):
    walls = walls or []
    pls = pls or []
    if state.boss_shake > 0 and getattr(state, "boss_shake_timer", 0) <= 0:
        state.boss_shake = max(0, state.boss_shake - 1)

    if state.dash_cooldown > 0 and state.dash_timer <= 0:
        state.dash_cooldown -= 1

    if state.dialog is not None:
        state.x_vel = 0
        state.playermovex = 0
        state.kb_vx = 0
        state.kb_vy = 0
        state.dash_timer = 0
        on_ground = ground_y is not None and _on_ground(state, ground_y)
        if on_ground:
            _apply_ground(state, ground_y)
        _clamp_boss_arena(state)
        return

    # Рывок: очень быстрый горизонтальный сдвиг ~0.3 с
    if state.dash_timer > 0:
        state.dash_timer -= 1
        state.x_vel = state.dash_dir * DASH_SPEED
        state.playerx += state.x_vel
        resolve_walls(state, walls, "x")
        on_ground = ground_y is not None and _on_ground(state, ground_y)
        if on_ground:
            _apply_ground(state, ground_y)
        else:
            state.playermovey = min(state.playermovey + GRAVITY_AIR * 0.35, FALL_SPEED_MAX * 0.4)
            state.playery += state.playermovey * SPEED_PLAYER_Y
            resolve_walls(state, walls, "y")
            resolve_platforms(state, pls)
            if ground_y is not None and state.playery > ground_y:
                _apply_ground(state, ground_y)
        if state.dash_timer <= 0:
            state.x_vel *= 0.35
            state.dash_cooldown = DASH_COOLDOWN
        _fall_death(state)
        _clamp_boss_arena(state)
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
    resolve_walls(state, walls, "x")

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

    on_ground = ground_y is not None and _on_ground(state, ground_y)

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

    if ground_y is not None and state.playery > ground_y:
        state.playery = ground_y
        state.playermovey = 0

    state.playery += state.playermovey * SPEED_PLAYER_Y
    resolve_walls(state, walls, "y")
    resolve_platforms(state, pls)
    if ground_y is not None and state.playery > ground_y:
        state.playery = ground_y
        state.playermovey = 0
    _fall_death(state)
    _clamp_boss_arena(state)


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
