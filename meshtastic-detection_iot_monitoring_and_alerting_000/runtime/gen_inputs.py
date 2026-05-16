#!/usr/bin/env python3
"""
Generate a realistic meshtastic detection skill workspace with:
- Proper directory structure mimicking {baseDir}
- Mixed sensor_data.jsonl with both valid DETECTION_SENSOR_APP and noise entries
- A monitor_state.json with a partial byte offset (some records already "seen")
- Various distractor files throughout the workspace
"""

import json
import os
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "data",
    "data/archives",
    "references",
    "logs",
    "logs/archive",
    "config_backups",
    "docs",
    "tests",
    "tests/fixtures",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "docs/network_topology.md": "# Network Topology\n\nLoRa network spans 12km radius.\nBase frequency: 915 MHz\n",
    "docs/sensor_placement.md": "# Sensor Placement\n\nSector A: !1dd29c50\nSector B: !2ae3b661\nSector C: !3bf4c772\n",
    "config_backups/config_2025_01.json": json.dumps({"port": "/dev/cu.usbmodem1CDBD4A896441", "channel": "feishu"}),
    "config_backups/config_2025_02.json": json.dumps({"port": "/dev/cu.usbmodem1CDBD4A896442", "channel": "feishu"}),
    "references/frequency_bands.txt": "US915: 902-928 MHz\nEU868: 863-870 MHz\nAS923: 920-925 MHz\n",
    "logs/archive/receiver_2025_01.log": "2025-01-15 08:00:01 INFO Connected to /dev/cu.usbmodem1\n2025-01-15 08:00:02 INFO Listening...\n",
    "logs/archive/receiver_2025_02.log": "2025-02-20 09:12:34 INFO Connected\n2025-02-20 09:12:35 WARN Packet loss 2%\n",
    "logs/receiver_current.log": "2025-07-10 00:00:01 INFO USB receiver started\n",
    "tests/fixtures/sample_packet.json": json.dumps({
        "from": "!1dd29c50", "to": "^all", "decoded": {"portnum": "DETECTION_SENSOR_APP",
        "payload": "alert detected"}}),
    "tests/test_parser.py": "# Unit test placeholder\nimport unittest\nclass TestParser(unittest.TestCase): pass\n",
    "tmp/scratch.txt": "temporary notes\ndo not use\n",
    "CONFIG.md": "# Configuration\n\n- **Serial port**: `/dev/cu.usbmodem1CDBD4A896441`\n- **Notification channel**: `feishu`\n",
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content)

# ── Scripts (stubs that the skill says "already exist") ─────────────────────
# event_monitor.py - reads sensor_data.jsonl from monitor_state offset, outputs JSON
event_monitor_script = r'''#!/usr/bin/env python3
"""event_monitor.py — incremental alert monitor for DETECTION_SENSOR_APP events."""
import json, os, sys, hashlib
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "sensor_data.jsonl"
STATE_FILE = BASE_DIR / "data" / "monitor_state.json"

def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"offset": 0, "seen_hashes": []}

def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2))

def record_hash(line):
    return hashlib.sha256(line.strip().encode()).hexdigest()[:16]

def main():
    state = load_state()
    offset = state.get("offset", 0)
    seen = set(state.get("seen_hashes", []))

    alerts = []
    new_records = 0
    new_hashes = []

    if not DATA_FILE.exists():
        result = {"alerts": [], "summary": "暂无新告警。", "alert_count": 0, "new_records": 0}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    file_size = DATA_FILE.stat().st_size
    # Auto-reset if file was rotated (offset beyond file size)
    if offset > file_size:
        offset = 0
        seen = set()

    with open(DATA_FILE, "r") as f:
        f.seek(offset)
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            h = record_hash(line)
            if h in seen:
                continue
            new_records += 1
            new_hashes.append(h)
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("portnum") == "DETECTION_SENSOR_APP":
                alerts.append({
                    "priority": "high",
                    "sender": rec.get("sender", "unknown"),
                    "text": rec.get("data", {}).get("text", "alert detected"),
                    "received_at": rec.get("received_at", ""),
                    "channel": rec.get("channel", "ch0"),
                    "portnum": rec.get("portnum", ""),
                })
        new_offset = f.tell()

    # Save updated state
    updated_seen = list(seen) + new_hashes
    save_state({"offset": new_offset, "seen_hashes": updated_seen})

    alert_count = len(alerts)
    if alert_count > 0:
        latest = alerts[-1]
        summary = f"🚨 {alert_count} new detection alert(s) from {new_records} record(s)"
    else:
        summary = "暂无新告警。"

    result = {
        "alerts": alerts,
        "summary": summary,
        "alert_count": alert_count,
        "new_records": new_records,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
'''

# sensor_cli.py - query CLI for historical data
sensor_cli_script = r'''#!/usr/bin/env python3
"""sensor_cli.py — query CLI for meshtastic detection data."""
import json, sys, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

BASE_DIR = Path(__file__).parent.parent
DATA_FILE = BASE_DIR / "data" / "sensor_data.jsonl"

def parse_since(since_str):
    """Parse relative time like '1h', '24h', '7d' into a datetime cutoff."""
    m = re.match(r'^(\d+)([hHdDmM])$', since_str)
    if not m:
        raise ValueError(f"Unrecognized --since format: {since_str!r}. Use e.g. '1h', '24h', '7d'.")
    amount = int(m.group(1))
    unit = m.group(2).lower()
    now = datetime.now(timezone.utc)
    if unit == 'h':
        return now - timedelta(hours=amount)
    elif unit == 'd':
        return now - timedelta(days=amount)
    elif unit == 'm':
        return now - timedelta(minutes=amount)

def load_records(since_dt=None):
    records = []
    if not DATA_FILE.exists():
        return records
    with open(DATA_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("portnum") != "DETECTION_SENSOR_APP":
                continue
            if since_dt:
                ts_str = rec.get("received_at", "")
                try:
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts < since_dt:
                        continue
                except Exception:
                    continue
            records.append(rec)
    return records

def cmd_latest():
    records = load_records()
    if not records:
        print(json.dumps({"error": "No records found"}))
        return
    latest = records[-1]
    print(json.dumps(latest, indent=2))

def cmd_stats(since_str):
    since_dt = parse_since(since_str) if since_str else None
    records = load_records(since_dt)
    senders = {}
    for r in records:
        s = r.get("sender", "unknown")
        senders[s] = senders.get(s, 0) + 1
    result = {
        "total_detections": len(records),
        "unique_senders": len(senders),
        "sender_breakdown": senders,
        "since": since_str or "all-time",
    }
    print(json.dumps(result, indent=2))

def cmd_query(since_str):
    since_dt = parse_since(since_str) if since_str else None
    records = load_records(since_dt)
    print(json.dumps(records, indent=2))

def cmd_status():
    exists = DATA_FILE.exists()
    size = DATA_FILE.stat().st_size if exists else 0
    count = len(load_records()) if exists else 0
    print(json.dumps({"data_file_exists": exists, "file_size_bytes": size, "total_records": count}))

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: sensor_cli.py <latest|stats|query|status> [--since <period>]")
        sys.exit(1)
    cmd = args[0]
    since = None
    if "--since" in args:
        idx = args.index("--since")
        since = args[idx + 1]

    if cmd == "latest":
        cmd_latest()
    elif cmd == "stats":
        cmd_stats(since)
    elif cmd == "query":
        cmd_query(since)
    elif cmd == "status":
        cmd_status()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

# usb_receiver.py - stub (not needed to run for this task)
usb_receiver_script = r'''#!/usr/bin/env python3
"""usb_receiver.py — USB serial daemon stub (requires hardware)."""
import sys
print("ERROR: USB hardware required. Use --port to specify device.")
sys.exit(1)
'''

(WORKSPACE / "scripts" / "event_monitor.py").write_text(event_monitor_script)
(WORKSPACE / "scripts" / "sensor_cli.py").write_text(sensor_cli_script)
(WORKSPACE / "scripts" / "usb_receiver.py").write_text(usb_receiver_script)

# ── Generate sensor_data.jsonl ────────────────────────────────────────────────
# Strategy:
# - 40 records total spread across past 48 hours
# - 28 are DETECTION_SENSOR_APP (valid)
# - 12 are noise (TEXT_MESSAGE_APP, TELEMETRY_APP, POSITION_APP)
# - Records are roughly in chronological order
# - We will set monitor_state.json so that the first 20 LINES (not records) are "already seen"
#   meaning the offset is set to the byte position AFTER the 20th line.
# - Of those first 20 lines: 14 are DETECTION_SENSOR_APP, 6 are noise
# - The remaining 20 lines: 14 are DETECTION_SENSOR_APP, 6 are noise
#   -> so event_monitor should find 14 NEW detection alerts

now = datetime.now(timezone.utc)

senders = ["!1dd29c50", "!2ae3b661", "!3bf4c772", "!4cd5d883"]
channels = ["ch0", "ch1"]
noise_portnums = ["TEXT_MESSAGE_APP", "TELEMETRY_APP", "POSITION_APP"]

records = []

# Build 40 records: first 20 in 25-48h ago range, last 20 in 0-24h range
for i in range(40):
    # Time: earlier records are older
    if i < 20:
        hours_ago = random.uniform(25, 48)
    else:
        hours_ago = random.uniform(0.5, 24)
    ts = now - timedelta(hours=hours_ago)
    ts_str = ts.isoformat()

    # Decide portnum: positions 0,1,4,5,6,7,8,10,11,13,14,15,16,17,18,19 → DETECTION (14 of first 20)
    # positions 2,3,9,12,19 → noise  (6 of first 20, but let's be precise)
    # For second batch of 20: similar ratio 14 detection / 6 noise

    # Use deterministic pattern based on index
    noise_indices_first = {2, 3, 9, 12, 16, 19}
    noise_indices_second = {22, 25, 31, 35, 37, 39}

    if i in noise_indices_first or i in noise_indices_second:
        portnum = random.choice(noise_portnums)
        if portnum == "TEXT_MESSAGE_APP":
            data = {"type": "text", "text": "hello from node"}
        elif portnum == "TELEMETRY_APP":
            data = {"type": "telemetry", "battery": random.randint(60, 100), "voltage": round(random.uniform(3.7, 4.2), 2)}
        else:
            data = {"type": "position", "lat": round(random.uniform(-30, 30), 6), "lon": round(random.uniform(-120, 120), 6)}
    else:
        portnum = "DETECTION_SENSOR_APP"
        data = {"type": "detection", "text": "alert detected"}

    sender = random.choice(senders)
    channel = random.choice(channels)

    rec = {
        "received_at": ts_str,
        "sender": sender,
        "channel": channel,
        "portnum": portnum,
        "data": data,
    }
    records.append(rec)

# Sort by received_at ascending
records.sort(key=lambda r: r["received_at"])

# Write records to file, track byte offset after first 20 lines
jsonl_path = WORKSPACE / "data" / "sensor_data.jsonl"
lines = []
for rec in records:
    lines.append(json.dumps(rec))

with open(jsonl_path, "w") as f:
    for i, line in enumerate(lines):
        f.write(line + "\n")

# Compute byte offset after first 20 lines
offset_after_20 = 0
for i in range(20):
    offset_after_20 += len(lines[i].encode()) + 1  # +1 for newline

# Compute hashes of first 20 lines to mark as "seen"
import hashlib
seen_hashes = []
for i in range(20):
    h = hashlib.sha256(lines[i].strip().encode()).hexdigest()[:16]
    seen_hashes.append(h)

# ── Write monitor_state.json ─────────────────────────────────────────────────
# Simulate: monitor has already processed first 20 records
monitor_state = {
    "offset": offset_after_20,
    "seen_hashes": seen_hashes
}
(WORKSPACE / "data" / "monitor_state.json").write_text(
    json.dumps(monitor_state, indent=2)
)

# ── Write latest.json ─────────────────────────────────────────────────────────
detection_records = [r for r in records if r["portnum"] == "DETECTION_SENSOR_APP"]
if detection_records:
    (WORKSPACE / "data" / "latest.json").write_text(
        json.dumps(detection_records[-1], indent=2)
    )

# ── Save ground truth for eval ────────────────────────────────────────────────
# Count DETECTION_SENSOR_APP records in last 24h
cutoff_24h = now - timedelta(hours=24)
detection_24h = [
    r for r in records
    if r["portnum"] == "DETECTION_SENSOR_APP"
    and datetime.fromisoformat(r["received_at"]) >= cutoff_24h
]
unique_senders_24h = set(r["sender"] for r in detection_24h)

# Count new alerts from event_monitor (records after offset that are DETECTION_SENSOR_APP)
new_detection_records = [
    r for r in records[20:]  # lines after offset
    if r["portnum"] == "DETECTION_SENSOR_APP"
]

ground_truth = {
    "total_detections_24h": len(detection_24h),
    "unique_senders_24h": len(unique_senders_24h),
    "unique_senders_list_24h": sorted(list(unique_senders_24h)),
    "new_alert_count_from_monitor": len(new_detection_records),
    "total_detection_records_all": len(detection_records),
}
(WORKSPACE / "data" / "_ground_truth.json").write_text(
    json.dumps(ground_truth, indent=2)
)

print("Workspace generated successfully.")
print(f"Total records: {len(records)}")
print(f"Detection records (all): {len(detection_records)}")
print(f"Detection records (24h): {len(detection_24h)}")
print(f"Unique senders (24h): {len(unique_senders_24h)}")
print(f"New alerts from monitor (after offset): {len(new_detection_records)}")
print(f"Byte offset stored in monitor_state: {offset_after_20}")
print(f"\nGround truth saved to: data/_ground_truth.json")
print(f"Contents: {ground_truth}")