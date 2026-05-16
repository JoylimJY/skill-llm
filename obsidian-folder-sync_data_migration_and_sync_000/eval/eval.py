#!/usr/bin/env python3
"""
Evaluation script for the obsidian-folder-sync task.
Usage: python3 eval_script.py <workspace_dir>
"""

import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # ─── Expected configuration ───────────────────────────
    source_root = workspace / "bioproject" / "pipeline-docs"
    vault = workspace / "ObsidianVault"
    # Agent is asked to sync under "BioPipeline2024" subdirectory
    target_subdir = "BioPipeline2024"
    target_dir = vault / target_subdir

    # .md files that MUST be synced (relative to source_root, not in excluded dirs)
    expected_md_files = [
        "README.md",
        "setup.md",
        "usage.md",
        "CHANGELOG.md",
        "modules/alignment.md",
        "modules/variant-calling.md",
        "modules/qc.md",
        "protocols/sample-prep.md",
        "protocols/sequencing.md",
        "results/benchmarks.md",
        "results/validation.md",
    ]

    # .md files that MUST NOT be synced (from excluded dirs)
    excluded_md_files = [
        "node_modules/lodash/README.md",
        "node_modules/axios/CHANGELOG.md",
        "__pycache__/module.md",
        ".git/COMMIT_EDITMSG.md",
        ".venv/lib/python3.10/site-packages/README.md",
        ".clawhub/metadata.md",
        ".learnings/session-2024.md",
    ]

    # Non-.md files that MUST NOT be synced
    excluded_non_md = [
        "environment.yml",
        "run_pipeline.py",
        "config.json",
        "modules/alignment.py",
        "data/sample_list.txt",
        "results/metrics.tsv",
        "Snakefile",
        "scripts/preprocess.sh",
    ]

    # ─── CHECK 1: Target subdirectory exists ──────────────
    try:
        exists = target_dir.exists() and target_dir.is_dir()
        checks.append({
            "name": "target_subdir_BioPipeline2024_exists",
            "passed": exists,
            "detail": f"Expected {target_dir} to exist. Found: {exists}"
        })
    except Exception as e:
        checks.append({
            "name": "target_subdir_BioPipeline2024_exists",
            "passed": False,
            "detail": f"Exception checking target dir: {e}"
        })

    # ─── CHECK 2: All expected .md files are present ──────
    try:
        missing = []
        for rel in expected_md_files:
            dest = target_dir / rel
            if not dest.exists():
                missing.append(rel)
        passed = len(missing) == 0
        checks.append({
            "name": "all_expected_md_files_synced",
            "passed": passed,
            "detail": f"Missing {len(missing)}/{len(expected_md_files)} files: {missing[:5]}" if missing else f"All {len(expected_md_files)} expected .md files present."
        })
    except Exception as e:
        checks.append({
            "name": "all_expected_md_files_synced",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─── CHECK 3: Excluded dir .md files are NOT present ──
    try:
        leaked = []
        for rel in excluded_md_files:
            dest = target_dir / rel
            if dest.exists():
                leaked.append(rel)
        passed = len(leaked) == 0
        checks.append({
            "name": "excluded_dir_md_files_not_synced",
            "passed": passed,
            "detail": f"Leaked {len(leaked)} files from excluded dirs: {leaked}" if leaked else "No excluded-dir .md files leaked."
        })
    except Exception as e:
        checks.append({
            "name": "excluded_dir_md_files_not_synced",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─── CHECK 4: Non-.md files are NOT synced ────────────
    try:
        leaked_non_md = []
        for rel in excluded_non_md:
            dest = target_dir / rel
            if dest.exists():
                leaked_non_md.append(rel)
        passed = len(leaked_non_md) == 0
        checks.append({
            "name": "non_md_files_not_synced",
            "passed": passed,
            "detail": f"Non-.md files leaked: {leaked_non_md}" if leaked_non_md else "No non-.md files synced."
        })
    except Exception as e:
        checks.append({
            "name": "non_md_files_not_synced",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─── CHECK 5: Directory structure is preserved ─────────
    try:
        structure_checks = [
            target_dir / "modules",
            target_dir / "protocols",
            target_dir / "results",
        ]
        all_present = all(p.is_dir() for p in structure_checks)
        checks.append({
            "name": "directory_structure_preserved",
            "passed": all_present,
            "detail": f"Subdirectory structure in BioPipeline2024: {[str(p.name) for p in structure_checks if p.is_dir()]} present, {[str(p.name) for p in structure_checks if not p.is_dir()]} missing."
        })
    except Exception as e:
        checks.append({
            "name": "directory_structure_preserved",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─── CHECK 6: Content integrity of a synced file ──────
    try:
        alignment_md = target_dir / "modules" / "alignment.md"
        if alignment_md.exists():
            content = alignment_md.read_text()
            content_ok = "BWA-MEM2" in content and "Alignment Module" in content
            checks.append({
                "name": "synced_file_content_integrity",
                "passed": content_ok,
                "detail": f"modules/alignment.md content check: {'OK' if content_ok else 'Content mismatch or truncated'}."
            })
        else:
            checks.append({
                "name": "synced_file_content_integrity",
                "passed": False,
                "detail": "modules/alignment.md not found in target."
            })
    except Exception as e:
        checks.append({
            "name": "synced_file_content_integrity",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─── CHECK 7: Log file created at the correct path ────
    try:
        log_path = Path("/root/.openclaw/workspace/logs/obsidian-folder-sync.log")
        log_exists = log_path.exists()
        log_has_content = False
        log_mentions_sync = False
        if log_exists:
            log_content = log_path.read_text()
            log_has_content = len(log_content.strip()) > 0
            log_mentions_sync = "sync" in log_content.lower() or "pipeline-docs" in log_content.lower() or "BioPipeline2024" in log_content.lower()
        passed = log_exists and log_has_content and log_mentions_sync
        checks.append({
            "name": "log_file_created_at_correct_path",
            "passed": passed,
            "detail": f"Log exists: {log_exists}, has content: {log_has_content}, mentions sync: {log_mentions_sync}. Path: {log_path}"
        })
    except Exception as e:
        checks.append({
            "name": "log_file_created_at_correct_path",
            "passed": False,
            "detail": f"Exception checking log: {e}"
        })

    # ─── CHECK 8: Pre-existing vault content untouched ────
    try:
        daily_note = vault / "Daily Notes" / "2024-01-15.md"
        personal_goals = vault / "Personal" / "goals.md"
        untouched = daily_note.exists() and personal_goals.exists()
        checks.append({
            "name": "preexisting_vault_content_untouched",
            "passed": untouched,
            "detail": f"Pre-existing vault files preserved: daily_note={daily_note.exists()}, personal/goals={personal_goals.exists()}"
        })
    except Exception as e:
        checks.append({
            "name": "preexisting_vault_content_untouched",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ─── Scoring ──────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall_passed = passed_count == total

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "arg_check", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    evaluate(sys.argv[1])