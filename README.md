# buse-dino

Multi-game collection for BUSE 128x19 LED display on Raspberry Pi. Includes 4 games: Dino (Chrome-style jumper), Pong (2-player), Snake, and Draw (freehand drawing).

## Controls

### Game Selection (from start screen)
- **A Button**: Dino game
- **B Button**: Pong (2-player)
- **Y Button**: Snake
- **LB/Start Button**: Draw

### In Any Game
- **X Button**: Exit to main menu

### Dino Game
- **A / Up / Enter**: Jump
- **B / Down / Space**: Duck (to avoid birds)

### Pong (2-player)
- **Right Joystick**: Move paddle up/down (smooth analog control)
- **Y Button**: Paddle up
- **A Button**: Paddle down
- Each controller controls one paddle

### Snake
- **Right Joystick**: Change direction

### Draw
- **Right Joystick**: Move cursor (smooth with easing)
- **LB Button**: Draw pixels
- **B Button**: Undo last pixel
- **A Button**: Clear canvas
- Auto-returns to menu after 15 seconds idle

### Keyboard (fallback)
- **Enter** or **PageUp**: Jump / Start game
- **Space**: Duck
- **Escape** or **q**: Quit

## Requirements

```bash
sudo apt install python3-evdev espeak alsa-utils
```

## Usage

```bash
# Framebuffer mode (on Raspberry Pi with BUSE display)
python3 dino.py

# Terminal test mode (for development/testing)
python3 dino.py --terminal

# Both modes simultaneously
python3 dino.py --both

# Custom framebuffer device
python3 dino.py --fb-path /dev/fb1

# Jump-only mode (birds at jumpable height, no duck needed)
python3 dino.py --no-duck

# Disable sound effects
python3 dino.py --no-sound
```

## Bluetooth Gamepad Setup

Supports GameSir Nova Lite and other Xbox-style controllers.

```bash
# Test gamepad connection
python3 test_gamepad.py

# List all input devices
python3 test_gamepad.py --list

# Test 2-player mode
python3 test_gamepad.py --multi
```

### Pairing a GameSir Nova Lite
1. Put controller in pairing mode (hold Home + pairing button)
2. Run `bluetoothctl` on the RPi
3. Commands: `scan on`, `pair <MAC>`, `connect <MAC>`, `trust <MAC>`

Controllers are detected dynamically - no restart needed if a controller disconnects and reconnects.

## Install as systemd service

```bash
# Copy files to /opt/buse-dino
sudo mkdir -p /opt/buse-dino
sudo cp dino.py /opt/buse-dino/
sudo chmod +x /opt/buse-dino/dino.py

# Install and enable service
sudo cp buse-dino.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable buse-dino
sudo systemctl start buse-dino

# Check status
sudo systemctl status buse-dino

# View logs
sudo journalctl -u buse-dino -f
```

## Game Features

### Start Screen
- Animated anime-style eyes with 16 different animations in random order
- Smooth sine/cosine-based motion with easing functions
- Text-to-speech announces current animation

### Dino Game
- Chrome-style dinosaur jumping game
- Running animation with duck ability
- Multiple obstacle types (cacti with L-shaped arms, birds)
- Increasing difficulty as score grows
- High score tracking

### Pong
- Classic 2-player Pong
- Smooth analog paddle control with right joystick
- Ball speeds up over time

### Snake
- Classic snake game
- Starts with 5 segments
- Grows when eating food

### Draw
- Freehand pixel drawing
- Smooth cursor with velocity easing
- Undo support (B button)
- 15-second idle timeout returns to menu

### General
- 60 FPS smooth animations
- 4x5 pixel font for clear text
- Auto-returns to start screen after game over

## Sound Features

- Retro-style sound effects inspired by classic games
- Text-to-speech announces animation messages using espeak
- Sound effects include:
  - Jump sound when dinosaur jumps
  - Cheerful arpeggio when scoring points
  - Triumphant fanfare every 100 points
  - Speed-up warning sound when game accelerates
  - Dramatic game over melody
  - Various animation sounds (wink, peek, dizzy, bounce, etc.)
- All sounds generated programmatically (no external audio files needed)
- Use `--no-sound` flag to disable all audio
