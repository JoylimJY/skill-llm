import json
import os
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    campaign = workspace / "memory" / "rpg" / "neon_drift"
    add_check("campaign_directory_exists", campaign.exists(), f"Path: {campaign}")
except Exception as e:
    add_check("campaign_directory_exists", False, f"Error: {type(e).__name__}: {e}")

try:
    world_path = workspace / "memory" / "rpg" / "neon_drift" / "world.json"
    if not world_path.exists():
        add_check("world_json_exists", False, "world.json is missing")
    else:
        data = json.loads(world_path.read_text(encoding='utf-8'))
        text = json.dumps(data).lower()
        ok = all(k in text for k in ["neon_drift", "cyberpunk", "gritty", "world_marker_42"])
        add_check("world_json_content", ok, "Required markers and metadata present" if ok else "Missing expected values in world.json")
except Exception as e:
    add_check("world_json_content", False, f"Error: {type(e).__name__}: {e}")

try:
    char_path = workspace / "memory" / "rpg" / "neon_drift" / "character.json"
    if not char_path.exists():
        add_check("character_json_exists", False, "character.json is missing")
    else:
        data = json.loads(char_path.read_text(encoding='utf-8'))
        text = json.dumps(data).lower()
        ok = all(k in text for k in ["mira", "hacker", "cheap datajack", "marker_item_alpha"])
        add_check("character_json_content", ok, "Required character markers present" if ok else "Missing expected values in character.json")
except Exception as e:
    add_check("character_json_content", False, f"Error: {type(e).__name__}: {e}")

try:
    journal_path = workspace / "memory" / "rpg" / "neon_drift" / "journal.md"
    if not journal_path.exists():
        add_check("journal_exists", False, "journal.md is missing")
    else:
        text = journal_path.read_text(encoding='utf-8').lower()
        ok = all(k in text for k in ["session zero", "begun", "marker_journal_99"])
        add_check("journal_content", ok, "Journal contains start marker" if ok else "Journal missing expected marker text")
except Exception as e:
    add_check("journal_content", False, f"Error: {type(e).__name__}: {e}")

try:
    npc_path = workspace / "memory" / "rpg" / "neon_drift" / "npcs.json"
    if not npc_path.exists():
        add_check("npcs_json_exists", False, "npcs.json is missing")
    else:
        data = json.loads(npc_path.read_text(encoding='utf-8'))
        text = json.dumps(data).lower()
        ok = "npc_marker_7" in text
        add_check("npcs_json_content", ok, "NPC marker present" if ok else "Missing NPC marker")
except Exception as e:
    add_check("npcs_json_content", False, f"Error: {type(e).__name__}: {e}")

try:
    passed = all(c["passed"] for c in checks)
    score = sum(1 for c in checks if c["passed"]) / len(checks) if checks else 0.0
    print(json.dumps({"passed": passed, "score": score, "checks": checks}))
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks + [{"name": "finalize", "passed": False, "detail": f"Error: {type(e).__name__}: {e}"}]}))
