import pygame as pg

import editor
import viewer

APP_W, APP_H = 1200, 800

BG         = (22, 22, 26)
BTN_BASE   = (44, 48, 60)
BTN_HOVER  = (70, 90, 130)
BTN_TEXT   = (235, 235, 245)
BTN_BORDER = (95, 100, 120)
TEXT_SUB   = (210, 210, 220)


def map_menu_screen() -> str:
    pg.init()
    screen = pg.display.set_mode((APP_W, APP_H))
    pg.display.set_caption("TreatQuest — Map Tools")

    font_title = pg.font.SysFont("consolas", 32)
    font_btn   = pg.font.SysFont("consolas", 28)
    font_small = pg.font.SysFont("consolas", 20)

    clock = pg.time.Clock()

    pad_x = 60
    btn_w = APP_W - pad_x * 2
    btn_h = 70
    start_y = 180
    gap = 20

    btn_create = pg.Rect(pad_x, start_y, btn_w, btn_h)
    btn_view   = pg.Rect(pad_x, start_y + (btn_h + gap), btn_w, btn_h)
    btn_back   = pg.Rect(pad_x, start_y + 2 * (btn_h + gap), btn_w, btn_h)

    choice = "back"
    running = True

    while running:
        for e in pg.event.get():
            if e.type == pg.QUIT:
                choice = "back"
                running = False

            elif e.type == pg.KEYDOWN:
                if e.key in (pg.K_ESCAPE, pg.K_q):
                    choice = "back"
                    running = False
                elif e.key in (pg.K_c, pg.K_1):
                    choice = "editor"
                    running = False
                elif e.key in (pg.K_v, pg.K_2):
                    choice = "viewer"
                    running = False
                elif e.key in (pg.K_b, pg.K_3):
                    choice = "back"
                    running = False

            elif e.type == pg.MOUSEBUTTONDOWN and e.button == 1:
                if btn_create.collidepoint(e.pos):
                    choice = "editor"
                    running = False
                elif btn_view.collidepoint(e.pos):
                    choice = "viewer"
                    running = False
                elif btn_back.collidepoint(e.pos):
                    choice = "back"
                    running = False

        mx, my = pg.mouse.get_pos()
        screen.fill(BG)

        title = font_title.render("Map Tools", True, BTN_TEXT)
        screen.blit(title, (pad_x, 80))

        hint = font_small.render(
            "Create maps or view existing ones. Close windows to return here.",
            True,
            TEXT_SUB,
        )
        screen.blit(hint, (pad_x, 120))

        def draw_button(rect, label):
            hovered = rect.collidepoint(mx, my)
            col = BTN_HOVER if hovered else BTN_BASE
            pg.draw.rect(screen, col, rect, border_radius=10)
            pg.draw.rect(screen, BTN_BORDER, rect, 1, border_radius=10)

            txt = font_btn.render(label, True, BTN_TEXT)
            screen.blit(
                txt,
                (rect.x + 20, rect.y + rect.height // 2 - txt.get_height() // 2),
            )

        draw_button(btn_create, "Create Map  [C / 1]")
        draw_button(btn_view,   "View Map    [V / 2]")
        draw_button(btn_back,   "Back to Launcher  [Esc / B / 3]")

        pg.display.flip()
        clock.tick(60)

    return choice


def main():
    while True:
        choice = map_menu_screen()

        if choice == "editor":
            editor.main()

        elif choice == "viewer":
            viewer.run_picker_and_view()

        else: 
            break


if __name__ == "__main__":
    main()
