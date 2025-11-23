import pygame
import sys

import main as game_main  
import map as map_menu    

APP_W, APP_H = 1200, 800

def round_image(surface, radius):
    width, height = surface.get_size()

    # Create a mask with rounded corners
    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255),
                     (0, 0, width, height), border_radius=radius)

    # Apply mask to the image
    rounded = pygame.Surface((width, height), pygame.SRCALPHA)
    rounded.blit(surface, (0, 0))
    rounded.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    return rounded



def navigation_screen() -> str:
    pygame.init()
    screen = pygame.display.set_mode((APP_W, APP_H))
    pygame.display.set_caption("Lil Cheese Hunter™")

    font_title   = pygame.font.SysFont("consolas", 60)
    font_sub     = pygame.font.SysFont("consolas", 26)
    font_btn     = pygame.font.SysFont("consolas", 32)
    font_credits = pygame.font.SysFont("consolas", 22)

    clock = pygame.time.Clock()

    btn_col  = (60, 120, 200)
    btn_hov  = (90, 150, 230)
    btn_text = (252, 238, 167)
    title_fg = (0, 0, 0)
    sub_fg   = (0, 0, 0)

    btn_w, btn_h = 320, 70
    cx = APP_W // 2
    start_y = APP_H // 2 - 40
    gap = 20

    play_rect = pygame.Rect(cx - btn_w // 2, start_y, btn_w, btn_h)
    map_rect  = pygame.Rect(cx - btn_w // 2, start_y + btn_h + gap, btn_w, btn_h)
    quit_rect = pygame.Rect(cx - btn_w // 2, start_y + 2 * (btn_h + gap), btn_w, btn_h)

        # Load logos
    chinchilla_logo = pygame.image.load("logos/chinchilla.png").convert_alpha()
    proto_raw  = pygame.image.load("logos/proto.png").convert_alpha()
    proto_logo = round_image(proto_raw, radius=40)

    # Load background
    bg_raw = pygame.image.load("logos/navbg.png").convert()
    background = pygame.transform.smoothscale(bg_raw, (APP_W, APP_H))
    
    logo_margin = 20

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

        screen.blit(background, (0, 0))

        # Title + subtitle
        title = font_title.render("Lil Cheese Hunter™", True, title_fg)
        sub   = font_sub.render("A Prototyp3 project • Developed by Team Chinchillas", True, sub_fg)
        screen.blit(title, (cx - title.get_width() // 2, 120))
        screen.blit(sub,   (cx - sub.get_width() // 2,   190))

        # Logos
        screen.blit(proto_logo, (logo_margin, logo_margin))  # top-left
        screen.blit(
            chinchilla_logo,
            (APP_W - chinchilla_logo.get_width() - logo_margin, logo_margin),  # top-right
        )

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

        draw_button(play_rect, "Playground")
        draw_button(map_rect,  "Map Tools")
        draw_button(quit_rect, "Quit")

        # Credits at bottom under buttons
        credits_lines = [
            "--- The Chinchillas ---",
            "Bhuvan | Joseph",
            "Noiva | Tasha",
        ]

        base_y = quit_rect.bottom + 60
        for i, line in enumerate(credits_lines):
            txt = font_credits.render(line, True, sub_fg)
            screen.blit(
                txt,
                (cx - txt.get_width() // 2,
                 base_y + i * (txt.get_height() + 4)),
            )

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
