import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Create distractor directory structure ---
dirs = [
    "scripts",
    "docs/network",
    "docs/hardware",
    "logs/2024",
    "logs/2023",
    "config/backups",
    "config/templates",
    "reports/q1",
    "reports/q2",
    "assets/diagrams",
    "tools/legacy",
    ".config/netmap",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "docs/network/topology_notes.txt": "Draft network topology notes from Q1 meeting.\nNeed to verify VLAN assignments.",
    "docs/network/old_device_list.csv": "IP,Device,Owner\n192.168.1.1,Router,IT\n192.168.1.50,Unknown,?\n10.0.0.5,Printer,Finance",
    "docs/hardware/purchase_orders.txt": "PO#2024-001: 3x Raspberry Pi 4\nPO#2024-002: 2x Unmanaged Switch",
    "logs/2024/scan_log_jan.txt": "Manual scan performed 2024-01-15. Found 12 devices. No anomalies.",
    "logs/2024/scan_log_feb.txt": "Scan 2024-02-10: New device detected MAC AA:BB:CC:11:22:33 - unidentified.",
    "logs/2023/archive.txt": "Legacy scan logs archived. See new system for current data.",
    "config/backups/devices_backup_old.json": json.dumps({"version": 1, "devices": []}),
    "config/templates/label_template.txt": "DEVICE_IP | FRIENDLY_NAME | DEPARTMENT",
    "reports/q1/inventory_draft.txt": "Draft inventory — not finalized. Do not use for production.",
    "reports/q2/placeholder.txt": "Q2 report pending network audit completion.",
    "assets/diagrams/floor_plan_notes.txt": "Server room: rack A slots 1-4 occupied. Break room: AP mounted above door.",
    "tools/legacy/old_scanner.sh": "#!/bin/bash\n# Deprecated. Use new netmap system.\nnmap -sn 192.168.1.0/24",
    ".config/netmap/README_IGNORE.txt": "This directory is managed by the netmap tool. Do not edit manually.",
}

for path, content in distractor_files.items():
    fpath = workspace / path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# --- Create the pre-populated device database ---
# Simulate a network that was already scanned, with some devices present
# Times: some devices are "new" (within last 60 min), some are older
now = datetime.now()
older_time = (now - timedelta(hours=5)).isoformat()
recent_time_1 = (now - timedelta(minutes=25)).isoformat()  # within 60 min
recent_time_2 = (now - timedelta(minutes=45)).isoformat()  # within 60 min
very_recent = (now - timedelta(minutes=10)).isoformat()    # within 60 min

devices_data = {
    "devices": {
        "192.168.1.1": {
            "ip": "192.168.1.1",
            "mac": "AA:BB:CC:00:11:22",
            "hostname": "gateway.local",
            "vendor": "Cisco Systems",
            "type": "router",
            "label": "",
            "first_seen": (now - timedelta(days=30)).isoformat(),
            "last_seen": older_time
        },
        "192.168.1.10": {
            "ip": "192.168.1.10",
            "mac": "DE:AD:BE:EF:01:01",
            "hostname": "nas-storage.local",
            "vendor": "Synology",
            "type": "nas",
            "label": "",
            "first_seen": (now - timedelta(days=15)).isoformat(),
            "last_seen": older_time
        },
        "192.168.1.20": {
            "ip": "192.168.1.20",
            "mac": "11:22:33:44:55:66",
            "hostname": "canon-mfp.local",
            "vendor": "Canon Inc.",
            "type": "printer",
            "label": "",
            "first_seen": (now - timedelta(days=10)).isoformat(),
            "last_seen": older_time
        },
        "192.168.1.30": {
            "ip": "192.168.1.30",
            "mac": "AA:11:BB:22:CC:33",
            "hostname": "dev-workstation.local",
            "vendor": "Dell Inc.",
            "type": "workstation",
            "label": "",
            "first_seen": (now - timedelta(days=7)).isoformat(),
            "last_seen": older_time
        },
        "192.168.1.40": {
            "ip": "192.168.1.40",
            "mac": "FF:EE:DD:CC:BB:AA",
            "hostname": "apple-macbook.local",
            "vendor": "Apple Inc.",
            "type": "laptop",
            "label": "",
            "first_seen": (now - timedelta(days=3)).isoformat(),
            "last_seen": older_time
        },
        # NEW DEVICES (within 60 minutes) - these should be found by `new --minutes 60`
        "192.168.1.101": {
            "ip": "192.168.1.101",
            "mac": "00:1A:2B:3C:4D:5E",
            "hostname": "rpi-sensor.local",
            "vendor": "Raspberry Pi Foundation",
            "type": "unknown",
            "label": "",
            "first_seen": recent_time_1,
            "last_seen": recent_time_1
        },
        "192.168.1.102": {
            "ip": "192.168.1.102",
            "mac": "BE:EF:CA:FE:00:01",
            "hostname": "",
            "vendor": "Unknown",
            "type": "unknown",
            "label": "",
            "first_seen": recent_time_2,
            "last_seen": recent_time_2
        },
        "192.168.1.103": {
            "ip": "192.168.1.103",
            "mac": "12:34:56:78:9A:BC",
            "hostname": "new-laptop.local",
            "vendor": "Lenovo",
            "type": "laptop",
            "label": "",
            "first_seen": very_recent,
            "last_seen": very_recent
        },
    }
}

devices_path = workspace / ".config/netmap/devices.json"
devices_path.write_text(json.dumps(devices_data, indent=2))

print("Workspace initialized successfully.")
print(f"Device database written to: {devices_path}")
print(f"Total devices in DB: {len(devices_data['devices'])}")
print(f"Recent devices (within 60 min): 192.168.1.101, 192.168.1.102, 192.168.1.103")