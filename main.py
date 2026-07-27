# main.py
import pygame
import sys
from config import WIDTH, HEIGHT, FPS, load_images, GameState
from platforms import create_platforms
from logic import (
    update_akum, get_ground_y, update_player_movement, handle_events,
    update_extra_life, update_boss, update_loot,
)
from render import render
from motion_blur import MotionBlur
from menu import run_menu

def run_game(screen, clock):
    # Загрузка изображений
    images = load_images()
    
    # Создание состояния игры
    state = GameState(images)
    
    # Создание платформ
    pls = create_platforms()

    # Motion blur
    blur = MotionBlur()
    
    # Игровой цикл
    game_run = True
    while game_run:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                game_run = False
        
        keys = pygame.key.get_pressed()
        
        # Обновление акума
        update_akum(state)
        
        # Получение высоты земли
        ground_y = get_ground_y(pls, state.playerx, state.playery)
        
        # Подбор плащика и доп. жизни
        update_extra_life(state)
        update_boss(state)
        update_loot(state)
        
        # Обработка событий клавиатуры
        handle_events(state, keys, ground_y, events)
        
        # Обновление движения игрока
        update_player_movement(state, keys, ground_y)
        
        # Отрисовка
        render(screen, state, pls, ground_y, blur)
        
        # Контроль FPS
        clock.tick(FPS)

def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Monocoleso")
    clock = pygame.time.Clock()

    if run_menu(screen, clock) == "play":
        run_game(screen, clock)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()