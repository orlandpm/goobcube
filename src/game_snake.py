from global_vars import WIDTH, HEIGHT, FPS, TITLE, Colors, FONTS
import pygame
import random
from utils import draw_shadowed_text, rounded_rect, WALL_BEEP

# -----------------------------
# Snake mini-game
# -----------------------------
class SnakeGame:
    def __init__(self):
        self.cell_size = 24
        self.grid_w = (WIDTH - 48) // self.cell_size
        self.grid_h = (HEIGHT - 128) // self.cell_size
        self.wall = pygame.Rect(24, 96, self.grid_w * self.cell_size, self.grid_h * self.cell_size)
        self.music_path = "../assets/music/NES.mp3"
        self._music_loaded = False
        # self.reset()
        self.return_prompt = False
        self.prompt_choice = 0  # 0 = No, 1 = Yes

    def on_enter(self):
        # Call this when the minigame is loaded/activated
        if not self._music_loaded:
            print("Loading music in on_enter")
            pygame.mixer.music.load(self.music_path)
            self._music_loaded = True
        print("Playing music in on_enter")
        pygame.mixer.music.play(-1)

    def reset(self):
        self.direction = (1, 0)
        self.snake = [(self.grid_w // 2, self.grid_h // 2)]
        self.grow = 0
        self.spawn_food()
        self.alive = True
        self.score = 0
        self.direction_changed = False
        # Play music
        if not self._music_loaded:
            print("Loading music in reset")
            pygame.mixer.music.load(self.music_path)
            self._music_loaded = True
        print("Playing music in reset")
        pygame.mixer.music.play(-1)

    def spawn_food(self):
        while True:
            fx = random.randint(0, self.grid_w - 1)
            fy = random.randint(0, self.grid_h - 1)
            if (fx, fy) not in self.snake:
                self.food = (fx, fy)
                break

    def handle_event(self, event):
        result = None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.return_prompt = True
        elif self.return_prompt and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.prompt_choice = 1 - self.prompt_choice
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.prompt_choice == 1:
                    result = "return_to_menu"
                    self.return_prompt = False
                    # Stop music when returning to menu
                    print("Stopping music in handle_event (return_to_menu)")
                    pygame.mixer.music.stop()
                else:
                    self.return_prompt = False
            elif event.key == pygame.K_ESCAPE:
                self.return_prompt = False
        elif self.alive and event.type == pygame.KEYDOWN:
            if not self.direction_changed:
                if event.key == pygame.K_UP and self.direction != (0, 1):
                    self.direction = (0, -1)
                    self.direction_changed = True
                elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                    self.direction = (0, 1)
                    self.direction_changed = True
                elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                    self.direction = (-1, 0)
                    self.direction_changed = True
                elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                    self.direction = (1, 0)
                    self.direction_changed = True
        if not self.alive and event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.reset()
        return result

    def update(self, dt):
        if self.return_prompt or not self.alive:
            return
        # Move every fixed time step
        if not hasattr(self, "move_timer"):
            self.move_timer = 0.0
        self.move_timer += dt
        move_interval = 0.13
        if self.move_timer >= move_interval:
            self.move_timer -= move_interval
            self._move_snake()
            self.direction_changed = False  # Reset after each move

    def _move_snake(self):
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)
        # Check wall collision
        if (new_head[0] < 0 or new_head[0] >= self.grid_w or
            new_head[1] < 0 or new_head[1] >= self.grid_h or
            new_head in self.snake):
            self.alive = False
            WALL_BEEP.play()
            return
        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.grow += 1
            self.score += 1
            WALL_BEEP.play()
            self.spawn_food()
        if self.grow > 0:
            self.grow -= 1
        else:
            self.snake.pop()

    def draw(self, surf):
        surf.fill(Colors.BG)
        # Header
        draw_shadowed_text(surf, "Snake", FONTS["h1"], Colors.HILITE, (28, 20))
        draw_shadowed_text(surf, "Arrows: move • Esc: return to main menu", FONTS["body"], Colors.MUTED, (32, 80))
        draw_shadowed_text(surf, f"Score: {self.score}", FONTS["body"], Colors.ACCENT, (WIDTH - 180, 20))

        # Playfield
        rounded_rect(surf, Colors.PANEL, self.wall, radius=16)
        pygame.draw.rect(surf, Colors.ACCENT_DIM, self.wall, width=2, border_radius=16)

        # Draw food
        fx, fy = self.food
        food_rect = pygame.Rect(
            self.wall.x + fx * self.cell_size,
            self.wall.y + fy * self.cell_size,
            self.cell_size, self.cell_size
        )
        pygame.draw.rect(surf, Colors.ACCENT, food_rect, border_radius=8)

        # Draw snake
        for i, (sx, sy) in enumerate(self.snake):
            snake_rect = pygame.Rect(
                self.wall.x + sx * self.cell_size,
                self.wall.y + sy * self.cell_size,
                self.cell_size, self.cell_size
            )
            color = Colors.HILITE if i == 0 else Colors.ACCENT_DIM
            pygame.draw.rect(surf, color, snake_rect, border_radius=8)
            pygame.draw.rect(surf, Colors.ACCENT, snake_rect, width=2, border_radius=8)

        if self.return_prompt:
            self._draw_prompt(surf)
        elif not self.alive:
            self._draw_gameover(surf)

    def _draw_prompt(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surf.blit(overlay, (0, 0))

        d_w, d_h = 540, 240
        rect = pygame.Rect((WIDTH - d_w)//2, (HEIGHT - d_h)//2, d_w, d_h)
        rounded_rect(surf, (28, 32, 44), rect, radius=18)
        pygame.draw.rect(surf, Colors.ACCENT_DIM, rect, width=2, border_radius=18)

        title = "Return to main menu?"
        subtitle = "Current game will be reset."
        title_img = FONTS["h2"].render(title, True, Colors.HILITE)
        surf.blit(title_img, (rect.centerx - title_img.get_width()//2, rect.y + 24))
        sub_img = FONTS["body"].render(subtitle, True, Colors.MUTED)
        surf.blit(sub_img, (rect.centerx - sub_img.get_width()//2, rect.y + 72))

        # Buttons
        btn_w, btn_h = 160, 48
        gap = 40
        bx = rect.centerx - btn_w - gap // 2
        by = rect.y + d_h - btn_h - 28

        no_rect = pygame.Rect(bx, by, btn_w, btn_h)
        yes_rect = pygame.Rect(bx + btn_w + gap, by, btn_w, btn_h)
        rounded_rect(surf, (40, 46, 58), no_rect, radius=12)
        rounded_rect(surf, (40, 46, 58), yes_rect, radius=12)
        pygame.draw.rect(surf, (64, 72, 92), no_rect, width=2, border_radius=12)
        pygame.draw.rect(surf, (64, 72, 92), yes_rect, width=2, border_radius=12)
        no_text = FONTS["body"].render("No", True, Colors.HILITE)
        yes_text = FONTS["body"].render("Yes", True, Colors.HILITE)
        surf.blit(no_text, (no_rect.centerx - no_text.get_width() // 2, no_rect.centery - no_text.get_height() // 2))
        surf.blit(yes_text, (yes_rect.centerx - yes_text.get_width() // 2, yes_rect.centery - yes_text.get_height() // 2))

        sel_rect = yes_rect if self.prompt_choice == 1 else no_rect
        pygame.draw.rect(surf, Colors.ACCENT, sel_rect.inflate(6, 6), width=3, border_radius=14)

    def _draw_gameover(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surf.blit(overlay, (0, 0))

        d_w, d_h = 540, 240
        rect = pygame.Rect((WIDTH - d_w)//2, (HEIGHT - d_h)//2, d_w, d_h)
        rounded_rect(surf, (44, 28, 32), rect, radius=18)
        pygame.draw.rect(surf, Colors.ACCENT_DIM, rect, width=2, border_radius=18)

        title = "Game Over"
        subtitle = f"Score: {self.score} • Press Enter to restart"
        title_img = FONTS["h2"].render(title, True, Colors.HILITE)
        surf.blit(title_img, (rect.centerx - title_img.get_width()//2, rect.y + 24))
        sub_img = FONTS["body"].render(subtitle, True, Colors.ACCENT)
        surf.blit(sub_img, (rect.centerx - sub_img.get_width()//2, rect.y + 72))