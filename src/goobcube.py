# goobcube.py
import math
import sys
import time
import pygame
from array import array
import random

pygame.init()

import global_vars

from global_vars import (
    WIDTH, HEIGHT, FPS, TITLE, Colors, MIXER_BUFFER, 
    MIXER_FREQ, MIXER_SIZE, MIXER_CHANNELS,
    FONTS
)
from utils import (
    lerp,
    make_beep_sound,
    rounded_rect,
    draw_shadowed_text,
    WALL_BEEP
)
from game_ball import BallGame
from game_snake import SnakeGame
from game_pong import PongGame
from game_asteroids import AsteroidsGame  # 1. Import AsteroidsGame
from game_piano import PianoMidiGame  # 1. Import PianoGame


# -----------------------------
# Basic setup
# -----------------------------

pygame.mixer.pre_init(MIXER_FREQ, MIXER_SIZE, MIXER_CHANNELS, MIXER_BUFFER)
pygame.mixer.init()

# Load menu music
MENU_MUSIC_PATH = "../assets/music/goldeneye.mp3"
pygame.mixer.music.load(MENU_MUSIC_PATH)

# Fullscreen by default, unless --windowed is supplied
windowed = "--windowed" in sys.argv
if windowed:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
else:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

SNAKE_MUSIC_PATH = "../assets/music/NES.mp3"
ASTEROIDS_MUSIC_PATH = "../assets/music/NASA beat.mp3"

# -----------------------------
# Loading animation
# -----------------------------
def loading_animation_3d(duration=1.7):
    start = time.time()
    logo_font = FONTS["h1"]
    sub_font = FONTS["body"]
    cube_size = 100
    cx, cy = WIDTH // 2, HEIGHT // 2 + 40

    # Define cube vertices (centered at origin)
    half = cube_size // 2
    vertices = [
        [-half, -half, -half],
        [ half, -half, -half],
        [ half,  half, -half],
        [-half,  half, -half],
        [-half, -half,  half],
        [ half, -half,  half],
        [ half,  half,  half],
        [-half,  half,  half],
    ]
    edges = [
        (0,1), (1,2), (2,3), (3,0),
        (4,5), (5,6), (6,7), (7,4),
        (0,4), (1,5), (2,6), (3,7)
    ]

    # Random rotation speeds (slowed down)
    rot_speed_x = 0.5 + random.random() * 0.5   # was 1.5 + random.random() * 1.5
    rot_speed_y = 0.4 + random.random() * 0.6   # was 1.0 + random.random() * 2.0
    rot_speed_z = 0.2 + random.random() * 0.3   # was 0.5 + random.random() * 1.0

    while time.time() - start < duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        t = time.time() - start
        screen.fill(Colors.BG)

        # Title (centered, more vertical spacing)
        logo_img = logo_font.render("GOOBCUBE", True, Colors.HILITE)
        draw_shadowed_text(
            screen, "GOOBCUBE", logo_font, Colors.HILITE,
            (WIDTH // 2 - logo_img.get_width() // 2, HEIGHT // 2 - 180)
        )
        draw_shadowed_text(
            screen, "booting goobcube-OS…", sub_font, Colors.MUTED,
            (WIDTH // 2 - 100, HEIGHT // 2 - 130)
        )

        # Rotation angles
        angle_x = t * rot_speed_x
        angle_y = t * rot_speed_y
        angle_z = t * rot_speed_z

        # Projected vertices
        projected = []
        for x, y, z in vertices:
            # Rotate in 3D
            # X rotation
            y, z = (y*math.cos(angle_x) - z*math.sin(angle_x),
                    y*math.sin(angle_x) + z*math.cos(angle_x))
            # Y rotation
            x, z = (x*math.cos(angle_y) + z*math.sin(angle_y),
                    -x*math.sin(angle_y) + z*math.cos(angle_y))
            # Z rotation
            x, y = (x*math.cos(angle_z) - y*math.sin(angle_z),
                    x*math.sin(angle_z) + y*math.cos(angle_z))

            # Perspective projection
            dist = 3 * half
            f = dist / (z + dist + 1e-5)  # avoid div by zero
            px, py = int(cx + x*f), int(cy + y*f)
            projected.append((px, py))

        # Draw cube edges
        for i,j in edges:
            pygame.draw.line(screen, Colors.ACCENT, projected[i], projected[j], 3)

        # Progress bar (move down for more spacing)
        bar_w, bar_h = 360, 10
        bx, by = WIDTH//2 - bar_w//2, cy + 140
        pygame.draw.rect(screen, Colors.PANEL, (bx, by, bar_w, bar_h), border_radius=6)
        linear_prog = min(max((t / duration), 0), 1)
        prog = math.sin(linear_prog * math.pi / 2)  # ease-in
        pygame.draw.rect(screen, Colors.ACCENT, (bx, by, int(bar_w * prog), bar_h), border_radius=6)

        pygame.display.flip()
        clock.tick(FPS)




def loading_animation(duration=1.7):
    start = time.time()
    logo_font = FONTS["h1"]
    sub_font = FONTS["body"]
    cube_size = 64
    cx, cy = WIDTH // 2, HEIGHT // 2 + 40

    while time.time() - start < duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        t = time.time() - start
        screen.fill(Colors.BG)

        # Title (centered, more vertical spacing)
        logo_img = logo_font.render("GOOBCUBE", True, Colors.HILITE)
        draw_shadowed_text(
            screen, "GOOBCUBE", logo_font, Colors.HILITE,
            (WIDTH // 2 - logo_img.get_width() // 2, HEIGHT // 2 - 180)
        )
        draw_shadowed_text(
            screen, "booting mini-OS…", sub_font, Colors.MUTED,
            (WIDTH // 2 - 100, HEIGHT // 2 - 130)
        )

        # Rotating “cube” (rounded square)
        angle = (t * 240) % 360
        scale = 1.0 + 0.08 * math.sin(t * 3.0)
        size = int(cube_size * scale)

        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        rounded_rect(surf, Colors.ACCENT, pygame.Rect(0, 0, size, size), radius=14)
        surf = pygame.transform.rotate(surf, angle)
        screen.blit(surf, surf.get_rect(center=(cx, cy)))

        # Progress bar (move down for more spacing)
        bar_w, bar_h = 360, 10
        bx, by = WIDTH//2 - bar_w//2, cy + 100
        pygame.draw.rect(screen, Colors.PANEL, (bx, by, bar_w, bar_h), border_radius=6)
        # Sine transformation for smooth ease-in/ease-out
        linear_prog = min(max((t / duration), 0), 1)
        prog = math.sin(linear_prog * math.pi / 2)  # 0..1, ease-in
        pygame.draw.rect(screen, Colors.ACCENT, (bx, by, int(bar_w * prog), bar_h), border_radius=6)

        pygame.display.flip()
        clock.tick(FPS)

# -----------------------------
# Menu
# -----------------------------
class Menu:
    def __init__(self):
        self.icons = self._make_icons()
        self.columns = 4
        self.icon_size = (150, 150)
        self.icon_padding = 26
        self.margin_top = 120
        self.margin_side = 64
        self.selected = 0
        self.confirm_exit = False
        self.confirm_choice = 0  # 0 = No, 1 = Yes

    def _make_icons(self):
        # Add "Asteroids" and "Piano" to the menu
        colors = [
            (86, 161, 255),  # Ball
            (126, 230, 160), # Snake
            (255, 86, 86),   # Pong (red)
            (255, 204, 86),  # Asteroids (yellow)
            (180, 120, 255), # Piano (purple)
        ]
        labels = [
            "Bouncy Ball",
            "Snake",
            "Pong",
            "Asteroids",
            "Piano"
        ]
        return [{"label": lbl, "color": col} for lbl, col in zip(labels, colors)]

    def handle_event(self, event):
        if self.confirm_exit:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    self.confirm_choice = 1 - self.confirm_choice
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.confirm_choice == 1:
                        pygame.quit(); sys.exit()
                    else:
                        self.confirm_exit = False
                elif event.key == pygame.K_ESCAPE:
                    self.confirm_exit = False
            return None

        if event.type == pygame.KEYDOWN:
            r = self.rows
            c = self.columns
            n = len(self.icons)
            row, col = divmod(self.selected, c)

            if event.key == pygame.K_RIGHT:
                if col < c - 1 and self.selected + 1 < n:
                    self.selected += 1
            elif event.key == pygame.K_LEFT:
                if col > 0:
                    self.selected -= 1
            elif event.key == pygame.K_DOWN:
                if self.selected + c < n:
                    self.selected += c
            elif event.key == pygame.K_UP:
                if self.selected - c >= 0:
                    self.selected -= c
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Launch different games based on selected icon
                if self.selected == 0:
                    return "start_ball"
                elif self.selected == 1:
                    return "start_snake"
                elif self.selected == 2:
                    return "start_pong"
                elif self.selected == 3:
                    return "start_asteroids"
                elif self.selected == 4:
                    return "start_piano"  # 2. Add piano launch
                # Add more elifs for other games if needed
            elif event.key == pygame.K_ESCAPE:
                self.confirm_exit = True
        return None

    @property
    def rows(self):
        return (len(self.icons) + self.columns - 1) // self.columns

    def draw(self, surf):
        surf.fill(Colors.BG)
        draw_shadowed_text(surf, "GOOBCUBE", FONTS["h1"], Colors.HILITE, (32, 28))
        draw_shadowed_text(surf, "Use arrows to move • Enter to launch • Esc for options", FONTS["body"], Colors.MUTED, (36, 86))

        grid_w = WIDTH - 2 * self.margin_side
        iw, ih = self.icon_size
        cols = self.columns
        total_icon_w = cols * iw + (cols - 1) * self.icon_padding
        start_x = self.margin_side + (grid_w - total_icon_w) // 2
        start_y = self.margin_top

        for idx, icon in enumerate(self.icons):
            row = idx // cols
            col = idx % cols
            x = start_x + col * (iw + self.icon_padding)
            y = start_y + row * (ih + self.icon_padding)

            rect = pygame.Rect(x, y, iw, ih)
            # Card background
            rounded_rect(surf, Colors.PANEL, rect, radius=20)
            inner = rect.inflate(-14, -14)
            rounded_rect(surf, icon["color"], inner, radius=18)

            # Label
            label_img = FONTS["body"].render(icon["label"], True, Colors.TEXT)
            surf.blit(label_img, (x + (iw - label_img.get_width()) // 2, y + ih + 8))

            # Selection ring
            if idx == self.selected:
                ring = rect.inflate(14, 14)
                pygame.draw.rect(surf, Colors.ACCENT, ring, width=4, border_radius=24)

        if self.confirm_exit:
            self._draw_confirm_dialog(surf, title="Exit GOOBCUBE?", subtitle="Unsaved fun will be lost.")

    def _draw_confirm_dialog(self, surf, title="Are you sure?", subtitle=""):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surf.blit(overlay, (0, 0))

        d_w, d_h = 520, 240
        rect = pygame.Rect((WIDTH - d_w) // 2, (HEIGHT - d_h) // 2, d_w, d_h)
        rounded_rect(surf, (28, 32, 44), rect, radius=18)
        pygame.draw.rect(surf, Colors.ACCENT_DIM, rect, width=2, border_radius=18)

        title_img = FONTS["h2"].render(title, True, Colors.HILITE)
        surf.blit(title_img, (rect.centerx - title_img.get_width() // 2, rect.y + 24))
        if subtitle:
            sub_img = FONTS["body"].render(subtitle, True, Colors.MUTED)
            surf.blit(sub_img, (rect.centerx - sub_img.get_width() // 2, rect.y + 72))

        # Buttons
        btn_w, btn_h = 160, 48
        gap = 40
        bx = rect.centerx - btn_w - gap // 2
        by = rect.y + d_h - btn_h - 28

        no_rect = pygame.Rect(bx, by, btn_w, btn_h)
        yes_rect = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)
        # No
        rounded_rect(surf, Colors.PANEL, no_rect, radius=12)
        pygame.draw.rect(surf, (64, 72, 92), no_rect, width=2, border_radius=12)
        no_text = FONTS["body"].render("No", True, Colors.HILITE)
        surf.blit(no_text, (no_rect.centerx - no_text.get_width() // 2, no_rect.centery - no_text.get_height() // 2))
        # Yes
        rounded_rect(surf, Colors.PANEL, yes_rect, radius=12)
        pygame.draw.rect(surf, (64, 72, 92), yes_rect, width=2, border_radius=12)
        yes_text = FONTS["body"].render("Yes", True, Colors.HILITE)
        surf.blit(yes_text, (yes_rect.centerx - yes_text.get_width() // 2, yes_rect.centery - yes_text.get_height() // 2))

        # Selection highlight
        sel_rect = yes_rect if self.confirm_choice == 1 else no_rect
        pygame.draw.rect(surf, Colors.ACCENT, sel_rect.inflate(6, 6), width=3, border_radius=14)

# -----------------------------
# Application state machine
# -----------------------------
class App:
    MENU = "menu"
    BALL = "ball"
    SNAKE = "snake"
    PONG = "pong"
    ASTEROIDS = "asteroids"
    PIANO = "piano"  # 3. Add piano state

    def __init__(self):
        self.state = "loading"
        self.menu = Menu()
        self.ball = BallGame()
        self.snake = SnakeGame()
        self.asteroids = AsteroidsGame()
        self.piano = PianoMidiGame()  # 4. Instantiate PianoGame

    def run(self):
        # Loading animation once
        loading_animation_3d(duration=5)
        self.state = App.MENU

        # Play menu music when menu loads
        pygame.mixer.music.load(MENU_MUSIC_PATH)
        pygame.mixer.music.play(-1)  # Loop indefinitely

        while True:
            dt = clock.tick(FPS) / 1000.0
            action = None

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if self.state == App.MENU:
                    action = self.menu.handle_event(event)
                elif self.state == App.BALL:
                    action = self.ball.handle_event(event)
                elif self.state == App.SNAKE:
                    action = self.snake.handle_event(event)
                elif self.state == App.ASTEROIDS:  # 5. Handle asteroids events
                    action = self.asteroids.handle_event(event)
                elif self.state == App.PIANO:  # 5. Handle piano events
                    action = self.piano.handle_event(event)

            if self.state == App.MENU:
                # Always reset to menu music before drawing menu
                if not pygame.mixer.music.get_busy() or pygame.mixer.music.get_pos() == -1:
                    pygame.mixer.music.load(MENU_MUSIC_PATH)
                    pygame.mixer.music.play(-1)

                if action == "start_ball":
                    pygame.mixer.music.stop()
                    self.ball.reset()
                    self.state = App.BALL
                elif action == "start_snake":
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(SNAKE_MUSIC_PATH)
                    pygame.mixer.music.play(-1)
                    self.snake.reset()
                    self.state = App.SNAKE
                elif action == "start_pong":
                    pygame.mixer.music.stop()
                    self._run_pong()
                    self.state = App.MENU
                elif action == "start_asteroids":
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(ASTEROIDS_MUSIC_PATH)
                    pygame.mixer.music.play(-1)
                    self.asteroids.reset()
                    self.state = App.ASTEROIDS
                elif action == "start_piano":
                    pygame.mixer.music.stop()
                    self.piano.reset()
                    self.state = App.PIANO
                self.menu.draw(screen)

            elif self.state == App.BALL:
                if action == "return_to_menu":
                    pygame.mixer.music.load(MENU_MUSIC_PATH)
                    pygame.mixer.music.play(-1)
                    self.state = App.MENU
                else:
                    self.ball.update(dt)
                self.ball.draw(screen)

            elif self.state == App.SNAKE:
                if action == "return_to_menu":
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(MENU_MUSIC_PATH)
                    pygame.mixer.music.play(-1)
                    self.state = App.MENU
                else:
                    self.snake.update(dt)
                self.snake.draw(screen)

            elif self.state == App.ASTEROIDS:
                if action == "return_to_menu":
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load(MENU_MUSIC_PATH)
                    pygame.mixer.music.play(-1)
                    self.state = App.MENU
                else:
                    self.asteroids.update(dt)
                self.asteroids.draw(screen)

            elif self.state == App.PIANO:
                if action == "return_to_menu":
                    pygame.mixer.music.load(MENU_MUSIC_PATH)
                    pygame.mixer.music.play(-1)
                    self.state = App.MENU
                else:
                    self.piano.update(dt)
                self.piano.draw(screen)

            pygame.display.flip()

    def _run_pong(self):
        game = PongGame()
        clock = pygame.time.Clock()
        running = True
        pygame.mixer.music.stop()
        while running:
            dt = clock.tick(FPS) / 1000.0
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                result = game.handle_event(event)
                if result == "return_to_menu":
                    running = False
                    break
            game.update(dt, keys)
            game.draw(screen)
            pygame.display.flip()
        pygame.mixer.music.load(MENU_MUSIC_PATH)
        pygame.mixer.music.play(-1)

# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    App().run()
