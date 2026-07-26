# logic.py
from config import GROUND_Y, GRAVITI, SPEED_PLAYER, SPEED_PLAYER_Y
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

def update_player_movement(state, keys, ground_y):
    # Движение по горизонтали
    state.playermovex = keys[pygame.K_d] - keys[pygame.K_a]
    state.playerx += state.playermovex * SPEED_PLAYER
    
    # Смена спрайтов при движении
    if state.playermovex == 1:
        state.player = state.images['playeridet1']
        if state.atakapl:
            state.flagatak = 1
    elif state.playermovex == -1:
        state.player = state.images['playeridet2']
        if state.atakapl:
            state.flagatak = 2
    else:
        if state.player == state.images['playeridet1'] or state.player == state.images['playerstoit1']:
            state.player = state.images['playerstoit1']
            if state.atakapl:
                state.flagatak = 1
        elif state.player == state.images['playeridet2'] or state.player == state.images['playerstoit2']:
            state.player = state.images['playerstoit2']
            if state.atakapl:
                state.flagatak = 2
    
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
    # Обработка нажатий клавиш
    if keys[pygame.K_s] and state.otpuskal and state.playermovey == 0:
        state.playery += 40
    
    if keys[pygame.K_w] and not state.atakapl:
        state.atakapl = True
    
    if keys[pygame.K_e] and state.akumpower == 5:
        state.akumpower = 0
        if state.health <= 5:
            state.health += 1