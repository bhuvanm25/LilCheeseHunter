import json, sys, os, glob, math
import pygame as pg

# Folders for raw and cleaned maps
RAW_DIR = "raw"
CLEAN_DIR = "cleaned"
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CLEAN_DIR, exist_ok=True)


def trim_rows_cols(grid):
    # Trim away all-zero rows/cols around the map
    if not grid:
        return []
    g = [row for row in grid if any(v != 0 for v in row)]
    if not g:
        return []
    cols_to_keep = [i for i in range(len(g[0])) if any(row[i] != 0 for row in g)]
    if not cols_to_keep:
        return []
    return [[row[i] for row in cols_to_keep] for row in g]


# Map size in tiles
MAP_W, MAP_H   = 50, 50
BASE_TILE      = 16        # Base tile size before zoom
BG             = (22, 22, 26)

# Sidebar layout
SIDEBAR_W      = 280
WIN_W          = MAP_W * BASE_TILE + SIDEBAR_W
WIN_H          = MAP_H * BASE_TILE

# Tile types and colors
PALETTE = {
    0: ("empty", (35, 35, 40)),
    1: ("wall",  (25, 60, 150)),
    2: ("floor", (180, 180, 190)),
    3: ("trap",  (150, 40, 40)),
    4: ("home",  (40, 170, 80)),
}
DEFAULT_TILE   = 0
PALETTE_ORDER  = [1, 2, 3, 4]

# Camera / zoom settings
MIN_ZOOM, MAX_ZOOM = 0.5, 3.0
PAN_SPEED = 600


def clamp(a, lo, hi):
    return max(lo, min(hi, a))


def new_map(w, h, fill=DEFAULT_TILE):
    # Create a w x h grid filled with 'fill'
    return [[fill for _ in range(w)] for _ in range(h)]


def next_save_name(prefix="map", ext=".json", width=3, folder=RAW_DIR):
    # Generate "map001.json", "map002.json", ... that doesn't exist yet
    n = 1
    while True:
        name = f"{prefix}{n:0{width}d}{ext}"
        path = os.path.join(folder, name)
        if not os.path.exists(path):
            return path
        n += 1


def safe_custom_name(name, ext=".json", folder=RAW_DIR):
    # Turn user-typed name into a unique filename (no overwrite)
    base = name.strip()
    if not base:
        return next_save_name(folder=folder)
    if not base.lower().endswith(ext):
        fname = base + ext
    else:
        fname = base
    path = os.path.join(folder, fname)
    if not os.path.exists(path):
        return path
    root, e = os.path.splitext(path)
    i = 1
    while True:
        alt = f"{root}-{i:03d}{e}"
        if not os.path.exists(alt):
            return alt
        i += 1


def cleaned_path_for(raw_path):
    # Mirror raw path into cleaned/ with " (cleaned)" suffix
    _raw_dir, raw_file = os.path.split(raw_path)
    base, ext = os.path.splitext(raw_file)
    target = os.path.join(CLEAN_DIR, f"{base} (cleaned){ext}")
    if not os.path.exists(target):
        return target
    i = 1
    while True:
        alt = os.path.join(CLEAN_DIR, f"{base} (cleaned-{i:03d}){ext}")
        if not os.path.exists(alt):
            return alt
        i += 1


def list_maps():
    # Collect all json maps from cleaned/ and raw/, newest first
    items = []
    for tag, folder in (("cleaned", CLEAN_DIR), ("raw", RAW_DIR)):
        if not os.path.isdir(folder):
            continue
        for p in glob.glob(os.path.join(folder, "*.json")):
            mtime = os.path.getmtime(p)
            label = f"[{tag}] {os.path.basename(p)}"
            items.append((label, p, mtime))
    items.sort(key=lambda t: t[2], reverse=True)
    return [(label, path) for (label, path, _mt) in items]


def save_map_to(grid, path):
    # Save map grid as JSON with w/h metadata
    with open(path, "w") as f:
        json.dump({"w": len(grid[0]), "h": len(grid), "grid": grid}, f)
    print("saved to", path)


def load_map_from(path):
    # Load JSON map and fit it into a fixed 50x50 canvas
    with open(path) as f:
        data = json.load(f)
    w, h = data["w"], data["h"]
    g_raw = data["grid"]

    # Trim to stored w/h just in case
    g_raw = [row[:w] for row in g_raw[:h]]

    canvas = new_map(MAP_W, MAP_H, DEFAULT_TILE)
    copy_h = min(h, MAP_H)
    copy_w = min(w, MAP_W)

    for y in range(copy_h):
        row = g_raw[y]
        for x in range(copy_w):
            v = row[x]
            if v not in PALETTE:
                v = DEFAULT_TILE
            canvas[y][x] = v

    print(f"loaded {path} ({w}x{h}) → placed into {MAP_W}x{MAP_H}")
    return canvas


def set_banner(msg, kind="error", duration=4.0):
    # Configure temporary banner message
    global banner_msg, banner_color, banner_ttl
    colors = {
        "error": (200, 60, 60),
        "warn":  (200, 150, 60),
        "ok":    (70, 160, 80),
        "info":  (90, 120, 180),
    }
    banner_msg   = msg
    banner_color = colors.get(kind, (200, 60, 60))
    banner_ttl   = duration


def _load_list_rect():
    # Rect used for the load file list area
    w, h = 560, 420
    rect = pg.Rect((WIN_W - w)//2, (WIN_H - h)//2, w, h)
    lr = pg.Rect(rect.x + 16, rect.y + 56, rect.width - 32, rect.height - 72)
    return lr


def _index_from_mouse(y, start, row_h=24):
    # Convert mouse y-pos into an index in the visible list
    lr = _load_list_rect()
    rel = y - (lr.y + 8)
    if rel < 0:
        return None
    idx_in_view = int(rel // row_h)
    return start + idx_in_view


def tile_px() -> int:
    # Current tile size in pixels (after zoom)
    return int(BASE_TILE * zoom)


def map_viewport_rect():
    # Map area (left), excludes sidebar
    return pg.Rect(0, 0, WIN_W - SIDEBAR_W, WIN_H)


def zoom_at(mouse_x, mouse_y, new_zoom):
    # Zoom around the mouse position and keep that world point stable
    global zoom, cam_x, cam_y
    vp = map_viewport_rect()
    if not vp.collidepoint(mouse_x, mouse_y):
        mouse_x, mouse_y = vp.centerx, vp.centery

    old_zoom = zoom
    if new_zoom == old_zoom:
        return
    old_s = BASE_TILE * old_zoom
    new_zoom = clamp(new_zoom, MIN_ZOOM, MAX_ZOOM)
    new_s = BASE_TILE * new_zoom
    if new_s == old_s:
        return

    wx = cam_x + mouse_x
    wy = cam_y + mouse_y
    scale = new_s / old_s
    cam_x = wx * scale - mouse_x
    cam_y = wy * scale - mouse_y
    zoom = new_zoom
    clamp_camera()


def clamp_camera():
    # Keep camera within the bounds of the map
    vp = map_viewport_rect()
    tp = tile_px()
    world_w = MAP_W * tp
    world_h = MAP_H * tp
    max_x = max(0, world_w - vp.width)
    max_y = max(0, world_h - vp.height)
    global cam_x, cam_y
    cam_x = clamp(cam_x, 0, max_x)
    cam_y = clamp(cam_y, 0, max_y)


def screen_to_tile(sx, sy):
    # Convert screen (pixels) to tile coordinates or None if outside
    vp = map_viewport_rect()
    if not vp.collidepoint(sx, sy):
        return None
    tp = tile_px()
    wx = cam_x + sx
    wy = cam_y + sy
    tx = int(wx // tp)
    ty = int(wy // tp)
    if 0 <= tx < MAP_W and 0 <= ty < MAP_H:
        return tx, ty
    return None


def draw_sidebar():
    # Draw right side panel: controls text, palette, and buttons
    x0 = WIN_W - SIDEBAR_W
    panel = pg.Rect(x0, 0, SIDEBAR_W, WIN_H)
    pg.draw.rect(screen, (28, 28, 32), panel)

    title = font.render("Controls", True, (230, 230, 240))
    screen.blit(title, (x0 + 12, 12))

    lines = [
        "Left click : paint",
        "Right click: erase",
        "1-4        : pick tile",
        "G          : toggle grid",
        "+ / -      : zoom",
        "Arrows     : move",
        "R          : reset view",
        "S          : save",
        "L          : load",
        "Esc        : back to Map Tools",
        "",
        "Rules for cleaned map:",
        "- Solid rectangle (no 0s)",
        "- Exactly ONE home",
        "- Traps <= roundup(sqrt(N))",
        "  N = floor + trap + home",
        "",
        f"Tile: {current_tile} ({PALETTE[current_tile][0]})",
        f"Zoom: {zoom:.2f}",
        f"Cam : {int(cam_x)}, {int(cam_y)}",
    ]
    y = 40
    for s in lines:
        txt = font_small.render(s, True, (210, 210, 220))
        screen.blit(txt, (x0 + 12, y))
        y += 20
    y += 8
    pal_title = font.render("Palette", True, (230, 230, 240))
    screen.blit(pal_title, (x0 + 12, y))
    y += 10

    pal_rects = []
    row_h = 36
    swatch = 24
    left_pad = 12
    col_gap = 10

    # Palette entries
    for tid in PALETTE_ORDER:
        y += row_h
        name, color = PALETTE[tid]

        row_rect = pg.Rect(x0 + 6, y - row_h + 4, SIDEBAR_W - 12, row_h - 8)
        if tid == current_tile:
            pg.draw.rect(screen, (60, 90, 130), row_rect, border_radius=6)
        else:
            pg.draw.rect(screen, (35, 35, 42), row_rect, border_radius=6)

        r = pg.Rect(x0 + left_pad, y - row_h + 8, swatch, swatch)
        pg.draw.rect(screen, color, r)
        pg.draw.rect(screen, (255, 255, 255), r, 2 if tid == current_tile else 1)

        label = f"{tid} — {name}"
        txt = font_small.render(label, True, (235, 235, 240))
        screen.blit(txt, (r.right + col_gap, r.y + 3))

        pal_rects.append((tid, row_rect))

    y += 18
    actions_title = font.render("Actions", True, (230, 230, 240))
    screen.blit(actions_title, (x0 + 12, y))
    y += 12

    def draw_button(label):
        # Draw one button row and return its rect
        nonlocal y
        br = pg.Rect(x0 + 10, y + 8, SIDEBAR_W - 20, 36)
        pg.draw.rect(screen, (40, 44, 54), br, border_radius=8)
        pg.draw.rect(screen, (85, 90, 110), br, 1, border_radius=8)
        t = font.render(label, True, (235, 235, 245))
        screen.blit(t, (br.x + 12, br.y + 6))
        y = br.bottom
        return br

    btn_rects = {
        "save": draw_button("Save"),
        "load": draw_button("Load"),
        "exit": draw_button("Back to Map Tools"),
    }

    return pal_rects, btn_rects


def draw_map():
    # Draw visible part of the map and optional grid overlay
    vp = map_viewport_rect()
    pg.draw.rect(screen, BG, vp)

    tp = tile_px()
    x0 = int(cam_x // tp)
    y0 = int(cam_y // tp)
    x1 = int((cam_x + vp.width) // tp) + 1
    y1 = int((cam_y + vp.height) // tp) + 1
    x0, y0 = clamp(x0, 0, MAP_W-1), clamp(y0, 0, MAP_H-1)
    x1, y1 = clamp(x1, 0, MAP_W-1), clamp(y1, 0, MAP_H-1)

    for ty in range(y0, y1 + 1):
        for tx in range(x0, x1 + 1):
            tid = grid[ty][tx]
            _, color = PALETTE.get(tid, ("?", (255, 0, 255)))
            px = tx * tp - cam_x
            py = ty * tp - cam_y
            pg.draw.rect(screen, color, (px, py, tp, tp))

    if show_grid and tp >= 8:
        gc = (60, 60, 68)
        tx = x0
        while tx <= x1 + 1:
            px = tx * tp - cam_x
            pg.draw.line(screen, gc, (px, 0), (px, vp.height))
            tx += 1
        ty = y0
        while ty <= y1 + 1:
            py = ty * tp - cam_y
            pg.draw.line(screen, gc, (0, py), (vp.width, py))
            ty += 1


def draw_save_prompt():
    # Dim screen and show save-name input overlay
    overlay = pg.Surface((WIN_W, WIN_H), pg.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    w, h = 520, 180
    rect = pg.Rect((WIN_W - w)//2, (WIN_H - h)//2, w, h)
    pg.draw.rect(screen, (24, 24, 28), rect, border_radius=8)
    pg.draw.rect(screen, (90, 90, 110), rect, 1, border_radius=8)
    t = font.render("Save map", True, (235, 235, 245))
    screen.blit(t, (rect.x + 16, rect.y + 14))

    msg = "Type a name (optional). Enter = save   Esc = cancel"
    screen.blit(font_small.render(msg, True, (220, 220, 230)), (rect.x + 16, rect.y + 48))

    ib = pg.Rect(rect.x + 16, rect.y + 80, rect.width - 32, 30)
    pg.draw.rect(screen, (35, 35, 45), ib, border_radius=6)
    pg.draw.rect(screen, (110, 110, 130), ib, 1, border_radius=6)
    shown = typed_name if typed_name else "(auto: mapNNN.json)"
    screen.blit(font.render(shown, True, (240, 240, 250)), (ib.x + 10, ib.y + 4))


def draw_load_menu():
    # Dim screen and show scrollable list of map files
    overlay = pg.Surface((WIN_W, WIN_H), pg.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    w, h = 560, 420
    rect = pg.Rect((WIN_W - w)//2, (WIN_H - h)//2, w, h)
    pg.draw.rect(screen, (24, 24, 28), rect, border_radius=8)
    pg.draw.rect(screen, (90, 90, 110), rect, 1, border_radius=8)
    t = font.render("Load map — choose a file (Enter)   Esc = cancel", True, (235, 235, 245))
    screen.blit(t, (rect.x + 16, rect.y + 14))

    lr = pg.Rect(rect.x + 16, rect.y + 56, rect.width - 32, rect.height - 72)
    pg.draw.rect(screen, (32, 32, 40), lr, border_radius=6)

    visible = 16
    start = scroll_offset
    end = min(start + visible, len(load_list))
    y = lr.y + 8
    for i in range(start, end):
        label, _path = load_list[i]
        row = pg.Rect(lr.x + 8, y, lr.width - 16, 22)
        if i == load_sel:
            pg.draw.rect(screen, (70, 90, 120), row, border_radius=4)
        screen.blit(font_small.render(label, True, (240, 240, 250)), (row.x + 8, row.y + 3))
        y += 24


def draw_banner(dt):
    # Draw the banner message at top-left of map area
    global banner_ttl
    if banner_ttl <= 0 or not banner_msg:
        return
    banner_ttl = max(0.0, banner_ttl - dt)

    vp = map_viewport_rect()
    pad_x, pad_y = 14, 10
    text = font.render(banner_msg, True, (245, 245, 250))
    box_w = min(vp.width - pad_x*2, text.get_width() + 28)
    box_h = text.get_height() + 16
    rect = pg.Rect(vp.x + pad_x, vp.y + pad_y, box_w, box_h)

    s = pg.Surface((rect.width, rect.height), pg.SRCALPHA)
    s.fill((*banner_color, 210))
    screen.blit(s, rect.topleft)
    pg.draw.rect(screen, (15, 15, 18), rect, 2, border_radius=8)

    screen.blit(text, (rect.x + 12, rect.y + (rect.height - text.get_height())//2))


def draw(dt):
    # High level draw: map, UI, modal dialogs, banner
    draw_map()
    pal_rects, btn_rects = draw_sidebar()
    if mode == "save_prompt":
        draw_save_prompt()
    elif mode == "load_menu":
        draw_load_menu()
    draw_banner(dt)
    pg.display.flip()
    return pal_rects, btn_rects


def main():
    # Main editor loop / state setup
    global screen, clock, font, font_small
    global cam_x, cam_y, zoom, current_tile, show_grid, mode
    global typed_name, load_list, load_sel, scroll_offset
    global grid, banner_msg, banner_color, banner_ttl

    if not pg.get_init():
        pg.init()

    screen = pg.display.set_mode((WIN_W, WIN_H))
    pg.display.set_caption("Lil Cheese Hunter™ - Map Editor")
    clock = pg.time.Clock()
    font = pg.font.SysFont("consolas", 16)
    font_small = pg.font.SysFont("consolas", 14)

    # Map / camera initial state
    grid = new_map(MAP_W, MAP_H)
    current_tile = 1

    cam_x, cam_y = 0.0, 0.0
    zoom = 1.0
    show_grid = True

    # UI state
    mode = "edit"
    typed_name = ""
    load_list = []
    load_sel = 0
    scroll_offset = 0

    # Banner state
    banner_msg = ""
    banner_color = (200, 60, 60)
    banner_ttl = 0.0

    running = True
    pal_rects = []

    # Button rects (get updated after first draw)
    btn_rects = {
        "save": pg.Rect(0, 0, 0, 0),
        "load": pg.Rect(0, 0, 0, 0),
        "exit": pg.Rect(0, 0, 0, 0),
    }

    while running:
        dt = clock.tick(60) / 1000.0

        for e in pg.event.get():
            if e.type == pg.QUIT:
                running = False
                break

            # SAVE PROMPT MODE ---------------------------------------
            if mode == "save_prompt":
                if e.type == pg.KEYDOWN:
                    if e.key == pg.K_ESCAPE:
                        mode = "edit"
                    elif e.key == pg.K_RETURN:
                        # Validate and save map
                        trimmed = trim_rows_cols(grid)
                        if not trimmed:
                            set_banner("Cannot save: nothing left after trimming.", "warn")
                            typed_name = ""
                            mode = "edit"
                            continue

                        zero_found = False
                        home_count = 0
                        floor_count = 0
                        trap_count = 0

                        for row in trimmed:
                            for v in row:
                                if v == 0:
                                    zero_found = True
                                if v == 4:
                                    home_count += 1
                                elif v == 2:
                                    floor_count += 1
                                elif v == 3:
                                    trap_count += 1

                        if zero_found:
                            set_banner(
                                "Cannot save: 0 tiles remain inside. Fill them to make a solid rectangle.",
                                "error"
                            )
                            typed_name = ""
                            mode = "edit"
                            continue

                        if home_count != 1:
                            if home_count == 0:
                                set_banner("Cannot save: MUST HAVE 1 home tile.", "error")
                            else:
                                extra_homes = home_count - 1
                                set_banner(
                                    f"Cannot save: too many homes — can only have 1, remove {extra_homes}.",
                                    "error"
                                )
                            typed_name = ""
                            mode = "edit"
                            continue

                        total = floor_count + trap_count + home_count
                        limit = math.ceil(math.sqrt(total))
                        if trap_count > limit:
                            extra = trap_count - limit
                            set_banner(
                                f"Cannot save: too many traps — {extra} extra "
                                f"(traps {trap_count}, limit {limit}, N={total}).",
                                "error"
                            )
                            typed_name = ""
                            mode = "edit"
                            continue

                        # Passed checks → save raw + cleaned variants
                        if typed_name.strip():
                            raw_path = safe_custom_name(typed_name.strip(), folder=RAW_DIR)
                        else:
                            raw_path = next_save_name(folder=RAW_DIR)

                        save_map_to(grid, raw_path)
                        cpath = cleaned_path_for(raw_path)
                        save_map_to(trimmed, cpath)
                        set_banner(
                            f"Saved ✓ {len(trimmed[0])}x{len(trimmed)} "
                            f"(traps {trap_count} ≤ limit {limit}, N={total})",
                            "ok"
                        )

                        typed_name = ""
                        mode = "edit"

                    elif e.key == pg.K_BACKSPACE:
                        typed_name = typed_name[:-1]
                    else:
                        if e.unicode and e.key not in (pg.K_RETURN, pg.K_TAB):
                            typed_name += e.unicode
                # Skip normal edit handling when save dialog is open
                continue

            # LOAD MENU MODE -----------------------------------------
            if mode == "load_menu":
                if e.type == pg.KEYDOWN:
                    if e.key == pg.K_ESCAPE:
                        mode = "edit"
                    elif e.key in (pg.K_UP, pg.K_k):
                        load_sel = max(0, load_sel - 1)
                        if load_sel < scroll_offset:
                            scroll_offset = load_sel
                    elif e.key in (pg.K_DOWN, pg.K_j):
                        load_sel = min(len(load_list) - 1, load_sel + 1)
                        visible = 16
                        if load_sel >= scroll_offset + visible:
                            scroll_offset = load_sel - visible + 1
                    elif e.key == pg.K_RETURN and load_list:
                        # Enter = load selected file
                        try:
                            path = load_list[load_sel][1]
                            new_grid = load_map_from(path)
                            for y in range(MAP_H):
                                grid[y] = new_grid[y][:]
                            mode = "edit"
                            set_banner(f"Loaded {os.path.basename(path)}", "info")
                        except Exception as ex:
                            print("load failed:", ex)
                            set_banner("Load failed — see console.", "error")

                elif e.type == pg.MOUSEBUTTONDOWN:
                    lr = _load_list_rect()
                    if e.button == 1 and lr.collidepoint(*e.pos):
                        # Single / double click in list
                        idx = _index_from_mouse(e.pos[1], scroll_offset)
                        if idx is not None and 0 <= idx < len(load_list):
                            if idx == load_sel and getattr(main, "_last_click_t", 0) and \
                               pg.time.get_ticks() - main._last_click_t < 350:
                                try:
                                    path = load_list[load_sel][1]
                                    new_grid = load_map_from(path)
                                    for y in range(MAP_H):
                                        grid[y] = new_grid[y][:]
                                    mode = "edit"
                                    set_banner(f"Loaded {os.path.basename(path)}", "info")
                                except Exception as ex:
                                    print("load failed:", ex)
                                    set_banner("Load failed — see console.", "error")
                            else:
                                load_sel = idx
                            main._last_click_t = pg.time.get_ticks()
                    elif e.button in (4, 5):
                        # Scroll with wheel
                        visible = 16
                        delta = -1 if e.button == 4 else 1
                        max_start = max(0, len(load_list) - visible)
                        scroll_offset = clamp(scroll_offset + delta, 0, max_start)

                # Skip edit handling while load dialog open
                continue

            # EDIT MODE ----------------------------------------------
            if e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    # Quit editor
                    running = False
                    break
                elif e.key == pg.K_g:
                    show_grid = not show_grid
                elif pg.K_0 <= e.key <= pg.K_9:
                    # Number keys choose tile (if in palette)
                    n = e.key - pg.K_0
                    if n in PALETTE_ORDER:
                        current_tile = n
                elif e.key in (pg.K_EQUALS, pg.K_PLUS):
                    mx, my = pg.mouse.get_pos()
                    zoom_at(mx, my, zoom * 1.1)
                elif e.key == pg.K_MINUS:
                    mx, my = pg.mouse.get_pos()
                    zoom_at(mx, my, zoom / 1.1)
                elif e.key == pg.K_r:
                    # Reset camera and zoom
                    zoom = 1.0
                    cam_x, cam_y = 0.0, 0.0
                    clamp_camera()
                elif e.key == pg.K_s:
                    # Open save prompt
                    typed_name = ""
                    mode = "save_prompt"
                elif e.key == pg.K_l:
                    # Open load menu
                    load_list[:] = list_maps()
                    load_sel = 0
                    scroll_offset = 0
                    mode = "load_menu"

            elif e.type == pg.MOUSEBUTTONDOWN and mode == "edit":
                mx, my = e.pos
                if e.button == 1:
                    # Check palette hit
                    for tid, r in pal_rects:
                        if r.collidepoint(mx, my):
                            current_tile = tid
                            break
                    else:
                        # Check buttons
                        if btn_rects["save"].collidepoint(mx, my):
                            typed_name = ""
                            mode = "save_prompt"
                        elif btn_rects["load"].collidepoint(mx, my):
                            load_list[:] = list_maps()
                            load_sel = 0
                            scroll_offset = 0
                            mode = "load_menu"
                        elif btn_rects["exit"].collidepoint(mx, my):
                            # Trigger quit event
                            pg.event.post(pg.event.Event(pg.QUIT))

        # Window might be gone already
        if not running or not pg.display.get_surface():
            break

        # Camera movement with arrow keys
        keys = pg.key.get_pressed()
        move = PAN_SPEED * dt / max(zoom, 1e-6)
        if keys[pg.K_LEFT]:
            cam_x -= move
        if keys[pg.K_RIGHT]:
            cam_x += move
        if keys[pg.K_UP]:
            cam_y -= move
        if keys[pg.K_DOWN]:
            cam_y += move
        clamp_camera()

        # Painting grid with mouse
        if mode == "edit" and pg.mouse.get_focused():
            pos = pg.mouse.get_pos()
            tt = screen_to_tile(*pos)
            if tt:
                tx, ty = tt
                buttons = pg.mouse.get_pressed(num_buttons=3)
                if buttons[0]:
                    # Left drag: paint
                    if current_tile == 4:
                        # Only one home: convert old homes to floor
                        for yy in range(MAP_H):
                            for xx in range(MAP_W):
                                if grid[yy][xx] == 4:
                                    grid[yy][xx] = 2
                        grid[ty][tx] = 4
                    else:
                        grid[ty][tx] = current_tile
                elif buttons[2]:
                    # Right drag: erase back to default
                    grid[ty][tx] = DEFAULT_TILE

        # Draw frame
        pal_rects, btn_rects = draw(dt)

    pg.quit()
    return


if __name__ == "__main__":
    main()
