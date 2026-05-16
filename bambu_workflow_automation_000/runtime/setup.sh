#!/bin/bash
set -e

# ---- Mock the `bambu` CLI ----
# We install a fake `bambu` binary that:
#   1. Records all commands to ~/.bambu/command_log.jsonl
#   2. Responds realistically to each subcommand
#   3. On `setup`, writes a real config.json to ~/.bambu/config.json
#   4. On `ping`, checks the config for the correct IP before responding
#   5. Returns realistic JSON for --json flags

cat > /usr/local/bin/bambu << 'BAMBU_SCRIPT'
#!/usr/bin/env python3
import sys
import json
import os
import datetime
from pathlib import Path

args = sys.argv[1:]
config_dir = Path.home() / ".bambu"
config_dir.mkdir(exist_ok=True)
config_path = config_dir / "config.json"
log_path = config_dir / "command_log.jsonl"

def log_command(args, output=None):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "args": args,
        "output_snippet": str(output)[:300] if output else None
    }
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

def load_config():
    if config_path.exists():
        return json.loads(config_path.read_text())
    return None

def require_config():
    cfg = load_config()
    if not cfg or "ip" not in cfg:
        print("❌ No printer configured. Run: bambu setup <ip> <serial> <access_code>", file=sys.stderr)
        sys.exit(1)
    return cfg

CORRECT_IP = "192.168.10.47"
CORRECT_SERIAL = "01S09C382900001"
CORRECT_CODE = "12345678"

if not args:
    print("Usage: bambu <command> [args]")
    sys.exit(0)

cmd = args[0]

# ---- setup ----
if cmd == "setup":
    if len(args) < 4:
        print("Usage: bambu setup <ip> <serial> <access_code>", file=sys.stderr)
        sys.exit(1)
    ip, serial, code = args[1], args[2], args[3]
    cfg = {"ip": ip, "serial": serial, "access_code": code}
    config_path.write_text(json.dumps(cfg, indent=2))
    log_command(args, f"Setup saved: ip={ip} serial={serial}")
    print(f"✅ Printer configured: {ip} ({serial})")
    sys.exit(0)

# ---- ping ----
elif cmd == "ping":
    cfg = require_config()
    if cfg.get("ip") == CORRECT_IP and cfg.get("serial") == CORRECT_SERIAL and cfg.get("access_code") == CORRECT_CODE:
        output = "🟢 Printer online. RTT: 4ms. MQTT: connected. FTP: ready."
    else:
        output = "❌ Connection failed: Auth rejected. Check credentials."
        log_command(args, output)
        print(output)
        sys.exit(1)
    log_command(args, output)
    print(output)
    sys.exit(0)

# ---- status ----
elif cmd == "status":
    cfg = require_config()
    json_flag = "--json" in args
    status_data = {
        "gcode_state": "IDLE",
        "mc_percent": 0,
        "mc_remaining_time": 0,
        "nozzle_temper": 23.4,
        "bed_temper": 22.1,
        "chamber_temper": 21.0,
        "wifi_signal": -48,
        "print_type": "idle",
        "layer_num": 0,
        "total_layer_num": 0,
        "serial": cfg.get("serial", ""),
        "ip": cfg.get("ip", "")
    }
    if json_flag:
        out = json.dumps(status_data, indent=2)
    else:
        out = "🖨️  Status: IDLE\n🌡️  Nozzle: 23.4°C | Bed: 22.1°C\n📶 WiFi: -48dBm\n⏱️  No active print"
    log_command(args, out[:100])
    print(out)
    sys.exit(0)

# ---- temp ----
elif cmd == "temp":
    cfg = require_config()
    out = "🌡️  Nozzle: 23.4°C (target: --)\n🛏️  Bed:    22.1°C (target: --)\n🏠 Chamber: 21.0°C"
    log_command(args, out)
    print(out)

# ---- ams ----
elif cmd == "ams":
    cfg = require_config()
    json_flag = "--json" in args
    ams_data = {
        "ams": [
            {
                "id": 0,
                "humidity": 3,
                "temp": 28.5,
                "trays": [
                    {"id": 0, "type": "PLA Basic", "color": "FFFFFFFF", "brand": "Bambu", "name": "PLA Basic White", "remain": 85},
                    {"id": 1, "type": "PLA Basic", "color": "1F1F1FFF", "brand": "Bambu", "name": "PLA Basic Black", "remain": 92},
                    {"id": 2, "type": "PLA Matte", "color": "808080FF", "brand": "Bambu", "name": "PLA Matte Grey", "remain": 78},
                    {"id": 3, "type": "EMPTY", "color": "00000000", "brand": "", "name": "Empty", "remain": 0}
                ]
            }
        ],
        "current_tray": 0,
        "current_type": "PLA Basic",
        "current_color": "FFFFFFFF"
    }
    if json_flag:
        out = json.dumps(ams_data, indent=2)
    else:
        out = "🧵 AMS Status:\n  Slot 0: PLA Basic White (85% remain) ← ACTIVE\n  Slot 1: PLA Basic Black (92% remain)\n  Slot 2: PLA Matte Grey (78% remain)\n  Slot 3: [EMPTY]"
    log_command(args, out[:200])
    print(out)
    sys.exit(0)

# ---- errors ----
elif cmd == "errors":
    cfg = require_config()
    out = '{"errors": []}' if "--json" in args else "✅ No active errors"
    log_command(args, out)
    print(out)

# ---- heat ----
elif cmd == "heat":
    cfg = require_config()
    targets = {}
    for a in args[1:]:
        if ":" in a:
            k, v = a.split(":", 1)
            targets[k.strip()] = v.strip()
    if not targets:
        print("Usage: bambu heat nozzle:<temp> bed:<temp>", file=sys.stderr)
        sys.exit(1)
    parts = []
    for k, v in targets.items():
        parts.append(f"{k}→{v}°C")
    out = f"🔥 Heating: {', '.join(parts)}"
    log_command(args, out)
    print(out)
    sys.exit(0)

# ---- cooldown ----
elif cmd == "cooldown":
    cfg = require_config()
    out = "❄️  Cooling down... Nozzle and bed targets set to 0°C"
    log_command(args, out)
    print(out)

# ---- fan ----
elif cmd == "fan":
    cfg = require_config()
    if len(args) < 3:
        print("Usage: bambu fan <part|aux|chamber> <0-100>", file=sys.stderr)
        sys.exit(1)
    fan_name, speed = args[1], args[2]
    out = f"💨 Fan '{fan_name}' set to {speed}%"
    log_command(args, out)
    print(out)

# ---- light ----
elif cmd == "light":
    cfg = require_config()
    state = args[1] if len(args) > 1 else "on"
    out = f"💡 Light: {state.upper()}"
    log_command(args, out)
    print(out)

# ---- home ----
elif cmd == "home":
    cfg = require_config()
    out = "🏠 Homing all axes..."
    log_command(args, out)
    print(out)

# ---- move ----
elif cmd == "move":
    cfg = require_config()
    out = f"📍 Move: {' '.join(args[1:])}"
    log_command(args, out)
    print(out)

# ---- gcode ----
elif cmd == "gcode":
    cfg = require_config()
    out = f"⚙️  G-code sent: {' '.join(args[1:])}"
    log_command(args, out)
    print(out)

# ---- print ----
elif cmd == "print":
    cfg = require_config()
    if len(args) < 2:
        print("Usage: bambu print <filename.3mf>", file=sys.stderr)
        sys.exit(1)
    fname = args[1]
    out = f"▶️  Starting print: {fname}"
    log_command(args, out)
    print(out)

# ---- pause / resume / stop ----
elif cmd in ("pause", "resume", "stop"):
    cfg = require_config()
    out = f"⏯️  Print {cmd}ed."
    log_command(args, out)
    print(out)

# ---- watch ----
elif cmd == "watch":
    cfg = require_config()
    out = "👁️  Monitoring print... (mock: no active print, exiting)"
    log_command(args, out)
    print(out)

# ---- job ----
elif cmd == "job":
    cfg = require_config()
    if len(args) < 2:
        print("Usage: bambu job <upload-and-print> <file>", file=sys.stderr)
        sys.exit(1)
    subcmd = args[1]
    if subcmd == "upload-and-print":
        if len(args) < 3:
            print("Usage: bambu job upload-and-print <file>", file=sys.stderr)
            sys.exit(1)
        fpath = args[2]
        fname = os.path.basename(fpath)
        # Check file exists
        if not os.path.exists(fpath):
            print(f"❌ File not found: {fpath}", file=sys.stderr)
            sys.exit(1)
        out = f"📤 Uploading {fname}... done\n▶️  Print started: {fname}\n📊 Job ID: JOB-{hash(fname) % 100000:05d}"
        log_command(args, out)
        print(out)
        sys.exit(0)
    else:
        print(f"Unknown job subcommand: {subcmd}", file=sys.stderr)
        sys.exit(1)

# ---- load ----
elif cmd == "load":
    cfg = require_config()
    if len(args) < 2:
        print("Usage: bambu load <tray_id>", file=sys.stderr)
        sys.exit(1)
    tray = args[1]
    out = f"🧵 Loading filament from tray {tray}..."
    log_command(args, out)
    print(out)

# ---- unload ----
elif cmd == "unload":
    cfg = require_config()
    out = "🧵 Unloading current filament..."
    log_command(args, out)
    print(out)

# ---- files ----
elif cmd == "files":
    cfg = require_config()
    out = "📂 SD Card Files:\n  enclosure_bracket_v4.3mf\n  test_cube.3mf"
    log_command(args, out)
    print(out)

# ---- upload ----
elif cmd == "upload":
    cfg = require_config()
    if len(args) < 2:
        print("Usage: bambu upload <file>", file=sys.stderr)
        sys.exit(1)
    fpath = args[1]
    if not os.path.exists(fpath):
        print(f"❌ File not found: {fpath}", file=sys.stderr)
        sys.exit(1)
    fname = os.path.basename(fpath)
    out = f"📤 Uploaded {fname} to SD card."
    log_command(args, out)
    print(out)

# ---- delete ----
elif cmd == "delete":
    cfg = require_config()
    out = f"🗑️  Deleted: {args[1] if len(args)>1 else '?'}"
    log_command(args, out)
    print(out)

# ---- calibrate ----
elif cmd == "calibrate":
    cfg = require_config()
    target = args[1] if len(args) > 1 else "all"
    out = f"📐 Calibrating: {target}... done"
    log_command(args, out)
    print(out)

# ---- version ----
elif cmd == "version":
    out = "bambu CLI v1.4.2 (mock)"
    log_command(args, out)
    print(out)

else:
    print(f"Unknown command: {cmd}", file=sys.stderr)
    sys.exit(1)

BAMBU_SCRIPT

chmod +x /usr/local/bin/bambu

# Ensure ~/.bambu exists
mkdir -p ~/.bambu

echo "Mock bambu CLI installed at /usr/local/bin/bambu"
bambu version