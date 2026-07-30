# render.py
import pygame
from config import (
    HEALTH_MAX, ATAKA_KADRY, WIDTH, HEIGHT, BOSS_MAX_HP, WALL_W, WALL_H,
)
from logic import get_camera, _boss_in_arena
from level_loader import ABILITY_CATALOG
from textures import load_texture
from platforms import PLATFORM_H

NPC_W, NPC_H = 36, 50
TELEPORT_R = 18
PICKUP_SIZE = 28


def _resolve_img(state, texture, default_key, fit=None, max_size=None):
    if texture:
        img = load_texture(texture, state.texture_cache, fit=fit, max_size=max_size)
        if img is not None:
            return img
    return state.images.get(default_key)


def _boss_sprite_key(state):
    if state.boss_dying:
        frame = min(state.boss_death_timer // 30, 2)
        return f"holodos_dead{frame + 1}"

    # Тело босса всегда idle-цикл; VFX атак рисуются отдельно (melee / projectiles)
    frame = (state.boss_anim // 10) % 3 + 1
    if state.boss_phase >= 2:
        return f"holodos{min(frame + 1, 4)}"
    return f"holodos{frame}"


def _draw_boss_hp_bar(screen, state):
    if not state.boss_alive or state.boss_dying:
        return
    if not _boss_in_arena(state):
        return

    bar_w = 400
    bar_h = 18
    bar_x = (WIDTH - bar_w) // 2
    bar_y = 36
    ratio = max(0, state.boss_hp) / BOSS_MAX_HP

    pygame.draw.rect(screen, (60, 60, 60), (bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4))
    pygame.draw.rect(screen, (40, 40, 40), (bar_x, bar_y, bar_w, bar_h))
    colors = {1: (100, 200, 255), 2: (255, 180, 80), 3: (255, 80, 80)}
    color = colors.get(state.boss_phase, (100, 200, 255))
    pygame.draw.rect(screen, color, (bar_x, bar_y, int(bar_w * ratio), bar_h))

    font = pygame.font.SysFont("dejavusans", 16, bold=True)
    label = f"Холодос — Фаза {state.boss_phase}"
    text = font.render(f"{label}  {max(0, state.boss_hp)}/{BOSS_MAX_HP}", True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=(WIDTH // 2, bar_y - 12)))


def _draw_boss_projectiles(screen, state, cam_x, cam_y):
    view_l, view_r = cam_x - 80, cam_x + WIDTH + 80
    view_t, view_b = cam_y - 80, cam_y + HEIGHT + 80
    for p in getattr(state, "boss_projectiles", []) or []:
        if p["x"] + p.get("w", 24) < view_l or p["x"] > view_r:
            continue
        if p["y"] + p.get("h", 24) < view_t or p["y"] > view_b:
            continue
        key = p.get("sprite")
        img = state.images.get(key) if key else None
        if img is not None:
            screen.blit(img, (p["x"] - cam_x, p["y"] - cam_y))
        else:
            r = pygame.Rect(p["x"] - cam_x, p["y"] - cam_y, p.get("w", 16), p.get("h", 16))
            pygame.draw.rect(screen, (180, 220, 255), r)

    melee = getattr(state, "boss_melee", None)
    if melee:
        key = melee.get("sprite")
        img = state.images.get(key) if key else None
        if img is not None:
            screen.blit(img, (melee["x"] - cam_x, melee["y"] - cam_y))
        else:
            r = pygame.Rect(
                melee["x"] - cam_x, melee["y"] - cam_y,
                melee.get("w", 100), melee.get("h", 100),
            )
            pygame.draw.rect(screen, (255, 100, 100), r, 2)


def _draw_npc(screen, npc, cam_x, cam_y, state=None):
    sx, sy = npc["x"] - cam_x, npc["y"] - cam_y
    tex = npc.get("texture") if state else None
    img = None
    if state and tex:
        img = load_texture(tex, state.texture_cache, max_size=(80, 100))
    if img is not None:
        screen.blit(img, (sx, sy))
    else:
        body = pygame.Rect(sx, sy, NPC_W, NPC_H)
        pygame.draw.rect(screen, (255, 152, 0), body)
        pygame.draw.rect(screen, (80, 50, 0), body, 2)
        pygame.draw.circle(screen, (255, 220, 180), (sx + NPC_W // 2, sy + 10), 10)
    font = pygame.font.SysFont("dejavusans", 14)
    name = font.render(npc.get("name", "NPC"), True, (40, 40, 40))
    mid_x = sx + (img.get_width() // 2 if img is not None else NPC_W // 2)
    screen.blit(name, name.get_rect(midbottom=(mid_x, sy - 4)))


def _draw_teleport(screen, tp, cam_x, cam_y, state=None):
    sx = tp["x"] - cam_x
    sy = tp["y"] - cam_y
    tex = tp.get("texture") if state else None
    img = None
    if state and tex:
        img = load_texture(tex, state.texture_cache, max_size=(48, 48))
    if img is not None:
        screen.blit(img, (sx, sy))
        return
    cx, cy = sx + TELEPORT_R, sy + TELEPORT_R
    pygame.draw.circle(screen, (0, 188, 212), (cx, cy), TELEPORT_R)
    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), TELEPORT_R - 6, 2)


def _draw_checkpoint(screen, cp, cam_x, cam_y, state=None):
    sx = cp["x"] - cam_x
    sy = cp["y"] - cam_y
    tex = cp.get("texture") if state else None
    img = None
    if state and tex:
        img = load_texture(tex, state.texture_cache, max_size=(48, 64))
    if img is not None:
        screen.blit(img, (sx, sy))
        return
    # флажок / столб
    pole = pygame.Rect(sx + 14, sy + 8, 6, 40)
    pygame.draw.rect(screen, (90, 70, 40), pole)
    flag = [(sx + 20, sy + 8), (sx + 42, sy + 18), (sx + 20, sy + 28)]
    pygame.draw.polygon(screen, (255, 215, 64), flag)
    pygame.draw.polygon(screen, (200, 160, 30), flag, 1)
    pygame.draw.circle(screen, (255, 240, 150), (sx + 17, sy + 8), 4)


def _draw_dialog(screen, state):
    d = state.dialog
    if d is None:
        return
    box_h = 140
    box = pygame.Rect(40, HEIGHT - box_h - 20, WIDTH - 80, box_h)
    overlay = pygame.Surface((box.w, box.h), pygame.SRCALPHA)
    overlay.fill((20, 24, 32, 220))
    screen.blit(overlay, box.topleft)
    pygame.draw.rect(screen, (0, 188, 212), box, 2, border_radius=6)

    font_name = pygame.font.SysFont("dejavusans", 22, bold=True)
    font_body = pygame.font.SysFont("dejavusans", 20)
    font_hint = pygame.font.SysFont("dejavusans", 14)

    name = font_name.render(d["name"], True, (0, 188, 212))
    screen.blit(name, (box.x + 20, box.y + 14))

    idx = d["index"]
    line = d["lines"][idx] if 0 <= idx < len(d["lines"]) else ""
    words = line.split()
    rows, cur = [], ""
    for w in words:
        test = f"{cur} {w}".strip()
        if font_body.size(test)[0] > box.w - 40:
            if cur:
                rows.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        rows.append(cur)
    y = box.y + 48
    for row in rows[:3]:
        screen.blit(font_body.render(row, True, (240, 240, 245)), (box.x + 20, y))
        y += 26

    hint = font_hint.render(
        f"E — дальше  ({idx + 1}/{len(d['lines'])})",
        True, (180, 190, 200),
    )
    screen.blit(hint, (box.right - hint.get_width() - 20, box.bottom - 28))


def _draw_hint(screen, state):
    if state.dialog is not None or not state.interact_hint:
        return
    font = pygame.font.SysFont("dejavusans", 18, bold=True)
    text = font.render(state.interact_hint, True, (30, 30, 30))
    bg = text.get_rect(center=(WIDTH // 2, HEIGHT - 48))
    pad = bg.inflate(24, 12)
    pygame.draw.rect(screen, (255, 255, 255), pad, border_radius=6)
    pygame.draw.rect(screen, (0, 188, 212), pad, 2, border_radius=6)
    screen.blit(text, bg)


def render(screen, state, pls, ground_y, blur, walls=None):
    walls = walls or []
    cam_x, cam_y = get_camera(state)
    # запас вокруг экрана — не рисуем далёкие тайлы
    view_l = cam_x - 120
    view_r = cam_x + WIDTH + 120
    view_t = cam_y - 120
    view_b = cam_y + HEIGHT + 120

    screen.fill([255, 255, 255])

    for pl in pls:
        if pl.x + pl.shir < view_l or pl.x > view_r:
            continue
        if pl.y + PLATFORM_H < view_t or pl.y > view_b:
            continue
        img = _resolve_img(
            state, getattr(pl, "texture", None), "platform",
            fit=(pl.shir, PLATFORM_H),
        )
        screen.blit(img, (pl.x - cam_x, pl.y - cam_y))

    for wall in walls:
        if wall.x + wall.w < view_l or wall.x > view_r:
            continue
        if wall.y + wall.h < view_t or wall.y > view_b:
            continue
        img = _resolve_img(
            state, getattr(wall, "texture", None), "wall",
            fit=(wall.w, wall.h),
        )
        screen.blit(img, (wall.x - cam_x, wall.y - cam_y))

    for tp in state.teleports:
        if view_l - 40 <= tp["x"] <= view_r and view_t - 40 <= tp["y"] <= view_b:
            _draw_teleport(screen, tp, cam_x, cam_y, state)

    for cp in getattr(state, "checkpoints", []) or []:
        if view_l - 40 <= cp["x"] <= view_r and view_t - 40 <= cp["y"] <= view_b:
            _draw_checkpoint(screen, cp, cam_x, cam_y, state)

    for npc in state.npcs:
        if view_l - 40 <= npc["x"] <= view_r and view_t - 40 <= npc["y"] <= view_b:
            _draw_npc(screen, npc, cam_x, cam_y, state)

    for pickup in state.level_pickups:
        if pickup["collected"]:
            continue
        if not (view_l - 40 <= pickup["x"] <= view_r and view_t - 40 <= pickup["y"] <= view_b):
            continue
        if pickup["type"] == "ability":
            aid = pickup.get("id", "sprint")
            key = ABILITY_CATALOG.get(aid, {}).get(
                "image", "dash_skill" if aid == "dash" else "sprint_skill",
            )
        elif pickup["type"] == "dash_skill":
            key = "dash_skill"
        elif pickup["type"] == "sprint_skill":
            key = "sprint_skill"
        else:
            key = "extra_life"
        img = _resolve_img(
            state, pickup.get("texture"), key,
            max_size=(PICKUP_SIZE * 2, PICKUP_SIZE * 2),
        )
        screen.blit(img, (pickup["x"] - cam_x, pickup["y"] - cam_y))

    if state.boss_alive or state.boss_dying:
        shake = state.boss_shake if state.boss_alive else 0
        sprite = state.images[_boss_sprite_key(state)]
        screen.blit(sprite, (state.boss_x + shake - cam_x, state.boss_y - cam_y))

    _draw_boss_projectiles(screen, state, cam_x, cam_y)

    for coin in state.coins:
        if not coin["collected"]:
            if view_l - 20 <= coin["x"] <= view_r and view_t - 20 <= coin["y"] <= view_b:
                screen.blit(state.images['coin'], (coin["x"] - 10 - cam_x, coin["y"] - 10 - cam_y))

    drawn_loot = set()
    for item in getattr(state, "boss_loot", []) or []:
        if not item.get("active"):
            continue
        aid = item.get("id", "sprint")
        img_key = ABILITY_CATALOG.get(aid, {}).get(
            "image", "dash_skill" if aid == "dash" else "sprint_skill",
        )
        ov = getattr(state, "texture_overrides", {}).get(f"ability:{aid}")
        img = _resolve_img(state, item.get("texture") or ov, img_key, max_size=(56, 56))
        screen.blit(img, (item["x"] - cam_x, item["y"] - cam_y))
        drawn_loot.add(id(item))

    if state.sprint_pickup and state.sprint_pickup.get("active") and id(state.sprint_pickup) not in drawn_loot:
        p = state.sprint_pickup
        ov = getattr(state, "texture_overrides", {}).get("ability:sprint")
        img = _resolve_img(state, p.get("texture") or ov, "sprint_skill", max_size=(56, 56))
        screen.blit(img, (p["x"] - cam_x, p["y"] - cam_y))

    blur.update(state.playerx, state.playery, state.player, strong=False)
    blur.draw(screen, cam_x, cam_y)
    screen.blit(state.player, (state.playerx - cam_x, state.playery - cam_y))

    giznx = 50
    for i in range(state.health):
        screen.blit(state.images['gizn'], (giznx, 2))
        giznx += 40
    for i in range(HEALTH_MAX - state.health):
        screen.blit(state.images['nogizn'], (giznx, 2))
        giznx += 40

    if state.flagatak == 1 and state.vrematakpl <= ATAKA_KADRY:
        screen.blit(state.images['playerataka1'], (state.playerx + 17 - cam_x, state.playery - cam_y))
        state.vrematakpl += 1
    elif state.flagatak == 2 and state.vrematakpl <= ATAKA_KADRY:
        screen.blit(state.images['playerataka2'], (state.playerx - 78 - cam_x, state.playery - cam_y))
        state.vrematakpl += 1
    elif state.flagatak == 3 and state.vrematakpl <= ATAKA_KADRY:
        screen.blit(state.images['playerataka3'], (state.playerx + 8 - cam_x, state.playery - 90 - cam_y))
        state.vrematakpl += 1
    elif state.flagatak == 4 and state.vrematakpl <= ATAKA_KADRY:
        screen.blit(state.images['playerataka4'], (state.playerx + 8 - cam_x, state.playery + 5 - cam_y))
        state.vrematakpl += 1
    else:
        state.atakapl = False
        state.flagatak = 0
        state.vrematakpl = 0

    state.neuyazvimost += 1

    screen.blit(state.akum, (0, 2))
    _draw_boss_hp_bar(screen, state)
    _draw_hint(screen, state)
    _draw_dialog(screen, state)

    pygame.display.flip()


def draw_loading_screen(screen, level_label, progress=0.0):
    """Короткий экран загрузки между уровнями. progress 0..1."""
    progress = max(0.0, min(1.0, float(progress)))
    screen.fill((18, 22, 30))
    font_title = pygame.font.SysFont("dejavusans", 42, bold=True)
    font_sub = pygame.font.SysFont("dejavusans", 22)
    title = font_title.render("Загрузка...", True, (240, 244, 250))
    screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
    sub = font_sub.render(str(level_label), True, (160, 190, 210))
    screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 5)))

    bar_w, bar_h = 360, 14
    bar = pygame.Rect(0, 0, bar_w, bar_h)
    bar.center = (WIDTH // 2, HEIGHT // 2 + 40)
    pygame.draw.rect(screen, (40, 48, 60), bar, border_radius=6)
    fill = bar.copy()
    fill.width = max(4, int(bar_w * progress))
    pygame.draw.rect(screen, (0, 188, 212), fill, border_radius=6)
    pygame.draw.rect(screen, (120, 200, 220), bar, 1, border_radius=6)
    pygame.display.flip()
