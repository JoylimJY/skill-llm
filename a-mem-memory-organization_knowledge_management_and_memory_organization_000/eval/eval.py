#!/usr/bin/env python3
"""
Evaluation script for A-MEM memory organization task.
Tests: note schema completeness, timestamp format, category validity,
keyword/tag counts, linking logic, and conservative evolution (superseded marking).
"""
import sys
import json
import re
from pathlib import Path

def main():
    workspace = Path(sys.argv[1])
    checks = []
    total_score = 0.0

    # --- 1. Find memory/notes.json ---
    notes_path = workspace / "memory" / "notes.json"
    
    # Also search recursively as fallback
    if not notes_path.exists():
        candidates = list(workspace.rglob("notes.json"))
        if candidates:
            notes_path = candidates[0]

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # Check 1: File exists at correct location
    correct_path = (workspace / "memory" / "notes.json").exists()
    score = add_check(
        "file_location_correct",
        correct_path,
        f"Expected memory/notes.json at {workspace}/memory/notes.json. Found: {correct_path}",
        weight=0.5
    )
    total_score += score

    if not notes_path.exists():
        checks.append({"name": "file_parseable", "passed": False, "detail": "notes.json not found anywhere in workspace."})
        print(json.dumps({
            "passed": False,
            "score": round(total_score / 15.0, 3),
            "checks": checks
        }))
        return

    # Check 2: Valid JSON with "notes" wrapper
    try:
        data = json.loads(notes_path.read_text())
        has_notes_key = isinstance(data, dict) and "notes" in data and isinstance(data["notes"], list)
        score = add_check(
            "json_structure_valid",
            has_notes_key,
            f"Top-level key 'notes' present: {has_notes_key}. Keys found: {list(data.keys()) if isinstance(data, dict) else 'N/A'}",
            weight=1.0
        )
        total_score += score
        notes = data.get("notes", []) if isinstance(data, dict) else []
    except Exception as e:
        add_check("file_parseable", False, f"JSON parse error: {e}", weight=1.0)
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # Check 3: Minimum note count (at least 7 — one per distinct observation, OBS-4 supersedes OBS-1)
    note_count = len(notes)
    score = add_check(
        "minimum_note_count",
        note_count >= 7,
        f"Found {note_count} notes. Expected at least 7 (one per distinct observation).",
        weight=1.0
    )
    total_score += score

    # Check 4: All required fields present in every note
    REQUIRED_FIELDS = {"id", "content", "context", "keywords", "tags", "category", "timestamp", "links"}
    notes_missing_fields = []
    for i, note in enumerate(notes):
        missing = REQUIRED_FIELDS - set(note.keys())
        if missing:
            notes_missing_fields.append(f"note[{i}] (id={note.get('id','?')}) missing: {missing}")
    
    score = add_check(
        "all_required_fields_present",
        len(notes_missing_fields) == 0,
        f"Field coverage OK" if not notes_missing_fields else f"Missing fields: {notes_missing_fields[:3]}",
        weight=1.5
    )
    total_score += score

    # Check 5: Timestamp format is YYYYMMDDHHmm (exactly 12 digits, no separators)
    timestamp_re = re.compile(r'^\d{12}$')
    bad_timestamps = []
    for note in notes:
        ts = str(note.get("timestamp", ""))
        if not timestamp_re.match(ts):
            bad_timestamps.append(f"id={note.get('id','?')} ts='{ts}'")
    
    score = add_check(
        "timestamp_format_YYYYMMDDHHmm",
        len(bad_timestamps) == 0,
        f"All timestamps valid" if not bad_timestamps else f"Bad timestamps: {bad_timestamps[:3]}",
        weight=1.5
    )
    total_score += score

    # Check 6: Category must be one of the allowed values
    VALID_CATEGORIES = {"Preference", "Project", "Decision", "Fact", "Workflow", "Bug", "Research"}
    bad_cats = []
    for note in notes:
        cat = note.get("category", "")
        if cat not in VALID_CATEGORIES:
            bad_cats.append(f"id={note.get('id','?')} category='{cat}'")
    
    score = add_check(
        "category_from_allowed_set",
        len(bad_cats) == 0,
        f"All categories valid" if not bad_cats else f"Invalid categories: {bad_cats[:3]}",
        weight=1.5
    )
    total_score += score

    # Check 7: keywords is a list with 3-6 items per note
    bad_keywords = []
    for note in notes:
        kws = note.get("keywords", [])
        if not isinstance(kws, list) or not (3 <= len(kws) <= 6):
            bad_keywords.append(f"id={note.get('id','?')} keywords_count={len(kws) if isinstance(kws, list) else 'not-list'}")
    
    score = add_check(
        "keywords_count_3_to_6",
        len(bad_keywords) == 0,
        f"All notes have 3-6 keywords" if not bad_keywords else f"Bad keyword counts: {bad_keywords[:3]}",
        weight=1.0
    )
    total_score += score

    # Check 8: tags is a list with 2-5 items per note
    bad_tags = []
    for note in notes:
        tgs = note.get("tags", [])
        if not isinstance(tgs, list) or not (2 <= len(tgs) <= 5):
            bad_tags.append(f"id={note.get('id','?')} tags_count={len(tgs) if isinstance(tgs, list) else 'not-list'}")
    
    score = add_check(
        "tags_count_2_to_5",
        len(bad_tags) == 0,
        f"All notes have 2-5 tags" if not bad_tags else f"Bad tag counts: {bad_tags[:3]}",
        weight=1.0
    )
    total_score += score

    # Check 9: Links are valid (each link ID references an existing note ID)
    all_ids = {note.get("id") for note in notes}
    broken_links = []
    for note in notes:
        for link in note.get("links", []):
            if link not in all_ids:
                broken_links.append(f"note id={note.get('id','?')} links to unknown id='{link}'")
    
    score = add_check(
        "links_reference_existing_notes",
        len(broken_links) == 0,
        f"All links valid" if not broken_links else f"Broken links: {broken_links[:3]}",
        weight=1.0
    )
    total_score += score

    # Check 10: OBS-7 and OBS-2 are linked (both are HAL-layer bugs — the raw log explicitly says so)
    # Find notes that seem to correspond to OBS-2 (CAN bus bug / FW-449) and OBS-7 (encoder overflow)
    def note_matches(note, terms):
        combined = " ".join([
            str(note.get("content", "")),
            str(note.get("context", "")),
            " ".join(note.get("keywords", [])),
            " ".join(note.get("tags", []))
        ]).lower()
        return all(t.lower() in combined for t in terms)

    obs2_candidates = [n for n in notes if note_matches(n, ["can"]) and note_matches(n, ["bug", "drop", "frame", "fw-449", "silent"])]
    obs7_candidates = [n for n in notes if note_matches(n, ["encoder"]) and note_matches(n, ["overflow", "rollover", "wrap"])]
    
    linked_pair = False
    if obs2_candidates and obs7_candidates:
        obs2_ids = {n["id"] for n in obs2_candidates}
        obs7_ids = {n["id"] for n in obs7_candidates}
        for n in obs2_candidates:
            if any(lid in obs7_ids for lid in n.get("links", [])):
                linked_pair = True
                break
        if not linked_pair:
            for n in obs7_candidates:
                if any(lid in obs2_ids for lid in n.get("links", [])):
                    linked_pair = True
                    break
    
    score = add_check(
        "hal_bugs_linked_obs2_obs7",
        linked_pair,
        f"CAN bus bug note and encoder overflow note are linked: {linked_pair}. OBS2 candidates: {[n['id'] for n in obs2_candidates]}, OBS7 candidates: {[n['id'] for n in obs7_candidates]}",
        weight=1.5
    )
    total_score += score

    # Check 11: Conservative evolution — OBS-1 (ring buffer) must be marked as superseded/obsolete
    # because OBS-4 explicitly replaces it.
    obs1_candidates = [n for n in notes if note_matches(n, ["ring buffer"]) or
                       (note_matches(n, ["ipc"]) and note_matches(n, ["planner", "hal"]))]
    
    # Check if any obs1 note has an "obsolete" marker — could be in content, a field, tags, or context
    obs1_superseded = False
    for note in obs1_candidates:
        note_str = json.dumps(note).lower()
        if any(word in note_str for word in ["superseded", "obsolete", "deprecated", "replaced", "outdated"]):
            obs1_superseded = True
            break
    
    # Also acceptable: obs1 note has a link to obs4 note (spsc queue note)
    obs4_candidates = [n for n in notes if note_matches(n, ["spsc"]) or 
                       (note_matches(n, ["readerwriterqueue"]) or note_matches(n, ["lock-free"]))]
    if not obs1_superseded and obs1_candidates and obs4_candidates:
        obs4_ids = {n["id"] for n in obs4_candidates}
        for note in obs1_candidates:
            if any(lid in obs4_ids for lid in note.get("links", [])):
                obs1_superseded = True  # linking to superseding note is also acceptable
                break

    score = add_check(
        "obs1_ring_buffer_marked_superseded",
        obs1_superseded,
        f"Ring buffer / OBS-1 note marked as superseded or linked to SPSC replacement: {obs1_superseded}. OBS1 candidates: {[n['id'] for n in obs1_candidates]}",
        weight=2.0
    )
    total_score += score

    # Check 12: OBS-4 (SPSC queue) note exists and references IPC/planner/HAL context
    spsc_exists = len(obs4_candidates) > 0
    score = add_check(
        "spsc_queue_note_exists",
        spsc_exists,
        f"SPSC/lock-free queue replacement note exists: {spsc_exists}.",
        weight=1.0
    )
    total_score += score

    # Check 13: content field is non-trivially filled (not just a copy of raw log line)
    # Each note's content should be a processed atomic fact, not just the raw header like "--- OBS-1 ---"
    trivial_contents = []
    for note in notes:
        content = str(note.get("content", ""))
        if re.match(r'^---\s*OBS-\d+\s*---$', content.strip()):
            trivial_contents.append(note.get("id", "?"))
        if len(content.strip()) < 20:
            trivial_contents.append(note.get("id", "?"))
    
    score = add_check(
        "content_fields_non_trivial",
        len(trivial_contents) == 0,
        f"All content fields are non-trivial atomic facts" if not trivial_contents else f"Trivial content in notes: {trivial_contents[:3]}",
        weight=1.0
    )
    total_score += score

    # Final score: normalize to 0-1
    max_score = 0.5 + 1.0 + 1.0 + 1.5 + 1.5 + 1.5 + 1.0 + 1.0 + 1.0 + 1.5 + 2.0 + 1.0 + 1.0  # = 16.0
    normalized = round(total_score / max_score, 3)
    passed = normalized >= 0.75 and all(
        c["passed"] for c in checks if c["name"] in [
            "file_parseable", "json_structure_valid", "all_required_fields_present",
            "timestamp_format_YYYYMMDDHHmm", "category_from_allowed_set"
        ]
    )

    print(json.dumps({
        "passed": passed,
        "score": normalized,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()