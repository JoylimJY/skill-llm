import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]
ws = Path(workspace)

checks = []
total_score = 0.0

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ─────────────────────────────────────────────
# CHECK 1: .env file has correct EVOLVE_STRATEGY
# Must be one of the valid values from SKILL.md, and appropriate for production-adjacent staging ("harden")
# ─────────────────────────────────────────────
VALID_STRATEGIES = {"balanced", "innovate", "harden", "repair-only", "early-stabilize", "steady-state", "auto"}

try:
    env_path = ws / ".env"
    if not env_path.exists():
        checks.append(make_check("env_EVOLVE_STRATEGY_valid", False, ".env file not found"))
    else:
        env_content = env_path.read_text()
        strategy_match = re.search(r'EVOLVE_STRATEGY\s*=\s*(\S+)', env_content)
        if not strategy_match:
            checks.append(make_check("env_EVOLVE_STRATEGY_valid", False, "EVOLVE_STRATEGY not set in .env"))
        else:
            strategy_val = strategy_match.group(1).strip().strip('"').strip("'")
            if strategy_val in VALID_STRATEGIES:
                checks.append(make_check("env_EVOLVE_STRATEGY_valid", True, f"EVOLVE_STRATEGY='{strategy_val}' is a valid strategy value"))
                total_score += 10
            else:
                checks.append(make_check("env_EVOLVE_STRATEGY_valid", False, f"EVOLVE_STRATEGY='{strategy_val}' is NOT a valid strategy. Valid values: {VALID_STRATEGIES}"))
except Exception as e:
    checks.append(make_check("env_EVOLVE_STRATEGY_valid", False, f"Exception: {e}"))

# ─────────────────────────────────────────────
# CHECK 2: .env has EVOLVE_LOAD_MAX set to a numeric value less than default (2.0)
# ─────────────────────────────────────────────
try:
    env_path = ws / ".env"
    env_content = env_path.read_text() if env_path.exists() else ""
    load_match = re.search(r'EVOLVE_LOAD_MAX\s*=\s*([\d.]+)', env_content)
    if not load_match:
        checks.append(make_check("env_EVOLVE_LOAD_MAX_corrected", False, "EVOLVE_LOAD_MAX not found in .env"))
    else:
        load_val = float(load_match.group(1))
        # The original broken value was 9.9; agent must correct it to something reasonable (< 2.0 default or at least != 9.9)
        if load_val != 9.9 and load_val > 0:
            checks.append(make_check("env_EVOLVE_LOAD_MAX_corrected", True, f"EVOLVE_LOAD_MAX corrected to {load_val} (was 9.9)"))
            total_score += 10
        else:
            checks.append(make_check("env_EVOLVE_LOAD_MAX_corrected", False, f"EVOLVE_LOAD_MAX={load_val} still appears incorrect (original broken value was 9.9)"))
except Exception as e:
    checks.append(make_check("env_EVOLVE_LOAD_MAX_corrected", False, f"Exception: {e}"))

# ─────────────────────────────────────────────
# CHECK 3: .env has EVOLVE_ALLOW_SELF_MODIFY=false (safety requirement)
# ─────────────────────────────────────────────
try:
    env_path = ws / ".env"
    env_content = env_path.read_text() if env_path.exists() else ""
    selfmod_match = re.search(r'EVOLVE_ALLOW_SELF_MODIFY\s*=\s*(\S+)', env_content)
    if not selfmod_match:
        checks.append(make_check("env_EVOLVE_ALLOW_SELF_MODIFY_false", False, "EVOLVE_ALLOW_SELF_MODIFY not set in .env"))
    else:
        val = selfmod_match.group(1).strip().strip('"').strip("'").lower()
        if val == "false":
            checks.append(make_check("env_EVOLVE_ALLOW_SELF_MODIFY_false", True, "EVOLVE_ALLOW_SELF_MODIFY=false correctly set for safety"))
            total_score += 10
        else:
            checks.append(make_check("env_EVOLVE_ALLOW_SELF_MODIFY_false", False, f"EVOLVE_ALLOW_SELF_MODIFY='{val}' — must be 'false' for production safety"))
except Exception as e:
    checks.append(make_check("env_EVOLVE_ALLOW_SELF_MODIFY_false", False, f"Exception: {e}"))

# ─────────────────────────────────────────────
# CHECK 4: assets/gep/genes.json — valid JSON array with at least 2 gene definitions (non-empty objects)
# ─────────────────────────────────────────────
try:
    genes_path = ws / "assets" / "gep" / "genes.json"
    if not genes_path.exists():
        checks.append(make_check("gep_genes_populated", False, "assets/gep/genes.json not found"))
    else:
        genes_data = json.loads(genes_path.read_text())
        if not isinstance(genes_data, list):
            checks.append(make_check("gep_genes_populated", False, f"genes.json must be a JSON array, got {type(genes_data).__name__}"))
        elif len(genes_data) < 2:
            checks.append(make_check("gep_genes_populated", False, f"genes.json has {len(genes_data)} gene(s); at least 2 required"))
        else:
            # Check that genes are non-trivial (each has at least one key)
            non_empty = [g for g in genes_data if isinstance(g, dict) and len(g) > 0]
            if len(non_empty) >= 2:
                checks.append(make_check("gep_genes_populated", True, f"genes.json has {len(non_empty)} valid gene definitions"))
                total_score += 15
            else:
                checks.append(make_check("gep_genes_populated", False, f"genes.json entries appear empty or malformed: {genes_data[:2]}"))
except Exception as e:
    checks.append(make_check("gep_genes_populated", False, f"Exception parsing genes.json: {e}"))

# ─────────────────────────────────────────────
# CHECK 5: assets/gep/capsules.json — exists, valid JSON, at least 1 success capsule
# ─────────────────────────────────────────────
try:
    capsules_path = ws / "assets" / "gep" / "capsules.json"
    if not capsules_path.exists():
        checks.append(make_check("gep_capsules_created", False, "assets/gep/capsules.json not found (was never created)"))
    else:
        caps_data = json.loads(capsules_path.read_text())
        if isinstance(caps_data, list) and len(caps_data) >= 1:
            non_empty = [c for c in caps_data if isinstance(c, dict) and len(c) > 0]
            if non_empty:
                checks.append(make_check("gep_capsules_created", True, f"capsules.json created with {len(non_empty)} capsule(s)"))
                total_score += 15
            else:
                checks.append(make_check("gep_capsules_created", False, "capsules.json exists but contains empty entries"))
        elif isinstance(caps_data, dict) and len(caps_data) > 0:
            # accept single object too
            checks.append(make_check("gep_capsules_created", True, "capsules.json created with at least 1 capsule (object form)"))
            total_score += 15
        else:
            checks.append(make_check("gep_capsules_created", False, f"capsules.json invalid or empty: {str(caps_data)[:100]}"))
except Exception as e:
    checks.append(make_check("gep_capsules_created", False, f"Exception parsing capsules.json: {e}"))

# ─────────────────────────────────────────────
# CHECK 6: assets/gep/events.jsonl — append-only, tree structure with parent_id linking
# Must have at least 3 NEW valid events (beyond the corrupt placeholder)
# Each subsequent event must reference a parent_id that matches a prior event's id
# ─────────────────────────────────────────────
try:
    events_path = ws / "assets" / "gep" / "events.jsonl"
    if not events_path.exists():
        checks.append(make_check("gep_events_tree_structure", False, "assets/gep/events.jsonl not found"))
    else:
        lines = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
        valid_events = []
        for line in lines:
            try:
                obj = json.loads(line)
                # A "real" event needs at minimum an 'id' field
                if isinstance(obj, dict) and 'id' in obj:
                    valid_events.append(obj)
            except:
                pass
        
        if len(valid_events) < 3:
            checks.append(make_check("gep_events_tree_structure", False, 
                f"Only {len(valid_events)} valid event(s) with 'id' field found; need at least 3"))
        else:
            # Verify parent_id chain: at least one event after the first must have parent_id = prior event's id
            ids_seen = set()
            chain_valid = False
            root_count = 0
            for ev in valid_events:
                ev_id = ev.get('id')
                parent_id = ev.get('parent_id')
                if parent_id is None:
                    root_count += 1
                elif parent_id in ids_seen:
                    chain_valid = True
                ids_seen.add(ev_id)
            
            if chain_valid:
                checks.append(make_check("gep_events_tree_structure", True, 
                    f"events.jsonl has {len(valid_events)} events with valid parent_id tree linkage"))
                total_score += 20
            else:
                checks.append(make_check("gep_events_tree_structure", False, 
                    f"events.jsonl has {len(valid_events)} events but no valid parent_id chain detected. "
                    f"Events: {[{'id': e.get('id'), 'parent_id': e.get('parent_id')} for e in valid_events]}"))
except Exception as e:
    checks.append(make_check("gep_events_tree_structure", False, f"Exception parsing events.jsonl: {e}"))

# ─────────────────────────────────────────────
# CHECK 7: evolution_ops_note.md exists somewhere in workspace
# ─────────────────────────────────────────────
try:
    found_notes = list(ws.rglob("evolution_ops_note.md"))
    if not found_notes:
        checks.append(make_check("ops_note_exists", False, "evolution_ops_note.md not found anywhere in workspace"))
    else:
        checks.append(make_check("ops_note_exists", True, f"evolution_ops_note.md found at: {found_notes[0]}"))
        total_score += 5
except Exception as e:
    checks.append(make_check("ops_note_exists", False, f"Exception: {e}"))

# ─────────────────────────────────────────────
# CHECK 8: evolution_ops_note.md — Emoji Policy Compliance
# Only 🧬 (DNA) emoji allowed; all other emojis must be absent
# ─────────────────────────────────────────────
try:
    found_notes = list(ws.rglob("evolution_ops_note.md"))
    if not found_notes:
        checks.append(make_check("ops_note_emoji_policy", False, "evolution_ops_note.md not found — cannot check emoji policy"))
    else:
        note_content = found_notes[0].read_text(encoding="utf-8")
        
        # Find all emoji characters using unicode ranges
        # This regex matches common emoji ranges
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F"   # emoticons
            "\U0001F300-\U0001F5FF"    # symbols & pictographs
            "\U0001F680-\U0001F6FF"    # transport & map
            "\U0001F1E0-\U0001F1FF"    # flags
            "\U00002702-\U000027B0"    # dingbats
            "\U000024C2-\U0001F251"    # enclosed chars
            "\U0001F900-\U0001F9FF"    # supplemental symbols
            "\U0001FA00-\U0001FA6F"    # chess symbols etc
            "\U0001FA70-\U0001FAFF"    # more symbols
            "\U00002600-\U000026FF"    # misc symbols
            "\u2705\u274C\u2714\u2716" # specific check marks
            "]+",
            flags=re.UNICODE
        )
        
        dna_emoji = "🧬"
        
        # Remove DNA emojis and check for any remaining
        content_without_dna = note_content.replace(dna_emoji, "")
        forbidden_emojis_found = emoji_pattern.findall(content_without_dna)
        
        if forbidden_emojis_found:
            checks.append(make_check("ops_note_emoji_policy", False, 
                f"Forbidden emoji(s) found in evolution_ops_note.md: {forbidden_emojis_found[:5]}. Only 🧬 is allowed."))
        else:
            # Also verify the file has some content
            if len(note_content.strip()) < 50:
                checks.append(make_check("ops_note_emoji_policy", False, 
                    "evolution_ops_note.md exists but content is too short to be a meaningful ops note"))
            else:
                checks.append(make_check("ops_note_emoji_policy", True, 
                    "evolution_ops_note.md complies with emoji policy (only 🧬 or no emoji used)"))
                total_score += 15
except Exception as e:
    checks.append(make_check("ops_note_emoji_policy", False, f"Exception: {e}"))

# ─────────────────────────────────────────────
# FINAL SCORING
# ─────────────────────────────────────────────
max_score = 100.0
normalized_score = total_score / max_score
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": round(normalized_score, 3),
    "checks": checks
}

print(json.dumps(result, indent=2, ensure_ascii=False))