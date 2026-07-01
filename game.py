import pygame
import random
import os
import json
import math
import sys
import subprocess
import string
import urllib.request
import hashlib
import time
import levels

pygame.init()
pygame.mixer.init()

# --- ПАПКИ И ФАЙЛЫ ---
PLAYERS_FOLDER = "players_data"
PROFILE_FILE = "profile.json"
SETTINGS_FILE = "settings.json"
BAN_FILE = "bans.json"

# --- ПРОВЕРКА ОБНОВЛЕНИЙ ---
def check_updates():
    if not os.path.exists("version.txt"):
        return False, "0.0.0", "0.0.0"
    try:
        with open("version.txt", "r") as f:
            local_version = f.read().strip()
        url = "https://raw.githubusercontent.com/anhedonuya/UniInARow/main/version.txt"
        req = urllib.request.Request(url, headers={"Accept": "text/plain"})
        with urllib.request.urlopen(req, timeout=5) as response:
            remote_version = response.read().decode("utf-8").strip()
        return local_version != remote_version, local_version, remote_version
    except Exception:
        return False, "0.0.0", "0.0.0"

# --- НАСТРОЙКИ ---
DEFAULT_SETTINGS = {
    "fullscreen": False,
    "music_volume": 0.5,
    "sound_effects": True
}
DEFAULT_PROFILE = {
    "player_name": "Игрок",
    "player_id": "",
    "level": 1,
    "xp": 0,
    "total_games": 0,
    "total_score": 0,
    "best_score": 0,
    "total_time": 0
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def generate_player_id():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=6))

def ensure_players_folder():
    if not os.path.exists(PLAYERS_FOLDER):
        os.makedirs(PLAYERS_FOLDER)

def get_all_players():
    ensure_players_folder()
    players = []
    for filename in os.listdir(PLAYERS_FOLDER):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(PLAYERS_FOLDER, filename), "r") as f:
                    data = json.load(f)
                    players.append({
                        "name": data.get("player_name"),
                        "id": data.get("player_id")
                    })
            except:
                pass
    return players

def is_name_taken(name, exclude_id=None):
    players = get_all_players()
    for p in players:
        if p["name"] == name and p["id"] != exclude_id:
            return True
    return False

def save_player_data(data):
    ensure_players_folder()
    filename = os.path.join(PLAYERS_FOLDER, f"{data['player_id']}.json")
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def delete_player_data(player_id):
    filename = os.path.join(PLAYERS_FOLDER, f"{player_id}.json")
    if os.path.exists(filename):
        os.remove(filename)

def load_bans():
    if os.path.exists(BAN_FILE):
        try:
            with open(BAN_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_bans(bans):
    with open(BAN_FILE, "w") as f:
        json.dump(bans, f, indent=4)

def is_developer():
    if os.path.exists("developer.key"):
        try:
            with open("developer.key", "r") as f:
                content = f.read().strip()
                if hashlib.sha256(content.encode()).hexdigest() == "a9f8c3e2b1d4567890abcdef1234567890abcdef1234567890abcdef12345678":
                    return True
        except:
            pass
    return False

def load_profile():
    ensure_players_folder()
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r") as f:
                data = json.load(f)
                if "level" not in data:
                    data["level"] = 1
                if "xp" not in data:
                    data["xp"] = 0
                if "total_time" not in data:
                    data["total_time"] = 0
                if "player_id" not in data or not data["player_id"]:
                    data["player_id"] = generate_player_id()
                    if is_developer():
                        data["player_id"] = "DEVELOPER"
                save_profile(data)
                save_player_data(data)
                return data
        except:
            pass
    new_profile = DEFAULT_PROFILE.copy()
    new_profile["player_id"] = generate_player_id()
    if is_developer():
        new_profile["player_id"] = "DEVELOPER"
    
    if new_profile["player_id"] != "DEVELOPER":
        if is_name_taken(new_profile["player_name"]):
            new_profile["player_name"] = f"Игрок_{new_profile['player_id'][:4]}"
    
    save_profile(new_profile)
    save_player_data(new_profile)
    return new_profile

def save_profile(profile):
    with open(PROFILE_FILE, "w") as f:
        json.dump(profile, f, indent=4)
    save_player_data(profile)

settings = load_settings()
profile = load_profile()
bans = load_bans()

if profile["player_id"] in bans or profile["player_name"] in bans:
    print("❌ Вы забанены!")
    pygame.quit()
    sys.exit()

# --- РАЗМЕРЫ ОКНА ---
WINDOW_WIDTH, WINDOW_HEIGHT = 600, 700
fullscreen = settings.get("fullscreen", False)

if fullscreen:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()
else:
    WIDTH, HEIGHT = WINDOW_WIDTH, WINDOW_HEIGHT
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

pygame.display.set_caption("Uni in a Row")
clock = pygame.time.Clock()

# --- ЦВЕТА ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
DARK_GRAY = (30, 30, 30)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)

# --- РАЗМЕРЫ ПОЛЯ (УМЕНЬШЕННЫЕ) ---
GRID_SIZE = 6
CELL_SIZE = 50
MARGIN = (WIDTH - (GRID_SIZE * CELL_SIZE)) // 2
TOP_OFFSET = 150

# --- ЗАГРУЗКА ФОНОВ ---
def load_backgrounds():
    bg = {}
    
    # Основной фон для меню и игры
    bg_path = "sprites/background.png"
    if os.path.exists(bg_path):
        try:
            bg["normal"] = pygame.image.load(bg_path).convert()
            bg["normal"] = pygame.transform.scale(bg["normal"], (WIDTH, HEIGHT))
        except:
            bg["normal"] = None
    else:
        bg["normal"] = None
    
    # Фон для полноэкранного режима
    bg_full_path = "sprites/background_fullscreen.png"
    if os.path.exists(bg_full_path):
        try:
            bg["fullscreen"] = pygame.image.load(bg_full_path).convert()
            bg["fullscreen"] = pygame.transform.scale(bg["fullscreen"], (WIDTH, HEIGHT))
        except:
            bg["fullscreen"] = None
    else:
        bg["fullscreen"] = None
    
    # Общий фон для всех остальных экранов (уровни, админка, смена ника)
    bg_common_path = "sprites/background_common.png"
    if os.path.exists(bg_common_path):
        try:
            bg["common"] = pygame.image.load(bg_common_path).convert()
            bg["common"] = pygame.transform.scale(bg["common"], (WIDTH, HEIGHT))
        except:
            bg["common"] = None
    else:
        bg["common"] = None
    
    return bg

backgrounds = load_backgrounds()

def get_current_background():
    if fullscreen and backgrounds["fullscreen"]:
        return backgrounds["fullscreen"]
    elif backgrounds["normal"]:
        return backgrounds["normal"]
    return None

def get_common_background():
    """Возвращает общий фон для всех вспомогательных экранов"""
    if backgrounds["common"]:
        return backgrounds["common"]
    return None

def draw_common_background():
    """Рисует общий фон или чёрный экран, если фона нет"""
    bg = get_common_background()
    if bg:
        screen.blit(bg, (0, 0))
    else:
        screen.fill(BLACK)

# --- ЗАГРУЗКА МУЗЫКИ ---
music_paths = ["sprites/menu_music.ogg", "sprites/menu_music.wav", "sounds/menu_music.ogg", "sounds/menu_music.wav"]
music_loaded = False
music_started = False

for path in music_paths:
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            music_loaded = True
            pygame.mixer.music.set_volume(settings.get("music_volume", 0.5))
            break
        except:
            pass

# --- ЗАГРУЗКА СПРАЙТОВ ---
def load_sprites():
    sprites = {}
    colors = ["blue", "green", "red", "yellow", "purple"]
    for color in colors:
        path = f"sprites/uni_{color}.png"
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.scale(img, (CELL_SIZE - 8, CELL_SIZE - 8))
            sprites[color] = img
        else:
            surf = pygame.Surface((CELL_SIZE - 8, CELL_SIZE - 8))
            surf.fill(pygame.Color(color))
            sprites[color] = surf
    return sprites

sprites = load_sprites()
colors_list = list(sprites.keys())

# --- ФУНКЦИИ СОХРАНЕНИЯ ИГРЫ ---
def get_save_path():
    if not os.path.exists("saves"):
        os.makedirs("saves")
    return "saves/save.dat"

def save_game(grid_data, score_val, level_val, moves_val, color_counters_val):
    data = {
        "grid": grid_data,
        "score": score_val,
        "level": level_val,
        "moves": moves_val,
        "color_counters": color_counters_val,
        "version": 1,
        "player_id": profile["player_id"],
        "player_name": profile["player_name"]
    }
    with open(get_save_path(), "w") as f:
        json.dump(data, f)

def load_game():
    path = get_save_path()
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        data = json.load(f)
    return data

def has_save():
    return os.path.exists(get_save_path())

# --- ПРОФИЛЬ И УРОВНИ ---
def calculate_xp(score):
    return score * 2 + 10

def check_level_up():
    global profile
    xp_needed = profile['level'] * 50 + 20
    while profile['xp'] >= xp_needed:
        profile['xp'] -= xp_needed
        profile['level'] += 1
        xp_needed = profile['level'] * 50 + 20
        print(f"🎉 Уровень повышен до {profile['level']}!")

def format_time(seconds):
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}ч {minutes}м {secs}с"
    elif minutes > 0:
        return f"{minutes}м {secs}с"
    else:
        return f"{secs}с"

def update_profile(score):
    global profile, session_time
    if score > 0:
        xp_gain = calculate_xp(score)
        profile['xp'] += xp_gain
        profile['total_games'] += 1
        profile['total_score'] += score
        if score > profile['best_score']:
            profile['best_score'] = score
        profile['total_time'] = profile.get('total_time', 0) + session_time
        session_time = 0
        check_level_up()
        save_profile(profile)
        save_player_data(profile)

# --- ФУНКЦИИ ДЛЯ РИСОВАНИЯ ---
def draw_button(surface, text, rect, color, hover_color, shadow_color, is_hovered, border_radius=12):
    offset = 0
    shadow_offset = 4
    if is_hovered:
        offset = -3
        shadow_offset = 6
    
    shadow_rect = rect.copy()
    shadow_rect.y += shadow_offset
    pygame.draw.rect(surface, shadow_color, shadow_rect, border_radius=border_radius)
    
    btn_rect = rect.copy()
    btn_rect.y += offset
    current_color = hover_color if is_hovered else color
    pygame.draw.rect(surface, current_color, btn_rect, border_radius=border_radius)
    
    text_surf = font.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=btn_rect.center)
    if is_hovered:
        text_rect.y -= 1
    surface.blit(text_surf, text_rect)
    return btn_rect

def draw_title(text, x, y, size=72):
    font_big = pygame.font.Font(None, size)
    text_surf = font_big.render(text, True, WHITE)
    text_rect = text_surf.get_rect(center=(x, y))
    
    shadow_surf = font_big.render(text, True, (30, 30, 30))
    shadow_rect = text_rect.copy()
    shadow_rect.x += 4
    shadow_rect.y += 4
    screen.blit(shadow_surf, shadow_rect)
    
    shadow2_surf = font_big.render(text, True, (60, 60, 60))
    shadow2_rect = text_rect.copy()
    shadow2_rect.x += 2
    shadow2_rect.y += 2
    screen.blit(shadow2_surf, shadow2_rect)
    
    colors = [(255, 200, 50), (255, 180, 30), (200, 150, 50)]
    for i, col in enumerate(colors):
        surf = font_big.render(text, True, col)
        rect = text_rect.copy()
        rect.x += i * 1
        rect.y += i * 1
        screen.blit(surf, rect)
    
    highlight_surf = font_big.render(text, True, (255, 240, 200))
    screen.blit(highlight_surf, text_rect)
    
    border_rect = text_rect.inflate(30, 20)
    pygame.draw.rect(screen, (100, 80, 30), border_rect, 2, border_radius=10)
    outer_rect = border_rect.inflate(10, 10)
    pygame.draw.rect(screen, (60, 50, 20), outer_rect, 1, border_radius=12)

def draw_xp_bar():
    xp_needed = profile['level'] * 50 + 20
    progress = min(profile['xp'] / xp_needed, 1.0)
    bar_width = 200
    bar_height = 10
    bar_x = WIDTH - 290
    bar_y = 115
    
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=4)
    pygame.draw.rect(screen, (100, 200, 100), (bar_x, bar_y, int(bar_width * progress), bar_height), border_radius=4)
    
    percent_text = small_font.render(f"{int(progress * 100)}%", True, (200, 200, 200))
    screen.blit(percent_text, (bar_x + bar_width + 10, bar_y - 2))

def draw_stats_window():
    draw_common_background()
    
    box_width, box_height = 400, 370
    box_x = (WIDTH - box_width) // 2
    box_y = (HEIGHT - box_height) // 2
    pygame.draw.rect(screen, (40, 40, 40), (box_x, box_y, box_width, box_height), border_radius=15)
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 2, border_radius=15)
    
    title = big_font.render("Статистика", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, box_y + 15))
    
    y_offset = box_y + 80
    total_time = profile.get('total_time', 0) + session_time
    lines = [
        f"Имя: {profile['player_name']}",
        f"ID: {profile['player_id']}",
        f"Уровень: {profile['level']}  XP: {profile['xp']}",
        f"Всего игр: {profile['total_games']}",
        f"Лучший счёт: {profile['best_score']}",
        f"Общий счёт: {profile['total_score']}",
        f"Время в игре: {format_time(total_time)}"
    ]
    
    for line in lines:
        line_surf = font.render(line, True, WHITE)
        screen.blit(line_surf, (box_x + 30, y_offset))
        y_offset += 35
    
    close_btn = pygame.Rect(box_x + box_width//2 - 60, box_y + box_height - 50, 120, 35)
    pygame.draw.rect(screen, RED, close_btn, border_radius=8)
    close_text = font.render("Закрыть", True, WHITE)
    screen.blit(close_text, (close_btn.x + 25, close_btn.y + 6))
    return close_btn

def draw_exit_confirm():
    draw_common_background()
    
    box_width, box_height = 350, 150
    box_x = (WIDTH - box_width) // 2
    box_y = (HEIGHT - box_height) // 2
    pygame.draw.rect(screen, (40, 40, 40), (box_x, box_y, box_width, box_height), border_radius=15)
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 2, border_radius=15)
    
    text = font.render("Вы уверены, что хотите выйти?", True, WHITE)
    screen.blit(text, (WIDTH//2 - text.get_width()//2, box_y + 25))
    
    yes_btn = pygame.Rect(box_x + 30, box_y + 80, 120, 40)
    pygame.draw.rect(screen, RED, yes_btn, border_radius=10)
    yes_text = font.render("Да", True, WHITE)
    screen.blit(yes_text, (yes_btn.x + 45, yes_btn.y + 8))
    
    no_btn = pygame.Rect(box_x + box_width - 150, box_y + 80, 120, 40)
    pygame.draw.rect(screen, GREEN, no_btn, border_radius=10)
    no_text = font.render("Нет", True, WHITE)
    screen.blit(no_text, (no_btn.x + 40, no_btn.y + 8))
    return yes_btn, no_btn

def draw_update_notification():
    draw_common_background()
    
    box_width, box_height = 400, 200
    box_x = (WIDTH - box_width) // 2
    box_y = (HEIGHT - box_height) // 2
    pygame.draw.rect(screen, (30, 30, 30), (box_x, box_y, box_width, box_height), border_radius=15)
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 2, border_radius=15)
    title = big_font.render("Обновление!", True, YELLOW)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, box_y + 20))
    info_text = font.render("Доступна новая версия игры", True, WHITE)
    screen.blit(info_text, (WIDTH//2 - info_text.get_width()//2, box_y + 70))
    update_btn = pygame.Rect(box_x + 100, box_y + 130, 200, 50)
    pygame.draw.rect(screen, GREEN, update_btn, border_radius=10)
    update_text = font.render("Обновить", True, WHITE)
    screen.blit(update_text, (update_btn.x + 55, update_btn.y + 12))
    return update_btn

def draw_gear_button():
    global gear_rotation, gear_open, gear_animating, gear_target_rotation
    
    btn_size = 50
    btn_x = WIDTH - btn_size - 15
    btn_y = HEIGHT - btn_size - 15
    
    if gear_animating:
        if gear_rotation < gear_target_rotation:
            gear_rotation += 6
            if gear_rotation >= gear_target_rotation:
                gear_rotation = gear_target_rotation
                gear_animating = False
        elif gear_rotation > gear_target_rotation:
            gear_rotation -= 6
            if gear_rotation <= gear_target_rotation:
                gear_rotation = gear_target_rotation
                gear_animating = False
    
    pygame.draw.circle(screen, (60, 60, 60), (btn_x + btn_size//2, btn_y + btn_size//2), btn_size//2 + 4)
    pygame.draw.circle(screen, (40, 40, 40), (btn_x + btn_size//2, btn_y + btn_size//2), btn_size//2 + 2)
    pygame.draw.circle(screen, (80, 80, 80), (btn_x + btn_size//2, btn_y + btn_size//2), btn_size//2)
    
    center_x = btn_x + btn_size//2
    center_y = btn_y + btn_size//2
    radius = 18
    tooth_count = 8
    tooth_size = 6
    
    for i in range(tooth_count):
        angle = math.radians(i * 360 / tooth_count + gear_rotation)
        x1 = center_x + radius * math.cos(angle)
        y1 = center_y + radius * math.sin(angle)
        x2 = center_x + (radius + tooth_size) * math.cos(angle)
        y2 = center_y + (radius + tooth_size) * math.sin(angle)
        pygame.draw.line(screen, (180, 180, 180), (x1, y1), (x2, y2), 4)
    
    pygame.draw.circle(screen, (180, 180, 180), (center_x, center_y), radius - 4)
    pygame.draw.circle(screen, (100, 100, 100), (center_x, center_y), radius - 8)
    pygame.draw.circle(screen, (60, 60, 60), (center_x, center_y), 6)
    
    if gear_open:
        menu_bg = pygame.Surface((180, 100), pygame.SRCALPHA)
        menu_bg.fill((0, 0, 0, 220))
        screen.blit(menu_bg, (btn_x - 140, btn_y - 110))
        pygame.draw.rect(screen, WHITE, (btn_x - 140, btn_y - 110, 180, 100), 1, border_radius=8)
        
        save_btn = pygame.Rect(btn_x - 130, btn_y - 100, 160, 35)
        pygame.draw.rect(screen, (0, 150, 0), save_btn, border_radius=6)
        save_text = small_font.render("Сохранить и выйти", True, WHITE)
        screen.blit(save_text, (save_btn.x + 10, save_btn.y + 8))
        
        menu_btn = pygame.Rect(btn_x - 130, btn_y - 55, 160, 35)
        pygame.draw.rect(screen, (150, 150, 0), menu_btn, border_radius=6)
        menu_text = small_font.render("Выйти в меню", True, WHITE)
        screen.blit(menu_text, (menu_btn.x + 25, menu_btn.y + 8))
        
        return save_btn, menu_btn
    return None, None

def draw_level_info():
    """Рисует информацию об уровне вверху по центру с красивой рамкой"""
    if game_state != PLAYING:
        return
    
    level_data = levels.get_level_data(current_level)
    
    # --- Фон панели ---
    panel_width = 400
    panel_height = 100
    panel_x = (WIDTH - panel_width) // 2
    panel_y = 10
    
    # Полупрозрачный фон
    panel_bg = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel_bg.fill((0, 0, 0, 180))
    screen.blit(panel_bg, (panel_x, panel_y))
    pygame.draw.rect(screen, WHITE, (panel_x, panel_y, panel_width, panel_height), 2, border_radius=10)
    
    # --- Уровень ---
    level_text = small_font.render(f"УРОВЕНЬ {current_level}", True, YELLOW)
    screen.blit(level_text, (WIDTH//2 - level_text.get_width()//2, panel_y + 6))
    
    # --- Цель ---
    if level_data["type"] == "score":
        target_text = f"Цель: {level_data['target']} очков"
        current_value = score
        max_value = level_data["target"]
        remaining = max(0, max_value - current_value)
    else:
        color_names = {
            "blue": "синих",
            "green": "зелёных",
            "red": "красных",
            "yellow": "жёлтых",
            "purple": "фиолетовых"
        }
        color_name = color_names.get(level_data["color"], level_data["color"])
        current_value = color_counters.get(level_data["color"], 0)
        max_value = level_data["target"]
        remaining = max(0, max_value - current_value)
        target_text = f"Цель: {current_value}/{level_data['target']} {color_name} фишек"
    
    target_surf = small_font.render(target_text, True, (200, 200, 200))
    screen.blit(target_surf, (WIDTH//2 - target_surf.get_width()//2, panel_y + 28))
    
    # --- Полоска прогресса ---
    progress = min(current_value / max_value, 1.0) if max_value > 0 else 0
    bar_width = 340
    bar_height = 12
    bar_x = WIDTH//2 - bar_width//2
    bar_y = panel_y + 50
    
    pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height), border_radius=6)
    if progress > 0:
        fill_color = (100, 255, 100) if progress < 1 else (100, 255, 100)
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, int(bar_width * progress), bar_height), border_radius=6)
    pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1, border_radius=6)
    
    percent_text = small_font.render(f"{int(progress * 100)}%", True, WHITE)
    screen.blit(percent_text, (bar_x + bar_width//2 - percent_text.get_width()//2, bar_y - 2))
    
    # --- Иконка цели для цветных уровней ---
    if level_data["type"] == "color" and remaining > 0:
        target_color = level_data["color"]
        if target_color in sprites:
            icon = sprites[target_color]
            icon_size = 24
            icon = pygame.transform.scale(icon, (icon_size, icon_size))
            icon_x = WIDTH//2 + 50
            icon_y = panel_y + 52
            screen.blit(icon, (icon_x, icon_y))
            
            # Цифра сколько осталось (под иконкой)
            remaining_text = small_font.render(str(remaining), True, WHITE)
            remaining_x = icon_x + icon_size//2 - remaining_text.get_width()//2
            screen.blit(remaining_text, (remaining_x, icon_y + icon_size + 2))
        else:
            color_map = {
                "blue": BLUE,
                "green": GREEN,
                "red": RED,
                "yellow": YELLOW,
                "purple": (128, 0, 128)
            }
            color = color_map.get(target_color, WHITE)
            pygame.draw.rect(screen, color, (WIDTH//2 + 50, panel_y + 52, 24, 24))
            remaining_text = small_font.render(str(remaining), True, WHITE)
            remaining_x = WIDTH//2 + 50 + 12 - remaining_text.get_width()//2
            screen.blit(remaining_text, (remaining_x, panel_y + 80))
    
    # --- Ходы ---
    moves_text = small_font.render(f"Ходы: {moves_left}", True, (200, 200, 255))
    screen.blit(moves_text, (WIDTH//2 + 150, panel_y + 72))

def draw_level_complete():
    """Экран завершения уровня с общим фоном"""
    draw_common_background()
    
    box_width, box_height = 400, 250
    box_x = (WIDTH - box_width) // 2
    box_y = (HEIGHT - box_height) // 2
    pygame.draw.rect(screen, (40, 40, 40), (box_x, box_y, box_width, box_height), border_radius=15)
    pygame.draw.rect(screen, WHITE, (box_x, box_y, box_width, box_height), 2, border_radius=15)
    
    if game_state == GAME_COMPLETE:
        title = big_font.render("🎉 Игра пройдена!", True, YELLOW)
    else:
        title = big_font.render(f"Уровень {current_level} пройден!", True, GREEN)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, box_y + 30))
    
    score_text = font.render(f"Очки: {score}", True, WHITE)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, box_y + 100))
    
    next_btn = pygame.Rect(box_x + box_width//2 - 80, box_y + 160, 160, 50)
    pygame.draw.rect(screen, BLUE, next_btn, border_radius=10)
    next_text = font.render("Далее", True, WHITE)
    screen.blit(next_text, (next_btn.x + 40, next_btn.y + 12))
    
    return next_btn

def draw_menu():
    global profile_btn_rect
    screen.fill(BLACK)
    bg = get_current_background()
    if bg:
        screen.blit(bg, (0, 0))
    
    draw_title("Uni in a Row", WIDTH//2, 120, 72 if not fullscreen else 96)
    
    btn_width, btn_height = 200, 50
    btn_x = WIDTH//2 - btn_width//2
    has_save_flag = has_save()
    y_start = 220 if not fullscreen else 270
    
    mouse_pos = pygame.mouse.get_pos()
    
    new_rect = pygame.Rect(btn_x, y_start, btn_width, btn_height)
    load_rect = pygame.Rect(btn_x, y_start + 70, btn_width, btn_height)
    profile_rect = pygame.Rect(btn_x, y_start + 140, btn_width, btn_height)
    settings_rect = pygame.Rect(btn_x, y_start + 210, btn_width, btn_height)
    exit_rect = pygame.Rect(btn_x, y_start + 280, btn_width, btn_height)
    
    new_hover = new_rect.collidepoint(mouse_pos)
    load_hover = load_rect.collidepoint(mouse_pos) and has_save_flag
    profile_hover = profile_rect.collidepoint(mouse_pos)
    settings_hover = settings_rect.collidepoint(mouse_pos)
    exit_hover = exit_rect.collidepoint(mouse_pos)
    
    draw_button(screen, "Новая игра", new_rect, GREEN, (0, 230, 0), (0, 100, 0), new_hover)
    draw_button(screen, "Загрузить", load_rect, BLUE if has_save_flag else GRAY, (0, 130, 255) if has_save_flag else GRAY, (0, 50, 150) if has_save_flag else (30, 30, 30), load_hover)
    draw_button(screen, "Профиль", profile_rect, (100, 100, 200), (130, 130, 230), (50, 50, 100), profile_hover)
    draw_button(screen, "Настройки", settings_rect, (100, 100, 200), (130, 130, 230), (50, 50, 100), settings_hover)
    draw_button(screen, "Выход", exit_rect, RED, (230, 0, 0), (100, 0, 0), exit_hover)
    
    profile_btn_rect = profile_rect
    
    if profile["player_id"] == "DEVELOPER":
        admin_rect = pygame.Rect(WIDTH - 170, 130, 150, 30)
        admin_hover = admin_rect.collidepoint(mouse_pos)
        draw_button(screen, "Админ панель", admin_rect, (100, 0, 100), (130, 0, 130), (50, 0, 50), admin_hover, border_radius=8)
        return new_rect, load_rect, profile_rect, settings_rect, exit_rect, admin_rect
    
    return new_rect, load_rect, profile_rect, settings_rect, exit_rect

def draw_settings_menu():
    screen.fill(BLACK)
    bg = get_current_background()
    if bg:
        screen.blit(bg, (0, 0))
    draw_title("Настройки", WIDTH//2, 120, 60)
    
    btn_width, btn_height = 250, 50
    btn_x = WIDTH//2 - btn_width//2
    y_start = 230 if not fullscreen else 280
    
    mouse_pos = pygame.mouse.get_pos()
    
    fs_rect = pygame.Rect(btn_x, y_start, btn_width, btn_height)
    vol_rect = pygame.Rect(btn_x, y_start + 70, btn_width, btn_height)
    name_rect = pygame.Rect(btn_x, y_start + 140, btn_width, btn_height)
    back_rect = pygame.Rect(btn_x, y_start + 210, btn_width, btn_height)
    
    fs_hover = fs_rect.collidepoint(mouse_pos)
    vol_hover = vol_rect.collidepoint(mouse_pos)
    name_hover = name_rect.collidepoint(mouse_pos)
    back_hover = back_rect.collidepoint(mouse_pos)
    
    fs_color = GREEN if settings.get("fullscreen", False) else GRAY
    fs_hover_color = (0, 230, 0) if settings.get("fullscreen", False) else (80, 80, 80)
    draw_button(screen, f"Полный экран: {'Вкл' if settings.get('fullscreen', False) else 'Выкл'}", fs_rect, fs_color, fs_hover_color, (0, 100, 0) if settings.get("fullscreen", False) else (30, 30, 30), fs_hover)
    
    vol_val = int(settings.get("music_volume", 0.5) * 100)
    draw_button(screen, f"Громкость: {vol_val}% (← →)", vol_rect, (100, 100, 200), (130, 130, 230), (50, 50, 100), vol_hover)
    
    draw_button(screen, f"Имя: {profile['player_name']}", name_rect, (100, 200, 100), (130, 230, 130), (50, 100, 50), name_hover)
    draw_button(screen, "Назад", back_rect, RED, (230, 0, 0), (100, 0, 0), back_hover)
    
    return fs_rect, vol_rect, name_rect, back_rect

def draw_game_over():
    screen.fill(BLACK)
    bg = get_current_background()
    if bg:
        screen.blit(bg, (0, 0))
    game_over_text = big_font.render("Игра окончена!", True, RED)
    screen.blit(game_over_text, (WIDTH//2 - game_over_text.get_width()//2, 150))
    score_text = font.render(f"Счёт: {score}", True, WHITE)
    screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 250))
    best_text = small_font.render(f"Рекорд: {profile['best_score']}  Всего очков: {profile['total_score']}", True, (200,200,200))
    screen.blit(best_text, (WIDTH//2 - best_text.get_width()//2, 290))
    
    mouse_pos = pygame.mouse.get_pos()
    
    restart_rect = pygame.Rect(WIDTH//2 - 80, 350, 160, 50)
    exit_rect = pygame.Rect(WIDTH//2 - 80, 450, 160, 50)
    
    restart_hover = restart_rect.collidepoint(mouse_pos)
    exit_hover = exit_rect.collidepoint(mouse_pos)
    
    draw_button(screen, "Новая игра", restart_rect, GREEN, (0, 230, 0), (0, 100, 0), restart_hover)
    draw_button(screen, "Выход", exit_rect, RED, (230, 0, 0), (100, 0, 0), exit_hover)
    
    return restart_rect, exit_rect

def toggle_fullscreen():
    global fullscreen, screen, WIDTH, HEIGHT, backgrounds
    fullscreen = not fullscreen
    settings["fullscreen"] = fullscreen
    save_settings(settings)
    if fullscreen:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        WIDTH, HEIGHT = screen.get_width(), screen.get_height()
    else:
        WIDTH, HEIGHT = WINDOW_WIDTH, WINDOW_HEIGHT
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    backgrounds = load_backgrounds()
    recalculate_sizes()
    pygame.display.flip()

def run_updater():
    try:
        subprocess.Popen([sys.executable, "updater.py"])
        pygame.quit()
        sys.exit(0)
    except:
        pass

def open_admin_panel():
    try:
        import admin_panel
        admin_panel.show_admin_panel(screen, font, small_font, WIDTH, HEIGHT, profile)
    except ImportError:
        print("admin_panel.py не найден")
    except Exception as e:
        print(f"Ошибка: {e}")

# --- УРОВНИ ---
current_level = 1
moves_left = levels.get_moves(1)
score = 0
color_counters = {
    "blue": 0,
    "green": 0,
    "red": 0,
    "yellow": 0,
    "purple": 0
}
max_level_unlocked = 1  # максимальный доступный уровень (для кнопки "Уровни")

# --- ИГРОВОЕ ПОЛЕ ---
def create_grid():
    return [[random.choice(colors_list) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def get_cell(pos):
    x, y = pos
    if x < MARGIN or y < TOP_OFFSET:
        return None
    col = (x - MARGIN) // CELL_SIZE
    row = (y - TOP_OFFSET) // CELL_SIZE
    if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
        return (row, col)
    return None

def find_matches():
    matches = set()
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE - 2):
            if grid[row][col] == grid[row][col+1] == grid[row][col+2]:
                matches.add((row, col))
                matches.add((row, col+1))
                matches.add((row, col+2))
    for row in range(GRID_SIZE - 2):
        for col in range(GRID_SIZE):
            if grid[row][col] == grid[row+1][col] == grid[row+2][col]:
                matches.add((row, col))
                matches.add((row+1, col))
                matches.add((row+2, col))
    return matches

def remove_matches(matches):
    for row, col in matches:
        grid[row][col] = None

def drop_down():
    drop_info = []
    for col in range(GRID_SIZE):
        for row in range(GRID_SIZE-1, -1, -1):
            if grid[row][col] is None:
                for r in range(row-1, -1, -1):
                    if grid[r][col] is not None:
                        grid[row][col] = grid[r][col]
                        grid[r][col] = None
                        drop_info.append((row, col, grid[row][col], r))
                        break
    for col in range(GRID_SIZE):
        for row in range(GRID_SIZE):
            if grid[row][col] is None:
                new_color = random.choice(colors_list)
                grid[row][col] = new_color
                drop_info.append((row, col, new_color, -1))
    return drop_info

def swap_cells(r1, c1, r2, c2):
    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
    if find_matches():
        return True
    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
    return False

def draw_grid():
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            x = MARGIN + col * CELL_SIZE
            y = TOP_OFFSET + row * CELL_SIZE
            pygame.draw.rect(screen, DARK_GRAY, (x-2, y-2, CELL_SIZE+4, CELL_SIZE+4))
            pygame.draw.rect(screen, GRAY, (x, y, CELL_SIZE, CELL_SIZE))
            color = grid[row][col]
            if color in sprites:
                sprite = sprites[color]
                sx = x + (CELL_SIZE - sprite.get_width()) // 2
                sy = y + (CELL_SIZE - sprite.get_height()) // 2
                screen.blit(sprite, (sx, sy))
            if selected and selected == (row, col):
                pygame.draw.rect(screen, WHITE, (x-3, y-3, CELL_SIZE+6, CELL_SIZE+6), 3)

def check_level_complete():
    global current_level, score, moves_left, grid, game_state, color_counters, max_level_unlocked
    level_data = levels.get_level_data(current_level)
    
    if level_data["type"] == "score":
        completed = score >= level_data["target"]
    else:  # color
        target_color = level_data["color"]
        completed = color_counters.get(target_color, 0) >= level_data["target"]
    
    if completed:
        if levels.is_last_level(current_level):
            game_state = GAME_COMPLETE
        else:
            # Открываем следующий уровень
            if current_level + 1 > max_level_unlocked:
                max_level_unlocked = current_level + 1
            game_state = LEVEL_COMPLETE
        return True
    return False

# --- АНИМАЦИИ ---
class SwapAnimation:
    def __init__(self, r1, c1, r2, c2, duration=200):
        self.r1, self.c1 = r1, c1
        self.r2, self.c2 = r2, c2
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False

    def update(self):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
            self.finished = True
        x1 = MARGIN + self.c1 * CELL_SIZE + CELL_SIZE // 2
        y1 = TOP_OFFSET + self.r1 * CELL_SIZE + CELL_SIZE // 2
        x2 = MARGIN + self.c2 * CELL_SIZE + CELL_SIZE // 2
        y2 = TOP_OFFSET + self.r2 * CELL_SIZE + CELL_SIZE // 2
        dx = (x2 - x1) * t
        dy = (y2 - y1) * t
        self.pos = (x1 + dx, y1 + dy)

    def draw(self, screen):
        if self.finished:
            return
        x, y = self.pos
        color1 = grid[self.r1][self.c1]
        color2 = grid[self.r2][self.c2]
        if color1 in sprites:
            sprite = sprites[color1]
            sx = x - CELL_SIZE//2 + (CELL_SIZE - sprite.get_width()) // 2
            sy = y - CELL_SIZE//2 + (CELL_SIZE - sprite.get_height()) // 2
            screen.blit(sprite, (sx, sy))
        x2 = 2*MARGIN + self.c1*CELL_SIZE + self.c2*CELL_SIZE + CELL_SIZE - x
        y2 = 2*TOP_OFFSET + self.r1*CELL_SIZE + self.r2*CELL_SIZE + CELL_SIZE - y
        if color2 in sprites:
            sprite = sprites[color2]
            sx = x2 - CELL_SIZE//2 + (CELL_SIZE - sprite.get_width()) // 2
            sy = y2 - CELL_SIZE//2 + (CELL_SIZE - sprite.get_height()) // 2
            screen.blit(sprite, (sx, sy))

class RemoveAnimation:
    def __init__(self, matches, duration=300):
        self.matches = list(matches)
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False

    def update(self):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
            self.finished = True

    def draw(self, screen):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
        alpha = int(255 * (1 - t))
        for row, col in self.matches:
            color = grid[row][col]
            if color in sprites:
                sprite = sprites[color].copy()
                sprite.set_alpha(alpha)
                x = MARGIN + col * CELL_SIZE + (CELL_SIZE - sprite.get_width()) // 2
                y = TOP_OFFSET + row * CELL_SIZE + (CELL_SIZE - sprite.get_height()) // 2
                screen.blit(sprite, (x, y))

class DropAnimation:
    def __init__(self, drop_info, duration=300):
        self.drop_info = drop_info
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False

    def update(self):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
            self.finished = True

    def draw(self, screen):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
        for row, col, color, start_row in self.drop_info:
            if color in sprites:
                sprite = sprites[color]
                y_offset = (start_row - row) * CELL_SIZE * (1 - t)
                x = MARGIN + col * CELL_SIZE + (CELL_SIZE - sprite.get_width()) // 2
                y = TOP_OFFSET + row * CELL_SIZE + (CELL_SIZE - sprite.get_height()) // 2 + y_offset
                screen.blit(sprite, (x, y))

class ErrorAnimation:
    def __init__(self, row, col, duration=300):
        self.row = row
        self.col = col
        self.start_time = pygame.time.get_ticks()
        self.duration = duration
        self.finished = False
        self.shake_offset = (0, 0)
        self.phase = 0

    def update(self):
        if self.finished:
            return
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
            self.finished = True
        intensity = max(0, (1 - t) * 8)
        self.shake_offset = (intensity * math.sin(t * 30), intensity * math.cos(t * 20))
        self.phase = t

    def draw(self, screen):
        if self.finished:
            return
        x = MARGIN + self.col * CELL_SIZE
        y = TOP_OFFSET + self.row * CELL_SIZE
        t = (pygame.time.get_ticks() - self.start_time) / self.duration
        if t >= 1:
            t = 1
        alpha = int(150 * (1 - t))
        flash_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        flash_surf.fill((255, 0, 0, alpha))
        screen.blit(flash_surf, (x + self.shake_offset[0], y + self.shake_offset[1]))

def add_error_animation(row, col):
    error_animations.append(ErrorAnimation(row, col))

def add_error_animation_pair(r1, c1, r2, c2):
    add_error_animation(r1, c1)
    add_error_animation(r2, c2)

# --- ГЛАВНЫЙ ЦИКЛ ---
font = pygame.font.Font(None, 36)
big_font = pygame.font.Font(None, 72)
small_font = pygame.font.Font(None, 20)

grid = create_grid()
selected = None
animations = []
error_animations = []
drag_start_cell = None
gear_rotation = 0
gear_open = False
gear_animating = False
gear_target_rotation = 0

MENU = 0
PLAYING = 1
GAME_OVER = 2
SETTINGS_MENU = 3
UPDATE_AVAILABLE = 4
EXIT_CONFIRM = 5
STATS = 6
LEVEL_COMPLETE = 7
GAME_COMPLETE = 8
LEVEL_SELECT = 9
game_state = MENU

recalculate_sizes()
has_update, local_ver, remote_ver = check_updates()
if has_update:
    game_state = UPDATE_AVAILABLE

running = True
input_active = False
input_text = ""
error_message = ""
error_timer = 0

session_time = 0
profile_btn_rect = None

while running:
    if music_loaded and not music_started:
        pygame.mixer.music.play(-1)
        music_started = True
    
    if game_state == PLAYING:
        session_time += clock.get_time() / 1000.0
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if game_state == PLAYING and score > 0:
                update_profile(score)
            running = False
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                toggle_fullscreen()
            if event.key == pygame.K_ESCAPE:
                if game_state == SETTINGS_MENU:
                    game_state = MENU
                elif game_state == STATS:
                    game_state = MENU
                elif game_state == LEVEL_COMPLETE or game_state == GAME_COMPLETE:
                    game_state = MENU
                elif game_state == LEVEL_SELECT:
                    game_state = MENU
                elif game_state == PLAYING:
                    if score > 0:
                        update_profile(score)
                    game_state = MENU
                    selected = None
                    drag_start_cell = None
                    gear_open = False
                    gear_target_rotation = 0
                    gear_rotation = 0
                    gear_animating = False
                elif game_state == UPDATE_AVAILABLE:
                    running = False
                elif game_state == EXIT_CONFIRM:
                    game_state = MENU
            if game_state == SETTINGS_MENU:
                if event.key == pygame.K_LEFT:
                    new_vol = settings.get("music_volume", 0.5) - 0.05
                    settings["music_volume"] = max(0.0, new_vol)
                    pygame.mixer.music.set_volume(settings["music_volume"])
                    save_settings(settings)
                elif event.key == pygame.K_RIGHT:
                    new_vol = settings.get("music_volume", 0.5) + 0.05
                    settings["music_volume"] = min(1.0, new_vol)
                    pygame.mixer.music.set_volume(settings["music_volume"])
                    save_settings(settings)
            if input_active:
                if event.key == pygame.K_RETURN:
                    new_name = input_text.strip()
                    if new_name:
                        if is_name_taken(new_name, exclude_id=profile["player_id"]):
                            error_message = "❌ Это имя уже занято!"
                            error_timer = 90
                        else:
                            delete_player_data(profile["player_id"])
                            profile["player_name"] = new_name
                            save_profile(profile)
                            save_player_data(profile)
                            input_active = False
                            input_text = ""
                    else:
                        input_active = False
                        input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                else:
                    input_text += event.unicode
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = pygame.mouse.get_pos()
            
            if game_state == UPDATE_AVAILABLE:
                update_btn = draw_update_notification()
                if update_btn.collidepoint(pos):
                    run_updater()
            
            elif game_state == MENU:
                if profile["player_id"] == "DEVELOPER":
                    new_btn, load_btn, profile_btn, settings_btn, exit_btn, admin_btn = draw_menu()
                    if admin_btn and admin_btn.collidepoint(pos):
                        open_admin_panel()
                else:
                    new_btn, load_btn, profile_btn, settings_btn, exit_btn = draw_menu()
                
                if new_btn.collidepoint(pos):
                    current_level = 1
                    score = 0
                    moves_left = levels.get_moves(1)
                    for key in color_counters:
                        color_counters[key] = 0
                    grid = create_grid()
                    selected = None
                    animations = []
                    error_animations = []
                    game_state = PLAYING
                    if os.path.exists(get_save_path()):
                        os.remove(get_save_path())
                elif load_btn.collidepoint(pos) and has_save():
                    data = load_game()
                    if data:
                        grid = data["grid"]
                        score = data["score"]
                        current_level = data.get("level", 1)
                        moves_left = data.get("moves", levels.get_moves(current_level))
                        color_counters = data.get("color_counters", {"blue": 0, "green": 0, "red": 0, "yellow": 0, "purple": 0})
                        selected = None
                        animations = []
                        error_animations = []
                        game_state = PLAYING
                elif profile_btn.collidepoint(pos):
                    game_state = STATS
                elif settings_btn.collidepoint(pos):
                    game_state = SETTINGS_MENU
                elif exit_btn.collidepoint(pos):
                    game_state = EXIT_CONFIRM
            
            elif game_state == STATS:
                close_btn = draw_stats_window()
                if close_btn.collidepoint(pos):
                    game_state = MENU
            
            elif game_state == EXIT_CONFIRM:
                yes_btn, no_btn = draw_exit_confirm()
                if yes_btn.collidepoint(pos):
                    running = False
                elif no_btn.collidepoint(pos):
                    game_state = MENU
            
            elif game_state == LEVEL_COMPLETE or game_state == GAME_COMPLETE:
                next_btn = draw_level_complete()
                if next_btn.collidepoint(pos):
                    if game_state == GAME_COMPLETE:
                        game_state = MENU
                    else:
                        # Переход на следующий уровень
                        current_level += 1
                        moves_left = levels.get_moves(current_level)
                        score = 0
                        for key in color_counters:
                            color_counters[key] = 0
                        grid = create_grid()
                        game_state = PLAYING
            
            elif game_state == SETTINGS_MENU:
                fs_btn, vol_btn, name_btn, back_btn = draw_settings_menu()
                if fs_btn.collidepoint(pos):
                    toggle_fullscreen()
                elif name_btn.collidepoint(pos):
                    input_active = True
                    input_text = ""
                elif back_btn.collidepoint(pos):
                    game_state = MENU
            
            elif game_state == GAME_OVER:
                restart_btn, exit_btn = draw_game_over()
                if restart_btn.collidepoint(pos):
                    # Перезапуск текущего уровня
                    moves_left = levels.get_moves(current_level)
                    score = 0
                    for key in color_counters:
                        color_counters[key] = 0
                    grid = create_grid()
                    selected = None
                    animations = []
                    error_animations = []
                    game_state = PLAYING
                    if os.path.exists(get_save_path()):
                        os.remove(get_save_path())
                elif exit_btn.collidepoint(pos):
                    game_state = EXIT_CONFIRM
            
            elif game_state == PLAYING:
                btn_size = 50
                btn_x = WIDTH - btn_size - 15
                btn_y = HEIGHT - btn_size - 15
                gear_rect = pygame.Rect(btn_x, btn_y, btn_size, btn_size)
                if gear_rect.collidepoint(pos):
                    if gear_open:
                        gear_open = False
                        gear_target_rotation = 0
                        gear_animating = True
                    else:
                        gear_open = True
                        gear_target_rotation = 360
                        gear_animating = True
                    continue
                
                if gear_open:
                    save_btn, menu_btn = draw_gear_button()
                    if save_btn and save_btn.collidepoint(pos):
                        save_game(grid, score, current_level, moves_left, color_counters)
                        running = False
                        continue
                    if menu_btn and menu_btn.collidepoint(pos):
                        if score > 0:
                            update_profile(score)
                        game_state = MENU
                        selected = None
                        drag_start_cell = None
                        gear_open = False
                        gear_target_rotation = 0
                        gear_rotation = 0
                        gear_animating = False
                        continue
                
                cell = get_cell(pos)
                if cell:
                    drag_start_cell = cell
                    selected = cell
        
        if event.type == pygame.MOUSEMOTION and game_state == PLAYING and drag_start_cell is not None:
            pos = pygame.mouse.get_pos()
            current_cell = get_cell(pos)
            if current_cell and current_cell != drag_start_cell:
                r1, c1 = drag_start_cell
                r2, c2 = current_cell
                if abs(r1-r2) + abs(c1-c2) == 1:
                    if swap_cells(r1, c1, r2, c2):
                        animations.append(SwapAnimation(r1, c1, r2, c2))
                        selected = None
                        drag_start_cell = None
                    else:
                        add_error_animation_pair(r1, c1, r2, c2)
                        selected = None
                        drag_start_cell = None
                else:
                    add_error_animation_pair(r1, c1, r2, c2)
                    selected = None
                    drag_start_cell = None
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if game_state == PLAYING:
                if drag_start_cell is not None:
                    pos = pygame.mouse.get_pos()
                    current_cell = get_cell(pos)
                    if current_cell and current_cell != drag_start_cell:
                        r1, c1 = drag_start_cell
                        r2, c2 = current_cell
                        if abs(r1-r2) + abs(c1-c2) == 1:
                            if not swap_cells(r1, c1, r2, c2):
                                add_error_animation_pair(r1, c1, r2, c2)
                            else:
                                animations.append(SwapAnimation(r1, c1, r2, c2))
                        else:
                            add_error_animation_pair(r1, c1, r2, c2)
                    drag_start_cell = None
                    selected = None

    if game_state == PLAYING:
        if not animations and not error_animations:
            matches = find_matches()
            if matches:
                points = len(matches) * 2
                score += points
                moves_left -= 1
                
                level_data = levels.get_level_data(current_level)
                if level_data["type"] == "color":
                    target_color = level_data["color"]
                    for row, col in matches:
                        if grid[row][col] == target_color:
                            color_counters[target_color] += 1
                
                animations.append(RemoveAnimation(matches))
                remove_matches(matches)
                drop_info = drop_down()
                if drop_info:
                    animations.append(DropAnimation(drop_info))
                
                if check_level_complete():
                    pass
                
                if moves_left <= 0 and game_state == PLAYING:
                    game_state = GAME_OVER
                    update_profile(score)
            elif not any(cell is not None for row in grid for cell in row):
                game_state = GAME_OVER
                update_profile(score)

        for anim in animations:
            anim.update()
        animations = [a for a in animations if not a.finished]
        
        for anim in error_animations:
            anim.update()
        error_animations = [a for a in error_animations if not a.finished]

    if game_state == MENU:
        draw_menu()
    elif game_state == SETTINGS_MENU:
        draw_settings_menu()
    elif game_state == GAME_OVER:
        draw_game_over()
    elif game_state == UPDATE_AVAILABLE:
        draw_update_notification()
    elif game_state == EXIT_CONFIRM:
        draw_exit_confirm()
    elif game_state == STATS:
        draw_stats_window()
    elif game_state == LEVEL_COMPLETE or game_state == GAME_COMPLETE:
        draw_level_complete()
    else:
        screen.fill(BLACK)
        bg = get_current_background()
        if bg:
            screen.blit(bg, (0, 0))
        draw_grid()
        for anim in error_animations:
            anim.draw(screen)
        for anim in animations:
            anim.draw(screen)
        
        score_text = font.render(f"Очки: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        draw_level_info()
        draw_gear_button()
        
        hint_text = small_font.render("F11 — полный экран", True, (100,100,100))
        screen.blit(hint_text, (WIDTH - hint_text.get_width() - 10, HEIGHT - 30))

    if input_active:
        draw_common_background()
        prompt = font.render("Введите имя:", True, WHITE)
        screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 - 60))
        input_box = pygame.Rect(WIDTH//2 - 150, HEIGHT//2 - 20, 300, 40)
        pygame.draw.rect(screen, WHITE, input_box, 2)
        text_surf = font.render(input_text + "|", True, WHITE)
        screen.blit(text_surf, (input_box.x + 10, input_box.y + 5))
        if error_message and error_timer > 0:
            err_surf = font.render(error_message, True, RED)
            screen.blit(err_surf, (WIDTH//2 - err_surf.get_width()//2, HEIGHT//2 + 40))
            error_timer -= 1
        else:
            error_message = ""
        pygame.display.flip()
        continue

    pygame.display.flip()
    clock.tick(60)

pygame.quit()