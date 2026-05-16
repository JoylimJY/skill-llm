import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create deeply nested distractor directory structure ---
distractor_dirs = [
    "home_automation/logs/2024/january",
    "home_automation/logs/2024/february",
    "home_automation/configs/backup",
    "home_automation/configs/archive",
    "home_automation/devices/sensors",
    "home_automation/devices/cameras",
    "home_automation/devices/thermostats",
    "home_automation/reports/monthly",
    "home_automation/reports/weekly",
    "home_automation/scripts/old",
    "home_automation/scripts/deprecated",
    "tenant_management/unit_101",
    "tenant_management/unit_102",
    "tenant_management/unit_103",
    "maintenance/requests",
    "maintenance/completed",
]

for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "home_automation/logs/2024/january/hvac_events.log": "2024-01-15 08:00:00 HVAC unit bedroom - mode changed to heat\n2024-01-15 08:05:00 HVAC unit living_room - temperature set to 24\n",
    "home_automation/logs/2024/february/hvac_events.log": "2024-02-10 09:00:00 HVAC unit bedroom - fan_speed set to medium\n2024-02-10 09:01:00 HVAC unit living_room - turned on\n",
    "home_automation/configs/backup/device_map.json": json.dumps({"bedroom": "192.168.1.101", "living_room": "192.168.1.102", "kitchen": "192.168.1.103"}, indent=2),
    "home_automation/configs/archive/old_settings.json": json.dumps({"version": "1.0", "rooms": ["bedroom", "living_room", "kitchen"], "default_temp": 22}, indent=2),
    "home_automation/devices/thermostats/thermostat_list.csv": "room,ip,model\nbedroom,192.168.1.101,MideaV3\nliving_room,192.168.1.102,MideaV3\nkitchen,192.168.1.103,MideaV2\n",
    "home_automation/devices/sensors/temp_readings.json": json.dumps({"bedroom": 23.5, "living_room": 21.0, "kitchen": 20.0}, indent=2),
    "home_automation/reports/monthly/feb_summary.txt": "Monthly HVAC Report - February 2024\nTotal runtime: 320 hours\nAverage temperature: 22.5C\n",
    "home_automation/reports/weekly/week8.txt": "Week 8 Report\nBedroom AC: 48hrs runtime\nLiving room AC: 52hrs runtime\n",
    "home_automation/scripts/old/legacy_control.sh": "#!/bin/bash\n# DEPRECATED - do not use\necho 'legacy control'\n",
    "home_automation/scripts/deprecated/set_temp.py": "# DEPRECATED\n# Use new skill instead\nprint('not implemented')\n",
    "tenant_management/unit_101/profile.json": json.dumps({"tenant": "Alice Smith", "unit": 101, "rooms": ["bedroom", "living_room"]}, indent=2),
    "tenant_management/unit_102/profile.json": json.dumps({"tenant": "Bob Jones", "unit": 102, "rooms": ["bedroom", "kitchen"]}, indent=2),
    "tenant_management/unit_103/profile.json": json.dumps({"tenant": "Carol White", "unit": 103, "rooms": ["living_room"]}, indent=2),
    "maintenance/requests/req_2024_003.txt": "Request #003: Bedroom AC not responding to fan speed commands\nStatus: Pending\nDate: 2024-02-20\n",
    "maintenance/completed/req_2024_001.txt": "Request #001: Living room AC temperature calibration\nStatus: Completed\nDate: 2024-02-01\n",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content)

# --- Create the skill directory structure ---
skill_dir = Path.home() / ".openclaw" / "skills" / "midea_ac" / "scripts"
skill_dir.mkdir(parents=True, exist_ok=True)

# --- Create the mock state file used by midea_ac.py ---
state_dir = Path.home() / ".openclaw" / "skills" / "midea_ac" / "state"
state_dir.mkdir(parents=True, exist_ok=True)

# Initial AC states
# living_room: ON, mode=cool, temperature=24, fan_speed=medium, aux_mode=off
# bedroom: ON, mode=heat, temperature=22, fan_speed=low, aux_mode=off
initial_state = {
    "living_room": {
        "power": "on",
        "mode": "cool",
        "temperature": 24,
        "fan_speed": "medium",
        "aux_mode": "off"
    },
    "bedroom": {
        "power": "on",
        "mode": "heat",
        "temperature": 22,
        "fan_speed": "low",
        "aux_mode": "off"
    },
    "kitchen": {
        "power": "off",
        "mode": "cool",
        "temperature": 25,
        "fan_speed": "auto",
        "aux_mode": "off"
    }
}

state_file = state_dir / "ac_state.json"
state_file.write_text(json.dumps(initial_state, indent=2))

print("Workspace and skill state initialized.")
print(f"Initial AC state written to: {state_file}")
print(json.dumps(initial_state, indent=2))