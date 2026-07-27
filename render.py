# render.py
import pygame
from config import (
    HEALTH_MAX, ATAKA_KADRY, WIDTH, BOSS_MAX_HP,
)
from logic import get_camera_x, _boss_in_arena


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


def render(screen, state, pls, ground_y, blur):
    cam_x = get_camera_x(state)

    screen.fill([255, 255, 255])

    for pl in pls:
        screen.blit(state.images['platform'], (pl.x - cam_x, pl.y))

    if not state.extra_life_podobran:
        screen.blit(state.images['extra_life'], (state.extra_lifex - cam_x, state.extra_lifey))

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

    pygame.display.flip()
