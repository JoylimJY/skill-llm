import json
import sys
import csv
from pathlib import Path

def load_datafile():
    data_path = Path.home() / ".ebook" / "data.jsonl"
    records = []
    if not data_path.exists():
        return records, f"data.jsonl not found at {data_path}"
    with open(data_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                pass
    return records, None

def main(workspace):
    workspace = Path(workspace)
    checks = []

    # ── Load JSONL data ──────────────────────────────────────────────────────
    records, err = load_datafile()
    if err:
        checks.append({"name": "data_file_exists", "passed": False, "detail": err})
        score = 0.0
        print(json.dumps({"passed": False, "score": score, "checks": checks}))
        return

    checks.append({"name": "data_file_exists", "passed": True, "detail": f"Found {len(records)} records"})

    books = [r for r in records if r.get("type") == "book"]
    sessions = [r for r in records if r.get("type") == "session"]
    highlights = [r for r in records if r.get("type") == "highlight"]
    reviews = [r for r in records if r.get("type") == "review"]

    # ── Check 1: Two books added ─────────────────────────────────────────────
    pragmatic = next((b for b in books if "Pragmatic Programmer" in b.get("title", "")), None)
    pattern = next((b for b in books if "Pattern Language" in b.get("title", "")), None)

    checks.append({
        "name": "book_pragmatic_programmer_exists",
        "passed": pragmatic is not None,
        "detail": "Found 'The Pragmatic Programmer'" if pragmatic else "Book not found"
    })
    checks.append({
        "name": "book_pattern_language_exists",
        "passed": pattern is not None,
        "detail": "Found 'A Pattern Language'" if pattern else "Book not found"
    })

    # ── Check 2: Correct formats (must be from the allowed set) ──────────────
    pragmatic_format_ok = pragmatic is not None and pragmatic.get("format") == "pdf"
    pattern_format_ok = pattern is not None and pattern.get("format") == "epub"

    checks.append({
        "name": "pragmatic_format_is_pdf",
        "passed": pragmatic_format_ok,
        "detail": f"format={pragmatic.get('format') if pragmatic else 'N/A'} (expected pdf)"
    })
    checks.append({
        "name": "pattern_format_is_epub",
        "passed": pattern_format_ok,
        "detail": f"format={pattern.get('format') if pattern else 'N/A'} (expected epub)"
    })

    # ── Check 3: Correct page counts ─────────────────────────────────────────
    pragmatic_pages_ok = pragmatic is not None and pragmatic.get("pages") == 352
    pattern_pages_ok = pattern is not None and pattern.get("pages") == 1171

    checks.append({
        "name": "pragmatic_pages_352",
        "passed": pragmatic_pages_ok,
        "detail": f"pages={pragmatic.get('pages') if pragmatic else 'N/A'} (expected 352)"
    })
    checks.append({
        "name": "pattern_pages_1171",
        "passed": pattern_pages_ok,
        "detail": f"pages={pattern.get('pages') if pattern else 'N/A'} (expected 1171)"
    })

    # ── Check 4: Tags present ─────────────────────────────────────────────────
    pragmatic_tags_ok = pragmatic is not None and set(["programming", "career"]).issubset(set(pragmatic.get("tags", [])))
    pattern_tags_ok = pattern is not None and set(["architecture", "design"]).issubset(set(pattern.get("tags", [])))

    checks.append({
        "name": "pragmatic_has_tags_programming_career",
        "passed": pragmatic_tags_ok,
        "detail": f"tags={pragmatic.get('tags') if pragmatic else 'N/A'}"
    })
    checks.append({
        "name": "pattern_has_tags_architecture_design",
        "passed": pattern_tags_ok,
        "detail": f"tags={pattern.get('tags') if pattern else 'N/A'}"
    })

    # ── Check 5: Reading sessions logged ─────────────────────────────────────
    pragmatic_id = pragmatic["id"] if pragmatic else None
    pattern_id = pattern["id"] if pattern else None

    pragmatic_sessions = [s for s in sessions if s.get("book_id") == pragmatic_id] if pragmatic_id else []
    pattern_sessions = [s for s in sessions if s.get("book_id") == pattern_id] if pattern_id else []

    # Pragmatic: pages 1-88, 45 minutes
    pragmatic_session_ok = any(
        s.get("start_page") == 1 and s.get("end_page") == 88 and s.get("duration") == 45
        for s in pragmatic_sessions
    )
    # Pattern Language: pages 1-60, 40 minutes
    pattern_session_ok = any(
        s.get("start_page") == 1 and s.get("end_page") == 60 and s.get("duration") == 40
        for s in pattern_sessions
    )

    checks.append({
        "name": "pragmatic_session_logged",
        "passed": pragmatic_session_ok,
        "detail": f"Sessions found: {pragmatic_sessions}"
    })
    checks.append({
        "name": "pattern_session_logged",
        "passed": pattern_session_ok,
        "detail": f"Sessions found: {pattern_sessions}"
    })

    # ── Check 6: Highlights linked correctly ────────────────────────────────
    pragmatic_highlights = [h for h in highlights if h.get("book_id") == pragmatic_id] if pragmatic_id else []
    pattern_highlights = [h for h in highlights if h.get("book_id") == pattern_id] if pattern_id else []

    pragmatic_highlight_ok = any(
        h.get("page") == 14 and "Care about your craft" in h.get("text", "")
        for h in pragmatic_highlights
    )
    pattern_highlight_ok = any(
        h.get("page") == 32 and "pattern describes a problem" in h.get("text", "")
        for h in pattern_highlights
    )

    checks.append({
        "name": "pragmatic_highlight_page14",
        "passed": pragmatic_highlight_ok,
        "detail": f"Highlights: {pragmatic_highlights}"
    })
    checks.append({
        "name": "pattern_highlight_page32",
        "passed": pattern_highlight_ok,
        "detail": f"Highlights: {pattern_highlights}"
    })

    # ── Check 7: Reviews ────────────────────────────────────────────────────
    pragmatic_reviews = [r for r in reviews if r.get("book_id") == pragmatic_id] if pragmatic_id else []
    pattern_reviews = [r for r in reviews if r.get("book_id") == pattern_id] if pattern_id else []

    pragmatic_review_ok = any(
        r.get("rating") == 5 and "must-read" in r.get("text", "").lower()
        for r in pragmatic_reviews
    )
    pattern_review_ok = any(
        r.get("rating") == 4 and ("dense" in r.get("text", "").lower() or "foundational" in r.get("text", "").lower())
        for r in pattern_reviews
    )

    checks.append({
        "name": "pragmatic_review_5stars",
        "passed": pragmatic_review_ok,
        "detail": f"Reviews: {pragmatic_reviews}"
    })
    checks.append({
        "name": "pattern_review_4stars",
        "passed": pattern_review_ok,
        "detail": f"Reviews: {pattern_reviews}"
    })

    # ── Check 8: Markdown library export ────────────────────────────────────
    md_files = list(workspace.rglob("library_spring2025.md"))
    md_ok = False
    md_detail = "library_spring2025.md not found"
    if md_files:
        try:
            md_content = md_files[0].read_text()
            has_pragmatic = "Pragmatic Programmer" in md_content
            has_pattern = "Pattern Language" in md_content
            has_header = "# My Ebook Library" in md_content or "## Books" in md_content
            md_ok = has_pragmatic and has_pattern and has_header
            md_detail = (
                f"Found at {md_files[0]}. "
                f"has_pragmatic={has_pragmatic}, has_pattern={has_pattern}, has_header={has_header}"
            )
        except Exception as e:
            md_detail = f"Error reading file: {e}"

    checks.append({
        "name": "markdown_library_export_exists_and_valid",
        "passed": md_ok,
        "detail": md_detail
    })

    # ── Check 9: Highlights CSV export ──────────────────────────────────────
    csv_files = list(workspace.rglob("highlights_spring2025.csv"))
    csv_ok = False
    csv_detail = "highlights_spring2025.csv not found"
    if csv_files:
        try:
            with open(csv_files[0], newline='') as cf:
                reader = csv.DictReader(cf)
                rows = list(reader)
            # Must have highlight rows (type == highlight or book_id present)
            highlight_rows = [r for r in rows if r.get("type") == "highlight" or r.get("book_id")]
            has_care_craft = any("Care about your craft" in r.get("text", "") for r in highlight_rows)
            has_pattern_desc = any("pattern describes a problem" in r.get("text", "") for r in highlight_rows)
            csv_ok = len(highlight_rows) >= 2 and has_care_craft and has_pattern_desc
            csv_detail = (
                f"Found {len(highlight_rows)} highlight rows. "
                f"has_care_craft={has_care_craft}, has_pattern_desc={has_pattern_desc}"
            )
        except Exception as e:
            csv_detail = f"Error reading CSV: {e}"

    checks.append({
        "name": "csv_highlights_export_exists_and_valid",
        "passed": csv_ok,
        "detail": csv_detail
    })

    # ── Check 10: Book statuses are valid ────────────────────────────────────
    valid_statuses = {"unread", "reading", "finished", "abandoned", "wishlist"}
    invalid_status_books = [b for b in books if b.get("status") not in valid_statuses]
    status_ok = len(invalid_status_books) == 0
    checks.append({
        "name": "all_book_statuses_valid",
        "passed": status_ok,
        "detail": f"Invalid status books: {invalid_status_books}" if not status_ok else "All statuses valid"
    })

    # ── Score calculation ────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = all(c["passed"] for c in checks)

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/workspace")