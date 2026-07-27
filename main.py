# main.py
import pygame
import sys
from config import WIDTH, HEIGHT, FPS, load_images, GameState
from platforms import create_platforms
from level_loader import load_level, DEFAULT_LEVEL_PATH
from logic import (
    update_akum, get_ground_y, update_player_movement, handle_events,
    update_extra_life, update_boss, update_loot, update_interactions,
)
from render import render
from motion_blur import MotionBlur
from menu import run_menu

def run_game(screen, clock, level_path=DEFAULT_LEVEL_PATH):
    images = load_images()
    level = load_level(level_path)
    state = GameState(images, level)
    pls = create_platforms(level)
    blur = MotionBlur()

    game_run = True
    while game_run:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                game_run = False

        keys = pygame.key.get_pressed()

        update_akum(state)
        ground_y = get_ground_y(
            pls, state.playerx, state.playery,
            getattr(state, "ground_y_default", None),
        )
        update_extra_life(state)
        update_boss(state)
        update_loot(state)
        update_interactions(state)
        handle_events(state, keys, ground_y, events)
        update_player_movement(state, keys, ground_y)
        render(screen, state, pls, ground_y, blur)

        if state.health <= 0:
            return "menu"

        clock.tick(FPS)

    return "quit"

def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Monocoleso")
    clock = pygame.time.Clock()

    while True:
        if run_menu(screen, clock) != "play":
            break
        if run_game(screen, clock) == "quit":
            break

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
