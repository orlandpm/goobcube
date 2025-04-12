import pygame
import time
import mido
from mido import Message, open_output, open_input, get_output_names, get_input_names
import colorsys
import random

mido.set_backend('mido.backends.rtmidi')

CURRENT_INSTRUMENT = 81

WHITE_KEYS = {
    pygame.K_a: 60, pygame.K_s: 62, pygame.K_d: 64, pygame.K_f: 65,
    pygame.K_g: 67, pygame.K_h: 69, pygame.K_j: 71, pygame.K_k: 72
}
BLACK_KEYS = {
    pygame.K_w: 61, pygame.K_e: 63, pygame.K_t: 66, pygame.K_y: 68, pygame.K_u: 70
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

print("\n🎛 Available MIDI output ports:")
for port in get_output_names():
    print(f"  {port}")

midi_out_name = next((name for name in get_output_names() if "fluid" in name.lower()), None)
if not midi_out_name:
    raise RuntimeError("Could not find FluidSynth MIDI output device.")

midi_output = open_output(midi_out_name)
midi_output.send(Message('program_change', program=CURRENT_INSTRUMENT, channel=0))


print("\n🎛 Available MIDI input ports:")
input_names = get_input_names()
for i, name in enumerate(input_names):
    print(f"  {i+1}. {name}")
selection = input("Select MIDI input device number (or leave blank for none): ")
midi_input = None
if selection:
    idx = int(selection) - 1
    if 0 <= idx < len(input_names):
        midi_input = open_input(input_names[idx])



pygame.init()
# screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
# screen = pygame.display.set_mode((0, 0))
screen = pygame.display.set_mode((640, 480), pygame.NOFRAME)
# screen = pygame.display.set_mode((1920, 1080))#, pygame.FULLSCREEN)


info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h
# pygame.display.set_caption("MIDI Piano Fullscreen")

try:
    font = pygame.font.Font("DejaVuSans.ttf", 200)
    print("Loaded custom font: DejaVuSans.ttf")
except Exception as e:
    print("⚠️ Failed to load DejaVuSans.ttf:", e)
    try:
        font = pygame.font.Font("DejaVuSans.ttf", 200)
        print("Loaded custom font: DejaVuSans.ttf")
    except Exception as e:
        print("⚠️ Failed to load DejaVuSans.ttf:", e)
        font = None

if font is None:
    try:
        font = pygame.font.Font(None, 200)
        print("Using default Pygame font")
    except Exception as e:
        print("⚠️ Failed to load default font:", e)
        font = None

def random_color():
    return tuple(random.randint(50, 255) for _ in range(3))

goob_color = random_color()
goob_text = font.render("GOOBCUBE", True, goob_color)
goob_rect = goob_text.get_rect(center=(screen_width // 2, screen_height // 2))
goob_velocity = [20, 1 * screen_height / 400] 

KEY_TO_NOTE = {**WHITE_KEYS, **BLACK_KEYS}
active_notes = set()
clock = pygame.time.Clock()
running = True


def note_to_name_octave(n):
    name = NOTE_NAMES[n % 12]
    octave = n // 12 - 1
    return name, octave


def note_to_color(note):
    name, octave = note_to_name_octave(note)
    hue = (note % 12) / 12.0
    brightness = (octave - 1) / 7.0
    brightness = max(0.2, min(brightness, 1.0))
    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, brightness)
    return int(r * 255), int(g * 255), int(b * 255)

import threading
def midi_listener():
    while running:
        if midi_input:
            for msg in midi_input.iter_pending():
                print("🎹 Incoming MIDI message:", msg)
                if msg.type == 'note_on' and msg.velocity > 0:
                    midi_output.send(msg)
                    active_notes.add(msg.note)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    midi_output.send(Message('note_off', note=msg.note, velocity=0, channel=msg.channel))
                    active_notes.discard(msg.note)

if midi_input:
    midi_thread = threading.Thread(target=midi_listener, daemon=True)
    midi_thread.start()

try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                note = KEY_TO_NOTE.get(event.key)
                if note is not None and note not in active_notes:
                    midi_output.send(Message('note_on', note=note, velocity=127, channel=0))
                    active_notes.add(note)

            elif event.type == pygame.KEYUP:
                note = KEY_TO_NOTE.get(event.key)
                if note is not None and note in active_notes:
                    midi_output.send(Message('note_off', note=note, velocity=0, channel=0))
                    active_notes.remove(note)

            # if midi_input:
            #     for msg in midi_input.iter_pending():
            #         print("🎹 Incoming MIDI message:", msg)
            #         if msg.type == 'note_on' and msg.velocity > 0:
            #             midi_output.send(msg)
            #             active_notes.add(msg.note)
            #         elif msg.type in ('note_off', 'note_on') and msg.velocity == 0:
            #             midi_output.send(Message('note_off', note=msg.note, velocity=0, channel=msg.channel))
            #             active_notes.discard(msg.note)

# port_name = ports[int(selection) - 1]
# with mido.open_input(port_name) as port:
#     print(f"Listening on {port_name}...")
#     for msg in port:
#         print(msg)

        screen.fill((0, 0, 0))
        notes = sorted(active_notes)
        if notes:
            width_per_note = screen_width // len(notes)
            for i, note in enumerate(notes):
                color = note_to_color(note)
                rect = pygame.Rect(i * width_per_note, 0, width_per_note, screen_height)
                pygame.draw.rect(screen, color, rect)
                name, octave = note_to_name_octave(note)
                if font:
                    text = font.render(f"{name}{octave}", True, (0, 0, 0))
                    screen.blit(text, text.get_rect(center=rect.center))
                else:
                    print('font not found')
        else:
            bounced = False

            # Move goobcube
            time_elapsed = clock.tick(60) / 1000.0
            goob_rect.x += goob_velocity[0] * time_elapsed
            goob_rect.y += goob_velocity[1] * time_elapsed

            # Bounce and flag if it hit anything
            if goob_rect.left <= 0 or goob_rect.right >= screen_width:
                goob_velocity[0] *= -1
                bounced = True
            if goob_rect.top <= 0 or goob_rect.bottom >= screen_height:
                goob_velocity[1] *= -1
                bounced = True

            # If bounced, change color
            if bounced:
                goob_color = random_color()
                goob_text = font.render("GOOBCUBE", True, goob_color)

            screen.blit(goob_text, goob_rect)

        pygame.display.flip()
        clock.tick(60)

except Exception as e:
    import traceback
    traceback.print_exc()

finally:
    if midi_input:
        midi_input.close()
    midi_output.close()
    pygame.quit()
