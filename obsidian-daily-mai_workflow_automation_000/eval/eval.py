import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── 1. Find the daily note file inside 00.DAILY ──────────────────────────
    daily_dir = workspace / "vault" / "00.DAILY"
    candidate_files = list(daily_dir.glob("2026-03-12_*.md")) if daily_dir.exists() else []

    file_found = len(candidate_files) > 0
    checks.append({
        "name": "File exists in vault/00.DAILY/",
        "passed": file_found,
        "detail": f"Found: {[f.name for f in candidate_files]}" if file_found else "No file matching 2026-03-12_*.md found in vault/00.DAILY/"
    })

    if not file_found:
        # Also check if agent put it in wrong location
        all_candidates = list(workspace.rglob("2026-03-12_*.md"))
        wrong_loc = [str(f.relative_to(workspace)) for f in all_candidates]
        if wrong_loc:
            checks[-1]["detail"] += f" | File(s) found in wrong location: {wrong_loc}"
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    note_file = candidate_files[0]

    # ── 2. Filename format: YYYY-MM-DD_short-summary.md ──────────────────────
    filename = note_file.name
    filename_pattern = re.compile(r"^2026-03-12_[a-z0-9][a-z0-9\-]+\.md$")
    filename_ok = bool(filename_pattern.match(filename))
    checks.append({
        "name": "Filename follows YYYY-MM-DD_short-summary.md convention",
        "passed": filename_ok,
        "detail": f"Filename: '{filename}' — {'OK' if filename_ok else 'Does not match pattern 2026-03-12_<short-summary>.md (lowercase, hyphens only)'}"
    })

    # ── Read file content ─────────────────────────────────────────────────────
    try:
        content = note_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "File readable as UTF-8", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "File readable as UTF-8", "passed": True, "detail": "OK"})

    # ── 3. Header: # 2026-03-12 (Thursday) — Daily Note ──────────────────────
    # 2026-03-12 is a Thursday
    header_pattern = re.compile(
        r"^#\s+2026-03-12\s+\(Thursday\)\s+[—–]\s+Daily Note",
        re.MULTILINE
    )
    em_dash_pattern = re.compile(
        r"^#\s+2026-03-12\s+\(Thursday\)\s+—\s+Daily Note",
        re.MULTILINE
    )
    header_match = bool(header_pattern.search(content))
    em_dash_match = bool(em_dash_pattern.search(content))

    checks.append({
        "name": "Header contains correct date, day-of-week (Thursday), and em-dash (—)",
        "passed": header_match,
        "detail": (
            f"Header found with correct format" if header_match
            else f"Expected '# 2026-03-12 (Thursday) — Daily Note'. Em-dash present: {em_dash_match}. Content preview: {content[:200]!r}"
        )
    })

    # ── 4. 'Completed Today' section exists ───────────────────────────────────
    completed_section = "## Completed Today" in content
    checks.append({
        "name": "'## Completed Today' section present",
        "passed": completed_section,
        "detail": "Found" if completed_section else "Missing '## Completed Today' section"
    })

    # ── 5. 'Tomorrow's Actions' section exists ────────────────────────────────
    tomorrow_section = bool(re.search(r"## Tomorrow'?s Actions", content))
    checks.append({
        "name": "'## Tomorrow's Actions' section present",
        "passed": tomorrow_section,
        "detail": "Found" if tomorrow_section else "Missing \"## Tomorrow's Actions\" section"
    })

    # ── 6. At least one category with correct emoji prefix ───────────────────
    valid_emojis = ["🔧", "📱", "🚀", "🔗", "📝", "💡", "📋"]
    emoji_lines = [line for line in content.splitlines() if any(e in line for e in valid_emojis)]
    has_emoji_categories = len(emoji_lines) >= 1

    # Specifically check for Dev (🔧) and Mobile (📱) which are clearly present in session log
    has_dev_emoji = any("🔧" in line for line in content.splitlines())
    has_mobile_emoji = any("📱" in line for line in content.splitlines())

    checks.append({
        "name": "At least one category uses correct emoji prefix (🔧/📱/🚀/🔗/📝/💡/📋)",
        "passed": has_emoji_categories,
        "detail": f"Found emoji category lines: {emoji_lines}" if has_emoji_categories else "No valid emoji category prefixes found"
    })

    checks.append({
        "name": "🔧 Dev category present (major work done on renderer/Vulkan)",
        "passed": has_dev_emoji,
        "detail": "Found 🔧 Dev category" if has_dev_emoji else "Missing 🔧 Dev category — significant dev work was done"
    })

    checks.append({
        "name": "📱 Mobile category present (Android/OpenGL ES work logged)",
        "passed": has_mobile_emoji,
        "detail": "Found 📱 Mobile category" if has_mobile_emoji else "Missing 📱 Mobile category — mobile port work was done"
    })

    # ── 7. Arrow syntax → in task bullets ────────────────────────────────────
    arrow_pattern = re.compile(r"\*\*[^*]+\*\*\s*→")
    has_arrow_format = bool(arrow_pattern.search(content))
    checks.append({
        "name": "Task bullets use '**Task** → Result' format with → arrow",
        "passed": has_arrow_format,
        "detail": "Found **Task** → Result format" if has_arrow_format else "Missing bold task + → arrow result format (e.g. '**Fixed shader** → ...')"
    })

    # ── 8. Tomorrow's action items are checkboxes ─────────────────────────────
    checkbox_pattern = re.compile(r"^- \[ \] .+", re.MULTILINE)
    checkbox_items = checkbox_pattern.findall(content)
    has_checkboxes = len(checkbox_items) >= 2  # session log had 3 pending items
    checks.append({
        "name": "Tomorrow's actions contain at least 2 '- [ ]' checkbox items",
        "passed": has_checkboxes,
        "detail": f"Found {len(checkbox_items)} checkbox item(s): {checkbox_items}" if checkbox_items else "No checkbox items found"
    })

    # ── 9. Substantive content (not empty/placeholder) ────────────────────────
    # Check that renderer/shadow/mobile content is actually present
    substantive_keywords = ["renderer", "shadow", "android", "mobile", "vulkan", "light", "frame"]
    content_lower = content.lower()
    keyword_hits = [kw for kw in substantive_keywords if kw in content_lower]
    has_substantive_content = len(keyword_hits) >= 3
    checks.append({
        "name": "Note contains substantive content derived from session log (3+ key topics)",
        "passed": has_substantive_content,
        "detail": f"Found keywords: {keyword_hits}" if has_substantive_content else f"Only found: {keyword_hits} — content too sparse or generic"
    })

    # ── Final scoring ─────────────────────────────────────────────────────────
    weights = {
        0: 0.10,   # file in right dir
        1: 0.08,   # filename format
        2: 0.02,   # utf-8 readable
        3: 0.15,   # header with em-dash + Thursday
        4: 0.08,   # Completed Today section
        5: 0.08,   # Tomorrow's Actions section
        6: 0.08,   # any emoji category
        7: 0.08,   # Dev emoji
        8: 0.08,   # Mobile emoji
        9: 0.10,   # arrow format
        10: 0.08,  # checkboxes
        11: 0.07,  # substantive content
    }
    total_weight = sum(weights.values())
    score = sum(weights[i] for i, c in enumerate(checks) if c["passed"])
    score = round(score / total_weight, 4)

    passed = all(c["passed"] for c in checks)

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))