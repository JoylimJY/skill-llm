import os
import json
import random
import stat

random.seed(42)

# ── directory layout ─────────────────────────────────────────────────────────
base = "/workspace"

dirs = [
    "skills/apple-media/scripts",
    "skills/apple-media/logs",
    "skills/apple-media/config",
    "skills/airfoil",
    "skills/airfoil/logs",
    "venue/rooms",
    "venue/schedules",
    "venue/audio_profiles",
    "infra/networking",
    "infra/monitoring",
    "docs/runbooks",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "venue/rooms/dining_room.json": json.dumps({"room": "dining", "capacity": 40, "audio_zone": "A"}),
    "venue/rooms/bar.json": json.dumps({"room": "bar", "capacity": 20, "audio_zone": "B"}),
    "venue/schedules/evening.json": json.dumps({"start": "18:00", "end": "23:00", "volume_target": 35}),
    "venue/audio_profiles/ambient.json": json.dumps({"genre": "jazz", "bpm_max": 90, "volume": 35}),
    "venue/audio_profiles/happy_hour.json": json.dumps({"genre": "pop", "bpm_max": 120, "volume": 50}),
    "infra/networking/vlans.txt": "VLAN 10: management\nVLAN 20: AV devices\nVLAN 30: guest wifi\n",
    "infra/monitoring/alerts.log": "2024-01-10 18:00:01 INFO device heartbeat ok\n2024-01-10 18:05:00 WARN latency spike on AV VLAN\n",
    "docs/runbooks/audio_setup.md": "# Audio Setup\nSee IT for device credentials.\nContact vendor for HomePod provisioning.\n",
    "skills/apple-media/logs/last_scan.log": "scan run at 2024-01-09 17:55:02 — 3 devices found\n",
    "skills/apple-media/config/targets.txt": "10.0.0.28\n10.0.0.111\n10.0.0.55\n",
    "skills/airfoil/logs/connections.log": "2024-01-09 18:00:00 connected Bar Speaker\n2024-01-09 18:00:05 volume 40\n",
}
for rel, content in distractors.items():
    path = os.path.join(base, rel)
    with open(path, "w") as f:
        f.write(content)

# ── mock atvremote binary ─────────────────────────────────────────────────────
# Simulates `atvremote scan` and `atvremote -n "Apple TV 4K" playing`
atvremote_mock = r"""#!/usr/bin/env python3
import sys, textwrap

SCAN_OUTPUT = textwrap.dedent('''
       Name: Dining Room
       Model: HomePod mini
    Address: 10.0.0.28
        MAC: AA:BB:CC:DD:EE:01
 Identifier: aaaa-bbbb-cccc-0001
   Protocol: AirPlay (port: 7000)

       Name: Bar Speaker
       Model: HomePod
    Address: 10.0.0.111
        MAC: AA:BB:CC:DD:EE:02
 Identifier: aaaa-bbbb-cccc-0002
   Protocol: AirPlay (port: 7000)

       Name: Apple TV 4K
       Model: Apple TV 4K
    Address: 10.0.0.55
        MAC: AA:BB:CC:DD:EE:03
 Identifier: aaaa-bbbb-cccc-0003
   Protocol: MRP (port: 49152)
   Protocol: AirPlay (port: 7000)
''').strip()

PLAYING_OUTPUT = "Media type: Music\nPlay state: Playing\nTitle: Blue in Green\nArtist: Miles Davis\nAlbum: Kind of Blue\nPosition: 0:02:14 of 0:05:37\n"

args = sys.argv[1:]
if "scan" in args:
    print(SCAN_OUTPUT)
elif "-n" in args:
    idx = args.index("-n")
    name = args[idx+1] if idx+1 < len(args) else ""
    cmd = args[-1] if args else ""
    if cmd == "playing" and "Apple TV" in name:
        print(PLAYING_OUTPUT)
    elif cmd == "turn_on":
        print("Sending turn_on to", name)
    elif cmd == "play_pause":
        print("Sending play_pause to", name)
    else:
        print(f"Command '{cmd}' sent to {name}")
elif "--help" in args:
    print("atvremote - pyatv CLI tool")
else:
    print("atvremote: no command given")
"""

atvremote_path = "/usr/local/bin/atvremote"
with open(atvremote_path, "w") as f:
    f.write(atvremote_mock)
os.chmod(atvremote_path, 0o755)

# ── scan.sh ───────────────────────────────────────────────────────────────────
scan_sh = """#!/bin/bash
TIMEOUT=${1:-5}
atvremote scan
"""
with open(os.path.join(base, "skills/apple-media/scripts/scan.sh"), "w") as f:
    f.write(scan_sh)

# ── scan-hosts.sh ─────────────────────────────────────────────────────────────
scan_hosts_sh = """#!/bin/bash
HOSTS=${1:-""}
TIMEOUT=${2:-3}
atvremote scan
"""
with open(os.path.join(base, "skills/apple-media/scripts/scan-hosts.sh"), "w") as f:
    f.write(scan_hosts_sh)

# ── scan-json.js ─────────────────────────────────────────────────────────────
# This script parses atvremote scan output into JSON
scan_json_js = r"""#!/usr/bin/env node
const { execSync } = require('child_process');

const timeout = parseInt(process.argv[2] || '5', 10);

let raw;
try {
  raw = execSync(`atvremote scan`, { timeout: timeout * 1000 + 2000, encoding: 'utf8' });
} catch (e) {
  raw = e.stdout || '';
}

// Parse blocks separated by blank lines
const blocks = raw.trim().split(/\n{2,}/);
const devices = [];

for (const block of blocks) {
  if (!block.trim()) continue;
  const lines = block.trim().split('\n');
  const dev = { name: null, address: null, model: null, identifier: null, services: [] };
  for (const line of lines) {
    const m = line.match(/^\s*(\w[\w\s]*):\s*(.+)$/);
    if (!m) continue;
    const key = m[1].trim().toLowerCase();
    const val = m[2].trim();
    if (key === 'name') dev.name = val;
    else if (key === 'address') dev.address = val;
    else if (key === 'model') dev.model = val;
    else if (key === 'identifier') dev.identifier = val;
    else if (key === 'protocol') dev.services.push(val);
  }
  if (dev.name) devices.push(dev);
}

console.log(JSON.stringify(devices, null, 2));
"""
with open(os.path.join(base, "skills/apple-media/scripts/scan-json.js"), "w") as f:
    f.write(scan_json_js)

# ── connect.sh ────────────────────────────────────────────────────────────────
# Wraps airfoil connect for a named speaker
connect_sh = r"""#!/bin/bash
SPEAKER="${1}"
if [ -z "$SPEAKER" ]; then
  echo "Usage: connect.sh <speaker_name>"
  exit 1
fi
../airfoil/airfoil.sh connect "$SPEAKER"
"""
with open(os.path.join(base, "skills/apple-media/scripts/connect.sh"), "w") as f:
    f.write(connect_sh)

# ── volume.sh ─────────────────────────────────────────────────────────────────
# Wraps airfoil volume for a named speaker
volume_sh = r"""#!/bin/bash
SPEAKER="${1}"
VOL="${2}"
if [ -z "$SPEAKER" ] || [ -z "$VOL" ]; then
  echo "Usage: volume.sh <speaker_name> <volume_0-100>"
  exit 1
fi
../airfoil/airfoil.sh volume "$SPEAKER" "$VOL"
"""
with open(os.path.join(base, "skills/apple-media/scripts/volume.sh"), "w") as f:
    f.write(volume_sh)

# ── mock airfoil.sh ───────────────────────────────────────────────────────────
airfoil_sh = r"""#!/bin/bash
CMD="${1}"
SPEAKER="${2}"
VOL="${3}"

LOGFILE="$(dirname "$0")/logs/connections.log"

timestamp() { date '+%Y-%m-%d %H:%M:%S'; }

case "$CMD" in
  list)
    echo "Dining Room"
    echo "Bar Speaker"
    echo "Computer"
    ;;
  connect)
    echo "Connected to: $SPEAKER"
    echo "$(timestamp) connected $SPEAKER" >> "$LOGFILE"
    ;;
  disconnect)
    echo "Disconnected: $SPEAKER"
    echo "$(timestamp) disconnected $SPEAKER" >> "$LOGFILE"
    ;;
  volume)
    echo "Set volume for $SPEAKER to $VOL"
    echo "$(timestamp) volume $SPEAKER $VOL" >> "$LOGFILE"
    ;;
  *)
    echo "airfoil.sh: unknown command $CMD"
    exit 1
    ;;
esac
"""
with open(os.path.join(base, "skills/airfoil/airfoil.sh"), "w") as f:
    f.write(airfoil_sh)

print("Workspace generated successfully.")
print("Structure:")
for root, dirs_list, files in os.walk(base):
    level = root.replace(base, "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    sub = " " * 2 * (level + 1)
    for fname in files:
        print(f"{sub}{fname}")