# inventory.py
"""Оверлей инвентаря (Assets/bg/inventory.png), кнопка I."""
import pygame
from config import WIDTH, HEIGHT
from level_loader import ABILITY_CATALOG, ability_label

# Координаты в пространстве исходного PNG 1000×500
INV_NATIVE_W = 1000
INV_NATIVE_H = 500

# Молния уже на артe; число HP рядом с короткой жёлтой чертой
HP_NUM_POS = (178, 78)

# Ромб персонажа (центр)
CHAR_CENTER = (113, 357)
CHAR_MAX = (86, 100)

# Центры зелёных слотов 4×4
ITEM_COLS = (345, 405, 479, 564)
ITEM_ROWS = (126, 217, 317, 395)
ITEM_ICON = 52

# Зона карты
MAP_CENTER = (800, 290)

# Красная рамка предметов — подчищаем звёзды под иконками лёгким затемнением слота
SLOT_COVER = 44


def add_inventory_item(state, item_id, label, icon_key, stackable=False):
    inv = getattr(state, "inventory", None)
    if inv is None:
        state.inventory = []
        inv = state.inventory
    for it in inv:
        if it["id"] == item_id:
            if stackable:
                it["count"] = int(it.get("count", 1)) + 1
            return
    inv.append({
        "id": item_id,
        "label": label,
        "icon": icon_key,
        "count": 1,
    })


def sync_inventory(state):
    """Подтянуть абилки из флагов (после загрузки сейва)."""
    if getattr(state, "inventory", None) is None:
        state.inventory = []
    if getattr(state, "sprint_unlocked", False):
        add_inventory_item(state, "ability:sprint", ability_label("sprint"), "sprint_skill")
    if getattr(state, "dash_unlocked", False):
        add_inventory_item(state, "ability:dash", ability_label("dash"), "dash_skill")


def _layout(overlay):
    """scale, offset для центрирования оверлея на экране."""
    ow, oh = overlay.get_size()
    scale = min((WIDTH - 60) / ow, (HEIGHT - 60) / oh, 1.35)
    sw, sh = int(ow * scale), int(oh * scale)
    ox = (WIDTH - sw) // 2
    oy = (HEIGHT - sh) // 2
    return scale, ox, oy, sw, sh


def _to_screen(nx, ny, scale, ox, oy):
    return int(ox + nx * scale), int(oy + ny * scale)


def _blit_centered(screen, img, cx, cy):
    screen.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))


def collect_inventory_entries(state):
    """Список предметов для сетки (абилки + подобранное)."""
    sync_inventory(state)
    return list(getattr(state, "inventory", []) or [])


def draw_inventory_overlay(screen, state):
    overlay = state.images.get("inventory")
    if overlay is None:
        return
    scale, ox, oy, sw, sh = _layout(overlay)
    scaled = pygame.transform.smoothscale(overlay, (sw, sh))

    dim = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    screen.blit(dim, (0, 0))
    screen.blit(scaled, (ox, oy))

    font_hp = pygame.font.SysFont("dejavusans", max(22, int(36 * scale)), bold=True)
    font_map = pygame.font.SysFont("dejavusans", max(16, int(26 * scale)), bold=True)
    font_cnt = pygame.font.SysFont("dejavusans", max(12, int(16 * scale)), bold=True)

    # HP: одна «молния» уже на артe — рисуем число рядом
    hp = int(getattr(state, "health", 0))
    hp_surf = font_hp.render(str(hp), True, (255, 220, 60))
    hx, hy = _to_screen(*HP_NUM_POS, scale, ox, oy)
    screen.blit(hp_surf, hp_surf.get_rect(midleft=(hx, hy + int(12 * scale))))

    # Персонаж в ромбе
    char = state.images.get("playerstoit1") or state.images.get("player")
    if char is not None:
        mw, mh = int(CHAR_MAX[0] * scale), int(CHAR_MAX[1] * scale)
        cw, ch = char.get_size()
        k = min(mw / max(cw, 1), mh / max(ch, 1))
        char_s = pygame.transform.smoothscale(char, (max(1, int(cw * k)), max(1, int(ch * k))))
        cx, cy = _to_screen(*CHAR_CENTER, scale, ox, oy)
        _blit_centered(screen, char_s, cx, cy)

    # Предметы в слотах
    entries = collect_inventory_entries(state)
    icon_sz = max(20, int(ITEM_ICON * scale))
    cover = max(18, int(SLOT_COVER * scale))
    idx = 0
    for row_y in ITEM_ROWS:
        for col_x in ITEM_COLS:
            sx, sy = _to_screen(col_x, row_y, scale, ox, oy)
            if idx < len(entries):
                # перекрываем зелёную звезду под иконкой
                pad = pygame.Surface((cover, cover), pygame.SRCALPHA)
                pad.fill((10, 10, 10, 210))
                screen.blit(pad, pad.get_rect(center=(sx, sy)))
                it = entries[idx]
                img = state.images.get(it.get("icon"))
                if img is not None:
                    iw, ih = img.get_size()
                    k = min(icon_sz / max(iw, 1), icon_sz / max(ih, 1))
                    icon = pygame.transform.smoothscale(
                        img, (max(1, int(iw * k)), max(1, int(ih * k))),
                    )
                    _blit_centered(screen, icon, sx, sy)
                cnt = int(it.get("count", 1))
                if cnt > 1:
                    cs = font_cnt.render(str(cnt), True, (255, 255, 255))
                    screen.blit(cs, (sx + icon_sz // 3, sy + icon_sz // 4))
            idx += 1

    # Карта
    map_txt = font_map.render("карта не изученна", True, (180, 140, 90))
    mx, my = _to_screen(*MAP_CENTER, scale, ox, oy)
    screen.blit(map_txt, map_txt.get_rect(center=(mx, my)))
