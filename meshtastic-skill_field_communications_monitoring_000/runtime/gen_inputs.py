import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create distractor directory structure ---
dirs = [
    "field_ops/comms/logs",
    "field_ops/comms/config",
    "field_ops/reports/daily",
    "field_ops/reports/weekly",
    "field_ops/hardware/inventory",
    "field_ops/hardware/manuals",
    "scripts/archive",
    "scripts/legacy",
    "monitoring/alerts",
    "monitoring/dashboards",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractors = {
    "field_ops/comms/config/radio_config_old.yaml": "frequency: 433.0\npower: 20\nspread_factor: 7\n",
    "field_ops/comms/config/channel_plan.txt": "Channel 0: LongFast (default)\nChannel 1: MediumSlow\nChannel 2: ShortFast\n",
    "field_ops/comms/logs/old_session_2025.log": "2025-01-10 09:12:33 - Session started\n2025-01-10 09:15:01 - Node joined: node_alpha\n2025-01-10 10:00:00 - Session ended\n",
    "field_ops/reports/daily/report_2025-06-01.txt": "Daily activity: 12 nodes seen, 45 messages exchanged.\nNetwork health: GOOD\n",
    "field_ops/reports/daily/report_2025-06-02.txt": "Daily activity: 9 nodes seen, 33 messages exchanged.\nNetwork health: GOOD\n",
    "field_ops/reports/weekly/week_22_summary.txt": "Weekly summary: 7 days, avg 11 nodes/day.\nHighest traffic day: Wednesday\n",
    "field_ops/hardware/inventory/devices.csv": "serial,model,firmware,status\nRAK-001,RAK4631,2.3.14,active\nRAK-002,RAK4631,2.3.14,active\nHEL-001,Heltec V3,2.3.10,standby\n",
    "field_ops/hardware/manuals/rak4631_quickstart.txt": "1. Connect USB\n2. Power on\n3. Wait for LED sequence\n4. Run meshtastic --info\n",
    "scripts/archive/old_bridge.py": "# Deprecated bridge script - do not use\nimport serial\n# ... old implementation ...\n",
    "scripts/legacy/monitor_v1.sh": "#!/bin/bash\n# Legacy monitor - replaced by systemd service\ntail -f /tmp/mesh_messages.txt\n",
    "monitoring/alerts/alert_rules.json": json.dumps({"rules": [{"name": "distant_node", "threshold_km": 1000, "action": "notify"}]}),
    "monitoring/dashboards/config.json": json.dumps({"refresh_interval": 30, "show_map": True, "filter_noise": True}),
}

for rel_path, content in distractors.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# --- Create /tmp/mesh_messages.txt with realistic messy data ---
# Format: TIMESTAMP|CHANNEL|SENDER|DISTANCE|TEXT
# Include noise and interesting messages mixed together

messages = [
    # Noise messages - should be filtered
    "2026-06-10T07:00:01|LongFast|!11111111|45km|Hello!",
    "2026-06-10T07:05:22|LongFast|!22222222|120km|hey",
    "2026-06-10T07:10:45|LongFast|!33333333|88km|mqtt-test",
    "2026-06-10T07:15:00|LongFast|!44444444|200km|Hello!",
    "2026-06-10T07:20:10|LongFast|!55555555|310km|hey",
    # Interesting messages - varying distances
    "2026-06-10T07:25:33|LongFast|!a1b2c3d4|387km|Buenas, alguien en Madrid?",
    "2026-06-10T07:30:00|LongFast|!b2c3d4e5|654km|Guten Morgen aus Berlin!",
    "2026-06-10T07:35:12|LongFast|!c3d4e5f6|1243km|Bonjour de Paris, tous va bien?",
    "2026-06-10T07:40:55|LongFast|!d4e5f6a7|1876km|Emergency supply drop coordinates needed",
    # More noise
    "2026-06-10T07:45:00|LongFast|!66666666|55km|mqtt-test",
    "2026-06-10T07:50:18|LongFast|!77777777|180km|Hello!",
    # More interesting messages
    "2026-06-10T08:00:00|LongFast|!e5f6a7b8|2341km|De Nairobi, necesitamos asistencia medica",
    "2026-06-10T08:05:44|LongFast|!f6a7b8c9|892km|Anyone monitoring this channel? Medical team here.",
    "2026-06-10T08:10:22|LongFast|!a7b8c9d0|1102km|Bom dia! Equipas de campo precisam de coordenação",
    # Another noise batch
    "2026-06-10T08:15:00|LongFast|!88888888|75km|hey",
    "2026-06-10T08:20:00|LongFast|!99999999|422km|Hello!",
    # More interesting
    "2026-06-10T08:25:30|LongFast|!b8c9d0e1|1654km|Field team alpha reporting in. All safe.",
    "2026-06-10T08:30:00|LongFast|!c9d0e1f2|3102km|MQTT relay from Auckland - mesh test successful",
    "2026-06-10T08:35:15|LongFast|!d0e1f2a3|445km|Relay station operational, forwarding traffic",
]

os.makedirs("/tmp", exist_ok=True)
with open("/tmp/mesh_messages.txt", "w") as f:
    f.write("\n".join(messages) + "\n")

# --- Create /tmp/mesh_nodes.json with cached node data ---
nodes_data = {
    "nodes": [
        {"id": "!a1b2c3d4", "name": "ES-Node-Madrid", "snr": -5.2, "last_seen": "2026-06-10T07:25:33", "distance_km": 387},
        {"id": "!b2c3d4e5", "name": "DE-Node-Berlin", "snr": -8.1, "last_seen": "2026-06-10T07:30:00", "distance_km": 654},
        {"id": "!c3d4e5f6", "name": "FR-Node-Paris", "snr": -10.3, "last_seen": "2026-06-10T07:35:12", "distance_km": 1243},
        {"id": "!d4e5f6a7", "name": "Field-Alpha", "snr": -12.7, "last_seen": "2026-06-10T07:40:55", "distance_km": 1876},
        {"id": "!e5f6a7b8", "name": "KE-Node-Nairobi", "snr": -14.9, "last_seen": "2026-06-10T08:00:00", "distance_km": 2341},
        {"id": "!f6a7b8c9", "name": "Medical-Team-1", "snr": -9.4, "last_seen": "2026-06-10T08:05:44", "distance_km": 892},
        {"id": "!a7b8c9d0", "name": "PT-Node-Lisbon", "snr": -11.1, "last_seen": "2026-06-10T08:10:22", "distance_km": 1102},
        {"id": "!b8c9d0e1", "name": "Field-Alpha-2", "snr": -13.5, "last_seen": "2026-06-10T08:25:30", "distance_km": 1654},
        {"id": "!c9d0e1f2", "name": "NZ-Relay", "snr": -15.8, "last_seen": "2026-06-10T08:30:00", "distance_km": 3102},
        {"id": "!d0e1f2a3", "name": "Relay-Station-7", "snr": -6.0, "last_seen": "2026-06-10T08:35:15", "distance_km": 445},
    ],
    "last_updated": "2026-06-10T08:35:15"
}

with open("/tmp/mesh_nodes.json", "w") as f:
    json.dump(nodes_data, f, indent=2)

print("Workspace and input files generated successfully.")
print(f"  /tmp/mesh_messages.txt: {len(messages)} messages")
print(f"  /tmp/mesh_nodes.json: {len(nodes_data['nodes'])} nodes")
print(f"  Distractor files: {len(distractors)}")