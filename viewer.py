import json, os, glob, sys
import pygame as pg

PALETTE = {
    0: ("empty", (35, 35, 40)),
    1: ("wall",  (25, 60, 150)),
    2: ("floor", (180, 180, 190)),
    3: ("trap",  (150, 40, 40)),
    4: ("home",  (40, 170, 80)),
}
BG = (0, 0, 0)

EXPECTED_KEYS = {"w", "h", "grid"}

def is_map_json(path):
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if not isinstance(data, dict) or not EXPECTED_KEYS.issubset(data.keys()):
            return False
        g = data["grid"]
        if not isinstance(g, list) or not g:
            return False
        w = len(g[0])
        for row in g:
            if not isinstance(row, list) or len(row) != w:
                return False
            if not all(isinstance(v, int) for v in row):
                return False
        return True
    except Exception:
        return False

SEARCH_DIRS = ["cleaned", "raw", "."]

def list_maps():
    results = []
    for d in SEARCH_DIRS:
        if not os.path.isdir(d):
            continue
        files = sorted(glob.glob(os.path.join(d, "*.json")))
        for f in files:
            if is_map_json(f):
                label = f"[{os.path.basename(d)}] {os.path.basename(f)}"
                results.append((label, f))
    if not results:
        for f in sorted(glob.glob("*.json")):
            if is_map_json(f):
                results.append(("[.]", os.path.abspath(f)))
    return results

def load_map(path):
    with open(path, "r") as f:
        data = json.load(f)
    w, h, g = data["w"], data["h"], data["grid"]
    g = [row[:w] for row in g[:h]]

    norm_grid = []
    for row in g:
        new_row = []
        for v in row:
 
            if v not in PALETTE:
                v = 0      
            new_row.append(v)
        norm_grid.append(new_row)

    return w, h, norm_grid

class Viewer:
    def __init__(self, map_path):
        self.path = map_path
        self.w, self.h, self.grid = load_map(map_path)

        pg.init()
        title_name = os.path.basename(map_path)
        folder = os.path.basename(os.path.dirname(os.path.abspath(map_path)))
        if folder in ("cleaned", "raw"):
            title_name = f"{title_name}  —  {folder}"
        pg.display.set_caption(f"TreatQuest Viewer — {title_name}")

        self.side_w = 260
        self.win_w, self.win_h = 1200, 800
        self.viewport = pg.Rect(0, 0, self.win_w - self.side_w, self.win_h)
        self.screen = pg.display.set_mode((self.win_w, self.win_h))
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont("consolas", 16)
        self.font_small = pg.font.SysFont("consolas", 14)

        self.min_tile = 2
        self.max_tile = 64
        self.tile_px = 16
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.show_grid = True

        self.is_panning = False
        self.pan_anchor = (0, 0)
        self.cam_anchor = (0.0, 0.0)

        self.back_rect = None

        self.fit_to_view()

    def world_size_px(self):
        return self.w * self.tile_px, self.h * self.tile_px

    def clamp_cam(self):
        vw, vh = self.viewport.size
        ww, wh = self.world_size_px()
        max_x = max(0, ww - vw)
        max_y = max(0, wh - vh)
        self.cam_x = max(0, min(self.cam_x, max_x))
        self.cam_y = max(0, min(self.cam_y, max_y))

    def fit_to_view(self):
        vw, vh = self.viewport.size
        if self.w == 0 or self.h == 0:
            self.tile_px = 16
        else:
            tx = max(self.min_tile, min(self.max_tile, vw // self.w))
            ty = max(self.min_tile, min(self.max_tile, vh // self.h))
            self.tile_px = max(self.min_tile, min(self.max_tile, int(min(tx, ty))))
        ww, wh = self.world_size_px()
        self.cam_x = max(0, (ww - self.viewport.width) / 2)
        self.cam_y = max(0, (wh - self.viewport.height) / 2)
        self.clamp_cam()

    def zoom_at(self, mx, my, factor):
        old = self.tile_px
        new = int(max(self.min_tile, min(self.max_tile, round(self.tile_px * factor))))
        if new == old:
            return
        if not self.viewport.collidepoint(mx, my):
            mx, my = self.viewport.center
        wx = self.cam_x + (mx - self.viewport.x)
        wy = self.cam_y + (my - self.viewport.y)
        scale = new / old
        self.cam_x = wx * scale - (mx - self.viewport.x)
        self.cam_y = wy * scale - (my - self.viewport.y)
        self.tile_px = new
        self.clamp_cam()

    def draw_side(self):
        x0 = self.viewport.right
        panel = pg.Rect(x0, 0, self.side_w, self.win_h)
        pg.draw.rect(self.screen, (28, 28, 32), panel)

        def line(y, text, big=False):
            f = self.font if big else self.font_small
            self.screen.blit(f.render(text, True, (230, 230, 240)), (x0 + 12, y))
            return y + (26 if big else 20)

        y = 12
        y = line(y, "Viewer", big=True)
        y = line(y, f"File: {os.path.basename(self.path)}")
        y = line(y, f"Size: {self.w} x {self.h}")
        y = line(y, f"Tile: {self.tile_px}px")
        y = line(y, f"Cam : {int(self.cam_x)}, {int(self.cam_y)}")
        y += 6
        y = line(y, "Controls", big=True)
        for s in [
            "+ / - : zoom",
            "Wheel : zoom",
            "Arrows: pan",
            "MMB   : drag pan",
            "F     : fit to view",
            "R     : reset zoom",
            "G     : grid on/off",
            "Esc   : back to Map Tools",
        ]:
            y = line(y, s)
        y += 8
        y = line(y, "Legend", big=True)

        row_h = 24
        for tid in sorted(PALETTE.keys()):
            name, color = PALETTE[tid]
            r = pg.Rect(x0 + 12, y, 18, 18)
            pg.draw.rect(self.screen, color, r)
            pg.draw.rect(self.screen, (255, 255, 255), r, 1)
            self.screen.blit(
                self.font_small.render(f"{tid} — {name}", True, (235, 235, 240)),
                (r.right + 8, y - 2)
            )
            y += row_h

        self.back_rect = None

        btn_h = 36
        btn_w = panel.width - 24
        bx = x0 + 12
        by = self.win_h - btn_h - 16
        back_rect = pg.Rect(bx, by, btn_w, btn_h)

        pg.draw.rect(self.screen, (60, 120, 200), back_rect, border_radius=8)
        pg.draw.rect(self.screen, (240, 240, 250), back_rect, 1, border_radius=8)

        label = self.font_small.render("Back to Map Tools", True, (5, 5, 10))
        self.screen.blit(
            label,
            (back_rect.centerx - label.get_width() // 2,
             back_rect.centery - label.get_height() // 2),
        )

        self.back_rect = back_rect


    def draw_map(self):
        pg.draw.rect(self.screen, BG, self.viewport)

        tp = self.tile_px
        x0 = int(self.cam_x // tp)
        y0 = int(self.cam_y // tp)
        x1 = int((self.cam_x + self.viewport.width) // tp) + 1
        y1 = int((self.cam_y + self.viewport.height) // tp) + 1
        x0 = max(0, min(self.w - 1 if self.w else 0, x0))
        y0 = max(0, min(self.h - 1 if self.h else 0, y0))
        x1 = max(0, min(self.w - 1 if self.w else 0, x1))
        y1 = max(0, min(self.h - 1 if self.h else 0, y1))

        for ty in range(y0, y1 + 1):
            row = self.grid[ty]
            for tx in range(x0, x1 + 1):
                tid = row[tx]
                _, color = PALETTE.get(tid, ("?", (255, 0, 255)))
                px = self.viewport.x + tx * tp - self.cam_x
                py = self.viewport.y + ty * tp - self.cam_y
                pg.draw.rect(self.screen, color, (px, py, tp, tp))

        if self.show_grid and tp >= 6:
            gc = (60, 60, 68)
            tx = x0
            while tx <= x1 + 1:
                px = self.viewport.x + tx * tp - self.cam_x
                pg.draw.line(self.screen, gc, (px, self.viewport.y), (px, self.viewport.bottom))
                tx += 1
            ty = y0
            while ty <= y1 + 1:
                py = self.viewport.y + ty * tp - self.cam_y
                pg.draw.line(self.screen, gc, (self.viewport.x, py), (self.viewport.right, py))
                ty += 1

    def loop(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            for e in pg.event.get():
                if e.type == pg.QUIT:
                    running = False
                elif e.type == pg.KEYDOWN:
                    if e.key == pg.K_ESCAPE:
                        running = False
                    elif e.key == pg.K_g:
                        self.show_grid = not self.show_grid
                    elif e.key in (pg.K_EQUALS, pg.K_PLUS):
                        mx, my = pg.mouse.get_pos()
                        self.zoom_at(mx, my, 1.1)
                    elif e.key == pg.K_MINUS:
                        mx, my = pg.mouse.get_pos()
                        self.zoom_at(mx, my, 1/1.1)
                    elif e.key == pg.K_r:
                        self.tile_px = max(self.min_tile, min(self.max_tile, 16))
                        self.cam_x, self.cam_y = 0.0, 0.0
                        self.clamp_cam()
                    elif e.key == pg.K_f:
                        self.fit_to_view()
                elif e.type == pg.MOUSEWHEEL:
                    mx, my = pg.mouse.get_pos()
                    self.zoom_at(mx, my, 1.1 if e.y > 0 else 1/1.1)
                elif e.type == pg.MOUSEBUTTONDOWN:
                    if e.button == 1:
                        if self.back_rect and self.back_rect.collidepoint(e.pos):
                            running = False  
                        else:
                            pass
                    elif e.button == 2:
                        self.is_panning = True
                        self.pan_anchor = e.pos
                        self.cam_anchor = (self.cam_x, self.cam_y)

                    elif e.button == 3:
                        pass

                elif e.type == pg.MOUSEBUTTONUP and e.button == 2:
                    self.is_panning = False
                elif e.type == pg.MOUSEMOTION and self.is_panning:
                    mx, my = e.pos
                    dx = mx - self.pan_anchor[0]
                    dy = my - self.pan_anchor[1]
                    self.cam_x = self.cam_anchor[0] - dx
                    self.cam_y = self.cam_anchor[1] - dy
                    self.clamp_cam()

            keys = pg.key.get_pressed()
            pan_speed = 800 * dt * max(1, 16 / max(1, self.tile_px))
            if keys[pg.K_LEFT]:  self.cam_x -= pan_speed
            if keys[pg.K_RIGHT]: self.cam_x += pan_speed
            if keys[pg.K_UP]:    self.cam_y -= pan_speed
            if keys[pg.K_DOWN]:  self.cam_y += pan_speed
            self.clamp_cam()

            self.draw_map()
            self.draw_side()
            pg.display.flip()
        pg.quit()

def run_picker_and_view():
    items = list_maps()
    if not items:
        print("No valid map JSONs found in cleaned/, raw/ or current folder.")
        return

    pg.init()
    font = pg.font.SysFont("consolas", 16)
    screen = pg.display.set_mode((760, 520))
    pg.display.set_caption("Select a TreatQuest map (Enter to open)")

    sel = 0
    offset = 0
    running = True

    while running:
        screen.fill((20, 20, 24))

        title = font.render(
            "Select a map (Up/Down, Enter, Esc/Back) — preferring [cleaned]",
            True,
            (240, 240, 250),
        )
        screen.blit(title, (16, 12))

        top_y = 52
        line_h = 24
        max_visible = (screen.get_height() - top_y - 70) // line_h
        visible = min(max_visible, len(items))

        if sel < offset:
            offset = sel
        if sel >= offset + visible:
            offset = sel - visible + 1

        for i in range(visible):
            idx = offset + i
            label, path = items[idx]
            y = top_y + i * line_h

            if idx == sel:
                pg.draw.rect(
                    screen,
                    (60, 80, 130),
                    pg.Rect(10, y - 2, screen.get_width() - 20, line_h + 4),
                    border_radius=4,
                )
                color = (255, 255, 255)
            else:
                color = (190, 190, 200)

            text_surf = font.render(label, True, color)
            screen.blit(text_surf, (20, y))

        back_rect = pg.Rect(16, screen.get_height() - 48, 120, 30)
        pg.draw.rect(screen, (60, 120, 200), back_rect, border_radius=6)
        pg.draw.rect(screen, (230, 230, 240), back_rect, 1, border_radius=6)
        back_label = font.render("Back", True, (0, 0, 0))
        screen.blit(
            back_label,
            (back_rect.centerx - back_label.get_width() // 2,
             back_rect.centery - back_label.get_height() // 2),
        )

        pg.display.flip()

        for e in pg.event.get():
            if e.type == pg.QUIT:
                pg.quit()
                return

            elif e.type == pg.KEYDOWN:
                if e.key == pg.K_ESCAPE:
                    pg.quit()
                    return
                elif e.key == pg.K_UP:
                    sel = max(0, sel - 1)
                elif e.key == pg.K_DOWN:
                    sel = min(len(items) - 1, sel + 1)
                elif e.key in (pg.K_RETURN, pg.K_SPACE):
                    path = items[sel][1]
                    pg.quit()
                    Viewer(path).loop()
                    return

            elif e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                if back_rect.collidepoint(e.pos):
                    pg.quit()
                    return

                click_x, click_y = e.pos
                if top_y <= click_y < top_y + visible * line_h:
                    row = (click_y - top_y) // line_h
                    idx = offset + row
                    if 0 <= idx < len(items):
                        sel = idx



if __name__ == "__main__":
    if len(sys.argv) == 2 and os.path.isfile(sys.argv[1]):
        Viewer(sys.argv[1]).loop()
    else:
        run_picker_and_view()
