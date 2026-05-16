import os
import stat
from pathlib import Path

# Fixed seed for determinism
import random
random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Full skill directory structure ──────────────────────────────────────────
skill_root = WORKSPACE / "skills" / "control-ikea-lightbulb"
scripts_dir = skill_root / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# ── pyproject.toml ─────────────────────────────────────────────────────────────
(skill_root / "pyproject.toml").write_text("""\
[project]
name = "control-ikea-lightbulb"
version = "0.1.0"
requires-python = ">=3.11, <4.0"
dependencies = [
    "python-kasa>=0.10.2",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""")

# ── control_kasa_light.py ──────────────────────────────────────────────────────
(scripts_dir / "control_kasa_light.py").write_text("""\
#!/usr/bin/env python3
\"\"\"Control a TP-Link Kasa smart bulb by IP address.\"\"\"

import argparse
import asyncio
import sys
import json
import os

def parse_args():
    p = argparse.ArgumentParser(description="Control a Kasa smart bulb.")
    p.add_argument("--ip", required=True, help="Bulb IP address")
    p.add_argument("--on", action="store_true", help="Turn bulb on")
    p.add_argument("--off", action="store_true", help="Turn bulb off")
    p.add_argument("--brightness", type=int, help="Brightness 0-100")
    p.add_argument("--hsv", nargs=3, type=int, metavar=("H", "S", "V"),
                   help="Set color as HSV (hue 0-360, saturation 0-100, value 0-100)")
    return p.parse_args()


async def main():
    args = parse_args()

    # Log the call for testing/mock purposes
    log_entry = {
        "ip": args.ip,
        "on": args.on,
        "off": args.off,
        "brightness": args.brightness,
        "hsv": args.hsv,
    }
    log_path = os.environ.get("KASA_LOG", "/tmp/kasa_calls.jsonl")
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\\n")

    try:
        from kasa import SmartBulb
        bulb = SmartBulb(args.ip)
        await bulb.update()

        if args.on:
            await bulb.turn_on()
        if args.off:
            await bulb.turn_off()
        if args.brightness is not None:
            await bulb.set_brightness(args.brightness)
        if args.hsv:
            h, s, v = args.hsv
            await bulb.set_hsv(h, s, v)

        await bulb.update()
        print(f"Bulb state: on={bulb.is_on}, brightness={bulb.brightness}")
    except Exception as e:
        print(f"[mock/error] {e} — call logged to {log_path}", file=sys.stderr)
        sys.exit(0)  # exit 0 so scripts can be tested without real device

asyncio.run(main())
""")

# ── light_show.py ──────────────────────────────────────────────────────────────
(scripts_dir / "light_show.py").write_text("""\
#!/usr/bin/env python3
\"\"\"
Light-show controller for Kasa smart bulbs.
Runs a predefined color sequence with configurable timing.

Default white uses a high color temperature (9000K); override with --white-temp.
--off-flash: adds a brief off-flash between color steps; ignores transitions
             to white (saturation==0) to avoid white<->blue ping-pong; only
             applies white-temp to white steps (fixes red being skipped).
             White steps also set brightness even without --double-write.
\"\"\"

import argparse
import asyncio
import sys
import json
import os


COLOR_SEQUENCE = [
    # (hue, saturation, value, label)
    (0,   100, 80, "red"),
    (240, 100, 80, "blue"),
    (120, 100, 80, "green"),
    (0,   0,   90, "white"),   # saturation==0 → white
    (300, 100, 80, "purple"),
]


def parse_args():
    p = argparse.ArgumentParser(description="Run a light show on a Kasa bulb.")
    p.add_argument("--ip", required=True, help="Bulb IP address")
    p.add_argument("--duration", type=float, default=6.0,
                   help="Duration (seconds) per color step")
    p.add_argument("--transition", type=float, default=1.0,
                   help="Transition time (seconds) between steps")
    p.add_argument("--off-flash", action="store_true",
                   help="Brief off flash between color steps (skips white transitions)")
    p.add_argument("--white-temp", type=int, default=9000,
                   help="Color temperature for white steps in Kelvin (default: 9000)")
    p.add_argument("--double-write", action="store_true",
                   help="Write each state twice for reliability")
    p.add_argument("--verbose", action="store_true",
                   help="Print each step as it executes")
    return p.parse_args()


async def apply_step(bulb, h, s, v, label, args):
    is_white = (s == 0)
    if args.verbose:
        print(f"  → {label} (hsv={h},{s},{v}{'  [white-temp=' + str(args.white_temp) + 'K]' if is_white else ''})")

    try:
        if is_white:
            # White step: apply color temp and brightness
            await bulb.set_color_temp(args.white_temp)
            await bulb.set_brightness(v)
        else:
            await bulb.set_hsv(h, s, v)
        if args.double_write:
            if is_white:
                await bulb.set_color_temp(args.white_temp)
                await bulb.set_brightness(v)
            else:
                await bulb.set_hsv(h, s, v)
    except Exception as e:
        if args.verbose:
            print(f"    [mock/error] {e}", file=sys.stderr)


async def main():
    args = parse_args()

    log_entry = {
        "ip": args.ip,
        "duration": args.duration,
        "transition": args.transition,
        "off_flash": args.off_flash,
        "white_temp": args.white_temp,
        "double_write": args.double_write,
        "verbose": args.verbose,
    }
    log_path = os.environ.get("KASA_LOG", "/tmp/kasa_calls.jsonl")
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\\n")

    if args.verbose:
        print(f"Light show on {args.ip}: {len(COLOR_SEQUENCE)} steps, "
              f"duration={args.duration}s, transition={args.transition}s, "
              f"off-flash={args.off_flash}, white-temp={args.white_temp}K")

    try:
        from kasa import SmartBulb
        bulb = SmartBulb(args.ip)
        await bulb.update()
        await bulb.turn_on()

        for h, s, v, label in COLOR_SEQUENCE:
            is_white = (s == 0)
            if args.off_flash and not is_white:
                # off-flash: skip for white steps to avoid ping-pong
                await bulb.turn_off()
                await asyncio.sleep(0.15)
                await bulb.turn_on()

            await apply_step(bulb, h, s, v, label, args)
            await asyncio.sleep(args.duration)

            if args.transition > 0:
                await asyncio.sleep(args.transition)

        if args.verbose:
            print("Light show complete.")

    except Exception as e:
        if args.verbose:
            print(f"[mock/error] {e} — sequence logged.", file=sys.stderr)
        sys.exit(0)

asyncio.run(main())
""")

# ── run_control_kasa.sh ────────────────────────────────────────────────────────
run_control = scripts_dir / "run_control_kasa.sh"
run_control.write_text("""\
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
exec uv run --project "$SKILL_ROOT" python "$SCRIPT_DIR/control_kasa_light.py" "$@"
""")
run_control.chmod(run_control.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── run_test_light_show.sh ─────────────────────────────────────────────────────
run_lightshow = scripts_dir / "run_test_light_show.sh"
run_lightshow.write_text("""\
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
exec uv run --project "$SKILL_ROOT" python "$SCRIPT_DIR/light_show.py" "$@"
""")
run_lightshow.chmod(run_lightshow.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── 2. Distractor files ────────────────────────────────────────────────────────
# Simulate a realistic project with many unrelated files

(WORKSPACE / "README.md").write_text("# Smart Office Automation Platform\n\nThis repo manages building systems.\n")

infra_dir = WORKSPACE / "infrastructure" / "networking"
infra_dir.mkdir(parents=True, exist_ok=True)
(infra_dir / "vlan_config.yaml").write_text("""\
vlans:
  - id: 10
    name: office_iot
    subnet: 192.168.1.0/24
  - id: 20
    name: av_systems
    subnet: 192.168.2.0/24
""")
(infra_dir / "dhcp_leases.txt").write_text("""\
# DHCP Leases - Meeting Room B
192.168.1.42    b4:e6:2d:aa:11:22    smart-bulb-meetingB
192.168.1.43    b4:e6:2d:aa:11:23    smart-bulb-meetingC
192.168.1.10    dc:a6:32:12:34:56    rpi-controller
""")

meeting_dir = WORKSPACE / "rooms" / "meeting_room_b"
meeting_dir.mkdir(parents=True, exist_ok=True)
(meeting_dir / "ambiance_requirements.txt").write_text("""\
Meeting Room B - Lighting Ambiance Demo Requirements
=====================================================
Contact: facilities@company.com
Bulb IP: 192.168.1.42

Demo sequence requirements:
- Run the full color cycling light show
  * Each color step: 8 seconds
  * Transition between steps: 2 seconds
  * Enable the brief off-flash effect between color changes
  * Override default white color temperature to 6500K (warmer)
  * Enable verbose logging of each step
- After the show completes, set the room to "Focus Blue" mode:
  * Hue: 200, Saturation: 80, Value: 70
  * Brightness: 70
  * Bulb must be ON

Deliverable: a shell script named lighting_demo.sh placed anywhere in the workspace.
The script should be executable and runnable from the workspace root.
""")

(meeting_dir / "room_schedule.csv").write_text("""\
date,time,event,room
2024-03-15,09:00,Board Presentation,B
2024-03-15,14:00,Product Demo,B
2024-03-16,10:00,Workshop,B
""")

devices_dir = WORKSPACE / "devices" / "bulbs"
devices_dir.mkdir(parents=True, exist_ok=True)
(devices_dir / "inventory.json").write_text("""\
{
  "bulbs": [
    {"id": "bulb-001", "ip": "192.168.1.42", "room": "meeting_b", "model": "KL130", "protocol": "kasa"},
    {"id": "bulb-002", "ip": "192.168.1.43", "room": "meeting_c", "model": "KL130", "protocol": "kasa"},
    {"id": "bulb-003", "ip": "192.168.2.10", "room": "lobby",     "model": "TRADFRI", "protocol": "ikea"}
  ]
}
""")

(devices_dir / "calibration_notes.txt").write_text("""\
Calibration Notes - 2024-02-01
Bulb 192.168.1.42: verified HSV range 0-360 hue, 0-100 sat/val
Bulb 192.168.1.43: same calibration
White balance: default 9000K feels too cool for meeting rooms; 6500K preferred.
""")

config_dir = WORKSPACE / "config"
config_dir.mkdir(parents=True, exist_ok=True)
(config_dir / "automation_rules.yaml").write_text("""\
rules:
  - name: morning_warmup
    trigger: "07:30"
    action: turn_on
    brightness: 50
  - name: meeting_mode
    trigger: manual
    action: light_show
    params:
      duration: 8
      transition: 2
""")
(config_dir / "network_map.txt").write_text("See infrastructure/networking/ for details.\n")

logs_dir = WORKSPACE / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
(logs_dir / "automation.log").write_text("""\
2024-02-10 09:00:01 INFO  morning_warmup triggered
2024-02-10 09:00:02 INFO  bulb 192.168.1.42 set brightness=50
2024-02-10 14:00:00 INFO  meeting_mode triggered manually
""")
(logs_dir / "errors.log").write_text("2024-01-15 ERROR connection timeout 192.168.1.99\n")

tests_dir = WORKSPACE / "tests"
tests_dir.mkdir(parents=True, exist_ok=True)
(tests_dir / "test_placeholder.py").write_text("# placeholder\n")

(WORKSPACE / "Makefile").write_text("""\
.PHONY: help
help:
\t@echo "Available targets: help"
""")

(WORKSPACE / ".gitignore").write_text("__pycache__/\n.venv/\n*.pyc\n")

print("Workspace generated successfully.")
print(f"Skill root: {skill_root}")
print(f"Scripts: {list(scripts_dir.iterdir())}")