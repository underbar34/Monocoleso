# main.py
import pygame
import sys
from config import WIDTH, HEIGHT, FPS, load_images, GameState
from platforms import create_platforms
from logic import update_akum, get_ground_y, update_player_movement, handle_events, update_plashik
from render import render

def main():
    pygame.init()
    
    # Создание окна
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("My Game")
    
    # Загрузка изображений
    images = load_images()
    
    # Создание состояния игры
    state = GameState(images)
    
    # Создание платформ
    pls = create_platforms()
    
    # Контроль FPS
    clock = pygame.time.Clock()
    
    # Игровой цикл
    game_run = True
    while game_run:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_run = False
        
        # Получение нажатых клавиш
        keys = pygame.key.get_pressed()
        
        # Обновление акума
        update_akum(state)
        
        # Получение высоты земли
        ground_y = get_ground_y(pls, state.playerx, state.playery)
        
        # Подбор плащика
        update_plashik(state)
        
        # Обработка событий клавиатуры
        handle_events(state, keys)
        
        # Обновление движения игрока
        update_player_movement(state, keys, ground_y)
        
        # Отрисовка
        render(screen, state, pls, ground_y)
        
        # Контроль FPS
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()