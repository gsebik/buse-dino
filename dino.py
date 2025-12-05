#!/usr/bin/env python3
"""
Dinosaur Game for BUSE 128x19 LED Display

A Chrome-style dinosaur jumping game for the BUSE framebuffer display.
Supports both framebuffer output and terminal test mode.

Controls:
  - Enter/PageUp: Jump / Start game
  - Space: Duck (to avoid birds)
  - Escape: Quit

Usage:
  python3 dino.py              # Framebuffer mode (default)
  python3 dino.py --terminal   # Terminal test mode
  python3 dino.py --both       # Both framebuffer and terminal
  python3 dino.py --no-duck    # Disable duck (jump only mode)
"""

import argparse
import math
import os
import random
import subprocess
import sys
import time
import wave
import struct
from select import select

try:
    from evdev import InputDevice, categorize, ecodes, list_devices
    HAS_EVDEV = True
except ImportError:
    HAS_EVDEV = False


class Sound:
    """Simple sound effects using aplay and generated WAV tones."""

    def __init__(self, enabled=True):
        self.enabled = enabled
        self.sound_dir = "/tmp/dino_sounds"
        if enabled:
            self._set_volume()
            self._init_sounds()

    def _set_volume(self):
        """Set system volume to 100%."""
        try:
            subprocess.run(["amixer", "set", "Master", "100%"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        try:
            subprocess.run(["amixer", "set", "PCM", "100%"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _init_sounds(self):
        """Generate sound effect WAV files."""
        try:
            os.makedirs(self.sound_dir, exist_ok=True)
            # Generate simple tone WAV files
            self._generate_tone("jump.wav", freq=600, duration=0.08, freq_end=900)
            self._generate_cheerful("score.wav")  # Cheerful arpeggio for points
            self._generate_milestone("milestone.wav")  # Every 100 points celebration
            self._generate_speedup("speedup.wav")  # Speed increase warning
            self._generate_gameover("gameover.wav")  # Classic game over melody
            self._generate_fanfare("start.wav")  # Game start fanfare
            # Animation sounds - more expressive
            self._generate_blink("blink.wav")  # Soft blink
            self._generate_wink("wink.wav")  # Playful wink
            self._generate_whoosh("look.wav")  # Eye movement whoosh
            self._generate_surprise("surprise.wav")  # Surprised eyes
            self._generate_sleepy("sleepy.wav")  # Drowsy sound
            self._generate_dizzy("dizzy.wav")  # Spinning dizzy
            self._generate_peek("peek.wav")  # Peek-a-boo reveal
            self._generate_hypno("hypno.wav")  # Hypnotic swirl
            self._generate_bounce("bounce.wav")  # Bouncy boing
            self._generate_nervous("nervous.wav")  # Nervous shake
            self._generate_search("search.wav")  # Searching around
            self._generate_flirt("flirt.wav")  # Flirty sound
        except Exception:
            self.enabled = False

    def _generate_tone(self, filename, freq, duration, freq_end=None, sample_rate=22050):
        """Generate a simple tone WAV file."""
        if freq_end is None:
            freq_end = freq

        filepath = os.path.join(self.sound_dir, filename)
        n_samples = int(sample_rate * duration)

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            for i in range(n_samples):
                t = i / sample_rate
                # Linear frequency sweep
                f = freq + (freq_end - freq) * (i / n_samples)
                # Generate sample with envelope
                envelope = min(1.0, min(i, n_samples - i) / (sample_rate * 0.01))
                sample = int(24000 * envelope * (((int(f * t * 2) % 2) * 2) - 1))
                wav.writeframes(struct.pack('<h', sample))

    def _generate_cheerful(self, filename, sample_rate=22050):
        """Generate a cheerful arpeggio sound for scoring."""
        filepath = os.path.join(self.sound_dir, filename)
        # Quick ascending arpeggio: C5, E5, G5
        notes = [523, 659, 784]
        note_duration = 0.04
        total_samples = int(sample_rate * note_duration * len(notes))

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            for i in range(total_samples):
                t = i / sample_rate
                note_idx = min(int(i / (sample_rate * note_duration)), len(notes) - 1)
                f = notes[note_idx]
                # Envelope for each note
                note_pos = i % int(sample_rate * note_duration)
                note_len = int(sample_rate * note_duration)
                envelope = min(1.0, min(note_pos, note_len - note_pos) / (sample_rate * 0.005))
                sample = int(24000 * envelope * (((int(f * t * 2) % 2) * 2) - 1))
                wav.writeframes(struct.pack('<h', sample))

    def _generate_gameover(self, filename, sample_rate=22050):
        """Generate a dramatic game over melody."""
        filepath = os.path.join(self.sound_dir, filename)
        # Dramatic descending game over - minor key, slower
        notes = [
            (440, 0.2),    # A4
            (415, 0.2),    # G#4
            (392, 0.2),    # G4
            (370, 0.25),   # F#4
            (0, 0.15),     # pause
            (330, 0.2),    # E4
            (311, 0.2),    # D#4
            (294, 0.25),   # D4
            (0, 0.1),      # pause
            (220, 0.5),    # A3 (long low)
            (147, 0.6),    # D3 (even lower, dramatic end)
        ]

        total_duration = sum(d for _, d in notes)
        total_samples = int(sample_rate * total_duration)

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            sample_pos = 0
            for freq, duration in notes:
                note_samples = int(sample_rate * duration)
                for i in range(note_samples):
                    t = sample_pos / sample_rate
                    if freq == 0:
                        sample = 0
                    else:
                        # Envelope with slower decay for drama
                        attack = min(1.0, i / (sample_rate * 0.015))
                        decay = max(0.2, 1.0 - (i / note_samples) * 0.6)
                        envelope = attack * decay
                        sample = int(24000 * envelope * (((int(freq * t * 2) % 2) * 2) - 1))
                    wav.writeframes(struct.pack('<h', sample))
                    sample_pos += 1

    def _generate_milestone(self, filename, sample_rate=22050):
        """Generate celebratory sound for every 100 points."""
        filepath = os.path.join(self.sound_dir, filename)
        # Triumphant ascending fanfare
        notes = [
            (523, 0.1),    # C5
            (659, 0.1),    # E5
            (784, 0.1),    # G5
            (1047, 0.25),  # C6 (high, held)
            (784, 0.08),   # G5
            (1047, 0.3),   # C6 (final flourish)
        ]

        total_duration = sum(d for _, d in notes)
        total_samples = int(sample_rate * total_duration)

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            sample_pos = 0
            for freq, duration in notes:
                note_samples = int(sample_rate * duration)
                for i in range(note_samples):
                    t = sample_pos / sample_rate
                    attack = min(1.0, i / (sample_rate * 0.008))
                    decay = max(0.4, 1.0 - (i / note_samples) * 0.4)
                    envelope = attack * decay
                    sample = int(24000 * envelope * (((int(freq * t * 2) % 2) * 2) - 1))
                    wav.writeframes(struct.pack('<h', sample))
                    sample_pos += 1

    def _generate_speedup(self, filename, sample_rate=22050):
        """Generate accelerating sound for speed increase."""
        filepath = os.path.join(self.sound_dir, filename)
        duration = 0.25
        n_samples = int(sample_rate * duration)

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            for i in range(n_samples):
                t = i / sample_rate
                progress = i / n_samples
                # Accelerating frequency sweep
                freq = 300 + (800 * progress * progress)
                envelope = min(1.0, min(i, n_samples - i) / (sample_rate * 0.02))
                sample = int(20000 * envelope * (((int(freq * t * 2) % 2) * 2) - 1))
                wav.writeframes(struct.pack('<h', sample))

    def _generate_fanfare(self, filename, sample_rate=22050):
        """Generate game start fanfare."""
        filepath = os.path.join(self.sound_dir, filename)
        notes = [
            (392, 0.12),   # G4
            (523, 0.12),   # C5
            (659, 0.15),   # E5
            (784, 0.25),   # G5
        ]

        total_duration = sum(d for _, d in notes)
        total_samples = int(sample_rate * total_duration)

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            sample_pos = 0
            for freq, duration in notes:
                note_samples = int(sample_rate * duration)
                for i in range(note_samples):
                    t = sample_pos / sample_rate
                    attack = min(1.0, i / (sample_rate * 0.01))
                    decay = max(0.5, 1.0 - (i / note_samples) * 0.3)
                    envelope = attack * decay
                    sample = int(24000 * envelope * (((int(freq * t * 2) % 2) * 2) - 1))
                    wav.writeframes(struct.pack('<h', sample))
                    sample_pos += 1

    def _generate_arpeggio(self, filename, notes, note_duration=0.08, volume=0.3, sample_rate=22050):
        """Generate an arpeggio (sequence of notes) like classic games."""
        filepath = os.path.join(self.sound_dir, filename)
        total_samples = int(sample_rate * note_duration * len(notes))

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            for i in range(total_samples):
                t = i / sample_rate
                note_idx = min(int(i / (sample_rate * note_duration)), len(notes) - 1)
                freq = notes[note_idx]
                # Classic game-style envelope per note
                note_pos = i % int(sample_rate * note_duration)
                note_len = int(sample_rate * note_duration)
                # Quick attack, gentle decay
                attack = min(1.0, note_pos / (sample_rate * 0.008))
                decay = max(0.3, 1.0 - (note_pos / note_len) * 0.5)
                envelope = attack * decay
                # Mix sine with slight square for retro feel
                tone = 0.7 * math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * freq * 2 * t)
                sample = int(24000 * volume * envelope * tone)
                wav.writeframes(struct.pack('<h', max(-32767, min(32767, sample))))

    def _generate_sweep(self, filename, start_freq, end_freq, duration, volume=0.25, sample_rate=22050):
        """Generate a frequency sweep sound."""
        filepath = os.path.join(self.sound_dir, filename)
        n_samples = int(sample_rate * duration)

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            for i in range(n_samples):
                t = i / sample_rate
                progress = i / n_samples
                freq = start_freq + (end_freq - start_freq) * progress
                envelope = min(1.0, min(i, n_samples - i) / (sample_rate * 0.015))
                tone = math.sin(2 * math.pi * freq * t)
                sample = int(24000 * volume * envelope * tone)
                wav.writeframes(struct.pack('<h', sample))

    def _generate_wobble(self, filename, base_freq, wobble_freq, duration, volume=0.25, sample_rate=22050):
        """Generate a wobbling/vibrato sound."""
        filepath = os.path.join(self.sound_dir, filename)
        n_samples = int(sample_rate * duration)

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            for i in range(n_samples):
                t = i / sample_rate
                progress = i / n_samples
                # Wobbling frequency
                freq = base_freq + 50 * math.sin(2 * math.pi * wobble_freq * t)
                envelope = (1 - progress) ** 0.8
                tone = math.sin(2 * math.pi * freq * t)
                sample = int(24000 * volume * envelope * tone)
                wav.writeframes(struct.pack('<h', sample))

    def _generate_blink(self, filename, sample_rate=22050):
        """Blink - quick descending two-note like Zelda item."""
        self._generate_arpeggio(filename, [880, 660], note_duration=0.06, volume=0.7)

    def _generate_wink(self, filename, sample_rate=22050):
        """Wink - playful three-note ascending like Mario coin."""
        self._generate_arpeggio(filename, [523, 659, 784], note_duration=0.07, volume=0.75)

    def _generate_whoosh(self, filename, sample_rate=22050):
        """Look/whoosh - sweeping sound like Sonic spin."""
        self._generate_sweep(filename, 300, 800, 0.15, volume=0.65)

    def _generate_surprise(self, filename, sample_rate=22050):
        """Surprise - dramatic rising arpeggio like Pokemon encounter."""
        self._generate_arpeggio(filename, [392, 494, 587, 784], note_duration=0.08, volume=0.8)

    def _generate_sleepy(self, filename, sample_rate=22050):
        """Sleepy - slow descending notes like lullaby."""
        self._generate_arpeggio(filename, [523, 440, 349, 294], note_duration=0.15, volume=0.6)

    def _generate_dizzy(self, filename, sample_rate=22050):
        """Dizzy - wobbling disorienting sound."""
        self._generate_wobble(filename, 400, 8, 0.4, volume=0.65)

    def _generate_peek(self, filename, sample_rate=22050):
        """Peek-a-boo - playful reveal like Mario power-up."""
        self._generate_arpeggio(filename, [262, 330, 392, 523], note_duration=0.08, volume=0.75)

    def _generate_hypno(self, filename, sample_rate=22050):
        """Hypno - mysterious wavering tones."""
        self._generate_wobble(filename, 350, 4, 0.5, volume=0.6)

    def _generate_bounce(self, filename, sample_rate=22050):
        """Bounce - springy boing like classic platformer jump."""
        self._generate_sweep(filename, 200, 600, 0.12, volume=0.75)

    def _generate_nervous(self, filename, sample_rate=22050):
        """Nervous - trembling rapid notes."""
        self._generate_arpeggio(filename, [440, 466, 440, 466, 440], note_duration=0.05, volume=0.6)

    def _generate_search(self, filename, sample_rate=22050):
        """Search - curious looking around sound."""
        self._generate_arpeggio(filename, [392, 440, 392, 349], note_duration=0.1, volume=0.65)

    def _generate_flirt(self, filename, sample_rate=22050):
        """Flirt - sweet melodic phrase like dating sim."""
        self._generate_arpeggio(filename, [523, 659, 784, 659, 523], note_duration=0.08, volume=0.7)

    def play(self, name):
        """Play a sound effect (non-blocking)."""
        if not self.enabled:
            return
        filepath = os.path.join(self.sound_dir, f"{name}.wav")
        if os.path.exists(filepath):
            try:
                subprocess.Popen(
                    ["aplay", "-q", filepath],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception:
                pass

    def speak(self, text, speed=150, pitch=50):
        """Speak text using espeak (non-blocking)."""
        if not self.enabled:
            return
        try:
            subprocess.Popen(
                ["espeak", "-s", str(speed), "-p", str(pitch), text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass


# Display configuration
WIDTH, HEIGHT = 128, 19
FB_PATH = "/dev/fb0"
BYTES_PER_ROW = WIDTH // 8
BUFFER_SIZE = BYTES_PER_ROW * HEIGHT

# Game physics (tuned for 60fps)
# Lower gravity = longer air time, higher jump velocity = higher jump
GRAVITY = 0.10
JUMP_VELOCITY = -1.7
GROUND_Y = HEIGHT - 1

# Timing
FRAME_INTERVAL = 0.016  # ~60 FPS for smoother animations
OBSTACLE_SPAWN_MIN = 1.5
OBSTACLE_SPAWN_MAX = 3.0

# Dinosaur sprite (7x9 pixels) - running frame 1
DINO_SPRITE_1 = [
    "   XXX ",
    "   XXXX",
    "   XX  ",
    "  XXXX ",
    "X XXX  ",
    "XXXX   ",
    " XX    ",
    " X X   ",
    "   X   ",
]

# Dinosaur sprite - running frame 2
DINO_SPRITE_2 = [
    "   XXX ",
    "   XXXX",
    "   XX  ",
    "  XXXX ",
    "X XXX  ",
    "XXXX   ",
    " XX    ",
    "  X    ",
    " X     ",
]

# Dinosaur jumping sprite
DINO_SPRITE_JUMP = [
    "   XXX ",
    "   XXXX",
    "   XX  ",
    "  XXXX ",
    "X XXX  ",
    "XXXX   ",
    " XX    ",
    " X X   ",
    "       ",
]

# Dinosaur ducking sprite (shorter, wider)
DINO_SPRITE_DUCK = [
    "   XXXX",
    "XXXXXX ",
    " X  X  ",
    "       ",
    "       ",
]

# Cactus sprites (various sizes) with L-shape arms
CACTUS_SMALL = [
    " X ",
    " X ",
    "XX ",
    " XX",
    " X ",
]

CACTUS_MEDIUM = [
    "  X  ",
    "  X  ",
    "X X  ",
    "XXX X",
    "  XXX",
    "  X  ",
]

CACTUS_TALL = [
    "  X  ",
    "X X  ",
    "X X  ",
    "XXX X",
    "  XXX",
    "  X  ",
    "  X  ",
]

# Bird/bat sprite (flying obstacle)
BIRD_1 = [
    "X X",
    " X ",
]

BIRD_2 = [
    " X ",
    "X X",
]

# 4x5 pixel font for text (wider and clearer)
FONT = {
    'P': [0b1110, 0b1001, 0b1110, 0b1000, 0b1000],
    'R': [0b1110, 0b1001, 0b1110, 0b1010, 0b1001],
    'E': [0b1111, 0b1000, 0b1110, 0b1000, 0b1111],
    'S': [0b0111, 0b1000, 0b0110, 0b0001, 0b1110],
    'N': [0b1001, 0b1101, 0b1011, 0b1001, 0b1001],
    'T': [0b1111, 0b0100, 0b0100, 0b0100, 0b0100],
    'O': [0b0110, 0b1001, 0b1001, 0b1001, 0b0110],
    'A': [0b0110, 0b1001, 0b1111, 0b1001, 0b1001],
    'G': [0b0111, 0b1000, 0b1011, 0b1001, 0b0110],
    'M': [0b1001, 0b1111, 0b1111, 0b1001, 0b1001],
    'V': [0b1001, 0b1001, 0b1001, 0b0110, 0b0100],
    'D': [0b1110, 0b1001, 0b1001, 0b1001, 0b1110],
    'I': [0b1110, 0b0100, 0b0100, 0b0100, 0b1110],
    'H': [0b1001, 0b1001, 0b1111, 0b1001, 0b1001],
    'C': [0b0111, 0b1000, 0b1000, 0b1000, 0b0111],
    'L': [0b1000, 0b1000, 0b1000, 0b1000, 0b1111],
    'Y': [0b1001, 0b1001, 0b0110, 0b0100, 0b0100],
    'B': [0b1110, 0b1001, 0b1110, 0b1001, 0b1110],
    'U': [0b1001, 0b1001, 0b1001, 0b1001, 0b0110],
    'W': [0b1001, 0b1001, 0b1111, 0b1111, 0b1001],
    'F': [0b1111, 0b1000, 0b1110, 0b1000, 0b1000],
    'K': [0b1001, 0b1010, 0b1100, 0b1010, 0b1001],
    'X': [0b1001, 0b0110, 0b0110, 0b0110, 0b1001],
    'Z': [0b1111, 0b0001, 0b0110, 0b1000, 0b1111],
    '!': [0b0100, 0b0100, 0b0100, 0b0000, 0b0100],
    '?': [0b0110, 0b1001, 0b0010, 0b0000, 0b0100],
    ' ': [0b0000, 0b0000, 0b0000, 0b0000, 0b0000],
    ':': [0b0000, 0b0100, 0b0000, 0b0100, 0b0000],
    '0': [0b0110, 0b1001, 0b1001, 0b1001, 0b0110],
    '1': [0b0100, 0b1100, 0b0100, 0b0100, 0b1110],
    '2': [0b0110, 0b1001, 0b0010, 0b0100, 0b1111],
    '3': [0b1110, 0b0001, 0b0110, 0b0001, 0b1110],
    '4': [0b1001, 0b1001, 0b1111, 0b0001, 0b0001],
    '5': [0b1111, 0b1000, 0b1110, 0b0001, 0b1110],
    '6': [0b0110, 0b1000, 0b1110, 0b1001, 0b0110],
    '7': [0b1111, 0b0001, 0b0010, 0b0100, 0b1000],
    '8': [0b0110, 0b1001, 0b0110, 0b1001, 0b0110],
    '9': [0b0110, 0b1001, 0b0111, 0b0001, 0b0110],
}

# 5x7 pixel large font for start screen (width=5, height=7)
FONT_LARGE = {
    'P': [
        "XXXX ",
        "X   X",
        "X   X",
        "XXXX ",
        "X    ",
        "X    ",
        "X    ",
    ],
    'L': [
        "X    ",
        "X    ",
        "X    ",
        "X    ",
        "X    ",
        "X    ",
        "XXXXX",
    ],
    'A': [
        " XXX ",
        "X   X",
        "X   X",
        "XXXXX",
        "X   X",
        "X   X",
        "X   X",
    ],
    'Y': [
        "X   X",
        "X   X",
        " X X ",
        "  X  ",
        "  X  ",
        "  X  ",
        "  X  ",
    ],
    '!': [
        "  X  ",
        "  X  ",
        "  X  ",
        "  X  ",
        "  X  ",
        "     ",
        "  X  ",
    ],
    ' ': [
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
        "     ",
    ],
}


class Display:
    """Abstract display interface supporting framebuffer and terminal output."""

    def __init__(self, use_framebuffer=True, use_terminal=False):
        self.use_framebuffer = use_framebuffer
        self.use_terminal = use_terminal
        self.buffer = bytearray(BUFFER_SIZE)
        self.prev_terminal_output = None

    def clear(self):
        """Clear the buffer."""
        for i in range(len(self.buffer)):
            self.buffer[i] = 0

    def set_pixel(self, x, y, value=1):
        """Set a pixel in the buffer."""
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            idx = y * BYTES_PER_ROW + (x // 8)
            mask = 1 << (7 - (x % 8))
            if value:
                self.buffer[idx] |= mask
            else:
                self.buffer[idx] &= ~mask

    def get_pixel(self, x, y):
        """Get pixel value from buffer."""
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            idx = y * BYTES_PER_ROW + (x // 8)
            mask = 1 << (7 - (x % 8))
            return 1 if self.buffer[idx] & mask else 0
        return 0

    def draw_sprite(self, sprite, x, y):
        """Draw a sprite (list of strings with X for pixels)."""
        for row_idx, row in enumerate(sprite):
            for col_idx, char in enumerate(row):
                if char == 'X':
                    self.set_pixel(x + col_idx, y + row_idx)

    def draw_char(self, x, y, char):
        """Draw a single character using the 4x5 font."""
        data = FONT.get(char.upper(), FONT[' '])
        for row in range(5):
            bits = data[row]
            for col in range(4):
                if bits & (1 << (3 - col)):
                    self.set_pixel(x + col, y + row)

    def draw_text(self, x, y, text):
        """Draw text at position."""
        for i, char in enumerate(text):
            self.draw_char(x + i * 5, y, char)

    def draw_centered_text(self, y, text):
        """Draw text centered horizontally."""
        total_width = len(text) * 5 - 1
        start_x = (WIDTH - total_width) // 2
        self.draw_text(start_x, y, text)

    def draw_large_char(self, x, y, char):
        """Draw a single character using the 5x7 large font."""
        data = FONT_LARGE.get(char.upper(), FONT_LARGE.get(' '))
        if data:
            for row_idx, row in enumerate(data):
                for col_idx, c in enumerate(row):
                    if c == 'X':
                        self.set_pixel(x + col_idx, y + row_idx)

    def draw_large_text(self, x, y, text):
        """Draw text using large font at position."""
        for i, char in enumerate(text):
            self.draw_large_char(x + i * 6, y, char)

    def draw_centered_large_text(self, y, text):
        """Draw large text centered horizontally."""
        total_width = len(text) * 6 - 1
        start_x = (WIDTH - total_width) // 2
        self.draw_large_text(start_x, y, text)

    def draw_line(self, x1, y1, x2, y2):
        """Draw a horizontal or vertical line."""
        if y1 == y2:  # Horizontal
            for x in range(min(x1, x2), max(x1, x2) + 1):
                self.set_pixel(x, y1)
        elif x1 == x2:  # Vertical
            for y in range(min(y1, y2), max(y1, y2) + 1):
                self.set_pixel(x1, y)

    def render(self):
        """Render the buffer to configured outputs."""
        if self.use_framebuffer:
            self._render_framebuffer()
        if self.use_terminal:
            self._render_terminal()

    def _render_framebuffer(self):
        """Write buffer to framebuffer device."""
        try:
            with open(FB_PATH, "wb") as fb:
                fb.write(self.buffer)
        except (FileNotFoundError, PermissionError) as e:
            if self.use_framebuffer and not self.use_terminal:
                print(f"Framebuffer error: {e}")
                print("Try running with --terminal for test mode")
                sys.exit(1)

    def _render_terminal(self):
        """Render buffer as ASCII art in terminal."""
        lines = []
        # Top border
        lines.append("+" + "-" * WIDTH + "+")

        for y in range(HEIGHT):
            row = "|"
            for x in range(WIDTH):
                row += "#" if self.get_pixel(x, y) else " "
            row += "|"
            lines.append(row)

        # Bottom border
        lines.append("+" + "-" * WIDTH + "+")

        output = "\n".join(lines)

        # Only redraw if changed (reduces flicker)
        if output != self.prev_terminal_output:
            # Move cursor to top-left and clear
            sys.stdout.write("\033[H\033[J")
            sys.stdout.write(output)
            sys.stdout.write("\n")
            sys.stdout.flush()
            self.prev_terminal_output = output


class InputHandler:
    """Handle keyboard input via evdev or stdin fallback."""

    def __init__(self, use_terminal_input=False):
        self.use_terminal_input = use_terminal_input
        self.keyboards = []  # Support multiple keyboards
        self.jump_pressed = False
        self.duck_pressed = False
        self.quit_requested = False
        self.old_settings = None

        if use_terminal_input:
            self._init_terminal()
        elif HAS_EVDEV:
            self._init_evdev()
        else:
            print("evdev not available, trying terminal input")
            self._init_terminal()

    def _init_evdev(self):
        """Initialize evdev keyboard input."""
        devices = list_devices()
        print(f"Found {len(devices)} input devices")

        # Try to find all suitable keyboard devices
        for path in devices:
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    # Look for device with common keys (Enter, PageUp, Space, or arrow keys)
                    has_keys = any(k in keys for k in [
                        ecodes.KEY_ENTER, ecodes.KEY_PAGEUP, ecodes.KEY_SPACE,
                        ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_A, ecodes.KEY_1
                    ])
                    if has_keys:
                        print(f"Using input device: {dev.name} ({path})")
                        try:
                            dev.grab()
                        except IOError as e:
                            print(f"  Could not grab device: {e}")
                        self.keyboards.append(dev)
            except Exception as e:
                print(f"Error checking device {path}: {e}")
                continue

        if not self.keyboards:
            # No keyboard found, try terminal if available
            if sys.stdin.isatty():
                print("No keyboard found via evdev, falling back to terminal input")
                self._init_terminal()
            else:
                print("Warning: No input device available")

    def _init_terminal(self):
        """Initialize terminal-based input."""
        self.use_terminal_input = True
        # Set terminal to raw mode for immediate key detection
        if sys.stdin.isatty():
            import tty
            import termios
            self.old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

    def poll(self):
        """Poll for input events. Returns (jump_triggered, duck_held, quit_requested)."""
        jump_triggered = False
        duck_held = False

        if self.use_terminal_input:
            # Check stdin for input
            r, _, _ = select([sys.stdin], [], [], 0)
            if r:
                char = sys.stdin.read(1)
                if char == '\n' or char == '\r':
                    jump_triggered = True
                elif char == ' ':
                    duck_held = True
                elif char == '\x1b':  # Escape sequence
                    # Read rest of escape sequence
                    seq = ''
                    while len(seq) < 5:
                        r2, _, _ = select([sys.stdin], [], [], 0.001)
                        if r2:
                            c = sys.stdin.read(1)
                            seq += c
                            if c == '~' or c.isalpha():
                                break
                        else:
                            break
                    # PageUp or any escape sequence = jump
                    jump_triggered = True
        elif self.keyboards:
            # Check all evdev keyboards
            r, _, _ = select(self.keyboards, [], [], 0)
            for kb in r:
                try:
                    for event in kb.read():
                        if event.type == ecodes.EV_KEY:
                            key_event = categorize(event)
                            # Jump keys: Enter, PageUp, Up arrow
                            if key_event.scancode in (ecodes.KEY_ENTER, ecodes.KEY_PAGEUP, ecodes.KEY_UP):
                                if key_event.keystate == key_event.key_down:
                                    jump_triggered = True
                            # Duck keys: Space, PageDown, Down arrow
                            elif key_event.scancode in (ecodes.KEY_SPACE, ecodes.KEY_PAGEDOWN, ecodes.KEY_DOWN):
                                if key_event.keystate == key_event.key_down:
                                    self.duck_pressed = True
                                elif key_event.keystate == key_event.key_up:
                                    self.duck_pressed = False
                            elif key_event.scancode == ecodes.KEY_ESC:
                                if key_event.keystate == key_event.key_down:
                                    self.quit_requested = True
                except Exception:
                    pass  # Device may have been disconnected
            duck_held = self.duck_pressed

        return jump_triggered, duck_held, self.quit_requested

    def cleanup(self):
        """Clean up input resources."""
        for kb in self.keyboards:
            try:
                kb.ungrab()
            except Exception:
                pass
        if self.old_settings and sys.stdin.isatty():
            import termios
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)
            except Exception:
                pass


class Obstacle:
    """Represents an obstacle (cactus or bird)."""

    CACTUS_TYPES = [
        ('cactus_small', CACTUS_SMALL, GROUND_Y - 5),
        ('cactus_medium', CACTUS_MEDIUM, GROUND_Y - 6),
        ('cactus_tall', CACTUS_TALL, GROUND_Y - 7),
    ]

    BIRD_TYPES = [
        ('bird_low', BIRD_1, GROUND_Y - 4),
        ('bird_high', BIRD_1, GROUND_Y - 8),
    ]

    # Birds at jumpable height for no-duck mode
    BIRD_JUMP_TYPES = [
        ('bird_jump', BIRD_1, GROUND_Y - 4),
    ]

    def __init__(self, x, include_birds=True, duck_enabled=True):
        self.x = x
        if include_birds:
            if duck_enabled:
                types = self.CACTUS_TYPES + self.BIRD_TYPES
            else:
                # No-duck mode: only low birds that can be jumped over
                types = self.CACTUS_TYPES + self.BIRD_JUMP_TYPES
        else:
            types = self.CACTUS_TYPES
        obstacle_type = random.choice(types)
        self.name = obstacle_type[0]
        self.sprite = obstacle_type[1]
        self.y = obstacle_type[2]
        self.width = max(len(row) for row in self.sprite)
        self.height = len(self.sprite)
        self.frame = 0

    def update(self, speed):
        """Move obstacle left."""
        self.x -= speed
        self.frame += 1

    def get_sprite(self):
        """Get current sprite (for animation)."""
        if 'bird' in self.name:
            return BIRD_1 if (self.frame // 6) % 2 == 0 else BIRD_2
        return self.sprite

    def get_hitbox(self):
        """Get collision hitbox (slightly smaller than sprite for fairness)."""
        return (self.x + 1, self.y + 1, self.width - 2, self.height - 2)


class Dinosaur:
    """The player-controlled dinosaur."""

    STAND_HEIGHT = 9
    DUCK_HEIGHT = 3
    DUCK_DURATION = 15  # Minimum frames to stay ducked

    def __init__(self):
        self.x = 10
        self.y = GROUND_Y - self.STAND_HEIGHT
        self.vy = 0
        self.on_ground = True
        self.ducking = False
        self.duck_timer = 0
        self.width = 5
        self.height = self.STAND_HEIGHT
        self.frame = 0

    def jump(self):
        """Make the dinosaur jump."""
        if self.on_ground and not self.ducking:
            self.vy = JUMP_VELOCITY
            self.on_ground = False

    def duck(self, is_ducking):
        """Set ducking state."""
        if self.on_ground:
            if is_ducking and not self.ducking:
                # Start ducking
                self.ducking = True
                self.duck_timer = self.DUCK_DURATION
                self.height = self.DUCK_HEIGHT
                self.y = GROUND_Y - self.DUCK_HEIGHT
            elif is_ducking and self.ducking:
                # Keep ducking, reset timer
                self.duck_timer = self.DUCK_DURATION

    def update(self):
        """Update dinosaur physics."""
        if not self.on_ground:
            self.vy += GRAVITY
            self.y += self.vy

            if self.y >= GROUND_Y - self.STAND_HEIGHT:
                self.y = GROUND_Y - self.STAND_HEIGHT
                self.vy = 0
                self.on_ground = True
                self.ducking = False
                self.duck_timer = 0
                self.height = self.STAND_HEIGHT
        else:
            self.frame += 1
            # Handle duck timer
            if self.ducking:
                self.duck_timer -= 1
                if self.duck_timer <= 0:
                    self.ducking = False
                    self.height = self.STAND_HEIGHT
                    self.y = GROUND_Y - self.STAND_HEIGHT

    def get_sprite(self):
        """Get current sprite based on state."""
        if not self.on_ground:
            return DINO_SPRITE_JUMP
        if self.ducking:
            return DINO_SPRITE_DUCK
        return DINO_SPRITE_1 if (self.frame // 6) % 2 == 0 else DINO_SPRITE_2

    def get_hitbox(self):
        """Get collision hitbox."""
        return (self.x + 1, int(self.y) + 1, self.width - 2, self.height - 2)


class Game:
    """Main game controller."""

    INITIAL_SPEED = 0.6  # Tuned for 60fps
    MAX_SPEED = 2.4  # Tuned for 60fps
    HIGH_SCORE_FILE = "/var/lib/dino_highscore"

    def __init__(self, display, input_handler, duck_enabled=True, sound_enabled=True):
        self.display = display
        self.input = input_handler
        self.duck_enabled = duck_enabled
        self.sound = Sound(enabled=sound_enabled)
        self.state = 'start'  # start, playing, gameover
        self.score = 0
        self.high_score = self._load_high_score()
        self.speed = self.INITIAL_SPEED
        self.dino = None
        self.obstacles = []
        self.next_obstacle_time = 0
        self.animation_frame = 0
        self.ground_offset = 0.0
        # Randomized scene order for start screen animations
        self.scene_order = list(range(16))
        random.shuffle(self.scene_order)
        self.current_scene_idx = -1  # Start at -1 so first scene triggers speech
        self.last_sound_frame = -1  # Track last sound to avoid repeats

    def _load_high_score(self):
        """Load high score from file."""
        try:
            with open(self.HIGH_SCORE_FILE, 'r') as f:
                return int(f.read().strip())
        except Exception:
            return 0

    def _save_high_score(self):
        """Save high score to file."""
        try:
            with open(self.HIGH_SCORE_FILE, 'w') as f:
                f.write(str(self.high_score))
        except Exception:
            pass  # Ignore errors (e.g., permission issues)

    def reset(self):
        """Reset game state for a new game."""
        self.dino = Dinosaur()
        self.obstacles = []
        self.score = 0
        self.speed = self.INITIAL_SPEED
        self.ground_offset = 0.0
        self.next_obstacle_time = time.time() + random.uniform(1.5, 2.5)

    def check_collision(self, box1, box2):
        """Check if two hitboxes collide."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)

    def update(self):
        """Update game logic."""
        jump, duck, quit_req = self.input.poll()

        if quit_req:
            return False

        if self.state == 'start':
            self.animation_frame += 1
            if jump:
                self.state = 'playing'
                self.reset()
                self.sound.play("start")
                self.sound.speak("Go!", speed=180, pitch=80)

        elif self.state == 'playing':
            if jump and self.dino.on_ground and not self.dino.ducking:
                self.sound.play("jump")
            if jump:
                self.dino.jump()

            self.dino.duck(duck)
            self.dino.update()

            # Spawn obstacles - spawn faster as score increases
            if time.time() >= self.next_obstacle_time:
                self.obstacles.append(Obstacle(WIDTH, include_birds=True, duck_enabled=self.duck_enabled))
                # Reduce spawn time as score increases (min 0.8s, max based on score)
                difficulty = min(self.score / 500, 1.0)  # 0 to 1 over 500 points
                spawn_min = OBSTACLE_SPAWN_MIN - difficulty * 0.7  # 1.5 -> 0.8
                spawn_max = OBSTACLE_SPAWN_MAX - difficulty * 1.5  # 3.0 -> 1.5
                self.next_obstacle_time = time.time() + random.uniform(spawn_min, spawn_max)

            # Update obstacles
            for obs in self.obstacles:
                obs.update(self.speed)

            # Remove off-screen obstacles and score
            new_obstacles = []
            for obs in self.obstacles:
                if obs.x + obs.width > 0:
                    new_obstacles.append(obs)
                else:
                    old_score = self.score
                    self.score += 10
                    # Play milestone sound every 100 points
                    if self.score // 100 > old_score // 100:
                        self.sound.play("milestone")
                        self.sound.speak(f"{self.score} points!", speed=160, pitch=70)
                    else:
                        self.sound.play("score")
            self.obstacles = new_obstacles

            # Check collisions
            dino_box = self.dino.get_hitbox()
            for obs in self.obstacles:
                if self.check_collision(dino_box, obs.get_hitbox()):
                    self.state = 'gameover'
                    self.animation_frame = 0
                    self.sound.play("gameover")
                    if self.score > self.high_score:
                        self.high_score = self.score
                        self._save_high_score()
                        self.sound.speak(f"Game over! New high score {self.score}!", speed=130, pitch=40)
                    else:
                        self.sound.speak(f"Game over! Score {self.score}", speed=130, pitch=40)
                    break

            # Update ground scroll
            self.ground_offset += self.speed
            if self.ground_offset >= 8:
                self.ground_offset -= 8

            # Increase difficulty gradually
            old_speed = self.speed
            self.speed = self.INITIAL_SPEED + self.score // 100 * 0.12  # Tuned for 60fps
            if self.speed > self.MAX_SPEED:
                self.speed = self.MAX_SPEED
            # Play speedup sound when speed increases
            if self.speed > old_speed and old_speed > self.INITIAL_SPEED:
                self.sound.play("speedup")

        elif self.state == 'gameover':
            self.animation_frame += 1
            if jump:
                self.state = 'playing'
                self.reset()
            # Return to start screen after 5 seconds (~300 frames at 60fps)
            elif self.animation_frame >= 300:
                self.state = 'start'
                self.animation_frame = 0
                # Reshuffle scenes for fresh start screen
                random.shuffle(self.scene_order)
                self.current_scene_idx = -1  # Reset to -1 so first scene triggers speech

        return True

    def render(self):
        """Render current game state."""
        self.display.clear()

        if self.state == 'start':
            self._render_start_screen()
        elif self.state == 'playing':
            self._render_game()
        elif self.state == 'gameover':
            self._render_gameover()

        self.display.render()

    def _play_anim_sound(self, sound_name):
        """Play animation sound only once per frame."""
        if self.animation_frame != self.last_sound_frame:
            self.sound.play(sound_name)
            self.last_sound_frame = self.animation_frame

    def _render_start_screen(self):
        """Render animated start screen with anime-style face and varied animations."""
        # Different animation scenes - 120 frames per scene at 60fps = 2 seconds each
        cycle = self.animation_frame % 120

        # Check if we need to advance to next scene
        new_scene_idx = (self.animation_frame // 120) % 16
        if new_scene_idx != self.current_scene_idx:
            self.current_scene_idx = new_scene_idx
            # Reshuffle when we complete all scenes
            if new_scene_idx == 0:
                random.shuffle(self.scene_order)
            # Speak the message for the new scene
            scene_messages = {
                0: "Press to play!",
                1: "Wake me up!",
                2: "Play with me!",
                3: "Peek a boo!",
                4: "Press to play!",
                5: "Awesome!",
                6: "I see you!",
                7: "Press to play!",
                8: "Hypnotizing!",
                9: "Boing boing!",
                10: "Interesting!",
                11: "Come play!",
                12: "So nervous!",
                13: "Where is it?",
                14: "Hey there!",
                15: "Press to play!",
            }
            scene = self.scene_order[self.current_scene_idx]
            if scene in scene_messages:
                self.sound.speak(scene_messages[scene], speed=140, pitch=60)

        big_cycle = self.scene_order[self.current_scene_idx]

        eye_left_x = 32
        eye_right_x = 88
        eye_y = 1

        def draw_anime_eye(cx, cy, state, pdx, pdy):
            if state == 'closed':
                for dx in range(-4, 5):
                    self.display.set_pixel(cx + dx, cy + 4)
                self.display.set_pixel(cx - 4, cy + 3)
                self.display.set_pixel(cx + 4, cy + 3)
            elif state == 'half':
                for dx in range(-4, 5):
                    self.display.set_pixel(cx + dx, cy + 2)
                    self.display.set_pixel(cx + dx, cy + 6)
                for dy in range(3, 6):
                    self.display.set_pixel(cx - 4, cy + dy)
                    self.display.set_pixel(cx + 4, cy + dy)
            elif state == 'wide':
                for dx in range(-4, 5):
                    self.display.set_pixel(cx + dx, cy - 1)
                    self.display.set_pixel(cx + dx, cy + 10)
                self.display.set_pixel(cx - 5, cy)
                self.display.set_pixel(cx + 5, cy)
                self.display.set_pixel(cx - 5, cy + 9)
                self.display.set_pixel(cx + 5, cy + 9)
                for dy in range(1, 9):
                    self.display.set_pixel(cx - 6, cy + dy)
                    self.display.set_pixel(cx + 6, cy + dy)
                for dx in range(2):
                    for dy in range(2):
                        self.display.set_pixel(cx + pdx + dx, cy + 4 + pdy + dy)
            elif state == 'dizzy':
                spiral = [" XXXXX ", "X     X", "X XXX X", "X X   X", "X XXXXX", "X      ", " XXXXXX"]
                for row_idx, row in enumerate(spiral):
                    for col_idx, char in enumerate(row):
                        if char == 'X':
                            self.display.set_pixel(cx - 3 + col_idx, cy + 1 + row_idx)
            elif state == 'hidden':
                pass
            else:
                for dx in range(-3, 4):
                    self.display.set_pixel(cx + dx, cy)
                self.display.set_pixel(cx - 4, cy + 1)
                self.display.set_pixel(cx + 4, cy + 1)
                for dx in range(-3, 4):
                    self.display.set_pixel(cx + dx, cy + 9)
                self.display.set_pixel(cx - 4, cy + 8)
                self.display.set_pixel(cx + 4, cy + 8)
                for dy in range(2, 8):
                    self.display.set_pixel(cx - 5, cy + dy)
                    self.display.set_pixel(cx + 5, cy + dy)
                for dx in range(-1, 3):
                    for dy in range(-1, 3):
                        self.display.set_pixel(cx + pdx + dx, cy + 4 + pdy + dy)
                self.display.set_pixel(cx + pdx - 1, cy + 3 + pdy, 0)

        left_state = 'open'
        right_state = 'open'
        pupil_dx, pupil_dy = 0, 0
        msg = ""

        if big_cycle == 0:
            # Normal looking around - with very smooth transitions
            c = cycle
            if c == 0: self._play_anim_sound("wink")

            if c in range(18, 26):
                left_state = 'closed'
                right_state = 'closed'
            elif c in range(50, 60):
                left_state = 'closed'
            elif c in range(90, 100):
                right_state = 'closed'

            # Very smooth pupil movement with many intermediate positions
            if c < 5: pupil_dx, pupil_dy = 0, 0
            elif c < 8: pupil_dx, pupil_dy = 1, 0
            elif c < 18: pupil_dx, pupil_dy = 2, 0  # Right
            elif c < 35: pupil_dx, pupil_dy = 2, 0  # Stay right
            elif c < 38: pupil_dx, pupil_dy = 1, 0
            elif c < 41: pupil_dx, pupil_dy = 0, 0
            elif c < 44: pupil_dx, pupil_dy = 0, -1
            elif c < 50: pupil_dx, pupil_dy = 0, -2  # Up
            elif c < 65: pupil_dx, pupil_dy = 0, -2  # Stay up
            elif c < 68: pupil_dx, pupil_dy = -1, -1
            elif c < 71: pupil_dx, pupil_dy = -2, -1
            elif c < 83: pupil_dx, pupil_dy = -2, 0  # Left
            elif c < 86: pupil_dx, pupil_dy = -1, 0
            elif c < 89: pupil_dx, pupil_dy = 0, 0
            elif c < 100: pupil_dx, pupil_dy = 0, 0  # Center
            elif c < 103: pupil_dx, pupil_dy = 0, 1
            elif c < 110: pupil_dx, pupil_dy = 0, 2  # Down
            elif c < 113: pupil_dx, pupil_dy = 0, 1
            else: pupil_dx, pupil_dy = 0, 0

            msg = "PRESS TO PLAY!"

        elif big_cycle == 1:
            # Sleepy then wake up
            c = cycle
            if c == 0: self._play_anim_sound("sleepy")

            if c < 38:
                left_state = 'half'
                right_state = 'half'
            elif c < 75:
                left_state = 'closed'
                right_state = 'closed'
            elif c < 98:
                left_state = 'half'
                right_state = 'half'
            else:
                left_state = 'wide'
                right_state = 'wide'

            # Smooth down position with transitions
            if c < 15: pupil_dx, pupil_dy = 0, 0
            elif c < 20: pupil_dx, pupil_dy = 0, 1
            elif c < 38: pupil_dx, pupil_dy = 0, 2
            elif c < 98: pupil_dx, pupil_dy = 0, 1
            elif c < 102: pupil_dx, pupil_dy = 0, 0  # Alert!
            else: pupil_dx, pupil_dy = 0, -1  # Surprised look up

            msg = "WAKE ME UP!"

        elif big_cycle == 2:
            # Full eye roll circle - very smooth
            c = cycle
            if c == 0: self._play_anim_sound("look")

            if c in range(54, 64):
                left_state = 'closed'
                right_state = 'closed'

            # Rolling in a circle with many intermediate frames
            if c < 5: pupil_dx, pupil_dy = 0, -2  # Up
            elif c < 8: pupil_dx, pupil_dy = 1, -2  # Up to up-right
            elif c < 12: pupil_dx, pupil_dy = 2, -2  # Up-right
            elif c < 15: pupil_dx, pupil_dy = 2, -1
            elif c < 20: pupil_dx, pupil_dy = 2, 0  # Right
            elif c < 23: pupil_dx, pupil_dy = 2, 1
            elif c < 28: pupil_dx, pupil_dy = 2, 2  # Down-right
            elif c < 31: pupil_dx, pupil_dy = 1, 2
            elif c < 36: pupil_dx, pupil_dy = 0, 2  # Down
            elif c < 39: pupil_dx, pupil_dy = -1, 2
            elif c < 44: pupil_dx, pupil_dy = -2, 2  # Down-left
            elif c < 47: pupil_dx, pupil_dy = -2, 1
            elif c < 54: pupil_dx, pupil_dy = -2, 0  # Left (then blink)
            elif c < 69: pupil_dx, pupil_dy = 0, 0  # Center (blink)
            elif c < 72: pupil_dx, pupil_dy = -1, 0
            elif c < 77: pupil_dx, pupil_dy = -2, 0  # Left
            elif c < 80: pupil_dx, pupil_dy = -2, -1
            elif c < 85: pupil_dx, pupil_dy = -2, -2  # Up-left
            elif c < 88: pupil_dx, pupil_dy = -1, -2
            elif c < 93: pupil_dx, pupil_dy = 0, -2  # Up
            elif c < 96: pupil_dx, pupil_dy = 1, -2
            elif c < 101: pupil_dx, pupil_dy = 2, -2  # Up-right
            elif c < 104: pupil_dx, pupil_dy = 2, -1
            elif c < 109: pupil_dx, pupil_dy = 2, 0  # Right
            elif c < 112: pupil_dx, pupil_dy = 1, 0
            else: pupil_dx, pupil_dy = 0, 0  # Center

            msg = "PLAY WITH ME!"

        elif big_cycle == 3:
            # Hide and seek
            c = cycle
            if c == 0: self._play_anim_sound("peek")

            if c < 24:
                pass
            elif c < 39:
                left_state = 'closed'
                right_state = 'closed'
            elif c < 50:
                left_state = 'hidden'
                right_state = 'hidden'
            elif c < 60:
                left_state = 'hidden'
                pupil_dx, pupil_dy = -1, 0
            elif c < 75:
                left_state = 'hidden'
                pupil_dx, pupil_dy = -2, 0
            elif c < 87:
                left_state = 'hidden'
                right_state = 'hidden'
            elif c < 97:
                right_state = 'hidden'
                pupil_dx, pupil_dy = 1, 0
            elif c < 105:
                right_state = 'hidden'
                pupil_dx, pupil_dy = 2, 0
            elif c < 112:
                pupil_dx, pupil_dy = 1, 0
            else:
                pupil_dx, pupil_dy = 0, 0

            msg = "PEEK A BOO!"

        elif big_cycle == 4:
            # Dizzy
            c = cycle
            if c == 0: self._play_anim_sound("dizzy")

            if c < 98:
                left_state = 'dizzy'
                right_state = 'dizzy'
            elif c < 105:
                left_state = 'half'
                right_state = 'half'
                pupil_dx, pupil_dy = 1, 1
            elif c < 112:
                pupil_dx, pupil_dy = -1, 0
            else:
                pupil_dx, pupil_dy = 0, 0

            msg = "PRESS TO PLAY!"

        elif big_cycle == 5:
            # Cross-eyed then opposite - with smooth transitions
            c = cycle
            if c == 0: self._play_anim_sound("blink")

            if c in range(35, 45):
                left_state = 'closed'
                right_state = 'closed'
            elif c in range(83, 93):
                left_state = 'closed'
                right_state = 'closed'

            # Very smooth eye movement
            if c < 5: pupil_dx, pupil_dy = 0, 0
            elif c < 10: pupil_dx, pupil_dy = 1, 0
            elif c < 35: pupil_dx, pupil_dy = 2, 0  # Right
            elif c < 50: pupil_dx, pupil_dy = 1, 0
            elif c < 55: pupil_dx, pupil_dy = 0, 0  # Center
            elif c < 60: pupil_dx, pupil_dy = -1, 0
            elif c < 83: pupil_dx, pupil_dy = -2, 0  # Left
            elif c < 97: pupil_dx, pupil_dy = -1, -1
            elif c < 105: pupil_dx, pupil_dy = 0, -2  # Up
            elif c < 112: pupil_dx, pupil_dy = 0, -1
            else: pupil_dx, pupil_dy = 0, 0

            msg = "AWESOME!"

        elif big_cycle == 6:
            # Suspicious - with very smooth transitions
            c = cycle
            if c == 0: self._play_anim_sound("look")
            # Smooth left to right
            if c < 5: pupil_dx, pupil_dy = 0, 0
            elif c < 10: pupil_dx, pupil_dy = -1, 0
            elif c < 25: pupil_dx, pupil_dy = -2, 0
            elif c < 30: pupil_dx, pupil_dy = -1, 0
            elif c < 35: pupil_dx, pupil_dy = 0, 0
            elif c < 40: pupil_dx, pupil_dy = 1, 0
            elif c < 55: pupil_dx, pupil_dy = 2, 0
            elif c < 70:
                left_state = 'half'
                right_state = 'half'
                pupil_dx, pupil_dy = 2, 0
            elif c < 86:
                left_state = 'half'
                right_state = 'half'
                pupil_dx, pupil_dy = 1, 0
            elif c < 97: pupil_dx, pupil_dy = 2, 1
            elif c < 107: pupil_dx, pupil_dy = 1, 1
            elif c < 115:
                left_state = 'closed'
                pupil_dx, pupil_dy = -1, 0
            else:
                left_state = 'closed'
                pupil_dx, pupil_dy = -2, 0

            msg = "I SEE YOU!"

        elif big_cycle == 7:
            # Crazy rapid - very smooth with many positions
            c = cycle
            if c == 0: self._play_anim_sound("dizzy")

            if c % 12 < 5:
                left_state = 'closed'
            if (c + 6) % 12 < 5:
                right_state = 'closed'
            # Many positions for very smooth crazy movement
            positions = [
                (0, 0), (0, -1), (1, -1), (1, -2), (2, -1), (2, 0), (1, 0),
                (1, 1), (0, 1), (-1, 1), (-1, 2), (-2, 1), (-2, 0), (-1, 0),
                (-1, -1), (0, -1), (0, -2), (1, -2), (2, -2), (2, -1),
                (1, 0), (0, 0), (0, 1), (0, 2), (-1, 2), (-2, 2), (-2, 1),
                (-2, 0), (-1, -1), (0, -1)
            ]
            pupil_dx, pupil_dy = positions[(c // 4) % len(positions)]

            msg = "PRESS TO PLAY!"

        elif big_cycle == 8:
            # Hypnotic - eyes move in opposite directions
            c = cycle
            if c == 0: self._play_anim_sound("hypno")
            # Smooth circular motion, eyes go opposite ways
            angle_steps = [
                (0, -2), (1, -2), (2, -1), (2, 0), (2, 1), (1, 2), (0, 2),
                (-1, 2), (-2, 1), (-2, 0), (-2, -1), (-1, -2)
            ]
            idx = (c // 5) % len(angle_steps)
            pupil_dx, pupil_dy = angle_steps[idx]
            # Draw eyes with opposite pupil directions
            draw_anime_eye(eye_left_x, eye_y, left_state, pupil_dx, pupil_dy)
            draw_anime_eye(eye_right_x, eye_y, right_state, -pupil_dx, -pupil_dy)
            self.display.draw_centered_text(13, "HYPNOTIZING!")
            return

        elif big_cycle == 9:
            # Bouncy - eyes look up and down like following a ball
            c = cycle
            if c == 0: self._play_anim_sound("bounce")

            if c in range(25, 35):
                left_state = 'wide'
                right_state = 'wide'
            elif c in range(75, 85):
                left_state = 'wide'
                right_state = 'wide'

            # Bouncy movement with smooth transitions
            bounce = [
                (0, -2), (0, -2), (0, -1), (0, 0), (0, 1), (0, 2), (0, 2),
                (0, 2), (0, 1), (0, 0), (0, -1), (0, -2)
            ]
            idx = (c // 5) % len(bounce)
            pupil_dx, pupil_dy = bounce[idx]

            # Add horizontal drift
            if c < 40:
                pupil_dx = -1
            elif c < 80:
                pupil_dx = 1
            else:
                pupil_dx = 0

            msg = "BOING BOING!"

        elif big_cycle == 10:
            # Reading - eyes scan left to right like reading text
            c = cycle
            if c == 0: self._play_anim_sound("look")

            if c in range(55, 65):
                left_state = 'closed'
                right_state = 'closed'

            # Reading motion - left to right, then jump back
            read_positions = [
                (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1),  # Read line
                (2, 1), (1, 1), (0, 1),  # Slight back
                (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2),  # Next line
            ]
            idx = (c // 6) % len(read_positions)
            if c < 55 or c >= 65:
                pupil_dx, pupil_dy = read_positions[idx]
            else:
                pupil_dx, pupil_dy = 0, 0

            msg = "INTERESTING!"

        elif big_cycle == 11:
            # Alternating winks with smooth pupil
            c = cycle
            if c == 0: self._play_anim_sound("flirt")

            # Wink pattern
            if c < 20:
                pass  # Both open
            elif c < 35:
                left_state = 'closed'
                pupil_dx, pupil_dy = 2, 0
            elif c < 50:
                pupil_dx, pupil_dy = 1, 0
            elif c < 60:
                pupil_dx, pupil_dy = 0, 0
            elif c < 75:
                right_state = 'closed'
                pupil_dx, pupil_dy = -2, 0
            elif c < 90:
                pupil_dx, pupil_dy = -1, 0
            elif c < 100:
                pupil_dx, pupil_dy = 0, 1
            elif c < 110:
                left_state = 'half'
                right_state = 'half'
                pupil_dx, pupil_dy = 0, 0
            else:
                pupil_dx, pupil_dy = 0, -1

            msg = "COME PLAY!"

        elif big_cycle == 12:
            # Shaking/Trembling - nervous shaking eyes
            c = cycle
            if c == 0: self._play_anim_sound("nervous")

            if c in range(60, 75):
                left_state = 'wide'
                right_state = 'wide'

            # Shaky nervous movement
            shake = [(0, 0), (1, 0), (0, 0), (-1, 0), (0, 1), (0, 0), (0, -1)]
            idx = (c // 2) % len(shake)
            pupil_dx, pupil_dy = shake[idx]

            msg = "SO NERVOUS!"

        elif big_cycle == 13:
            # Searching - looking around frantically
            c = cycle
            if c == 0: self._play_anim_sound("search")

            if c in range(30, 40) or c in range(80, 90):
                left_state = 'wide'
                right_state = 'wide'

            # Frantic searching pattern
            search = [
                (-2, -2), (-1, -1), (0, -2), (1, -1), (2, -2),
                (2, 0), (2, 2), (1, 1), (0, 2), (-1, 1), (-2, 2),
                (-2, 0), (-1, -1), (0, 0), (1, -1), (2, 0)
            ]
            idx = (c // 4) % len(search)
            pupil_dx, pupil_dy = search[idx]

            msg = "WHERE IS IT?"

        elif big_cycle == 14:
            # Flirty - batting eyelashes with playful look
            c = cycle
            if c == 0: self._play_anim_sound("flirt")

            # Quick blinks
            if c in range(15, 20) or c in range(35, 40) or c in range(55, 60):
                left_state = 'closed'
                right_state = 'closed'
            elif c in range(75, 95):
                left_state = 'half'
                right_state = 'half'

            # Playful side glances
            if c < 25:
                pupil_dx, pupil_dy = 2, 1
            elif c < 45:
                pupil_dx, pupil_dy = -2, 1
            elif c < 65:
                pupil_dx, pupil_dy = 0, -1
            elif c < 85:
                pupil_dx, pupil_dy = 1, 0
            else:
                pupil_dx, pupil_dy = -1, 1

            msg = "HEY THERE!"

        elif big_cycle == 15:
            # Figure 8 - smooth figure 8 pattern
            c = cycle
            if c == 0: self._play_anim_sound("hypno")

            if c in range(58, 68):
                left_state = 'closed'
                right_state = 'closed'

            # Figure 8 with many intermediate positions
            fig8 = [
                (0, -2), (1, -2), (2, -1), (2, 0), (2, 1), (1, 2), (0, 2),
                (-1, 1), (-2, 0), (-2, -1), (-1, -2), (0, -2),
                (-1, -2), (-2, -1), (-2, 0), (-2, 1), (-1, 2), (0, 2),
                (1, 1), (2, 0), (2, -1), (1, -2), (0, -2)
            ]
            idx = (c // 3) % len(fig8)
            if c < 58 or c >= 68:
                pupil_dx, pupil_dy = fig8[idx]
            else:
                pupil_dx, pupil_dy = 0, 0

            msg = "PRESS TO PLAY!"

        draw_anime_eye(eye_left_x, eye_y, left_state, pupil_dx, pupil_dy)
        draw_anime_eye(eye_right_x, eye_y, right_state, pupil_dx, pupil_dy)

        self.display.draw_centered_text(13, msg)

    def _render_game(self):
        """Render game play."""
        # Draw solid ground line
        self.display.draw_line(0, GROUND_Y, WIDTH - 1, GROUND_Y)

        # Draw dinosaur
        self.display.draw_sprite(self.dino.get_sprite(), self.dino.x, int(self.dino.y))

        # Draw obstacles
        for obs in self.obstacles:
            self.display.draw_sprite(obs.get_sprite(), int(obs.x), obs.y)

        # Draw score (top right)
        score_str = str(self.score)
        self.display.draw_text(WIDTH - len(score_str) * 4 - 2, 1, score_str)

    def _render_gameover(self):
        """Render game over screen."""
        # Draw "GAME OVER" text - single line, larger
        self.display.draw_centered_text(1, "GAME OVER")

        # Draw score and high score with labels
        score_str = "SCORE " + str(self.score)
        hi_str = "HIGH SCORE " + str(self.high_score)
        self.display.draw_centered_text(8, score_str)
        self.display.draw_centered_text(14, hi_str)


def main():
    parser = argparse.ArgumentParser(description="Dinosaur Game for BUSE Display")
    parser.add_argument('--terminal', '-t', action='store_true',
                        help='Run in terminal test mode')
    parser.add_argument('--both', '-b', action='store_true',
                        help='Output to both framebuffer and terminal')
    parser.add_argument('--fb-path', default='/dev/fb0',
                        help='Framebuffer device path')
    parser.add_argument('--no-duck', action='store_true',
                        help='Disable duck mechanic (jump only, no birds)')
    parser.add_argument('--no-sound', action='store_true',
                        help='Disable sound effects')
    args = parser.parse_args()

    global FB_PATH
    FB_PATH = args.fb_path

    # Determine display mode
    use_fb = not args.terminal
    use_term = args.terminal or args.both

    if use_term:
        # Clear terminal and hide cursor
        sys.stdout.write("\033[2J\033[H\033[?25l")
        sys.stdout.flush()

    display = Display(use_framebuffer=use_fb, use_terminal=use_term)
    input_handler = InputHandler(use_terminal_input=use_term)

    game = Game(display, input_handler, duck_enabled=not args.no_duck, sound_enabled=not args.no_sound)

    try:
        last_frame = time.time()
        while True:
            now = time.time()
            if now - last_frame >= FRAME_INTERVAL:
                if not game.update():
                    break
                game.render()
                last_frame = now
            time.sleep(0.001)
    except KeyboardInterrupt:
        pass
    finally:
        input_handler.cleanup()
        if use_term:
            # Show cursor again and clear
            sys.stdout.write("\033[?25h\033[2J\033[H")
            sys.stdout.flush()
        print("Thanks for playing!")


if __name__ == "__main__":
    main()
