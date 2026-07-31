# main.py
import pygame
import sys
from config import WIDTH, HEIGHT, FPS, load_images, GameState
from platforms import create_platforms, create_walls
from level_loader import load_level, DEFAULT_LEVEL_PATH, resolve_level_path
from logic import (
    update_akum, get_ground_y, update_player_movement, handle_events,
    update_extra_life, update_boss, update_loot, update_interactions,
    request_respawn_from_checkpoint, apply_checkpoint_progress,
)
from enemies import update_enemies
from render import render, draw_loading_screen
from motion_blur import MotionBlur
from menu import run_menu, run_pause_menu
from savegame import read_save

LOADING_FRAMES = 48  # ~0.8 сек при 60 FPS


def _apply_pending_level(screen, clock, state, blur, info=None):
    """Экран загрузки + смена JSON-уровня. Возвращает (pls, walls) или ('quit', None)."""
    if info is None:
        info = state.pending_level
        state.pending_level = None
    if not info:
        return None, None

    path = resolve_level_path(info.get("path")) or info.get("path")
    label = info.get("label") or path

    for i in range(LOADING_FRAMES):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit", None
        t = (i + 1) / LOADING_FRAMES
        draw_loading_screen(screen, label, progress=t)
        clock.tick(FPS)

    level = load_level(path)
    spawn = (info.get("spawn_x"), info.get("spawn_y"))
    if spawn[0] is None or spawn[1] is None:
        sp = level.get("player_spawn") or {}
        spawn = (sp.get("x", 120), sp.get("y", 640))
    state.apply_level(level, spawn_xy=spawn, level_path=path)
    progress = info.get("progress")
    if progress:
        apply_checkpoint_progress(state, progress)
        state.health = max(1, int(progress.get("health", state.health)))
        state.checkpoint = progress
    if blur is not None:
        blur.clear()
    return create_platforms(level), create_walls(level)


def run_game(screen, clock, level_path=DEFAULT_LEVEL_PATH):
    images = load_images()
    save = read_save()
    if save:
        level_path = resolve_level_path(save.get("level_path")) or level_path
        level = load_level(level_path)
        state = GameState(images, level)
        state.current_level_path = level_path
        state.level_name = level.get("name") or level_path
        apply_checkpoint_progress(state, save)
        state.playerx = float(save["x"])
        state.playery = float(save["y"])
        state.cam_x = None
        state.cam_y = None
        state.checkpoint = save
    else:
        level_path = resolve_level_path(level_path) or level_path
        level = load_level(level_path)
        state = GameState(images, level)
        state.current_level_path = level_path
        state.level_name = level.get("name") or level_path

    pls = create_platforms(level)
    walls = create_walls(level)
    blur = MotionBlur()

    game_run = True
    while game_run:
        events = pygame.event.get()
        open_pause = False
        for event in events:
            if event.type == pygame.QUIT:
                game_run = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                open_pause = True

        if open_pause:
            backdrop = screen.copy()
            result = run_pause_menu(screen, clock, backdrop=backdrop)
            if result == "quit":
                return "quit"
            if result == "menu":
                return "menu"
            continue

        keys = pygame.key.get_pressed()

        update_akum(state)
        ground_y = get_ground_y(
            pls, state.playerx, state.playery,
            getattr(state, "ground_y_default", None),
            walls,
        )
        update_extra_life(state)
        update_boss(state)
        update_enemies(state, pls, walls)
        update_loot(state)
        update_interactions(state)
        handle_events(state, keys, ground_y, events)
        update_player_movement(state, keys, ground_y, walls, pls)
        render(screen, state, pls, ground_y, blur, walls)

        if getattr(state, "pending_level", None):
            result = _apply_pending_level(screen, clock, state, blur)
            if result[0] == "quit":
                return "quit"
            if result[0] is not None:
                pls, walls = result

        if getattr(state, "pending_respawn", None):
            info = state.pending_respawn
            state.pending_respawn = None
            result = _apply_pending_level(screen, clock, state, blur, info=info)
            if result[0] == "quit":
                return "quit"
            if result[0] is not None:
                pls, walls = result

        if state.health <= 0:
            if request_respawn_from_checkpoint(state):
                if getattr(state, "pending_respawn", None):
                    continue
                if blur is not None:
                    blur.clear()
                continue
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
