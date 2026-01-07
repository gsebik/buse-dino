#!/usr/bin/env python3
"""
Dinosaur Game for BUSE 144x19 LED Display

A Chrome-style dinosaur jumping game for the BUSE framebuffer display.
Supports both framebuffer output and terminal test mode.

Controls:
  Keyboard:
    - Enter/PageUp/Up: Jump / Start game
    - Space/Down: Duck (to avoid birds)
    - Escape: Quit
  Gamepad (GameSir Nova Lite / Xbox-style):
    - A Button: Jump / Start game
    - B Button: Duck
    - Start/Select: Start game

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
            self._generate_point_lost("point_lost.wav")  # Quick sad sound for losing a point
            self._generate_hit("hit.wav")  # Quick hit sound for dino losing a life
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
        """Generate a smooth sine tone WAV file."""
        if freq_end is None:
            freq_end = freq

        filepath = os.path.join(self.sound_dir, filename)
        n_samples = int(sample_rate * duration)

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            phase = 0
            for i in range(n_samples):
                t = i / sample_rate
                # Linear frequency sweep
                f = freq + (freq_end - freq) * (i / n_samples)
                # Generate smooth sine wave with envelope
                envelope = min(1.0, min(i, n_samples - i) / (sample_rate * 0.01))
                # Sine wave with slight harmonics for warmth
                tone = 0.8 * math.sin(2 * math.pi * f * t) + 0.2 * math.sin(4 * math.pi * f * t)
                sample = int(24000 * envelope * tone)
                wav.writeframes(struct.pack('<h', max(-32767, min(32767, sample))))

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
                # Smooth sine wave
                tone = 0.8 * math.sin(2 * math.pi * f * t) + 0.2 * math.sin(4 * math.pi * f * t)
                sample = int(24000 * envelope * tone)
                wav.writeframes(struct.pack('<h', max(-32767, min(32767, sample))))

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
                        # Smooth sine wave with harmonics
                        tone = 0.7 * math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(4 * math.pi * freq * t)
                        sample = int(24000 * envelope * tone)
                    wav.writeframes(struct.pack('<h', max(-32767, min(32767, sample))))
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
                    # Smooth sine wave
                    tone = 0.8 * math.sin(2 * math.pi * freq * t) + 0.2 * math.sin(4 * math.pi * freq * t)
                    sample = int(24000 * envelope * tone)
                    wav.writeframes(struct.pack('<h', max(-32767, min(32767, sample))))
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
                # Smooth sine wave
                tone = math.sin(2 * math.pi * freq * t)
                sample = int(20000 * envelope * tone)
                wav.writeframes(struct.pack('<h', max(-32767, min(32767, sample))))

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
                    # Smooth sine wave
                    tone = 0.8 * math.sin(2 * math.pi * freq * t) + 0.2 * math.sin(4 * math.pi * freq * t)
                    sample = int(24000 * envelope * tone)
                    wav.writeframes(struct.pack('<h', max(-32767, min(32767, sample))))
                    sample_pos += 1

    def _generate_point_lost(self, filename, sample_rate=22050):
        """Generate a short descending tone for losing a point in pong."""
        filepath = os.path.join(self.sound_dir, filename)
        # Quick descending two notes - not as dramatic as game over
        notes = [(400, 0.1), (250, 0.15)]

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
                    decay = max(0.3, 1.0 - (i / note_samples) * 0.5)
                    envelope = attack * decay
                    tone = math.sin(2 * math.pi * freq * t)
                    sample = int(20000 * envelope * tone)
                    wav.writeframes(struct.pack('<h', max(-32767, min(32767, sample))))
                    sample_pos += 1

    def _generate_hit(self, filename, sample_rate=22050):
        """Generate a quick hit sound for dino losing a life."""
        filepath = os.path.join(self.sound_dir, filename)
        duration = 0.15
        n_samples = int(sample_rate * duration)

        with wave.open(filepath, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)

            for i in range(n_samples):
                t = i / sample_rate
                progress = i / n_samples
                # Descending frequency
                freq = 500 - 300 * progress
                envelope = (1 - progress) ** 1.5
                tone = math.sin(2 * math.pi * freq * t)
                sample = int(22000 * envelope * tone)
                wav.writeframes(struct.pack('<h', max(-32767, min(32767, sample))))

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
        self._generate_arpeggio(filename, [880, 660], note_duration=0.06, volume=1.0)

    def _generate_wink(self, filename, sample_rate=22050):
        """Wink - playful three-note ascending like Mario coin."""
        self._generate_arpeggio(filename, [523, 659, 784], note_duration=0.07, volume=1.0)

    def _generate_whoosh(self, filename, sample_rate=22050):
        """Look/whoosh - sweeping sound like Sonic spin."""
        self._generate_sweep(filename, 300, 800, 0.15, volume=1.0)

    def _generate_surprise(self, filename, sample_rate=22050):
        """Surprise - dramatic rising arpeggio like Pokemon encounter."""
        self._generate_arpeggio(filename, [392, 494, 587, 784], note_duration=0.08, volume=1.0)

    def _generate_sleepy(self, filename, sample_rate=22050):
        """Sleepy - slow descending notes like lullaby."""
        self._generate_arpeggio(filename, [523, 440, 349, 294], note_duration=0.15, volume=1.0)

    def _generate_dizzy(self, filename, sample_rate=22050):
        """Dizzy - wobbling disorienting sound."""
        self._generate_wobble(filename, 400, 8, 0.4, volume=1.0)

    def _generate_peek(self, filename, sample_rate=22050):
        """Peek-a-boo - playful reveal like Mario power-up."""
        self._generate_arpeggio(filename, [262, 330, 392, 523], note_duration=0.08, volume=1.0)

    def _generate_hypno(self, filename, sample_rate=22050):
        """Hypno - mysterious wavering tones."""
        self._generate_wobble(filename, 350, 4, 0.5, volume=1.0)

    def _generate_bounce(self, filename, sample_rate=22050):
        """Bounce - springy boing like classic platformer jump."""
        self._generate_sweep(filename, 200, 600, 0.12, volume=1.0)

    def _generate_nervous(self, filename, sample_rate=22050):
        """Nervous - trembling rapid notes."""
        self._generate_arpeggio(filename, [440, 466, 440, 466, 440], note_duration=0.05, volume=1.0)

    def _generate_search(self, filename, sample_rate=22050):
        """Search - curious looking around sound."""
        self._generate_arpeggio(filename, [392, 440, 392, 349], note_duration=0.1, volume=1.0)

    def _generate_flirt(self, filename, sample_rate=22050):
        """Flirt - sweet melodic phrase like dating sim."""
        self._generate_arpeggio(filename, [523, 659, 784, 659, 523], note_duration=0.08, volume=1.0)

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
WIDTH, HEIGHT = 144, 19
FB_PATH = "/dev/fb0"
BYTES_PER_ROW = WIDTH // 8
BUFFER_SIZE = BYTES_PER_ROW * HEIGHT

# Game physics (tuned for 60fps)
# Lower gravity = longer air time, higher jump velocity = higher jump
GRAVITY = 0.10  # Reduced for easier jumping (more air time)
JUMP_VELOCITY = -1.55  # Slightly higher jump for easier obstacle clearing
GROUND_Y = HEIGHT - 1

# Timing
FRAME_INTERVAL = 0.016  # ~60 FPS for smoother animations
OBSTACLE_SPAWN_MIN = 1.5
OBSTACLE_SPAWN_MAX = 3.0

# Lives system
MAX_LIVES = 3

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

# UFO sprite (appears at 2000+ points)
UFO_1 = [
    "  XXX  ",
    " XXXXX ",
    "XXXXXXX",
    " X X X ",
]

UFO_2 = [
    "  XXX  ",
    " XXXXX ",
    "XXXXXXX",
    "X X X X",
]

# Meteor sprite (appears at 2000+ points)
METEOR = [
    " XX",
    "XXX",
    " X ",
]

# Comet sprite
COMET = [
    "   X",
    "  XX",
    " XXX",
    "XXXX",
]

# Robot sprite (appears at 1500+ points)
ROBOT = [
    " XXX ",
    "XXXXX",
    " X X ",
    "XXXXX",
    " X X ",
]

# Volcano sprites for eruption animation
VOLCANO_BASE = [
    "    X    ",
    "   XXX   ",
    "  XXXXX  ",
    " XXXXXXX ",
    "XXXXXXXXX",
]

# Lava/eruption particles
LAVA_PARTICLES = [
    ["X", " ", "X", " ", "X"],
    [" ", "X", " ", "X", " "],
    ["X", " ", "X", " ", "X"],
]

# Heart sprite for lives display
HEART = [
    " X X ",
    "XXXXX",
    " XXX ",
    "  X  ",
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
        """Set a pixel in the buffer - matches test_pattern.py exactly."""
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            idx = y * WIDTH + x
            byte_idx = idx >> 3
            bit = idx & 7
            mask = 1 << bit
            if value:
                self.buffer[byte_idx] |= mask
            else:
                self.buffer[byte_idx] &= ~mask

    def get_pixel(self, x, y):
        """Get pixel value from buffer."""
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            idx = y * WIDTH + x
            byte_idx = idx >> 3
            bit = idx & 7
            mask = 1 << bit
            return 1 if self.buffer[byte_idx] & mask else 0
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
    """Handle keyboard input via evdev and/or stdin."""

    def __init__(self, use_terminal_input=False):
        self.use_terminal_input = use_terminal_input
        self.keyboards = []  # Support multiple keyboards/gamepads
        self.gamepads = []   # Track gamepads separately for 2-player
        self.jump_pressed = False
        self.duck_pressed = False
        self.quit_requested = False
        self.old_settings = None

        # Pong controls (for multiplayer)
        self.p1_up = False
        self.p1_down = False
        self.p2_up = False
        self.p2_down = False

        # Game selection
        self.select_pong = False  # BTN_B pressed on start screen
        self.select_snake = False  # BTN_Y pressed on start screen
        self.select_draw = False   # BTN_START for draw
        self.back_to_menu = False  # BTN_X to exit game
        self.draw_button = False  # BTN_TL to draw

        # Joystick for draw game (left stick)
        self.stick_x = 0  # -1, 0, or 1
        self.stick_y = 0
        # Right joystick - tracked per player for multiplayer
        # Now stores actual analog value (0-255, 128=center) for smooth control
        self.rstick_x = 128
        self.rstick_y = 128
        self.p1_rstick_y = 128  # Player 1 right stick Y (0-255)
        self.p2_rstick_y = 128  # Player 2 right stick Y (0-255)
        # Y/A buttons for paddle control (Y=up, A=down)
        self.p1_btn_up = False  # Player 1 Y button
        self.p1_btn_down = False  # Player 1 A button
        self.p2_btn_up = False  # Player 2 Y button
        self.p2_btn_down = False  # Player 2 A button

        # Always try to init evdev for gamepad support
        self.known_device_paths = set()  # Track known devices for hot-plug detection
        self.last_device_check = 0  # Last time we checked for new devices
        if HAS_EVDEV:
            self._init_evdev()

        # Also init terminal if requested (allows both gamepad + terminal)
        if use_terminal_input:
            self._init_terminal()
        elif not self.keyboards:
            # No evdev devices found, fall back to terminal
            print("No evdev devices found, falling back to terminal input")
            self._init_terminal()

    def _init_evdev(self):
        """Initialize evdev keyboard/gamepad input."""
        devices = list_devices()
        print(f"Found {len(devices)} input devices")

        # Try to find all suitable keyboard and gamepad devices
        for path in devices:
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    # Look for device with common keys (Enter, PageUp, Space, or arrow keys)
                    has_keyboard_keys = any(k in keys for k in [
                        ecodes.KEY_ENTER, ecodes.KEY_PAGEUP, ecodes.KEY_SPACE,
                        ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_A, ecodes.KEY_1
                    ])
                    # Also check for gamepad buttons (BTN_A, BTN_B, etc.)
                    has_gamepad_btns = any(k in keys for k in [
                        ecodes.BTN_A, ecodes.BTN_B, ecodes.BTN_X, ecodes.BTN_Y,
                        ecodes.BTN_SOUTH, ecodes.BTN_EAST, ecodes.BTN_NORTH, ecodes.BTN_WEST,
                        ecodes.BTN_START, ecodes.BTN_SELECT, ecodes.BTN_GAMEPAD
                    ])

                    # Check if it has analog sticks (full gamepad)
                    has_sticks = False
                    if ecodes.EV_ABS in caps:
                        abs_caps = [c[0] if isinstance(c, tuple) else c for c in caps[ecodes.EV_ABS]]
                        has_sticks = ecodes.ABS_X in abs_caps and ecodes.ABS_Y in abs_caps

                    has_keys = has_keyboard_keys or has_gamepad_btns
                    if has_keys:
                        print(f"Using input device: {dev.name} ({path})")
                        try:
                            dev.grab()
                        except IOError as e:
                            print(f"  Could not grab device: {e}")
                        self.keyboards.append(dev)
                        self.known_device_paths.add(path)

                        # Track full gamepads separately for 2-player
                        if has_gamepad_btns and has_sticks:
                            self.gamepads.append(dev)
                            print(f"  -> Gamepad #{len(self.gamepads)} for multiplayer")

            except Exception as e:
                print(f"Error checking device {path}: {e}")
                continue

        if self.gamepads:
            print(f"Found {len(self.gamepads)} gamepad(s) for 2-player Pong")

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

    def _check_new_devices(self):
        """Check for newly connected controllers (hot-plug support)."""
        if not HAS_EVDEV:
            return

        # Only check every 2 seconds
        now = time.time()
        if now - self.last_device_check < 2.0:
            return
        self.last_device_check = now

        # Get current device list
        current_devices = set(list_devices())

        # Find new devices
        new_paths = current_devices - self.known_device_paths

        for path in new_paths:
            try:
                dev = InputDevice(path)
                caps = dev.capabilities()
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    has_gamepad_btns = any(k in keys for k in [
                        ecodes.BTN_A, ecodes.BTN_B, ecodes.BTN_X, ecodes.BTN_Y,
                        ecodes.BTN_SOUTH, ecodes.BTN_EAST, ecodes.BTN_NORTH, ecodes.BTN_WEST,
                        ecodes.BTN_START, ecodes.BTN_SELECT, ecodes.BTN_GAMEPAD
                    ])

                    has_sticks = False
                    if ecodes.EV_ABS in caps:
                        abs_caps = [c[0] if isinstance(c, tuple) else c for c in caps[ecodes.EV_ABS]]
                        has_sticks = ecodes.ABS_X in abs_caps and ecodes.ABS_Y in abs_caps

                    if has_gamepad_btns:
                        print(f"New controller connected: {dev.name} ({path})")
                        try:
                            dev.grab()
                        except IOError as e:
                            print(f"  Could not grab device: {e}")
                        self.keyboards.append(dev)
                        self.known_device_paths.add(path)

                        if has_gamepad_btns and has_sticks:
                            self.gamepads.append(dev)
                            print(f"  -> Gamepad #{len(self.gamepads)} for multiplayer")

            except Exception as e:
                pass  # Device might have disconnected already

        # Also clean up disconnected devices
        for kb in self.keyboards[:]:
            try:
                _ = kb.fd  # Check if device is still valid
            except (OSError, IOError):
                print(f"Controller disconnected: {kb.path}")
                self.keyboards.remove(kb)
                if kb in self.gamepads:
                    self.gamepads.remove(kb)
                if kb.path in self.known_device_paths:
                    self.known_device_paths.discard(kb.path)

    def poll(self):
        """Poll for input events. Returns (jump_triggered, duck_held, quit_requested)."""
        # Check for newly connected controllers
        self._check_new_devices()

        jump_triggered = False
        duck_held = False
        self.select_pong = False  # Reset each frame
        self.select_snake = False
        self.select_draw = False
        self.back_to_menu = False
        # Note: stick values are NOT reset here - they persist until stick position changes
        # This allows continuous movement while holding the stick

        # Check terminal input if enabled
        if self.use_terminal_input:
            r, _, _ = select([sys.stdin], [], [], 0)
            if r:
                char = sys.stdin.read(1)
                if char == '\n' or char == '\r':
                    jump_triggered = True
                elif char == ' ':
                    duck_held = True
                elif char == 'b' or char == 'B':
                    self.select_pong = True
                elif char == 'w' or char == 'W':
                    self.p1_up = True
                elif char == 's' or char == 'S':
                    self.p1_down = True
                elif char == 'i' or char == 'I':
                    self.p2_up = True
                elif char == 'k' or char == 'K':
                    self.p2_down = True
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
                    # Check for arrow keys
                    if seq == '[A':  # Up
                        self.p1_up = True
                    elif seq == '[B':  # Down
                        self.p1_down = True
                    else:
                        jump_triggered = True

        # Also check evdev devices (gamepads, keyboards)
        if self.keyboards:
            r, _, _ = select(self.keyboards, [], [], 0)
            for kb in r:
                try:
                    # Determine which player this controller is (for 2-player pong)
                    # First gamepad = P1, second gamepad = P2
                    is_p1_controller = (len(self.gamepads) < 2 or
                                        kb not in self.gamepads or
                                        self.gamepads.index(kb) == 0)
                    is_p2_controller = (len(self.gamepads) >= 2 and
                                        kb in self.gamepads and
                                        self.gamepads.index(kb) == 1)

                    for event in kb.read():
                        if event.type == ecodes.EV_KEY:
                            key_event = categorize(event)
                            is_down = key_event.keystate == key_event.key_down
                            is_up = key_event.keystate == key_event.key_up

                            # Jump/Select Dino: A button (also paddle DOWN in pong)
                            if key_event.scancode in (ecodes.KEY_ENTER, ecodes.BTN_A, ecodes.BTN_SOUTH):
                                if is_down:
                                    jump_triggered = True
                                # Track A button per player for paddle control
                                if is_p1_controller:
                                    self.p1_btn_down = is_down
                                elif is_p2_controller:
                                    self.p2_btn_down = is_down

                            # Select Pong / Duck: B button
                            elif key_event.scancode in (ecodes.BTN_B, ecodes.BTN_EAST):
                                if is_down:
                                    print(f"DEBUG: BTN_B detected! scancode={key_event.scancode}")
                                    self.select_pong = True
                                    self.duck_pressed = True
                                elif is_up:
                                    self.duck_pressed = False

                            # D-pad Up/Down - route to correct player
                            elif key_event.scancode in (ecodes.KEY_UP, ecodes.KEY_PAGEUP):
                                if is_p1_controller:
                                    self.p1_up = is_down
                                elif is_p2_controller:
                                    self.p2_up = is_down
                                if is_down:
                                    jump_triggered = True

                            elif key_event.scancode in (ecodes.KEY_DOWN, ecodes.KEY_PAGEDOWN, ecodes.KEY_SPACE):
                                if is_p1_controller:
                                    self.p1_down = is_down
                                elif is_p2_controller:
                                    self.p2_down = is_down
                                if is_down:
                                    self.duck_pressed = True
                                elif is_up:
                                    self.duck_pressed = False

                            # Y button - select snake / paddle UP
                            elif key_event.scancode in (ecodes.BTN_Y, ecodes.BTN_WEST):
                                if is_down:
                                    self.select_snake = True
                                # Track Y button per player for paddle control
                                if is_p1_controller:
                                    self.p1_btn_up = is_down
                                elif is_p2_controller:
                                    self.p2_btn_up = is_down

                            # X button - back to menu / P2 down (single controller)
                            elif key_event.scancode in (ecodes.BTN_X, ecodes.BTN_NORTH):
                                if is_down:
                                    self.back_to_menu = True
                                self.p2_down = is_down

                            # Left trigger/bumper - draw button AND start draw game
                            elif key_event.scancode == ecodes.BTN_TL:
                                self.draw_button = is_down
                                if is_down:
                                    self.select_draw = True  # Also starts Draw from menu

                            # Start = draw game, Select = start dino
                            # BTN_START is 0x13b (315), BTN_MODE is 0x13c (316)
                            elif key_event.scancode in (ecodes.BTN_START, ecodes.BTN_MODE, 315, 316):
                                if is_down:
                                    self.select_draw = True
                                    print(f"DEBUG: Start/Draw button pressed: {key_event.scancode}")
                            elif key_event.scancode in (ecodes.BTN_SELECT, 314):
                                if is_down:
                                    jump_triggered = True

                            elif key_event.scancode == ecodes.KEY_ESC:
                                if is_down:
                                    self.quit_requested = True

                        # Handle analog stick / D-pad for pong and draw
                        elif event.type == ecodes.EV_ABS:
                            # HAT0X for D-pad left/right
                            if event.code == ecodes.ABS_HAT0X:
                                self.stick_x = -1 if event.value < 0 else (1 if event.value > 0 else 0)
                            # HAT0Y for D-pad up/down
                            elif event.code == ecodes.ABS_HAT0Y:
                                self.stick_y = -1 if event.value < 0 else (1 if event.value > 0 else 0)
                                if is_p1_controller:
                                    self.p1_up = event.value < 0
                                    self.p1_down = event.value > 0
                                elif is_p2_controller:
                                    self.p2_up = event.value < 0
                                    self.p2_down = event.value > 0
                            # Left stick X (wider deadzone 90-166)
                            elif event.code == ecodes.ABS_X:
                                if event.value < 90:
                                    self.stick_x = -1
                                elif event.value > 166:
                                    self.stick_x = 1
                                else:
                                    self.stick_x = 0
                            # Left stick Y
                            elif event.code == ecodes.ABS_Y:
                                if event.value < 100:
                                    self.stick_y = -1
                                    if is_p1_controller:
                                        self.p1_up = True
                                        self.p1_down = False
                                    elif is_p2_controller:
                                        self.p2_up = True
                                        self.p2_down = False
                                elif event.value > 156:
                                    self.stick_y = 1
                                    if is_p1_controller:
                                        self.p1_down = True
                                        self.p1_up = False
                                    elif is_p2_controller:
                                        self.p2_down = True
                                        self.p2_up = False
                                else:
                                    # Stick centered - reset movement
                                    self.stick_y = 0
                                    if is_p1_controller:
                                        self.p1_up = False
                                        self.p1_down = False
                                    elif is_p2_controller:
                                        self.p2_up = False
                                        self.p2_down = False
                            # Right stick X (ABS_Z on some controllers, ABS_RX on others)
                            # Store actual analog value (0-255) for smooth control
                            elif event.code in (ecodes.ABS_RX, ecodes.ABS_Z):
                                self.rstick_x = event.value
                            # Right stick Y (ABS_RZ on some controllers, ABS_RY on others)
                            # Store actual analog value (0-255) for smooth proportional control
                            elif event.code in (ecodes.ABS_RY, ecodes.ABS_RZ):
                                self.rstick_y = event.value
                                if is_p1_controller:
                                    self.p1_rstick_y = event.value
                                elif is_p2_controller:
                                    self.p2_rstick_y = event.value

                except Exception:
                    pass  # Device may have been disconnected
            duck_held = duck_held or self.duck_pressed

        return jump_triggered, duck_held, self.quit_requested

    def get_pong_input(self):
        """Get pong-specific input state."""
        return self.p1_up, self.p1_down, self.p2_up, self.p2_down

    def reset_pong_input(self):
        """Reset pong input for next frame (for terminal mode)."""
        if self.use_terminal_input:
            self.p1_up = False
            self.p1_down = False
            self.p2_up = False
            self.p2_down = False

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
    """Represents an obstacle (cactus, bird, ufo, etc.)."""

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

    # New obstacles for higher scores
    ROBOT_TYPES = [
        ('robot', ROBOT, GROUND_Y - 5),
    ]

    UFO_TYPES = [
        ('ufo_low', UFO_1, GROUND_Y - 6),
        ('ufo_high', UFO_1, GROUND_Y - 10),
    ]

    METEOR_TYPES = [
        ('meteor', METEOR, GROUND_Y - 5),
        ('comet', COMET, GROUND_Y - 6),
    ]

    def __init__(self, x, include_birds=True, duck_enabled=True, score=0):
        self.x = x
        self.score = score

        # Build available types based on score
        types = list(self.CACTUS_TYPES)

        if include_birds:
            if duck_enabled:
                types.extend(self.BIRD_TYPES)
            else:
                types.extend(self.BIRD_JUMP_TYPES)

        # Add robots at 1500+ points
        if score >= 1500:
            types.extend(self.ROBOT_TYPES)

        # Add UFOs and meteors at 2000+ points
        if score >= 2000:
            types.extend(self.UFO_TYPES)
            types.extend(self.METEOR_TYPES)

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
        if 'ufo' in self.name:
            return UFO_1 if (self.frame // 4) % 2 == 0 else UFO_2
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
        """Get collision hitbox (slightly smaller for more forgiving gameplay)."""
        return (self.x + 2, int(self.y) + 2, self.width - 4, self.height - 3)


class PongGame:
    """Multiplayer Pong game for BUSE display."""

    PADDLE_HEIGHT = 6  # Taller paddle for easier play
    PADDLE_WIDTH = 2
    BALL_SPEED_INITIAL = 0.4  # Start slow
    BALL_SPEED_MAX = 1.5
    WINNING_SCORE = 5

    # Paddle positions - moderate distance apart
    P1_X = 15  # Left paddle
    P2_X = WIDTH - 17  # Right paddle
    PLAY_WIDTH = P2_X - P1_X  # Playable area width

    def __init__(self, display, sound):
        self.display = display
        self.sound = sound
        self.reset()

    def reset(self):
        """Reset game state."""
        self.ball_x = WIDTH // 2
        self.ball_y = HEIGHT // 2
        self.ball_dx = 1.0
        self.ball_dy = 0.5
        self.ball_speed = self.BALL_SPEED_INITIAL

        # Paddles - player 1 on left, player 2 on right
        self.p1_y = HEIGHT // 2 - self.PADDLE_HEIGHT // 2
        self.p2_y = HEIGHT // 2 - self.PADDLE_HEIGHT // 2

        # Scores
        self.p1_score = 0
        self.p2_score = 0

        self.state = 'playing'  # playing, p1_wins, p2_wins
        self.frame = 0

    def update(self, p1_stick, p2_stick, p1_btn_up=False, p1_btn_down=False, p2_btn_up=False, p2_btn_down=False):
        """Update pong game state with analog stick values (0-255, 128=center)."""
        if self.state != 'playing':
            self.frame += 1
            return

        self.frame += 1

        # Calculate paddle velocities from analog stick values
        # Deadzone of 20 around center (108-148)
        # Max speed of 3 pixels per frame at full deflection
        def stick_to_velocity(stick_val):
            centered = stick_val - 128  # -128 to +127
            if abs(centered) < 20:  # Deadzone
                return 0
            # Scale to max speed of 3
            return (centered / 128.0) * 3.0

        p1_vel = stick_to_velocity(p1_stick)
        p2_vel = stick_to_velocity(p2_stick)

        # Button overrides (Y=up, A=down)
        if p1_btn_up:
            p1_vel = -2
        elif p1_btn_down:
            p1_vel = 2
        if p2_btn_up:
            p2_vel = -2
        elif p2_btn_down:
            p2_vel = 2

        # Move P1 paddle
        self.p1_y += p1_vel
        self.p1_y = max(0, min(HEIGHT - 1 - self.PADDLE_HEIGHT, self.p1_y))

        # Move P2 paddle
        self.p2_y += p2_vel
        self.p2_y = max(0, min(HEIGHT - 1 - self.PADDLE_HEIGHT, self.p2_y))

        # Move ball
        self.ball_x += self.ball_dx * self.ball_speed
        self.ball_y += self.ball_dy * self.ball_speed

        # Ball collision with top/bottom
        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_dy = abs(self.ball_dy)
            self.sound.play("bounce")
        elif self.ball_y >= HEIGHT - 1:
            self.ball_y = HEIGHT - 1
            self.ball_dy = -abs(self.ball_dy)
            self.sound.play("bounce")

        # Ball collision with paddles
        # Left paddle (P1)
        if (self.ball_x <= self.P1_X + self.PADDLE_WIDTH and self.ball_dx < 0 and
            self.p1_y <= self.ball_y < self.p1_y + self.PADDLE_HEIGHT):
            self.ball_dx = abs(self.ball_dx)
            # Add angle based on where ball hit paddle
            hit_pos = (self.ball_y - self.p1_y) / self.PADDLE_HEIGHT
            self.ball_dy = (hit_pos - 0.5) * 1.5
            self.ball_speed = min(self.ball_speed + 0.1, self.BALL_SPEED_MAX)
            self.sound.play("jump")

        # Right paddle (P2)
        if (self.ball_x >= self.P2_X - 1 and self.ball_dx > 0 and
            self.p2_y <= self.ball_y < self.p2_y + self.PADDLE_HEIGHT):
            self.ball_dx = -abs(self.ball_dx)
            hit_pos = (self.ball_y - self.p2_y) / self.PADDLE_HEIGHT
            self.ball_dy = (hit_pos - 0.5) * 1.5
            self.ball_speed = min(self.ball_speed + 0.1, self.BALL_SPEED_MAX)
            self.sound.play("jump")

        # Scoring - ball passes paddle
        if self.ball_x < self.P1_X - 5:
            self.p2_score += 1
            self.sound.play("point_lost")
            self._reset_ball(-1)
        elif self.ball_x > self.P2_X + 5:
            self.p1_score += 1
            self.sound.play("point_lost")
            self._reset_ball(1)

        # Check for winner
        if self.p1_score >= self.WINNING_SCORE:
            self.state = 'p1_wins'
            self.sound.speak("Player 1 wins!", speed=150, pitch=60)
        elif self.p2_score >= self.WINNING_SCORE:
            self.state = 'p2_wins'
            self.sound.speak("Player 2 wins!", speed=150, pitch=60)

    def _reset_ball(self, direction):
        """Reset ball after scoring."""
        self.ball_x = WIDTH // 2
        self.ball_y = HEIGHT // 2
        self.ball_dx = direction
        self.ball_dy = random.uniform(-0.5, 0.5)
        self.ball_speed = self.BALL_SPEED_INITIAL

    def render(self):
        """Render pong game."""
        self.display.clear()

        if self.state == 'playing':
            # Draw center line
            for y in range(0, HEIGHT, 2):
                self.display.set_pixel(WIDTH // 2, y)

            # Draw play area boundaries
            for y in range(HEIGHT):
                self.display.set_pixel(self.P1_X - 3, y)
                self.display.set_pixel(self.P2_X + 3, y)

            # Draw paddles
            for i in range(self.PADDLE_HEIGHT):
                for w in range(self.PADDLE_WIDTH):
                    self.display.set_pixel(self.P1_X + w, int(self.p1_y) + i)
                    self.display.set_pixel(self.P2_X + w, int(self.p2_y) + i)

            # Draw ball (2x2 for visibility)
            bx, by = int(self.ball_x), int(self.ball_y)
            self.display.set_pixel(bx, by)
            self.display.set_pixel(bx + 1, by)
            if by + 1 < HEIGHT:
                self.display.set_pixel(bx, by + 1)
                self.display.set_pixel(bx + 1, by + 1)

            # Draw scores on sides
            self.display.draw_text(5, 7, str(self.p1_score))
            self.display.draw_text(WIDTH - 10, 7, str(self.p2_score))

        else:
            # Game over screen
            if self.state == 'p1_wins':
                self.display.draw_centered_text(3, "PLAYER 1")
                self.display.draw_centered_text(9, "WINS!")
            else:
                self.display.draw_centered_text(3, "PLAYER 2")
                self.display.draw_centered_text(9, "WINS!")

            score_str = f"{self.p1_score} - {self.p2_score}"
            self.display.draw_centered_text(15, score_str)


class SnakeGame:
    """Classic Snake game for BUSE display."""

    def __init__(self, display, sound):
        self.display = display
        self.sound = sound
        self.reset()

    def reset(self):
        """Reset game state."""
        # Snake starts in center, moving right, with 5 segments
        start_x = WIDTH // 2
        start_y = HEIGHT // 2
        self.snake = [(start_x - i, start_y) for i in range(5)]  # 5 segments
        self.direction = (1, 0)  # (dx, dy)
        self.next_direction = (1, 0)
        self.food = self._spawn_food()
        self.score = 0
        self.state = 'playing'  # playing, gameover
        self.frame = 0
        self.move_timer = 0
        self.move_delay = 6  # Frames between moves (slower = easier)

    def _spawn_food(self):
        """Spawn food at random location not on snake."""
        while True:
            x = random.randint(1, WIDTH - 2)
            y = random.randint(1, HEIGHT - 2)
            if (x, y) not in self.snake:
                return (x, y)

    def update(self, up, down, left, right):
        """Update snake game state."""
        if self.state != 'playing':
            self.frame += 1
            return

        self.frame += 1

        # Update direction (can't reverse)
        if up and self.direction != (0, 1):
            self.next_direction = (0, -1)
        elif down and self.direction != (0, -1):
            self.next_direction = (0, 1)
        elif left and self.direction != (1, 0):
            self.next_direction = (-1, 0)
        elif right and self.direction != (-1, 0):
            self.next_direction = (1, 0)

        # Move snake at fixed intervals
        self.move_timer += 1
        if self.move_timer < self.move_delay:
            return
        self.move_timer = 0

        self.direction = self.next_direction

        # Calculate new head position
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])

        # Check wall collision
        if new_head[0] < 0 or new_head[0] >= WIDTH or new_head[1] < 0 or new_head[1] >= HEIGHT:
            self.state = 'gameover'
            self.sound.play("gameover")
            self.sound.speak(f"Snake died! Score {self.score}", speed=140, pitch=50)
            return

        # Check self collision
        if new_head in self.snake:
            self.state = 'gameover'
            self.sound.play("gameover")
            self.sound.speak(f"Snake died! Score {self.score}", speed=140, pitch=50)
            return

        # Move snake
        self.snake.insert(0, new_head)

        # Check food collision
        if new_head == self.food:
            self.score += 10
            self.food = self._spawn_food()
            self.sound.play("score")
            # Speed up slightly
            if self.move_delay > 2:
                self.move_delay = max(2, self.move_delay - 0.2)
        else:
            self.snake.pop()  # Remove tail if no food eaten

    def render(self):
        """Render snake game."""
        self.display.clear()

        if self.state == 'playing':
            # Draw border
            for x in range(WIDTH):
                self.display.set_pixel(x, 0)
                self.display.set_pixel(x, HEIGHT - 1)
            for y in range(HEIGHT):
                self.display.set_pixel(0, y)
                self.display.set_pixel(WIDTH - 1, y)

            # Draw snake
            for i, (x, y) in enumerate(self.snake):
                self.display.set_pixel(x, y)
                # Make head bigger
                if i == 0:
                    if x + 1 < WIDTH:
                        self.display.set_pixel(x + 1, y)
                    if y + 1 < HEIGHT:
                        self.display.set_pixel(x, y + 1)

            # Draw food (blinking)
            if (self.frame // 4) % 2 == 0:
                fx, fy = self.food
                self.display.set_pixel(fx, fy)
                self.display.set_pixel(fx + 1, fy)
                self.display.set_pixel(fx, fy + 1)
                self.display.set_pixel(fx + 1, fy + 1)

            # Draw score
            self.display.draw_text(WIDTH - 20, 2, str(self.score))

        else:
            # Game over
            self.display.draw_centered_text(3, "GAME OVER")
            self.display.draw_centered_text(9, f"SCORE {self.score}")
            if (self.frame // 30) % 2 == 0:
                self.display.draw_centered_text(15, "PRESS A")


class DrawGame:
    """Simple drawing game with joystick cursor."""

    def __init__(self, display, sound):
        self.display = display
        self.sound = sound
        self.reset()

    def reset(self):
        """Reset game state."""
        self.cursor_x = WIDTH // 2
        self.cursor_y = HEIGHT // 2
        self.vel_x = 0.0  # Current smoothed velocity
        self.vel_y = 0.0
        self.canvas = set()  # Set of (x, y) pixels that are drawn
        self.history = []  # History for undo (list of pixels added)
        self.frame = 0
        self.has_drawn = False  # True once user starts drawing
        self.last_action_frame = 0  # Frame of last draw/undo action

    def update(self, stick_x, stick_y, draw_button):
        """Update draw game state.

        stick_x, stick_y: analog values 0-255 (128=center)
        draw_button: True if drawing
        """
        self.frame += 1

        # Convert analog to target velocity with deadzone
        def analog_to_target(val):
            centered = val - 128
            if abs(centered) < 40:  # Large deadzone for precision
                return 0
            return centered / 300.0  # Very slow for easy drawing

        target_x = analog_to_target(stick_x)
        target_y = analog_to_target(stick_y)

        # Smooth velocity interpolation (easing)
        smooth = 0.15  # Lower = smoother but slower response
        self.vel_x += (target_x - self.vel_x) * smooth
        self.vel_y += (target_y - self.vel_y) * smooth

        # Stop completely when nearly still
        if abs(self.vel_x) < 0.001:
            self.vel_x = 0
        if abs(self.vel_y) < 0.001:
            self.vel_y = 0

        # Move cursor with smoothed velocity
        self.cursor_x += self.vel_x
        self.cursor_y += self.vel_y

        # Clamp to screen
        self.cursor_x = max(0, min(WIDTH - 1, self.cursor_x))
        self.cursor_y = max(0, min(HEIGHT - 1, self.cursor_y))

        # Draw if button held
        if draw_button:
            pixel = (int(self.cursor_x), int(self.cursor_y))
            if pixel not in self.canvas:
                self.canvas.add(pixel)
                self.history.append(pixel)  # Track for undo
                self.has_drawn = True
                self.last_action_frame = self.frame

    def undo(self):
        """Undo last drawn pixel."""
        if self.history:
            pixel = self.history.pop()
            self.canvas.discard(pixel)
            self.sound.play("jump")
            self.last_action_frame = self.frame

    def is_idle(self):
        """Check if idle for 15 seconds (900 frames at 60fps)."""
        return self.frame - self.last_action_frame > 900

    def clear_canvas(self):
        """Clear the drawing."""
        self.canvas.clear()
        self.sound.play("score")

    def render(self):
        """Render draw game."""
        self.display.clear()

        # Draw canvas pixels
        for x, y in self.canvas:
            self.display.set_pixel(x, y)

        # Get integer cursor position
        cx, cy = int(self.cursor_x), int(self.cursor_y)

        # Draw cursor (blinking)
        if (self.frame // 4) % 2 == 0:
            self.display.set_pixel(cx, cy)

        # Draw small crosshair around cursor
        if cx > 0:
            self.display.set_pixel(cx - 1, cy)
        if cx < WIDTH - 1:
            self.display.set_pixel(cx + 1, cy)
        if cy > 0:
            self.display.set_pixel(cx, cy - 1)
        if cy < HEIGHT - 1:
            self.display.set_pixel(cx, cy + 1)

        # Only show instructions before user starts drawing
        if not self.has_drawn:
            self.display.draw_text(2, 1, "LB:DRAW B:UNDO A:CLR")


class Game:
    """Main game controller."""

    INITIAL_SPEED = 0.55  # Slightly slower start for easier beginning
    MAX_SPEED = 2.2  # Slightly lower max for more manageable late game
    HIGH_SCORE_FILE = "/var/lib/dino_highscore"

    # Milestone thresholds
    VOLCANO_MILESTONE = 500
    INVERT_MILESTONES = [1000, 1500]
    ROBOT_MILESTONE = 1500
    UFO_MILESTONE = 2000

    def __init__(self, display, input_handler, duck_enabled=True, sound_enabled=True):
        self.display = display
        self.input = input_handler
        self.duck_enabled = duck_enabled
        self.sound = Sound(enabled=sound_enabled)
        self.state = 'start'  # start, playing, gameover, volcano, paused, pong
        self.score = 0
        self.high_score = self._load_high_score()
        self.speed = self.INITIAL_SPEED
        self.dino = None
        self.obstacles = []
        self.next_obstacle_time = 0
        self.animation_frame = 0
        self.ground_offset = 0.0

        # Lives system
        self.lives = MAX_LIVES
        self.invincible_frames = 0  # Brief invincibility after hit

        # Milestone tracking
        self.milestones_triggered = set()
        self.invert_screen = False
        self.invert_end_frame = 0

        # Volcano animation state
        self.volcano_frame = 0

        # Controller state
        self.controller_connected = True
        self.last_controller_check = 0

        # Mini games
        self.pong = PongGame(display, self.sound)
        self.snake = SnakeGame(display, self.sound)
        self.draw = DrawGame(display, self.sound)

        # Randomized scene order for start screen animations
        self.scene_order = list(range(16))
        random.shuffle(self.scene_order)
        self.current_scene_idx = -1  # Start at -1 so first scene triggers speech

        # Smooth animation state for fluid eye movements
        self.smooth_pupil_x = 0.0  # Current smooth pupil position
        self.smooth_pupil_y = 0.0
        self.smooth_eye_open_l = 1.0  # 0=closed, 0.5=half, 1=open, 1.5=wide
        self.smooth_eye_open_r = 1.0
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

        # Reset lives and milestones
        self.lives = MAX_LIVES
        self.invincible_frames = 0
        self.milestones_triggered = set()
        self.invert_screen = False
        self.invert_end_frame = 0

    def check_collision(self, box1, box2):
        """Check if two hitboxes collide."""
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)

    def _check_controller(self):
        """Check if controller is still connected."""
        if not HAS_EVDEV:
            return True

        # Only check periodically (every 60 frames / 1 second)
        now = time.time()
        if now - self.last_controller_check < 1.0:
            return self.controller_connected

        self.last_controller_check = now

        # Check if we have any working gamepad
        has_gamepad = False
        for kb in self.input.keyboards[:]:  # Copy list to allow modification
            try:
                # Try to read device info to check if still connected
                _ = kb.name
                caps = kb.capabilities()
                if ecodes.EV_KEY in caps:
                    keys = caps[ecodes.EV_KEY]
                    if any(k in keys for k in [ecodes.BTN_A, ecodes.BTN_GAMEPAD, ecodes.BTN_SOUTH]):
                        has_gamepad = True
            except (OSError, IOError):
                # Device disconnected
                self.input.keyboards.remove(kb)

        self.controller_connected = has_gamepad or self.input.use_terminal_input
        return self.controller_connected

    def _check_milestones(self):
        """Check and trigger milestone events."""
        # Volcano eruption at 500 points
        if self.score >= self.VOLCANO_MILESTONE and 'volcano' not in self.milestones_triggered:
            self.milestones_triggered.add('volcano')
            self.state = 'volcano'
            self.volcano_frame = 0
            self.sound.play("surprise")
            self.sound.speak("Volcano eruption!", speed=140, pitch=50)

        # Screen invert at 1000 and 1500 points
        for milestone in self.INVERT_MILESTONES:
            key = f'invert_{milestone}'
            if self.score >= milestone and key not in self.milestones_triggered:
                self.milestones_triggered.add(key)
                self.invert_screen = True
                self.invert_end_frame = self.animation_frame + 300  # 5 seconds
                self.sound.play("hypno")
                self.sound.speak("Inverted!", speed=160, pitch=70)

        # Announce new enemies at milestones
        if self.score >= self.ROBOT_MILESTONE and 'robot_announce' not in self.milestones_triggered:
            self.milestones_triggered.add('robot_announce')
            self.sound.speak("Robots incoming!", speed=150, pitch=60)

        if self.score >= self.UFO_MILESTONE and 'ufo_announce' not in self.milestones_triggered:
            self.milestones_triggered.add('ufo_announce')
            self.sound.speak("UFOs detected!", speed=150, pitch=60)

    def _get_difficulty_params(self):
        """Get difficulty parameters based on score."""
        # Progressive difficulty tiers - more gradual ramp for easier gameplay
        if self.score >= 3000:
            return {'spawn_min': 0.7, 'spawn_max': 1.1, 'speed_mult': 1.3}
        elif self.score >= 2000:
            return {'spawn_min': 0.8, 'spawn_max': 1.3, 'speed_mult': 1.2}
        elif self.score >= 1000:
            return {'spawn_min': 0.9, 'spawn_max': 1.6, 'speed_mult': 1.15}
        elif self.score >= 500:
            return {'spawn_min': 1.1, 'spawn_max': 2.0, 'speed_mult': 1.05}
        else:
            return {'spawn_min': 1.4, 'spawn_max': 2.8, 'speed_mult': 1.0}

    def update(self):
        """Update game logic."""
        jump, duck, quit_req = self.input.poll()

        if quit_req:
            return False

        # Check controller connection
        if not self._check_controller():
            if self.state == 'playing':
                self.state = 'paused'
                self.animation_frame = 0
            # Still allow terminal input if available
            if not self.input.use_terminal_input:
                return True

        if self.state == 'start':
            self.animation_frame += 1
            # Game selection: A=Dino, B=Pong, Y=Snake, Start=Draw
            if self.input.select_pong:
                self.state = 'pong'
                self.pong.reset()
                self.sound.play("start")
                self.sound.speak("Pong!", speed=180, pitch=80)
            elif self.input.select_snake:
                self.state = 'snake'
                self.snake.reset()
                self.sound.play("start")
                self.sound.speak("Snake!", speed=180, pitch=80)
            elif self.input.select_draw:
                self.state = 'draw'
                self.draw.reset()
                self.sound.play("start")
                self.sound.speak("Draw!", speed=180, pitch=80)
            elif jump:
                self.state = 'playing'
                self.reset()
                self.sound.play("start")
                self.sound.speak("Go!", speed=180, pitch=80)

        elif self.state == 'paused':
            # Controller disconnected - wait for reconnection
            self.animation_frame += 1
            if self._check_controller():
                self.state = 'playing'
                self.controller_connected = True
            elif jump:  # Allow terminal input to resume
                self.state = 'playing'

        elif self.state == 'volcano':
            # Volcano eruption animation
            self.volcano_frame += 1
            if self.volcano_frame >= 180:  # 3 seconds at 60fps
                self.state = 'playing'
                self.volcano_frame = 0
                self.sound.speak("New enemies incoming!", speed=150, pitch=60)

        elif self.state == 'playing':
            # X button exits to menu
            if self.input.back_to_menu:
                self.state = 'start'
                self.animation_frame = 0
                return True

            # Check for milestone events
            self._check_milestones()

            # Handle invert screen timer
            if self.invert_screen and self.animation_frame >= self.invert_end_frame:
                self.invert_screen = False

            # Decrease invincibility timer
            if self.invincible_frames > 0:
                self.invincible_frames -= 1

            if jump and self.dino.on_ground and not self.dino.ducking:
                self.sound.play("jump")
            if jump:
                self.dino.jump()

            self.dino.duck(duck)
            self.dino.update()

            # Get difficulty parameters
            diff = self._get_difficulty_params()

            # Spawn obstacles with proper spacing based on difficulty
            if time.time() >= self.next_obstacle_time:
                self.obstacles.append(Obstacle(WIDTH, include_birds=True,
                                               duck_enabled=self.duck_enabled, score=self.score))
                self.next_obstacle_time = time.time() + random.uniform(diff['spawn_min'], diff['spawn_max'])

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

            # Check collisions (only if not invincible)
            if self.invincible_frames == 0:
                dino_box = self.dino.get_hitbox()
                for obs in self.obstacles:
                    if self.check_collision(dino_box, obs.get_hitbox()):
                        self.lives -= 1
                        self.obstacles.remove(obs)  # Remove the obstacle that hit

                        if self.lives <= 0:
                            # Game over
                            self.state = 'gameover'
                            self.animation_frame = 0
                            self.sound.play("gameover")
                            if self.score > self.high_score:
                                self.high_score = self.score
                                self._save_high_score()
                                self.sound.speak(f"Game over! New high score {self.score}!", speed=130, pitch=40)
                            else:
                                self.sound.speak(f"Game over! Score {self.score}", speed=130, pitch=40)
                        else:
                            # Lost a life but continue
                            self.invincible_frames = 120  # 2 seconds invincibility
                            self.sound.play("hit")
                            self.sound.speak(f"{self.lives} lives left!", speed=150, pitch=50)
                        break

            # Update ground scroll
            self.ground_offset += self.speed
            if self.ground_offset >= 8:
                self.ground_offset -= 8

            # Increase difficulty gradually
            old_speed = self.speed
            diff = self._get_difficulty_params()
            base_speed = self.INITIAL_SPEED + self.score // 100 * 0.10
            self.speed = min(base_speed * diff['speed_mult'], self.MAX_SPEED)

            # Play speedup sound when speed increases
            if self.speed > old_speed and old_speed > self.INITIAL_SPEED:
                self.sound.play("speedup")

            self.animation_frame += 1

        elif self.state == 'gameover':
            self.animation_frame += 1
            # X button exits to menu immediately
            if self.input.back_to_menu:
                self.state = 'start'
                self.animation_frame = 0
                random.shuffle(self.scene_order)
                self.current_scene_idx = -1
                return True
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

        elif self.state == 'pong':
            # X button exits to menu
            if self.input.back_to_menu:
                self.state = 'start'
                self.animation_frame = 0
                return True

            # Each controller's RIGHT stick controls its own paddle (analog values 0-255)
            # Also Y button = up, A button = down
            self.pong.update(
                self.input.p1_rstick_y,  # P1 analog stick (0-255)
                self.input.p2_rstick_y,  # P2 analog stick (0-255)
                self.input.p1_btn_up, self.input.p1_btn_down,
                self.input.p2_btn_up, self.input.p2_btn_down
            )

            # Check if game is over and user wants to return
            if self.pong.state != 'playing':
                if jump or self.input.select_pong:
                    if self.pong.frame >= 180:  # 3 seconds after game ends
                        self.state = 'start'
                        self.animation_frame = 0

        elif self.state == 'snake':
            # X button exits to menu
            if self.input.back_to_menu:
                self.state = 'start'
                self.animation_frame = 0
                return True

            # Get directional input from RIGHT joystick or D-pad
            # rstick values are 0-255, center=128, so use thresholds
            up = self.input.rstick_y < 80 or self.input.p1_up
            down = self.input.rstick_y > 176 or self.input.p1_down
            left = self.input.rstick_x < 80 or self.input.stick_x < 0
            right = self.input.rstick_x > 176 or self.input.stick_x > 0

            self.snake.update(up, down, left, right)

            # Restart or return to menu on game over
            if self.snake.state == 'gameover':
                if jump:
                    self.snake.reset()
                elif self.snake.frame >= 180:  # Auto-return after 3 seconds
                    self.state = 'start'
                    self.animation_frame = 0

        elif self.state == 'draw':
            # X button exits to menu
            if self.input.back_to_menu:
                self.state = 'start'
                self.animation_frame = 0
                return True

            # Auto-return to menu if idle for 15 seconds
            if self.draw.is_idle():
                self.state = 'start'
                self.animation_frame = 0
                return True

            # A button clears canvas
            if jump:
                self.draw.clear_canvas()

            # B button undoes last pixel
            if duck:
                self.draw.undo()

            # Update draw game with RIGHT joystick and trigger button
            self.draw.update(self.input.rstick_x, self.input.rstick_y, self.input.draw_button)

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
        elif self.state == 'volcano':
            self._render_volcano()
        elif self.state == 'paused':
            self._render_paused()
        elif self.state == 'pong':
            self.pong.render()
            self.display.render()
            return
        elif self.state == 'snake':
            self.snake.render()
            self.display.render()
            return
        elif self.state == 'draw':
            self.draw.render()
            self.display.render()
            return

        # Apply screen invert if active
        if self.invert_screen:
            self._invert_buffer()

        self.display.render()

    def _invert_buffer(self):
        """Invert all pixels in the display buffer."""
        for i in range(len(self.display.buffer)):
            self.display.buffer[i] = ~self.display.buffer[i] & 0xFF

    def _render_volcano(self):
        """Render volcano eruption animation."""
        # Draw volcano base at bottom center
        volcano_x = (WIDTH - 9) // 2
        volcano_y = GROUND_Y - 4

        for row_idx, row in enumerate(VOLCANO_BASE):
            for col_idx, char in enumerate(row):
                if char == 'X':
                    self.display.set_pixel(volcano_x + col_idx, volcano_y + row_idx)

        # Animate lava particles rising
        frame = self.volcano_frame
        for i in range(5):
            # Multiple particles at different heights
            particle_y = volcano_y - 2 - ((frame + i * 20) % 15)
            particle_x = volcano_x + 4 + random.randint(-2, 2)
            if 0 <= particle_y < HEIGHT:
                self.display.set_pixel(particle_x, particle_y)

        # Draw explosion particles
        if frame < 60:
            for _ in range(3):
                px = volcano_x + 4 + random.randint(-6, 6)
                py = volcano_y - 3 - random.randint(0, 8)
                if 0 <= px < WIDTH and 0 <= py < HEIGHT:
                    self.display.set_pixel(px, py)

        # Text
        if frame < 90:
            self.display.draw_centered_text(1, "VOLCANO!")
        else:
            self.display.draw_centered_text(1, "NEW ENEMIES!")

        # Show score
        score_str = str(self.score)
        self.display.draw_text(WIDTH - len(score_str) * 4 - 2, 8, score_str)

    def _render_paused(self):
        """Render paused screen (controller disconnected)."""
        # Flashing text
        if (self.animation_frame // 30) % 2 == 0:
            self.display.draw_centered_text(2, "CONTROLLER")
            self.display.draw_centered_text(8, "DISCONNECTED")
        else:
            self.display.draw_centered_text(5, "RECONNECT")

        # Show current score
        score_str = f"SCORE {self.score}"
        self.display.draw_centered_text(14, score_str)

    def _draw_lives(self):
        """Draw lives as hearts in top-left corner."""
        for i in range(self.lives):
            x = 2 + i * 6
            for row_idx, row in enumerate(HEART):
                for col_idx, char in enumerate(row):
                    if char == 'X':
                        self.display.set_pixel(x + col_idx, 1 + row_idx)

    def _play_anim_sound(self, sound_name):
        """Play animation sound only once per frame."""
        if self.animation_frame != self.last_sound_frame:
            self.sound.play(sound_name)
            self.last_sound_frame = self.animation_frame

    def _render_start_screen(self):
        """Render animated start screen with anime-style face and smooth animations."""
        # Different animation scenes - 240 frames per scene at 60fps = 4 seconds each
        cycle = self.animation_frame % 240
        t = cycle / 240.0  # Normalized time 0-1 for smooth math

        # Check if we need to advance to next scene
        new_scene_idx = (self.animation_frame // 240) % 16
        if new_scene_idx != self.current_scene_idx:
            self.current_scene_idx = new_scene_idx
            if new_scene_idx == 0:
                random.shuffle(self.scene_order)
            scene_messages = {
                0: "A for Dino!", 1: "Wake me up!", 2: "Y for Snake!", 3: "B for Pong!",
                4: "A for Dino!", 5: "Start for Draw!", 6: "I see you!", 7: "B for Pong!",
                8: "Y for Snake!", 9: "Boing boing!", 10: "Start for Draw!", 11: "Come play!",
                12: "So nervous!", 13: "X to exit!", 14: "Hey there!", 15: "Choose game!",
            }
            scene = self.scene_order[self.current_scene_idx]
            if scene in scene_messages:
                self.sound.speak(scene_messages[scene], speed=140, pitch=60)

        big_cycle = self.scene_order[self.current_scene_idx]

        eye_left_x, eye_right_x, eye_y = 32, 88, 1

        # Easing functions for smooth motion
        def ease_in_out(x):
            return 0.5 - 0.5 * math.cos(x * math.pi)

        def ease_out(x):
            return math.sin(x * math.pi * 0.5)

        # Target values for this frame
        target_px, target_py = 0.0, 0.0
        target_eye_l, target_eye_r = 1.0, 1.0  # 0=closed, 0.5=half, 1=open, 1.5=wide
        msg = "PRESS TO PLAY!"
        special_render = None

        if big_cycle == 0:
            # Smooth looking around with sine curves
            if t == 0: self._play_anim_sound("wink")
            # Smooth circular gaze pattern
            target_px = 2.5 * math.sin(t * math.pi * 4)
            target_py = 2.0 * math.cos(t * math.pi * 2)
            # Occasional blinks
            if 0.15 < t < 0.22 or 0.55 < t < 0.62:
                target_eye_l = target_eye_r = 0.0

        elif big_cycle == 1:
            # Sleepy then wake up - smooth easing
            if t == 0: self._play_anim_sound("sleepy")
            if t < 0.3:
                target_eye_l = target_eye_r = 0.5
                target_py = 2.0 * ease_in_out(t / 0.3)
            elif t < 0.6:
                target_eye_l = target_eye_r = 0.0
                target_py = 2.0
            elif t < 0.85:
                p = (t - 0.6) / 0.25
                target_eye_l = target_eye_r = 0.5 * ease_out(p)
                target_py = 2.0 * (1 - p)
            else:
                p = (t - 0.85) / 0.15
                target_eye_l = target_eye_r = 1.0 + 0.5 * ease_out(p)
                target_py = -2.0 * ease_out(p)
            msg = "WAKE ME UP!"

        elif big_cycle == 2:
            # Smooth eye roll circle using sine/cosine
            if t == 0: self._play_anim_sound("look")
            angle = t * math.pi * 3  # 1.5 full rotations
            target_px = 2.5 * math.sin(angle)
            target_py = 2.0 * math.cos(angle)
            if 0.4 < t < 0.5:
                target_eye_l = target_eye_r = 0.0
            msg = "PLAY WITH ME!"

        elif big_cycle == 3:
            # Peek-a-boo with smooth transitions
            if t == 0: self._play_anim_sound("peek")
            if t < 0.2:
                target_px = 2.0 * math.sin(t * math.pi * 2)
            elif t < 0.3:
                p = (t - 0.2) / 0.1
                target_eye_l = target_eye_r = 1.0 - p
            elif t < 0.45:
                target_eye_l = target_eye_r = 0.0
            elif t < 0.55:
                # Right eye peeks
                p = (t - 0.45) / 0.1
                target_eye_r = p
                target_px = -2.0 * p
            elif t < 0.7:
                target_eye_l = 0.0
                target_px = -2.0
            elif t < 0.8:
                p = (t - 0.7) / 0.1
                target_eye_l = p
                target_px = 2.0 * (p - 1)
            else:
                p = (t - 0.8) / 0.2
                target_px = 2.0 * (1 - p) * math.cos(p * math.pi)
            msg = "PEEK A BOO!"

        elif big_cycle == 4:
            # Dizzy spiral
            if t == 0: self._play_anim_sound("dizzy")
            special_render = 'dizzy' if t < 0.75 else None
            if t >= 0.75:
                p = (t - 0.75) / 0.25
                target_eye_l = target_eye_r = 0.5 + 0.5 * ease_out(p)
                target_px = 2.0 * math.sin(p * math.pi * 4) * (1 - p)

        elif big_cycle == 5:
            # Smooth side to side with blinks
            if t == 0: self._play_anim_sound("blink")
            target_px = 2.5 * math.sin(t * math.pi * 2)
            target_py = 0.5 * math.sin(t * math.pi * 4)
            if 0.25 < t < 0.32 or 0.75 < t < 0.82:
                target_eye_l = target_eye_r = 0.0
            msg = "AWESOME!"

        elif big_cycle == 6:
            # Suspicious scanning
            if t == 0: self._play_anim_sound("look")
            target_px = 2.5 * math.sin(t * math.pi * 1.5 - math.pi/2)
            if 0.4 < t < 0.7:
                target_eye_l = target_eye_r = 0.5
            if t > 0.85:
                target_eye_l = 0.0
            msg = "I SEE YOU!"

        elif big_cycle == 7:
            # Crazy rapid movement with alternating blinks
            if t == 0: self._play_anim_sound("dizzy")
            speed = 8 + 4 * math.sin(t * math.pi)  # Variable speed
            target_px = 2.5 * math.sin(t * math.pi * speed)
            target_py = 2.0 * math.cos(t * math.pi * speed * 0.7)
            blink_phase = (t * 10) % 1
            if blink_phase < 0.3:
                target_eye_l = 0.0
            elif 0.5 < blink_phase < 0.8:
                target_eye_r = 0.0

        elif big_cycle == 8:
            # Hypnotic opposite direction eyes
            if t == 0: self._play_anim_sound("hypno")
            angle = t * math.pi * 4
            px = 2.5 * math.sin(angle)
            py = 2.0 * math.cos(angle)
            special_render = ('hypno', px, py)
            msg = "HYPNOTIZING!"

        elif big_cycle == 9:
            # Bouncy with smooth sine bounce
            if t == 0: self._play_anim_sound("bounce")
            bounce_t = t * 3  # 3 bounces
            target_py = 2.5 * abs(math.sin(bounce_t * math.pi))
            target_px = 2.0 * math.sin(t * math.pi * 2)
            if 0.2 < (t * 3 % 1) < 0.4:
                target_eye_l = target_eye_r = 1.5
            msg = "BOING BOING!"

        elif big_cycle == 10:
            # Reading with smooth scanning
            if t == 0: self._play_anim_sound("look")
            line = int(t * 3) % 2
            line_t = (t * 3) % 1
            target_px = -2.5 + 5.0 * ease_in_out(line_t)
            target_py = 1.0 + line * 1.5
            if 0.45 < t < 0.55:
                target_eye_l = target_eye_r = 0.0
            msg = "INTERESTING!"

        elif big_cycle == 11:
            # Alternating winks with smooth pupil
            if t == 0: self._play_anim_sound("flirt")
            target_px = 2.5 * math.sin(t * math.pi * 2)
            if 0.15 < t < 0.35:
                target_eye_l = 0.0
            elif 0.55 < t < 0.75:
                target_eye_r = 0.0
            elif t > 0.85:
                target_eye_l = target_eye_r = 0.5
            msg = "COME PLAY!"

        elif big_cycle == 12:
            # Nervous trembling with small rapid movements
            if t == 0: self._play_anim_sound("nervous")
            shake = 0.8 * math.sin(t * math.pi * 30)  # Fast shake
            target_px = shake
            target_py = shake * 0.5
            if 0.4 < t < 0.6:
                target_eye_l = target_eye_r = 1.5
            msg = "SO NERVOUS!"

        elif big_cycle == 13:
            # Searching with smooth scanning pattern
            if t == 0: self._play_anim_sound("search")
            target_px = 2.5 * math.sin(t * math.pi * 5)
            target_py = 2.0 * math.sin(t * math.pi * 3 + math.pi/4)
            if 0.2 < t < 0.35 or 0.6 < t < 0.75:
                target_eye_l = target_eye_r = 1.5
            msg = "WHERE IS IT?"

        elif big_cycle == 14:
            # Flirty with playful movements
            if t == 0: self._play_anim_sound("flirt")
            target_px = 2.0 * math.sin(t * math.pi * 3)
            target_py = 1.5 * math.cos(t * math.pi * 2)
            # Quick blinks
            blink_times = [0.12, 0.28, 0.45]
            for bt in blink_times:
                if bt < t < bt + 0.06:
                    target_eye_l = target_eye_r = 0.0
            if t > 0.7:
                target_eye_l = target_eye_r = 0.5
            msg = "HEY THERE!"

        elif big_cycle == 15:
            # Figure 8 with smooth lissajous curve
            if t == 0: self._play_anim_sound("hypno")
            target_px = 2.5 * math.sin(t * math.pi * 4)
            target_py = 2.0 * math.sin(t * math.pi * 2)
            if 0.4 < t < 0.5:
                target_eye_l = target_eye_r = 0.0

        # Smooth interpolation to target positions
        smooth = 0.12
        self.smooth_pupil_x += (target_px - self.smooth_pupil_x) * smooth
        self.smooth_pupil_y += (target_py - self.smooth_pupil_y) * smooth
        self.smooth_eye_open_l += (target_eye_l - self.smooth_eye_open_l) * smooth * 2
        self.smooth_eye_open_r += (target_eye_r - self.smooth_eye_open_r) * smooth * 2

        # Convert smooth eye values to states
        def eye_val_to_state(v):
            if v < 0.25: return 'closed'
            elif v < 0.75: return 'half'
            elif v < 1.25: return 'open'
            else: return 'wide'

        left_state = eye_val_to_state(self.smooth_eye_open_l)
        right_state = eye_val_to_state(self.smooth_eye_open_r)
        pupil_dx = int(round(self.smooth_pupil_x))
        pupil_dy = int(round(self.smooth_pupil_y))

        def draw_anime_eye(cx, cy, state, pdx, pdy):
            pdx = max(-3, min(3, pdx))
            pdy = max(-3, min(3, pdy))
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
            else:  # open
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

        # Handle special render modes
        if special_render == 'dizzy':
            draw_anime_eye(eye_left_x, eye_y, 'dizzy', 0, 0)
            draw_anime_eye(eye_right_x, eye_y, 'dizzy', 0, 0)
        elif isinstance(special_render, tuple) and special_render[0] == 'hypno':
            _, px, py = special_render
            pdx, pdy = int(round(px)), int(round(py))
            draw_anime_eye(eye_left_x, eye_y, left_state, pdx, pdy)
            draw_anime_eye(eye_right_x, eye_y, right_state, -pdx, -pdy)
        else:
            draw_anime_eye(eye_left_x, eye_y, left_state, pupil_dx, pupil_dy)
            draw_anime_eye(eye_right_x, eye_y, right_state, pupil_dx, pupil_dy)

        # Alternate between scene message and game selection hints
        cycle_phase = (self.animation_frame // 180) % 6
        if cycle_phase == 1:
            msg = "A:DINO  B:PONG"
        elif cycle_phase == 3:
            msg = "Y:SNAKE ST:DRAW"
        elif cycle_phase == 5:
            msg = "X:EXIT GAME"

        self.display.draw_centered_text(13, msg)

    def _render_game(self):
        """Render game play."""
        # Draw solid ground line
        self.display.draw_line(0, GROUND_Y, WIDTH - 1, GROUND_Y)

        # Draw dinosaur (blink when invincible)
        if self.invincible_frames == 0 or (self.invincible_frames // 4) % 2 == 0:
            self.display.draw_sprite(self.dino.get_sprite(), self.dino.x, int(self.dino.y))

        # Draw obstacles
        for obs in self.obstacles:
            self.display.draw_sprite(obs.get_sprite(), int(obs.x), obs.y)

        # Draw lives (top left)
        self._draw_lives()

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
