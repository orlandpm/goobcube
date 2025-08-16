import pygame
import random
from global_vars import WIDTH, HEIGHT, FPS, Colors, FONTS
from utils import draw_shadowed_text, rounded_rect, WALL_BEEP

class PongGame:
    def __init__(self):
        self.paddle_w, self.paddle_h = 18, 100
        self.ball_size = 20
        self.paddle_speed = 320
        self.ball_speed = 320
        self.reset()
        self.return_prompt = False
        self.prompt_choice = 0

    def reset(self):
        self.p1_y = HEIGHT // 2 - self.paddle_h // 2
        self.p2_y = HEIGHT // 2 - self.paddle_h // 2
        self.ball_x = WIDTH // 2 - self.ball_size // 2
        self.ball_y = HEIGHT // 2 - self.ball_size // 2
        angle = random.choice([random.uniform(-0.3, 0.3), random.uniform(2.8, 3.4)])
        self.ball_dx = self.ball_speed * (1 if random.random() < 0.5 else -1)
        self.ball_dy = self.ball_speed * random.uniform(-0.5, 0.5)
        self.score = [0, 0]
        self.alive = True
        self.return_prompt = False  # Clear exit menu flag
        self.prompt_choice = 0      # Reset prompt selection

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
                else:
                    self.return_prompt = False
            elif event.key == pygame.K_ESCAPE:
                self.return_prompt = False
        elif not self.alive and event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.reset()
        return result

    def update(self, dt, keys=None):
        if self.return_prompt or not self.alive:
            return
        # Player 1 controls (W/S)
        if keys:
            if keys[pygame.K_w]:
                self.p1_y -= self.paddle_speed * dt
            if keys[pygame.K_s]:
                self.p1_y += self.paddle_speed * dt
        # Player 2 controls (Up/Down)
            if keys[pygame.K_UP]:
                self.p2_y -= self.paddle_speed * dt
            if keys[pygame.K_DOWN]:
                self.p2_y += self.paddle_speed * dt
        self.p1_y = max(0, min(HEIGHT - self.paddle_h, self.p1_y))
        self.p2_y = max(0, min(HEIGHT - self.paddle_h, self.p2_y))

        # Move ball
        self.ball_x += self.ball_dx * dt
        self.ball_y += self.ball_dy * dt

        # Ball collision with top/bottom
        if self.ball_y <= 0 or self.ball_y + self.ball_size >= HEIGHT:
            self.ball_dy *= -1
            WALL_BEEP.play()

        # Ball collision with paddles
        ball_rect = pygame.Rect(self.ball_x, self.ball_y, self.ball_size, self.ball_size)
        p1_rect = pygame.Rect(32, self.p1_y, self.paddle_w, self.paddle_h)
        p2_rect = pygame.Rect(WIDTH - 32 - self.paddle_w, self.p2_y, self.paddle_w, self.paddle_h)
        if ball_rect.colliderect(p1_rect) and self.ball_dx < 0:
            self.ball_dx *= -1
            self.ball_x = p1_rect.right
            WALL_BEEP.play()
        if ball_rect.colliderect(p2_rect) and self.ball_dx > 0:
            self.ball_dx *= -1
            self.ball_x = p2_rect.left - self.ball_size
            WALL_BEEP.play()

        # Ball out of bounds
        if self.ball_x < 0:
            self.score[1] += 1
            self.alive = False
        elif self.ball_x > WIDTH:
            self.score[0] += 1
            self.alive = False

    def draw(self, surf):
        surf.fill(Colors.BG)
        draw_shadowed_text(surf, "Pong", FONTS["h1"], Colors.HILITE, (28, 20))
        draw_shadowed_text(surf, "W/S: left paddle • Up/Down: right paddle • Esc: menu", FONTS["body"], Colors.MUTED, (32, 80))
        draw_shadowed_text(surf, f"{self.score[0]} : {self.score[1]}", FONTS["h2"], Colors.ACCENT, (WIDTH//2 - 40, 20))

        # Playfield
        field_rect = pygame.Rect(24, 96, WIDTH - 48, HEIGHT - 128)
        rounded_rect(surf, Colors.PANEL, field_rect, radius=16)
        pygame.draw.rect(surf, Colors.ACCENT_DIM, field_rect, width=2, border_radius=16)

        # Center line
        for y in range(96, HEIGHT - 128, 32):
            pygame.draw.rect(surf, Colors.ACCENT_DIM, (WIDTH//2 - 4, y, 8, 16), border_radius=4)

        # Paddles
        pygame.draw.rect(surf, Colors.HILITE, (32, self.p1_y, self.paddle_w, self.paddle_h), border_radius=8)
        pygame.draw.rect(surf, Colors.HILITE, (WIDTH - 32 - self.paddle_w, self.p2_y, self.paddle_w, self.paddle_h), border_radius=8)

        # Ball
        pygame.draw.rect(surf, Colors.ACCENT, (self.ball_x, self.ball_y, self.ball_size, self.ball_size), border_radius=10)

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
        title = "Point Scored!"
        subtitle = f"{self.score[0]} : {self.score[1]} • Press Enter to continue"
        title_img = FONTS["h2"].render(title, True, Colors.HILITE)
        surf.blit(title_img, (rect.centerx - title_img.get_width()//2, rect.y + 24))
        sub_img = FONTS["body"].render(subtitle, True, Colors.ACCENT)
        surf.blit(sub_img, (rect.centerx - sub_img.get_width()//2, rect.y + 72)
        )
