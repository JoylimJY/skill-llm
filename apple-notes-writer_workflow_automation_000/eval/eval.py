import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ══ FIND ARTIFACTS ══════════════════════════════════════════════════════
    html_files = list(workspace_path.rglob("note_content.html"))
    py_files   = list(workspace_path.rglob("publish_note.py"))

    html_content = ""
    py_content   = ""

    # Check 1: note_content.html exists
    try:
        assert len(html_files) > 0, "note_content.html not found anywhere in workspace"
        html_content = html_files[0].read_text(encoding="utf-8")
        add_check("note_content.html exists", True, f"Found at {html_files[0]}")
    except Exception as e:
        add_check("note_content.html exists", False, str(e))

    # Check 2: publish_note.py exists
    try:
        assert len(py_files) > 0, "publish_note.py not found anywhere in workspace"
        py_content = py_files[0].read_text(encoding="utf-8")
        add_check("publish_note.py exists", True, f"Found at {py_files[0]}")
    except Exception as e:
        add_check("publish_note.py exists", False, str(e))

    # ══ HTML CONTENT CHECKS ══════════════════════════════════════════════════

    # Check 3: Outer <div> wrapper (MANDATORY per SKILL.md)
    try:
        stripped = html_content.strip()
        has_outer_div = stripped.startswith("<div") and stripped.endswith("</div>")
        add_check(
            "HTML wrapped in outer <div>",
            has_outer_div,
            "Content must start with <div> and end with </div> (SKILL.md requirement)"
        )
    except Exception as e:
        add_check("HTML wrapped in outer <div>", False, str(e))

    # Check 4: No unsupported tags — <code>, <img>, <table>, <pre>
    try:
        forbidden = re.findall(r"<(code|img|table|pre|thead|tbody|tr|td|th)\b", html_content, re.IGNORECASE)
        no_forbidden = len(forbidden) == 0
        add_check(
            "No unsupported HTML tags (code/img/table/pre)",
            no_forbidden,
            f"Found forbidden tags: {list(set(forbidden))}" if forbidden else "All tags are supported"
        )
    except Exception as e:
        add_check("No unsupported HTML tags", False, str(e))

    # Check 5: Code blocks replaced with italic note
    try:
        has_italic_replacement = bool(
            re.search(r"<i[^>]*>.*?see attached config file.*?</i>", html_content, re.IGNORECASE | re.DOTALL)
        )
        add_check(
            "Code blocks replaced with italic '(see attached config file)'",
            has_italic_replacement,
            "Each code block should be replaced with <i>(see attached config file)</i>"
        )
    except Exception as e:
        add_check("Code blocks replaced with italic placeholder", False, str(e))

    # Check 6: ☐ symbol for pending action items (SKILL.md Unicode symbols)
    try:
        has_pending_checkbox = "☐" in html_content
        add_check(
            "Pending action items use ☐ Unicode symbol",
            has_pending_checkbox,
            "Markdown '- [ ]' should be converted to ☐ (U+2610) per SKILL.md recommended symbols"
        )
    except Exception as e:
        add_check("Pending action items use ☐ symbol", False, str(e))

    # Check 7: ✓ symbol for completed action items (SKILL.md Unicode symbols)
    try:
        has_done_checkmark = "✓" in html_content
        add_check(
            "Completed action items use ✓ Unicode symbol",
            has_done_checkmark,
            "Markdown '- [x]' should be converted to ✓ (U+2713) per SKILL.md recommended symbols"
        )
    except Exception as e:
        add_check("Completed action items use ✓ symbol", False, str(e))

    # Check 8: Proper heading tags present (h1 for title at minimum)
    try:
        has_h1 = bool(re.search(r"<h1>", html_content, re.IGNORECASE))
        add_check(
            "Contains <h1> heading tag",
            has_h1,
            "The postmortem title/main heading should be an <h1> tag"
        )
    except Exception as e:
        add_check("Contains <h1> heading tag", False, str(e))

    # Check 9: Key content preserved — incident ID and severity appear
    try:
        has_inc_id    = "INC-2024-0042" in html_content
        has_severity  = "P1" in html_content or "Critical" in html_content
        add_check(
            "Key incident metadata preserved in HTML",
            has_inc_id and has_severity,
            f"INC-2024-0042 present: {has_inc_id}, P1/Critical present: {has_severity}"
        )
    except Exception as e:
        add_check("Key incident metadata preserved", False, str(e))

    # Check 10: All HTML tags are properly closed (basic check)
    try:
        block_tags = ["h1", "h2", "h3", "p", "ul", "ol", "li", "b", "i", "u", "div"]
        unclosed = []
        for tag in block_tags:
            opens  = len(re.findall(rf"<{tag}(?:\s[^>]*)?>",  html_content, re.IGNORECASE))
            closes = len(re.findall(rf"</{tag}>", html_content, re.IGNORECASE))
            if opens != closes:
                unclosed.append(f"<{tag}> (opened {opens}, closed {closes})")
        all_closed = len(unclosed) == 0
        add_check(
            "All block HTML tags properly closed",
            all_closed,
            f"Mismatched tags: {unclosed}" if unclosed else "All tags balanced"
        )
    except Exception as e:
        add_check("All HTML tags properly closed", False, str(e))

    # ══ PYTHON SCRIPT CHECKS ═════════════════════════════════════════════════

    # Check 11: Imports AppleNotesWriter from scripts.apple_notes
    try:
        imports_writer = bool(
            re.search(r"from\s+scripts\.apple_notes\s+import.*AppleNotesWriter", py_content)
            or re.search(r"import\s+scripts\.apple_notes", py_content)
        )
        add_check(
            "publish_note.py imports AppleNotesWriter from scripts.apple_notes",
            imports_writer,
            "Must use 'from scripts.apple_notes import AppleNotesWriter' per SKILL.md"
        )
    except Exception as e:
        add_check("publish_note.py imports AppleNotesWriter", False, str(e))

    # Check 12: Correct note title used
    try:
        correct_title = "INC-2024-0042 API Gateway Outage Postmortem" in py_content
        add_check(
            "publish_note.py uses correct note title",
            correct_title,
            "Title must be 'INC-2024-0042 API Gateway Outage Postmortem' per task brief"
        )
    except Exception as e:
        add_check("publish_note.py uses correct note title", False, str(e))

    # Check 13: Target folder is "Incident Reports"
    try:
        correct_folder = bool(re.search(r"[Ii]ncident\s+[Rr]eports", py_content))
        add_check(
            "publish_note.py targets folder 'Incident Reports'",
            correct_folder,
            "folder parameter must be 'Incident Reports' per task brief"
        )
    except Exception as e:
        add_check("publish_note.py targets 'Incident Reports' folder", False, str(e))

    # Check 14: update_existing=True (PROPRIETARY: NOT update=True)
    try:
        # Must use update_existing=True, NOT --update flag (which maps to update_existing in CLI)
        uses_update_existing = bool(re.search(r"update_existing\s*=\s*True", py_content))
        # Also accept CLI --update flag usage (secondary path)
        uses_cli_update = bool(re.search(r"--update", py_content))
        correct_update_param = uses_update_existing or uses_cli_update
        add_check(
            "publish_note.py uses update_existing=True (not a different param name)",
            correct_update_param,
            f"update_existing=True: {uses_update_existing}, --update CLI: {uses_cli_update}. "
            "SKILL.md specifies update_existing=True for the Python API"
        )
    except Exception as e:
        add_check("publish_note.py uses update_existing=True", False, str(e))

    # Check 15: .write() method is called
    try:
        calls_write = bool(re.search(r"\.write\s*\(", py_content))
        add_check(
            "publish_note.py calls .write() method on writer instance",
            calls_write,
            "Must instantiate AppleNotesWriter and call .write() with correct parameters"
        )
    except Exception as e:
        add_check("publish_note.py calls .write()", False, str(e))

    # ══ SCORING ══════════════════════════════════════════════════════════════
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = round(len(passed_checks) / total, 4) if total > 0 else 0.0
    overall = score >= 0.75  # Must pass at least 75% of checks

    return {
        "passed": overall,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))