# level_editor.py
"""
Визуальный редактор уровней Monocoleso.

Запуск:  python level_editor.py [путь/к/уровню.json]

Управление:
  ЛКМ          — поставить выбранный объект / выделить / перетащить
  ПКМ          — удалить объект/платформу под курсором
  WASD/стрелки — камера
  1–8          — выбор инструмента
  T            — для телепорта: клик задаёт точку назначения
  Enter        — редактировать диалог выделенного NPC
  M            — мувсеты выделенного босса
  I            — текстура ТИПА (все абилки спринта / все платформы / …)
  U            — текстура одного выделенного объекта
  Delete/Backspace — удалить выделение
  Ctrl+S       — сохранить
  Ctrl+O       — перезагрузить файл
  Esc          — снять выделение / выйти из режима текста
  Q / крестик  — выход
"""
import sys
import os
import pygame

from config import WIDTH, HEIGHT, FPS, load_images, WALL_W, WALL_H
from level_loader import (
    DEFAULT_LEVEL_PATH,
    TOOL_CATEGORIES,
    OBJECT_COLORS,
    OBJECT_LABELS,
    BOSS_CATALOG,
    ABILITY_CATALOG,
    default_object,
    load_level,
    save_level,
    ability_label,
    boss_label,
    boss_drop,
    catalog_moveset,
)
from textures import (
    list_asset_textures,
    load_texture,
    texture_label,
    TEXTUREABLE_OBJECT_TYPES,
    TEXTUREABLE_TOOLS,
    override_key_for_object,
    override_key_for_tool,
    get_override,
    stamp_override_on_level,
    ability_override_key,
)
from platforms import PLATFORM_H
from boss_moves import (
    ACTIONS,
    deep_copy_moveset,
    default_holodos_moveset,
    empty_event,
    event_summary,
)

TOOLS = TOOL_CATEGORIES

PANEL_W = 280
SNAP = 5
HIT_PAD = 18
NPC_W, NPC_H = 36, 50
TELEPORT_R = 18
PICKUP_SIZE = 28


def _snap(v):
    return round(v / SNAP) * SNAP


def _make_font(size, bold=False):
    return pygame.font.SysFont("dejavusans", size, bold=bold)


def _is_ability_obj(obj):
    return obj.get("type") in ("ability", "sprint_skill", "dash_skill")


def _is_boss_obj(obj):
    return obj.get("type") == "boss"


def _ability_id(obj):
    if obj.get("type") == "ability":
        return obj.get("id", "sprint")
    if obj.get("type") == "sprint_skill":
        return "sprint"
    if obj.get("type") == "dash_skill":
        return "dash"
    return "sprint"


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
        self.cam_y = 0
        self.tool = "platform"
        self.boss_variant = next(iter(BOSS_CATALOG))
        self.ability_variant = next(iter(ABILITY_CATALOG))
        self.selected = None
        self.dragging = False
        self.drag_ox = 0
        self.drag_oy = 0
        self.setting_teleport_target = False
        self.status = f"Загружено: {path}"
        self.status_timer = 180

        self.font = _make_font(16)
        self.font_sm = _make_font(13)
        self.font_bold = _make_font(18, bold=True)

        self.text_mode = False
        self.text_buffer = ""
        self.text_line_idx = 0

        self.moveset_mode = False
        self.ms_phase_idx = 0
        self.ms_move_idx = 0
        self.ms_event_idx = 0
        self.ms_focus = "phase"  # phase | moves | events | field | action_pick
        self.ms_field_idx = 0
        self.ms_preview = False
        self.ms_edit_buffer = ""
        self.ms_editing_value = False
        self.ms_renaming = False
        self.ms_action_choices = list(ACTIONS.keys())
        self.ms_action_pick_idx = 0

        self.texture_mode = False
        self.texture_list = []
        self.texture_idx = 0
        self.texture_cache = {}
        self.texture_filter = ""
        self.texture_edit_key = None  # ключ texture_overrides (режим type)
        self.texture_edit_label = ""
        self.texture_scope = "type"  # type | instance
        self.texture_instance_ref = None  # dict объекта в режиме instance

        self.tool_rects = []
        self.variant_rects = []

    def world_pos(self, mx, my):
        return mx + self.cam_x, my + self.cam_y

    def screen_x(self, wx):
        return wx - self.cam_x

    def screen_y(self, wy):
        return wy - self.cam_y

    def set_status(self, msg, frames=180):
        self.status = msg
        self.status_timer = frames

    def hit_at(self, wx, wy):
        for i, obj in enumerate(self.level["objects"]):
            if obj["type"] == "npc":
                r = pygame.Rect(obj["x"], obj["y"], NPC_W, NPC_H)
                if r.collidepoint(wx, wy):
                    return ("object", i)
        for i, obj in enumerate(self.level["objects"]):
            if _is_boss_obj(obj):
                bid = obj.get("id", "holodos")
                sprite = BOSS_CATALOG.get(bid, {}).get("sprite", "holodos1")
                img = self.images.get(sprite) or self.images.get("holodos1")
                w = img.get_width() if img else 200
                h = img.get_height() if img else 400
                r = pygame.Rect(obj["x"], obj["y"], w, h)
                if r.inflate(HIT_PAD, HIT_PAD).collidepoint(wx, wy):
                    return ("object", i)
        for i, obj in enumerate(self.level["objects"]):
            if obj["type"] == "teleport":
                cx, cy = obj["x"] + TELEPORT_R, obj["y"] + TELEPORT_R
                if (wx - cx) ** 2 + (wy - cy) ** 2 <= (TELEPORT_R + 8) ** 2:
                    return ("object", i)
        for i, obj in enumerate(self.level["objects"]):
            if _is_ability_obj(obj) or obj["type"] == "extra_life":
                r = pygame.Rect(obj["x"], obj["y"], PICKUP_SIZE, PICKUP_SIZE)
                if r.inflate(HIT_PAD, HIT_PAD).collidepoint(wx, wy):
                    return ("object", i)
        sp = self.level["player_spawn"]
        r = pygame.Rect(sp["x"], sp["y"], 40, 50)
        if r.inflate(HIT_PAD, HIT_PAD).collidepoint(wx, wy):
            return ("spawn", None)
        for i in range(len(self.level.get("walls", [])) - 1, -1, -1):
            w = self.level["walls"][i]
            r = pygame.Rect(w["x"], w["y"], WALL_W, WALL_H)
            if r.inflate(8, 8).collidepoint(wx, wy):
                return ("wall", i)
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

    def place_at(self, wx, wy):
        wx, wy = _snap(wx), _snap(wy)
        if self.tool == "platform":
            item = {"x": int(wx), "y": int(wy)}
            tex = get_override(self.level, "platform")
            if tex:
                item["texture"] = tex
            self.level["platforms"].append(item)
            self.selected = ("platform", len(self.level["platforms"]) - 1)
            self.set_status(f"Платформа @ ({int(wx)}, {int(wy)})")
            return
        if self.tool == "wall":
            item = {"x": int(wx), "y": int(wy)}
            tex = get_override(self.level, "wall")
            if tex:
                item["texture"] = tex
            self.level.setdefault("walls", []).append(item)
            self.selected = ("wall", len(self.level["walls"]) - 1)
            self.set_status(f"Стена @ ({int(wx)}, {int(wy)})")
            return
        if self.tool == "player_spawn":
            self.level["player_spawn"] = {"x": int(wx), "y": int(wy)}
            self.selected = ("spawn", None)
            self.set_status(f"Спавн @ ({int(wx)}, {int(wy)})")
            return
        if self.tool == "boss":
            self.level["objects"] = [
                o for o in self.level["objects"] if o.get("type") != "boss"
            ]
            obj = default_object("boss", int(wx), int(wy), self.boss_variant)
            label = boss_label(self.boss_variant)
        elif self.tool == "ability":
            obj = default_object("ability", int(wx), int(wy), self.ability_variant)
            label = ability_label(self.ability_variant)
        else:
            obj = default_object(self.tool, int(wx), int(wy))
            label = OBJECT_LABELS.get(self.tool, self.tool)
        key = override_key_for_object(obj) if self.tool != "boss" else None
        if key:
            tex = get_override(self.level, key)
            if tex:
                obj["texture"] = tex
        self.level["objects"].append(obj)
        self.selected = ("object", len(self.level["objects"]) - 1)
        self.set_status(f"{label} @ ({int(wx)}, {int(wy)})")

    def delete_selected(self):
        if not self.selected:
            return
        kind, idx = self.selected
        if kind == "platform" and 0 <= idx < len(self.level["platforms"]):
            del self.level["platforms"][idx]
            self.set_status("Платформа удалена")
        elif kind == "wall" and 0 <= idx < len(self.level.get("walls", [])):
            del self.level["walls"][idx]
            self.set_status("Стена удалена")
        elif kind == "object" and 0 <= idx < len(self.level["objects"]):
            obj = self.level["objects"][idx]
            if _is_ability_obj(obj):
                name = ability_label(_ability_id(obj))
            elif _is_boss_obj(obj):
                name = boss_label(obj.get("id", "holodos"))
            else:
                name = OBJECT_LABELS.get(obj["type"], "?")
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
        elif kind == "wall":
            w = self.level["walls"][idx]
            self.drag_ox, self.drag_oy = wx - w["x"], wy - w["y"]
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
        elif kind == "wall":
            self.level["walls"][idx]["x"] = int(nx)
            self.level["walls"][idx]["y"] = int(ny)
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

    def _ensure_boss_moveset(self, obj):
        if not obj.get("moveset"):
            cat = catalog_moveset(obj.get("id", "holodos")) or default_holodos_moveset()
            obj["moveset"] = deep_copy_moveset(cat)
        return obj["moveset"]

    def begin_moveset_edit(self):
        obj = self.get_selected_obj()
        if not obj or not _is_boss_obj(obj):
            self.set_status("Выделите босса, затем M")
            return
        self._ensure_boss_moveset(obj)
        self.moveset_mode = True
        self.ms_phase_idx = 0
        self.ms_move_idx = 0
        self.ms_event_idx = 0
        self.ms_focus = "phase"
        self.ms_preview = False
        self.ms_editing_value = False
        self.set_status("Мувсеты: Tab фокус, ←/→ фаза, ↑/↓ список, A событие, N мув, P превью, Esc выход")

    def _selected_texture_target(self):
        """Точечная правка: (dict_ref, label) или (None, error)."""
        if not self.selected:
            return None, "Выделите объект для точечной текстуры (U)"
        kind, idx = self.selected
        if kind == "platform":
            if 0 <= idx < len(self.level["platforms"]):
                return self.level["platforms"][idx], f"платформа #{idx}"
            return None, "Платформа не найдена"
        if kind == "wall":
            walls = self.level.get("walls", [])
            if 0 <= idx < len(walls):
                return walls[idx], f"стена #{idx}"
            return None, "Стена не найдена"
        if kind == "spawn":
            return None, "Спавну текстуру задать нельзя"
        if kind == "object":
            obj = self.get_selected_obj()
            if not obj:
                return None, "Объект не найден"
            if _is_boss_obj(obj):
                return None, "Текстуру босса менять нельзя"
            if obj.get("type") not in TEXTUREABLE_OBJECT_TYPES:
                return None, f"Тип {obj.get('type')} без кастомной текстуры"
            if _is_ability_obj(obj):
                return obj, f"абилка «{ability_label(_ability_id(obj))}» (этот)"
            return obj, f"{OBJECT_LABELS.get(obj.get('type'), obj.get('type'))} (этот)"
        return None, "Нельзя"

    def _texture_edit_context(self):
        """
        Контекст правки текстуры ТИПА (на все объекты).
        Возвращает (override_key, label) или (None, error_msg).
        Приоритет: выделенный объект → текущий инструмент.
        """
        if self.selected:
            kind, idx = self.selected
            if kind == "platform":
                return "platform", "все платформы"
            if kind == "wall":
                return "wall", "все стены"
            if kind == "spawn":
                return None, "Спавну текстуру задать нельзя"
            if kind == "object":
                obj = self.get_selected_obj()
                if not obj:
                    return None, "Объект не найден"
                if _is_boss_obj(obj):
                    return None, "Текстуру босса менять нельзя"
                if _is_ability_obj(obj):
                    aid = _ability_id(obj)
                    return ability_override_key(aid), f"все абилки «{ability_label(aid)}»"
                key = override_key_for_object(obj)
                if key:
                    return key, f"все: {OBJECT_LABELS.get(obj.get('type'), obj.get('type'))}"
                return None, f"Тип {obj.get('type')} без кастомной текстуры"

        if self.tool == "boss" or self.tool == "player_spawn":
            return None, "Выберите инструмент абилки/платформы/… или объект (не босс)"
        if self.tool not in TEXTUREABLE_TOOLS:
            return None, "Этот инструмент не поддерживает текстуры"
        key = override_key_for_tool(self.tool, self.ability_variant)
        if self.tool == "ability":
            return key, f"все абилки «{ability_label(self.ability_variant)}»"
        return key, f"все: {OBJECT_LABELS.get(self.tool, self.tool)}"

    def begin_texture_edit(self):
        """I — текстура типа (на все)."""
        key, label = self._texture_edit_context()
        if key is None:
            self.set_status(label)
            return
        self.texture_scope = "type"
        self.texture_instance_ref = None
        self.texture_edit_key = key
        self.texture_edit_label = label
        self.texture_list = list_asset_textures()
        self.texture_filter = ""
        current = get_override(self.level, key)
        self.texture_idx = 0
        if current and current in self.texture_list:
            self.texture_idx = self.texture_list.index(current)
        self.texture_mode = True
        self.set_status(f"Тип ({label}): ↑/↓, Enter — на ВСЕ, 0 сброс, Esc")

    def begin_texture_edit_instance(self):
        """U — текстура одного выделенного объекта."""
        target, label = self._selected_texture_target()
        if target is None:
            self.set_status(label)
            return
        self.texture_scope = "instance"
        self.texture_instance_ref = target
        self.texture_edit_key = None
        self.texture_edit_label = label
        self.texture_list = list_asset_textures()
        self.texture_filter = ""
        current = target.get("texture")
        self.texture_idx = 0
        if current and current in self.texture_list:
            self.texture_idx = self.texture_list.index(current)
        self.texture_mode = True
        self.set_status(f"Точка ({label}): ↑/↓, Enter — только этот, 0 сброс, Esc")

    def _filtered_textures(self):
        q = self.texture_filter.lower()
        if not q:
            return self.texture_list
        return [p for p in self.texture_list if q in p.lower()]

    def apply_texture(self, path):
        if getattr(self, "texture_scope", "type") == "instance":
            target = self.texture_instance_ref
            label = self.texture_edit_label or "объект"
            if target is None:
                target, label = self._selected_texture_target()
            if target is None:
                self.set_status(label or "Нельзя")
                self.texture_mode = False
                return
            if path:
                target["texture"] = path
                self.set_status(f"{label}: {texture_label(path)} (только этот)")
            else:
                target.pop("texture", None)
                self.set_status(f"{label}: сброс (только этот)")
            self.texture_mode = False
            self.texture_instance_ref = None
            return

        key = self.texture_edit_key
        label = self.texture_edit_label or key
        if not key:
            key, label = self._texture_edit_context()
        if not key:
            self.set_status(label or "Нельзя")
            self.texture_mode = False
            return
        stamp_override_on_level(self.level, key, path)
        if path:
            self.set_status(f"{label}: {texture_label(path)} (на все)")
        else:
            self.set_status(f"{label}: сброс на дефолт (на все)")
        self.texture_mode = False
        self.texture_edit_key = None

    def draw_texture_overlay(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 210))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(60, 40, WIDTH - 120, HEIGHT - 80)
        pygame.draw.rect(self.screen, (24, 28, 38), panel, border_radius=8)
        border = (120, 200, 160) if getattr(self, "texture_scope", "type") == "type" else (200, 180, 100)
        pygame.draw.rect(self.screen, border, panel, 2, border_radius=8)

        label = self.texture_edit_label or "?"
        if getattr(self, "texture_scope", "type") == "instance":
            title = self.font_bold.render(f"Текстура объекта — {label}", True, (255, 255, 255))
            target = self.texture_instance_ref or {}
            cur = target.get("texture")
            hint = "применится только к этому объекту"
        else:
            title = self.font_bold.render(f"Текстура типа — {label}", True, (255, 255, 255))
            cur = get_override(self.level, self.texture_edit_key) if self.texture_edit_key else None
            hint = "применится ко ВСЕМ объектам типа"
        self.screen.blit(title, (panel.x + 16, panel.y + 12))
        cur_txt = texture_label(cur) if cur else "(дефолт)"
        self.screen.blit(
            self.font_sm.render(f"Сейчас: {cur_txt}  ·  {hint}", True, (180, 200, 190)),
            (panel.x + 16, panel.y + 40),
        )
        if self.texture_filter:
            self.screen.blit(
                self.font_sm.render(f"Фильтр: {self.texture_filter}_", True, (255, 220, 120)),
                (panel.x + 16, panel.y + 60),
            )
        else:
            self.screen.blit(
                self.font_sm.render("Фильтр: начните печатать имя файла", True, (120, 130, 140)),
                (panel.x + 16, panel.y + 60),
            )

        items = self._filtered_textures()
        if items:
            self.texture_idx = max(0, min(self.texture_idx, len(items) - 1))
        else:
            self.texture_idx = 0

        list_y = panel.y + 90
        visible = 18
        start = max(0, self.texture_idx - visible // 2)
        end = min(len(items), start + visible)
        for i in range(start, end):
            path = items[i]
            mark = ">" if i == self.texture_idx else " "
            c = (120, 255, 180) if i == self.texture_idx else (190, 195, 205)
            self.screen.blit(
                self.font_sm.render(f"{mark} {texture_label(path, 70)}", True, c),
                (panel.x + 20, list_y),
            )
            list_y += 18

        preview = pygame.Rect(panel.right - 220, panel.y + 90, 190, 190)
        pygame.draw.rect(self.screen, (15, 18, 26), preview, border_radius=6)
        pygame.draw.rect(self.screen, (80, 100, 90), preview, 1, border_radius=6)
        if items:
            img = load_texture(
                items[self.texture_idx], self.texture_cache, max_size=(170, 170),
            )
            if img is not None:
                px = preview.centerx - img.get_width() // 2
                py = preview.centery - img.get_height() // 2
                self.screen.blit(img, (px, py))

        if getattr(self, "texture_scope", "type") == "instance":
            help_txt = "↑/↓ · Enter только этот · 0 сброс · Esc  |  I=тип, U=точка"
        else:
            help_txt = "↑/↓ · Enter на ВСЕ · 0 сброс · Esc  |  I=тип, U=точка"
        self.screen.blit(
            self.font_sm.render(help_txt, True, (130, 140, 150)),
            (panel.x + 16, panel.bottom - 28),
        )

    def _handle_texture_event(self, event):
        if event.type == pygame.QUIT:
            self.texture_mode = False
            return
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.texture_mode = False
            self.texture_instance_ref = None
            self.set_status("Выбор текстуры отменён")
            return
        if event.key == pygame.K_RETURN:
            items = self._filtered_textures()
            if items:
                self.apply_texture(items[self.texture_idx])
            else:
                self.set_status("Нет файлов в Assets/")
            return
        if event.key == pygame.K_0:
            self.apply_texture(None)
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            items = self._filtered_textures()
            if items:
                self.texture_idx = (self.texture_idx - 1) % len(items)
            return
        if event.key in (pygame.K_DOWN, pygame.K_s):
            items = self._filtered_textures()
            if items:
                self.texture_idx = (self.texture_idx + 1) % len(items)
            return
        if event.key == pygame.K_BACKSPACE:
            self.texture_filter = self.texture_filter[:-1]
            self.texture_idx = 0
            return
        if event.unicode and event.unicode.isprintable():
            if event.unicode == "0" and not self.texture_filter:
                return
            self.texture_filter += event.unicode
            self.texture_idx = 0

    def _ms_phases(self, obj):
        return self._ensure_boss_moveset(obj).setdefault("phases", [])

    def _ms_moves_dict(self, obj):
        return self._ensure_boss_moveset(obj).setdefault("moves", {})

    def _ms_phase(self, obj):
        phases = self._ms_phases(obj)
        if not phases:
            return None
        self.ms_phase_idx = max(0, min(self.ms_phase_idx, len(phases) - 1))
        return phases[self.ms_phase_idx]

    def _ms_move_names(self, obj):
        ph = self._ms_phase(obj)
        if not ph:
            return []
        return list(ph.get("moves") or [])

    def _ms_current_move_name(self, obj):
        names = self._ms_move_names(obj)
        if not names:
            return None
        self.ms_move_idx = max(0, min(self.ms_move_idx, len(names) - 1))
        return names[self.ms_move_idx]

    def _ms_events(self, obj):
        name = self._ms_current_move_name(obj)
        if not name:
            return []
        move = self._ms_moves_dict(obj).setdefault(name, {"duration": 60, "events": []})
        return move.setdefault("events", [])

    def _ms_current_event(self, obj):
        events = self._ms_events(obj)
        if not events:
            return None
        self.ms_event_idx = max(0, min(self.ms_event_idx, len(events) - 1))
        return events[self.ms_event_idx]

    def _ms_event_fields(self, ev):
        action = ev.get("action", "missile")
        meta = ACTIONS.get(action, {})
        fields = [{"key": "frame", "type": "int", "default": 10}]
        for f in meta.get("fields", []):
            fields.append(f)
        return fields

    def _ms_field_value(self, ev, field):
        key = field.get("store_as", field["key"])
        if key in ev:
            return ev[key]
        return field.get("default", field.get("choices", [""])[0] if field.get("choices") else "")

    def _ms_set_field_value(self, ev, field, value):
        key = field.get("store_as", field["key"])
        ftype = field.get("type", "str")
        if ftype == "int":
            try:
                ev[key] = int(value)
            except ValueError:
                return False
        elif ftype == "float":
            try:
                ev[key] = float(value)
            except ValueError:
                return False
        else:
            ev[key] = value
        return True

    def _ms_nudge_field(self, ev, field, delta):
        key = field.get("store_as", field["key"])
        ftype = field.get("type", "str")
        if ftype == "choice":
            choices = field.get("choices") or []
            if not choices:
                return
            cur = str(self._ms_field_value(ev, field))
            try:
                i = choices.index(cur)
            except ValueError:
                i = 0
            ev[key] = choices[(i + delta) % len(choices)]
        elif ftype == "int":
            ev[key] = int(self._ms_field_value(ev, field) or 0) + delta
        elif ftype == "float":
            step = 0.5 if abs(delta) == 1 else float(delta)
            ev[key] = round(float(self._ms_field_value(ev, field) or 0) + step, 2)

    def draw_moveset_overlay(self):
        obj = self.get_selected_obj()
        if not obj or not _is_boss_obj(obj):
            return
        ms = self._ensure_boss_moveset(obj)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 22, 210))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(40, 30, WIDTH - 80, HEIGHT - 60)
        pygame.draw.rect(self.screen, (24, 28, 38), panel, border_radius=8)
        pygame.draw.rect(self.screen, (80, 160, 220), panel, 2, border_radius=8)

        title = self.font_bold.render(
            f"Мувсеты — {boss_label(obj.get('id', 'holodos'))}", True, (255, 255, 255),
        )
        self.screen.blit(title, (panel.x + 16, panel.y + 12))

        phases = self._ms_phases(obj)
        ph = self._ms_phase(obj)
        y = panel.y + 48
        phase_label = (
            f"Фаза {self.ms_phase_idx + 1}/{max(1, len(phases))}  "
            f"hp_below={ph.get('hp_below') if ph else '?'}  "
            f"idle={ph.get('idle') if ph else '?'} кадров"
        )
        col = (255, 220, 120) if self.ms_focus == "phase" else (200, 210, 220)
        self.screen.blit(self.font.render(phase_label, True, col), (panel.x + 16, y))
        y += 28
        self.screen.blit(
            self.font_sm.render("←/→ смена фазы · [/] idle ±5 · ;/' hp_below ±0.05", True, (140, 150, 160)),
            (panel.x + 16, y),
        )
        y += 26

        # Moves list
        names = self._ms_move_names(obj)
        self.screen.blit(
            self.font.render(
                "Мувы фазы:" + ("  [фокус]" if self.ms_focus == "moves" else ""),
                True,
                (255, 220, 120) if self.ms_focus == "moves" else (220, 220, 230),
            ),
            (panel.x + 16, y),
        )
        y += 24
        if not names:
            self.screen.blit(self.font_sm.render("(пусто — N чтобы добавить)", True, (160, 160, 160)), (panel.x + 24, y))
            y += 20
        else:
            for i, name in enumerate(names):
                mark = ">" if i == self.ms_move_idx else " "
                line = f"{mark} {name}"
                if self.ms_renaming and i == self.ms_move_idx:
                    line = f"{mark} {self.ms_edit_buffer}_"
                c = (120, 220, 255) if i == self.ms_move_idx else (180, 185, 195)
                self.screen.blit(self.font_sm.render(line, True, c), (panel.x + 24, y))
                y += 18
                if y > panel.y + 220:
                    break

        y = max(y + 8, panel.y + 230)
        move_name = self._ms_current_move_name(obj)
        move = (ms.get("moves") or {}).get(move_name) if move_name else None
        dur = move.get("duration", 60) if move else 0
        self.screen.blit(
            self.font.render(
                f"События «{move_name or '—'}»  duration={dur}"
                + ("  [фокус]" if self.ms_focus in ("events", "field") else ""),
                True,
                (255, 220, 120) if self.ms_focus in ("events", "field") else (220, 220, 230),
            ),
            (panel.x + 16, y),
        )
        y += 22
        self.screen.blit(
            self.font_sm.render("A добавить · Del удалить · Enter поля · ,/. duration ±5", True, (140, 150, 160)),
            (panel.x + 16, y),
        )
        y += 22

        events = self._ms_events(obj)
        list_top = y
        for i, ev in enumerate(events):
            mark = ">" if i == self.ms_event_idx else " "
            line = f"{mark} {event_summary(ev)}"
            c = (120, 255, 180) if i == self.ms_event_idx else (180, 185, 195)
            self.screen.blit(self.font_sm.render(line[:70], True, c), (panel.x + 24, y))
            y += 17
            if y > panel.bottom - 160:
                break

        # Field editor
        ev = self._ms_current_event(obj)
        fy = panel.bottom - 150
        pygame.draw.line(self.screen, (60, 70, 90), (panel.x + 12, fy - 8), (panel.right - 12, fy - 8))
        if self.ms_focus == "action_pick":
            self.screen.blit(self.font.render("Выбор action (↑/↓, Enter):", True, (255, 200, 100)), (panel.x + 16, fy))
            fy += 22
            for i, act in enumerate(self.ms_action_choices):
                mark = ">" if i == self.ms_action_pick_idx else " "
                label = ACTIONS[act]["label"]
                c = (255, 230, 120) if i == self.ms_action_pick_idx else (180, 185, 195)
                self.screen.blit(self.font_sm.render(f"{mark} {act} — {label}", True, c), (panel.x + 24, fy))
                fy += 16
        elif ev is not None:
            fields = self._ms_event_fields(ev)
            self.ms_field_idx = max(0, min(self.ms_field_idx, max(0, len(fields) - 1)))
            self.screen.blit(
                self.font.render(
                    "Поля события ([/] или ввод+Enter):" if self.ms_focus == "field" else "Поля (Enter — править):",
                    True, (200, 210, 220),
                ),
                (panel.x + 16, fy),
            )
            fy += 22
            for i, field in enumerate(fields):
                key = field.get("store_as", field["key"])
                val = self._ms_field_value(ev, field)
                mark = ">" if self.ms_focus == "field" and i == self.ms_field_idx else " "
                shown = f"{mark} {key} = {val}"
                if self.ms_editing_value and self.ms_focus == "field" and i == self.ms_field_idx:
                    shown = f"{mark} {key} = {self.ms_edit_buffer}_"
                c = (255, 220, 120) if mark == ">" else (170, 175, 185)
                self.screen.blit(self.font_sm.render(shown, True, c), (panel.x + 24, fy))
                fy += 16

        help_y = panel.bottom - 28
        help_txt = "Tab фокус · N новый мув · R rename · P превью · Esc закрыть · Ctrl+S сохранить уровень"
        self.screen.blit(self.font_sm.render(help_txt, True, (130, 140, 150)), (panel.x + 16, help_y))

        if self.ms_preview and ev is not None:
            self._draw_moveset_preview(panel, obj, ev)

    def _draw_moveset_preview(self, panel, obj, ev):
        """Мини-схема: босс + направление выбранного события."""
        box = pygame.Rect(panel.right - 320, panel.y + 50, 290, 180)
        pygame.draw.rect(self.screen, (15, 18, 26), box, border_radius=6)
        pygame.draw.rect(self.screen, (100, 140, 180), box, 1, border_radius=6)
        self.screen.blit(self.font_sm.render("Превью схемы (P)", True, (180, 200, 220)), (box.x + 8, box.y + 6))

        bx, by = box.centerx, box.centery + 10
        pygame.draw.rect(self.screen, (80, 160, 220), (bx - 20, by - 40, 40, 70), 2)
        self.screen.blit(self.font_sm.render("BOSS", True, (80, 160, 220)), (bx - 18, by - 55))

        action = ev.get("action")
        if action == "missile":
            mode = ev.get("mode", "aim")
            pygame.draw.circle(self.screen, (255, 180, 80), (bx + 50, by - 20), 6)
            if mode in ("aim", "spread"):
                pygame.draw.line(self.screen, (255, 180, 80), (bx + 20, by - 10), (bx + 90, by + 20), 2)
            elif mode == "ring":
                pygame.draw.circle(self.screen, (255, 180, 80), (bx, by), 50, 1)
            self.screen.blit(self.font_sm.render(f"missile/{mode}", True, (255, 200, 120)), (box.x + 8, box.bottom - 22))
        elif action == "slash_proj":
            side = ev.get("side", "auto")
            x2 = bx - 80 if side == "left" else bx + 80
            pygame.draw.line(self.screen, (120, 180, 255), (bx, by), (x2, by), 3)
            self.screen.blit(self.font_sm.render(f"slash {side}", True, (120, 180, 255)), (box.x + 8, box.bottom - 22))
        elif action == "ice_rise":
            pygame.draw.rect(self.screen, (150, 220, 255), (bx - 60, by + 30, 120, 12))
            self.screen.blit(self.font_sm.render(f"ice → {ev.get('target', 'player')}", True, (150, 220, 255)), (box.x + 8, box.bottom - 22))
        elif action == "melee":
            side = ev.get("side", "auto")
            rx = bx - 70 if side != "right" else bx + 10
            pygame.draw.rect(self.screen, (255, 100, 100), (rx, by - 30, 60, 50), 2)
            self.screen.blit(self.font_sm.render(f"melee {side}", True, (255, 120, 120)), (box.x + 8, box.bottom - 22))
        elif action == "set_sprite":
            self.screen.blit(self.font_sm.render(f"sprite={ev.get('sprite')}", True, (200, 200, 200)), (box.x + 8, box.bottom - 22))
        else:
            self.screen.blit(self.font_sm.render(str(action), True, (180, 180, 180)), (box.x + 8, box.bottom - 22))

    def _handle_moveset_event(self, event):
        if event.type == pygame.QUIT:
            self.moveset_mode = False
            return
        if event.type != pygame.KEYDOWN:
            return

        obj = self.get_selected_obj()
        if not obj or not _is_boss_obj(obj):
            self.moveset_mode = False
            return

        if event.key == pygame.K_ESCAPE:
            if self.ms_editing_value or self.ms_renaming:
                self.ms_editing_value = False
                self.ms_renaming = False
                return
            if self.ms_focus == "action_pick":
                self.ms_focus = "events"
                return
            if self.ms_preview:
                self.ms_preview = False
                return
            self.moveset_mode = False
            self.set_status("Редактор мувсетов закрыт")
            return

        mods = pygame.key.get_mods()
        if event.key == pygame.K_s and (mods & pygame.KMOD_CTRL):
            self.save()
            return

        if self.ms_renaming:
            if event.key == pygame.K_RETURN:
                old = getattr(self, "_ms_rename_pending", None)
                new = self.ms_edit_buffer.strip().replace(" ", "_")
                moves = self._ms_moves_dict(obj)
                if old and new and new != old and new not in moves and old in moves:
                    moves[new] = moves.pop(old)
                    for ph2 in self._ms_phases(obj):
                        lst = ph2.get("moves") or []
                        for i, m in enumerate(lst):
                            if m == old:
                                lst[i] = new
                    self.set_status(f"Мува {old} → {new}")
                self.ms_renaming = False
                self._ms_rename_pending = None
                return
            if event.key == pygame.K_BACKSPACE:
                self.ms_edit_buffer = self.ms_edit_buffer[:-1]
                return
            if event.unicode and event.unicode.isprintable():
                self.ms_edit_buffer += event.unicode
            return

        if self.ms_editing_value:
            if event.key == pygame.K_RETURN:
                ev = self._ms_current_event(obj)
                fields = self._ms_event_fields(ev) if ev else []
                if ev and fields:
                    field = fields[self.ms_field_idx]
                    if self._ms_set_field_value(ev, field, self.ms_edit_buffer):
                        self.set_status(f"{field.get('store_as', field['key'])} = {self.ms_edit_buffer}")
                    else:
                        self.set_status("Неверное значение")
                self.ms_editing_value = False
                return
            if event.key == pygame.K_BACKSPACE:
                self.ms_edit_buffer = self.ms_edit_buffer[:-1]
                return
            if event.unicode and event.unicode.isprintable():
                self.ms_edit_buffer += event.unicode
            return

        if self.ms_focus == "action_pick":
            if event.key in (pygame.K_UP, pygame.K_w):
                self.ms_action_pick_idx = (self.ms_action_pick_idx - 1) % len(self.ms_action_choices)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.ms_action_pick_idx = (self.ms_action_pick_idx + 1) % len(self.ms_action_choices)
            elif event.key == pygame.K_RETURN:
                act = self.ms_action_choices[self.ms_action_pick_idx]
                events = self._ms_events(obj)
                events.append(empty_event(act))
                events.sort(key=lambda e: int(e.get("frame", 0)))
                self.ms_event_idx = len(events) - 1
                # найти после sort
                for i, e in enumerate(events):
                    if e is events[self.ms_event_idx] or e.get("action") == act:
                        pass
                # re-find last added by matching newest
                self.ms_event_idx = max(0, len(events) - 1)
                self.ms_focus = "events"
                self.set_status(f"Событие {act} добавлено")
            return

        if event.key == pygame.K_TAB:
            order = ["phase", "moves", "events", "field"]
            i = order.index(self.ms_focus) if self.ms_focus in order else 0
            self.ms_focus = order[(i + 1) % len(order)]
            return

        if event.key == pygame.K_p:
            self.ms_preview = not self.ms_preview
            return

        if event.key == pygame.K_LEFT:
            if self.ms_focus == "phase":
                self.ms_phase_idx = max(0, self.ms_phase_idx - 1)
                self.ms_move_idx = 0
                self.ms_event_idx = 0
            elif self.ms_focus == "field":
                ev = self._ms_current_event(obj)
                fields = self._ms_event_fields(ev) if ev else []
                if ev and fields:
                    self._ms_nudge_field(ev, fields[self.ms_field_idx], -1)
            return

        if event.key == pygame.K_RIGHT:
            if self.ms_focus == "phase":
                phases = self._ms_phases(obj)
                self.ms_phase_idx = min(len(phases) - 1, self.ms_phase_idx + 1)
                self.ms_move_idx = 0
                self.ms_event_idx = 0
            elif self.ms_focus == "field":
                ev = self._ms_current_event(obj)
                fields = self._ms_event_fields(ev) if ev else []
                if ev and fields:
                    self._ms_nudge_field(ev, fields[self.ms_field_idx], 1)
            return

        if event.key in (pygame.K_UP, pygame.K_w):
            if self.ms_focus == "moves":
                self.ms_move_idx = max(0, self.ms_move_idx - 1)
                self.ms_event_idx = 0
            elif self.ms_focus in ("events", "field"):
                if self.ms_focus == "field":
                    self.ms_field_idx = max(0, self.ms_field_idx - 1)
                else:
                    self.ms_event_idx = max(0, self.ms_event_idx - 1)
            return

        if event.key in (pygame.K_DOWN, pygame.K_s):
            if self.ms_focus == "moves":
                names = self._ms_move_names(obj)
                self.ms_move_idx = min(max(0, len(names) - 1), self.ms_move_idx + 1)
                self.ms_event_idx = 0
            elif self.ms_focus in ("events", "field"):
                if self.ms_focus == "field":
                    ev = self._ms_current_event(obj)
                    fields = self._ms_event_fields(ev) if ev else []
                    self.ms_field_idx = min(max(0, len(fields) - 1), self.ms_field_idx + 1)
                else:
                    events = self._ms_events(obj)
                    self.ms_event_idx = min(max(0, len(events) - 1), self.ms_event_idx + 1)
            return

        # idle nudge
        if event.key == pygame.K_LEFTBRACKET:
            ph = self._ms_phase(obj)
            if ph is not None and self.ms_focus == "phase":
                ph["idle"] = max(5, int(ph.get("idle", 60)) - 5)
            elif self.ms_focus == "field":
                ev = self._ms_current_event(obj)
                fields = self._ms_event_fields(ev) if ev else []
                if ev and fields:
                    self._ms_nudge_field(ev, fields[self.ms_field_idx], -1)
            return
        if event.key == pygame.K_RIGHTBRACKET:
            ph = self._ms_phase(obj)
            if ph is not None and self.ms_focus == "phase":
                ph["idle"] = int(ph.get("idle", 60)) + 5
            elif self.ms_focus == "field":
                ev = self._ms_current_event(obj)
                fields = self._ms_event_fields(ev) if ev else []
                if ev and fields:
                    self._ms_nudge_field(ev, fields[self.ms_field_idx], 1)
            return

        if event.key == pygame.K_SEMICOLON:
            ph = self._ms_phase(obj)
            if ph is not None:
                ph["hp_below"] = round(max(0.05, float(ph.get("hp_below", 1.0)) - 0.05), 2)
            return
        if event.key == pygame.K_QUOTE:
            ph = self._ms_phase(obj)
            if ph is not None:
                ph["hp_below"] = round(min(1.0, float(ph.get("hp_below", 1.0)) + 0.05), 2)
            return

        if event.key == pygame.K_COMMA:
            name = self._ms_current_move_name(obj)
            if name:
                move = self._ms_moves_dict(obj)[name]
                move["duration"] = max(10, int(move.get("duration", 60)) - 5)
            return
        if event.key == pygame.K_PERIOD:
            name = self._ms_current_move_name(obj)
            if name:
                move = self._ms_moves_dict(obj)[name]
                move["duration"] = int(move.get("duration", 60)) + 5
            return

        if event.key == pygame.K_a:
            self.ms_focus = "action_pick"
            self.ms_action_pick_idx = 0
            return

        if event.key == pygame.K_n:
            # new move
            moves = self._ms_moves_dict(obj)
            base = "new_move"
            name = base
            n = 1
            while name in moves:
                n += 1
                name = f"{base}_{n}"
            moves[name] = {"duration": 60, "events": [empty_event("missile")]}
            ph = self._ms_phase(obj)
            if ph is not None:
                ph.setdefault("moves", []).append(name)
                self.ms_move_idx = len(ph["moves"]) - 1
            self.ms_event_idx = 0
            self.ms_focus = "moves"
            self.set_status(f"Мува {name} добавлена")
            return

        if event.key == pygame.K_r and self.ms_focus == "moves":
            old = self._ms_current_move_name(obj)
            if not old:
                return
            self.ms_renaming = True
            self.ms_edit_buffer = old
            self._ms_rename_pending = old
            self.set_status("Введите новое имя мува и Enter")
            return

        if event.key == pygame.K_RETURN:
            if self.ms_focus == "field":
                ev = self._ms_current_event(obj)
                fields = self._ms_event_fields(ev) if ev else []
                if ev and fields:
                    field = fields[self.ms_field_idx]
                    self.ms_editing_value = True
                    self.ms_edit_buffer = str(self._ms_field_value(ev, field))
                return
            self.ms_focus = "field"
            return

        if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
            if self.ms_focus == "events":
                events = self._ms_events(obj)
                if events:
                    del events[self.ms_event_idx]
                    self.ms_event_idx = max(0, self.ms_event_idx - 1)
                    self.set_status("Событие удалено")
            elif self.ms_focus == "moves":
                name = self._ms_current_move_name(obj)
                ph = self._ms_phase(obj)
                if name and ph and name in ph.get("moves", []):
                    ph["moves"].remove(name)
                    self.ms_move_idx = max(0, self.ms_move_idx - 1)
                    self.set_status(f"{name} убрана из фазы (определение сохранено)")
            return

    def save(self):
        save_level(self.level, self.path)
        self.set_status(f"Сохранено → {self.path}")

    def reload(self):
        self.level = load_level(self.path)
        self.selected = None
        self.set_status(f"Перезагружено ← {self.path}")

    def draw_world(self):
        self.screen.fill((245, 248, 252))
        world_w = self.level.get("world_width", 6200)
        ground_y = self.level.get("ground_y", 726)
        view_w = WIDTH - PANEL_W

        start = int(self.cam_x // 105) * 105
        for x in range(start, int(self.cam_x + view_w) + 105, 105):
            sx = self.screen_x(x)
            pygame.draw.line(self.screen, (230, 235, 240), (sx, 0), (sx, HEIGHT))
        start_y = int(self.cam_y // 85) * 85
        for y in range(start_y, int(self.cam_y + HEIGHT) + 85, 85):
            sy = self.screen_y(y)
            pygame.draw.line(self.screen, (230, 235, 240), (0, sy), (view_w, sy))

        gy = self.screen_y(ground_y)
        pygame.draw.line(self.screen, (180, 180, 180), (0, gy), (view_w, gy), 2)
        tip = self.font_sm.render(
            f"ground_y={ground_y}  cam=({int(self.cam_x)}, {int(self.cam_y)})  world_w={world_w}",
            True, (150, 150, 150),
        )
        self.screen.blit(tip, (8, gy + 6))

        plat_img = self.images["platform"]
        plat_override = get_override(self.level, "platform")
        for i, p in enumerate(self.level["platforms"]):
            sx, sy = self.screen_x(p["x"]), self.screen_y(p["y"])
            img = plat_img
            tex = p.get("texture") or plat_override
            if tex:
                custom = load_texture(tex, self.texture_cache, fit=(105, PLATFORM_H))
                if custom is not None:
                    img = custom
            self.screen.blit(img, (sx, sy))
            if self.selected == ("platform", i):
                pygame.draw.rect(self.screen, (255, 80, 80), (sx - 2, sy - 2, 109, 24), 2)

        wall_img = self.images["wall"]
        wall_override = get_override(self.level, "wall")
        for i, w in enumerate(self.level.get("walls", [])):
            sx, sy = self.screen_x(w["x"]), self.screen_y(w["y"])
            img = wall_img
            tex = w.get("texture") or wall_override
            if tex:
                custom = load_texture(tex, self.texture_cache, fit=(WALL_W, WALL_H))
                if custom is not None:
                    img = custom
            self.screen.blit(img, (sx, sy))
            if self.selected == ("wall", i):
                pygame.draw.rect(
                    self.screen, (255, 80, 80),
                    (sx - 2, sy - 2, WALL_W + 4, WALL_H + 4), 2,
                )

        for i, obj in enumerate(self.level["objects"]):
            self._draw_object(obj, i)

        sp = self.level["player_spawn"]
        sx, sy = self.screen_x(sp["x"]), self.screen_y(sp["y"])
        self.screen.blit(self.images["playerstoit1"], (sx, sy))
        col = (255, 80, 80) if self.selected and self.selected[0] == "spawn" else (244, 67, 54)
        pygame.draw.rect(self.screen, col, (sx - 2, sy - 2, 44, 54), 2)
        label = self.font_sm.render("SPAWN", True, col)
        self.screen.blit(label, (sx, sy - 16))

    def _draw_object(self, obj, idx):
        t = obj["type"]
        sx, sy = self.screen_x(obj["x"]), self.screen_y(obj["y"])
        selected = self.selected == ("object", idx)

        if _is_boss_obj(obj):
            bid = obj.get("id", "holodos")
            meta = BOSS_CATALOG.get(bid, {})
            sprite = meta.get("sprite", "holodos1")
            img = self.images.get(sprite) or self.images["holodos1"]
            color = meta.get("color", OBJECT_COLORS["boss"])
            self.screen.blit(img, (sx, sy))
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
            tag = self.font_sm.render(boss_label(bid), True, color)
            self.screen.blit(tag, (sx, sy - 14))
            return

        if _is_ability_obj(obj):
            aid = _ability_id(obj)
            meta = ABILITY_CATALOG.get(aid, {})
            img_key = meta.get("image", "sprint_skill")
            color = meta.get("color", OBJECT_COLORS["ability"])
            img = self.images[img_key]
            tex = obj.get("texture") or get_override(self.level, ability_override_key(aid))
            if tex:
                custom = load_texture(tex, self.texture_cache, max_size=(48, 48))
                if custom is not None:
                    img = custom
            self.screen.blit(img, (sx, sy))
            if selected:
                pygame.draw.rect(
                    self.screen, (255, 80, 80),
                    (sx - 2, sy - 2, img.get_width() + 4, img.get_height() + 4), 2,
                )
            tag = self.font_sm.render(ability_label(aid), True, color)
            self.screen.blit(tag, (sx, sy - 14))
            return

        color = OBJECT_COLORS.get(t, (100, 100, 100))
        type_tex = get_override(self.level, t) if t in ("extra_life", "npc", "teleport") else None
        if t == "extra_life":
            img = self.images["extra_life"]
            tex = obj.get("texture") or type_tex
            if tex:
                custom = load_texture(tex, self.texture_cache, max_size=(48, 48))
                if custom is not None:
                    img = custom
            self.screen.blit(img, (sx, sy))
            if selected:
                pygame.draw.rect(
                    self.screen, (255, 80, 80),
                    (sx - 2, sy - 2, img.get_width() + 4, img.get_height() + 4), 2,
                )
        elif t == "teleport":
            tex = obj.get("texture") or type_tex
            custom = load_texture(tex, self.texture_cache, max_size=(48, 48)) if tex else None
            if custom is not None:
                self.screen.blit(custom, (sx, sy))
            else:
                pygame.draw.circle(self.screen, color, (sx + TELEPORT_R, sy + TELEPORT_R), TELEPORT_R)
                pygame.draw.circle(self.screen, (255, 255, 255), (sx + TELEPORT_R, sy + TELEPORT_R), TELEPORT_R - 6, 2)
            tx = self.screen_x(obj.get("target_x", obj["x"] + 200))
            ty = self.screen_y(obj.get("target_y", obj["y"]))
            pygame.draw.line(
                self.screen, color,
                (sx + TELEPORT_R, sy + TELEPORT_R), (tx, ty), 2,
            )
            pygame.draw.circle(self.screen, (255, 80, 80), (tx, ty), 8, 2)
            if selected:
                pygame.draw.circle(self.screen, (255, 80, 80), (sx + TELEPORT_R, sy + TELEPORT_R), TELEPORT_R + 4, 2)
        elif t == "npc":
            tex = obj.get("texture") or type_tex
            custom = load_texture(tex, self.texture_cache, max_size=(80, 100)) if tex else None
            if custom is not None:
                self.screen.blit(custom, (sx, sy))
                body = pygame.Rect(sx, sy, custom.get_width(), custom.get_height())
            else:
                body = pygame.Rect(sx, sy, NPC_W, NPC_H)
                pygame.draw.rect(self.screen, color, body)
                pygame.draw.rect(self.screen, (60, 40, 0), body, 2)
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
            rect = pygame.Rect(WIDTH - PANEL_W + 12, y, PANEL_W - 24, 30)
            self.tool_rects.append((rect, tool))
            active = tool == self.tool
            bg = OBJECT_COLORS.get(tool, (90, 90, 90)) if active else (55, 60, 70)
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            if active:
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=4)
            text = self.font.render(f"{i + 1}. {OBJECT_LABELS.get(tool, tool)}", True, (255, 255, 255))
            self.screen.blit(text, (rect.x + 8, rect.y + 5))
            y += 34

        # Подменю вариантов для боссов / абилок
        self.variant_rects = []
        if self.tool in ("boss", "ability"):
            y += 6
            catalog = BOSS_CATALOG if self.tool == "boss" else ABILITY_CATALOG
            current = self.boss_variant if self.tool == "boss" else self.ability_variant
            sub = self.font_bold.render(
                "Выбор босса" if self.tool == "boss" else "Выбор абилки",
                True, (255, 255, 255),
            )
            self.screen.blit(sub, (WIDTH - PANEL_W + 14, y))
            y += 24
            for vid, meta in catalog.items():
                rect = pygame.Rect(WIDTH - PANEL_W + 20, y, PANEL_W - 40, 28)
                self.variant_rects.append((rect, vid))
                active = vid == current
                bg = meta["color"] if active else (50, 55, 65)
                pygame.draw.rect(self.screen, bg, rect, border_radius=4)
                if active:
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2, border_radius=4)
                # иконка
                if self.tool == "ability":
                    img = self.images.get(meta.get("image", "sprint_skill"))
                    if img:
                        self.screen.blit(img, (rect.x + 4, rect.y + 0))
                    label = f"{meta['label']}  [{meta.get('key_hint', '')}]"
                    self.screen.blit(self.font_sm.render(label, True, (255, 255, 255)), (rect.x + 36, rect.y + 6))
                else:
                    self.screen.blit(self.font_sm.render(meta["label"], True, (255, 255, 255)), (rect.x + 10, rect.y + 6))
                y += 32

        y += 8
        help_lines = [
            "ЛКМ — поставить/тащить",
            "ПКМ — удалить",
            "WASD/стрелки — камера",
            "T — цель телепорта",
            "Enter — диалог NPC",
            "M — мувсеты босса",
            "I — текстура типа (на все)",
            "U — текстура одного объекта",
            "Ctrl+S — сохранить",
            "Del — удалить выделение",
        ]
        htitle = self.font_bold.render("Управление", True, (255, 255, 255))
        self.screen.blit(htitle, (WIDTH - PANEL_W + 14, y))
        y += 24
        for line in help_lines:
            self.screen.blit(self.font_sm.render(line, True, (200, 205, 215)), (WIDTH - PANEL_W + 14, y))
            y += 17

        y += 12
        stitle = self.font_bold.render("Свойства", True, (255, 255, 255))
        self.screen.blit(stitle, (WIDTH - PANEL_W + 14, y))
        y += 24
        for line in self._props_lines():
            self.screen.blit(self.font_sm.render(line, True, (220, 220, 230)), (WIDTH - PANEL_W + 14, y))
            y += 16

        if self.text_mode:
            y += 10
            box = pygame.Rect(WIDTH - PANEL_W + 10, min(y, HEIGHT - 90), PANEL_W - 20, 70)
            pygame.draw.rect(self.screen, (20, 24, 30), box, border_radius=4)
            pygame.draw.rect(self.screen, (0, 188, 212), box, 2, border_radius=4)
            prompt = self.font_sm.render(f"Строка {self.text_line_idx + 1}:", True, (0, 188, 212))
            self.screen.blit(prompt, (box.x + 6, box.y + 6))
            shown = self.text_buffer[-28:] + "_"
            self.screen.blit(self.font_sm.render(shown, True, (255, 255, 255)), (box.x + 6, box.y + 28))

        if self.status_timer > 0:
            self.status_timer -= 1
            bar = pygame.Rect(WIDTH - PANEL_W + 8, HEIGHT - 40, PANEL_W - 16, 28)
            pygame.draw.rect(self.screen, (20, 60, 40), bar, border_radius=4)
            msg = self.font_sm.render(self.status[:42], True, (180, 255, 200))
            self.screen.blit(msg, (bar.x + 6, bar.y + 6))

        mx, my = pygame.mouse.get_pos()
        if mx < WIDTH - PANEL_W:
            wx, wy = self.world_pos(mx, my)
            coord = self.font_sm.render(f"({int(wx)}, {int(wy)})", True, (255, 255, 255))
            self.screen.blit(coord, (WIDTH - PANEL_W + 14, HEIGHT - 60))

    def _props_lines(self):
        if not self.selected:
            if self.tool == "boss":
                return [f"Ставится: {boss_label(self.boss_variant)}"]
            if self.tool == "ability":
                ov = get_override(self.level, ability_override_key(self.ability_variant))
                lines = [f"Ставится: {ability_label(self.ability_variant)}"]
                if ov:
                    lines.append(f"tex={texture_label(ov, 28)}")
                lines.append("I — текстура для ВСЕХ таких")
                return lines
            if self.tool in TEXTUREABLE_TOOLS:
                ov = get_override(self.level, override_key_for_tool(self.tool))
                lines = [f"Инструмент: {OBJECT_LABELS.get(self.tool, self.tool)}"]
                if ov:
                    lines.append(f"tex={texture_label(ov, 28)}")
                lines.append("I — текстура для ВСЕХ таких")
                return lines
            return ["(нет выделения)"]
        kind, idx = self.selected
        if kind == "spawn":
            sp = self.level["player_spawn"]
            return [f"Спавн x={sp['x']} y={sp['y']}"]
        if kind == "platform":
            p = self.level["platforms"][idx]
            lines = [f"Платформа #{idx}", f"x={p['x']} y={p['y']}"]
            ov = p.get("texture") or get_override(self.level, "platform")
            if ov:
                lines.append(f"tex={texture_label(ov, 28)}")
            lines.append("I — все платформы · U — эта")
            return lines
        if kind == "wall":
            w = self.level["walls"][idx]
            lines = [f"Стена #{idx}", f"x={w['x']} y={w['y']}"]
            ov = w.get("texture") or get_override(self.level, "wall")
            if ov:
                lines.append(f"tex={texture_label(ov, 28)}")
            lines.append("I — все стены · U — эта")
            return lines
        obj = self.level["objects"][idx]
        if _is_boss_obj(obj):
            bid = obj.get("id", "holodos")
            drop = boss_drop(bid)
            ms = obj.get("moveset") or {}
            n_phases = len(ms.get("phases") or [])
            n_moves = len(ms.get("moves") or {})
            lines = [
                f"Босс: {boss_label(bid)}",
                f"x={obj['x']} y={obj['y']}",
                f"arena_x={obj.get('arena_x')}",
                f"min_x={obj.get('min_x')} max_x={obj.get('max_x')}",
                f"мувсет: {n_phases} фаз, {n_moves} мувов",
                "M — редактор мувсетов",
                "(текстуру босса менять нельзя)",
            ]
            if drop:
                abl = ", ".join(drop["abilities"]) if drop["abilities"] else "—"
                lines.append(f"дроп: {drop['coins']} монет")
                lines.append(f"абилки: {abl}")
            else:
                lines.append("дроп: нет")
            return lines
        if _is_ability_obj(obj):
            aid = _ability_id(obj)
            meta = ABILITY_CATALOG.get(aid, {})
            lines = [
                f"Абилка: {ability_label(aid)}",
                f"клавиша: {meta.get('key_hint', '?')}",
                f"x={obj['x']} y={obj['y']}",
            ]
            ov = obj.get("texture") or get_override(self.level, ability_override_key(aid))
            if ov:
                lines.append(f"tex={texture_label(ov, 28)}")
            lines.append("I — все такие · U — эта")
            return lines
        lines = [
            f"{OBJECT_LABELS.get(obj['type'], obj['type'])}",
            f"x={obj['x']} y={obj['y']}",
        ]
        key = override_key_for_object(obj)
        ov = obj.get("texture") or (get_override(self.level, key) if key else None)
        if ov:
            lines.append(f"tex={texture_label(ov, 28)}")
        if obj["type"] == "teleport":
            lines += [
                f"→ ({obj.get('target_x')}, {obj.get('target_y')})",
                "T + клик = новая цель",
            ]
        elif obj["type"] == "npc":
            lines.append(f"name={obj.get('name', 'NPC')}")
            dialog = obj.get("dialog", [])
            lines.append(f"строк диалога: {len(dialog)}")
            for i, d in enumerate(dialog[:3]):
                lines.append(f"  {i + 1}. {d[:26]}")
            lines.append("Enter — править диалог")
        if obj.get("type") in TEXTUREABLE_OBJECT_TYPES:
            lines.append("I — все такие · U — эта")
        return lines

    def handle_event(self, event):
        if self.moveset_mode:
            self._handle_moveset_event(event)
            return True

        if self.texture_mode:
            self._handle_texture_event(event)
            return True

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
            if event.key == pygame.K_m:
                self.begin_moveset_edit()
                return True
            if event.key == pygame.K_i:
                self.begin_texture_edit()
                return True
            if event.key == pygame.K_u:
                self.begin_texture_edit_instance()
                return True
            if event.key == pygame.K_RETURN:
                self.begin_dialog_edit()
                return True
            if pygame.K_1 <= event.key <= pygame.K_8:
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
                for rect, vid in self.variant_rects:
                    if rect.collidepoint(mx, my):
                        if self.tool == "boss":
                            self.boss_variant = vid
                            self.set_status(f"Босс: {boss_label(vid)}")
                        else:
                            self.ability_variant = vid
                            self.set_status(f"Абилка: {ability_label(vid)}")
                        return True
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
        dx = dy = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= speed
        # S без Ctrl — вниз (Ctrl+S = сохранить)
        if keys[pygame.K_DOWN] or (keys[pygame.K_s] and not (pygame.key.get_mods() & pygame.KMOD_CTRL)):
            dy += speed
        # Почти бесконечное пространство — мягкий предел только от переполнения
        limit = 2_000_000
        self.cam_x = max(-limit, min(self.cam_x + dx, limit))
        self.cam_y = max(-limit, min(self.cam_y + dy, limit))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if self.handle_event(event) is False:
                    running = False

            if not self.text_mode and not self.moveset_mode and not self.texture_mode:
                self.update_camera(pygame.key.get_pressed())

            self.draw_world()
            self.draw_panel()
            if self.setting_teleport_target:
                mx, my = pygame.mouse.get_pos()
                if mx < WIDTH - PANEL_W:
                    pygame.draw.circle(self.screen, (255, 80, 80), (mx, my), 10, 2)
            if self.moveset_mode:
                self.draw_moveset_overlay()
            if self.texture_mode:
                self.draw_texture_overlay()

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
