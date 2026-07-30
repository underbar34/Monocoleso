# render.py
import pygame
from config import (
    HEALTH_MAX, ATAKA_KADRY, WIDTH, HEIGHT, BOSS_MAX_HP,
)
from logic import get_camera, _boss_in_arena
from level_loader import ABILITY_CATALOG

NPC_W, NPC_H = 36, 50
TELEPORT_R = 18


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
    for p in getattr(state, "boss_projectiles", []) or []:
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


def _draw_npc(screen, npc, cam_x, cam_y):
    sx, sy = npc["x"] - cam_x, npc["y"] - cam_y
    body = pygame.Rect(sx, sy, NPC_W, NPC_H)
    pygame.draw.rect(screen, (255, 152, 0), body)
    pygame.draw.rect(screen, (80, 50, 0), body, 2)
    pygame.draw.circle(screen, (255, 220, 180), (sx + NPC_W // 2, sy + 10), 10)
    font = pygame.font.SysFont("dejavusans", 14)
    name = font.render(npc.get("name", "NPC"), True, (40, 40, 40))
    screen.blit(name, name.get_rect(midbottom=(sx + NPC_W // 2, sy - 4)))


def _draw_teleport(screen, tp, cam_x, cam_y):
    sx = tp["x"] - cam_x + TELEPORT_R
    sy = tp["y"] - cam_y + TELEPORT_R
    pygame.draw.circle(screen, (0, 188, 212), (sx, sy), TELEPORT_R)
    pygame.draw.circle(screen, (255, 255, 255), (sx, sy), TELEPORT_R - 6, 2)


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

    screen.fill([255, 255, 255])

    for pl in pls:
        screen.blit(state.images['platform'], (pl.x - cam_x, pl.y - cam_y))

    for wall in walls:
        screen.blit(state.images['wall'], (wall.x - cam_x, wall.y - cam_y))

    for tp in state.teleports:
        _draw_teleport(screen, tp, cam_x, cam_y)

    for npc in state.npcs:
        _draw_npc(screen, npc, cam_x, cam_y)

    for pickup in state.level_pickups:
        if pickup["collected"]:
            continue
        if pickup["type"] == "ability":
            aid = pickup.get("id", "sprint")
            key = "dash_skill" if aid == "dash" else "sprint_skill"
        elif pickup["type"] == "dash_skill":
            key = "dash_skill"
        elif pickup["type"] == "sprint_skill":
            key = "sprint_skill"
        else:
            key = "extra_life"
        screen.blit(state.images[key], (pickup["x"] - cam_x, pickup["y"] - cam_y))

    if state.boss_alive or state.boss_dying:
        shake = state.boss_shake if state.boss_alive else 0
        sprite = state.images[_boss_sprite_key(state)]
        screen.blit(sprite, (state.boss_x + shake - cam_x, state.boss_y - cam_y))

    _draw_boss_projectiles(screen, state, cam_x, cam_y)

    for coin in state.coins:
        if not coin["collected"]:
            screen.blit(state.images['coin'], (coin["x"] - 10 - cam_x, coin["y"] - 10 - cam_y))

    drawn_loot = set()
    for item in getattr(state, "boss_loot", []) or []:
        if not item.get("active"):
            continue
        aid = item.get("id", "sprint")
        img_key = ABILITY_CATALOG.get(aid, {}).get(
            "image", "dash_skill" if aid == "dash" else "sprint_skill",
        )
        screen.blit(state.images[img_key], (item["x"] - cam_x, item["y"] - cam_y))
        drawn_loot.add(id(item))

    if state.sprint_pickup and state.sprint_pickup.get("active") and id(state.sprint_pickup) not in drawn_loot:
        p = state.sprint_pickup
        screen.blit(state.images['sprint_skill'], (p["x"] - cam_x, p["y"] - cam_y))

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
