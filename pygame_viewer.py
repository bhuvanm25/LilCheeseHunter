import os
import pygame

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900

COLORS = {
    "WALL": (20, 20, 30),
    "EMPTY": (235, 85, 100),
    "GRID": (45, 45, 60),
    "AGENT": (255, 220, 240),
    "TREAT": (255, 200, 40),
    "TRAP": (80, 0, 0),
    "HOME": (0, 200, 0),
    "PANEL_BG": (30, 30, 40),
}

IDX_VOID = 1
IDX_WALL = 2
IDX_FLOOR = 3
IDX_TRAP = 4
IDX_CHEESE = 5
IDX_JERRY = 6
IDX_JERRY_ON_CHEESE = 7
IDX_JERRY_ON_TRAP = 8
IDX_HOME = 9


class PygameViewer:
    def __init__(self, rows, cols, max_width=WINDOW_WIDTH,
                 max_height=WINDOW_HEIGHT, title="TreatQuest"):
        pygame.init()
        self.rows = rows
        self.cols = cols

        self.prev_cheese_mask = None
        self.prev_agent_pos = None

        margin_factor = 1.1
        tile_w = max_width / (cols * margin_factor)
        tile_h = max_height / (rows * margin_factor)
        tile = int(min(tile_w, tile_h))
        tile = max(4, tile)

        margin = 0
        self.tile = tile
        self.margin = margin

        grid_w = cols * tile + (cols + 1) * margin
        grid_h = rows * tile + (rows + 1) * margin
        self.grid_width = grid_w
        self.grid_height = grid_h

        self.panel_width = 300
        total_w = grid_w + self.panel_width
        total_h = grid_h

        self.screen = pygame.display.set_mode(
            (int(total_w), int(total_h)),
            pygame.RESIZABLE | pygame.SCALED
        )
        self.min_window_size = (int(total_w), int(total_h))

        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.closed = False

        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 20)

        self.tile_images = self._load_tile_images()

        self.slider_min_fps = 5
        self.slider_max_fps = 500
        self.fps_value = 50
        self.slider_dragging = False

        panel_x0 = self.grid_width
        panel_w = self.panel_width

        self.slider_width = int(panel_w * 0.8)
        self.slider_height = 8
        self.slider_x = panel_x0 + (panel_w - self.slider_width) // 2
        self.slider_y = self.grid_height - 70

        btn_w, btn_h = 80, 30
        btn_x = panel_x0 + (panel_w - btn_w) // 2
        btn_y = self.slider_y + 30
        self.skip_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

        self.show_animation = True

        self.show_report_overlay = False
        self.report_surface = None
        self.report_button_rect = None
        self.report_close_rect = None

    def _load_tile_images(self):
        images = {}
        base_dir = os.path.dirname(os.path.abspath(__file__))
        img_dir = os.path.join(base_dir, "images")

        mapping = {
            IDX_VOID: "void.png",
            IDX_WALL: "wall.png",
            IDX_FLOOR: "floor.png",
            IDX_TRAP: "trap.png",
            IDX_CHEESE: "cheese.png",
            IDX_JERRY: "jerry.png",
            IDX_JERRY_ON_CHEESE: "jerryWcheese.png",
            IDX_JERRY_ON_TRAP: "jerryWtrap.png",
            IDX_HOME: "home.png",
        }

        for idx, filename in mapping.items():
            path = os.path.join(img_dir, filename)
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.smoothscale(img, (self.tile, self.tile))
                images[idx] = img
                print(f"[OK] Loaded {filename}")
            except Exception as e:
                print(f"[WARN] Could not load {path}: {e}")
                images[idx] = None

        return images

    def load_report_image(self, filename="training_report.png"):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, filename)

        try:
            img = pygame.image.load(path).convert()
        except Exception as e:
            print(f"[WARN] Could not load report image {path}: {e}")
            self.report_surface = None
            return

        sw, sh = self.screen.get_size()
        target_w = int(sw * 0.8)
        target_h = int(sh * 0.8)
        img = pygame.transform.smoothscale(img, (target_w, target_h))
        self.report_surface = img
        print(f"[OK] Loaded report image from {path}")

    def close(self):
        if not self.closed:
            pygame.display.quit()
            pygame.quit()
            self.closed = True

    def _rect_at(self, r, c):
        x = self.margin + c * (self.tile + self.margin)
        y = self.margin + r * (self.tile + self.margin)
        return pygame.Rect(x, y, self.tile, self.tile)

    def cell_at_pixel(self, x, y):
        if x >= self.grid_width:
            return None
        c = (x - self.margin) // (self.tile + self.margin)
        r = (y - self.margin) // (self.tile + self.margin)
        r, c = int(r), int(c)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return r, c
        return None

    def _value_to_slider_x(self, value: int) -> int:
        ratio = (value - self.slider_min_fps) / (self.slider_max_fps - self.slider_min_fps)
        ratio = max(0.0, min(1.0, ratio))
        return int(self.slider_x + ratio * self.slider_width)

    def _pos_to_value(self, px: int) -> int:
        ratio = (px - self.slider_x) / self.slider_width
        ratio = max(0.0, min(1.0, ratio))
        return int(self.slider_min_fps + ratio * (self.slider_max_fps - self.slider_min_fps))

    def _handle_slider_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if (self.slider_y - 10) <= my <= (self.slider_y + self.slider_height + 10) and \
               self.slider_x <= mx <= (self.slider_x + self.slider_width):
                self.slider_dragging = True
                self.fps_value = self._pos_to_value(mx)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.slider_dragging = False
        elif event.type == pygame.MOUSEMOTION and self.slider_dragging:
            mx, _ = event.pos
            mx = max(self.slider_x, min(mx, self.slider_x + self.slider_width))
            self.fps_value = self._pos_to_value(mx)

    def _draw_slider_and_button(self):
        line_y = self.slider_y + self.slider_height // 2
        pygame.draw.line(
            self.screen,
            (220, 220, 220),
            (self.slider_x, line_y),
            (self.slider_x + self.slider_width, line_y),
            4,
        )

        knob_x = self._value_to_slider_x(self.fps_value)
        pygame.draw.circle(self.screen, (255, 200, 40), (knob_x, line_y), 10)

        fps_text = self.small_font.render(
            f"Speed: {self.fps_value} FPS", True, (255, 255, 255)
        )
        self.screen.blit(fps_text, (self.slider_x, self.slider_y - 22))

        label = "SKIP" if self.show_animation else "SHOW"
        pygame.draw.rect(self.screen, (60, 60, 60), self.skip_button_rect, border_radius=6)
        txt = self.small_font.render(label, True, (255, 255, 255))
        txt_rect = txt.get_rect(center=self.skip_button_rect.center)
        self.screen.blit(txt, txt_rect)

    def _draw_report_overlay(self):
        if not self.show_report_overlay or self.report_surface is None:
            self.report_close_rect = None
            return

        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        img_rect = self.report_surface.get_rect(center=self.screen.get_rect().center)
        self.screen.blit(self.report_surface, img_rect)

        x_size = 32
        padding = 8
        x_rect = pygame.Rect(
            img_rect.right - x_size - padding,
            img_rect.top + padding,
            x_size,
            x_size,
        )
        self.report_close_rect = x_rect

        pygame.draw.rect(self.screen, (40, 40, 60), x_rect, border_radius=6)
        pygame.draw.rect(self.screen, (200, 200, 220), x_rect, 2, border_radius=6)

        x_text = self.small_font.render("X", True, (255, 255, 255))
        x_text_rect = x_text.get_rect(center=x_rect.center)
        self.screen.blit(x_text, x_text_rect)

        hint = self.small_font.render("Press Esc or click X to close", True, (255, 255, 255))
        hint_rect = hint.get_rect(
            midbottom=(self.screen.get_width() // 2, self.screen.get_height() - 20)
        )
        self.screen.blit(hint, hint_rect)

    def _draw_stats_panel(self, env):
        panel_x0 = self.grid_width
        panel_rect = pygame.Rect(panel_x0, 0, self.panel_width, self.grid_height)
        pygame.draw.rect(self.screen, COLORS["PANEL_BG"], panel_rect)

        y = 10

        title = self.font.render("TreatQuest Stats", True, (255, 255, 255))
        self.screen.blit(title, (panel_x0 + 10, y))
        y += 30

        map_text = self.small_font.render(
            f"Map: {self.rows} × {self.cols}", True, (220, 220, 220)
        )
        self.screen.blit(map_text, (panel_x0 + 10, y))
        y += 20

        in_training = getattr(env, "in_training", False)
        mode_str = "Training" if in_training else "Play"
        mode_text = self.small_font.render(f"Mode: {mode_str}", True, (220, 220, 220))
        self.screen.blit(mode_text, (panel_x0 + 10, y))
        y += 25

        has_report = getattr(env, "has_training_report", False)
        if has_report and self.report_surface is not None:
            btn_w, btn_h = 110, 30
            btn_x = panel_x0 + 10
            btn_y = y
            self.report_button_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

            pygame.draw.rect(self.screen, (80, 80, 110), self.report_button_rect, border_radius=8)
            txt = self.small_font.render("REPORT", True, (255, 255, 255))
            txt_rect = txt.get_rect(center=self.report_button_rect.center)
            self.screen.blit(txt, txt_rect)

            y += 40
        else:
            self.report_button_rect = None

        alpha = getattr(env, "alpha", None)
        gamma = getattr(env, "gamma", None)
        eps0 = getattr(env, "epsilon", None)
        max_st = getattr(env, "max_steps", None)
        eps_pt = getattr(env, "episodes_per_tile", None)

        if alpha is not None and gamma is not None:
            self.screen.blit(
                self.small_font.render(f"α={alpha:.2f}  γ={gamma:.2f}",
                                       True, (200, 200, 200)),
                (panel_x0 + 10, y),
            )
            y += 20
        if eps0 is not None:
            self.screen.blit(
                self.small_font.render(f"ε(start)={eps0:.2f}", True, (200, 200, 200)),
                (panel_x0 + 10, y),
            )
            y += 20
        if max_st is not None:
            self.screen.blit(
                self.small_font.render(f"Max steps/episode: {max_st}",
                                       True, (200, 200, 200)),
                (panel_x0 + 10, y),
            )
            y += 20
        if eps_pt is not None:
            self.screen.blit(
                self.small_font.render(f"Max episodes/tile: {eps_pt}",
                                       True, (200, 200, 200)),
                (panel_x0 + 10, y),
            )
            y += 25

        if in_training:
            total_tiles = getattr(env, "training_total_tiles", 0)
            tile_index = getattr(env, "training_tile_index", 0)
            episode = getattr(env, "training_episode", 0)
            max_eps_tile = getattr(env, "training_max_episodes_for_this_tile", 1)
            success_rate = getattr(env, "training_success_rate", None)

            if total_tiles > 0:
                tile_line = f"Tile: {tile_index + 1}/{total_tiles}"
            else:
                tile_line = "Tile: n/a"
            self.screen.blit(
                self.small_font.render(tile_line, True, (220, 220, 220)),
                (panel_x0 + 10, y),
            )
            y += 20

            ep_line = f"Episode: {episode}/{max_eps_tile}"
            self.screen.blit(
                self.small_font.render(ep_line, True, (220, 220, 220)),
                (panel_x0 + 10, y),
            )
            y += 20

            if success_rate is not None:
                sr_line = f"Recent success: {success_rate * 100:5.1f}%"
                self.screen.blit(
                    self.small_font.render(sr_line, True, (220, 220, 220)),
                    (panel_x0 + 10, y),
                )
                y += 20

            cur_step = getattr(env, "current_step", 0)
            cur_max = getattr(env, "current_max_steps", 0)
            cur_eps = getattr(env, "training_epsilon",
                              getattr(env, "epsilon", 0.0))
            last_R = getattr(env, "training_last_reward", None)
            avg_R = getattr(env, "training_avg_reward", None)

            step_line = f"Step: {cur_step}/{cur_max}"
            self.screen.blit(
                self.small_font.render(step_line, True, (220, 220, 220)),
                (panel_x0 + 10, y),
            )
            y += 18

            eps_line = f"ε(now)={cur_eps:.3f}"
            self.screen.blit(
                self.small_font.render(eps_line, True, (220, 220, 220)),
                (panel_x0 + 10, y),
            )
            y += 18

            if last_R is not None:
                self.screen.blit(
                    self.small_font.render(f"Last R: {last_R:.1f}",
                                           True, (220, 220, 220)),
                    (panel_x0 + 10, y),
                )
                y += 18

            if avg_R is not None:
                self.screen.blit(
                    self.small_font.render(f"Avg R: {avg_R:.1f}",
                                           True, (220, 220, 220)),
                    (panel_x0 + 10, y),
                )
                y += 25

            if total_tiles > 0:
                frac_tile = min(1.0, episode / max_eps_tile) if max_eps_tile > 0 else 0.0
                frac_overall = (tile_index + frac_tile) / total_tiles
                frac_overall = max(0.0, min(1.0, frac_overall))
            else:
                frac_overall = 0.0

            bar_w = self.panel_width - 30
            bar_h = 16
            bar_x = panel_x0 + 10
            bar_y = y

            pygame.draw.rect(
                self.screen, (80, 80, 80),
                (bar_x, bar_y, bar_w, bar_h), border_radius=6
            )
            fill_w = int(bar_w * frac_overall)
            pygame.draw.rect(
                self.screen, (255, 200, 40),
                (bar_x, bar_y, fill_w, bar_h), border_radius=6
            )

            y += 30
        else:
            step = getattr(env, "current_step", 0)
            max_steps = getattr(env, "current_max_steps", 0)
            total = getattr(env, "current_total_reward", 0)

            cheeses_all = list(getattr(env, "_cheeses", []))
            cheese_mask = getattr(env, "cheese_mask", 0)
            remaining = sum(
                1 for idx, _ in enumerate(cheeses_all) if (cheese_mask & (1 << idx))
            )

            self.screen.blit(
                self.small_font.render(f"Run steps: {step}/{max_steps}",
                                       True, (220, 220, 220)),
                (panel_x0 + 10, y),
            )
            y += 20
            self.screen.blit(
                self.small_font.render(f"Run reward: {total}",
                                       True, (220, 220, 220)),
                (panel_x0 + 10, y),
            )
            y += 20
            self.screen.blit(
                self.small_font.render(f"Cheese left: {remaining}",
                                       True, (220, 220, 220)),
                (panel_x0 + 10, y),
            )
            y += 25

        if in_training and not self.show_animation:
            info_y = self.grid_height - 180
            self.screen.blit(
                self.small_font.render("Skip mode: fast training", True, (255, 230, 120)),
                (panel_x0 + 10, info_y),
            )

        self.screen.blit(
            self.small_font.render("Use slider to control speed", True, (180, 180, 180)),
            (panel_x0 + 10, self.grid_height - 140),
        )
        self.screen.blit(
            self.small_font.render("Click SKIP to hide animation", True, (180, 180, 180)),
            (panel_x0 + 10, self.grid_height - 120),
        )

        self._draw_slider_and_button()

    def _draw_progress_only(self, env):
        self.screen.fill(COLORS["GRID"])
        grid_rect = pygame.Rect(0, 0, self.grid_width, self.grid_height)
        pygame.draw.rect(self.screen, COLORS["GRID"], grid_rect)
        self._draw_stats_panel(env)

    def draw(self, env, handle_events=True, fps=None):
        if getattr(env, "in_training", False) and not self.show_animation:
            self._draw_progress_only(env)
            self._draw_report_overlay()
            pygame.display.flip()
            self.clock.tick(self.fps_value)
            self.prev_cheese_mask = getattr(env, "cheese_mask", 0)
            self.prev_agent_pos = getattr(env, "agent_pos", None)
            return True

        if handle_events:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.close()
                    return False

                self._handle_slider_event(event)

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    if self.show_report_overlay:
                        self.show_report_overlay = False
                    continue

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos

                    if self.show_report_overlay and self.report_close_rect is not None:
                        if self.report_close_rect.collidepoint((mx, my)):
                            self.show_report_overlay = False
                            continue

                    if self.skip_button_rect.collidepoint((mx, my)):
                        self.show_animation = not self.show_animation

                    if (
                        self.report_button_rect is not None
                        and self.report_button_rect.collidepoint((mx, my))
                        and self.report_surface is not None
                        and getattr(env, "has_training_report", False)
                    ):
                        self.show_report_overlay = True

        self.screen.fill(COLORS["GRID"])

        traps = set(getattr(env, "_traps", []))
        cheeses_all = list(getattr(env, "_cheeses", []))
        cheese_mask = getattr(env, "cheese_mask", 0)
        home_pos = getattr(env, "home_pos", None)
        agent_pos = getattr(env, "agent_pos", None)

        just_ate_cheese = False
        just_hit_trap = False

        if self.prev_cheese_mask is not None and agent_pos is not None:
            for idx, pos in enumerate(cheeses_all):
                prev_has = (self.prev_cheese_mask & (1 << idx)) != 0
                now_has = (cheese_mask & (1 << idx)) != 0
                if prev_has and not now_has and agent_pos == pos:
                    just_ate_cheese = True
                    break

        if agent_pos is not None and self.prev_agent_pos is not None:
            if agent_pos in traps and agent_pos != self.prev_agent_pos:
                just_hit_trap = True

        for r in range(env.rows):
            for c in range(env.cols):
                rect = self._rect_at(r, c)
                cell = env.grid[r][c]

                if cell == '⬛':
                    base_idx = IDX_WALL
                else:
                    base_idx = IDX_FLOOR

                img = self.tile_images.get(base_idx)
                if img is not None:
                    self.screen.blit(img, rect)
                else:
                    color = COLORS["WALL"] if cell == '⬛' else COLORS["EMPTY"]
                    pygame.draw.rect(self.screen, color, rect, border_radius=8)

        active_cheeses = set()
        for idx, pos in enumerate(cheeses_all):
            if cheese_mask & (1 << idx):
                active_cheeses.add(pos)

        for tr, tc in traps:
            rect = self._rect_at(tr, tc)
            img = self.tile_images.get(IDX_TRAP)
            if img is not None:
                self.screen.blit(img, rect)
            else:
                pygame.draw.rect(self.screen, COLORS["TRAP"], rect, border_radius=6)

        for cr, cc in active_cheeses:
            rect = self._rect_at(cr, cc)
            img = self.tile_images.get(IDX_CHEESE)
            if img is not None:
                self.screen.blit(img, rect)
            else:
                pygame.draw.rect(self.screen, COLORS["TREAT"], rect, border_radius=10)

        if home_pos is not None:
            hr, hc = home_pos
            rect = self._rect_at(hr, hc)
            img = self.tile_images.get(IDX_HOME)
            if img is not None:
                self.screen.blit(img, rect)
            else:
                pygame.draw.rect(self.screen, COLORS["HOME"], rect, border_radius=8)

        if agent_pos is not None:
            ar, ac = agent_pos
            rect = self._rect_at(ar, ac)

            if just_ate_cheese:
                agent_idx = IDX_JERRY_ON_CHEESE
            elif just_hit_trap:
                agent_idx = IDX_JERRY_ON_TRAP
            else:
                agent_idx = IDX_JERRY

            img = self.tile_images.get(agent_idx)
            if img is not None:
                self.screen.blit(img, rect)
            else:
                center = (rect.x + rect.w // 2, rect.y + rect.h // 2)
                radius = int(rect.w * 0.35)
                pygame.draw.circle(self.screen, COLORS["AGENT"], center, radius)

        self._draw_stats_panel(env)
        self._draw_report_overlay()

        pygame.display.flip()

        if just_ate_cheese or just_hit_trap:
            pygame.time.delay(200)

        self.clock.tick(self.fps_value)

        self.prev_cheese_mask = cheese_mask
        self.prev_agent_pos = agent_pos

        return True
