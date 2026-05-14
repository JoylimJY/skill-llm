#!/usr/bin/env python3
"""Evaluation script for the wol-sleep-pc skill task."""
import sys, json, pathlib, re

workspace = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/workspace")

checks = []
overall_passed = True

def add_check(name: str, passed: bool, detail: str):
    global overall_passed
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        overall_passed = False

# ──────────────────────────────────────────────────────────────────────────
# CHECK 1: Config file exists at the correct proprietary path
# ──────────────────────────────────────────────────────────────────────────
config_path = pathlib.Path.home() / ".config" / "wol-sleep-pc" / "config.json"
try:
    config_text = config_path.read_text()
    config_data = json.loads(config_text)
    add_check(
        "config_file_exists_at_correct_path",
        True,
        f"Found config at {config_path}"
    )
except FileNotFoundError:
    add_check("config_file_exists_at_correct_path", False,
              f"Config not found at {config_path}. Wrong path or not created.")
    config_data = {}
except json.JSONDecodeError as e:
    add_check("config_file_exists_at_correct_path", False,
              f"Config file at {config_path} is not valid JSON: {e}")
    config_data = {}

# ──────────────────────────────────────────────────────────────────────────
# CHECK 2: Config has all four required fields, non-zero/non-template values
# ──────────────────────────────────────────────────────────────────────────
required_fields = {"mac", "sleep_mac", "broadcast", "port"}
missing = required_fields - set(config_data.keys())
if missing:
    add_check("config_has_required_fields", False,
              f"Config missing fields: {missing}")
else:
    add_check("config_has_required_fields", True,
              f"All required fields present: {list(config_data.keys())}")

# ──────────────────────────────────────────────────────────────────────────
# CHECK 3: MAC address is non-zero and valid format
# ──────────────────────────────────────────────────────────────────────────
mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$')
mac_val = config_data.get("mac", "00:00:00:00:00:00")
sleep_mac_val = config_data.get("sleep_mac", "00:00:00:00:00:00")

mac_valid = bool(mac_pattern.match(str(mac_val))) and mac_val != "00:00:00:00:00:00"
add_check(
    "config_mac_is_valid_nonzero",
    mac_valid,
    f"mac='{mac_val}' valid={mac_valid}"
)

# ──────────────────────────────────────────────────────────────────────────
# CHECK 4: sleep_mac is the byte-reversed (inverted) form of mac
# i.e., bytes of sleep_mac reversed == bytes of mac
# ──────────────────────────────────────────────────────────────────────────
try:
    mac_bytes = [b.lower() for b in re.split(r'[:\-]', mac_val)]
    sleep_bytes = [b.lower() for b in re.split(r'[:\-]', sleep_mac_val)]
    is_inverted = (list(reversed(mac_bytes)) == sleep_bytes)
    add_check(
        "sleep_mac_is_byte_reversed_of_mac",
        is_inverted,
        f"mac bytes: {mac_bytes}, sleep_mac bytes: {sleep_bytes}, reversed match: {is_inverted}"
    )
except Exception as e:
    add_check("sleep_mac_is_byte_reversed_of_mac", False, f"Error comparing MACs: {e}")

# ──────────────────────────────────────────────────────────────────────────
# CHECK 5: broadcast is a valid, non-zero broadcast address
# ──────────────────────────────────────────────────────────────────────────
bcast = config_data.get("broadcast", "0.0.0.0")
bcast_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.(255|0)$')
bcast_valid = bool(bcast_pattern.match(str(bcast))) and bcast not in ("0.0.0.0", "255.255.255.255")
# allow 255.255.255.255 as it's a valid global broadcast
bcast_valid = bool(bcast_pattern.match(str(bcast))) or bcast == "255.255.255.255"
bcast_nonzero = bcast != "0.0.0.0"
add_check(
    "config_broadcast_is_valid",
    bcast_valid and bcast_nonzero,
    f"broadcast='{bcast}'"
)

# ──────────────────────────────────────────────────────────────────────────
# CHECK 6: port is 9 (standard WOL port per SKILL.md example)
# ──────────────────────────────────────────────────────────────────────────
port_val = config_data.get("port", 0)
add_check(
    "config_port_is_9",
    port_val == 9,
    f"port={port_val}, expected 9"
)

# ──────────────────────────────────────────────────────────────────────────
# CHECK 7: send_wol.py was executed and used the config's MAC
# ──────────────────────────────────────────────────────────────────────────
wol_log = pathlib.Path("/tmp/wol_invocations.log")
try:
    wol_entries = [json.loads(line) for line in wol_log.read_text().strip().splitlines() if line.strip()]
    if not wol_entries:
        raise ValueError("Empty log")
    # Latest entry
    latest_wol = wol_entries[-1]
    wol_mac_used = latest_wol.get("mac", "")
    config_mac = config_data.get("mac", "MISSING")
    mac_matches = wol_mac_used.lower() == config_mac.lower()
    add_check(
        "wol_script_executed_with_config_mac",
        mac_matches,
        f"WOL used mac='{wol_mac_used}', config mac='{config_mac}', match={mac_matches}"
    )
except FileNotFoundError:
    add_check("wol_script_executed_with_config_mac", False,
              "WOL log not found — send_wol.py was never executed.")
except Exception as e:
    add_check("wol_script_executed_with_config_mac", False, f"Error reading WOL log: {e}")

# ──────────────────────────────────────────────────────────────────────────
# CHECK 8: send_sleep.py was executed with a CLI --mac override
# (the MAC used must differ from the config's sleep_mac field,
#  proving that CLI override was used, not just the config default)
# ──────────────────────────────────────────────────────────────────────────
sol_log = pathlib.Path("/tmp/sol_invocations.log")
try:
    sol_entries = [json.loads(line) for line in sol_log.read_text().strip().splitlines() if line.strip()]
    if not sol_entries:
        raise ValueError("Empty log")

    # Find an entry where the mac differs from the config sleep_mac (override proof)
    config_sleep_mac = config_data.get("sleep_mac", "MISSING")
    
    override_entry = None
    for entry in sol_entries:
        used_mac = entry.get("mac", "")
        if used_mac.lower() != config_sleep_mac.lower():
            override_entry = entry
            break

    if override_entry is not None:
        add_check(
            "sol_script_executed_with_cli_mac_override",
            True,
            f"SOL override confirmed: used mac='{override_entry['mac']}' != config sleep_mac='{config_sleep_mac}'"
        )
    else:
        # All entries used the config sleep_mac — no override was demonstrated
        used_macs = [e.get("mac") for e in sol_entries]
        add_check(
            "sol_script_executed_with_cli_mac_override",
            False,
            f"SOL was only ever called with config sleep_mac='{config_sleep_mac}'. "
            f"No CLI --mac override detected. Used: {used_macs}"
        )
except FileNotFoundError:
    add_check("sol_script_executed_with_cli_mac_override", False,
              "SOL log not found — send_sleep.py was never executed.")
except Exception as e:
    add_check("sol_script_executed_with_cli_mac_override", False, f"Error reading SOL log: {e}")

# ──────────────────────────────────────────────────────────────────────────
# CHECK 9: The override MAC used for SOL is itself a valid non-zero MAC
# ──────────────────────────────────────────────────────────────────────────
try:
    sol_entries_all = [json.loads(line) for line in sol_log.read_text().strip().splitlines() if line.strip()]
    config_sleep_mac = config_data.get("sleep_mac", "MISSING")
    override_macs = [e["mac"] for e in sol_entries_all if e.get("mac","").lower() != config_sleep_mac.lower()]
    if override_macs:
        ov_mac = override_macs[-1]
        ov_valid = bool(mac_pattern.match(str(ov_mac))) and ov_mac != "00:00:00:00:00:00"
        add_check(
            "sol_override_mac_is_valid_nonzero",
            ov_valid,
            f"Override MAC '{ov_mac}' valid={ov_valid}"
        )
    else:
        add_check("sol_override_mac_is_valid_nonzero", False,
                  "No override MAC found to validate.")
except Exception as e:
    add_check("sol_override_mac_is_valid_nonzero", False, f"Error: {e}")

# ──────────────────────────────────────────────────────────────────────────
# Score
# ──────────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total else 0.0

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))