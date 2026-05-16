#!/usr/bin/env python3
"""
Evaluation script for the Memoria System task.
Usage: python3 eval_script.py <workspace_dir>
"""
import sys
import os
import json
import glob
import subprocess
from pathlib import Path

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    memoria_dir = os.path.join(workspace, "memoria-system")
    memory_dir  = os.path.join(memoria_dir, "memory")

    checks = []
    total_score = 0.0
    max_checks  = 7  # we have 7 graded checks

    # ─────────────────────────────────────────────────────
    # CHECK 1: config.json is valid and complete
    # ─────────────────────────────────────────────────────
    try:
        config_path = os.path.join(memoria_dir, "config.json")
        with open(config_path) as f:
            cfg = json.load(f)

        has_memory    = "memory"       in cfg
        has_backup    = "backup"       in cfg
        has_health    = "health_check" in cfg
        has_base_path = cfg.get("memory", {}).get("base_path") is not None
        has_retention = cfg.get("backup", {}).get("retention_days") is not None
        has_auto_fix  = cfg.get("health_check", {}).get("auto_fix") is not None

        all_fields = all([has_memory, has_backup, has_health,
                          has_base_path, has_retention, has_auto_fix])
        passed = all_fields
        detail = (
            f"memory={has_memory}, backup={has_backup}, health_check={has_health}, "
            f"base_path={has_base_path}, retention_days={has_retention}, auto_fix={has_auto_fix}"
        )
        checks.append({"name": "config.json is valid and complete", "passed": passed, "detail": detail})
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "config.json is valid and complete", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────
    # CHECK 2: All required memory subdirectories exist (health-check --fix did its work)
    # ─────────────────────────────────────────────────────
    try:
        required_dirs = [
            "semantic/knowledge",
            "episodic/events",
            "procedural/scripts",
            "working/session",
            "index/search",
        ]
        missing = [d for d in required_dirs if not os.path.isdir(os.path.join(memory_dir, d))]
        passed = len(missing) == 0
        detail = f"Missing dirs: {missing}" if missing else "All required directories present"
        checks.append({"name": "All required memory subdirectories exist", "passed": passed, "detail": detail})
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "All required memory subdirectories exist", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────
    # CHECK 3: All required memory files exist
    # ─────────────────────────────────────────────────────
    try:
        required_files = [
            "semantic/facts.md",
            "semantic/concepts.md",
            "procedural/skills.md",
            "procedural/workflows.md",
            "working/current.md",
            "index/tags.json",
            "index/timeline.json",
        ]
        missing_files = [f for f in required_files if not os.path.isfile(os.path.join(memory_dir, f))]
        passed = len(missing_files) == 0
        detail = f"Missing files: {missing_files}" if missing_files else "All required files present"
        checks.append({"name": "All required memory files exist", "passed": passed, "detail": detail})
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "All required memory files exist", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────
    # CHECK 4: index/tags.json and index/timeline.json are valid JSON (not corrupted)
    # ─────────────────────────────────────────────────────
    try:
        errors = []
        for jfile in ["index/tags.json", "index/timeline.json"]:
            jpath = os.path.join(memory_dir, jfile)
            if os.path.isfile(jpath):
                try:
                    with open(jpath) as f:
                        json.load(f)
                except json.JSONDecodeError as je:
                    errors.append(f"{jfile}: {je}")
            else:
                errors.append(f"{jfile}: file missing")
        passed = len(errors) == 0
        detail = "; ".join(errors) if errors else "Both JSON index files are valid"
        checks.append({"name": "Index JSON files are valid (not corrupted)", "passed": passed, "detail": detail})
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "Index JSON files are valid (not corrupted)", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────
    # CHECK 5: episodic/2024-11-20.md daily log exists with non-trivial content
    # ─────────────────────────────────────────────────────
    try:
        daily_path = os.path.join(memory_dir, "episodic", "2024-11-20.md")
        if not os.path.isfile(daily_path):
            checks.append({
                "name": "Daily log episodic/2024-11-20.md exists",
                "passed": False,
                "detail": f"File not found: {daily_path}"
            })
        else:
            with open(daily_path) as f:
                content = f.read()
            has_date    = "2024-11-20" in content
            has_content = len(content.strip()) > 20
            passed = has_date and has_content
            detail = (
                f"File exists, length={len(content)}, "
                f"contains date={has_date}, has_content={has_content}"
            )
            checks.append({"name": "Daily log episodic/2024-11-20.md exists", "passed": passed, "detail": detail})
            if passed:
                total_score += 1
    except Exception as e:
        checks.append({"name": "Daily log episodic/2024-11-20.md exists", "passed": False, "detail": str(e)})
    else:
        if os.path.isfile(os.path.join(memory_dir, "episodic", "2024-11-20.md")):
            # already scored inside the else branch above
            pass
        else:
            pass  # already appended failed check

    # ─────────────────────────────────────────────────────
    # CHECK 6: A backup archive exists in the backups/ directory
    # ─────────────────────────────────────────────────────
    try:
        backup_dir = os.path.join(memoria_dir, "backups")
        backups = []
        if os.path.isdir(backup_dir):
            backups = [f for f in os.listdir(backup_dir) if f.endswith(".tar.gz")]

        # Also check any backup path specified in config
        try:
            with open(os.path.join(memoria_dir, "config.json")) as f:
                cfg2 = json.load(f)
            alt_backup = cfg2.get("backup", {}).get("output_path", "")
            if alt_backup:
                if not os.path.isabs(alt_backup):
                    alt_backup = os.path.join(memoria_dir, alt_backup)
                if os.path.isdir(alt_backup):
                    backups += [f for f in os.listdir(alt_backup) if f.endswith(".tar.gz")]
        except Exception:
            pass

        # Also search workspace-wide
        all_tgz = list(Path(workspace).rglob("memoria-backup-*.tar.gz"))

        passed = len(backups) > 0 or len(all_tgz) > 0
        detail = (
            f"Found {len(backups)} backup(s) in expected locations; "
            f"{len(all_tgz)} backup(s) found workspace-wide: "
            f"{[str(p) for p in all_tgz[:3]]}"
        )
        checks.append({"name": "A backup archive has been created", "passed": passed, "detail": detail})
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "A backup archive has been created", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────
    # CHECK 7: health-check repair log or evidence that --fix was used
    #   We accept: logs/health.log exists in memoria-system, OR
    #   all corrupted/missing structural items from setup are now present (already covered by checks 2-4)
    #   We give a bonus point if the health log exists explicitly.
    # ─────────────────────────────────────────────────────
    try:
        health_log = os.path.join(memoria_dir, "logs", "health.log")
        passed = os.path.isfile(health_log)
        if passed:
            with open(health_log) as f:
                log_content = f.read()
            detail = f"health.log found; content snippet: {log_content[:200]}"
        else:
            # Accept that if all structural checks pass, --fix was implicitly run
            struct_checks_passed = all(
                c["passed"] for c in checks
                if c["name"] in [
                    "All required memory subdirectories exist",
                    "All required memory files exist",
                    "Index JSON files are valid (not corrupted)"
                ]
            )
            if struct_checks_passed:
                passed = True
                detail = "health.log not found, but all structural issues repaired — --fix was applied"
            else:
                detail = "health.log not found and structural issues remain; --fix may not have been run"
        checks.append({"name": "memory-health-check.sh --fix was executed", "passed": passed, "detail": detail})
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "memory-health-check.sh --fix was executed", "passed": False, "detail": str(e)})

    # ─────────────────────────────────────────────────────
    # Final scoring
    # ─────────────────────────────────────────────────────
    # Re-deduplicate check 5 score (it was conditionally scored above, need to recount)
    # Recount from check results directly
    scored_names = {
        "config.json is valid and complete",
        "All required memory subdirectories exist",
        "All required memory files exist",
        "Index JSON files are valid (not corrupted)",
        "Daily log episodic/2024-11-20.md exists",
        "A backup archive has been created",
        "memory-health-check.sh --fix was executed",
    }
    total_score = sum(1 for c in checks if c["passed"] and c["name"] in scored_names)
    score = round(total_score / max_checks, 4)
    overall_passed = total_score >= 5  # pass threshold: 5 out of 7

    result = {
        "passed": overall_passed,
        "score":  score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()