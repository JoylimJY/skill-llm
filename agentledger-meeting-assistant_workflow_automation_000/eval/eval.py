import sys
import json
import re
from pathlib import Path

def run_checks(workspace_dir: str):
    ws = Path(workspace_dir)
    checks = []

    # ── Helper ──────────────────────────────────────────────────────────────
    def read(p: Path):
        try:
            return p.read_text(encoding="utf-8")
        except Exception as e:
            return None

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 1: Pre-Meeting Brief for Paxo Financial Discovery Call
    # Expected: a discovery brief file somewhere under meetings/
    # Must contain BANT section, Discovery Objectives, Qualification Signal
    # ════════════════════════════════════════════════════════════════════════

    # Find candidate brief file(s): any .md file under meetings/ whose name
    # contains "paxo" or "discovery" or "brief"
    brief_candidates = list(ws.rglob("*.md"))
    brief_file = None
    brief_text = None
    for f in brief_candidates:
        rel = str(f.relative_to(ws)).lower()
        txt = read(f)
        if txt and ("paxo" in rel or "discovery" in rel or "brief" in rel or
                    ("paxo" in txt.lower() and "brief" in txt.lower())):
            if "bant" in txt.lower() or "budget" in txt.lower():
                brief_file = f
                brief_text = txt
                break

    # Fallback: search any md file under meetings/ for BANT
    if brief_file is None:
        for f in (ws / "meetings").rglob("*.md"):
            txt = read(f)
            if txt and ("budget" in txt.lower() and "authority" in txt.lower()):
                brief_file = f
                brief_text = txt
                break

    c1_found = brief_file is not None
    checks.append({
        "name": "brief_file_exists",
        "passed": c1_found,
        "detail": f"Discovery brief file found at: {brief_file}" if c1_found else "No discovery brief file found under meetings/"
    })

    bant_ok = False
    if brief_text:
        has_budget = bool(re.search(r'\bbudget\b', brief_text, re.IGNORECASE))
        has_authority = bool(re.search(r'\bauthority\b', brief_text, re.IGNORECASE))
        has_need = bool(re.search(r'\bneed\b', brief_text, re.IGNORECASE))
        has_timeline = bool(re.search(r'\btimeline\b', brief_text, re.IGNORECASE))
        bant_ok = has_budget and has_authority and has_need and has_timeline
        checks.append({
            "name": "brief_bant_section",
            "passed": bant_ok,
            "detail": f"BANT fields — Budget:{has_budget}, Authority:{has_authority}, Need:{has_need}, Timeline:{has_timeline}"
        })
    else:
        checks.append({
            "name": "brief_bant_section",
            "passed": False,
            "detail": "Brief text not available; cannot check BANT"
        })

    discovery_objectives_ok = False
    if brief_text:
        discovery_objectives_ok = bool(re.search(r'discovery\s+objectives?', brief_text, re.IGNORECASE))
        checks.append({
            "name": "brief_discovery_objectives",
            "passed": discovery_objectives_ok,
            "detail": "Discovery Objectives section present" if discovery_objectives_ok else "Missing 'Discovery Objectives' section"
        })
    else:
        checks.append({
            "name": "brief_discovery_objectives",
            "passed": False,
            "detail": "Brief text not available"
        })

    qualification_ok = False
    if brief_text:
        qualification_ok = bool(re.search(r'qualification', brief_text, re.IGNORECASE))
        checks.append({
            "name": "brief_qualification_signal",
            "passed": qualification_ok,
            "detail": "Qualification Signal section present" if qualification_ok else "Missing Qualification Signal section"
        })
    else:
        checks.append({
            "name": "brief_qualification_signal",
            "passed": False,
            "detail": "Brief text not available"
        })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 2: Meeting Notes File — correct location and naming
    # Expected: meetings/YYYY-MM/YYYY-MM-DD-[slug-with-paxo-or-discovery].md
    # ════════════════════════════════════════════════════════════════════════

    notes_file = None
    notes_text = None
    date_pattern = re.compile(r'^\d{4}-\d{2}$')

    for subdir in (ws / "meetings").iterdir():
        if subdir.is_dir() and date_pattern.match(subdir.name):
            for f in subdir.glob("*.md"):
                txt = read(f)
                if txt and ("paxo" in f.name.lower() or "discovery" in f.name.lower()):
                    notes_file = f
                    notes_text = txt
                    break
            if notes_file:
                break

    # Also accept brief+notes combined in same file IF it has Key Decisions section
    if notes_file is None:
        for subdir in (ws / "meetings").iterdir():
            if subdir.is_dir() and date_pattern.match(subdir.name):
                for f in subdir.glob("*.md"):
                    txt = read(f)
                    if txt and ("key decision" in txt.lower() or "action items" in txt.lower()):
                        if "paxo" in txt.lower() or "discovery" in txt.lower():
                            notes_file = f
                            notes_text = txt
                            break

    naming_ok = False
    if notes_file:
        # Check file is in meetings/YYYY-MM/ folder
        parent = notes_file.parent
        naming_ok = (
            parent.parent == ws / "meetings"
            and date_pattern.match(parent.name)
            and re.match(r'^\d{4}-\d{2}-\d{2}-', notes_file.name)
        )
    checks.append({
        "name": "notes_file_correct_location_and_naming",
        "passed": naming_ok,
        "detail": f"Notes file: {notes_file} — naming/location {'OK' if naming_ok else 'WRONG'}" if notes_file else "No meeting notes file found in meetings/YYYY-MM/ subdirectory"
    })

    # Notes must have key decisions and action items table
    notes_has_decisions = False
    notes_has_actions_table = False
    if notes_text:
        notes_has_decisions = bool(re.search(r'key\s+decisions?', notes_text, re.IGNORECASE))
        # Action items table: must have the 5-column header # | Action | Owner | Due | Priority
        notes_has_actions_table = bool(re.search(
            r'\|\s*#\s*\|.*action.*\|.*owner.*\|.*due.*\|.*priority', notes_text, re.IGNORECASE
        ))
    checks.append({
        "name": "notes_has_key_decisions",
        "passed": notes_has_decisions,
        "detail": "Key Decisions section present in notes" if notes_has_decisions else "Missing Key Decisions section in notes"
    })
    checks.append({
        "name": "notes_has_action_items_table",
        "passed": notes_has_actions_table,
        "detail": "Action items table with # | Action | Owner | Due | Priority found" if notes_has_actions_table else "Action items table missing or incorrectly formatted"
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 3: meeting-log.md updated with new entry
    # ════════════════════════════════════════════════════════════════════════
    log_path = ws / "meetings" / "meeting-log.md"
    log_text = read(log_path)
    log_updated = False
    log_has_correct_cols = False
    if log_text:
        # Must still have the header with all 5 columns
        log_has_correct_cols = bool(re.search(
            r'\|\s*Date\s*\|.*Meeting.*\|.*Type.*\|.*Key\s+Decision.*\|.*File\s*\|',
            log_text, re.IGNORECASE
        ))
        # Must contain a new row referencing paxo or discovery
        log_updated = bool(re.search(r'paxo|discovery', log_text, re.IGNORECASE)) and \
                      len([l for l in log_text.splitlines() if l.strip().startswith('|') and '---' not in l]) >= 3
    checks.append({
        "name": "meeting_log_has_correct_columns",
        "passed": log_has_correct_cols,
        "detail": "meeting-log.md has Date|Meeting|Type|Key Decision|File columns" if log_has_correct_cols else "meeting-log.md missing or has wrong column headers"
    })
    checks.append({
        "name": "meeting_log_updated_with_new_entry",
        "passed": log_updated,
        "detail": "New Paxo/discovery entry found in meeting-log.md" if log_updated else "meeting-log.md not updated with new meeting entry"
    })

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 4: open-actions.md updated — correct schema + old row preserved
    # ════════════════════════════════════════════════════════════════════════
    actions_path = ws / "meetings" / "open-actions.md"
    actions_text = read(actions_path)

    actions_correct_schema = False
    actions_old_row_preserved = False
    actions_new_rows_added = False
    actions_meeting_column_populated = False

    if actions_text:
        # Schema check: # | Action | Owner | Due | Meeting | Status
        actions_correct_schema = bool(re.search(
            r'\|\s*#\s*\|.*Action.*\|.*Owner.*\|.*Due.*\|.*Meeting.*\|.*Status\s*\|',
            actions_text, re.IGNORECASE
        ))
        # Old row must still be present (revised invoice row)
        actions_old_row_preserved = "Send revised invoice" in actions_text
        # New rows: at least one row referencing paxo, discovery, or dana
        data_rows = [l for l in actions_text.splitlines()
                     if l.strip().startswith('|') and '---' not in l and
                     not re.search(r'#\s*\|.*action', l, re.IGNORECASE)]
        actions_new_rows_added = any(
            re.search(r'paxo|discovery|dana|paxo', row, re.IGNORECASE)
            for row in data_rows
        )
        # Meeting column should reference a .md file (link to source meeting)
        actions_meeting_column_populated = bool(re.search(
            r'\d{4}-\d{2}-\d{2}-.*\.md', actions_text
        ))

    checks.append({
        "name": "open_actions_correct_schema",
        "passed": actions_correct_schema,
        "detail": "open-actions.md has # | Action | Owner | Due | Meeting | Status columns" if actions_correct_schema else "open-actions.md missing Meeting column or wrong schema"
    })
    checks.append({
        "name": "open_actions_old_row_preserved",
        "passed": actions_old_row_preserved,
        "detail": "Pre-existing 'Send revised invoice' row preserved" if actions_old_row_preserved else "Pre-existing row was deleted — should have been preserved"
    })
    checks.append({
        "name": "open_actions_new_rows_added",
        "passed": actions_new_rows_added,
        "detail": "New action items from Paxo discovery call added" if actions_new_rows_added else "No new Paxo/discovery action items found in open-actions.md"
    })
    checks.append({
        "name": "open_actions_meeting_column_has_filename",
        "passed": actions_meeting_column_populated,
        "detail": "Meeting column references source .md filename" if actions_meeting_column_populated else "Meeting column does not link back to source meeting file"
    })

    # ════════════════════════════════════════════════════════════════════════
    # SCORING
    # ════════════════════════════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall = passed_count >= 10  # must pass at least 10 of 13 checks

    return {
        "passed": overall,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "No workspace path provided"}))
        sys.exit(1)
    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))