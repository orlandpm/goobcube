import pygame
import math
from global_vars import MIXER_FREQ
from array import array

# -----------------------------
# Helpers
# -----------------------------
def lerp(a, b, t):
    return a + (b - a) * t

def make_beep_sound(freq=880, duration=0.08, volume=0.4):
    """Generate a tiny sine beep as a pygame.Sound without numpy."""
    n_samples = int(MIXER_FREQ * duration)
    amplitude = int(32767 * volume)
    samples = array("h")
    phase = 0.0
    dphi = 2.0 * math.pi * freq / MIXER_FREQ
    for _ in range(n_samples):
        samples.append(int(amplitude * math.sin(phase)))
        phase += dphi
    return pygame.mixer.Sound(buffer=samples.tobytes())

def rounded_rect(surface, color, rect, radius=12, width=0):
    """Draw a rounded rectangle (fallback if pygame.draw has no border_radius in your version)."""
    try:
        pygame.draw.rect(surface, color, rect, width=width, border_radius=radius)
    except TypeError:
        # Simple fallback: draw normal rect
        pygame.draw.rect(surface, color, rect, width=width)

def draw_shadowed_text(surface, text, font, color, pos, shadow_offset=(2,2), shadow_color=(0,0,0)):
    x, y = pos
    shx, shy = shadow_offset
    shadow = font.render(text, True, shadow_color)
    surface.blit(shadow, (x+shx, y+shy))
    img = font.render(text, True, color)
    surface.blit(img, pos)

# Sounds
WALL_BEEP = make_beep_sound(freq=880, duration=0.06, volume=0.35)
