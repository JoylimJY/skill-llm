#!/usr/bin/env python3
"""
Evaluation script for the network-scanner task.
Usage: python3 eval.py /workspace
"""

import json
import os
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
total_score = 0.0
max_checks = 10  # we'll normalize at end


def check(name, passed, detail=""):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed


# ── 1. Config file existence ──────────────────────────────────────────────────
config_path = Path.home() / ".config" / "network-scanner" / "networks.json"
config_data = None

try:
    if config_path.exists():
        with open(config_path) as f:
            config_data = json.load(f)
        check("config_file_exists", True, f"Found at {config_path}")
    else:
        check("config_file_exists", False, f"Not found at {config_path}")
except Exception as e:
    check("config_file_exists", False, f"Error reading config: {e}")
    config_data = None

# ── 2. Config has correct top-level keys ──────────────────────────────────────
if config_data is not None:
    has_networks_key = isinstance(config_data.get("networks"), dict)
    has_blocklist_key = isinstance(config_data.get("blocklist"), list)
    check(
        "config_schema_valid",
        has_networks_key and has_blocklist_key,
        f"networks: {has_networks_key}, blocklist: {has_blocklist_key}"
    )
else:
    check("config_schema_valid", False, "Config could not be loaded")

# ── 3. Named network 'lab' exists with correct CIDR ───────────────────────────
lab_ok = False
if config_data:
    networks = config_data.get("networks", {})
    lab = networks.get("lab", {})
    cidr_ok = lab.get("cidr", "").strip() == "10.0.1.0/24"
    lab_ok = cidr_ok
    check(
        "network_lab_cidr",
        lab_ok,
        f"lab.cidr='{lab.get('cidr','')}' (expected 10.0.1.0/24)"
    )
else:
    check("network_lab_cidr", False, "Config not loaded")

# ── 4. Named network 'lab' has description ────────────────────────────────────
if config_data:
    lab = config_data.get("networks", {}).get("lab", {})
    desc = lab.get("description", "").strip()
    desc_ok = len(desc) > 0
    check("network_lab_description", desc_ok, f"lab.description='{desc}'")
else:
    check("network_lab_description", False, "Config not loaded")

# ── 5. Named network 'dmz' exists with correct CIDR ──────────────────────────
dmz_ok = False
if config_data:
    networks = config_data.get("networks", {})
    dmz = networks.get("dmz", {})
    cidr_ok = dmz.get("cidr", "").strip() == "172.16.0.0/24"
    dmz_ok = cidr_ok
    check(
        "network_dmz_cidr",
        dmz_ok,
        f"dmz.cidr='{dmz.get('cidr','')}' (expected 172.16.0.0/24)"
    )
else:
    check("network_dmz_cidr", False, "Config not loaded")

# ── 6. Blocklist contains 10.99.0.0/24 with correct reason ───────────────────
if config_data:
    blocklist = config_data.get("blocklist", [])
    blocked_entry = None
    for entry in blocklist:
        if entry.get("cidr", "").strip() == "10.99.0.0/24":
            blocked_entry = entry
            break
    if blocked_entry:
        reason = blocked_entry.get("reason", "").strip()
        reason_ok = len(reason) > 0
        check(
            "blocklist_10_99_entry",
            True,
            f"Found entry: cidr=10.99.0.0/24, reason='{reason}'"
        )
        check(
            "blocklist_10_99_has_reason",
            reason_ok,
            f"reason field: '{reason}'"
        )
    else:
        check("blocklist_10_99_entry", False,
              f"10.99.0.0/24 not found in blocklist. blocklist={blocklist}")
        check("blocklist_10_99_has_reason", False, "Entry missing")
else:
    check("blocklist_10_99_entry", False, "Config not loaded")
    check("blocklist_10_99_has_reason", False, "Config not loaded")

# ── 7. lab_inventory.json exists with correct JSON schema ─────────────────────
inventory_files = list(workspace.rglob("lab_inventory.json"))
inventory_data = None

try:
    if inventory_files:
        inv_path = inventory_files[0]
        with open(inv_path) as f:
            inventory_data = json.load(f)
        check("lab_inventory_exists", True, f"Found at {inv_path}")
    else:
        check("lab_inventory_exists", False, "lab_inventory.json not found anywhere in workspace")
except Exception as e:
    check("lab_inventory_exists", False, f"Error reading lab_inventory.json: {e}")

if inventory_data is not None:
    # Must have the proprietary JSON keys from SKILL.md
    required_keys = {"network", "cidr", "devices", "scanned_at", "device_count"}
    present_keys = set(inventory_data.keys())
    missing = required_keys - present_keys
    has_all_keys = len(missing) == 0
    check(
        "lab_inventory_json_schema",
        has_all_keys,
        f"Present: {present_keys}, Missing: {missing}"
    )
    # cidr must match lab network
    cidr_val = inventory_data.get("cidr", "")
    check(
        "lab_inventory_cidr_correct",
        cidr_val.strip() == "10.0.1.0/24",
        f"cidr='{cidr_val}' (expected 10.0.1.0/24)"
    )
    # devices must be a list
    devices_val = inventory_data.get("devices")
    check(
        "lab_inventory_devices_is_list",
        isinstance(devices_val, list),
        f"devices type: {type(devices_val).__name__}"
    )
else:
    check("lab_inventory_json_schema", False, "File not loaded")
    check("lab_inventory_cidr_correct", False, "File not loaded")
    check("lab_inventory_devices_is_list", False, "File not loaded")

# ── 8. network_list.txt exists and contains both lab and dmz ─────────────────
list_files = list(workspace.rglob("network_list.txt"))
list_content = None

try:
    if list_files:
        list_path = list_files[0]
        with open(list_path) as f:
            list_content = f.read()
        check("network_list_exists", True, f"Found at {list_path}")
    else:
        check("network_list_exists", False, "network_list.txt not found in workspace")
except Exception as e:
    check("network_list_exists", False, f"Error reading network_list.txt: {e}")

if list_content is not None:
    has_lab = "lab" in list_content.lower()
    has_dmz = "dmz" in list_content.lower()
    check(
        "network_list_contains_lab_dmz",
        has_lab and has_dmz,
        f"has_lab={has_lab}, has_dmz={has_dmz}\nContent snippet: {list_content[:300]}"
    )
else:
    check("network_list_contains_lab_dmz", False, "File not loaded")

# ── Scoring ───────────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / len(checks), 4) if checks else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))