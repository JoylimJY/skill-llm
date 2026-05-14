#!/usr/bin/env python3
"""
Evaluation script for session-health-monitor task.
Usage: python3 eval_script.py /workspace
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

def run_eval(workspace_str: str) -> dict:
    workspace = Path(workspace_str)
    checks = []

    # ──────────────────────────────────────────────────────────────
    # CHECK 1: telegram_footer.txt exists and has correct RED-level format
    # Expected: ⚠️ 📊 78% Context Window | 2x compacted
    # ──────────────────────────────────────────────────────────────
    footer_files = list(workspace.rglob("telegram_footer.txt"))
    if not footer_files:
        checks.append({
            "name": "telegram_footer_exists",
            "passed": False,
            "detail": "telegram_footer.txt not found anywhere in workspace."
        })
        checks.append({
            "name": "telegram_footer_correct_format",
            "passed": False,
            "detail": "Skipped: file not found."
        })
    else:
        footer_path = footer_files[0]
        try:
            footer_content = footer_path.read_text(encoding="utf-8").strip()
            checks.append({
                "name": "telegram_footer_exists",
                "passed": True,
                "detail": f"Found at {footer_path}. Content: {repr(footer_content)}"
            })

            # RED level: must start with ⚠️ and contain 📊 78% Context Window | 2x compacted
            # Exact format from SKILL.md: ⚠️ 📊 81% Context Window | 2x compacted
            # Our scenario: 78% and 2 compactions
            pattern_red = r"⚠️\s*📊\s*78%\s*Context\s*Window\s*\|\s*2x\s*compacted"
            match = re.search(pattern_red, footer_content)
            checks.append({
                "name": "telegram_footer_correct_format",
                "passed": bool(match),
                "detail": (
                    f"Footer content: {repr(footer_content)}\n"
                    f"Expected pattern: '⚠️ 📊 78% Context Window | 2x compacted'\n"
                    f"Match found: {bool(match)}"
                )
            })
        except Exception as e:
            checks.append({
                "name": "telegram_footer_correct_format",
                "passed": False,
                "detail": f"Error reading footer file: {e}"
            })

    # ──────────────────────────────────────────────────────────────
    # CHECK 2: snapshot written to memory/YYYY-MM-DD.md
    # Must exist and contain a Pre-Compaction Snapshot section
    # ──────────────────────────────────────────────────────────────
    today_str = datetime.now().strftime("%Y-%m-%d")
    memory_dir = workspace / "memory"
    today_memory = memory_dir / f"{today_str}.md"

    try:
        if not today_memory.exists():
            checks.append({
                "name": "snapshot_file_exists",
                "passed": False,
                "detail": f"Expected memory file {today_memory} does not exist. Files in memory/: {list(memory_dir.glob('*.md'))}"
            })
            checks.append({
                "name": "snapshot_has_precompaction_section",
                "passed": False,
                "detail": "Skipped: file not found."
            })
            checks.append({
                "name": "snapshot_contains_session_facts",
                "passed": False,
                "detail": "Skipped: file not found."
            })
        else:
            checks.append({
                "name": "snapshot_file_exists",
                "passed": True,
                "detail": f"Found: {today_memory}"
            })
            content = today_memory.read_text(encoding="utf-8")

            # Must have "## Pre-Compaction Snapshot" header
            has_header = "## Pre-Compaction Snapshot" in content
            checks.append({
                "name": "snapshot_has_precompaction_section",
                "passed": has_header,
                "detail": f"'## Pre-Compaction Snapshot' header {'found' if has_header else 'NOT found'} in {today_memory}.\nContent preview: {content[:400]}"
            })

            # Must contain at least 3 key facts from the session notes
            # Key facts that should be extractable from session_notes.txt:
            # - CP-204 escalation decision / escalate above $50,000
            # - rules.yaml / R002 / risk-scanner config modified
            # - sanctions API / rate limit / cache workaround
            # - flagged transactions / manual review
            # - next steps: escalation report / fix retry logic
            fact_patterns = [
                # Decision about escalation threshold or CP-204
                r"(?i)(CP-204|escalat|50[,.]?000|\$50)",
                # File changed: rules.yaml
                r"(?i)(rules\.yaml|R002|risk.scanner|rules\s+engine)",
                # Sanctions API blocker
                r"(?i)(sanction|rate.limit|api|cache|retry)",
            ]
            facts_found = []
            for pat in fact_patterns:
                if re.search(pat, content):
                    facts_found.append(pat)

            min_facts = 2  # At least 2 of 3 key categories
            facts_ok = len(facts_found) >= min_facts
            checks.append({
                "name": "snapshot_contains_session_facts",
                "passed": facts_ok,
                "detail": (
                    f"Found {len(facts_found)}/{len(fact_patterns)} key fact categories in snapshot.\n"
                    f"Matched patterns: {facts_found}\n"
                    f"Content preview: {content[:600]}"
                )
            })
    except Exception as e:
        checks.append({
            "name": "snapshot_file_exists",
            "passed": False,
            "detail": f"Exception: {e}"
        })
        checks.append({
            "name": "snapshot_has_precompaction_section",
            "passed": False,
            "detail": f"Exception: {e}"
        })
        checks.append({
            "name": "snapshot_contains_session_facts",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ──────────────────────────────────────────────────────────────
    # CHECK 3: Memory rotation with KEEP_DAYS=7
    # Files older than 7 days should be in memory/archive/
    # Files 0-7 days old should remain in memory/
    # ──────────────────────────────────────────────────────────────
    today_date = datetime.now().date()
    archive_dir = memory_dir / "archive"

    # Files that SHOULD be archived (>7 days old based on filename date):
    # today - 8 days and today - 14 days
    should_be_archived = [
        (today_date - timedelta(days=8)).isoformat() + ".md",
        (today_date - timedelta(days=14)).isoformat() + ".md",
    ]
    # Files that SHOULD remain (<=7 days):
    should_remain = [
        today_str + ".md",
        (today_date - timedelta(days=1)).isoformat() + ".md",
        (today_date - timedelta(days=3)).isoformat() + ".md",
    ]

    archived_correctly = []
    archived_errors = []
    for fname in should_be_archived:
        in_archive = (archive_dir / fname).exists()
        still_in_memory = (memory_dir / fname).exists()
        if in_archive and not still_in_memory:
            archived_correctly.append(fname)
        else:
            archived_errors.append(f"{fname}: in_archive={in_archive}, still_in_memory={still_in_memory}")

    rotation_archive_ok = len(archived_correctly) >= 1  # at least one old file archived
    checks.append({
        "name": "rotation_archives_old_files",
        "passed": rotation_archive_ok,
        "detail": (
            f"Files correctly archived: {archived_correctly}\n"
            f"Files with issues: {archived_errors}\n"
            f"Archive dir contents: {[f.name for f in archive_dir.glob('*.md')] if archive_dir.exists() else 'dir missing'}"
        )
    })

    # Recent files should NOT be archived (should still be in memory/)
    remaining_correctly = []
    remaining_errors = []
    for fname in should_remain:
        # today's file was just created by agent's snapshot, that's expected
        if fname == today_str + ".md":
            continue  # skip today — agent creates it, don't penalize for it
        still_in_memory = (memory_dir / fname).exists()
        wrongly_archived = (archive_dir / fname).exists() and not still_in_memory
        if wrongly_archived:
            remaining_errors.append(f"{fname} was wrongly archived")
        else:
            remaining_correctly.append(fname)

    rotation_kept_ok = len(remaining_errors) == 0
    checks.append({
        "name": "rotation_keeps_recent_files",
        "passed": rotation_kept_ok,
        "detail": (
            f"Recent files correctly kept: {remaining_correctly}\n"
            f"Wrongly archived (should have stayed): {remaining_errors}\n"
            f"Memory dir contents: {[f.name for f in memory_dir.glob('*.md')]}"
        )
    })

    # ──────────────────────────────────────────────────────────────
    # SCORING
    # ──────────────────────────────────────────────────────────────
    weights = {
        "telegram_footer_exists": 0.5,
        "telegram_footer_correct_format": 2.0,
        "snapshot_file_exists": 0.5,
        "snapshot_has_precompaction_section": 1.0,
        "snapshot_contains_session_facts": 1.5,
        "rotation_archives_old_files": 1.5,
        "rotation_keeps_recent_files": 1.0,
    }
    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 1.0) for c in checks if c["passed"])
    score = round(earned / total_weight, 4)
    passed = score >= 0.75 and all(
        c["passed"] for c in checks if c["name"] in {
            "telegram_footer_correct_format",
            "snapshot_has_precompaction_section",
            "rotation_archives_old_files",
        }
    )

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))