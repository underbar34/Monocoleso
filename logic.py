# logic.py
from config import (
    GROUND_Y, GRAVITI, SPEED_PLAYER, SPEED_PLAYER_Y, ATAKA_ZADERZHKA,
    RYVOK_VREMYA, RYVOK_SPEED, PLASHIK_ZAMOROZKA,
)
import pygame

def update_akum(state):
    power = state.akumpower
    if power == 0:
        state.akum = state.images['akum0']
    elif power == 1:
        state.akum = state.images['akum1']
    elif power == 2:
        state.akum = state.images['akum2']
    elif power == 3:
        state.akum = state.images['akum3']
    elif power == 4:
        state.akum = state.images['akum4']
    elif power == 5:
        state.akum = state.images['akum5']

def get_ground_y(pls, playerx, playery):
    ground_y = GROUND_Y
    e = True
    n = 0
    while e:
        ground_y = pls[n].pup(playerx, playery, ground_y)
        if ground_y == GROUND_Y:
            n += 1
            if n > len(pls) - 1:
                e = False
        else:
            e = False
    return ground_y

def update_plashik(state):
    if state.plashik_podobran:
        if state.plashik_zamorozka > 0:
            state.plashik_zamorozka -= 1
        return

    px, py = state.playerx, state.playery
    cx, cy = state.plashikx, state.plashiky
    if px < cx + 28 and px + 40 > cx and py < cy + 28 and py + 50 > cy:
        state.plashik_podobran = True
        state.plashik_zamorozka = PLASHIK_ZAMOROZKA
        state.playermovex = 0
        state.playermovey = 0

def update_player_movement(state, keys, ground_y):
    zamorozhen = state.plashik_zamorozka > 0

    # Рывок: очень быстрое движение 0.6 сек
    if state.ryvok:
        state.playerx += state.ryvok_dir * RYVOK_SPEED
        state.ryvok_timer -= 1
        state.playermovey = 0
        if state.ryvok_timer <= 0:
            state.ryvok = False
            state.ryvok_timer = 0
        if state.playery > ground_y:
            state.playery = ground_y
        return

    if zamorozhen:
        state.playermovex = 0
        state.playermovey = 0
        if state.playery > ground_y:
            state.playery = ground_y
        elif state.playery < ground_y:
            state.playery = min(state.playery + SPEED_PLAYER_Y, ground_y)
        return

    # Движение по горизонтали
    state.playermovex = keys[pygame.K_d] - keys[pygame.K_a]
    state.playerx += state.playermovex * SPEED_PLAYER

    # Смена спрайтов при движении
    if state.playermovex == 1:
        state.player = state.images['playeridet1']
        state.lookdir = 1
    elif state.playermovex == -1:
        state.player = state.images['playeridet2']
        state.lookdir = -1
    else:
        if state.player == state.images['playeridet1'] or state.player == state.images['playerstoit1']:
            state.player = state.images['playerstoit1']
            state.lookdir = 1
        elif state.player == state.images['playeridet2'] or state.player == state.images['playerstoit2']:
            state.player = state.images['playerstoit2']
            state.lookdir = -1

    # Прыжок
    if keys[pygame.K_SPACE] == 1 and state.timer == 0 and state.playery == ground_y and state.playermovey < 0.1:
        state.timer += 1
        state.otpuskal = False
        state.playermovey = -2

    if state.timer != 0 and state.timer != -15 and keys[pygame.K_SPACE] == 1 and state.timer <= 15 and state.otpuskal == False and state.playermovey < 0.1:
        state.timer += 1
        state.playermovey += 0.1

    if state.timer > 15 and state.playery <= ground_y or keys[pygame.K_SPACE] != 1 and state.playery <= ground_y:
        state.timer = -15
        state.playermovey = 1
        state.playermovey += 0.1
        state.otpuskal = True

    if state.timer == -15 and state.playery >= ground_y:
        state.playermovey = 0
        state.playery = ground_y
        state.timer = 0
        state.opuskatsa = 0

    if state.playery < ground_y and state.playermovey == 0 and keys[pygame.K_SPACE] == 1:
        state.playermovey = 0.7

    if state.playery > ground_y:
        state.playery = ground_y
        state.playermovey = 0

    state.playery += state.playermovey * SPEED_PLAYER_Y

def handle_events(state, keys):
    zamorozhen = state.plashik_zamorozka > 0

    # Спуск с платформы
    if keys[pygame.K_s] and state.otpuskal and state.playermovey == 0 and not zamorozhen and not state.ryvok:
        state.playery += 40

    if state.atakazaderzhka > 0:
        state.atakazaderzhka -= 1

    if not state.atakapl and state.atakazaderzhka == 0 and not zamorozhen:
        if keys[pygame.K_RIGHT]:
            state.atakapl = True
            state.flagatak = 1
            state.atakazaderzhka = ATAKA_ZADERZHKA
        elif keys[pygame.K_LEFT]:
            state.atakapl = True
            state.flagatak = 2
            state.atakazaderzhka = ATAKA_ZADERZHKA
        elif keys[pygame.K_UP]:
            state.atakapl = True
            state.flagatak = 3
            state.atakazaderzhka = ATAKA_ZADERZHKA
        elif keys[pygame.K_DOWN]:
            state.atakapl = True
            state.flagatak = 4
            state.atakazaderzhka = ATAKA_ZADERZHKA

    # Рывок (Shift) — только после подбора плащика, по нажатию
    shift = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
    if (
        state.plashik_podobran
        and state.plashik_zamorozka == 0
        and not state.ryvok
        and shift
        and not state.shift_derzali
    ):
        direction = keys[pygame.K_d] - keys[pygame.K_a]
        if direction == 0:
            direction = state.lookdir
        state.ryvok = True
        state.ryvok_timer = RYVOK_VREMYA
        state.ryvok_dir = direction
        state.lookdir = direction
        if direction == 1:
            state.player = state.images['playeridet1']
        else:
            state.player = state.images['playeridet2']
    state.shift_derzali = shift

    if keys[pygame.K_e] and state.akumpower == 5:
        state.akumpower = 0
        if state.health <= 5:
            state.health += 1
