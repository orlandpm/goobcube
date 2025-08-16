from global_vars import WIDTH, HEIGHT, FPS, TITLE, Colors, FONTS
import pygame
import time
import mido
from mido import Message, open_output, open_input, get_output_names, get_input_names
import colorsys
import random
import threading
from utils import draw_shadowed_text, rounded_rect, WALL_BEEP  # prompt visuals consistent with other games

# -----------------------------
# Piano/MIDI mini-game
# -----------------------------
class PianoMidiGame:
    def __init__(self):
        # ---- Visuals/state (kept the same look/feel as your script) ----
        self.screen_width = WIDTH
        self.screen_height = HEIGHT
        self.font_size = self.screen_height // 5
        self.font = None
        self._load_font()  # Try DejaVuSans.ttf, then default

        self.goob_color = self._random_color()
        self.goob_text = self._render_goob(self.goob_color)
        self.goob_rect = self.goob_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.goob_velocity = [100, 100]  # px/s

        # Keyboard mappings
        self.WHITE_KEYS = {
            pygame.K_a: 48, pygame.K_s: 50, pygame.K_d: 52, pygame.K_f: 53,
            pygame.K_g: 55, pygame.K_h: 57, pygame.K_j: 59, pygame.K_k: 60,
            pygame.K_l: 62, pygame.K_SEMICOLON: 64, pygame.K_QUOTE: 65
        }
        self.BLACK_KEYS = {
            pygame.K_w: 49, pygame.K_e: 51, pygame.K_t: 54, pygame.K_y: 56,
            pygame.K_u: 58, pygame.K_o: 61, pygame.K_p: 63
        }
        self.KEY_TO_NOTE = {**self.WHITE_KEYS, **self.BLACK_KEYS}

        self.NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        self.active_notes = set()

        # Keyboard geometry (computed in draw)
        self.white_keys_order = [48, 50, 52, 53, 55, 57, 59, 60, 62, 64, 65, 67, 69, 71, 72]  # C3..C5
        self.black_keys_map = {
            49: 0.5, 51: 1.5, 54: 3.5, 56: 4.5, 58: 5.5, 61: 7.5, 63: 8.5, 66: 10.5, 68: 11.5, 70: 12.5
        }

        # Timers
        self.last_note_time = time.time()
        self._clock = pygame.time.Clock()

        # ---- Mini-game common UI (return prompt) ----
        self.return_prompt = False
        self.prompt_choice = 0  # 0=No, 1=Yes

        # ---- MIDI setup ----
        mido.set_backend('mido.backends.rtmidi')
        self.CURRENT_INSTRUMENT = 80
        self.midi_output = None
        self.midi_input = None
        self._thread = None
        self._thread_running = False
        self._init_midi()

    # ---------- Lifecycle ----------

    def on_enter(self):
        # Start/ensure MIDI listener
        if (self.midi_input is not None) and not self._thread_running:
            self._thread_running = True
            self._thread = threading.Thread(target=self._midi_listener, daemon=True)
            self._thread.start()
        # Make sure any stuck notes are off when entering
        self._all_notes_off()

    def reset(self):
        # Keep visuals exactly as before; just re-center the text and clear notes
        self.goob_color = self._random_color()
        self.goob_text = self._render_goob(self.goob_color)
        self.goob_rect = self.goob_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.goob_velocity = [100, 100]
        self.active_notes.clear()
        self._all_notes_off()

    # ---------- Input handling ----------

    def handle_event(self, event):
        result = None
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # Open return prompt (don’t immediately exit)
            self.return_prompt = True

        elif self.return_prompt and event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                self.prompt_choice = 1 - self.prompt_choice
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.prompt_choice == 1:
                    # Confirm return to menu
                    self.return_prompt = False
                    self._all_notes_off()
                    result = "return_to_menu"
                else:
                    self.return_prompt = False
            elif event.key == pygame.K_ESCAPE:
                self.return_prompt = False

        else:
            # Normal controls (preserve original behavior)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.CURRENT_INSTRUMENT = (self.CURRENT_INSTRUMENT + 1) % 128
                    self._program_change(self.CURRENT_INSTRUMENT)
                    self._preview_note(60, 0.1)
                    print(f"🎵 MIDI Instrument changed to {self.CURRENT_INSTRUMENT}")
                elif event.key == pygame.K_DOWN:
                    self.CURRENT_INSTRUMENT = (self.CURRENT_INSTRUMENT - 1) % 128
                    self._program_change(self.CURRENT_INSTRUMENT)
                    self._preview_note(60, 0.5)
                    print(f"🎵 MIDI Instrument changed to {self.CURRENT_INSTRUMENT}")

                note = self.KEY_TO_NOTE.get(event.key)
                if note is not None and note not in self.active_notes:
                    self._send_note_on(note)
                    self.active_notes.add(note)
                    self.last_note_time = time.time()

            elif event.type == pygame.KEYUP:
                note = self.KEY_TO_NOTE.get(event.key)
                if note is not None and note in self.active_notes:
                    self._send_note_off(note)
                    self.active_notes.remove(note)

        return result

    # ---------- Update / Draw ----------

    def update(self, dt):
        if self.return_prompt:
            return

        # Move the bouncing "GOOBCUBE"
        time_elapsed = self._clock.tick(60) / 1000.0  # keep original timing feel
        bounced = False

        self.goob_rect.x += int(self.goob_velocity[0] * time_elapsed)
        self.goob_rect.y += int(self.goob_velocity[1] * time_elapsed)

        white_height = int(self.screen_height * 0.4)
        # Bounce on edges (top/left/right) and top of keyboard
        if self.goob_rect.left <= 0:
            self.goob_rect.left = 0
            self.goob_velocity[0] = abs(self.goob_velocity[0])
            bounced = True
        elif self.goob_rect.right >= self.screen_width:
            self.goob_rect.right = self.screen_width
            self.goob_velocity[0] = -abs(self.goob_velocity[0])
            bounced = True
        if self.goob_rect.top <= 0:
            self.goob_rect.top = 0
            self.goob_velocity[1] = abs(self.goob_velocity[1])
            bounced = True
        elif self.goob_rect.bottom >= self.screen_height - white_height:
            self.goob_rect.bottom = self.screen_height - white_height
            self.goob_velocity[1] = -abs(self.goob_velocity[1])
            bounced = True

        if bounced:
            self.goob_color = self._random_color()
            self.goob_text = self._render_goob(self.goob_color)

    def draw(self, surf):
        # Keep visuals the same: black background, keyboard at bottom, bouncing text
        surf.fill((0, 0, 0))

        # --- Draw keyboard (as in original) ---
        white_width = self.screen_width // len(self.white_keys_order)
        white_height = int(self.screen_height * 0.4)
        black_width = int(white_width * 0.6)
        black_height = int(white_height * 0.6)

        # White keys
        for i, note in enumerate(self.white_keys_order):
            x = i * white_width
            rect = pygame.Rect(x, self.screen_height - white_height, white_width, white_height)
            color = self._note_to_color(note) if note in self.active_notes else (255, 255, 255)
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(surf, (0, 0, 0), rect, 2)

        # Black keys overlay
        for note, rel_pos in self.black_keys_map.items():
            x = int(rel_pos * white_width + white_width / 2 - black_width / 2)
            rect = pygame.Rect(x, self.screen_height - white_height, black_width, black_height)
            color = self._note_to_color(note) if note in self.active_notes else (0, 0, 0)
            pygame.draw.rect(surf, color, rect)
            pygame.draw.rect(surf, (50, 50, 50), rect, 1)

        # Bouncing label
        surf.blit(self.goob_text, self.goob_rect)

        # Return prompt overlay
        if self.return_prompt:
            self._draw_prompt(surf)

    # ---------- Prompt UI (same style as other games) ----------

    def _draw_prompt(self, surf):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surf.blit(overlay, (0, 0))

        d_w, d_h = 540, 240
        rect = pygame.Rect((WIDTH - d_w)//2, (HEIGHT - d_h)//2, d_w, d_h)
        rounded_rect(surf, (28, 32, 44), rect, radius=18)
        pygame.draw.rect(surf, Colors.ACCENT_DIM, rect, width=2, border_radius=18)

        title = "Return to main menu?"
        subtitle = "Current session will be reset."
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

    # ---------- MIDI helpers ----------

    def _init_midi(self):
        # Output: prefer FluidSynth; fall back to first available; else None
        out_name = next((n for n in get_output_names() if "fluid" in n.lower()), None)
        if out_name is None:
            names = get_output_names()
            out_name = names[0] if names else None
        if out_name:
            try:
                self.midi_output = open_output(out_name)
                self._program_change(self.CURRENT_INSTRUMENT)
            except Exception as e:
                print(f"⚠️ Could not open MIDI output '{out_name}': {e}")
                self.midi_output = None
        else:
            print("⚠️ No MIDI output devices available.")

        # Input: prefer microKEY; otherwise none (no blocking selection)
        in_name = next((n for n in get_input_names() if "microkey" in n.lower()), None)
        if in_name:
            try:
                self.midi_input = open_input(in_name)
            except Exception as e:
                print(f"⚠️ Could not open MIDI input '{in_name}': {e}")
                self.midi_input = None
        else:
            self.midi_input = None  # optional

    def _midi_listener(self):
        while self._thread_running:
            if self.midi_input:
                for msg in self.midi_input.iter_pending():
                    if msg.type == 'note_on' and msg.velocity > 0:
                        self._forward(msg)
                        self.active_notes.add(msg.note)
                        self.last_note_time = time.time()
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        self._send_note_off(msg.note, channel=getattr(msg, "channel", 0))
                        self.active_notes.discard(msg.note)
                    elif msg.type == 'control_change':
                        # Map CC1/CC2 to pitch wheel (like your script)
                        value = int((msg.value / 127) * 8191)
                        if msg.control in (1, 2):
                            self._send_pitchwheel(value, channel=getattr(msg, "channel", 0))
            # Light sleep to avoid busy loop
            time.sleep(0.002)

    def _forward(self, msg):
        if self.midi_output:
            try:
                self.midi_output.send(msg)
            except Exception as e:
                print("MIDI send error:", e)

    def _program_change(self, program):
        if self.midi_output:
            self._forward(Message('program_change', program=program, channel=0))

    def _preview_note(self, note, dur=0.2):
        if not self.midi_output:
            return
        try:
            self._forward(Message('note_on', note=note, velocity=127, channel=0))
            # Non-blocking-ish preview using short sleep (keeps visuals unchanged)
            time.sleep(max(0.01, dur))
        finally:
            self._forward(Message('note_off', note=note, velocity=0, channel=0))

    def _send_note_on(self, note, velocity=127, channel=0):
        if self.midi_output:
            self._forward(Message('note_on', note=note, velocity=velocity, channel=channel))

    def _send_note_off(self, note, channel=0):
        if self.midi_output:
            self._forward(Message('note_off', note=note, velocity=0, channel=channel))

    def _send_pitchwheel(self, value, channel=0):
        if self.midi_output:
            self._forward(Message('pitchwheel', pitch=value, channel=channel))

    def _all_notes_off(self):
        if not self.midi_output:
            return
        try:
            # CC 123 (All Notes Off) is not universally honored; send explicit offs too
            for n in list(self.active_notes):
                self._send_note_off(n)
            self.active_notes.clear()
            self._forward(Message('control_change', control=123, value=0, channel=0))
        except Exception:
            pass

    # ---------- Utility: visuals/color ----------

    def _random_color(self):
        return tuple(random.randint(50, 255) for _ in range(3))

    def _render_goob(self, color):
        if self.font is None:
            # Fallback to any body font available
            return FONTS["h1"].render("GOOBCUBE", True, color)
        return self.font.render("GOOBCUBE", True, color)

    def _load_font(self):
        try:
            self.font = pygame.font.Font("DejaVuSans.ttf", self.font_size)
        except Exception:
            try:
                self.font = pygame.font.Font(None, self.font_size)
            except Exception:
                self.font = None

    def _note_to_name_octave(self, n):
        name = self.NOTE_NAMES[n % 12]
        octave = n // 12 - 1
        return name, octave

    def _note_to_color(self, note):
        # Same HSV mapping as your script
        name, octave = self._note_to_name_octave(note)
        hue = (note % 12) / 12.0
        brightness = ((octave - 1) / 7.0) / 2
        brightness = 0.5 + max(0.1, min(brightness, 5.0))
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, brightness)
        return int(r * 255), int(g * 255), int(b * 255)

    # ---------- Optional cleanup (if you ever need it) ----------
    def close(self):
        # Stop listener thread
        self._thread_running = False
        # Ensure notes are off
        self._all_notes_off()
        try:
            if self.midi_input:
                self.midi_input.close()
        except Exception:
            pass
        try:
            if self.midi_output:
                self.midi_output.close()
        except Exception:
            pass
