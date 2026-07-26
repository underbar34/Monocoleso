# render.py
import pygame
from config import HEALTH_MAX, ATAKA_KADRY

def render(screen, state, pls, ground_y):
    screen.fill([255, 255, 255])
    
    # Отрисовка платформ
    for pl in pls:
        screen.blit(state.images['platform'], (pl.x, pl.y))

    # Отрисовка плащика
    if not state.plashik_podobran:
        screen.blit(state.images['plashik'], (state.plashikx, state.plashiky))

    # Отрисовка игрока
    screen.blit(state.player, (state.playerx, state.playery))
    
    # Отрисовка здоровья
    giznx = 50
    for i in range(state.health):
        screen.blit(state.images['gizn'], (giznx, 2))
        giznx += 40
    for i in range(HEALTH_MAX - state.health):
        screen.blit(state.images['nogizn'], (giznx, 2))
        giznx += 40
    
    # Отрисовка атаки
    if state.flagatak == 1 and state.vrematakpl <= ATAKA_KADRY:
        atakax = state.playerx + 30
        screen.blit(state.images['playerataka1'], (atakax, state.playery - 10))
        state.vrematakpl += 1
    elif state.flagatak == 2 and state.vrematakpl <= ATAKA_KADRY:
        atakax = state.playerx - 30
        screen.blit(state.images['playerataka2'], (atakax, state.playery - 10))
        state.vrematakpl += 1
    elif state.flagatak == 3 and state.vrematakpl <= ATAKA_KADRY:
        screen.blit(state.images['playerataka3'], (state.playerx - 10, state.playery - 50))
        state.vrematakpl += 1
    elif state.flagatak == 4 and state.vrematakpl <= ATAKA_KADRY:
        screen.blit(state.images['playerataka4'], (state.playerx - 10, state.playery + 30))
        state.vrematakpl += 1
    else:
        state.atakapl = False
        state.flagatak = 0
        state.vrematakpl = 0
    
    # Неуязвимость
    state.neuyazvimost += 1
    
    # Отрисовка акума
    screen.blit(state.akum, (0, 2))
    
    pygame.display.flip()
