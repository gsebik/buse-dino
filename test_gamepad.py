#!/usr/bin/env python3
"""
Bluetooth Gamepad Test Script for GameSir Nova Lite

Tests Bluetooth controller connection and displays all input events.
Use this to verify your controller is working and identify button/axis codes.

Pairing instructions:
1. Put controller in pairing mode (usually hold home + pair button)
2. On RPi: bluetoothctl
3. Commands: scan on, pair <MAC>, connect <MAC>, trust <MAC>
4. Run this script to test

Usage:
  python3 test_gamepad.py              # Auto-detect gamepad
  python3 test_gamepad.py --list       # List all input devices
  python3 test_gamepad.py --device N   # Use specific device number
"""

import argparse
import sys
import time

try:
    from evdev import InputDevice, categorize, ecodes, list_devices
    HAS_EVDEV = True
except ImportError:
    HAS_EVDEV = False
    print("Error: evdev library not found")
    print("Install with: sudo apt install python3-evdev")
    sys.exit(1)


def list_all_devices():
    """List all input devices with their capabilities."""
    devices = list_devices()
    print(f"\nFound {len(devices)} input devices:\n")

    for i, path in enumerate(devices):
        try:
            dev = InputDevice(path)
            caps = dev.capabilities(verbose=True)

            # Check for gamepad-like capabilities
            has_keys = ecodes.EV_KEY in dev.capabilities()
            has_abs = ecodes.EV_ABS in dev.capabilities()

            device_type = []
            if has_keys and has_abs:
                device_type.append("Gamepad/Joystick")
            elif has_keys:
                device_type.append("Keyboard/Buttons")
            if has_abs:
                device_type.append("Analog axes")

            type_str = ", ".join(device_type) if device_type else "Unknown"

            print(f"[{i}] {path}")
            print(f"    Name: {dev.name}")
            print(f"    Type: {type_str}")

            # Show gamepad-specific info
            if has_abs:
                abs_caps = dev.capabilities().get(ecodes.EV_ABS, [])
                axes = []
                for code in abs_caps:
                    if isinstance(code, tuple):
                        code = code[0]
                    name = ecodes.ABS.get(code, f"ABS_{code}")
                    axes.append(name)
                if axes:
                    print(f"    Axes: {', '.join(axes[:6])}" + ("..." if len(axes) > 6 else ""))

            print()

        except Exception as e:
            print(f"[{i}] {path} - Error: {e}\n")

    return devices


def find_gamepad():
    """Find a gamepad device automatically."""
    devices = list_devices()

    candidates = []

    for path in devices:
        try:
            dev = InputDevice(path)
            caps = dev.capabilities()
            name = dev.name.lower()

            # Look for gamepad indicators
            has_abs = ecodes.EV_ABS in caps
            has_keys = ecodes.EV_KEY in caps

            # Check for gamepad-specific buttons
            if has_keys:
                keys = caps[ecodes.EV_KEY]
                has_gamepad_btns = any(k in keys for k in [
                    ecodes.BTN_A, ecodes.BTN_B, ecodes.BTN_X, ecodes.BTN_Y,
                    ecodes.BTN_GAMEPAD, ecodes.BTN_SOUTH, ecodes.BTN_EAST,
                    ecodes.BTN_START, ecodes.BTN_SELECT, ecodes.BTN_MODE,
                    ecodes.BTN_TL, ecodes.BTN_TR,  # Shoulder buttons
                ])
            else:
                has_gamepad_btns = False

            # Check for analog sticks
            if has_abs:
                abs_caps = [c[0] if isinstance(c, tuple) else c for c in caps[ecodes.EV_ABS]]
                has_sticks = ecodes.ABS_X in abs_caps and ecodes.ABS_Y in abs_caps
            else:
                has_sticks = False

            # Score this device
            score = 0
            if has_gamepad_btns:
                score += 10
            if has_sticks:
                score += 5
            if 'gamepad' in name or 'controller' in name or 'joystick' in name:
                score += 3
            if 'gamesir' in name or 'nova' in name:
                score += 20  # Prefer GameSir
            if 'xbox' in name or 'sony' in name or 'nintendo' in name:
                score += 2

            if score > 0:
                candidates.append((score, dev))

        except Exception:
            continue

    if not candidates:
        return None

    # Return highest scoring device
    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def print_event(event):
    """Print a formatted event."""
    if event.type == ecodes.EV_KEY:
        key_event = categorize(event)
        state = "PRESSED" if key_event.keystate == 1 else "RELEASED" if key_event.keystate == 0 else "HELD"
        # Get button name
        btn_name = ecodes.BTN.get(event.code, ecodes.KEY.get(event.code, f"CODE_{event.code}"))
        print(f"  Button: {btn_name} ({event.code}) - {state}")

    elif event.type == ecodes.EV_ABS:
        axis_name = ecodes.ABS.get(event.code, f"ABS_{event.code}")
        print(f"  Axis: {axis_name} ({event.code}) = {event.value}")

    elif event.type == ecodes.EV_SYN:
        pass  # Sync events, ignore
    else:
        type_name = ecodes.EV.get(event.type, f"EV_{event.type}")
        print(f"  Event: type={type_name} code={event.code} value={event.value}")


def show_gamepad_state(device):
    """Show current state of gamepad axes."""
    try:
        abs_state = device.absinfo
        print("\n  Current axis states:")
        for code in [ecodes.ABS_X, ecodes.ABS_Y, ecodes.ABS_RX, ecodes.ABS_RY,
                     ecodes.ABS_Z, ecodes.ABS_RZ, ecodes.ABS_HAT0X, ecodes.ABS_HAT0Y]:
            try:
                info = device.absinfo(code)
                name = ecodes.ABS.get(code, f"ABS_{code}")
                # Calculate percentage
                range_val = info.max - info.min
                if range_val > 0:
                    pct = int(((info.value - info.min) / range_val) * 100)
                else:
                    pct = 0
                print(f"    {name}: {info.value} (min={info.min}, max={info.max}, {pct}%)")
            except Exception:
                pass
    except Exception as e:
        print(f"  Could not read axis state: {e}")


def monitor_gamepad(device):
    """Monitor gamepad input in real-time."""
    print(f"\nMonitoring: {device.name}")
    print(f"Path: {device.path}")
    print("-" * 50)
    print("Press buttons and move sticks to see events.")
    print("Press Ctrl+C to exit.\n")

    # Show initial state
    show_gamepad_state(device)
    print()

    # Mapping info for dino game
    print("Suggested button mappings for dino game:")
    print("  Jump: A/B button, D-pad Up, or Left stick up")
    print("  Duck: X/Y button, D-pad Down, or Left stick down")
    print("-" * 50)
    print()

    try:
        for event in device.read_loop():
            print_event(event)
    except KeyboardInterrupt:
        print("\n\nExiting...")


def monitor_multiple_gamepads(devices):
    """Monitor multiple gamepads simultaneously."""
    from select import select

    print(f"\nMonitoring {len(devices)} controllers:")
    for i, dev in enumerate(devices):
        print(f"  Player {i+1}: {dev.name} ({dev.path})")
    print("-" * 50)
    print("Press buttons on either controller to see events.")
    print("Press Ctrl+C to exit.\n")

    try:
        while True:
            r, _, _ = select(devices, [], [], 0.1)
            for dev in r:
                for event in dev.read():
                    # Find which player this is
                    player = devices.index(dev) + 1
                    if event.type == ecodes.EV_KEY:
                        key_event = categorize(event)
                        state = "PRESSED" if key_event.keystate == 1 else "RELEASED"
                        btn_name = ecodes.BTN.get(event.code, ecodes.KEY.get(event.code, f"CODE_{event.code}"))
                        print(f"  P{player} Button: {btn_name} ({event.code}) - {state}")
                    elif event.type == ecodes.EV_ABS:
                        axis_name = ecodes.ABS.get(event.code, f"ABS_{event.code}")
                        print(f"  P{player} Axis: {axis_name} ({event.code}) = {event.value}")
    except KeyboardInterrupt:
        print("\n\nExiting...")


def find_all_gamepads():
    """Find all gamepad devices."""
    devices = list_devices()
    gamepads = []

    for path in devices:
        try:
            dev = InputDevice(path)
            caps = dev.capabilities()
            name = dev.name.lower()

            has_abs = ecodes.EV_ABS in caps
            has_keys = ecodes.EV_KEY in caps

            if has_keys:
                keys = caps[ecodes.EV_KEY]
                has_gamepad_btns = any(k in keys for k in [
                    ecodes.BTN_A, ecodes.BTN_B, ecodes.BTN_X, ecodes.BTN_Y,
                    ecodes.BTN_GAMEPAD, ecodes.BTN_SOUTH, ecodes.BTN_EAST,
                ])
            else:
                has_gamepad_btns = False

            if has_abs:
                abs_caps = [c[0] if isinstance(c, tuple) else c for c in caps[ecodes.EV_ABS]]
                has_sticks = ecodes.ABS_X in abs_caps and ecodes.ABS_Y in abs_caps
            else:
                has_sticks = False

            # Only include devices with both gamepad buttons and analog sticks
            if has_gamepad_btns and has_sticks:
                gamepads.append(dev)

        except Exception:
            continue

    return gamepads


def main():
    parser = argparse.ArgumentParser(description="Bluetooth Gamepad Test for GameSir Nova Lite")
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all input devices')
    parser.add_argument('--device', '-d', type=int, default=None,
                        help='Use specific device number from --list')
    parser.add_argument('--info', '-i', action='store_true',
                        help='Show detailed device info and exit')
    parser.add_argument('--multi', '-m', action='store_true',
                        help='Monitor all gamepads simultaneously (for 2-player testing)')
    args = parser.parse_args()

    print("=" * 50)
    print("GameSir Nova Lite Bluetooth Gamepad Test")
    print("=" * 50)

    if args.list:
        list_all_devices()
        print("\nTo use a specific device: python3 test_gamepad.py --device N")
        print("To test both controllers: python3 test_gamepad.py --multi")
        return

    # Multi-controller mode
    if args.multi:
        gamepads = find_all_gamepads()
        if len(gamepads) < 2:
            print(f"\nFound {len(gamepads)} gamepad(s), need 2 for multi mode.")
            print("Use --list to see all devices.")
            if gamepads:
                print(f"Found: {gamepads[0].name}")
            sys.exit(1)
        monitor_multiple_gamepads(gamepads[:2])  # Use first 2
        return

    # Find or select device
    if args.device is not None:
        devices = list_devices()
        if args.device >= len(devices):
            print(f"Error: Device {args.device} not found. Use --list to see devices.")
            sys.exit(1)
        device = InputDevice(devices[args.device])
    else:
        print("\nSearching for gamepad...")
        device = find_gamepad()

        if device is None:
            print("\nNo gamepad found!")
            print("\nPairing instructions for GameSir Nova Lite:")
            print("1. Turn on controller and enter pairing mode")
            print("   (Usually hold Home + dedicated pairing button)")
            print("2. On Raspberry Pi, run: bluetoothctl")
            print("3. In bluetoothctl:")
            print("   > power on")
            print("   > agent on")
            print("   > scan on")
            print("   (Wait for 'GameSir' device to appear)")
            print("   > pair XX:XX:XX:XX:XX:XX")
            print("   > connect XX:XX:XX:XX:XX:XX")
            print("   > trust XX:XX:XX:XX:XX:XX")
            print("   > quit")
            print("4. Run this script again")
            print("\nUse --list to see all available input devices.")
            sys.exit(1)

    print(f"\nFound gamepad: {device.name}")

    if args.info:
        print(f"Path: {device.path}")
        print(f"\nCapabilities:")
        caps = device.capabilities(verbose=True)
        for ev_type, codes in caps.items():
            print(f"\n  {ev_type}:")
            for code in codes[:20]:  # Limit output
                if isinstance(code, tuple):
                    print(f"    {code[0]}: {code[1]}")
                else:
                    print(f"    {code}")
            if len(codes) > 20:
                print(f"    ... and {len(codes) - 20} more")
        return

    monitor_gamepad(device)


if __name__ == "__main__":
    main()
