# menu.py
import sys
import pygame
from config import WIDTH, HEIGHT, FPS

BTN_LARGE_W = 420
BTN_LARGE_H = 72
BTN_GAP = 20
LOGO_GAP = 45
BTN_SMALL_W = (BTN_LARGE_W - BTN_GAP) // 2
BTN_SMALL_H = BTN_LARGE_H

COLOR_BG = (255, 255, 255)
COLOR_BTN = (45, 55, 85)
COLOR_BTN_HOVER = (65, 80, 120)
COLOR_BTN_TEXT = (255, 255, 255)
COLOR_TITLE = (30, 35, 55)
COLOR_SUBTITLE = (80, 90, 110)


class Button:
    def __init__(self, rect, text, font):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

    def draw(self, surface):
        color = COLOR_BTN_HOVER if self.hovered else COLOR_BTN
        pygame.draw.rect(surface, color, self.rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_TITLE, self.rect, width=2, border_radius=8)
        label = self.font.render(self.text, True, COLOR_BTN_TEXT)
        surface.blit(label, label.get_rect(center=self.rect.center))


def _load_logo():
    logo = pygame.image.load("Assets/akum/akum5.png")
    scale = 2
    size = (logo.get_width() * scale, logo.get_height() * scale)
    return pygame.transform.scale(logo, size)


def _make_font(size, bold=False):
    return pygame.font.SysFont("dejavusans", size, bold=bold)


def _build_layout(title_font):
    logo = _load_logo()
    title_surf = title_font.render("Monocoleso", True, COLOR_TITLE)
    btn_font = _make_font(32, bold=True)
    btn_font_small = _make_font(26, bold=True)

    logo_h = logo.get_height()
    title_h = title_surf.get_height()
    block_h = logo_h + 12 + title_h + LOGO_GAP + BTN_LARGE_H + BTN_GAP + BTN_SMALL_H

    top_y = (HEIGHT - block_h) // 2
    center_x = WIDTH // 2

    logo_rect = logo.get_rect(midtop=(center_x, top_y))
    title_rect = title_surf.get_rect(midtop=(center_x, logo_rect.bottom + 12))

    play_y = title_rect.bottom + LOGO_GAP
    play_rect = pygame.Rect(0, play_y, BTN_LARGE_W, BTN_LARGE_H)
    play_rect.centerx = center_x

    row_y = play_rect.bottom + BTN_GAP
    authors_rect = pygame.Rect(0, row_y, BTN_SMALL_W, BTN_SMALL_H)
    authors_rect.right = center_x - BTN_GAP // 2
    exit_rect = pygame.Rect(0, row_y, BTN_SMALL_W, BTN_SMALL_H)
    exit_rect.left = center_x + BTN_GAP // 2

    return {
        "logo": logo,
        "logo_rect": logo_rect,
        "title": title_surf,
        "title_rect": title_rect,
        "play": Button(play_rect, "Играть", btn_font),
        "authors": Button(authors_rect, "Авторы", btn_font_small),
        "exit": Button(exit_rect, "Выйти", btn_font_small),
    }


def _draw_menu(screen, layout):
    screen.fill(COLOR_BG)
    screen.blit(layout["logo"], layout["logo_rect"])
    screen.blit(layout["title"], layout["title_rect"])
    layout["play"].draw(screen)
    layout["authors"].draw(screen)
    layout["exit"].draw(screen)
    pygame.display.flip()


def _run_authors_screen(screen, clock):
    title_font = _make_font(48, bold=True)
    body_font = _make_font(28)
    hint_font = _make_font(22)
    back_font = _make_font(26, bold=True)

    back_rect = pygame.Rect(0, HEIGHT - 100, 200, BTN_SMALL_H)
    back_rect.centerx = WIDTH // 2
    back_btn = Button(back_rect, "Назад", back_font)

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

        screen.fill(COLOR_BG)
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
        back_btn.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)


def run_menu(screen, clock):
    """Показывает главное меню. Возвращает 'play' при нажатии «Играть»."""
    title_font = _make_font(56, bold=True)
    layout = _build_layout(title_font)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if layout["play"].handle_event(event):
                return "play"
            if layout["authors"].handle_event(event):
                _run_authors_screen(screen, clock)
                layout = _build_layout(title_font)
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
