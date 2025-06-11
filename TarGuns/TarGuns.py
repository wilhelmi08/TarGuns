import pygame
import time
import random
import sys
import json
import os


pygame.init()

def save_game(credits=None, volume=None):
    data = {}
    if os.path.exists("save_data.json"):
        with open("save_data.json", "r") as f:
            data = json.load(f)

    if score is not None:
        data["credits"] = int(credits)
    if volume is not None:
        data["volume"] = float(volume)

    with open("save_data.json", "w") as f:
        json.dump(data, f)

def load_game():
    if os.path.exists("save_data.json"):
        with open("save_data.json", "r") as f:
            data = json.load(f)
            return data.get("credits", 0), data.get("volume", 1.0)
    return 0, 1.0

credits, volume = load_game()

# Screen setup
WIDTH, HEIGHT = 913, 408
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TarGuns")
clock = pygame.time.Clock()

# Fonts
font_large = pygame.font.SysFont(None, 100)
font_small = pygame.font.SysFont(None, 40)
font_button = pygame.font.SysFont(None, 60)

# Colors
WHITE = (255, 255, 255)
BLUE = (0, 115, 255)
TEXT_COLOR = (200, 200, 200)
BUTTON_COLOR = (50, 150, 255)
BUTTON_HOVER = (70, 170, 255)

# Load sound
pistol_sound = pygame.mixer.Sound("pistol.mp3")
empty_sound = pygame.mixer.Sound("emptyPistol.mp3")

# Box properties
BOX_WIDTH, BOX_HEIGHT = 100, 100
BOX_SPEED = 15  # Increased speed

# Load and scale image
image = pygame.image.load("target.png").convert_alpha()
image = pygame.transform.scale(image, (BOX_WIDTH, BOX_HEIGHT))

# Countdown before game start
countdown_duration = 5
start_time = time.time()
game_started = False

# Player
player_health = 100
MAX_HEALTH = 100
damage_per_missed_target = 10

# Load gun sprite sheet
gun_sprite_sheet = pygame.image.load("pistolAnimation.png").convert_alpha()
frame_width = 150
frame_height = 100
num_frames = 2  # number of frames in the sheet
gun_fire_frames = []
for i in range(num_frames):
    rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
    frame = gun_sprite_sheet.subsurface(rect)
    gun_fire_frames.append(frame)

gun_state = "idle"
gun_frame_time = 0
gun_x = WIDTH // 2 - frame_width // 2
gun_y = HEIGHT - frame_height

# Ammo & Reload
AMMO_MAX = 17
ammo = AMMO_MAX
reloading = False
reload_start_time = None
reload_duration = 3  # seconds

# Wave & Score System
wave = 1
points_per_target = 1
bonus_per_wave = 10

if credits == None:
    credits = 0  # Initialize score if not loaded

wave_in_progress = False
between_waves = False
between_waves_start = None
between_waves_duration = 5  # seconds
mini_waves_per_wave = 3  # number of mini waves (batches) per wave
mini_waves_spawned = 0   # how many batches spawned so far

batch_size = 3  # number of targets per batch (initially)
batch_delay = 5  # seconds between batches (initially)

next_batch_time = None
targets_spawned = 0
total_targets_in_wave = 0

base_target_timeout = 10  # seconds before target disappears

# Targets
active_targets = []

def spawn_box(existing_rects):
    max_attempts = 50
    for _ in range(max_attempts):
        start_x = random.randint(50, WIDTH - BOX_WIDTH - 50)
        new_rect = pygame.Rect(start_x, HEIGHT, BOX_WIDTH, BOX_HEIGHT)

        # Check for overlap with existing targets
        if all(not new_rect.colliderect(existing) for existing in existing_rects):
            return {
                "rect": new_rect,
                "target_y": random.uniform(300, 0),
                "speed": BOX_SPEED,
                "image": image,
                "at_target_time": None
            }
    return None  # if we failed to find a good spot

def start_wave(wave_num):
    global active_targets, wave_in_progress, batch_size, batch_delay, next_batch_time
    global mini_waves_spawned, mini_waves_per_wave, total_targets_in_wave

    mini_waves_per_wave = 3 + (wave_num - 1)  # increase mini waves per wave if you want
    mini_waves_spawned = 0

    batch_size = min(3 + (wave_num // 2), 6)
    batch_delay = max(2.5, 6 - (wave_num * 0.5))

    total_targets_in_wave = mini_waves_per_wave * batch_size

    active_targets = []
    wave_in_progress = True
    next_batch_time = time.time()  # spawn first batch immediately
    targets_spawned = 0

def draw_menu():
    screen.fill(BLUE)

    # Title
    title_text = font_large.render("TarGuns", True, WHITE)
    title_rect = title_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
    screen.blit(title_text, title_rect)

    # Start button
    mouse_pos = pygame.mouse.get_pos()
    button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2, 300, 70)
    color = BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, button_rect)

    button_text = font_button.render("PLAY", True, WHITE)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)

    # Settings button
    settings_text = font_small.render("Settings", True, TEXT_COLOR)
    settings_rect = settings_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
    screen.blit(settings_text, settings_rect)
    pygame.draw.rect(screen, BUTTON_COLOR, settings_rect.inflate(20, 10), border_radius=5)
    pygame.draw.rect(screen, BUTTON_HOVER if settings_rect.collidepoint(mouse_pos) else BUTTON_COLOR, settings_rect.inflate(20, 10), 2)
    screen.blit(settings_text, settings_rect)

    pygame.display.flip()

def show_menu():
    while True:
        draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2, 300, 70)
                settings_rect = pygame.font.SysFont(None, 40).render("Settings", True, (200, 200, 200)).get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
                settings_rect = settings_rect.inflate(20, 10)
                if button_rect.collidepoint(event.pos):
                    return "start"
                elif settings_rect.collidepoint(event.pos):
                    return "settings"
        clock.tick(60)

if volume == None:
    volume = 1.0  # Default volume if not loaded

def show_settings():
    global volume
    dragging = False
    slider_x = WIDTH // 2 - 150
    slider_y = HEIGHT // 2
    slider_width = 300
    slider_height = 8
    knob_radius = 15

    def get_knob_pos():
        return int(slider_x + volume * slider_width)

    while True:
        screen.fill(BLUE)
        settings_title = font_large.render("Settings", True, WHITE)
        screen.blit(settings_title, (WIDTH // 2 - settings_title.get_width() // 2, HEIGHT // 2 - 120))

        # Volume label
        volume_label = font_small.render("Audio Volume", True, TEXT_COLOR)
        screen.blit(volume_label, (slider_x, slider_y - 40))

        # Draw slider bar
        pygame.draw.rect(screen, (180, 180, 180), (slider_x, slider_y, slider_width, slider_height), border_radius=4)
        # Draw knob
        knob_pos = get_knob_pos()
        pygame.draw.circle(screen, BUTTON_COLOR, (knob_pos, slider_y + slider_height // 2), knob_radius)
        # Draw volume percent
        percent_text = font_small.render(f"{int(volume * 100)}%", True, TEXT_COLOR)
        screen.blit(percent_text, (slider_x + slider_width + 20, slider_y - 15))

        # Back button (upper left)
        back_rect = pygame.Rect(20, 20, 100, 40)
        pygame.draw.rect(screen, BUTTON_COLOR, back_rect, border_radius=8)
        back_text = font_small.render("Back", True, WHITE)
        back_text_rect = back_text.get_rect(center=back_rect.center)
        screen.blit(back_text, back_text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                # Check back button
                if back_rect.collidepoint(mx, my):
                    save_game(volume=volume)
                    return
                # Check knob drag
                if (mx - knob_pos) ** 2 + (my - (slider_y + slider_height // 2)) ** 2 <= knob_radius ** 2:
                    dragging = True
                # Click on slider bar
                elif slider_x <= mx <= slider_x + slider_width and slider_y - 10 <= my <= slider_y + slider_height + 10:
                    volume = (mx - slider_x) / slider_width
                    volume = max(0.0, min(1.0, volume))
                    pistol_sound.set_volume(volume)
                    empty_sound.set_volume(volume)
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging:
                mx, my = event.pos
                volume = (mx - slider_x) / slider_width
                volume = max(0.0, min(1.0, volume))
                pistol_sound.set_volume(volume)
                empty_sound.set_volume(volume)

        clock.tick(60)

# Set initial volume for sounds
pistol_sound.set_volume(volume)
empty_sound.set_volume(volume)

game_over = False
game_over_start = None  # Track when game over started

running = True
while running:
    menu_choice = show_menu()

    if menu_choice == "start":
        # Initialize game state
        credits, volume = load_game()
        game_started = False
        game_over = False
        game_over_start = None
        start_time = time.time()
        player_health = 100
        ammo = AMMO_MAX
        reloading = False
        wave = 1
        score = 0

        # Set volume for sounds after loading
        pistol_sound.set_volume(volume)
        empty_sound.set_volume(volume)

        # Start the game
        while not game_over:
            screen.fill(BLUE)
            now = time.time()
            elapsed = now - start_time

            # Game start countdown
            if not game_started:
                remaining = max(0, countdown_duration - int(elapsed))
                countdown_text = font_large.render(str(remaining), True, TEXT_COLOR)
                screen.blit(countdown_text, (WIDTH // 2 - 25, HEIGHT // 2 - 50))

                if elapsed >= countdown_duration:
                    game_started = True
                    start_wave(wave)
            else:
                if game_over:
                    if game_over_start is None:
                        game_over_start = now  # mark when game over began

                    # Show game over text
                    screen.fill(BLUE)
                    game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
                    screen.blit(game_over_text, (WIDTH // 2 - 150, HEIGHT // 2 - 50))

                    # After 5 seconds, return to menu
                    if now - game_over_start >= 5:
                        break

                else:
                    # Reload handling
                    if reloading and (now - reload_start_time) >= reload_duration:
                        ammo = AMMO_MAX
                        reloading = False

                    if wave_in_progress:
                        # Spawn batches if needed
                        if next_batch_time and now >= next_batch_time and mini_waves_spawned < mini_waves_per_wave:
                            existing_rects = [t["rect"] for t in active_targets]
                            spawn_count = batch_size
                            for _ in range(spawn_count):
                                box = spawn_box(existing_rects)
                                if box:
                                    active_targets.append(box)
                                    existing_rects.append(box["rect"])

                            mini_waves_spawned += 1
                            next_batch_time = now + batch_delay
                        elif mini_waves_spawned >= mini_waves_per_wave:
                            next_batch_time = None

                        # Update targets
                        for target in active_targets[:]:
                            rect = target["rect"]
                            if rect.y > target["target_y"]:
                                rect.y -= target["speed"]
                                if rect.y < target["target_y"]:
                                    rect.y = target["target_y"]
                                    target["at_target_time"] = now
                            else:
                                timeout = base_target_timeout + wave * 0.5  # Increase timeout a bit each wave
                                if target["at_target_time"] and (time.time() - target["at_target_time"]) >= timeout:
                                    active_targets.remove(target)
                                    player_health -= damage_per_missed_target
                                    if player_health <= 0:
                                        credits += int(score)
                                        save_game(credits=credits, volume=volume)
                                        game_over = True

                            screen.blit(target["image"], rect)

                        # Check wave completion
                        if mini_waves_spawned == mini_waves_per_wave and len(active_targets) == 0:
                            wave_in_progress = False
                            between_waves = True
                            between_waves_start = now
                            score += bonus_per_wave
                            points_per_target *= 1.5
                            player_health = min(MAX_HEALTH, player_health + 30)
                            wave += 1

                    # Between waves countdown
                    if between_waves:
                        seconds_left = between_waves_duration - (now - between_waves_start)
                        if seconds_left <= 0:
                            between_waves = False
                            start_wave(wave)
                        else:
                            countdown_text = font_large.render(f"Next wave in {int(seconds_left) + 1}", True, TEXT_COLOR)
                            text_rect = countdown_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
                            screen.blit(countdown_text, text_rect)

                    # Draw player health FIRST
                    health_bar_width = 200
                    health_bar_height = 20
                    health_bar_x = 10
                    health_bar_y = 10

                    pygame.draw.rect(screen, (180, 0, 0), (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
                    current_width = int((player_health / MAX_HEALTH) * health_bar_width)
                    pygame.draw.rect(screen, (0, 255, 0), (health_bar_x, health_bar_y, current_width, health_bar_height))

                    # Ammo, score, wave below health bar
                    ammo_text = font_small.render(f"Ammo: {ammo}/{AMMO_MAX}", True, TEXT_COLOR)
                    screen.blit(ammo_text, (10, health_bar_y + health_bar_height + 10))

                    score_text = font_small.render(f"Score: {int(score)}", True, TEXT_COLOR)
                    screen.blit(score_text, (10, health_bar_y + health_bar_height + 40))

                    wave_text = font_small.render(f"Wave: {wave}", True, TEXT_COLOR)
                    screen.blit(wave_text, (10, health_bar_y + health_bar_height + 70))

                    # Reload text
                    if reloading:
                        reload_text = font_small.render("Reloading...", True, TEXT_COLOR)
                        screen.blit(reload_text, (10, health_bar_y + health_bar_height + 100))

                    # Gun animation
                    if gun_state == "firing":
                        screen.blit(gun_fire_frames[1], (gun_x, gun_y))
                        if now - gun_frame_time > 0.1:
                            gun_state = "idle"
                    else:
                        screen.blit(gun_fire_frames[0], (gun_x, gun_y))

                    # Quit button (top right)
                    quit_button_rect = pygame.Rect(WIDTH - 130, 10, 120, 40)
                    pygame.draw.rect(screen, BUTTON_COLOR, quit_button_rect, border_radius=8)
                    quit_text = font_small.render("Quit", True, WHITE)
                    quit_text_rect = quit_text.get_rect(center=quit_button_rect.center)
                    screen.blit(quit_text, quit_text_rect)

            # Event handling: only accept input if NOT game over
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if quit_button_rect.collidepoint(event.pos):
                        credits += int(score)
                        save_game(credits=credits, volume=volume)
                        game_over = True
                        break

                if not game_over and event.type == pygame.MOUSEBUTTONDOWN and game_started:
                    if not reloading and ammo > 0 and wave_in_progress:
                        pistol_sound.play()
                        gun_state = "firing"
                        gun_frame_time = now

                        pos = pygame.mouse.get_pos()
                        for target in active_targets[:]:
                            if target["rect"].collidepoint(pos):
                                active_targets.remove(target)
                                score += points_per_target
                                break

                        ammo -= 1
                        if ammo <= 0:
                            reloading = True
                            reload_start_time = now
                    elif reloading:
                        empty_sound.play()

            pygame.display.update()
            clock.tick(60)
    elif menu_choice == "settings":
        show_settings()

pygame.quit()
