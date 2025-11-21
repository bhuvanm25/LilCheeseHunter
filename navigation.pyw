import pygame
import sys

import main as game_main  
import map as map_menu    

APP_W, APP_H = 1200, 800


def navigation_screen() -> str:
    pygame.init()
    screen = pygame.display.set_mode((APP_W, APP_H))
    pygame.display.set_caption("TreatQuest — Launcher")

    font_title = pygame.font.SysFont("consolas", 60)
    font_sub   = pygame.font.SysFont("consolas", 26)
    font_btn   = pygame.font.SysFont("consolas", 32)

    clock = pygame.time.Clock()

    bg       = (20, 20, 30)
    btn_col  = (60, 120, 200)
    btn_hov  = (90, 150, 230)
    btn_text = (0, 0, 0)
    title_fg = (255, 255, 255)
    sub_fg   = (200, 200, 210)

    btn_w, btn_h = 320, 70
    cx = APP_W // 2
    start_y = APP_H // 2 - 40
    gap = 20

    play_rect = pygame.Rect(cx - btn_w // 2, start_y, btn_w, btn_h)
    map_rect  = pygame.Rect(cx - btn_w // 2, start_y + btn_h + gap, btn_w, btn_h)
    quit_rect = pygame.Rect(cx - btn_w // 2, start_y + 2 * (btn_h + gap), btn_w, btn_h)

    choice = "quit"
    running = True

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False

            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_ESCAPE, pygame.K_q):
                    choice = "quit"
                    running = False
                elif e.key in (pygame.K_p, pygame.K_RETURN):
                    choice = "play"
                    running = False
                elif e.key in (pygame.K_m,):
                    choice = "map"
                    running = False

            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                if play_rect.collidepoint(e.pos):
                    choice = "play"
                    running = False
                elif map_rect.collidepoint(e.pos):
                    choice = "map"
                    running = False
                elif quit_rect.collidepoint(e.pos):
                    choice = "quit"
                    running = False

        mx, my = pygame.mouse.get_pos()

        screen.fill(bg)

        title = font_title.render("TreatQuest", True, title_fg)
        sub   = font_sub.render("RL playground • Map editor • Viewer", True, sub_fg)
        screen.blit(title, (cx - title.get_width() // 2, 120))
        screen.blit(sub,   (cx - sub.get_width() // 2,   190))

        def draw_button(rect, label):
            hovered = rect.collidepoint(mx, my)
            col = btn_hov if hovered else btn_col
            pygame.draw.rect(screen, col, rect, border_radius=12)
            pygame.draw.rect(screen, (240, 240, 250), rect, 2, border_radius=12)
            txt = font_btn.render(label, True, btn_text)
            screen.blit(
                txt,
                (rect.centerx - txt.get_width() // 2,
                 rect.centery - txt.get_height() // 2),
            )

        draw_button(play_rect, "Play")
        draw_button(map_rect,  "Map Tools")
        draw_button(quit_rect, "Quit")

        pygame.display.flip()
        clock.tick(60)

    return choice


def main():
    while True:
        choice = navigation_screen()

        if choice == "play":
            game_main.main()

        elif choice == "map":
            map_menu.main()

        else: 
            break


if __name__ == "__main__":
    main()
