import pygame
import time
import random
import sys
import json
import os


pygame.init()

def save_game(credits=None, music_volume=None, sfx_volume=None):
    data = {}
    if os.path.exists("save_data.json"):
        with open("save_data.json", "r") as f:
            data = json.load(f)
    if credits is not None:
        data["credits"] = int(credits)
    if music_volume is not None:
        data["music_volume"] = float(music_volume)
    if sfx_volume is not None:
        data["sfx_volume"] = float(sfx_volume)
    with open("save_data.json", "w") as f:
        json.dump(data, f)

def load_game():
    if os.path.exists("save_data.json"):
        with open("save_data.json", "r") as f:
            data = json.load(f)
            return (
                data.get("credits", 0),
                data.get("music_volume", 1.0),
                data.get("sfx_volume", 1.0),
            )
    return 0, 1.0, 1.0

credits, music_volume, sfx_volume = load_game()

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
store_entrance_sound = pygame.mixer.Sound("storeEntrance.mp3")
store_exit_sound = pygame.mixer.Sound("storeExit.mp3")

# Load store music
STORE_MUSIC_PATH = "storeMusic.mp3"
MENU_MUSIC_PATH = "menuMusic.mp3"
import random

# List all your game music tracks
GAME_MUSIC_TRACKS = [
    "track01.mp3",
    "track02.mp3",
    "track03.mp3",
    # Add more as needed
]

# Shuffle at the start of the game
random.shuffle(GAME_MUSIC_TRACKS)
current_track_index = 0

def play_next_game_track(volume):
    global current_track_index
    pygame.mixer.music.load(GAME_MUSIC_TRACKS[current_track_index])
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play()
    current_track_index = (current_track_index + 1) % len(GAME_MUSIC_TRACKS)

pygame.mixer.set_num_channels(12)  # Ensure at least 11 channels are available
GUNSHOT_CHANNELS = [pygame.mixer.Channel(i) for i in range(2, 12)]  # Reserve channels 2-10 for gunshots
gunshot_channel_idx = 0

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
gun_sprite_sheet = pygame.image.load("newPistolAnimation.png").convert_alpha()
frame_width = 300
frame_height = 200
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

def play_next_game_track(volume):
    global current_track_index
    pygame.mixer.music.load(GAME_MUSIC_TRACKS[current_track_index])
    pygame.mixer.music.set_volume(music_volume)
    pygame.mixer.music.play()
    current_track_index = (current_track_index + 1) % len(GAME_MUSIC_TRACKS)

def show_quit_confirmation():
    dialog_width, dialog_height = 400, 200
    dialog_x = WIDTH // 2 - dialog_width // 2
    dialog_y = HEIGHT // 2 - dialog_height // 2
    yes_rect = pygame.Rect(dialog_x + 60, dialog_y + 120, 100, 50)
    no_rect = pygame.Rect(dialog_x + 240, dialog_y + 120, 100, 50)

    while True:
        # Do NOT draw a semi-transparent overlay here!
        # Just draw the dialog box and its contents

        # Draw dialog box
        pygame.draw.rect(screen, (30, 30, 30), (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=12)
        pygame.draw.rect(screen, (200, 200, 200), (dialog_x, dialog_y, dialog_width, dialog_height), 3, border_radius=12)

        # Draw text (render each line separately)
        lines = ["Are you sure you want to", "          quit to menu?"]
        for i, line in enumerate(lines):
            msg = font_small.render(line, True, WHITE)
            screen.blit(msg, (dialog_x + 30, dialog_y + 40 + i * (font_small.get_height() + 5)))

        # Draw buttons
        pygame.draw.rect(screen, BUTTON_COLOR, yes_rect, border_radius=8)
        pygame.draw.rect(screen, BUTTON_COLOR, no_rect, border_radius=8)
        yes_text = font_small.render("Yes", True, WHITE)
        no_text = font_small.render("No", True, WHITE)
        screen.blit(yes_text, yes_rect.move((yes_rect.width - yes_text.get_width()) // 2, (yes_rect.height - yes_text.get_height()) // 2))
        screen.blit(no_text, no_rect.move((no_rect.width - no_text.get_width()) // 2, (no_rect.height - no_text.get_height()) // 2))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if yes_rect.collidepoint(event.pos):
                    return True
                elif no_rect.collidepoint(event.pos):
                    return False

def spawn_box(existing_rects):
    max_attempts = 50
    for _ in range(max_attempts):
        start_x = random.randint(50, WIDTH - BOX_WIDTH - 50)
        new_rect = pygame.Rect(start_x, HEIGHT, BOX_WIDTH, BOX_HEIGHT)

        # Check for overlap with existing targets
        if all(not new_rect.colliderect(existing) for existing in existing_rects):
            return {
                "rect": new_rect,
                "target_y": random.uniform(250, 50),
                "speed": BOX_SPEED,
                "image": image,
                "at_target_time": None
            }
    return None  # if we failed to find a good spot

def start_wave(wave_num):
    global active_targets, wave_in_progress, batch_size, batch_delay, next_batch_time
    global mini_waves_spawned, mini_waves_per_wave, total_targets_in_wave

    if wave_num <= 10:
        mini_waves_per_wave = 2 + wave_num  # Wave 1: 3, Wave 2: 4, ..., Wave 10: 12
        batch_size = min(3 + (wave_num // 2), 6)
        batch_delay = max(2.5, 6 - (wave_num * 0.5))
    else:
        # Intensify after 10th wave
        mini_waves_per_wave = 12 + (wave_num - 10) * 2  # Grows faster after wave 10
        batch_size = min(6 + (wave_num - 10) // 2, 12)
        batch_delay = max(0.7, 2.5 - (wave_num - 10) * 0.15)

    total_targets_in_wave = mini_waves_per_wave * batch_size

    active_targets = []
    wave_in_progress = True
    next_batch_time = time.time()
    mini_waves_spawned = 0

def draw_menu():
    screen.fill(BLUE)

    # Logo (scaled to 0.3 of its original size)
    logo_img = pygame.image.load("TarGunsLogo.png").convert_alpha()
    logo_width, logo_height = logo_img.get_size()
    scale_factor = 0.27
    scaled_width = int(logo_width * scale_factor)
    scaled_height = int(logo_height * scale_factor)
    logo_img = pygame.transform.smoothscale(logo_img, (scaled_width, scaled_height))
    logo_rect = logo_img.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
    screen.blit(logo_img, logo_rect)

    # Start button
    mouse_pos = pygame.mouse.get_pos()
    button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2 + 40, 300, 70)
    color = BUTTON_HOVER if button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(screen, color, button_rect)

    button_text = font_button.render("PLAY", True, WHITE)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)

    settings_text = font_small.render("Settings", True, TEXT_COLOR)
    settings_rect = settings_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 140))
    inflated_settings_rect = settings_rect.inflate(20, 10)
    pygame.draw.rect(screen, BUTTON_COLOR, inflated_settings_rect, border_radius=5)
    pygame.draw.rect(screen, BUTTON_HOVER if inflated_settings_rect.collidepoint(mouse_pos) else BUTTON_COLOR, inflated_settings_rect, 2)
    screen.blit(settings_text, settings_rect)

    store_icon = pygame.image.load("storeIcon.png").convert_alpha()
    store_icon = pygame.transform.scale(store_icon, (100, 100))
    store_rect = store_icon.get_rect(bottomright=(WIDTH - 5, HEIGHT - 300))
    screen.blit(store_icon, store_rect)

    # Darken effect on hover or press (only icon, not background)
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]
    if store_rect.collidepoint(mouse_pos):
        darken = pygame.Surface((store_rect.width, store_rect.height), pygame.SRCALPHA)
        alpha = 80 if mouse_pressed else 40  # More dark when pressed
        darken.fill((0, 0, 0, alpha))
        # Use BLEND_RGBA_MULT to only darken non-transparent pixels
        store_icon_darken = store_icon.copy()
        store_icon_darken.blit(darken, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(store_icon_darken, store_rect.topleft)
    
    # Quit button (lower left)
    quit_rect = pygame.Rect(20, HEIGHT - 60, 120, 40)
    button_surf = pygame.Surface((quit_rect.width, quit_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(button_surf, BUTTON_COLOR, button_surf.get_rect(), border_radius=8)
    quit_text = font_small.render("Quit", True, WHITE)
    quit_text_rect = quit_text.get_rect(center=button_surf.get_rect().center)
    button_surf.blit(quit_text, quit_text_rect)
    mouse_pos = pygame.mouse.get_pos()
    mouse_pressed = pygame.mouse.get_pressed()[0]
    if quit_rect.collidepoint(mouse_pos):
        darken = pygame.Surface((quit_rect.width, quit_rect.height), pygame.SRCALPHA)
        alpha = 80 if mouse_pressed else 40
        darken.fill((0, 0, 0, alpha))
        button_surf.blit(darken, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # Blit the text again so it stays visible
        button_surf.blit(quit_text, quit_text_rect)
    screen.blit(button_surf, quit_rect.topleft)

    pygame.display.flip()
    return store_rect, quit_rect, inflated_settings_rect

def show_menu():
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load(MENU_MUSIC_PATH)
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)
            

    while True:
        store_rect, quit_rect, settings_rect = draw_menu()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT // 2, 300, 70)
                if button_rect.collidepoint(event.pos):
                    pygame.mixer.music.stop()
                    return "start"
                elif settings_rect.collidepoint(event.pos):
                    return "settings"
                elif store_rect.collidepoint(event.pos):
                    store_entrance_sound.play()
                    store_entrance_sound.set_volume(sfx_volume)
                    pygame.mixer.music.stop()
                    return "store"
                elif quit_rect.collidepoint(event.pos):
                    if show_quit_confirmation():
                        pygame.quit()
                        sys.exit()
        clock.tick(60)

def show_store():
    # Play store music only if not already playing
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load(STORE_MUSIC_PATH)
        pygame.mixer.music.set_volume(music_volume)
        pygame.mixer.music.play(-1)

    global credits
    # Load equipped weapon from save_data.json
    equipped = "pistol"
    if os.path.exists("save_data.json"):
        with open("save_data.json", "r") as f:
            data = json.load(f)
            equipped = data.get("equipped", "pistol")
            owned_items = set(data.get("owned_items", ["pistol"]))
    else:
        owned_items = {"pistol"}

    def save_ownership():
        # Save credits, owned items, and equipped weapon to save_data.json
        if os.path.exists("save_data.json"):
            with open("save_data.json", "r") as f:
                data = json.load(f)
        else:
            data = {}
        data["credits"] = int(credits)
        data["owned_items"] = list(owned_items)
        data["equipped"] = equipped
        with open("save_data.json", "w") as f:
            json.dump(data, f)

    def show_purchase_dialog(item):
        dialog_width, dialog_height = 420, 210
        dialog_x = WIDTH // 2 - dialog_width // 2
        dialog_y = HEIGHT // 2 - dialog_height // 2
        yes_rect = pygame.Rect(dialog_x + 60, dialog_y + 120, 100, 50)
        no_rect = pygame.Rect(dialog_x + 260, dialog_y + 120, 100, 50)
        while True:
            pygame.draw.rect(screen, (30, 30, 30), (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=12)
            pygame.draw.rect(screen, (200, 200, 200), (dialog_x, dialog_y, dialog_width, dialog_height), 3, border_radius=12)
            msg1 = font_small.render("Are you sure you want to buy", True, WHITE)
            msg2 = font_small.render(f"{item['name']} for {item['price']} credits?", True, WHITE)
            screen.blit(msg1, (dialog_x + 30, dialog_y + 40))
            screen.blit(msg2, (dialog_x + 30, dialog_y + 40 + font_small.get_height() + 5))
            pygame.draw.rect(screen, BUTTON_COLOR, yes_rect, border_radius=8)
            pygame.draw.rect(screen, BUTTON_COLOR, no_rect, border_radius=8)
            yes_text = font_small.render("Yes", True, WHITE)
            no_text = font_small.render("No", True, WHITE)
            screen.blit(yes_text, yes_rect.move((yes_rect.width - yes_text.get_width()) // 2, (yes_rect.height - yes_text.get_height()) // 2))
            screen.blit(no_text, no_rect.move((no_rect.width - no_text.get_width()) // 2, (no_rect.height - no_text.get_height()) // 2))
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if yes_rect.collidepoint(event.pos):
                        return True
                    elif no_rect.collidepoint(event.pos):
                        return False

    while True:
        screen.fill(BLUE)
        title = font_large.render("STORE", True, WHITE)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 40))

        # Show credits in upper right
        credits_text = font_small.render(f"Credits: {credits}", True, TEXT_COLOR)
        credits_x = WIDTH - credits_text.get_width() - 20
        credits_y = 20
        screen.blit(credits_text, (credits_x, credits_y))

        back_rect = pygame.Rect(20, 20, 100, 40)
        button_surf = pygame.Surface((back_rect.width, back_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(button_surf, BUTTON_COLOR, button_surf.get_rect(), border_radius=8)
        back_text = font_small.render("Back", True, WHITE)
        back_text_rect = back_text.get_rect(center=button_surf.get_rect().center)
        button_surf.blit(back_text, back_text_rect)
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if back_rect.collidepoint(mouse_pos):
            darken = pygame.Surface((back_rect.width, back_rect.height), pygame.SRCALPHA)
            alpha = 80 if mouse_pressed else 40
            darken.fill((0, 0, 0, alpha))
            button_surf.blit(darken, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            button_surf.blit(back_text, back_text_rect)
        screen.blit(button_surf, back_rect.topleft)

        # Store items data
        items = [
            {
                "id": "pistol",
                "name": "Pistol",
                "icon": "pistol.png",
                "price": 0,
                "desc": "Standard sidearm.",
                "owned": "pistol" in owned_items
            },
            {
                "id": "ak",
                "name": "Assault Rifle",
                "icon": "ak.png",
                "price": 2000,
                "desc": "Automatic rifle.",
                "owned": "ak" in owned_items
            }
        ]

        item_box_width = 300
        item_box_height = 250
        spacing = 40
        total_width = len(items) * item_box_width + (len(items) - 1) * spacing
        start_x = WIDTH // 2 - total_width // 2
        item_box_y = HEIGHT // 2 - item_box_height // 2 + 50

        item_boxes = []
        for idx, item in enumerate(items):
            box_x = start_x + idx * (item_box_width + spacing)
            box_rect = pygame.Rect(box_x, item_box_y, item_box_width, item_box_height)
            item_boxes.append((box_rect, item))
            pygame.draw.rect(screen, (30, 30, 30), box_rect, border_radius=12)
            pygame.draw.rect(screen, (200, 200, 200), box_rect, 3, border_radius=12)

            item_icon = pygame.image.load(item["icon"]).convert_alpha()
            native_width, native_height = item_icon.get_size()
            scale_factor = 0.2
            scaled_width = int(native_width * scale_factor)
            scaled_height = int(native_height * scale_factor)
            item_icon_scaled = pygame.transform.smoothscale(item_icon, (scaled_width, scaled_height))
            item_icon_rect = item_icon_scaled.get_rect(center=(box_x + item_box_width // 2, item_box_y + 80))
            screen.blit(item_icon_scaled, item_icon_rect)

            item_text = font_small.render(item["name"], True, WHITE)
            item_text_rect = item_text.get_rect(center=(box_x + item_box_width // 2, item_icon_rect.bottom + 40))
            screen.blit(item_text, item_text_rect)

            # Draw price/equipped/owned
            if equipped == item["id"]:
                price_text = font_small.render("Equipped", True, (75, 255, 50))
            elif item["owned"]:
                price_text = font_small.render("Owned", True, (200, 200, 200))
            elif item["price"] > 0:
                price_text = font_small.render(f"Price: {item['price']} Credits", True, TEXT_COLOR)
            else:
                price_text = font_small.render("Free", True, TEXT_COLOR)
            price_text_rect = price_text.get_rect(center=(box_x + item_box_width // 2, item_text_rect.bottom + 20))
            screen.blit(price_text, price_text_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    save_ownership()
                    store_exit_sound.set_volume(sfx_volume)
                    store_exit_sound.play()
                    pygame.mixer.music.stop()  # Stop music when leaving store
                    return
                # Check if any item box is clicked
                for box_rect, item in item_boxes:
                    if box_rect.collidepoint(event.pos):
                        if equipped == item["id"]:
                            show_upgrade_screen(equipped, owned_items)
                        elif not item["owned"]:
                            if show_purchase_dialog(item):
                                if credits >= item["price"]:
                                    credits -= item["price"]
                                    owned_items.add(item["id"])
                                    save_ownership()
                                else:
                                    # ...existing not enough credits dialog...
                                    dialog_width, dialog_height = 350, 120
                                    dialog_x = WIDTH // 2 - dialog_width // 2
                                    dialog_y = HEIGHT // 2 - dialog_height // 2
                                    ok_rect = pygame.Rect(dialog_x + dialog_width // 2 - 50, dialog_y + 60, 100, 40)
                                    while True:
                                        pygame.draw.rect(screen, (30, 30, 30), (dialog_x, dialog_y, dialog_width, dialog_height), border_radius=12)
                                        pygame.draw.rect(screen, (200, 200, 200), (dialog_x, dialog_y, dialog_width, dialog_height), 3, border_radius=12)
                                        msg = font_small.render("Not enough credits!", True, (255, 80, 80))
                                        screen.blit(msg, (dialog_x + 30, dialog_y + 30))
                                        pygame.draw.rect(screen, BUTTON_COLOR, ok_rect, border_radius=8)
                                        ok_text = font_small.render("OK", True, WHITE)
                                        screen.blit(ok_text, ok_rect.move((ok_rect.width - ok_text.get_width()) // 2, (ok_rect.height - ok_text.get_height()) // 2))
                                        pygame.display.update()
                                        for e in pygame.event.get():
                                            if e.type == pygame.QUIT:
                                                pygame.quit()
                                                sys.exit()
                                            elif e.type == pygame.MOUSEBUTTONDOWN:
                                                if ok_rect.collidepoint(e.pos):
                                                    break
                                        else:
                                            continue
                                        break
                        elif item["owned"]:
                            # Equip the weapon if owned
                            equipped = item["id"]
                            save_ownership()
        clock.tick(60)

def show_upgrade_screen(equipped, owned_items):
    global credits
    # Load current upgrades from save_data.json
    upgrades = {}
    if os.path.exists("save_data.json"):
        with open("save_data.json", "r") as f:
            data = json.load(f)
            upgrades = data.get("upgrades", {})
    weapon_upgrades = upgrades.get(equipped, {"magazine": 0, "reload": 0})

    # Upgrade parameters
    base_magazine = 17 if equipped == "pistol" else 30
    base_reload = 3.0 if equipped == "pistol" else 5.0
    reload_min = 1.5 if equipped == "pistol" else 2.5
    mag_upgrade_cost = 500 * (weapon_upgrades.get("magazine", 0) + 1)
    reload_upgrade_cost = 700 * (weapon_upgrades.get("reload", 0) + 1)
    max_mag_upgrade = 5
    max_reload_upgrade = int((base_reload - reload_min) / 0.5)

    scroll_y = 0
    scroll_speed = 30  # for wheel/keys
    dragging = False
    drag_start_y = 0
    scroll_start_y = 0

    while True:
        screen.fill(BLUE)
        # Title (fixed)
        title = font_large.render("UPGRADE", True, WHITE)
        title_rect = title.get_rect(center=(WIDTH // 2, 70))
        screen.blit(title, title_rect)

        # Back button (fixed)
        back_rect = pygame.Rect(20, 20, 100, 40)
        button_surf = pygame.Surface((back_rect.width, back_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(button_surf, BUTTON_COLOR, button_surf.get_rect(), border_radius=8)
        back_text = font_small.render("Back", True, WHITE)
        back_text_rect = back_text.get_rect(center=button_surf.get_rect().center)
        button_surf.blit(back_text, back_text_rect)
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if back_rect.collidepoint(mouse_pos):
            darken = pygame.Surface((back_rect.width, back_rect.height), pygame.SRCALPHA)
            alpha = 80 if mouse_pressed else 40
            darken.fill((0, 0, 0, alpha))
            button_surf.blit(darken, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            button_surf.blit(back_text, back_text_rect)
        screen.blit(button_surf, back_rect.topleft)

        # Credits (fixed)
        credits_text = font_small.render(f"Credits: {credits}", True, TEXT_COLOR)
        credits_rect = credits_text.get_rect(topright=(WIDTH - 20, 20))
        screen.blit(credits_text, credits_rect)

        # --- SCROLLABLE AREA CLIP ---
        scroll_clip_rect = pygame.Rect(0, 120, WIDTH, HEIGHT - 120)  # 120px leaves room for title/bar
        screen.set_clip(scroll_clip_rect)

        # --- Scrollable area ---
        center_x = WIDTH // 2
        y = 150 + scroll_y
        spacing = 55

        # Magazine size
        mag_level = weapon_upgrades.get("magazine", 0)
        mag_size = base_magazine + mag_level * 3
        mag_text = font_small.render(f"Magazine Size: {mag_size}", True, WHITE)
        mag_text_rect = mag_text.get_rect(center=(center_x, y))
        screen.blit(mag_text, mag_text_rect)
        y += spacing

        # Magazine upgrade price
        mag_upgrade_text = font_small.render(f"Upgrade (+3): {mag_upgrade_cost} Credits", True, TEXT_COLOR)
        mag_upgrade_text_rect = mag_upgrade_text.get_rect(center=(center_x, y))
        screen.blit(mag_upgrade_text, mag_upgrade_text_rect)
        y += spacing

        # Magazine upgrade button
        mag_upgrade_rect = pygame.Rect(center_x - 60, y - 20, 120, 40)
        pygame.draw.rect(screen, BUTTON_COLOR, mag_upgrade_rect, border_radius=8)
        mag_btn_text = font_small.render("Upgrade", True, WHITE)
        mag_btn_rect = mag_btn_text.get_rect(center=mag_upgrade_rect.center)
        screen.blit(mag_btn_text, mag_btn_rect)
        if mag_level >= max_mag_upgrade:
            max_text = font_small.render("Maxed", True, (255, 80, 80))
            max_text_rect = max_text.get_rect(center=(center_x, y + 40))
            screen.blit(max_text, max_text_rect)
        y += spacing + 20

        # Reload speed
        reload_level = weapon_upgrades.get("reload", 0)
        reload_time = max(reload_min, base_reload - reload_level * 0.5)
        reload_text = font_small.render(f"Reload Time: {reload_time:.1f}s", True, WHITE)
        reload_text_rect = reload_text.get_rect(center=(center_x, y + 20))
        screen.blit(reload_text, reload_text_rect)
        y += spacing

        # Reload upgrade price
        reload_upgrade_text = font_small.render(f"Upgrade (-0.5s): {reload_upgrade_cost} Credits", True, TEXT_COLOR)
        reload_upgrade_text_rect = reload_upgrade_text.get_rect(center=(center_x, y))
        screen.blit(reload_upgrade_text, reload_upgrade_text_rect)
        y += spacing

        # Reload upgrade button
        reload_upgrade_rect = pygame.Rect(center_x - 60, y - 20, 120, 40)
        pygame.draw.rect(screen, BUTTON_COLOR, reload_upgrade_rect, border_radius=8)
        reload_btn_text = font_small.render("Upgrade", True, WHITE)
        reload_btn_rect = reload_btn_text.get_rect(center=reload_upgrade_rect.center)
        screen.blit(reload_btn_text, reload_btn_rect)
        if reload_level >= max_reload_upgrade:
            max_text = font_small.render("Maxed", True, (255, 80, 80))
            max_text_rect = max_text.get_rect(center=(center_x, y + 40))
            screen.blit(max_text, max_text_rect)

        # --- END SCROLLABLE AREA CLIP ---
        screen.set_clip(None)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_rect.collidepoint(event.pos):
                    if back_rect.collidepoint(event.pos):
                        # Save upgrades and return
                        if os.path.exists("save_data.json"):
                            with open("save_data.json", "r") as f:
                                data = json.load(f)
                        else:
                            data = {}
                        if "upgrades" not in data:
                            data["upgrades"] = {}
                        data["upgrades"][equipped] = weapon_upgrades
                        with open("save_data.json", "w") as f:
                            json.dump(data, f)
                        return
                # Check upgrade buttons FIRST (before dragging)
                if mag_upgrade_rect.collidepoint(event.pos) and mag_level < max_mag_upgrade:
                    if credits >= mag_upgrade_cost:
                        credits -= mag_upgrade_cost
                        weapon_upgrades["magazine"] = mag_level + 1
                        mag_upgrade_cost = 500 * (weapon_upgrades["magazine"] + 1)
                elif reload_upgrade_rect.collidepoint(event.pos) and reload_level < max_reload_upgrade:
                    if credits >= reload_upgrade_cost:
                        credits -= reload_upgrade_cost
                        weapon_upgrades["reload"] = reload_level + 1
                        reload_upgrade_cost = 700 * (weapon_upgrades["reload"] + 1)
                # Prepare for possible drag
                dragging = True
                drag_start_y = event.pos[1]
                scroll_start_y = scroll_y
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
            elif event.type == pygame.MOUSEMOTION and dragging:
                dy = event.pos[1] - drag_start_y
                # Only start scrolling if the drag is more than a few pixels (to avoid accidental drags)
                if abs(dy) > 5:
                    scroll_y = scroll_start_y + dy
            elif event.type == pygame.MOUSEWHEEL:
                scroll_y += event.y * scroll_speed
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    scroll_y -= scroll_speed
                elif event.key == pygame.K_UP:
                    scroll_y += scroll_speed

        # Clamp scroll_y so you can't scroll too far
        min_scroll = min(-200, HEIGHT - y - 150)  # Always allow at least 200px scroll up
        max_scroll = 0
        scroll_y = max(min_scroll, min(scroll_y, max_scroll))

        clock.tick(60)

if music_volume is None:
    music_volume = 1.0  # Default volume if not loaded

if sfx_volume is None:
    sfx_volume = 1.0  # Default volume if not loaded

def show_settings():
    global music_volume, sfx_volume
    dragging = None  # None, "music", or "sfx"
    slider_x = WIDTH // 2 - 150
    slider_width = 300
    slider_height = 8
    knob_radius = 15
    slider_y_music = HEIGHT // 2 + 20
    slider_y_sfx = HEIGHT // 2 + 100

    def get_knob_pos(vol, y):
        return int(slider_x + vol * slider_width), y + slider_height // 2

    while True:
        screen.fill(BLUE)
        settings_title = font_large.render("Settings", True, WHITE)
        screen.blit(settings_title, (WIDTH // 2 - settings_title.get_width() // 2, HEIGHT // 2 - 120))

        # Music Volume
        music_label = font_small.render("Music Volume", True, TEXT_COLOR)
        screen.blit(music_label, (slider_x, slider_y_music - 40))
        pygame.draw.rect(screen, (180, 180, 180), (slider_x, slider_y_music, slider_width, slider_height), border_radius=4)
        knob_x, knob_y = get_knob_pos(music_volume, slider_y_music)
        pygame.draw.circle(screen, BUTTON_COLOR, (knob_x, knob_y), knob_radius)
        percent_text = font_small.render(f"{int(music_volume * 100)}%", True, TEXT_COLOR)
        screen.blit(percent_text, (slider_x + slider_width + 20, slider_y_music - 15))

        # SFX Volume
        sfx_label = font_small.render("SFX Volume", True, TEXT_COLOR)
        screen.blit(sfx_label, (slider_x, slider_y_sfx - 40))
        pygame.draw.rect(screen, (180, 180, 180), (slider_x, slider_y_sfx, slider_width, slider_height), border_radius=4)
        knob_x2, knob_y2 = get_knob_pos(sfx_volume, slider_y_sfx)
        pygame.draw.circle(screen, BUTTON_COLOR, (knob_x2, knob_y2), knob_radius)
        percent_text2 = font_small.render(f"{int(sfx_volume * 100)}%", True, TEXT_COLOR)
        screen.blit(percent_text2, (slider_x + slider_width + 20, slider_y_sfx - 15))

        # Back button
        back_rect = pygame.Rect(20, 20, 100, 40)
        button_surf = pygame.Surface((back_rect.width, back_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(button_surf, BUTTON_COLOR, button_surf.get_rect(), border_radius=8)
        back_text = font_small.render("Back", True, WHITE)
        back_text_rect = back_text.get_rect(center=button_surf.get_rect().center)
        button_surf.blit(back_text, back_text_rect)
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if back_rect.collidepoint(mouse_pos):
            darken = pygame.Surface((back_rect.width, back_rect.height), pygame.SRCALPHA)
            alpha = 80 if mouse_pressed else 40
            darken.fill((0, 0, 0, alpha))
            button_surf.blit(darken, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            button_surf.blit(back_text, back_text_rect)
        screen.blit(button_surf, back_rect.topleft)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if back_rect.collidepoint(mx, my):
                    save_game(music_volume=music_volume, sfx_volume=sfx_volume)
                    return
                # Music knob
                if (mx - get_knob_pos(music_volume, slider_y_music)[0]) ** 2 + (my - get_knob_pos(music_volume, slider_y_music)[1]) ** 2 <= knob_radius ** 2:
                    dragging = "music"
                # SFX knob
                elif (mx - get_knob_pos(sfx_volume, slider_y_sfx)[0]) ** 2 + (my - get_knob_pos(sfx_volume, slider_y_sfx)[1]) ** 2 <= knob_radius ** 2:
                    dragging = "sfx"
                # Click on music slider
                elif slider_x <= mx <= slider_x + slider_width and slider_y_music - knob_radius <= my <= slider_y_music + slider_height + knob_radius:
                    music_volume = (mx - slider_x) / slider_width
                    music_volume = max(0.0, min(1.0, music_volume))
                    pygame.mixer.music.set_volume(music_volume)
                # Click on sfx slider
                elif slider_x <= mx <= slider_x + slider_width and slider_y_sfx - knob_radius <= my <= slider_y_sfx + slider_height + knob_radius:
                    sfx_volume = (mx - slider_x) / slider_width
                    sfx_volume = max(0.0, min(1.0, sfx_volume))
                    pistol_sound.set_volume(sfx_volume)
                    empty_sound.set_volume(sfx_volume)
                    store_entrance_sound.set_volume(sfx_volume)
                    store_exit_sound.set_volume(sfx_volume)
            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = None
            elif event.type == pygame.MOUSEMOTION and dragging:
                mx, my = event.pos
                if dragging == "music":
                    music_volume = (mx - slider_x) / slider_width
                    music_volume = max(0.0, min(1.0, music_volume))
                    pygame.mixer.music.set_volume(music_volume)
                elif dragging == "sfx":
                    sfx_volume = (mx - slider_x) / slider_width
                    sfx_volume = max(0.0, min(1.0, sfx_volume))
                    pistol_sound.set_volume(sfx_volume)
                    empty_sound.set_volume(sfx_volume)
                    store_entrance_sound.set_volume(sfx_volume)
                    store_exit_sound.set_volume(sfx_volume)
        clock.tick(60)

# Set initial volume for sounds
pistol_sound.set_volume(sfx_volume)
empty_sound.set_volume(sfx_volume)

game_over = False
game_over_start = None  # Track when game over started

running = True
while running:
    menu_choice = show_menu()

    if menu_choice == "start":
        # Initialize game state
        credits, music_volume, sfx_volume = load_game()
        # Load equipped weapon
        equipped = "pistol"
        owned_items = {"pistol"}
        weapon_upgrades = {"magazine": 0}
        if os.path.exists("save_data.json"):
            with open("save_data.json", "r") as f:
                data = json.load(f)
                equipped = data.get("equipped", "pistol")
                owned_items = set(data.get("owned_items", ["pistol"]))
                upgrades = data.get("upgrades", {})
                weapon_upgrades = upgrades.get(equipped, {"magazine": 0})

        # Set weapon stats and load correct spritesheet based on equipped weapon
        if equipped == "ak":
            base_mag = 30
            mag_upgrade = weapon_upgrades.get("magazine", 0)
            reload_level = weapon_upgrades.get("reload", 0)
            base_reload = 5.0
            reload_min = 2.5
            reload_duration = max(reload_min, base_reload - reload_level * 0.5)
            AMMO_MAX = base_mag + mag_upgrade * 3
            fire_rate = 0.08  # seconds between shots
            is_auto = True
            # Load AK spritesheet and scale frames to 0.5
            gun_sprite_sheet = pygame.image.load("akAnimation.png").convert_alpha()
            frame_width = 195
            frame_height = 454
            num_frames = 2
            scale_factor = 0.5
            gun_fire_frames = []
            for i in range(num_frames):
                rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                frame = gun_sprite_sheet.subsurface(rect)
                scaled_frame = pygame.transform.smoothscale(
                    frame,
                    (int(frame_width * scale_factor), int(frame_height * scale_factor))
                )
                gun_fire_frames.append(scaled_frame)
            frame_width = int(frame_width * scale_factor)
            frame_height = int(frame_height * scale_factor)
            gun_x = WIDTH // 2 - frame_width // 2
            gun_y = HEIGHT - frame_height
        else:
            base_mag = 17
            mag_upgrade = weapon_upgrades.get("magazine", 0)
            reload_level = weapon_upgrades.get("reload", 0)
            base_reload = 3.0
            reload_min = 1.5
            reload_duration = max(reload_min, base_reload - reload_level * 0.5)
            AMMO_MAX = base_mag + mag_upgrade * 3
            fire_rate = 0.25
            is_auto = False
            # Load pistol spritesheet and scale frames to 0.8
            gun_sprite_sheet = pygame.image.load("newPistolAnimation.png").convert_alpha()
            frame_width = 300
            frame_height = 200
            num_frames = 2
            scale_factor = 0.8
            gun_fire_frames = []
            for i in range(num_frames):
                rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                frame = gun_sprite_sheet.subsurface(rect)
                scaled_frame = pygame.transform.smoothscale(
                    frame,
                    (int(frame_width * scale_factor), int(frame_height * scale_factor))
                )
                gun_fire_frames.append(scaled_frame)
            frame_width = int(frame_width * scale_factor)
            frame_height = int(frame_height * scale_factor)
            gun_x = WIDTH // 2 - frame_width // 2
            gun_y = HEIGHT - frame_height

        game_started = False
        game_over = False
        game_over_start = None
        start_time = time.time()
        player_health = 100
        ammo = AMMO_MAX  # <-- This now uses the upgraded value
        reloading = False
        wave = 1
        score = 0
        last_shot_time = 0

        pistol_sound.set_volume(sfx_volume)
        empty_sound.set_volume(sfx_volume)

        # Start the game
        while not game_over:
            screen.fill(BLUE)
            now = time.time()
            elapsed = now - start_time

            random.shuffle(GAME_MUSIC_TRACKS)
            current_track_index = 0

            # Game start countdown
            if not game_started:
                remaining = max(0, countdown_duration - int(elapsed))
                countdown_text = font_large.render(str(remaining), True, TEXT_COLOR)
                screen.blit(countdown_text, (WIDTH // 2 - 25, HEIGHT // 2 - 50))

                if elapsed >= countdown_duration:
                    game_started = True
                    start_wave(wave)
            else:
                # In your game loop, after starting the first wave:
                if not pygame.mixer.music.get_busy():
                    play_next_game_track(music_volume)

                # Also, in your main game loop, check if the music finished and play the next:
                if game_started and not pygame.mixer.music.get_busy():
                    play_next_game_track(music_volume)

                if game_over:
                    if game_over_start is None:
                        game_over_start = now  # mark when game over began

                    # Show game over text
                    screen.fill(BLUE)
                    game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
                    screen.blit(game_over_text, (WIDTH // 2 - 150, HEIGHT // 2 - 50))

                    # After 5 seconds, return to menu
                    if now - game_over_start >= 5:
                        #stop music and return to menu
                        pygame.mixer.music.stop()
                        save_game(credits=credits, music_volume=music_volume, sfx_volume=sfx_volume)
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
                                        save_game(credits=credits, music_volume=music_volume, sfx_volume=sfx_volume)
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
                    if game_started and not game_over:
                        if quit_button_rect.collidepoint(event.pos):
                            if show_quit_confirmation():
                                credits += int(score)
                                save_game(credits=credits, music_volume=music_volume, sfx_volume=sfx_volume)
                                game_over = True
                                pygame.mixer.music.stop()
                                break

                if not game_over and game_started:
                                    mouse_down = pygame.mouse.get_pressed()[0]
                                    now = time.time()
                                    can_shoot = not reloading and ammo > 0 and wave_in_progress and (now - last_shot_time >= fire_rate)
                                    if is_auto:
                                        if mouse_down and can_shoot:
                                            # Play on the next channel in round-robin fashion
                                            GUNSHOT_CHANNELS[gunshot_channel_idx].play(pistol_sound)
                                            gunshot_channel_idx = (gunshot_channel_idx + 1) % len(GUNSHOT_CHANNELS)
                                            gun_state = "firing"
                                            gun_frame_time = now
                                            pos = pygame.mouse.get_pos()
                                            for target in active_targets[:]:
                                                if target["rect"].collidepoint(pos):
                                                    active_targets.remove(target)
                                                    score += points_per_target
                                                    break
                                            ammo -= 1
                                            last_shot_time = now
                                            if ammo <= 0:
                                                reloading = True
                                                reload_start_time = now
                                        elif mouse_down and reloading:
                                            empty_sound.play()
                                    else:
                                        if event.type == pygame.MOUSEBUTTONDOWN and can_shoot:
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
                                            last_shot_time = now
                                            if ammo <= 0:
                                                reloading = True
                                                reload_start_time = now
                                        elif event.type == pygame.MOUSEBUTTONDOWN and reloading:
                                            empty_sound.play()

            pygame.display.update()
            clock.tick(60)
    elif menu_choice == "settings":
        show_settings()
    elif menu_choice == "store":
        show_store()

pygame.quit()
