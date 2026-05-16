#!/usr/bin/env python3
import sys
import json
import os
import re

workspace = sys.argv[1]
home = f"/home/agent"

checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

# ── 1. Config file exists at the CORRECT Linux path ──────────────────────────
config_path = os.path.join(home, ".config/clawnet/config.toml")
config_exists = os.path.isfile(config_path)
check(
    "config_file_at_correct_linux_path",
    config_exists,
    f"Expected config at {config_path}, exists={config_exists}"
)

config_content = ""
config_data = {}
if config_exists:
    try:
        with open(config_path, "r") as f:
            config_content = f.read()
        # Parse TOML manually (basic key=value)
        for line in config_content.splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if "=" in line:
                k, _, v = line.partition("=")
                config_data[k.strip()] = v.strip().strip('"').strip("'")
    except Exception as e:
        check("config_file_readable", False, f"Error reading config: {e}")

# ── 2. Config: bot name is "sentinel-7" ──────────────────────────────────────
bot_name = config_data.get("name", "")
check(
    "config_name_is_sentinel7",
    bot_name == "sentinel-7",
    f"Expected name='sentinel-7', got '{bot_name}'"
)

# ── 3. Config: capabilities includes search, monitor, alert ──────────────────
capabilities_raw = config_data.get("capabilities", "")
# May be array notation: ["search", "monitor", "alert"]
caps_str = capabilities_raw.lower()
has_search = "search" in caps_str
has_monitor = "monitor" in caps_str
has_alert = "alert" in caps_str
check(
    "config_capabilities_search_monitor_alert",
    has_search and has_monitor and has_alert,
    f"capabilities raw='{capabilities_raw}', search={has_search}, monitor={has_monitor}, alert={has_alert}"
)

# ── 4. Config: announce_interval = 120 ───────────────────────────────────────
announce_interval = config_data.get("announce_interval", "")
check(
    "config_announce_interval_120",
    str(announce_interval) == "120",
    f"Expected announce_interval=120, got '{announce_interval}'"
)

# ── 5. Config: peer_ttl = 600 ────────────────────────────────────────────────
peer_ttl = config_data.get("peer_ttl", "")
check(
    "config_peer_ttl_600",
    str(peer_ttl) == "600",
    f"Expected peer_ttl=600, got '{peer_ttl}'"
)

# ── 6. Config: mode = "dedicated" ────────────────────────────────────────────
mode = config_data.get("mode", "")
check(
    "config_mode_dedicated",
    mode == "dedicated",
    f"Expected mode='dedicated', got '{mode}'"
)

# ── 7. Config: openclaw_version = "1.0.0" ────────────────────────────────────
ocv = config_data.get("openclaw_version", "")
check(
    "config_openclaw_version_1_0_0",
    ocv == "1.0.0",
    f"Expected openclaw_version='1.0.0', got '{ocv}'"
)

# ── 8. Friends file at correct Linux path ────────────────────────────────────
friends_path = os.path.join(home, ".local/share/clawnet/friends.json")
friends_exists = os.path.isfile(friends_path)
check(
    "friends_file_at_correct_linux_path",
    friends_exists,
    f"Expected friends at {friends_path}, exists={friends_exists}"
)

friends_data = []
if friends_exists:
    try:
        with open(friends_path, "r") as f:
            friends_data = json.load(f)
    except Exception as e:
        check("friends_file_valid_json", False, f"Error parsing friends.json: {e}")

# ── 9. All 3 trusted peers are in friends ────────────────────────────────────
EXPECTED_NODE_IDS = {
    "b5e7f3a91c2d4e6f8a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f",
    "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
    "f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1"
}

registered_ids = set()
if isinstance(friends_data, list):
    for entry in friends_data:
        if isinstance(entry, dict):
            nid = entry.get("node_id", "")
            if nid:
                registered_ids.add(nid)

missing = EXPECTED_NODE_IDS - registered_ids
check(
    "all_three_trusted_peers_registered_as_friends",
    len(missing) == 0,
    f"Missing friends: {missing}, registered: {registered_ids}"
)

# ── 10. friends_export.json was created ──────────────────────────────────────
try:
    export_files = list(__import__("pathlib").Path(workspace).rglob("friends_export.json"))
    # Also search home dir
    export_files += list(__import__("pathlib").Path(home).rglob("friends_export.json"))
    export_file = export_files[0] if export_files else None
    export_exists = export_file is not None
    check(
        "friends_export_json_created",
        export_exists,
        f"friends_export.json found at: {export_file}"
    )
except Exception as e:
    check("friends_export_json_created", False, f"Error searching for friends_export.json: {e}")
    export_file = None

# ── 11. friends_export.json contains valid JSON with all 3 friends ───────────
if export_file and os.path.isfile(str(export_file)):
    try:
        with open(str(export_file), "r") as f:
            export_data = json.load(f)

        if isinstance(export_data, list):
            export_ids = {e.get("node_id", "") for e in export_data if isinstance(e, dict)}
        elif isinstance(export_data, dict):
            # Maybe wrapped: {"friends": [...]}
            inner = export_data.get("friends", export_data.get("data", []))
            if isinstance(inner, list):
                export_ids = {e.get("node_id", "") for e in inner if isinstance(e, dict)}
            else:
                export_ids = set()
        else:
            export_ids = set()

        export_missing = EXPECTED_NODE_IDS - export_ids
        check(
            "friends_export_contains_all_three_friends",
            len(export_missing) == 0,
            f"Export missing: {export_missing}, found IDs: {export_ids}"
        )
    except Exception as e:
        check("friends_export_contains_all_three_friends", False, f"Error parsing friends_export.json: {e}")
else:
    check("friends_export_contains_all_three_friends", False, "friends_export.json not found or not a file")

# ── 12. Config NOT at macOS path (must use Linux path) ───────────────────────
macos_config = os.path.join(home, "Library/Preferences/clawnet/config.toml")
check(
    "not_using_macos_path",
    not os.path.isfile(macos_config),
    f"macOS config path should NOT be used in Linux container; macos_path_exists={os.path.isfile(macos_config)}"
)

# ── Score ─────────────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4)
overall = passed_count >= 9  # Must pass at least 9 of 12 checks

result = {
    "passed": overall,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))