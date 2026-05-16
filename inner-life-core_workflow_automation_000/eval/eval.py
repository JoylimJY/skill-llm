#!/usr/bin/env python3
"""
Evaluates whether the agent correctly bootstrapped the inner-life-core system.

Checks:
1. memory/inner-state.json has all 6 documented emotions with correct decay schema
2. memory/drive.json has required fields (seeking, anticipating)
3. At least one memory/daily-notes/*.md contains ALL 3 signal tag types
4. memory/habits.json exists and is valid JSON
5. memory/relationship.json has trust field (correct schema)
6. A file named inner-life-score.txt exists (agent ran score.sh)
7. At least one synapse tag is present somewhere in daily-notes
"""

import sys
import json
import re
from pathlib import Path

def load_json(path):
    return json.loads(Path(path).read_text())

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Check 1: inner-state.json has all 6 emotions ──────────────────────────
    REQUIRED_EMOTIONS = {"connection", "confidence", "curiosity", "boredom", "frustration", "impatience"}
    check1_name = "inner-state.json has all 6 documented emotions"
    try:
        state = load_json(ws / "memory/inner-state.json")
        # Accept either top-level keys or nested under 'emotions'
        emotions_node = state.get("emotions", state)
        found_emotions = set(emotions_node.keys()) if isinstance(emotions_node, dict) else set()
        missing = REQUIRED_EMOTIONS - found_emotions
        if not missing:
            checks.append({"name": check1_name, "passed": True,
                            "detail": f"All 6 emotions present: {sorted(found_emotions & REQUIRED_EMOTIONS)}"})
            total_score += 2.0
        else:
            checks.append({"name": check1_name, "passed": False,
                            "detail": f"Missing emotions: {sorted(missing)}. Found keys: {sorted(found_emotions)}"})
    except Exception as e:
        checks.append({"name": check1_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 2: Each emotion node has decay-related fields ───────────────────
    DECAY_KEYWORDS = {"decay", "half_life", "decay_rate", "delta", "rate", "per_6h", "recovery"}
    check2_name = "Emotion entries contain decay schema fields"
    try:
        state = load_json(ws / "memory/inner-state.json")
        emotions_node = state.get("emotions", state)
        emotions_with_decay = []
        for emo in REQUIRED_EMOTIONS:
            if emo not in emotions_node:
                continue
            entry = emotions_node[emo]
            if not isinstance(entry, dict):
                continue
            keys_lower = {k.lower() for k in entry.keys()}
            # check if any decay keyword overlaps OR the entry has a 'value' field (correct schema base)
            has_value = "value" in keys_lower
            has_decay = bool(keys_lower & DECAY_KEYWORDS)
            if has_value or has_decay:
                emotions_with_decay.append(emo)
        if len(emotions_with_decay) >= 4:
            checks.append({"name": check2_name, "passed": True,
                            "detail": f"{len(emotions_with_decay)}/6 emotion entries have decay-related schema fields."})
            total_score += 1.5
        else:
            checks.append({"name": check2_name, "passed": False,
                            "detail": f"Only {len(emotions_with_decay)}/6 emotions have proper schema. "
                                       f"Each should have at least 'value' and decay info."})
    except Exception as e:
        checks.append({"name": check2_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 3: drive.json has 'seeking' and 'anticipating' fields ───────────
    check3_name = "drive.json contains 'seeking' and 'anticipating' fields"
    try:
        drive = load_json(ws / "memory/drive.json")
        has_seeking = "seeking" in drive
        has_anticipating = "anticipating" in drive
        if has_seeking and has_anticipating:
            checks.append({"name": check3_name, "passed": True,
                            "detail": f"seeking={drive['seeking']!r}, anticipating={drive['anticipating']!r}"})
            total_score += 1.5
        else:
            missing_fields = [f for f, p in [("seeking", has_seeking), ("anticipating", has_anticipating)] if not p]
            checks.append({"name": check3_name, "passed": False,
                            "detail": f"Missing fields: {missing_fields}. Keys found: {list(drive.keys())}"})
    except Exception as e:
        checks.append({"name": check3_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 4: A daily note contains all 3 signal tag types ─────────────────
    check4_name = "A daily-notes file contains all 3 signal tag types"
    SIGNAL_PATTERNS = {
        "dream-topic":    re.compile(r"<!--\s*dream-topic\s*:\s*.+?-->", re.IGNORECASE),
        "handoff":        re.compile(r"<!--\s*handoff\s*:\s*.+?-->", re.IGNORECASE),
        "seeking-spark":  re.compile(r"<!--\s*seeking-spark\s*:\s*.+?-->", re.IGNORECASE),
    }
    try:
        notes_dir = ws / "memory/daily-notes"
        note_files = list(notes_dir.glob("*.md"))
        found_all = False
        best_found = set()
        for nf in note_files:
            content = nf.read_text()
            found_here = {tag for tag, pat in SIGNAL_PATTERNS.items() if pat.search(content)}
            if len(found_here) > len(best_found):
                best_found = found_here
            if len(found_here) == 3:
                found_all = True
                break
        if found_all:
            checks.append({"name": check4_name, "passed": True,
                            "detail": "Found dream-topic, handoff, and seeking-spark signal tags."})
            total_score += 2.0
        else:
            checks.append({"name": check4_name, "passed": False,
                            "detail": f"Best coverage: {sorted(best_found)}/3 signal types. "
                                       f"Need: dream-topic, handoff, seeking-spark."})
    except Exception as e:
        checks.append({"name": check4_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 5: A daily note contains at least one synapse tag ───────────────
    check5_name = "A daily-notes file contains at least one synapse tag"
    SYNAPSE_PATTERN = re.compile(
        r"<!--\s*(contradicts|caused-by|updates)\s*:\s*.+?-->", re.IGNORECASE
    )
    try:
        notes_dir = ws / "memory/daily-notes"
        note_files = list(notes_dir.glob("*.md"))
        synapse_found = False
        for nf in note_files:
            content = nf.read_text()
            if SYNAPSE_PATTERN.search(content):
                synapse_found = True
                break
        if synapse_found:
            checks.append({"name": check5_name, "passed": True,
                            "detail": "Found at least one synapse tag (contradicts/caused-by/updates)."})
            total_score += 1.0
        else:
            checks.append({"name": check5_name, "passed": False,
                            "detail": "No synapse tags found in any daily-notes file. "
                                       "Expected <!-- contradicts: ref -->, <!-- caused-by: ref -->, or <!-- updates: ref -->."})
    except Exception as e:
        checks.append({"name": check5_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 6: memory/habits.json exists and is valid JSON ──────────────────
    check6_name = "memory/habits.json exists and is valid JSON"
    try:
        habits = load_json(ws / "memory/habits.json")
        checks.append({"name": check6_name, "passed": True,
                        "detail": f"habits.json parsed successfully. Keys: {list(habits.keys()) if isinstance(habits, dict) else type(habits).__name__}"})
        total_score += 0.75
    except Exception as e:
        checks.append({"name": check6_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 7: memory/relationship.json has 'trust' field ───────────────────
    check7_name = "memory/relationship.json has correct schema with 'trust' field"
    try:
        rel = load_json(ws / "memory/relationship.json")
        if "trust" in rel:
            checks.append({"name": check7_name, "passed": True,
                            "detail": f"trust={rel['trust']!r}"})
            total_score += 0.75
        else:
            checks.append({"name": check7_name, "passed": False,
                            "detail": f"No 'trust' field. Found keys: {list(rel.keys())}"})
    except Exception as e:
        checks.append({"name": check7_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 8: inner-life-score.txt exists (agent ran score.sh) ─────────────
    check8_name = "inner-life-score.txt exists (score.sh was executed)"
    try:
        score_files = list(ws.rglob("inner-life-score.txt"))
        if score_files:
            content = score_files[0].read_text().strip()
            checks.append({"name": check8_name, "passed": True,
                            "detail": f"Found at {score_files[0].relative_to(ws)}. Content preview: {content[:120]!r}"})
            total_score += 0.5
        else:
            checks.append({"name": check8_name, "passed": False,
                            "detail": "No inner-life-score.txt found anywhere in workspace."})
    except Exception as e:
        checks.append({"name": check8_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Check 9: boredom emotion uses counter/day model (not float decay) ─────
    check9_name = "boredom emotion uses day-counter model (not simple float decay)"
    try:
        state = load_json(ws / "memory/inner-state.json")
        emotions_node = state.get("emotions", state)
        boredom = emotions_node.get("boredom", {})
        if not isinstance(boredom, dict):
            raise ValueError("boredom is not a dict")
        keys_lower = {k.lower() for k in boredom.keys()}
        # boredom should NOT have the same decay pattern as connection/curiosity
        # it should have 'counter', 'days', 'day_count', or similar counter field
        COUNTER_KEYS = {"counter", "days", "day_count", "count", "streak"}
        has_counter = bool(keys_lower & COUNTER_KEYS)
        # Also acceptable: a 'reset_on_novelty' flag or 'novelty' key
        has_novelty = bool(keys_lower & {"novelty", "reset_on_novelty", "reset"})
        if has_counter or has_novelty:
            checks.append({"name": check9_name, "passed": True,
                            "detail": f"boredom uses counter model. Keys: {sorted(boredom.keys())}"})
            total_score += 1.0
        else:
            checks.append({"name": check9_name, "passed": False,
                            "detail": f"boredom entry doesn't reflect day-counter model. "
                                       f"Keys found: {sorted(boredom.keys())}. "
                                       f"Expected fields like 'counter'/'days' and 'reset_on_novelty'."})
    except Exception as e:
        checks.append({"name": check9_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Compute final pass/fail ────────────────────────────────────────────────
    MAX_SCORE = 11.0
    normalized = round(total_score / MAX_SCORE, 4)
    # Must pass checks 1, 3, 4 (the core proprietary ones) to overall pass
    core_checks_passed = all(
        c["passed"] for c in checks
        if c["name"] in {
            check1_name,
            check3_name,
            check4_name,
        }
    )
    passed = core_checks_passed and normalized >= 0.55

    return {
        "passed": passed,
        "score": normalized,
        "checks": checks,
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))