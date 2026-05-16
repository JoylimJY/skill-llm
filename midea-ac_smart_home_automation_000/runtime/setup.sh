#!/bin/bash
set -e

SKILL_DIR="$HOME/.openclaw/skills/midea_ac"
SCRIPTS_DIR="$SKILL_DIR/scripts"
STATE_FILE="$SKILL_DIR/state/ac_state.json"

mkdir -p "$SCRIPTS_DIR"
mkdir -p "$SKILL_DIR/state"

# Write the midea_ac.py mock script
cat > "$SCRIPTS_DIR/midea_ac.py" << 'PYEOF'
#!/usr/bin/env python3
"""
Mock Midea AC control script.
Simulates real device control by reading/writing state from a JSON file.
"""

import sys
import json
import argparse
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent / "state" / "ac_state.json"

VALID_MODES = ["cool", "heat", "auto", "dry", "fan_only"]
VALID_FAN_SPEEDS = ["low", "medium", "high", "max", "auto"]
TEMP_MIN = 16
TEMP_MAX = 30


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))


def print_status(room, ac):
    print(f"=== {room} AC Status ===")
    print(f"Power:       {ac.get('power', 'unknown')}")
    print(f"Mode:        {ac.get('mode', 'unknown')}")
    print(f"Temperature: {ac.get('temperature', 'unknown')}°C")
    print(f"Fan Speed:   {ac.get('fan_speed', 'unknown')}")
    print(f"Aux Mode:    {ac.get('aux_mode', 'unknown')}")


def main():
    parser = argparse.ArgumentParser(description="Midea AC Control")
    parser.add_argument("room", help="Room name")
    parser.add_argument("action", nargs="?", default=None,
                        choices=["on", "off", "toggle", "status"],
                        help="Action to perform")
    parser.add_argument("--mode", choices=VALID_MODES, help="Operation mode")
    parser.add_argument("--temperature", type=int, help="Target temperature")
    parser.add_argument("--fan_speed", choices=VALID_FAN_SPEEDS, help="Fan speed")
    parser.add_argument("--aux_mode", choices=["on", "off"], help="Aux heat mode")

    args = parser.parse_args()

    state = load_state()
    room = args.room

    if room not in state:
        print(f"Error: Room '{room}' not found in device registry.")
        sys.exit(1)

    ac = state[room]

    # Handle power actions
    if args.action == "status":
        print_status(room, ac)
        return

    if args.action == "on":
        ac["power"] = "on"
        print(f"{room} AC turned ON.")

    elif args.action == "off":
        ac["power"] = "off"
        print(f"{room} AC turned OFF.")

    elif args.action == "toggle":
        ac["power"] = "off" if ac.get("power") == "on" else "on"
        print(f"{room} AC toggled to {ac['power'].upper()}.")

    # Handle parameter changes
    if args.mode:
        if ac.get("power") != "on":
            print("Warning: AC is off. Setting mode anyway.")
        ac["mode"] = args.mode
        print(f"{room} AC mode set to {args.mode}.")

    if args.temperature is not None:
        if args.temperature < TEMP_MIN or args.temperature > TEMP_MAX:
            print(f"Error: Temperature must be between {TEMP_MIN} and {TEMP_MAX}.")
            sys.exit(1)
        ac["temperature"] = args.temperature
        print(f"{room} AC temperature set to {args.temperature}°C.")

    if args.fan_speed:
        ac["fan_speed"] = args.fan_speed
        print(f"{room} AC fan speed set to {args.fan_speed}.")

    if args.aux_mode:
        ac["aux_mode"] = args.aux_mode
        print(f"{room} AC aux mode set to {args.aux_mode}.")

    state[room] = ac
    save_state(state)
    print(f"State saved for {room}.")


if __name__ == "__main__":
    main()
PYEOF

chmod +x "$SCRIPTS_DIR/midea_ac.py"

echo "Mock midea_ac.py installed at $SCRIPTS_DIR/midea_ac.py"
echo "State file location: $STATE_FILE"
echo "Current state:"
cat "$STATE_FILE"