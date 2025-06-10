import pygame
import sys
import subprocess

pygame.init()

WIDTH, HEIGHT = 913, 408
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TarGuns - Menu")

font_title = pygame.font.SysFont(None, 100)
font_button = pygame.font.SysFont(None, 60)

WHITE = (255, 255, 255)
BLUE = (0, 115, 255)
BUTTON_COLOR = (50, 150, 255)
BUTTON_HOVER = (70, 170, 255)

clock = pygame.time.Clock()

# Button setup
button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2, 300, 70)

def draw_menu():
    screen.fill(BLUE)

    # Title
    title_text = font_title.render("TarGuns", True, WHITE)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
    screen.blit(title_text, title_rect)

    # Start button
    mouse_pos = pygame.mouse.get_pos()
    color = BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, button_rect)

    button_text = font_button.render("Start Game", True, WHITE)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)

    pygame.display.flip()

def run_menu():
    while True:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button_rect.collidepoint(event.pos):
                    # Launch main game
                    pygame.quit()
                    subprocess.run(["python", "TarGuns.py"])  # Change if filename is different
                    sys.exit()

        clock.tick(60)

if __name__ == "__main__":
    run_menu()
