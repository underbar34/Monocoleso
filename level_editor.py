# level_editor.py
"""
Визуальный редактор уровней Monocoleso.

Запуск:  python level_editor.py [путь/к/уровню.json]

Управление:
  ЛКМ          — поставить выбранный объект / выделить / перетащить
  ПКМ          — удалить объект/платформу под курсором
  WASD/стрелки — камера
  1–7          — выбор инструмента
  T            — для телепорта: клик задаёт точку назначения
  Enter        — редактировать диалог выделенного NPC
  Delete/Backspace — удалить выделение
  Ctrl+S       — сохранить
  Ctrl+O       — перезагрузить файл
  Esc          — снять выделение / выйти из режима текста
  Q / крестик  — выход
"""
import sys
import os
import pygame

from config import WIDTH, HEIGHT, FPS, load_images
from level_loader import (
    DEFAULT_LEVEL_PATH,
    OBJECT_TYPES,
    OBJECT_COLORS,
    OBJECT_LABELS,
    default_object,
    load_level,
    save_level,
)

# Инструменты палитры (порядок = горячие клавиши 1–7)
TOOLS = ("platform", "player_spawn") + OBJECT_TYPES

PANEL_W = 260
SNAP = 5
HIT_PAD = 18
NPC_W, NPC_H = 36, 50
TELEPORT_R = 18
PICKUP_SIZE = 28


def _snap(v):
    return round(v / SNAP) * SNAP


def _make_font(size, bold=False):
    return pygame.font.SysFont("dejavusans", size, bold=bold)


class LevelEditor:
    def __init__(self, path):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption(f"Monocoleso Editor — {path}")
        self.clock = pygame.time.Clock()
        self.path = path
        self.level = load_level(path)
        self.images = load_images()

        self.cam_x = 0
        self.tool = "platform"
        self.selected = None  # ("platform", idx) | ("object", idx) | ("spawn", None)
        self.dragging = False
        self.drag_ox = 0
        self.drag_oy = 0
        self.setting_teleport_target = False
        self.status = f"Загружено: {path}"
        self.status_timer = 180

        self.font = _make_font(16)
        self.font_sm = _make_font(13)
        self.font_bold = _make_font(18, bold=True)

        # Режим ввода текста для диалога NPC
        self.text_mode = False
        self.text_buffer = ""
        self.text_line_idx = 0

    # --- координаты ---
    def world_pos(self, mx, my):
        return mx + self.cam_x, my

    def screen_x(self, wx):
        return wx - self.cam_x

    # --- статус ---
    def set_status(self, msg, frames=180):
        self.status = msg
        self.status_timer = frames

    # --- hit-test ---
    def hit_at(self, wx, wy):
        # NPC
        for i, obj in enumerate(self.level["objects"]):
            if obj["type"] == "npc":
                r = pygame.Rect(obj["x"], obj["y"], NPC_W, NPC_H)
                if r.collidepoint(wx, wy):
                    return ("object", i)
        # boss
        for i, obj in enumerate(self.level["objects"]):
            if obj["type"] == "boss":
                img = self.images.get("holodos1")
                w = img.get_width() if img else 200
                h = img.get_height() if img else 400
                r = pygame.Rect(obj["x"], obj["y"], w, h)
                if r.inflate(HIT_PAD, HIT_PAD).collidepoint(wx, wy):
                    return ("object", i)
        # teleports
        for i, obj in enumerate(self.level["objects"]):
            if obj["type"] == "teleport":
                cx, cy = obj["x"] + TELEPORT_R, obj["y"] + TELEPORT_R
                if (wx - cx) ** 2 + (wy - cy) ** 2 <= (TELEPORT_R + 8) ** 2:
                    return ("object", i)
        # pickups
        for i, obj in enumerate(self.level["objects"]):
            if obj["type"] in ("extra_life", "sprint_skill"):
                r = pygame.Rect(obj["x"], obj["y"], PICKUP_SIZE, PICKUP_SIZE)
                if r.inflate(HIT_PAD, HIT_PAD).collidepoint(wx, wy):
                    return ("object", i)
        # spawn
        sp = self.level["player_spawn"]
        r = pygame.Rect(sp["x"], sp["y"], 40, 50)
        if r.inflate(HIT_PAD, HIT_PAD).collidepoint(wx, wy):
            return ("spawn", None)
        # platforms (сверху вниз — последняя в списке приоритетнее)
        for i in range(len(self.level["platforms"]) - 1, -1, -1):
            p = self.level["platforms"][i]
            r = pygame.Rect(p["x"], p["y"], 105, 20)
            if r.inflate(8, 12).collidepoint(wx, wy):
                return ("platform", i)
        return None

    def get_selected_obj(self):
        if self.selected and self.selected[0] == "object":
            idx = self.selected[1]
            if 0 <= idx < len(self.level["objects"]):
                return self.level["objects"][idx]
        return None

    # --- действия ---
    def place_at(self, wx, wy):
        wx, wy = _snap(wx), _snap(wy)
        if self.tool == "platform":
            self.level["platforms"].append({"x": int(wx), "y": int(wy)})
            self.selected = ("platform", len(self.level["platforms"]) - 1)
            self.set_status(f"Платформа @ ({int(wx)}, {int(wy)})")
            return
        if self.tool == "player_spawn":
            self.level["player_spawn"] = {"x": int(wx), "y": int(wy)}
            self.selected = ("spawn", None)
            self.set_status(f"Спавн @ ({int(wx)}, {int(wy)})")
            return
        if self.tool == "boss":
            # один босс на уровень — заменяем
            self.level["objects"] = [
                o for o in self.level["objects"] if o.get("type") != "boss"
            ]
        obj = default_object(self.tool, int(wx), int(wy))
        self.level["objects"].append(obj)
        self.selected = ("object", len(self.level["objects"]) - 1)
        self.set_status(f"{OBJECT_LABELS[self.tool]} @ ({int(wx)}, {int(wy)})")

    def delete_selected(self):
        if not self.selected:
            return
        kind, idx = self.selected
        if kind == "platform" and 0 <= idx < len(self.level["platforms"]):
            del self.level["platforms"][idx]
            self.set_status("Платформа удалена")
        elif kind == "object" and 0 <= idx < len(self.level["objects"]):
            name = OBJECT_LABELS.get(self.level["objects"][idx]["type"], "?")
            del self.level["objects"][idx]
            self.set_status(f"{name} удалён")
        elif kind == "spawn":
            self.set_status("Спавн нельзя удалить — переместите его")
            return
        self.selected = None

    def delete_at(self, wx, wy):
        hit = self.hit_at(wx, wy)
        if hit:
            self.selected = hit
            self.delete_selected()

    def start_drag(self, wx, wy):
        hit = self.hit_at(wx, wy)
        if not hit:
            self.selected = None
            return False
        self.selected = hit
        kind, idx = hit
        if kind == "platform":
            p = self.level["platforms"][idx]
            self.drag_ox, self.drag_oy = wx - p["x"], wy - p["y"]
        elif kind == "object":
            o = self.level["objects"][idx]
            self.drag_ox, self.drag_oy = wx - o["x"], wy - o["y"]
        elif kind == "spawn":
            sp = self.level["player_spawn"]
            self.drag_ox, self.drag_oy = wx - sp["x"], wy - sp["y"]
        self.dragging = True
        return True

    def drag_to(self, wx, wy):
        if not self.dragging or not self.selected:
            return
        kind, idx = self.selected
        nx, ny = _snap(wx - self.drag_ox), _snap(wy - self.drag_oy)
        if kind == "platform":
            self.level["platforms"][idx]["x"] = int(nx)
            self.level["platforms"][idx]["y"] = int(ny)
        elif kind == "object":
            self.level["objects"][idx]["x"] = int(nx)
            self.level["objects"][idx]["y"] = int(ny)
        elif kind == "spawn":
            self.level["player_spawn"]["x"] = int(nx)
            self.level["player_spawn"]["y"] = int(ny)

    def set_teleport_target(self, wx, wy):
        obj = self.get_selected_obj()
        if not obj or obj.get("type") != "teleport":
            self.set_status("Выделите телепорт, затем T и клик")
            self.setting_teleport_target = False
            return
        obj["target_x"] = int(_snap(wx))
        obj["target_y"] = int(_snap(wy))
        self.setting_teleport_target = False
        self.set_status(f"Цель телепорта: ({obj['target_x']}, {obj['target_y']})")

    def begin_dialog_edit(self):
        obj = self.get_selected_obj()
        if not obj or obj.get("type") != "npc":
            self.set_status("Выделите NPC для редактирования диалога")
            return
        dialog = obj.setdefault("dialog", [""])
        if not dialog:
            dialog.append("")
        self.text_line_idx = 0
        self.text_buffer = dialog[0]
        self.text_mode = True
        self.set_status("Редактор диалога: Enter=след.строка, Ctrl+Enter=готово, Esc=отмена")

    def apply_dialog_line(self, advance=True):
        obj = self.get_selected_obj()
        if not obj or obj.get("type") != "npc":
            self.text_mode = False
            return
        dialog = obj.setdefault("dialog", [])
        while len(dialog) <= self.text_line_idx:
            dialog.append("")
        self.text_buffer = self.text_buffer.strip()
        if self.text_buffer:
            dialog[self.text_line_idx] = self.text_buffer
        else:
            # пустая строка — удаляем хвост
            if self.text_line_idx < len(dialog):
                dialog[self.text_line_idx] = ""
        dialog[:] = [line for line in dialog if line.strip()]
        if not dialog:
            dialog.append("...")
        if advance:
            self.text_line_idx = len(dialog)
            dialog.append("")
            self.text_buffer = ""
        else:
            self.text_mode = False
            if dialog and dialog[-1] == "":
                dialog.pop()
            if not dialog:
                dialog.append("...")
            self.set_status(f"Диалог NPC «{obj.get('name', 'NPC')}»: {len(dialog)} строк")

    def save(self):
        save_level(self.level, self.path)
        self.set_status(f"Сохранено → {self.path}")

    def reload(self):
        self.level = load_level(self.path)
        self.selected = None
        self.set_status(f"Перезагружено ← {self.path}")

    # --- отрисовка ---
    def draw_world(self):
        self.screen.fill((245, 248, 252))
        world_w = self.level.get("world_width", 6200)
        ground_y = self.level.get("ground_y", 726)

        # сетка
        start = int(self.cam_x // 105) * 105
        for x in range(start, int(self.cam_x + WIDTH - PANEL_W) + 105, 105):
            sx = self.screen_x(x)
            pygame.draw.line(self.screen, (230, 235, 240), (sx, 0), (sx, HEIGHT))
        for y in range(0, HEIGHT, 85):
            pygame.draw.line(self.screen, (230, 235, 240), (0, y), (WIDTH - PANEL_W, y))

        # земля
        gy = ground_y
        pygame.draw.line(
            self.screen, (180, 180, 180),
            (0, gy), (WIDTH - PANEL_W, gy), 2,
        )
        tip = self.font_sm.render(f"ground_y={ground_y}  world={world_w}", True, (150, 150, 150))
        self.screen.blit(tip, (8, gy + 6))

        # платформы
        plat_img = self.images["platform"]
        for i, p in enumerate(self.level["platforms"]):
            sx, sy = self.screen_x(p["x"]), p["y"]
            self.screen.blit(plat_img, (sx, sy))
            if self.selected == ("platform", i):
                pygame.draw.rect(self.screen, (255, 80, 80), (sx - 2, sy - 2, 109, 24), 2)

        # объекты
        for i, obj in enumerate(self.level["objects"]):
            self._draw_object(obj, i)

        # спавн
        sp = self.level["player_spawn"]
        sx, sy = self.screen_x(sp["x"]), sp["y"]
        self.screen.blit(self.images["playerstoit1"], (sx, sy))
        col = (255, 80, 80) if self.selected and self.selected[0] == "spawn" else (244, 67, 54)
        pygame.draw.rect(self.screen, col, (sx - 2, sy - 2, 44, 54), 2)
        label = self.font_sm.render("SPAWN", True, col)
        self.screen.blit(label, (sx, sy - 16))

    def _draw_object(self, obj, idx):
        t = obj["type"]
        sx, sy = self.screen_x(obj["x"]), obj["y"]
        selected = self.selected == ("object", idx)
        color = OBJECT_COLORS.get(t, (100, 100, 100))

        if t == "boss":
            img = self.images["holodos1"]
            self.screen.blit(img, (sx, sy))
            # зона арены
            arena = obj.get("arena_x", obj["x"] - 1300)
            ax = self.screen_x(arena)
            pygame.draw.line(self.screen, (255, 100, 100), (ax, 0), (ax, HEIGHT), 1)
            mark = self.font_sm.render("арена→", True, (255, 100, 100))
            self.screen.blit(mark, (ax + 4, 40))
            if selected:
                pygame.draw.rect(
                    self.screen, (255, 80, 80),
                    (sx - 2, sy - 2, img.get_width() + 4, img.get_height() + 4), 2,
                )
        elif t == "extra_life":
            self.screen.blit(self.images["extra_life"], (sx, sy))
            if selected:
                pygame.draw.rect(self.screen, (255, 80, 80), (sx - 2, sy - 2, 32, 32), 2)
        elif t == "sprint_skill":
            self.screen.blit(self.images["sprint_skill"], (sx, sy))
            if selected:
                pygame.draw.rect(self.screen, (255, 80, 80), (sx - 2, sy - 2, 32, 32), 2)
        elif t == "teleport":
            pygame.draw.circle(self.screen, color, (sx + TELEPORT_R, sy + TELEPORT_R), TELEPORT_R)
            pygame.draw.circle(self.screen, (255, 255, 255), (sx + TELEPORT_R, sy + TELEPORT_R), TELEPORT_R - 6, 2)
            tx = self.screen_x(obj.get("target_x", obj["x"] + 200))
            ty = obj.get("target_y", obj["y"])
            pygame.draw.line(
                self.screen, color,
                (sx + TELEPORT_R, sy + TELEPORT_R), (tx, ty), 2,
            )
            pygame.draw.circle(self.screen, (255, 80, 80), (tx, ty), 8, 2)
            if selected:
                pygame.draw.circle(self.screen, (255, 80, 80), (sx + TELEPORT_R, sy + TELEPORT_R), TELEPORT_R + 4, 2)
        elif t == "npc":
            body = pygame.Rect(sx, sy, NPC_W, NPC_H)
            pygame.draw.rect(self.screen, color, body)
            pygame.draw.rect(self.screen, (60, 40, 0), body, 2)
            # голова
            pygame.draw.circle(self.screen, (255, 220, 180), (sx + NPC_W // 2, sy + 10), 10)
            name = obj.get("name", "NPC")
            label = self.font_sm.render(name, True, (40, 40, 40))
            self.screen.blit(label, (sx, sy - 16))
            if selected:
                pygame.draw.rect(self.screen, (255, 80, 80), body.inflate(6, 6), 2)

        tag = self.font_sm.render(OBJECT_LABELS.get(t, t), True, color)
        self.screen.blit(tag, (sx, sy - 14 if t != "npc" else sy - 30))

    def draw_panel(self):
        panel = pygame.Rect(WIDTH - PANEL_W, 0, PANEL_W, HEIGHT)
        pygame.draw.rect(self.screen, (35, 40, 48), panel)
        pygame.draw.line(self.screen, (70, 80, 95), (WIDTH - PANEL_W, 0), (WIDTH - PANEL_W, HEIGHT), 2)

        y = 12
        title = self.font_bold.render("Инструменты", True, (255, 255, 255))
        self.screen.blit(title, (WIDTH - PANEL_W + 14, y))
        y += 28

        self.tool_rects = []
        for i, tool in enumerate(TOOLS):
            rect = pygame.Rect(WIDTH - PANEL_W + 12, y, PANEL_W - 24, 32)
            self.tool_rects.append((rect, tool))
            active = tool == self.tool
            bg = OBJECT_COLORS.get(tool, (90, 90, 90)) if active else (55, 60, 70)
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            if active:
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=4)
            text = self.font.render(f"{i + 1}. {OBJECT_LABELS.get(tool, tool)}", True, (255, 255, 255))
            self.screen.blit(text, (rect.x + 8, rect.y + 6))
            y += 38

        y += 10
        help_lines = [
            "ЛКМ — поставить/тащить",
            "ПКМ — удалить",
            "T — цель телепорта",
            "Enter — диалог NPC",
            "Ctrl+S — сохранить",
            "Ctrl+O — перезагрузить",
            "Del — удалить выделение",
        ]
        htitle = self.font_bold.render("Управление", True, (255, 255, 255))
        self.screen.blit(htitle, (WIDTH - PANEL_W + 14, y))
        y += 26
        for line in help_lines:
            self.screen.blit(self.font_sm.render(line, True, (200, 205, 215)), (WIDTH - PANEL_W + 14, y))
            y += 18

        # свойства выделения
        y += 16
        stitle = self.font_bold.render("Свойства", True, (255, 255, 255))
        self.screen.blit(stitle, (WIDTH - PANEL_W + 14, y))
        y += 26
        for line in self._props_lines():
            self.screen.blit(self.font_sm.render(line, True, (220, 220, 230)), (WIDTH - PANEL_W + 14, y))
            y += 17

        if self.text_mode:
            y += 10
            box = pygame.Rect(WIDTH - PANEL_W + 10, y, PANEL_W - 20, 70)
            pygame.draw.rect(self.screen, (20, 24, 30), box, border_radius=4)
            pygame.draw.rect(self.screen, (0, 188, 212), box, 2, border_radius=4)
            prompt = self.font_sm.render(f"Строка {self.text_line_idx + 1}:", True, (0, 188, 212))
            self.screen.blit(prompt, (box.x + 6, box.y + 6))
            shown = self.text_buffer[-28:] + "_"
            self.screen.blit(self.font_sm.render(shown, True, (255, 255, 255)), (box.x + 6, box.y + 28))

        # статус
        if self.status_timer > 0:
            self.status_timer -= 1
            bar = pygame.Rect(WIDTH - PANEL_W + 8, HEIGHT - 40, PANEL_W - 16, 28)
            pygame.draw.rect(self.screen, (20, 60, 40), bar, border_radius=4)
            msg = self.font_sm.render(self.status[:40], True, (180, 255, 200))
            self.screen.blit(msg, (bar.x + 6, bar.y + 6))

        # курсор-мир
        mx, my = pygame.mouse.get_pos()
        if mx < WIDTH - PANEL_W:
            wx, wy = self.world_pos(mx, my)
            coord = self.font_sm.render(f"({int(wx)}, {int(wy)})", True, (255, 255, 255))
            self.screen.blit(coord, (WIDTH - PANEL_W + 14, HEIGHT - 60))

    def _props_lines(self):
        if not self.selected:
            return ["(нет выделения)"]
        kind, idx = self.selected
        if kind == "spawn":
            sp = self.level["player_spawn"]
            return [f"Спавн x={sp['x']} y={sp['y']}"]
        if kind == "platform":
            p = self.level["platforms"][idx]
            return [f"Платформа #{idx}", f"x={p['x']} y={p['y']}"]
        obj = self.level["objects"][idx]
        lines = [
            f"{OBJECT_LABELS.get(obj['type'], obj['type'])}",
            f"x={obj['x']} y={obj['y']}",
        ]
        if obj["type"] == "boss":
            lines += [
                f"arena_x={obj.get('arena_x')}",
                f"min_x={obj.get('min_x')}",
                f"max_x={obj.get('max_x')}",
            ]
        elif obj["type"] == "teleport":
            lines += [
                f"→ ({obj.get('target_x')}, {obj.get('target_y')})",
                "T + клик = новая цель",
            ]
        elif obj["type"] == "npc":
            lines.append(f"name={obj.get('name', 'NPC')}")
            dialog = obj.get("dialog", [])
            lines.append(f"строк диалога: {len(dialog)}")
            for i, d in enumerate(dialog[:4]):
                lines.append(f"  {i + 1}. {d[:28]}")
            if len(dialog) > 4:
                lines.append("  ...")
            lines.append("Enter — править диалог")
        return lines

    # --- события ---
    def handle_event(self, event):
        if self.text_mode:
            self._handle_text_event(event)
            return

        if event.type == pygame.QUIT:
            return False

        if event.type == pygame.KEYDOWN:
            mods = pygame.key.get_mods()
            if event.key == pygame.K_q:
                return False
            if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
                self.save()
                return True
            if event.key == pygame.K_o and (mods & pygame.KMOD_CTRL):
                self.reload()
                return True
            if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                self.delete_selected()
                return True
            if event.key == pygame.K_ESCAPE:
                self.selected = None
                self.setting_teleport_target = False
                return True
            if event.key == pygame.K_t:
                obj = self.get_selected_obj()
                if obj and obj.get("type") == "teleport":
                    self.setting_teleport_target = True
                    self.set_status("Кликните точку назначения телепорта")
                else:
                    self.set_status("Сначала выделите телепорт")
                return True
            if event.key == pygame.K_RETURN:
                self.begin_dialog_edit()
                return True
            # горячие клавиши инструментов
            if pygame.K_1 <= event.key <= pygame.K_7:
                idx = event.key - pygame.K_1
                if idx < len(TOOLS):
                    self.tool = TOOLS[idx]
                    self.set_status(f"Инструмент: {OBJECT_LABELS.get(self.tool, self.tool)}")
                return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if mx >= WIDTH - PANEL_W:
                for rect, tool in self.tool_rects:
                    if rect.collidepoint(mx, my):
                        self.tool = tool
                        self.set_status(f"Инструмент: {OBJECT_LABELS.get(tool, tool)}")
                return True
            wx, wy = self.world_pos(mx, my)
            if event.button == 3:
                self.delete_at(wx, wy)
                return True
            if event.button == 1:
                if self.setting_teleport_target:
                    self.set_teleport_target(wx, wy)
                    return True
                if not self.start_drag(wx, wy):
                    self.place_at(wx, wy)
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False

        if event.type == pygame.MOUSEMOTION and self.dragging:
            mx, my = event.pos
            if mx < WIDTH - PANEL_W:
                wx, wy = self.world_pos(mx, my)
                self.drag_to(wx, wy)

        return True

    def _handle_text_event(self, event):
        if event.type == pygame.QUIT:
            self.text_mode = False
            return
        if event.type != pygame.KEYDOWN:
            return
        mods = pygame.key.get_mods()
        if event.key == pygame.K_ESCAPE:
            self.text_mode = False
            self.set_status("Редактирование диалога отменено")
            return
        if event.key == pygame.K_RETURN:
            if mods & pygame.KMOD_CTRL:
                self.apply_dialog_line(advance=False)
            else:
                self.apply_dialog_line(advance=True)
            return
        if event.key == pygame.K_BACKSPACE:
            self.text_buffer = self.text_buffer[:-1]
            return
        if event.unicode and event.unicode.isprintable():
            self.text_buffer += event.unicode

    def update_camera(self, keys):
        speed = 14
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            speed = 28
        dx = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            pass  # мир горизонтальный — вертикаль фиксирована
        world_w = self.level.get("world_width", 6200)
        self.cam_x = max(0, min(self.cam_x + dx, max(0, world_w - (WIDTH - PANEL_W))))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if self.handle_event(event) is False:
                    running = False

            if not self.text_mode:
                self.update_camera(pygame.key.get_pressed())

            self.draw_world()
            self.draw_panel()
            if self.setting_teleport_target:
                mx, my = pygame.mouse.get_pos()
                if mx < WIDTH - PANEL_W:
                    pygame.draw.circle(self.screen, (255, 80, 80), (mx, my), 10, 2)

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_LEVEL_PATH
    if not os.path.exists(path):
        from level_loader import empty_level, save_level as _save
        _save(empty_level(os.path.splitext(os.path.basename(path))[0]), path)
        print(f"Создан пустой уровень: {path}")
    LevelEditor(path).run()


if __name__ == "__main__":
    main()
