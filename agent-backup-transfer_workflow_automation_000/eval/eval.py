#!/usr/bin/env python3
"""
Evaluation script for openclaw-backup skill task.
Checks:
1. Exactly 10 backups exist in ~/openclaw-backups/ after the agent's create run
2. A NEW backup with today's timestamp pattern exists
3. The OLDEST pre-seeded backup was pruned (rotation logic)
4. The new backup is a valid tarball containing key workspace files
5. The new backup EXCLUDES logs, temp, node_modules, .git directories
"""

import sys
import json
import os
import re
import tarfile
import io
from pathlib import Path
from datetime import datetime

def main():
    workspace_arg = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~")
    HOME = Path(os.path.expanduser("~"))
    BACKUPS_DIR = HOME / "openclaw-backups"

    checks = []
    overall_passed = True

    # ----------------------------------------------------------------
    # Load eval metadata
    # ----------------------------------------------------------------
    oldest_backup_name = None
    preseeded_names = []
    try:
        oldest_backup_name = (HOME / ".eval_oldest_backup.txt").read_text().strip()
        preseeded_names = json.loads((HOME / ".eval_preseeded_backups.json").read_text())
    except Exception as e:
        checks.append({
            "name": "eval_metadata_load",
            "passed": False,
            "detail": f"Could not load eval metadata: {e}"
        })
        overall_passed = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ----------------------------------------------------------------
    # Check 1: Exactly 10 backups exist in ~/openclaw-backups/
    # ----------------------------------------------------------------
    try:
        backup_files = sorted(BACKUPS_DIR.glob("openclaw-backup-*.tar.gz"))
        backup_names = [f.name for f in backup_files]
        count = len(backup_files)
        passed = (count == 10)
        checks.append({
            "name": "backup_count_is_10",
            "passed": passed,
            "detail": f"Found {count} backups in {BACKUPS_DIR}. Expected exactly 10 (10 pre-existing + 1 new - 1 pruned). Files: {backup_names}"
        })
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "backup_count_is_10", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # ----------------------------------------------------------------
    # Check 2: A NEW backup exists (not one of the 10 pre-seeded ones)
    # ----------------------------------------------------------------
    new_backup_path = None
    try:
        backup_files_list = sorted(BACKUPS_DIR.glob("openclaw-backup-*.tar.gz"))
        backup_names_set = {f.name for f in backup_files_list}
        new_backups = [n for n in backup_names_set if n not in set(preseeded_names)]
        
        # Also check naming pattern: openclaw-backup-YYYY-MM-DD_HHMMSS.tar.gz
        pattern = re.compile(r"^openclaw-backup-\d{4}-\d{2}-\d{2}_\d{6}\.tar\.gz$")
        valid_new = [n for n in new_backups if pattern.match(n)]
        
        passed = len(valid_new) >= 1
        if passed:
            # Pick the newest for further checks
            new_backup_path = BACKUPS_DIR / valid_new[0]
        checks.append({
            "name": "new_backup_created_with_correct_name",
            "passed": passed,
            "detail": f"New backups found (not pre-seeded): {new_backups}. Valid pattern matches: {valid_new}"
        })
        if not passed:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "new_backup_created_with_correct_name", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # ----------------------------------------------------------------
    # Check 3: Oldest pre-seeded backup was PRUNED
    # ----------------------------------------------------------------
    try:
        backup_files_list = sorted(BACKUPS_DIR.glob("openclaw-backup-*.tar.gz"))
        current_names = {f.name for f in backup_files_list}
        oldest_was_pruned = oldest_backup_name not in current_names
        checks.append({
            "name": "oldest_backup_pruned",
            "passed": oldest_was_pruned,
            "detail": (
                f"Oldest pre-seeded backup '{oldest_backup_name}' "
                f"{'was correctly removed' if oldest_was_pruned else 'still exists — pruning logic did not trigger correctly'}. "
                f"Current backups: {sorted(current_names)}"
            )
        })
        if not oldest_was_pruned:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "oldest_backup_pruned", "passed": False, "detail": f"Exception: {e}"})
        overall_passed = False

    # ----------------------------------------------------------------
    # Check 4: New backup is a valid tarball with expected workspace files
    # ----------------------------------------------------------------
    if new_backup_path and new_backup_path.exists():
        try:
            required_paths = [
                ".openclaw/workspace/identity.json",
                ".openclaw/workspace/memories/core.json",
            ]
            found_paths = set()
            with tarfile.open(new_backup_path, "r:gz") as tf:
                all_names = tf.getnames()
                for rp in required_paths:
                    if rp in all_names:
                        found_paths.add(rp)

            missing = [rp for rp in required_paths if rp not in found_paths]
            passed = len(missing) == 0
            checks.append({
                "name": "backup_contains_key_workspace_files",
                "passed": passed,
                "detail": (
                    f"Required paths found: {sorted(found_paths)}. "
                    f"Missing: {missing}. "
                    f"Total entries in archive: {len(all_names)}"
                )
            })
            if not passed:
                overall_passed = False

            # Validate identity content
            try:
                with tarfile.open(new_backup_path, "r:gz") as tf:
                    member = tf.getmember(".openclaw/workspace/identity.json")
                    f = tf.extractfile(member)
                    identity_data = json.loads(f.read().decode())
                    name_ok = identity_data.get("name") == "Axiom"
                    checks.append({
                        "name": "identity_content_correct",
                        "passed": name_ok,
                        "detail": f"identity.json name field = '{identity_data.get('name')}' (expected 'Axiom')"
                    })
                    if not name_ok:
                        overall_passed = False
            except Exception as e2:
                checks.append({"name": "identity_content_correct", "passed": False, "detail": f"Exception reading identity: {e2}"})
                overall_passed = False

        except Exception as e:
            checks.append({"name": "backup_contains_key_workspace_files", "passed": False, "detail": f"Exception opening tarball: {e}"})
            overall_passed = False
    else:
        checks.append({
            "name": "backup_contains_key_workspace_files",
            "passed": False,
            "detail": "Skipped — no new backup file found to inspect."
        })
        overall_passed = False

    # ----------------------------------------------------------------
    # Check 5: New backup EXCLUDES logs, temp, node_modules, .git
    # ----------------------------------------------------------------
    if new_backup_path and new_backup_path.exists():
        try:
            excluded_patterns = ["logs/", "temp/", "node_modules/", ".git/"]
            violations = []
            with tarfile.open(new_backup_path, "r:gz") as tf:
                all_names = tf.getnames()
                for name in all_names:
                    for pat in excluded_patterns:
                        if pat in name:
                            violations.append(name)
                            break

            passed = len(violations) == 0
            checks.append({
                "name": "backup_excludes_logs_temp_node_modules_git",
                "passed": passed,
                "detail": (
                    f"{'No excluded paths found in archive.' if passed else f'Found {len(violations)} excluded path(s): {violations[:10]}'}"
                )
            })
            if not passed:
                overall_passed = False
        except Exception as e:
            checks.append({"name": "backup_excludes_logs_temp_node_modules_git", "passed": False, "detail": f"Exception: {e}"})
            overall_passed = False
    else:
        checks.append({
            "name": "backup_excludes_logs_temp_node_modules_git",
            "passed": False,
            "detail": "Skipped — no new backup file found to inspect."
        })
        overall_passed = False

    # ----------------------------------------------------------------
    # Final scoring
    # ----------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()