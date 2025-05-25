import pygame
import time
import mido
from mido import Message, open_output, open_input, get_output_names, get_input_names
import colorsys
import random

mido.set_backend('mido.backends.rtmidi')

CURRENT_INSTRUMENT = 80

WHITE_KEYS = {
    pygame.K_a: 48, pygame.K_s: 50, pygame.K_d: 52, pygame.K_f: 53,
    pygame.K_g: 55, pygame.K_h: 57, pygame.K_j: 59, pygame.K_k: 60,
    pygame.K_l: 62, pygame.K_SEMICOLON: 64, pygame.K_QUOTE: 65
}
BLACK_KEYS = {
    pygame.K_w: 49, pygame.K_e: 51, pygame.K_t: 54, pygame.K_y: 56,
    pygame.K_u: 58, pygame.K_o: 61, pygame.K_p: 63
}

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']



midi_out_name = next((name for name in get_output_names() if "fluid" in name.lower()), None)
if not midi_out_name:
    raise RuntimeError("Could not find FluidSynth MIDI output device.")

midi_output = open_output(midi_out_name)
midi_output.send(Message('program_change', program=CURRENT_INSTRUMENT, channel=0))


# by default select first MIDI input device containing "microKEY"
# otherwise show selection menu

input_names = get_input_names()
midi_input_name = next((name for name in input_names if "microkey" in name.lower()), None)
if midi_input_name:
    midi_input = open_input(midi_input_name)
else:
    print("\n🎛 Available MIDI output ports:")
    for port in get_output_names():
        print(f"  {port}")

    print("\n🎛 Available MIDI input ports:")
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
# screen = pygame.display.set_mode((640, 480))
screen = pygame.display.set_mode((640, 480), pygame.FULLSCREEN)


info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h
font_size = screen_height // 5

try:
    font = pygame.font.Font("DejaVuSans.ttf", font_size)
    print("Loaded custom font: DejaVuSans.ttf")
except Exception as e:
    # print("⚠️ Failed to load DejaVuSans.ttf:", e)
    try:
        font = pygame.font.Font("DejaVuSans.ttf", font_size)
        print("Loaded custom font: DejaVuSans.ttf")
    except Exception as e:
        # print("⚠️ Failed to load DejaVuSans.ttf:", e)
        font = None

if font is None:
    try:
        font = pygame.font.Font(None, font_size)
        # print("Using default Pygame font")
    except Exception as e:
        # print("⚠️ Failed to load default font:", e)
        font = None

def random_color():
    return tuple(random.randint(50, 255) for _ in range(3))


goob_color = random_color()
goob_text = font.render("GOOBCUBE", True, goob_color)
goob_rect = goob_text.get_rect(center=(screen_width // 2, screen_height // 2))
goob_velocity = [100,100] #[screen_height/5, screen_width/5] 

KEY_TO_NOTE = {**WHITE_KEYS, **BLACK_KEYS}
active_notes = set()
clock = pygame.time.Clock()
running = True

last_note_time = time.time()  # Track the last time a note was pressed

def note_to_name_octave(n):
    name = NOTE_NAMES[n % 12]
    octave = n // 12 - 1
    return name, octave


def note_to_color(note):
    name, octave = note_to_name_octave(note)
    hue = (note % 12) / 12.0
    brightness = ((octave - 1) / 7.0) / 2
    brightness = 0.5 + max(0.1, min(brightness, 5.0))

    r, g, b = colorsys.hsv_to_rgb(hue, 1.0, brightness)
    return int(r * 255), int(g * 255), int(b * 255)

import threading
def midi_listener():
    while running:
        if midi_input:
            for msg in midi_input.iter_pending():
                # print("🎹 Incoming MIDI message:", msg)
                if msg.type == 'note_on' and msg.velocity > 0:
                    midi_output.send(msg)
                    active_notes.add(msg.note)
                    global last_note_time
                    last_note_time = time.time()  # Update last note time
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    midi_output.send(Message('note_off', note=msg.note, velocity=0, channel=msg.channel))
                    active_notes.discard(msg.note)
                elif msg.type == 'control_change':
                    value = msg.value
                    # value is 0-127, scale to integer -8192..8191
                    value = int((value / 127) * 8191)
                    # print('pitchwheel value', value)
                    if msg.control == 1:  # Pitch bend up
                        midi_output.send(Message('pitchwheel', pitch=value, channel=msg.channel))
                    elif msg.control == 2:  # Pitch bend down
                        midi_output.send(Message('pitchwheel', pitch=value, channel=msg.channel))

if midi_input:
    midi_thread = threading.Thread(target=midi_listener, daemon=True)
    midi_thread.start()

value = 64  # Initialize pitch bend value

try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_UP:
                    CURRENT_INSTRUMENT = (CURRENT_INSTRUMENT + 1) % 128  # Increment instrument
                    midi_output.send(Message('program_change', program=CURRENT_INSTRUMENT, channel=0))
                    midi_output.send(Message('note_on', note=60, velocity=127, channel=0))
                    midi_output.send(Message('note_off', note=60, velocity=0, channel=0))
                    print(f"🎵 MIDI Instrument changed to {CURRENT_INSTRUMENT}")
                elif event.key == pygame.K_DOWN:
                    CURRENT_INSTRUMENT = (CURRENT_INSTRUMENT - 1) % 128  # Decrement instrument
                    midi_output.send(Message('program_change', program=CURRENT_INSTRUMENT, channel=0))
                    # play middle c for half a second
                    midi_output.send(Message('note_on', note=60, velocity=127, channel=0))
                    time.sleep(0.5)
                    midi_output.send(Message('note_off', note=60, velocity=0, channel=0))
                    print(f"🎵 MIDI Instrument changed to {CURRENT_INSTRUMENT}")
                note = KEY_TO_NOTE.get(event.key)
                if note is not None and note not in active_notes:
                    midi_output.send(Message('note_on', note=note, velocity=127, channel=0))
                    active_notes.add(note)
                    last_note_time = time.time()  # Update last note time

            elif event.type == pygame.KEYUP:
                note = KEY_TO_NOTE.get(event.key)
                if note is not None and note in active_notes:
                    midi_output.send(Message('note_off', note=note, velocity=0, channel=0))
                    active_notes.remove(note)

        screen.fill((0, 0, 0))

        if True:
            # Draw keyboard
            white_keys_order = [48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72]  # C3 to C5
            black_keys_map = {
                49: 0.5, 51: 1.5, 54: 3.5, 56: 4.5, 58: 5.5, 61: 7.5, 63: 8.5, 66: 10.5, 68: 11.5, 70: 12.5  # relative to white keys
            }

            # Dynamically calculate key sizes to fit the screen
            white_width = screen_width // len(white_keys_order)
            white_height = int(screen_height * 0.4)  # Reduce height to fit better
            black_width = int(white_width * 0.6)  # Black keys are narrower
            black_height = int(white_height * 0.6)

            # Draw white keys
            for i, note in enumerate(white_keys_order):
                x = i * white_width
                rect = pygame.Rect(x, screen_height - white_height, white_width, white_height)
                color = note_to_color(note) if note in active_notes else (255, 255, 255)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (0, 0, 0), rect, 2)

            # Draw black keys (overlay)
            for note, rel_pos in black_keys_map.items():
                x = int(rel_pos * white_width + white_width/2 - black_width / 2)
                rect = pygame.Rect(x, screen_height - white_height, black_width, black_height)
                color = note_to_color(note) if note in active_notes else (0, 0, 0)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, (50, 50, 50), rect, 1)

        if True:
            bounced = False

            # Move goobcube
            time_elapsed = clock.tick(60) / 1000.0
            goob_rect.x += goob_velocity[0] * time_elapsed
            goob_rect.y += goob_velocity[1] * time_elapsed

            # Bounce and flag if it hit anything
            if goob_rect.left <= 0:
                goob_velocity[0] = abs(goob_velocity[0])
                bounced = True

            elif goob_rect.right >= screen_width:
                goob_velocity[0] *= -abs(goob_velocity[0])
                bounced = True
            
            if goob_rect.top <= 0:
                goob_velocity[1] = abs(goob_velocity[1])
                bounced = True
            elif goob_rect.bottom >= screen_height-white_height:
                goob_velocity[1] *= -abs(goob_velocity[1])
                bounced = True

            # If bounced, change color
            if bounced:
                goob_color = random_color()
                goob_text = font.render("GOOBCUBE", True, goob_color)

            screen.blit(goob_text, goob_rect)

        pygame.display.flip()
        # clock.tick(60)

except Exception as e:
    import traceback
    traceback.print_exc()

finally:
    if midi_input:
        midi_input.close()
    midi_output.close()
    pygame.quit()
