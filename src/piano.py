import pygame
import time
import mido
from mido import Message, open_output, open_input, get_output_names, get_input_names

# 🎛 Choose your General MIDI instrument
CURRENT_INSTRUMENT = 81  # 0 = Grand Piano, 81 = Synth Lead 1 (square)

# 🎹 Define key mappings
WHITE_KEYS = {
    pygame.K_a: 60,  # C
    pygame.K_s: 62,  # D
    pygame.K_d: 64,  # E
    pygame.K_f: 65,  # F
    pygame.K_g: 67,  # G
    pygame.K_h: 69,  # A
    pygame.K_j: 71,  # B
    pygame.K_k: 72   # C
}

BLACK_KEYS = {
    pygame.K_w: 61,  # C#
    pygame.K_e: 63,  # D#
    pygame.K_t: 66,  # F#
    pygame.K_y: 68,  # G#
    pygame.K_u: 70   # A#
}

def build_key_map():
    key_map = {}
    key_map.update(WHITE_KEYS)
    key_map.update(BLACK_KEYS)
    return key_map

# 🧩 Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((400, 100))
pygame.display.set_caption("MIDI Piano (Keyboard + Controller)")

# 🔌 MIDI output device
print("\n🎛 Available MIDI output ports:")
for port in get_output_names():
    print(f"  {port}")

# Open FluidSynth or default output port
midi_out_name = next((name for name in get_output_names() if "fluid" in name.lower()), None)
if not midi_out_name:
    raise RuntimeError("Could not find FluidSynth MIDI output device.")

midi_output = open_output(midi_out_name)

# Send program change to set instrument
midi_output.send(Message('program_change', program=CURRENT_INSTRUMENT, channel=0))

# 🎛 Optional MIDI input (controller)
midi_input_name = next((name for name in get_input_names() if "midi" in name.lower()), None)
midi_input = open_input(midi_input_name) if midi_input_name else None

# 🎹 Key mapping and app state
KEY_TO_NOTE = build_key_map()
active_notes = set()
clock = pygame.time.Clock()
running = True

try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                key_name = pygame.key.name(event.key)
                note = KEY_TO_NOTE.get(event.key)
                print(f"Key pressed: {event.key} ({key_name}) -> Note ON {note}")
                if note is not None and note not in active_notes:
                    midi_output.send(Message('note_on', note=note, velocity=127, channel=0))
                    active_notes.add(note)

            elif event.type == pygame.KEYUP:
                note = KEY_TO_NOTE.get(event.key)
                print(f"Key released: {event.key} -> Note OFF {note}")
                if note is not None and note in active_notes:
                    midi_output.send(Message('note_off', note=note, velocity=0, channel=0))
                    active_notes.remove(note)

        # Handle MIDI controller input
        if midi_input and midi_input.poll():
            for msg in midi_input.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    midi_output.send(msg)
                elif msg.type in ('note_off', 'note_on') and msg.velocity == 0:
                    midi_output.send(Message('note_off', note=msg.note, velocity=0, channel=msg.channel))

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
