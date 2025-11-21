import pygame
import subprocess
import sys


def run_main():
    subprocess.Popen([sys.executable, "main.py"])

def run_map_editor():
    subprocess.Popen([sys.executable, "map.py"])


def main():
    pygame.init()
    WIDTH, HEIGHT = 600, 400
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Navigation")

    font_title = pygame.font.SysFont(None, 64)
    font_btn = pygame.font.SysFont(None, 40)

    play_rect = pygame.Rect(WIDTH//2 - 100, 160, 200, 50)
    map_rect = pygame.Rect(WIDTH//2 - 100, 240, 200, 50)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_rect.collidepoint(event.pos):
                    run_main()
                if map_rect.collidepoint(event.pos):
                    run_map_editor()

        screen.fill((20, 20, 30))

        title = font_title.render("PROJECT NAME", True, (255, 255, 255))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))

        pygame.draw.rect(screen, (70, 170, 70), play_rect)
        play_txt = font_btn.render("Play", True, (0, 0, 0))
        screen.blit(play_txt, (play_rect.centerx - play_txt.get_width()//2,
                               play_rect.centery - play_txt.get_height()//2))

        pygame.draw.rect(screen, (70, 120, 200), map_rect)
        map_txt = font_btn.render("Map Editor", True, (0, 0, 0))
        screen.blit(map_txt, (map_rect.centerx - map_txt.get_width()//2,
                              map_rect.centery - map_txt.get_height()//2))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
