# enemies.py
"""Побочные враги: патруль влево/вправо, разворот у обрыва."""
import pygame
from config import FPS, PLAYER_W, PLAYER_H

ENEMY_W = 36
ENEMY_H = 44
ENEMY_SPEED = 1.55
PATROL_FRAMES = FPS * 2  # 2 секунды в каждую сторону
CLIFF_LOOK_AHEAD = 22
CLIFF_DROP = 36  # насколько ниже земля = обрыв
ENEMY_DAMAGE = 1


def make_enemy_from_object(obj):
    d = int(obj.get("dir", 1))
    if d == 0:
        d = 1
    d = 1 if d > 0 else -1
    return {
        "x": float(obj["x"]),
        "y": float(obj["y"]),
        "w": int(obj.get("w", ENEMY_W)),
        "h": int(obj.get("h", ENEMY_H)),
        "dir": d,
        "timer": PATROL_FRAMES,
        "alive": True,
        "texture": obj.get("texture"),
        "anim": 0,
    }


def _platform_top_at(pls, walls, x, prefer_y):
    """Y верхней грани опоры под x рядом с prefer_y, или None."""
    best = None
    best_dist = None
    for pl in pls or []:
        if pl.x - 4 <= x <= pl.x + pl.shir + 4:
            top = pl.y
            dist = abs(top - prefer_y)
            if dist > 220:
                continue
            if best is None or dist < best_dist:
                best, best_dist = top, dist
    for wall in walls or []:
        if wall.x - 4 <= x <= wall.x + wall.w + 4:
            top = wall.y
            dist = abs(top - prefer_y)
            if dist > 220:
                continue
            if best is None or dist < best_dist:
                best, best_dist = top, dist
    return best


def _enemy_rect(e):
    return pygame.Rect(int(e["x"]), int(e["y"]), e["w"], e["h"])


def _hits_wall(e, walls, nx):
    test = pygame.Rect(int(nx), int(e["y"]), e["w"], e["h"])
    for wall in walls or []:
        wr = pygame.Rect(wall.x, wall.y, wall.w, wall.h)
        if test.colliderect(wr):
            return True
    return False


def _sees_cliff(e, pls, walls, at_x=None):
    """Впереди нет земли или она заметно ниже — обрыв."""
    x = e["x"] if at_x is None else at_x
    feet_y = e["y"] + e["h"]
    cx = x + e["w"] / 2
    cur = _platform_top_at(pls, walls, cx, feet_y)
    if cur is None:
        return True
    ahead_x = cx + e["dir"] * (e["w"] / 2 + CLIFF_LOOK_AHEAD)
    ahead = _platform_top_at(pls, walls, ahead_x, feet_y)
    if ahead is None:
        return True
    return ahead > cur + CLIFF_DROP


def _turn(e):
    e["dir"] = -int(e["dir"])
    e["timer"] = PATROL_FRAMES


def _snap_to_ground(e, pls, walls):
    feet = e["y"] + e["h"]
    top = _platform_top_at(pls, walls, e["x"] + e["w"] / 2, feet)
    if top is None:
        return
    target_y = top - e["h"]
    if abs(e["y"] - target_y) < 80:
        e["y"] = float(target_y)


def update_enemies(state, pls=None, walls=None):
    enemies = getattr(state, "enemies", None)
    if not enemies:
        return
    pls = pls or []
    walls = walls or []

    from logic import _attack_rect, _charge_akum, _damage_player

    pr = pygame.Rect(int(state.playerx), int(state.playery), PLAYER_W, PLAYER_H)
    atk = _attack_rect(state) if state.atakapl else None

    for e in enemies:
        if not e.get("alive", True):
            continue

        if atk is not None and atk.colliderect(_enemy_rect(e)):
            e["alive"] = False
            _charge_akum(state)
            continue

        _snap_to_ground(e, pls, walls)
        e["anim"] = (e.get("anim", 0) + 1) % 40
        e["timer"] = int(e.get("timer", PATROL_FRAMES)) - 1

        if _sees_cliff(e, pls, walls) or _hits_wall(e, walls, e["x"] + e["dir"] * ENEMY_SPEED):
            _turn(e)
        elif e["timer"] <= 0:
            _turn(e)

        nx = e["x"] + e["dir"] * ENEMY_SPEED
        if _hits_wall(e, walls, nx) or _sees_cliff(e, pls, walls, at_x=nx):
            _turn(e)
            nx = e["x"] + e["dir"] * ENEMY_SPEED
            if _hits_wall(e, walls, nx):
                nx = e["x"]
        e["x"] = nx
        _snap_to_ground(e, pls, walls)

        if pr.colliderect(_enemy_rect(e)):
            _damage_player(state, ENEMY_DAMAGE)
