# buse-dino

Dinosaur jumping game for BUSE 128x19 LED display (Chrome-style no-internet game)

## Controls

- **Enter** or **PageUp**: Jump / Start game
- **Space**: Duck (to avoid birds)
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

# Jump-only mode (birds at jumpable height, no duck needed - for single button setups)
python3 dino.py --no-duck

# Disable sound effects
python3 dino.py --no-sound
```

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

- Animated start screen with anime-style eyes (16 different animations in random order)
- Jumping dinosaur with running animation
- Duck to avoid flying birds (or use --no-duck for jump-only mode)
- Multiple obstacle types (cacti with L-shaped arms, birds)
- Increasing difficulty as score grows
- Game over screen with score and high score display
- Auto-returns to start screen after game over
- 60 FPS smooth animations
- 4x5 pixel font for clear text readability

## Sound Features

- Retro-style sound effects inspired by classic games (Mario, Zelda, Sonic, Pokemon)
- Text-to-speech announces animation messages using espeak
- Sound effects include:
  - Jump sound when dinosaur jumps
  - Cheerful arpeggio when scoring points
  - Triumphant fanfare every 100 points (milestone)
  - Speed-up warning sound when game accelerates
  - Dramatic game over melody
  - Various animation sounds (wink, peek, dizzy, bounce, etc.)
- All sounds generated programmatically (no external audio files needed)
- Use `--no-sound` flag to disable all audio
