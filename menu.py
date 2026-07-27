# menu.py
import sys
import pygame
from config import WIDTH, HEIGHT, FPS

MENU_ASSETS = "Assets/menuelements"

BTN_LARGE_W = 344
BTN_LARGE_H = 86
BTN_GAP = 20
LOGO_GAP = 45
BTN_SMALL_W = (BTN_LARGE_W - BTN_GAP) // 2
BTN_SMALL_H = BTN_LARGE_H * BTN_SMALL_W // BTN_LARGE_W
BTN_ANIM_SPEED = 12

COLOR_BTN_TEXT = (255, 255, 255)
COLOR_TITLE = (255, 255, 255)
COLOR_SUBTITLE = (220, 220, 220)

_menu_assets = None


def _load_menu_assets():
    global _menu_assets
    if _menu_assets is not None:
        return _menu_assets

    btn1 = pygame.image.load(f"{MENU_ASSETS}/knopka1.png")
    btn2 = pygame.image.load(f"{MENU_ASSETS}/knopka2.png")
    _menu_assets = {
        "background": pygame.image.load(f"{MENU_ASSETS}/menubagground.png"),
        "btn_frames": [btn1, btn2],
    }
    return _menu_assets


def _scale_frames(frames, size):
    return [pygame.transform.scale(frame, size) for frame in frames]


def _make_font(size, bold=False):
    return pygame.font.SysFont("dejavusans", size, bold=bold)


class AnimatedButton:
    def __init__(self, rect, text, font, frames, anim_speed=BTN_ANIM_SPEED):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.frames = frames
        self.anim_speed = anim_speed
        self.anim_timer = 0
        self.frame_index = 0
        self.hovered = False

    @classmethod
    def create(cls, rect, text, font, raw_frames, anim_speed=BTN_ANIM_SPEED):
        size = (pygame.Rect(rect).width, pygame.Rect(rect).height)
        return cls(rect, text, font, _scale_frames(raw_frames, size), anim_speed)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def update(self):
        self.anim_timer += 1
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def draw(self, surface):
        surface.blit(self.frames[self.frame_index], self.rect)
        label = self.font.render(self.text, True, COLOR_BTN_TEXT)
        surface.blit(label, label.get_rect(center=self.rect.center))


def _build_layout(assets, title_font):
    title_surf = title_font.render("Monocoleso", True, COLOR_TITLE)
    btn_font = _make_font(32, bold=True)
    btn_font_small = _make_font(22, bold=True)
    raw_frames = assets["btn_frames"]

    title_h = title_surf.get_height()
    block_h = title_h + LOGO_GAP + BTN_LARGE_H + BTN_GAP + BTN_SMALL_H

    top_y = (HEIGHT - block_h) // 2
    center_x = WIDTH // 2

    title_rect = title_surf.get_rect(midtop=(center_x, top_y))

    play_y = title_rect.bottom + LOGO_GAP
    play_rect = pygame.Rect(0, play_y, BTN_LARGE_W, BTN_LARGE_H)
    play_rect.centerx = center_x

    row_y = play_rect.bottom + BTN_GAP
    authors_rect = pygame.Rect(0, row_y, BTN_SMALL_W, BTN_SMALL_H)
    authors_rect.right = center_x - BTN_GAP // 2
    exit_rect = pygame.Rect(0, row_y, BTN_SMALL_W, BTN_SMALL_H)
    exit_rect.left = center_x + BTN_GAP // 2

    return {
        "background": assets["background"],
        "title": title_surf,
        "title_rect": title_rect,
        "play": AnimatedButton.create(play_rect, "Играть", btn_font, raw_frames),
        "authors": AnimatedButton.create(authors_rect, "Авторы", btn_font_small, raw_frames),
        "exit": AnimatedButton.create(exit_rect, "Выйти", btn_font_small, raw_frames),
    }


def _draw_menu(screen, layout):
    screen.blit(layout["background"], (0, 0))
    screen.blit(layout["title"], layout["title_rect"])

    for key in ("play", "authors", "exit"):
        layout[key].update()
        layout[key].draw(screen)

    pygame.display.flip()


def _run_authors_screen(screen, clock, assets):
    title_font = _make_font(48, bold=True)
    body_font = _make_font(28)
    hint_font = _make_font(22)
    back_font = _make_font(22, bold=True)

    back_rect = pygame.Rect(0, HEIGHT - 100, BTN_SMALL_W, BTN_SMALL_H)
    back_rect.centerx = WIDTH // 2
    back_btn = AnimatedButton.create(back_rect, "Назад", back_font, assets["btn_frames"])

    lines = [
        "Monocoleso",
        "",
        "Разработка игры — команда Monocoleso",
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if back_btn.handle_event(event):
                return

        screen.blit(assets["background"], (0, 0))

        title = title_font.render("Авторы", True, COLOR_TITLE)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 3)))

        y = HEIGHT // 3 + 70
        for line in lines:
            if line:
                surf = body_font.render(line, True, COLOR_SUBTITLE)
                screen.blit(surf, surf.get_rect(center=(WIDTH // 2, y)))
            y += 40

        hint = hint_font.render("Нажмите «Назад», чтобы вернуться в меню", True, COLOR_SUBTITLE)
        screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT - 160)))

        back_btn.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pygame.mouse.get_pos()))
        back_btn.update()
        back_btn.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


def run_menu(screen, clock):
    """Показывает главное меню. Возвращает 'play' при нажатии «Играть»."""
    assets = _load_menu_assets()
    title_font = _make_font(56, bold=True)
    layout = _build_layout(assets, title_font)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if layout["play"].handle_event(event):
                return "play"
            if layout["authors"].handle_event(event):
                _run_authors_screen(screen, clock, assets)
                layout = _build_layout(assets, title_font)
            if layout["exit"].handle_event(event):
                pygame.quit()
                sys.exit()

        layout["play"].handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pygame.mouse.get_pos()))
        layout["authors"].handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pygame.mouse.get_pos()))
        layout["exit"].handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=pygame.mouse.get_pos()))

        _draw_menu(screen, layout)
        clock.tick(FPS)


if __name__ == "__main__":
    from main import main
    main()
