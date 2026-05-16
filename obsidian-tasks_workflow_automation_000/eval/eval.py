#!/usr/bin/env python3
"""
Evaluation script for the obsidian-tasks pharma vault task.
Usage: python3 eval_script.py <workspace_dir>
"""

import sys
import json
import re
from pathlib import Path

def load_file(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def parse_frontmatter(content: str):
    """Extract YAML frontmatter as a dict (simple key:value parser)."""
    if not content:
        return {}
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).splitlines():
        if ':' in line:
            k, _, v = line.partition(':')
            fm[k.strip()] = v.strip()
    return fm

def find_board(vault: Path):
    """Find Board.md inside the Pipeline folder."""
    candidates = list(vault.rglob("Board.md"))
    return candidates[0] if candidates else None

def find_dashboard(vault: Path):
    candidates = list(vault.rglob("Dashboard.md"))
    return candidates[0] if candidates else None

def find_task_note(vault: Path, name: str):
    """Find a task note by filename stem (case-insensitive)."""
    for f in vault.rglob("*.md"):
        if f.stem.lower() == name.lower():
            return f
    return None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    vault = workspace / "PharmaVault"
    checks = []

    # ── CHECK 1: Pipeline folder exists ──────────────────────────────────────
    pipeline_dir = vault / "Pipeline"
    c1_passed = pipeline_dir.is_dir()
    checks.append(check(
        "Pipeline folder created",
        c1_passed,
        f"{'Found' if c1_passed else 'Missing'}: {pipeline_dir}"
    ))

    # ── CHECK 2: Board.md exists in Pipeline folder ───────────────────────────
    board_path = pipeline_dir / "Board.md"
    board_content = load_file(board_path)
    c2_passed = board_content is not None
    checks.append(check(
        "Board.md exists in Pipeline/",
        c2_passed,
        f"{'Found' if c2_passed else 'Missing'}: {board_path}"
    ))

    # ── CHECK 3: Board.md has all 5 correct column headers ────────────────────
    required_cols = ["Backlog", "Todo", "In Progress", "Review", "Done"]
    if board_content:
        found_cols = [col for col in required_cols if f"## {col}" in board_content]
        c3_passed = len(found_cols) == 5
        checks.append(check(
            "Board.md has all 5 custom columns",
            c3_passed,
            f"Found columns: {found_cols}"
        ))
    else:
        checks.append(check("Board.md has all 5 custom columns", False, "Board.md not found"))

    # ── CHECK 4: Dashboard.md exists ─────────────────────────────────────────
    dash_path = pipeline_dir / "Dashboard.md"
    dash_content = load_file(dash_path)
    c4_passed = dash_content is not None
    checks.append(check(
        "Dashboard.md exists in Pipeline/",
        c4_passed,
        f"{'Found' if c4_passed else 'Missing'}: {dash_path}"
    ))

    # ── CHECK 5: Task notes exist (all 4 tasks) ───────────────────────────────
    task_names = [
        "Synthesize-X47-Batch2",
        "Toxicology-Report-Review",
        "IND-Application-Draft",
        "Competitor-IP-Landscape",
    ]
    found_notes = {}
    for t in task_names:
        note = find_task_note(vault, t)
        found_notes[t] = note

    all_found = all(v is not None for v in found_notes.values())
    checks.append(check(
        "All 4 task notes created",
        all_found,
        f"Found: {[k for k,v in found_notes.items() if v]} | Missing: {[k for k,v in found_notes.items() if not v]}"
    ))

    # ── CHECK 6: Frontmatter correctness for all 4 tasks ─────────────────────
    expected_fm = {
        "Synthesize-X47-Batch2": {
            "status": "todo",           # moved back from in-progress
            "priority": "P1",
            "category": "research",
            "due": "2026-02-20",
        },
        "Toxicology-Report-Review": {
            "status": "done",           # moved to done
            "priority": "P2",
            "category": "research",
            "due": "2026-02-28",
        },
        "IND-Application-Draft": {
            "status": "backlog",
            "priority": "P1",
            "category": "revenue",
            "due": "2026-03-01",
        },
        "Competitor-IP-Landscape": {
            "status": "todo",
            "priority": "P3",
            "category": "research",
        },
    }

    fm_results = []
    for task_name, exp in expected_fm.items():
        note_path = found_notes.get(task_name)
        if not note_path:
            fm_results.append(f"{task_name}: note missing")
            continue
        content = load_file(note_path)
        fm = parse_frontmatter(content or "")
        errors = []
        for field, val in exp.items():
            actual = fm.get(field, "MISSING")
            if actual.lower() != val.lower():
                errors.append(f"{field}={actual!r} (expected {val!r})")
        # check required fields present
        for req in ["status", "priority", "category", "created"]:
            if req not in fm:
                errors.append(f"missing required field: {req}")
        if errors:
            fm_results.append(f"{task_name}: {errors}")

    c6_passed = len(fm_results) == 0
    checks.append(check(
        "All task frontmatter fields correct (status, priority, category, due, created)",
        c6_passed,
        f"Issues: {fm_results}" if fm_results else "All frontmatter correct"
    ))

    # ── CHECK 7: Status values use hyphens (in-progress, not in_progress) ─────
    hyphen_ok = True
    hyphen_detail = []
    for task_name, note_path in found_notes.items():
        if not note_path:
            continue
        content = load_file(note_path) or ""
        fm = parse_frontmatter(content)
        status = fm.get("status", "")
        if "_" in status:
            hyphen_ok = False
            hyphen_detail.append(f"{task_name}: status={status!r} uses underscore")
        if status not in ["backlog", "todo", "in-progress", "review", "done"]:
            hyphen_ok = False
            hyphen_detail.append(f"{task_name}: status={status!r} is not a valid value")
    checks.append(check(
        "Status values use correct hyphenated format",
        hyphen_ok,
        "; ".join(hyphen_detail) if hyphen_detail else "All status values valid"
    ))

    # ── CHECK 8: Board.md has correct emoji priority prefixes ─────────────────
    # P1 tasks → 🔴, P2 → 🟡, P3 → 🟢
    if board_content:
        emoji_errors = []

        # IND-Application-Draft is P1 → must have 🔴
        if "IND-Application-Draft" in board_content:
            # find the line
            for line in board_content.splitlines():
                if "IND-Application-Draft" in line:
                    if "🔴" not in line:
                        emoji_errors.append("IND-Application-Draft (P1) missing 🔴")
                    break

        # Toxicology-Report-Review is P2 → but it's done, check ✅ marker
        # Synthesize-X47-Batch2 is P1 → 🔴 (in Todo column now)
        if "Synthesize-X47-Batch2" in board_content:
            for line in board_content.splitlines():
                if "Synthesize-X47-Batch2" in line and line.strip().startswith("-"):
                    if "🔴" not in line:
                        emoji_errors.append("Synthesize-X47-Batch2 (P1) missing 🔴")
                    break

        # Competitor-IP-Landscape is P3 → 🟢
        if "Competitor-IP-Landscape" in board_content:
            for line in board_content.splitlines():
                if "Competitor-IP-Landscape" in line and line.strip().startswith("-"):
                    if "🟢" not in line:
                        emoji_errors.append("Competitor-IP-Landscape (P3) missing 🟢")
                    break

        c8_passed = len(emoji_errors) == 0
        checks.append(check(
            "Board.md uses correct emoji priority prefixes (🔴/🟡/🟢)",
            c8_passed,
            "; ".join(emoji_errors) if emoji_errors else "Emoji prefixes correct"
        ))
    else:
        checks.append(check("Board.md uses correct emoji priority prefixes", False, "Board.md not found"))

    # ── CHECK 9: Toxicology-Report-Review is DONE on board with ✅ and date ───
    if board_content:
        done_section_match = re.search(
            r'## Done\s*\n(.*?)(?=\n## |\Z)', board_content, re.DOTALL
        )
        tox_done_ok = False
        tox_detail = "Toxicology-Report-Review not found in Done column"
        if done_section_match:
            done_section = done_section_match.group(1)
            if "Toxicology-Report-Review" in done_section:
                # Should be - [x] [[Toxicology-Report-Review]] ✅ 2026-02-12
                for line in done_section.splitlines():
                    if "Toxicology-Report-Review" in line:
                        has_checked = "- [x]" in line
                        has_checkmark = "✅" in line
                        has_date = "2026-02-12" in line
                        if has_checked and has_checkmark and has_date:
                            tox_done_ok = True
                            tox_detail = f"Correctly marked done: {line.strip()}"
                        else:
                            tox_detail = (
                                f"Line found but incorrect: {line.strip()} "
                                f"(checked={has_checked}, ✅={has_checkmark}, date={has_date})"
                            )
                        break
        checks.append(check(
            "Toxicology-Report-Review marked [x] ✅ 2026-02-12 in Done column",
            tox_done_ok,
            tox_detail
        ))
    else:
        checks.append(check("Toxicology-Report-Review done on board", False, "Board.md not found"))

    # ── CHECK 10: Synthesize-X47-Batch2 is in Todo column (moved back) ────────
    if board_content:
        todo_section_match = re.search(
            r'## Todo\s*\n(.*?)(?=\n## |\Z)', board_content, re.DOTALL
        )
        synth_todo_ok = False
        synth_detail = "Synthesize-X47-Batch2 not found in Todo column"
        if todo_section_match:
            todo_section = todo_section_match.group(1)
            if "Synthesize-X47-Batch2" in todo_section:
                synth_todo_ok = True
                synth_detail = "Synthesize-X47-Batch2 found in Todo column"
        # Also verify it is NOT in In Progress anymore
        in_progress_match = re.search(
            r'## In Progress\s*\n(.*?)(?=\n## |\Z)', board_content, re.DOTALL
        )
        if in_progress_match and "Synthesize-X47-Batch2" in in_progress_match.group(1):
            synth_todo_ok = False
            synth_detail = "Synthesize-X47-Batch2 still in In Progress column"
        checks.append(check(
            "Synthesize-X47-Batch2 moved back to Todo column on board",
            synth_todo_ok,
            synth_detail
        ))
    else:
        checks.append(check("Synthesize-X47-Batch2 in Todo", False, "Board.md not found"))

    # ── CHECK 11: Board cards use @{date} syntax for due dates ────────────────
    if board_content:
        # Check any card with a date uses @{YYYY-MM-DD} not plain dates
        date_pattern_wrong = re.compile(r'(?<!@{)\b\d{4}-\d{2}-\d{2}\b(?!})')
        # Find card lines (lines starting with - [ ] or - [x])
        card_lines = [l for l in board_content.splitlines() if re.match(r'\s*-\s*\[', l)]
        bad_date_lines = []
        for line in card_lines:
            # Skip the ✅ completion date format which is allowed plain
            if "✅" in line:
                continue
            if date_pattern_wrong.search(line):
                # Check if @{...} is NOT present but a bare date IS
                if "@{" not in line and re.search(r'\d{4}-\d{2}-\d{2}', line):
                    bad_date_lines.append(line.strip())
        c11_passed = len(bad_date_lines) == 0
        checks.append(check(
            "Board card due dates use @{YYYY-MM-DD} syntax",
            c11_passed,
            f"Bad lines: {bad_date_lines}" if bad_date_lines else "Date syntax correct on cards"
        ))
    else:
        checks.append(check("Board card due dates use @{} syntax", False, "Board.md not found"))

    # ── CHECK 12: Wikilinks in task notes reference Research docs ─────────────
    wikilink_checks = {
        "Synthesize-X47-Batch2": "compound-X47-assay-results",
        "Toxicology-Report-Review": "toxicology-prelim-2026-01",
        "Competitor-IP-Landscape": "competitor-landscape",
    }
    wikilink_errors = []
    for task_name, expected_ref in wikilink_checks.items():
        note_path = found_notes.get(task_name)
        if not note_path:
            wikilink_errors.append(f"{task_name}: note missing")
            continue
        content = load_file(note_path) or ""
        if f"[[{expected_ref}" not in content:
            wikilink_errors.append(f"{task_name}: missing [[{expected_ref}...]] wikilink")
    c12_passed = len(wikilink_errors) == 0
    checks.append(check(
        "Task notes contain required [[wikilinks]] to Research docs",
        c12_passed,
        "; ".join(wikilink_errors) if wikilink_errors else "All wikilinks present"
    ))

    # ── CHECK 13: Board has wikilink-style card references [[Task Name]] ───────
    if board_content:
        board_wikilink_errors = []
        for task_name in task_names:
            if task_name not in board_content:
                board_wikilink_errors.append(f"{task_name} missing from board")
            elif f"[[{task_name}]]" not in board_content and f"[[{task_name}|" not in board_content:
                board_wikilink_errors.append(f"{task_name} on board but not as [[wikilink]]")
        c13_passed = len(board_wikilink_errors) == 0
        checks.append(check(
            "Board.md references tasks as [[wikilinks]]",
            c13_passed,
            "; ".join(board_wikilink_errors) if board_wikilink_errors else "All wikilinks on board correct"
        ))
    else:
        checks.append(check("Board.md wikilinks", False, "Board.md not found"))

    # ── SCORING ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 10  # must pass at least 10/13

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()