from global_vars import WIDTH, HEIGHT, FPS, TITLE, Colors
import pygame
import math
from utils import (draw_shadowed_text, rounded_rect, WALL_BEEP)
from global_vars import FONTS
# -----------------------------
# Ball mini-game
# -----------------------------
class BallGame:
    def __init__(self):
        self.reset()
        self.return_prompt = False
        self.prompt_choice = 0  # 0 = No, 1 = Yes

    def reset(self):
        self.x = WIDTH / 2
        self.y = HEIGHT / 2
        self.vx = 220.0
        self.vy = -140.0
        self.radius = 16
        self.accel = 480.0  # pixels/s^2
        self.max_speed = 640.0
        self.wall = pygame.Rect(24, 96, WIDTH - 48, HEIGHT - 128)  # playfield

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.return_prompt = True
        elif self.return_prompt and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.prompt_choice = 1 - self.prompt_choice
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Yes => return to menu; No => close prompt
                if self.prompt_choice == 1:
                    return "return_to_menu"
                else:
                    self.return_prompt = False
            elif event.key == pygame.K_ESCAPE:
                self.return_prompt = False
        return None

    def update(self, dt):
        if self.return_prompt:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.vx -= self.accel * dt
        if keys[pygame.K_RIGHT]:
            self.vx += self.accel * dt
        if keys[pygame.K_UP]:
            self.vy -= self.accel * dt
        if keys[pygame.K_DOWN]:
            self.vy += self.accel * dt

        # Clamp speed
        speed = math.hypot(self.vx, self.vy)
        if speed > self.max_speed:
            scale = self.max_speed / max(speed, 1e-6)
            self.vx *= scale
            self.vy *= scale

        # Integrate
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Collisions with the playfield rectangle
        bounced = False
        left = self.wall.left + self.radius
        right = self.wall.right - self.radius
        top = self.wall.top + self.radius
        bottom = self.wall.bottom - self.radius

        if self.x < left:
            self.x = left
            self.vx = -self.vx
            bounced = True
        elif self.x > right:
            self.x = right
            self.vx = -self.vx
            bounced = True

        if self.y < top:
            self.y = top
            self.vy = -self.vy
            bounced = True
        elif self.y > bottom:
            self.y = bottom
            self.vy = -self.vy
            bounced = True

        if bounced:
            WALL_BEEP.play()

    def draw(self, surf):
        surf.fill(Colors.BG)
        # Header
        draw_shadowed_text(surf, "Bouncy Ball", FONTS["h1"], Colors.HILITE, (28, 20))
        draw_shadowed_text(surf, "Hold arrows to accelerate • Esc: return to main menu", FONTS["body"], Colors.MUTED, (32, 80))

        # Playfield
        rounded_rect(surf, Colors.PANEL, self.wall, radius=16)
        pygame.draw.rect(surf, Colors.ACCENT_DIM, self.wall, width=2, border_radius=16)

        # Ball
        pygame.draw.circle(surf, Colors.ACCENT, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, Colors.HILITE, (int(self.x), int(self.y)), self.radius, width=2)

        if self.return_prompt:
            self._draw_prompt(surf)

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
