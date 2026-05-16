import sys
import re
import json
from pathlib import Path
from datetime import date

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # =========================================================================
    # CHECK 1: Five learning entries captured via mem_learn.py
    # Verify .learning_count file shows >= 5
    # =========================================================================
    try:
        count_file = workspace / "memory" / "learnings" / ".learning_count"
        if count_file.exists():
            count = int(count_file.read_text().strip())
            passed = count >= 5
            add_check(
                "five_learnings_captured",
                passed,
                f"Learning count file shows {count} (need >= 5)",
                weight=2.0
            )
        else:
            add_check(
                "five_learnings_captured",
                False,
                "No .learning_count file found in memory/learnings/",
                weight=2.0
            )
    except Exception as e:
        add_check("five_learnings_captured", False, f"Error reading count: {e}", weight=2.0)

    # =========================================================================
    # CHECK 2: Learning files exist in memory/learnings/ with correct format
    # Must have ## Incident, ## Lesson, ## Context, ## Tags sections
    # =========================================================================
    try:
        learnings_dir = workspace / "memory" / "learnings"
        learning_files = sorted([
            f for f in learnings_dir.glob("*.md")
            if f.name != "patterns.md" and not f.name.startswith(".")
        ]) if learnings_dir.exists() else []

        if not learning_files:
            add_check("learning_files_correct_format", False, "No learning .md files found", weight=2.0)
        else:
            all_content = "\n".join(f.read_text() for f in learning_files)
            has_incident = "## Incident" in all_content
            has_lesson = "## Lesson" in all_content
            has_tags = "## Tags" in all_content
            has_context = "## Context" in all_content
            all_sections = has_incident and has_lesson and has_tags and has_context
            add_check(
                "learning_files_correct_format",
                all_sections,
                f"Sections found - Incident:{has_incident}, Lesson:{has_lesson}, Context:{has_context}, Tags:{has_tags}",
                weight=2.0
            )
    except Exception as e:
        add_check("learning_files_correct_format", False, f"Error: {e}", weight=2.0)

    # =========================================================================
    # CHECK 3: All 5 incidents from raw_feedback_notes.txt are captured
    # Each incident must map to a learning entry — check for key content
    # =========================================================================
    try:
        learnings_dir = workspace / "memory" / "learnings"
        learning_files = sorted([
            f for f in learnings_dir.glob("*.md")
            if f.name != "patterns.md" and not f.name.startswith(".")
        ]) if learnings_dir.exists() else []
        all_content = "\n".join(f.read_text() for f in learning_files).lower()

        incident_keywords = [
            ("vendorx_or_vendor_tool", ["vendorx", "vendor", "tool inventory", "licensing"]),
            ("formatting_prose_vs_bullets", ["bullet", "format", "prose", "user preference", "output format"]),
            ("cloudbridge_rate_limit", ["cloudbridge", "rate limit", "constraint", "confirm"]),
            ("harmon_jurisdiction", ["harmon", "gdpr", "jurisdiction", "compliance", "us-only", "verification"]),
            ("repeated_vendor_pattern", ["second time", "repeated", "again", "behavioral", "permanent"]),
        ]

        found_all = True
        details = []
        for name, keywords in incident_keywords:
            found = any(kw in all_content for kw in keywords)
            details.append(f"{name}:{'✓' if found else '✗'}")
            if not found:
                found_all = False

        add_check(
            "all_five_incidents_captured",
            found_all,
            "Incident coverage: " + ", ".join(details),
            weight=2.0
        )
    except Exception as e:
        add_check("all_five_incidents_captured", False, f"Error: {e}", weight=2.0)

    # =========================================================================
    # CHECK 4: Confidence levels are valid (high/medium/low) in learning files
    # =========================================================================
    try:
        learnings_dir = workspace / "memory" / "learnings"
        learning_files = sorted([
            f for f in learnings_dir.glob("*.md")
            if f.name != "patterns.md" and not f.name.startswith(".")
        ]) if learnings_dir.exists() else []
        all_content = "\n".join(f.read_text() for f in learning_files)

        # Check that confidence values appear (from LEARN/LESSON/CONFIDENCE block or stored in file)
        # The format in SKILL.md specifies CONFIDENCE: high/medium/low — check files reference it
        # OR check that the lessons don't have invalid confidence values
        valid_confidences = re.findall(r"confidence[:\s]+(high|medium|low)", all_content, re.IGNORECASE)
        # At minimum 1 confidence label present (mem_learn.py requires it)
        has_valid = len(valid_confidences) >= 1
        add_check(
            "confidence_levels_valid",
            has_valid,
            f"Found {len(valid_confidences)} valid confidence labels (high/medium/low) in learning files",
            weight=1.0
        )
    except Exception as e:
        add_check("confidence_levels_valid", False, f"Error: {e}", weight=1.0)

    # =========================================================================
    # CHECK 5: mem_evolve.py was run — patterns.md exists and has content
    # =========================================================================
    try:
        patterns_file = workspace / "memory" / "learnings" / "patterns.md"
        if not patterns_file.exists():
            add_check("patterns_md_exists", False, "patterns.md does not exist", weight=2.0)
        else:
            content = patterns_file.read_text()
            has_pattern_review = "Pattern Review" in content
            has_archived = "Archived Lessons" in content or len(content) > 100
            passed = has_pattern_review and has_archived
            add_check(
                "patterns_md_exists",
                passed,
                f"patterns.md exists. Has 'Pattern Review': {has_pattern_review}, Has content: {has_archived}",
                weight=2.0
            )
    except Exception as e:
        add_check("patterns_md_exists", False, f"Error: {e}", weight=2.0)

    # =========================================================================
    # CHECK 6: SOUL.md has been updated with Behavioral Guidelines Update section
    # (from mem_evolve.py run)
    # =========================================================================
    try:
        soul_file = workspace / "SOUL.md"
        if not soul_file.exists():
            add_check("soul_md_updated", False, "SOUL.md does not exist", weight=2.0)
        else:
            content = soul_file.read_text()
            has_guidelines_update = "Behavioral Guidelines Update" in content
            # Also check vendor-selection pattern is reflected
            has_vendor_pattern = any(kw in content.lower() for kw in ["vendor", "tool-choice", "tool_choice", "recurring"])
            passed = has_guidelines_update
            add_check(
                "soul_md_updated",
                passed,
                f"SOUL.md has 'Behavioral Guidelines Update': {has_guidelines_update}. Vendor pattern reflected: {has_vendor_pattern}",
                weight=2.0
            )
    except Exception as e:
        add_check("soul_md_updated", False, f"Error: {e}", weight=2.0)

    # =========================================================================
    # CHECK 7: MEMORY.md has ALL five required categories
    # Identity, User, Learnings, Projects, Patterns
    # =========================================================================
    try:
        memory_file = workspace / "MEMORY.md"
        if not memory_file.exists():
            add_check("memory_md_all_categories", False, "MEMORY.md not found", weight=2.0)
        else:
            content = memory_file.read_text()
            required = ["Identity", "User", "Learnings", "Projects", "Patterns"]
            found = [c for c in required if c in content]
            missing = [c for c in required if c not in content]
            passed = len(missing) == 0
            add_check(
                "memory_md_all_categories",
                passed,
                f"Found: {found}. Missing: {missing}",
                weight=2.0
            )
    except Exception as e:
        add_check("memory_md_all_categories", False, f"Error: {e}", weight=2.0)

    # =========================================================================
    # CHECK 8: MEMORY.md Learnings section has distilled content from incidents
    # =========================================================================
    try:
        memory_file = workspace / "MEMORY.md"
        if not memory_file.exists():
            add_check("memory_md_learnings_populated", False, "MEMORY.md not found", weight=1.5)
        else:
            content = memory_file.read_text().lower()
            # Check that at least 2 of the key lessons appear distilled in MEMORY.md
            lesson_signals = ["vendor", "format", "bullet", "confirm", "compliance", "jurisdiction", "constraint", "tool"]
            found_signals = [s for s in lesson_signals if s in content]
            passed = len(found_signals) >= 2
            add_check(
                "memory_md_learnings_populated",
                passed,
                f"MEMORY.md Learnings section signals found: {found_signals} ({len(found_signals)}/2 required)",
                weight=1.5
            )
    except Exception as e:
        add_check("memory_md_learnings_populated", False, f"Error: {e}", weight=1.5)

    # =========================================================================
    # CHECK 9: Daily log exists in memory/ with correct ## Session format
    # =========================================================================
    try:
        memory_dir = workspace / "memory"
        daily_logs = sorted([
            f for f in memory_dir.glob("[0-9]*.md")
        ]) if memory_dir.exists() else []

        if not daily_logs:
            add_check("daily_log_correct_format", False, "No dated daily logs found in memory/", weight=1.5)
        else:
            # Check at least one daily log has the required format
            found_correct = False
            detail_parts = []
            for log in daily_logs:
                content = log.read_text()
                has_session = "## Session" in content
                has_what_happened = "### What happened" in content or "What happened" in content
                has_key_decisions = "### Key decisions" in content or "Key decisions" in content
                if has_session and has_what_happened:
                    found_correct = True
                    detail_parts.append(f"{log.name}: Session✓ WhatHappened✓ KeyDecisions:{has_key_decisions}")
                else:
                    detail_parts.append(f"{log.name}: Session:{has_session} WhatHappened:{has_what_happened}")
            add_check(
                "daily_log_correct_format",
                found_correct,
                "Daily logs: " + "; ".join(detail_parts),
                weight=1.5
            )
    except Exception as e:
        add_check("daily_log_correct_format", False, f"Error: {e}", weight=1.5)

    # =========================================================================
    # CHECK 10: Session activity from raw_feedback_notes.txt recorded in daily log
    # (RetailCore/Kafka decision, DataFlow recommendations)
    # =========================================================================
    try:
        memory_dir = workspace / "memory"
        daily_logs = sorted([
            f for f in memory_dir.glob("[0-9]*.md")
        ]) if memory_dir.exists() else []
        all_daily = "\n".join(f.read_text() for f in daily_logs).lower()

        session_signals = ["kafka", "retailcore", "dataflow", "blue-green", "schema", "cloudbridge"]
        found_signals = [s for s in session_signals if s in all_daily]
        passed = len(found_signals) >= 2
        add_check(
            "session_activities_in_daily_log",
            passed,
            f"Session activity signals in daily logs: {found_signals} ({len(found_signals)}/2 required)",
            weight=1.5
        )
    except Exception as e:
        add_check("session_activities_in_daily_log", False, f"Error: {e}", weight=1.5)

    # =========================================================================
    # Final scoring
    # =========================================================================
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    overall_passed = score >= 0.75

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)