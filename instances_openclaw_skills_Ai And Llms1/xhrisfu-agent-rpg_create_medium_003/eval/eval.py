from pathlib import Path
import json
import sys

workspace = Path(sys.argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})

try:
    campaign = workspace / "memory" / "rpg" / "neon_ash"
    add_check("campaign_dir_exists", campaign.exists(), f"path={campaign}")
except Exception as e:
    add_check("campaign_dir_exists", False, f"error: {e}")


def load_json(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        return None, str(e)

try:
    world_path = campaign / "world.json"
    if world_path.exists():
        try:
            world = json.loads(world_path.read_text(encoding='utf-8'))
            text = json.dumps(world).lower()
            ok = all(marker.lower() in text for marker in ["neon_marker_world", "cyberpunk", "gritty"])
            add_check("world_marker_content", ok, "markers present" if ok else "missing required world markers")
        except Exception as e:
            add_check("world_marker_content", False, f"error reading/parsing world.json: {e}")
    else:
        add_check("world_marker_content", False, "world.json missing")
except Exception as e:
    add_check("world_marker_content", False, f"error: {e}")

try:
    char_path = campaign / "character.json"
    if char_path.exists():
        try:
            char = json.loads(char_path.read_text(encoding='utf-8'))
            text = json.dumps(char).lower()
            ok = all(marker.lower() in text for marker in ["mara vex", "street samurai", "neon_marker_char"])
            add_check("character_marker_content", ok, "markers present" if ok else "missing required character markers")
        except Exception as e:
            add_check("character_marker_content", False, f"error reading/parsing character.json: {e}")
    else:
        add_check("character_marker_content", False, "character.json missing")
except Exception as e:
    add_check("character_marker_content", False, f"error: {e}")

try:
    npc_path = campaign / "npcs.json"
    if npc_path.exists():
        try:
            npc = json.loads(npc_path.read_text(encoding='utf-8'))
            text = json.dumps(npc).lower()
            ok = "neon_marker_npc" in text and "sable kade" in text
            add_check("npc_marker_content", ok, "npc marker present" if ok else "missing npc marker content")
        except Exception as e:
            add_check("npc_marker_content", False, f"error reading/parsing npcs.json: {e}")
    else:
        add_check("npc_marker_content", False, "npcs.json missing")
except Exception as e:
    add_check("npc_marker_content", False, f"error: {e}")

try:
    journal_path = campaign / "journal.md"
    if journal_path.exists():
        try:
            text = journal_path.read_text(encoding='utf-8').lower()
            ok = "neon_marker_journal" in text and "campaign initialized" in text
            add_check("journal_marker_content", ok, "journal marker present" if ok else "missing journal marker content")
        except Exception as e:
            add_check("journal_marker_content", False, f"error reading journal.md: {e}")
    else:
        add_check("journal_marker_content", False, "journal.md missing")
except Exception as e:
    add_check("journal_marker_content", False, f"error: {e}")

passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result))
