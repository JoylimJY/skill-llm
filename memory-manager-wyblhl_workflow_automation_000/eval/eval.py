#!/usr/bin/env python3
"""
Evaluation script for the OpenClaw memory management task.
Reference NOW = 2026-04-20T12:00:00

Checks:
1. config.json corrected per SKILL.md canonical values
2. Working memory files >7 days old migrated to short-term/
3. Short-term memory files >30 days old migrated to long-term/
4. Learning rounds pruned to most recent 50 (rounds 1-28 deleted, 29-78 kept)
5. Conversations pruned to most recent 10 (conversations 1-13 deleted, 14-23 kept)
6. MEMORY.md preserved (untouched)
7. Archive report generated (memory-archive-report.json)
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

def evaluate(workspace: str):
    ws = Path(workspace)
    memory = ws / "memory"
    tiers = memory / "tiers"
    working = tiers / "working"
    short_term = tiers / "short-term"
    long_term = tiers / "long-term"

    checks = []
    total_score = 0.0

    NOW = datetime(2026, 4, 20, 12, 0, 0)
    WORKING_THRESHOLD = 7
    SHORT_TERM_THRESHOLD = 30
    MAX_LEARNING_ROUNDS = 50
    MAX_CONVERSATIONS = 10

    # ── CHECK 1: config.json corrected ──────────────────────────────────────
    check_name = "config.json corrected per SKILL.md canonical values"
    try:
        config_path = tiers / "config.json"
        with open(config_path) as f:
            config = json.load(f)
        mm = config.get("memoryManager", {})

        errors = []
        if mm.get("workingMemoryDays") != 7:
            errors.append(f"workingMemoryDays={mm.get('workingMemoryDays')} (expected 7)")
        if mm.get("shortTermMemoryDays") != 30:
            errors.append(f"shortTermMemoryDays={mm.get('shortTermMemoryDays')} (expected 30)")
        if mm.get("maxLearningRounds") != 50:
            errors.append(f"maxLearningRounds={mm.get('maxLearningRounds')} (expected 50)")
        if mm.get("maxConversations") != 10:
            errors.append(f"maxConversations={mm.get('maxConversations')} (expected 10)")
        if mm.get("autoCompact") != True:
            errors.append(f"autoCompact={mm.get('autoCompact')} (expected true)")
        if mm.get("compactThreshold") != 0.7:
            errors.append(f"compactThreshold={mm.get('compactThreshold')} (expected 0.7)")
        if mm.get("mergeStrategy") != "summarize":
            errors.append(f"mergeStrategy={mm.get('mergeStrategy')} (expected 'summarize')")

        if not errors:
            checks.append({"name": check_name, "passed": True, "detail": "All 7 config values correctly set per SKILL.md"})
            total_score += 1.0
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"Config errors: {'; '.join(errors)}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 2: Working memory migration (>7 days → short-term) ────────────
    check_name = "Stale working-memory files (>7 days) migrated to short-term tier"
    try:
        # Files that were >7 days old: zeta(8d), eta(10d), theta(15d), iota(19d), kappa(29d)
        stale_from_working = ["session-20260412-zeta.json", "session-20260410-eta.json",
                               "session-20260405-theta.json", "session-20260401-iota.json",
                               "session-20260322-kappa.json"]
        # Files that should stay in working: alpha(1d), beta(2d), gamma(5d), delta(6d), epsilon(7d)
        fresh_in_working = ["session-20260419-alpha.json", "session-20260418-beta.json",
                            "session-20260415-gamma.json", "session-20260414-delta.json",
                            "session-20260413-epsilon.json"]

        migrated_ok = []
        not_migrated = []
        for fname in stale_from_working:
            # Should NOT be in working/, SHOULD be in short-term/ or long-term/
            in_working = (working / fname).exists()
            in_short = (short_term / fname).exists()
            in_long = (long_term / fname).exists()
            if not in_working and (in_short or in_long):
                migrated_ok.append(fname)
            else:
                not_migrated.append(f"{fname}(in_working={in_working},in_short={in_short},in_long={in_long})")

        fresh_ok = []
        fresh_missing = []
        for fname in fresh_in_working:
            if (working / fname).exists():
                fresh_ok.append(fname)
            else:
                fresh_missing.append(fname)

        passed = len(migrated_ok) >= 4 and len(fresh_missing) == 0
        detail = (f"Migrated {len(migrated_ok)}/5 stale files; "
                  f"Fresh files preserved: {len(fresh_ok)}/5. "
                  f"Not migrated: {not_migrated}; Missing fresh: {fresh_missing}")
        checks.append({"name": check_name, "passed": passed, "detail": detail})
        if passed:
            total_score += 1.0
        elif len(migrated_ok) >= 2:
            total_score += 0.4
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 3: Short-term migration (>30 days → long-term) ────────────────
    check_name = "Stale short-term files (>30 days) migrated to long-term tier"
    try:
        # Files >30 days old in short-term: 002(31d), 003(36d), 004(41d), 005(50d), 006(59d), 007(69d)
        stale_from_short = ["memo-20260320-002.json", "memo-20260315-003.json",
                            "memo-20260310-004.json", "memo-20260301-005.json",
                            "memo-20260220-006.json", "memo-20260210-007.json"]
        # Files <=30 days: 001(26d) stays in short-term
        fresh_in_short = ["memo-20260325-001.json"]

        migrated_ok = []
        not_migrated = []
        for fname in stale_from_short:
            in_short = (short_term / fname).exists()
            in_long = (long_term / fname).exists()
            if not in_short and in_long:
                migrated_ok.append(fname)
            else:
                not_migrated.append(f"{fname}(in_short={in_short},in_long={in_long})")

        fresh_ok = all((short_term / f).exists() for f in fresh_in_short)

        passed = len(migrated_ok) >= 5 and fresh_ok
        detail = (f"Migrated {len(migrated_ok)}/6 stale short-term files to long-term. "
                  f"Fresh short-term preserved: {fresh_ok}. "
                  f"Not migrated: {not_migrated}")
        checks.append({"name": check_name, "passed": passed, "detail": detail})
        if passed:
            total_score += 1.0
        elif len(migrated_ok) >= 3:
            total_score += 0.4
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 4: Learning rounds pruned to most recent 50 ───────────────────
    check_name = "Learning rounds pruned: only most recent 50 kept (rounds 29-78)"
    try:
        all_rounds = list(memory.glob("learning-round-*.json"))
        round_numbers = []
        for f in all_rounds:
            try:
                n = int(f.stem.replace("learning-round-", ""))
                round_numbers.append(n)
            except ValueError:
                pass
        round_numbers.sort()

        # Rounds 1-28 should be DELETED; rounds 29-78 should be KEPT
        deleted_old = [n for n in range(1, 29) if n not in round_numbers]
        kept_new = [n for n in range(29, 79) if n in round_numbers]
        spurious_deletions = [n for n in range(29, 79) if n not in round_numbers]
        remaining_old = [n for n in range(1, 29) if n in round_numbers]

        total_remaining = len(round_numbers)
        passed = (len(deleted_old) >= 25 and  # at least 25 of 28 old rounds deleted
                  len(kept_new) >= 48 and      # at least 48 of 50 new rounds kept
                  total_remaining <= 52)        # no more than 52 rounds total

        detail = (f"Total remaining rounds: {total_remaining}. "
                  f"Old rounds (1-28) deleted: {len(deleted_old)}/28. "
                  f"New rounds (29-78) kept: {len(kept_new)}/50. "
                  f"Spurious deletions from new range: {spurious_deletions}. "
                  f"Old rounds still present: {remaining_old}")
        checks.append({"name": check_name, "passed": passed, "detail": detail})
        if passed:
            total_score += 1.0
        elif len(deleted_old) >= 10:
            total_score += 0.3
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 5: Conversations pruned to most recent 10 ──────────────────────
    check_name = "Conversations pruned: only most recent 10 kept (conv 14-23)"
    try:
        all_convs = list(memory.glob("conversation-*.json"))
        conv_numbers = []
        for f in all_convs:
            stem = f.stem.replace("conversation-", "")
            try:
                n = int(stem)
                conv_numbers.append(n)
            except ValueError:
                pass
        conv_numbers.sort()

        # Convs 1-13 should be DELETED; convs 14-23 should be KEPT
        deleted_old = [n for n in range(1, 14) if n not in conv_numbers]
        kept_new = [n for n in range(14, 24) if n in conv_numbers]
        remaining_old = [n for n in range(1, 14) if n in conv_numbers]
        total_remaining = len(conv_numbers)

        passed = (len(deleted_old) >= 11 and   # at least 11 of 13 old convs deleted
                  len(kept_new) >= 9 and        # at least 9 of 10 new convs kept
                  total_remaining <= 12)         # no more than 12 conversations total

        detail = (f"Total remaining conversations: {total_remaining}. "
                  f"Old convs (1-13) deleted: {len(deleted_old)}/13. "
                  f"New convs (14-23) kept: {len(kept_new)}/10. "
                  f"Old convs still present: {remaining_old}")
        checks.append({"name": check_name, "passed": passed, "detail": detail})
        if passed:
            total_score += 1.0
        elif len(deleted_old) >= 5:
            total_score += 0.3
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 6: MEMORY.md preserved ────────────────────────────────────────
    check_name = "MEMORY.md main file preserved (never deleted)"
    try:
        memory_md = memory / "MEMORY.md"
        if memory_md.exists():
            content = memory_md.read_text()
            if "OpenClaw" in content and len(content) > 100:
                checks.append({"name": check_name, "passed": True, "detail": "MEMORY.md exists and contains expected content"})
                total_score += 0.5
            else:
                checks.append({"name": check_name, "passed": False, "detail": "MEMORY.md exists but content appears corrupted or truncated"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "MEMORY.md was deleted - this file must ALWAYS be preserved"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 7: Archive report generated ───────────────────────────────────
    check_name = "Memory archive report (memory-archive-report.json) generated with correct structure"
    try:
        # Search for the archive report anywhere in memory directory
        report_candidates = list(memory.rglob("memory-archive-report.json"))
        if not report_candidates:
            # Also check workspace root
            report_candidates = list(ws.rglob("memory-archive-report.json"))

        if not report_candidates:
            checks.append({"name": check_name, "passed": False, "detail": "memory-archive-report.json not found anywhere in workspace"})
        else:
            report_path = report_candidates[0]
            with open(report_path) as f:
                report = json.load(f)

            issues = []
            # Must be a dict/object
            if not isinstance(report, dict):
                issues.append("Report must be a JSON object")

            # Should contain summary of what was migrated/deleted
            content_str = json.dumps(report).lower()
            has_migration_info = any(kw in content_str for kw in
                                     ["migrat", "moved", "transfer", "working", "short", "long"])
            has_deletion_info = any(kw in content_str for kw in
                                    ["delet", "pruned", "remov", "clean"])
            has_counts = any(isinstance(v, (int, float)) for v in
                            _flatten_values(report) if isinstance(v, (int, float)))

            if not has_migration_info:
                issues.append("Report lacks migration/tier-movement information")
            if not has_deletion_info:
                issues.append("Report lacks deletion/pruning information")

            passed = len(issues) == 0 and has_migration_info
            detail = (f"Report found at {report_path.relative_to(ws)}. "
                      f"Has migration info: {has_migration_info}. "
                      f"Has deletion info: {has_deletion_info}. "
                      f"Issues: {issues}")
            checks.append({"name": check_name, "passed": passed, "detail": detail})
            if passed:
                total_score += 0.5
            elif has_migration_info or has_deletion_info:
                total_score += 0.25
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # ── Final scoring ────────────────────────────────────────────────────────
    max_score = 6.0
    normalized = round(total_score / max_score, 3)
    all_passed = all(c["passed"] for c in checks)

    # Require at least checks 1, 4, 5 to pass for overall pass
    critical_checks = [checks[0]["passed"], checks[3]["passed"], checks[4]["passed"]]
    overall_passed = all(critical_checks) and normalized >= 0.6

    return {
        "passed": overall_passed,
        "score": normalized,
        "checks": checks
    }


def _flatten_values(obj):
    """Recursively yield all scalar values from a nested dict/list."""
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _flatten_values(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _flatten_values(item)
    else:
        yield obj


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))