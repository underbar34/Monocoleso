# boss_moves.py
"""Таймлайн-мувсеты боссов: каталог действий, дефолты Холодоса, resolve/apply."""
import copy
import math
import random


# Параметры действий для UI редактора
ACTIONS = {
    "set_sprite": {
        "label": "Спрайт босса",
        "fields": [
            {"key": "sprite", "type": "choice", "choices": [
                "idle", "attack_left", "attack_right", "attack_left2", "attack_right2",
            ]},
        ],
    },
    "missile": {
        "label": "Ракета (boegolovka)",
        "fields": [
            {"key": "mode", "type": "choice", "choices": ["aim", "spread", "angle", "ring"]},
            {"key": "speed", "type": "float", "default": 5.5},
            {"key": "count", "type": "int", "default": 1},
            {"key": "spread_deg", "type": "float", "default": 40},
            {"key": "angle_deg", "type": "float", "default": 0},
        ],
    },
    "slash_proj": {
        "label": "Slash-снаряд",
        "fields": [
            {"key": "side", "type": "choice", "choices": ["auto", "left", "right"]},
            {"key": "speed", "type": "float", "default": 7.0},
        ],
    },
    "melee": {
        "label": "Ближняя атака",
        "fields": [
            {"key": "side", "type": "choice", "choices": ["auto", "left", "right"]},
            {"key": "atk_frame", "type": "choice", "choices": ["1", "2"]},
            {"key": "duration", "type": "int", "default": 18},
            {"key": "damage", "type": "int", "default": 1},
        ],
    },
    "ice_rise": {
        "label": "Лёд снизу",
        "fields": [
            {"key": "target", "type": "choice", "choices": ["player", "boss", "arena"]},
            {"key": "offset_x", "type": "int", "default": 0},
            {"key": "lifetime", "type": "int", "default": 90},
            {"key": "damage", "type": "int", "default": 1},
        ],
    },
    "shake": {
        "label": "Тряска",
        "fields": [
            {"key": "amount", "type": "int", "default": 6},
            {"key": "frames", "type": "int", "default": 20},
        ],
    },
    "end": {
        "label": "Конец мува",
        "fields": [],
    },
}

SPRITE_KEYS = {
    "idle": None,  # цикл holodos1-4
    "attack_left": "holodos_atk_left1",
    "attack_left2": "holodos_atk_left2",
    "attack_right": "holodos_atk_right1",
    "attack_right2": "holodos_atk_right2",
}


def default_holodos_moveset():
    """3 фазы, атаки на реальных ассетах, idle сокращается с фазой."""
    return {
        "phases": [
            {
                "hp_below": 1.0,
                "idle": 90,
                "moves": ["aim_missile", "side_slash"],
            },
            {
                "hp_below": 0.66,
                "idle": 55,
                "moves": ["aim_missile", "ice_trap", "double_slash", "melee_swipe"],
            },
            {
                "hp_below": 0.33,
                "idle": 30,
                "moves": ["rage_combo", "ice_trap", "missile_fan", "melee_swipe"],
            },
        ],
        "moves": {
            "aim_missile": {
                "duration": 70,
                "events": [
                    {"frame": 8, "action": "set_sprite", "sprite": "attack_right"},
                    {"frame": 36, "action": "missile", "mode": "aim", "speed": 5.5, "count": 1},
                    {"frame": 52, "action": "set_sprite", "sprite": "idle"},
                ],
            },
            "side_slash": {
                "duration": 65,
                "events": [
                    {"frame": 10, "action": "set_sprite", "sprite": "attack_left"},
                    {"frame": 28, "action": "slash_proj", "side": "auto", "speed": 7.5},
                    {"frame": 45, "action": "set_sprite", "sprite": "idle"},
                ],
            },
            "ice_trap": {
                "duration": 80,
                "events": [
                    {"frame": 5, "action": "shake", "amount": 4, "frames": 15},
                    {"frame": 20, "action": "set_sprite", "sprite": "attack_left2"},
                    {"frame": 35, "action": "ice_rise", "target": "player", "offset_x": 0, "lifetime": 100},
                    {"frame": 55, "action": "set_sprite", "sprite": "idle"},
                ],
            },
            "double_slash": {
                "duration": 85,
                "events": [
                    {"frame": 8, "action": "set_sprite", "sprite": "attack_left"},
                    {"frame": 22, "action": "slash_proj", "side": "left", "speed": 8.0},
                    {"frame": 40, "action": "set_sprite", "sprite": "attack_right"},
                    {"frame": 52, "action": "slash_proj", "side": "right", "speed": 8.0},
                    {"frame": 68, "action": "set_sprite", "sprite": "idle"},
                ],
            },
            "melee_swipe": {
                "duration": 70,
                "events": [
                    {"frame": 5, "action": "set_sprite", "sprite": "attack_left"},
                    {"frame": 18, "action": "melee", "side": "auto", "atk_frame": "1", "duration": 16},
                    {"frame": 36, "action": "set_sprite", "sprite": "attack_left2"},
                    {"frame": 42, "action": "melee", "side": "auto", "atk_frame": "2", "duration": 14},
                    {"frame": 58, "action": "set_sprite", "sprite": "idle"},
                ],
            },
            "missile_fan": {
                "duration": 75,
                "events": [
                    {"frame": 10, "action": "set_sprite", "sprite": "attack_right2"},
                    {"frame": 28, "action": "missile", "mode": "spread", "speed": 5.0, "count": 5, "spread_deg": 55},
                    {"frame": 48, "action": "missile", "mode": "aim", "speed": 6.5, "count": 1},
                    {"frame": 60, "action": "set_sprite", "sprite": "idle"},
                ],
            },
            "rage_combo": {
                "duration": 110,
                "events": [
                    {"frame": 1, "action": "shake", "amount": 8, "frames": 25},
                    {"frame": 12, "action": "set_sprite", "sprite": "attack_right"},
                    {"frame": 22, "action": "missile", "mode": "ring", "speed": 4.5, "count": 8},
                    {"frame": 40, "action": "set_sprite", "sprite": "attack_left"},
                    {"frame": 48, "action": "melee", "side": "auto", "atk_frame": "1", "duration": 18},
                    {"frame": 58, "action": "ice_rise", "target": "player", "offset_x": -80, "lifetime": 80},
                    {"frame": 62, "action": "ice_rise", "target": "player", "offset_x": 80, "lifetime": 80},
                    {"frame": 78, "action": "slash_proj", "side": "auto", "speed": 9.0},
                    {"frame": 90, "action": "set_sprite", "sprite": "idle"},
                ],
            },
        },
    }


def empty_event(action="missile"):
    """Событие с дефолтными полями для редактора."""
    meta = ACTIONS.get(action, ACTIONS["missile"])
    ev = {"frame": 10, "action": action}
    for f in meta["fields"]:
        key = f.get("store_as", f["key"])
        if "default" in f:
            ev[key] = f["default"]
        elif f["type"] == "choice" and f.get("choices"):
            ev[key] = f["choices"][0]
    return ev


def deep_copy_moveset(ms):
    return copy.deepcopy(ms)


def resolve_moveset(boss_obj_or_id, catalog_moveset=None):
    """
    Склеивает moveset объекта уровня с дефолтом каталога.
    boss_obj_or_id: dict босса или id строки.
    """
    default = catalog_moveset
    if default is None:
        default = default_holodos_moveset()

    if isinstance(boss_obj_or_id, dict):
        override = boss_obj_or_id.get("moveset")
        bid = boss_obj_or_id.get("id", "holodos")
    else:
        override = None
        bid = boss_obj_or_id or "holodos"

    if not override:
        return deep_copy_moveset(default)

    result = deep_copy_moveset(default)
    if "phases" in override and override["phases"]:
        result["phases"] = copy.deepcopy(override["phases"])
    if "moves" in override and override["moves"]:
        # Полная замена словаря мувов, если задан; иначе merge
        if override.get("replace_moves"):
            result["moves"] = copy.deepcopy(override["moves"])
        else:
            result["moves"].update(copy.deepcopy(override["moves"]))
    return result


def phase_index_for_hp(moveset, hp_ratio):
    """Индекс фазы 0..n-1. Фазы отсортированы по hp_below убыванию."""
    phases = sorted(moveset.get("phases", []), key=lambda p: -float(p.get("hp_below", 1.0)))
    if not phases:
        return 0, {"hp_below": 1.0, "idle": 90, "moves": []}
    chosen_i = 0
    for i, ph in enumerate(phases):
        if hp_ratio <= float(ph.get("hp_below", 1.0)):
            chosen_i = i
    # Берём самую «низкую» подходящую: среди тех где hp <= hp_below, с минимальным hp_below
    eligible = [i for i, ph in enumerate(phases) if hp_ratio <= float(ph.get("hp_below", 1.0))]
    if not eligible:
        chosen_i = 0
    else:
        # среди eligible выбрать с наименьшим hp_below (самая жёсткая фаза)
        chosen_i = min(eligible, key=lambda i: float(phases[i].get("hp_below", 1.0)))
    return chosen_i, phases[chosen_i]


def phase_number(moveset, hp_ratio):
    idx, _ = phase_index_for_hp(moveset, hp_ratio)
    return idx + 1


def pick_move_name(moveset, phase_data, last_move):
    options = list(phase_data.get("moves") or [])
    options = [m for m in options if m in (moveset.get("moves") or {})]
    if not options:
        return None
    if last_move in options and len(options) > 1:
        options = [m for m in options if m != last_move]
    return random.choice(options)


def _boss_center(state):
    from config import BOSS_W, BOSS_H
    return state.boss_x + BOSS_W // 2, state.boss_y + BOSS_H // 2


def _aim_vel(state, speed, spread=0.0):
    bx, by = _boss_center(state)
    dx = state.playerx + 20 - bx
    dy = state.playery + 25 - by
    dist = math.hypot(dx, dy) or 1
    angle = math.atan2(dy, dx) + spread
    return speed * math.cos(angle), speed * math.sin(angle)


def _spawn_projectile(state, kind, x, y, vx, vy, **extra):
    proj = {
        "kind": kind,
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "life": extra.get("life", 300),
        "damage": extra.get("damage", 1),
        "w": extra.get("w", 24),
        "h": extra.get("h", 24),
        "side": extra.get("side", "right"),
        "sprite": extra.get("sprite"),
    }
    proj.update({k: v for k, v in extra.items() if k not in proj})
    state.boss_projectiles.append(proj)


def apply_event(state, event):
    """Выполнить одно событие таймлайна. Возвращает True если мув надо завершить."""
    from config import BOSS_W, BOSS_H

    action = event.get("action")
    if action == "end":
        return True

    if action == "set_sprite":
        state.boss_sprite_mode = event.get("sprite", "idle")
        return False

    if action == "shake":
        state.boss_shake = int(event.get("amount", 6))
        state.boss_shake_timer = int(event.get("frames", 20))
        return False

    bx, by = _boss_center(state)

    if action == "missile":
        mode = event.get("mode", "aim")
        speed = float(event.get("speed", 5.5))
        count = int(event.get("count", 1))
        spread_deg = float(event.get("spread_deg", 40))
        if mode == "aim":
            for _ in range(max(1, count)):
                vx, vy = _aim_vel(state, speed)
                _spawn_projectile(
                    state, "missile", bx, by - 40, vx, vy,
                    w=36, h=64, sprite="boegolovka",
                )
        elif mode == "spread":
            base = math.atan2(state.playery + 25 - by, state.playerx + 20 - bx)
            n = max(1, count)
            step = math.radians(spread_deg) / max(n - 1, 1)
            start = base - math.radians(spread_deg) / 2
            for i in range(n):
                a = start + step * i
                _spawn_projectile(
                    state, "missile", bx, by - 40,
                    speed * math.cos(a), speed * math.sin(a),
                    w=36, h=64, sprite="boegolovka",
                )
        elif mode == "ring":
            n = max(1, count)
            for i in range(n):
                a = 2 * math.pi * i / n
                _spawn_projectile(
                    state, "missile", bx, by,
                    speed * math.cos(a), speed * math.sin(a),
                    w=36, h=64, sprite="boegolovka",
                )
        elif mode == "angle":
            a = math.radians(float(event.get("angle_deg", 0)))
            for _ in range(max(1, count)):
                _spawn_projectile(
                    state, "missile", bx, by - 40,
                    speed * math.cos(a), speed * math.sin(a),
                    w=36, h=64, sprite="boegolovka",
                )
        return False

    if action == "slash_proj":
        side = event.get("side", "auto")
        speed = float(event.get("speed", 7.0))
        if side == "auto":
            side = "left" if state.playerx + 20 < bx else "right"
        if side == "left":
            vx, sprite = -speed, "holodos_slash_left"
            x = state.boss_x - 40
        else:
            vx, sprite = speed, "holodos_slash_right"
            x = state.boss_x + BOSS_W + 10
        y = state.boss_y + BOSS_H // 2 - 30
        _spawn_projectile(
            state, "slash", x, y, vx, 0,
            w=160, h=48, side=side, sprite=sprite, life=180,
        )
        return False

    if action == "melee":
        side = event.get("side", "auto")
        if side == "auto":
            side = "left" if state.playerx + 20 < bx else "right"
        atk_frame = str(event.get("atk_frame", "1"))
        if atk_frame not in ("1", "2"):
            atk_frame = "1"
        duration = int(event.get("duration", 18))
        damage = int(event.get("damage", 1))
        if side == "left":
            sprite = f"holodos_atk_left{atk_frame}"
            state.boss_sprite_mode = "attack_left" if atk_frame == "1" else "attack_left2"
            hx = state.boss_x - 180
        else:
            sprite = f"holodos_atk_right{atk_frame}"
            state.boss_sprite_mode = "attack_right" if atk_frame == "1" else "attack_right2"
            hx = state.boss_x + BOSS_W - 40
        hy = state.boss_y + 80
        state.boss_melee = {
            "x": hx,
            "y": hy,
            "w": 220,
            "h": 280,
            "life": duration,
            "damage": damage,
            "sprite": sprite,
            "side": side,
        }
        return False

    if action == "ice_rise":
        target = event.get("target", "player")
        offset_x = int(event.get("offset_x", 0))
        lifetime = int(event.get("lifetime", 90))
        damage = int(event.get("damage", 1))
        ice_w = 280
        if target == "player":
            cx = state.playerx + 20 + offset_x
        elif target == "boss":
            cx = bx + offset_x
        else:
            arena = getattr(state, "boss_arena_x", 0)
            max_x = getattr(state, "boss_max_x", arena + 2000)
            cx = (arena + max_x) // 2 + offset_x
        # лёд у «земли» под игроком / боссом
        ground = getattr(state, "ground_y_default", None)
        if ground is None:
            ice_y = state.playery + 40
        else:
            ice_y = ground - 40
        # если игрок в воздухе — лёд под его ногами
        ice_y = max(state.playery + 30, ice_y - 20)
        _spawn_projectile(
            state, "ice", cx - ice_w // 2, ice_y,
            0, 0,
            w=ice_w, h=48, sprite="holodos_ice",
            life=lifetime, damage=damage, rising=12,
        )
        return False

    return False


def event_summary(ev):
    """Короткая строка для списка в редакторе."""
    action = ev.get("action", "?")
    parts = [f"{ev.get('frame', 0):>3}", action]
    if action == "set_sprite":
        parts.append(str(ev.get("sprite", "")))
    elif action == "missile":
        parts.append(str(ev.get("mode", "aim")))
        parts.append(f"spd={ev.get('speed', 5)}")
        if int(ev.get("count", 1)) > 1:
            parts.append(f"n={ev.get('count')}")
    elif action == "slash_proj":
        parts.append(str(ev.get("side", "auto")))
        parts.append(f"spd={ev.get('speed', 7)}")
    elif action == "melee":
        parts.append(str(ev.get("side", "auto")))
        parts.append(f"f{ev.get('atk_frame', 1)}")
    elif action == "ice_rise":
        parts.append(str(ev.get("target", "player")))
        if ev.get("offset_x"):
            parts.append(f"ox={ev.get('offset_x')}")
    elif action == "shake":
        parts.append(f"a={ev.get('amount', 6)}")
    return " ".join(parts)
