#!/usr/bin/env python3
"""
Evaluate agent's memory defragmentation workflow.
Checks:
1. defragment-plan.md was generated (--plan was run)
2. Backups exist (safety rule enforced)
3. HOT tier file (memory.md) is within 100-line limit
4. All WARM tier files are within 200-line limit
5. Archive directory contains newly archived stale entries
6. No stale (30+ day) entries remain in HOT/WARM files
7. No duplicate entries remain in any tier file
8. verification_result.json exists (verify step was run)
9. verification_result.json reports passed=true
"""

import sys
import os
import json
import re
from pathlib import Path
from datetime import datetime

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg_check", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    checks = []
    STALE_DAYS = 30
    today = datetime.now().date()

    def check(name, passed, detail=""):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ----------------------------------------------------------------
    # CHECK 1: defragment-plan.md exists
    # ----------------------------------------------------------------
    plan_path = os.path.join(workspace, "defragment-plan.md")
    try:
        with open(plan_path) as f:
            plan_content = f.read()
        check("plan_generated", True, f"defragment-plan.md exists ({len(plan_content)} chars)")
    except Exception as e:
        check("plan_generated", False, f"defragment-plan.md missing: {e}")

    # ----------------------------------------------------------------
    # CHECK 2: Backups exist (safety rule: always backup before executing)
    # ----------------------------------------------------------------
    backup_dir = os.path.join(workspace, "backups")
    try:
        bak_files = [f for f in os.listdir(backup_dir) if f.endswith(".bak")]
        has_backups = len(bak_files) > 0
        check("backups_created", has_backups,
              f"Found {len(bak_files)} .bak files: {bak_files[:3]}" if has_backups else "No .bak files in backups/")
    except Exception as e:
        check("backups_created", False, f"Could not read backups dir: {e}")

    # ----------------------------------------------------------------
    # CHECK 3: HOT tier limit — memory.md <= 100 lines
    # ----------------------------------------------------------------
    hot_path = os.path.join(workspace, "memory.md")
    try:
        with open(hot_path) as f:
            hot_lines = f.readlines()
        hot_count = len(hot_lines)
        within_hot = hot_count <= 100
        check("hot_tier_within_limit", within_hot,
              f"memory.md has {hot_count} lines (limit=100)")
    except Exception as e:
        check("hot_tier_within_limit", False, f"Could not read memory.md: {e}")
        hot_lines = []
        hot_count = 9999

    # ----------------------------------------------------------------
    # CHECK 4: WARM tier limits — each memory/*.md <= 200 lines
    # ----------------------------------------------------------------
    warm_files = [
        os.path.join(workspace, "memory", "domains.md"),
        os.path.join(workspace, "memory", "protocols.md"),
        os.path.join(workspace, "memory", "researcher_notes.md"),
    ]
    warm_violations = []
    for wf in warm_files:
        try:
            with open(wf) as f:
                wlines = f.readlines()
            wcount = len(wlines)
            if wcount > 200:
                warm_violations.append(f"{os.path.basename(wf)}: {wcount} lines")
        except Exception as e:
            warm_violations.append(f"{os.path.basename(wf)}: unreadable ({e})")
    check("warm_tier_within_limits", len(warm_violations) == 0,
          "All WARM files within 200 lines" if not warm_violations else f"Violations: {warm_violations}")

    # ----------------------------------------------------------------
    # CHECK 5: Archive has newly created content (stale entries archived)
    # ----------------------------------------------------------------
    archive_dir = os.path.join(workspace, "archive")
    try:
        arch_files = os.listdir(archive_dir)
        # We pre-created one old archive file; new ones should have been created by execution
        # Count files that contain "Archived from" (written by defragment.py --execute)
        new_arch_files = []
        for af in arch_files:
            afp = os.path.join(archive_dir, af)
            try:
                with open(afp) as ff:
                    content = ff.read()
                if "Archived from" in content:
                    new_arch_files.append(af)
            except Exception:
                pass
        check("archive_has_new_content", len(new_arch_files) > 0,
              f"Found {len(new_arch_files)} newly archived files: {new_arch_files[:3]}" if new_arch_files
              else "No newly archived files found in archive/")
    except Exception as e:
        check("archive_has_new_content", False, f"Could not read archive dir: {e}")

    # ----------------------------------------------------------------
    # CHECK 6: No stale entries (30+ days old) remain in HOT/WARM files
    # ----------------------------------------------------------------
    all_tier_files = [hot_path] + warm_files
    stale_found = []
    for tf in all_tier_files:
        try:
            with open(tf) as f:
                lines = f.readlines()
            for line in lines:
                m = re.search(r'\[added:(\d{4}-\d{2}-\d{2})\]', line)
                if m:
                    added = datetime.strptime(m.group(1), '%Y-%m-%d').date()
                    age = (today - added).days
                    if age >= STALE_DAYS:
                        stale_found.append(f"{os.path.basename(tf)}: '{line.strip()[:60]}' (age={age}d)")
        except Exception:
            pass

    # Allow small tolerance: if the execution removed >90% of original stale entries it passes
    # Count original stale in plan
    try:
        plan_stale_match = re.search(r'Total entries to archive:\s*(\d+)', plan_content)
        planned_stale = int(plan_stale_match.group(1)) if plan_stale_match else 0
    except Exception:
        planned_stale = 0

    stale_ok = len(stale_found) == 0
    check("stale_entries_archived",
          stale_ok,
          f"0 stale entries remain" if stale_ok else
          f"{len(stale_found)} stale entries still present (sample: {stale_found[:2]})")

    # ----------------------------------------------------------------
    # CHECK 7: No duplicate entries remain in any tier file
    # ----------------------------------------------------------------
    dup_violations = []
    for tf in all_tier_files:
        try:
            with open(tf) as f:
                lines = f.readlines()
            texts = []
            for line in lines:
                m = re.search(r'\[added:\d{4}-\d{2}-\d{2}\](.*)', line)
                if m:
                    texts.append(m.group(1).strip())
            dups = len(texts) - len(set(texts))
            if dups > 0:
                dup_violations.append(f"{os.path.basename(tf)}: {dups} duplicates")
        except Exception as e:
            dup_violations.append(f"{os.path.basename(tf)}: unreadable ({e})")

    check("no_duplicates_remain", len(dup_violations) == 0,
          "No duplicates in any tier file" if not dup_violations else
          f"Duplicate violations: {dup_violations}")

    # ----------------------------------------------------------------
    # CHECK 8: verification_result.json exists (verify step was run)
    # ----------------------------------------------------------------
    verify_path = os.path.join(workspace, "verification_result.json")
    try:
        with open(verify_path) as f:
            verify_data = json.load(f)
        check("verify_step_run", True, f"verification_result.json found, passed={verify_data.get('passed')}")
    except Exception as e:
        check("verify_step_run", False, f"verification_result.json missing or invalid: {e}")
        verify_data = {}

    # ----------------------------------------------------------------
    # CHECK 9: verification reports passed=true
    # ----------------------------------------------------------------
    try:
        verify_passed = verify_data.get("passed", False)
        check("verify_passed", bool(verify_passed),
              f"verify_memory.py reported: passed={verify_passed}")
    except Exception as e:
        check("verify_passed", False, f"Could not evaluate verify result: {e}")

    # ----------------------------------------------------------------
    # SCORING
    # ----------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)

    # Overall pass: must pass critical checks
    critical = ["plan_generated", "backups_created", "hot_tier_within_limit",
                "warm_tier_within_limits", "archive_has_new_content", "verify_step_run"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    overall_passed = critical_passed and score >= 0.78

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()