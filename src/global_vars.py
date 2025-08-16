import pygame

WIDTH, HEIGHT = 960, 600
FPS = 60
TITLE = "GOOBCUBE"


class Colors:
    BG = (14, 16, 22)
    PANEL = (24, 28, 38)
    ACCENT = (74, 126, 255)
    ACCENT_DIM = (54, 96, 210)
    TEXT = (230, 235, 245)
    MUTED = (160, 168, 184)
    HILITE = (255, 255, 255)

# Init audio first so our generated Sound matches the format
MIXER_FREQ = 44100
MIXER_SIZE = -16  # signed 16-bit
MIXER_CHANNELS = 1
MIXER_BUFFER = 512


# Fonts
def make_fonts():
    return {
        "h1": pygame.font.SysFont(None, 64),
        "h2": pygame.font.SysFont(None, 40),
        "body": pygame.font.SysFont(None, 28),
        "mono": pygame.font.SysFont("couriernew", 22)
    }


FONTS = make_fonts()

