from global_vars import WIDTH, HEIGHT, FPS, TITLE, Colors, FONTS
import pygame
import random
import math
from utils import draw_shadowed_text, rounded_rect, WALL_BEEP

# -----------------------------
# Asteroids mini-game
# -----------------------------
class AsteroidsGame:
    def __init__(self):
        # Playfield similar to Snake for visual consistency
        self.cell_margin = 24
        self.top_margin = 96
        self.wall = pygame.Rect(
            self.cell_margin,
            self.top_margin,
            WIDTH - 2 * self.cell_margin,
            HEIGHT - (self.top_margin + self.cell_margin)
        )

        # Audio
        self.music_path = "../assets/music/NASA beat.mp3"
        self._music_loaded = False

        # Menu prompt state
        self.return_prompt = False
        self.prompt_choice = 0  # 0 = No, 1 = Yes

        # Gameplay state
        self.alive = True
        self.score = 0
        self.lives = 3
        self.level = 1

        # Timers
        self._shot_cooldown = 0.0
        self._respawn_timer = 0.0
        self._invincible_timer = 0.0

        # Init entities
        self._rng = random.Random()
        self._rng.seed()  # system entropy
        # self.reset()

    # ---------- Lifecycle ----------

    def on_enter(self):
        if not self._music_loaded:
            try:
                pygame.mixer.music.load(self.music_path)
                self._music_loaded = True
            except Exception as e:
                print(f"Music load error: {e}")
        pygame.mixer.music.play(-1)

    def reset(self):
        # Preserve score/lives across deaths; only hard reset on game over
        self._init_player(new_life=True)
        self.bullets = []
        self.asteroids = []
        self.spawn_wave(self.level)

        self.alive = True
        self._shot_cooldown = 0.0

        # (Re)start music if needed
        if not self._music_loaded:
            try:
                pygame.mixer.music.load(self.music_path)
                self._music_loaded = True
            except Exception as e:
                print(f"Music load error: {e}")
        pygame.mixer.music.play(-1)

    # ---------- Entities ----------

    def _init_player(self, new_life=False):
        cx = self.wall.centerx
        cy = self.wall.centery
        self.ship_pos = pygame.Vector2(cx, cy)
        self.ship_vel = pygame.Vector2(0, 0)
        self.ship_angle = -90.0  # pointing up
        self.ship_radius = 14
        self._invincible_timer = 2.0 if new_life else 0.0

    def spawn_wave(self, level):
        # Spawn N asteroids around the edges, avoiding center
        self.asteroids = []
        n = 3 + level
        for _ in range(n):
            pos = self._random_edge_position(margin=32)
            vel = self._random_unit() * self._rng.uniform(40, 100)  # px/s
            size = self._rng.choice([3, 3, 2])  # favor large
            self.asteroids.append(self._make_asteroid(pos, vel, size))

    def _make_asteroid(self, pos, vel, size):
        # size: 3=large, 2=medium, 1=small
        base_radius = {3: 36, 2: 24, 1: 14}[size]
        jagginess = 0.4
        verts = []
        points = self._rng.randint(8, 12)
        for i in range(points):
            ang = (2 * math.pi) * i / points
            radius = base_radius * (1.0 + jagginess * (self._rng.random() - 0.5))
            verts.append(pygame.Vector2(math.cos(ang), math.sin(ang)) * radius)
        rot = self._rng.uniform(0, 360)
        rot_speed = self._rng.uniform(-60, 60)
        return {
            "pos": pygame.Vector2(pos),
            "vel": pygame.Vector2(vel),
            "verts": verts,
            "angle": rot,
            "rot_speed": rot_speed,
            "size": size,
        }

    # ---------- Input ----------

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
                    pygame.mixer.music.stop()
                else:
                    self.return_prompt = False
            elif event.key == pygame.K_ESCAPE:
                self.return_prompt = False
        elif self.alive and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._fire_bullet()
        if (not self.alive) and event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            # Hard restart on game over
            self.score = 0
            self.lives = 3
            self.level = 1
            self.reset()
        return result

    # ---------- Update ----------

    def update(self, dt):
        if self.return_prompt:
            return

        # Cooldowns/timers
        self._shot_cooldown = max(0.0, self._shot_cooldown - dt)
        if self._invincible_timer > 0:
            self._invincible_timer = max(0.0, self._invincible_timer - dt)

        if not self.alive:
            return

        # Keyboard state for continuous controls
        keys = pygame.key.get_pressed()
        turn_speed = 200.0  # deg/s
        thrust_acc = 220.0  # px/s^2
        friction = 0.995

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.ship_angle -= turn_speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.ship_angle += turn_speed * dt
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            forward = pygame.Vector2(math.cos(math.radians(self.ship_angle)),
                                     math.sin(math.radians(self.ship_angle)))
            self.ship_vel += forward * thrust_acc * dt

        self.ship_vel *= friction
        self.ship_pos += self.ship_vel * dt
        self._wrap_position(self.ship_pos)

        # Update asteroids
        for ast in self.asteroids:
            ast["pos"] += ast["vel"] * dt
            ast["angle"] += ast["rot_speed"] * dt
            self._wrap_position(ast["pos"])

        # Update bullets
        for b in self.bullets:
            b["pos"] += b["vel"] * dt
            b["life"] -= dt
            self._wrap_position(b["pos"])
        self.bullets = [b for b in self.bullets if b["life"] > 0]

        # Collisions
        self._handle_collisions()

        # Advance level if cleared
        if not self.asteroids and self.alive:
            self.level += 1
            self.spawn_wave(self.level)

    def _handle_collisions(self):
        # Bullet vs asteroid
        new_asteroids = []
        for ast in self.asteroids:
            hit = False
            for b in self.bullets:
                if self._point_in_asteroid(b["pos"], ast):
                    hit = True
                    b["life"] = 0  # remove bullet
                    self.score += 10 * ast["size"]
                    WALL_BEEP.play()
                    # Split asteroid
                    if ast["size"] > 1:
                        for _ in range(2):
                            vel = self._random_unit() * self._rng.uniform(80, 140)
                            child = self._make_asteroid(ast["pos"], vel, ast["size"] - 1)
                            new_asteroids.append(child)
                    break
            if not hit:
                new_asteroids.append(ast)
        self.asteroids = new_asteroids
        self.bullets = [b for b in self.bullets if b["life"] > 0]

        # Ship vs asteroid
        if self._invincible_timer <= 0:
            for ast in self.asteroids:
                if self._circle_intersect_asteroid(self.ship_pos, self.ship_radius, ast):
                    self.lives -= 1
                    WALL_BEEP.play()
                    if self.lives <= 0:
                        self.alive = False
                    else:
                        # Respawn
                        self._init_player(new_life=True)
                    break

    # ---------- Rendering ----------

    def draw(self, surf):
        surf.fill(Colors.BG)

        # Header
        draw_shadowed_text(surf, "Asteroids", FONTS["h1"], Colors.HILITE, (28, 20))
        draw_shadowed_text(
            surf,
            "Left/Right: rotate • Up: thrust • Space: fire • Esc: return",
            FONTS["body"],
            Colors.MUTED,
            (32, 80),
        )
        draw_shadowed_text(surf, f"Score: {self.score}", FONTS["body"], Colors.ACCENT, (WIDTH - 220, 20))
        draw_shadowed_text(surf, f"Lives: {self.lives}  Level: {self.level}", FONTS["body"], Colors.ACCENT, (WIDTH - 220, 48))

        # Playfield
        rounded_rect(surf, Colors.PANEL, self.wall, radius=16)
        pygame.draw.rect(surf, Colors.ACCENT_DIM, self.wall, width=2, border_radius=16)

        # Draw asteroids
        for ast in self.asteroids:
            self._draw_asteroid(surf, ast)

        # Draw bullets
        for b in self.bullets:
            p = (int(b["pos"].x), int(b["pos"].y))
            pygame.draw.circle(surf, Colors.HILITE, p, 2)

        # Draw ship (blink when invincible)
        if not self.alive:
            self._draw_gameover(surf)
        else:
            blink = (self._invincible_timer > 0) and (int(pygame.time.get_ticks() * 0.01) % 2 == 0)
            if not blink:
                self._draw_ship(surf)

        if self.return_prompt:
            self._draw_prompt(surf)

    def _draw_ship(self, surf):
        # Triangle centered on ship_pos, pointing at ship_angle
        ang = math.radians(self.ship_angle)
        tip = pygame.Vector2(math.cos(ang), math.sin(ang)) * (self.ship_radius + 6)
        left = pygame.Vector2(math.cos(ang + 2.5), math.sin(ang + 2.5)) * (self.ship_radius)
        right = pygame.Vector2(math.cos(ang - 2.5), math.sin(ang - 2.5)) * (self.ship_radius)
        pts = [
            (self.ship_pos + tip),
            (self.ship_pos + left),
            (self.ship_pos + right),
        ]
        pygame.draw.polygon(surf, Colors.HILITE, pts, width=2)

    def _draw_asteroid(self, surf, ast):
        # Transform verts by rotation & translation
        rot = math.radians(ast["angle"])
        ca, sa = math.cos(rot), math.sin(rot)
        pts = []
        for v in ast["verts"]:
            x = v.x * ca - v.y * sa
            y = v.x * sa + v.y * ca
            pts.append((ast["pos"].x + x, ast["pos"].y + y))
        pygame.draw.polygon(surf, Colors.ACCENT_DIM, pts, width=2)

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

        title = "Game Over"
        subtitle = f"Score: {self.score} • Press Enter to restart"
        title_img = FONTS["h2"].render(title, True, Colors.HILITE)
        surf.blit(title_img, (rect.centerx - title_img.get_width()//2, rect.y + 24))
        sub_img = FONTS["body"].render(subtitle, True, Colors.ACCENT)
        surf.blit(sub_img, (rect.centerx - sub_img.get_width()//2, rect.y + 72))

    # ---------- Helpers ----------

    def _fire_bullet(self):
        if self._shot_cooldown > 0.0:
            return
        # Spawn from ship nose
        ang = math.radians(self.ship_angle)
        dirv = pygame.Vector2(math.cos(ang), math.sin(ang))
        pos = self.ship_pos + dirv * (self.ship_radius + 8)
        speed = 420.0
        bullet = {
            "pos": pygame.Vector2(pos),
            "vel": dirv * speed + self.ship_vel * 0.3,
            "life": 0.9,  # seconds
        }
        self.bullets.append(bullet)
        self._shot_cooldown = 0.18
        # Optional feedback
        try:
            WALL_BEEP.play()
        except Exception:
            pass

    def _wrap_position(self, v):
        # Wrap within the inner playfield rectangle
        minx, miny = self.wall.left, self.wall.top
        maxx, maxy = self.wall.right, self.wall.bottom
        if v.x < minx: v.x = maxx - 1
        if v.x >= maxx: v.x = minx
        if v.y < miny: v.y = maxy - 1
        if v.y >= maxy: v.y = miny

    def _random_unit(self):
        ang = self._rng.uniform(0, 2 * math.pi)
        return pygame.Vector2(math.cos(ang), math.sin(ang))

    def _random_edge_position(self, margin=0):
        # Random point along the border of the playfield
        edges = ["top", "bottom", "left", "right"]
        e = self._rng.choice(edges)
        if e == "top":
            x = self._rng.uniform(self.wall.left + margin, self.wall.right - margin)
            y = self.wall.top + margin
        elif e == "bottom":
            x = self._rng.uniform(self.wall.left + margin, self.wall.right - margin)
            y = self.wall.bottom - margin
        elif e == "left":
            x = self.wall.left + margin
            y = self._rng.uniform(self.wall.top + margin, self.wall.bottom - margin)
        else:
            x = self.wall.right - margin
            y = self._rng.uniform(self.wall.top + margin, self.wall.bottom - margin)
        return pygame.Vector2(x, y)

    def _point_in_asteroid(self, p, ast):
        # Rough circle test using average radius
        center = ast["pos"]
        avg_r = sum(v.length() for v in ast["verts"]) / len(ast["verts"])
        return (p - center).length_squared() <= (avg_r * 0.9) ** 2

    def _circle_intersect_asteroid(self, c, r, ast):
        # Circle vs polygon (separating axis not needed; sampling edges is fine for this scope)
        rot = math.radians(ast["angle"])
        ca, sa = math.cos(rot), math.sin(rot)
        pts = []
        for v in ast["verts"]:
            x = v.x * ca - v.y * sa
            y = v.x * sa + v.y * ca
            pts.append(pygame.Vector2(ast["pos"].x + x, ast["pos"].y + y))
        # Quick center distance prune
        if (c - ast["pos"]).length_squared() > (max((p - ast["pos"]).length() for p in pts) + r) ** 2:
            return False
        # Edge distance check
        for i in range(len(pts)):
            a = pts[i]
            b = pts[(i + 1) % len(pts)]
            if self._dist_point_segment_sq(c, a, b) <= r * r:
                return True
        # Also check if center inside polygon (winding)
        return self._point_in_polygon(c, pts)

    def _dist_point_segment_sq(self, p, a, b):
        ab = b - a
        t = 0.0
        denom = ab.length_squared()
        if denom > 0:
            t = max(0.0, min(1.0, (p - a).dot(ab) / denom))
        proj = a + ab * t
        return (p - proj).length_squared()

    def _point_in_polygon(self, p, pts):
        # Ray cast
        x, y = p.x, p.y
        inside = False
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i].x, pts[i].y
            x2, y2 = pts[(i + 1) % n].x, pts[(i + 1) % n].y
            if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1):
                inside = not inside
        return inside
