# render.py
import pygame
from config import (
    HEALTH_MAX, ATAKA_KADRY, WIDTH, HEIGHT, BOSS_MAX_HP,
)
from logic import get_camera_x, _boss_in_arena

NPC_W, NPC_H = 36, 50
TELEPORT_R = 18


def _boss_sprite_key(state):
    if state.boss_dying:
        frame = min(state.boss_death_timer // 30, 2)
        return f"holodos_dead{frame + 1}"
    phase = state.boss_phase
    frame = (state.boss_anim // 10) % 3 + 1
    if phase == 1:
        return f"holodos{frame}"
    return f"holodos{min(frame + 1, 4)}"


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
    color = (100, 200, 255) if state.boss_phase == 1 else (255, 100, 100)
    pygame.draw.rect(screen, color, (bar_x, bar_y, int(bar_w * ratio), bar_h))

    font = pygame.font.SysFont("dejavusans", 16, bold=True)
    label = "Холодос"
    if state.boss_phase == 2:
        label += " — Фаза 2"
    text = font.render(f"{label}  {max(0, state.boss_hp)}/{BOSS_MAX_HP}", True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=(WIDTH // 2, bar_y - 12)))


def _draw_npc(screen, npc, cam_x):
    sx, sy = npc["x"] - cam_x, npc["y"]
    body = pygame.Rect(sx, sy, NPC_W, NPC_H)
    pygame.draw.rect(screen, (255, 152, 0), body)
    pygame.draw.rect(screen, (80, 50, 0), body, 2)
    pygame.draw.circle(screen, (255, 220, 180), (sx + NPC_W // 2, sy + 10), 10)
    font = pygame.font.SysFont("dejavusans", 14)
    name = font.render(npc.get("name", "NPC"), True, (40, 40, 40))
    screen.blit(name, name.get_rect(midbottom=(sx + NPC_W // 2, sy - 4)))


def _draw_teleport(screen, tp, cam_x):
    sx = tp["x"] - cam_x + TELEPORT_R
    sy = tp["y"] + TELEPORT_R
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
    # перенос длинных строк
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


def render(screen, state, pls, ground_y, blur):
    cam_x = get_camera_x(state)

    screen.fill([255, 255, 255])

    for pl in pls:
        screen.blit(state.images['platform'], (pl.x - cam_x, pl.y))

    for tp in state.teleports:
        _draw_teleport(screen, tp, cam_x)

    for npc in state.npcs:
        _draw_npc(screen, npc, cam_x)

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
        screen.blit(state.images[key], (pickup["x"] - cam_x, pickup["y"]))

    if state.boss_alive or state.boss_dying:
        shake = state.boss_shake if state.boss_alive else 0
        sprite = state.images[_boss_sprite_key(state)]
        screen.blit(sprite, (state.boss_x + shake - cam_x, state.boss_y))

    for sf in state.snowflakes:
        screen.blit(state.images['snowflake'], (sf["x"] - 8 - cam_x, sf["y"] - 8))

    for coin in state.coins:
        if not coin["collected"]:
            screen.blit(state.images['coin'], (coin["x"] - 10 - cam_x, coin["y"] - 10))

    if state.sprint_pickup and state.sprint_pickup["active"]:
        p = state.sprint_pickup
        screen.blit(state.images['sprint_skill'], (p["x"] - cam_x, p["y"]))

    blur.update(state.playerx, state.playery, state.player, strong=False)
    blur.draw(screen, cam_x)
    screen.blit(state.player, (state.playerx - cam_x, state.playery))

    giznx = 50
    for i in range(state.health):
        screen.blit(state.images['gizn'], (giznx, 2))
        giznx += 40
    for i in range(HEALTH_MAX - state.health):
        screen.blit(state.images['nogizn'], (giznx, 2))
        giznx += 40

    if state.flagatak == 1 and state.vrematakpl <= ATAKA_KADRY:
        screen.blit(state.images['playerataka1'], (state.playerx + 17 - cam_x, state.playery))
        state.vrematakpl += 1
    elif state.flagatak == 2 and state.vrematakpl <= ATAKA_KADRY:
        screen.blit(state.images['playerataka2'], (state.playerx - 78 - cam_x, state.playery))
        state.vrematakpl += 1
    elif state.flagatak == 3 and state.vrematakpl <= ATAKA_KADRY:
        screen.blit(state.images['playerataka3'], (state.playerx + 8 - cam_x, state.playery - 90))
        state.vrematakpl += 1
    elif state.flagatak == 4 and state.vrematakpl <= ATAKA_KADRY:
        screen.blit(state.images['playerataka4'], (state.playerx + 8 - cam_x, state.playery + 5))
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
