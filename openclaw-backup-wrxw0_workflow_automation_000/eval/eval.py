import sys
import os
import json
import hashlib
import tarfile
import re
from pathlib import Path

def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

def run_checks(workspace: str):
    checks = []
    HOME = Path("/root")
    BACKUP_DIR = HOME / "openclaw-backups"

    # ── CHECK 1: A new "skills" type backup was created ──────────────────────
    try:
        # Must match openclaw_skills_{TIMESTAMP}.tar.gz pattern
        pattern = re.compile(r'^openclaw_skills_\d{8}_\d{6}\.tar\.gz$')
        all_tgz = list(BACKUP_DIR.glob("openclaw_skills_*.tar.gz"))
        
        # Original 5 old timestamps
        old_timestamps = {
            "openclaw_skills_20250101_020000.tar.gz",
            "openclaw_skills_20250215_020000.tar.gz",
            "openclaw_skills_20250310_020000.tar.gz",
            "openclaw_skills_20250401_020000.tar.gz",
            "openclaw_skills_20250510_020000.tar.gz",
        }
        
        new_archives = [
            f for f in all_tgz
            if f.name not in old_timestamps and pattern.match(f.name)
        ]
        
        if new_archives:
            checks.append({
                "name": "new_skills_backup_created",
                "passed": True,
                "detail": f"Found new skills backup(s): {[f.name for f in new_archives]}"
            })
            new_backup = sorted(new_archives, key=lambda f: f.stat().st_mtime, reverse=True)[0]
        else:
            checks.append({
                "name": "new_skills_backup_created",
                "passed": False,
                "detail": f"No new 'openclaw_skills_YYYYMMDD_HHMMSS.tar.gz' found in {BACKUP_DIR}. Files: {[f.name for f in all_tgz]}"
            })
            new_backup = None
    except Exception as e:
        checks.append({"name": "new_skills_backup_created", "passed": False, "detail": f"Exception: {e}"})
        new_backup = None

    # ── CHECK 2: Archive contains .claude/skills AND .claude/commands (relative paths, -C $HOME) ──
    try:
        if new_backup and new_backup.exists():
            with tarfile.open(new_backup, 'r:gz') as tf:
                members = tf.getnames()
            
            has_skills = any(m.startswith('.claude/skills') for m in members)
            has_commands = any(m.startswith('.claude/commands') for m in members)
            
            # Must NOT have absolute paths (i.e., not /root/.claude/...)
            has_absolute = any(m.startswith('/') for m in members)
            
            all_ok = has_skills and has_commands and not has_absolute
            detail = (
                f"has_skills={has_skills}, has_commands={has_commands}, "
                f"has_absolute_paths={has_absolute}. "
                f"Sample members: {members[:8]}"
            )
            checks.append({
                "name": "archive_contains_skills_and_commands_relative_paths",
                "passed": all_ok,
                "detail": detail
            })
        else:
            checks.append({
                "name": "archive_contains_skills_and_commands_relative_paths",
                "passed": False,
                "detail": "No new backup found to inspect."
            })
    except Exception as e:
        checks.append({
            "name": "archive_contains_skills_and_commands_relative_paths",
            "passed": False,
            "detail": f"Exception reading archive: {e}"
        })

    # ── CHECK 3: SHA256 sidecar file created for the new backup ──────────────
    try:
        if new_backup and new_backup.exists():
            sha_file = BACKUP_DIR / f"{new_backup.name}.sha256"
            if sha_file.exists():
                sha_content = sha_file.read_text().strip()
                # Expected: "<hash>  <filename>" or "<hash> <filename>"
                expected_hash = sha256_of_file(new_backup)
                
                # Parse the sha256 file
                parts = sha_content.split()
                if len(parts) >= 2:
                    recorded_hash = parts[0]
                    hash_matches = (recorded_hash.lower() == expected_hash.lower())
                    checks.append({
                        "name": "sha256_sidecar_file_correct",
                        "passed": hash_matches,
                        "detail": f"sha256 file exists. recorded={recorded_hash[:16]}..., expected={expected_hash[:16]}..., match={hash_matches}"
                    })
                else:
                    # Maybe it's just the hash without filename
                    hash_only = sha_content.strip().lower()
                    hash_matches = (hash_only == expected_hash.lower())
                    checks.append({
                        "name": "sha256_sidecar_file_correct",
                        "passed": hash_matches,
                        "detail": f"sha256 file exists (hash-only format). match={hash_matches}"
                    })
            else:
                checks.append({
                    "name": "sha256_sidecar_file_correct",
                    "passed": False,
                    "detail": f"Expected sha256 file at {sha_file} but not found."
                })
        else:
            checks.append({
                "name": "sha256_sidecar_file_correct",
                "passed": False,
                "detail": "No new backup to check sha256 for."
            })
    except Exception as e:
        checks.append({
            "name": "sha256_sidecar_file_correct",
            "passed": False,
            "detail": f"Exception checking sha256: {e}"
        })

    # ── CHECK 4: Cleanup/rotation enforced — only 3 most recent backups remain ──
    # The task specifies MAX_BACKUPS=3. We started with 5 old + 1 new = 6.
    # After cleanup with MAX=3, only the 3 newest should remain.
    try:
        all_remaining = sorted(
            list(BACKUP_DIR.glob("openclaw_skills_*.tar.gz")),
            key=lambda f: f.stat().st_mtime,
            reverse=True  # newest first
        )
        remaining_count = len(all_remaining)
        
        if remaining_count <= 3:
            checks.append({
                "name": "backup_rotation_max_3_enforced",
                "passed": True,
                "detail": f"Correct: {remaining_count} backup(s) remain (≤3). Files: {[f.name for f in all_remaining]}"
            })
        else:
            checks.append({
                "name": "backup_rotation_max_3_enforced",
                "passed": False,
                "detail": f"Expected ≤3 backups after rotation, but found {remaining_count}: {[f.name for f in all_remaining]}"
            })
    except Exception as e:
        checks.append({
            "name": "backup_rotation_max_3_enforced",
            "passed": False,
            "detail": f"Exception checking backup count: {e}"
        })

    # ── CHECK 5: The newest backup IS among the survivors ──────────────────────
    try:
        all_remaining_names = {f.name for f in BACKUP_DIR.glob("openclaw_skills_*.tar.gz")}
        if new_backup and new_backup.name in all_remaining_names:
            checks.append({
                "name": "newest_backup_retained",
                "passed": True,
                "detail": f"New backup {new_backup.name} was kept after rotation."
            })
        elif new_backup is None:
            checks.append({
                "name": "newest_backup_retained",
                "passed": False,
                "detail": "No new backup was created, so cannot check retention."
            })
        else:
            checks.append({
                "name": "newest_backup_retained",
                "passed": False,
                "detail": f"New backup {new_backup.name} was deleted during rotation — oldest should be removed, not newest."
            })
    except Exception as e:
        checks.append({
            "name": "newest_backup_retained",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── CHECK 6: Actual .claude/skills content is correctly archived ──────────
    try:
        if new_backup and new_backup.exists():
            with tarfile.open(new_backup, 'r:gz') as tf:
                members = set(tf.getnames())
            
            expected_paths = [
                ".claude/skills/code-review/SKILL.md",
                ".claude/skills/deploy-helper/SKILL.md",
                ".claude/skills/doc-writer/SKILL.md",
                ".claude/commands/review.md",
                ".claude/commands/deploy.md",
            ]
            
            found = [p for p in expected_paths if p in members]
            missing = [p for p in expected_paths if p not in members]
            
            passed = len(missing) == 0
            checks.append({
                "name": "archive_contains_actual_skill_files",
                "passed": passed,
                "detail": f"Found {len(found)}/{len(expected_paths)} expected files. Missing: {missing}"
            })
        else:
            checks.append({
                "name": "archive_contains_actual_skill_files",
                "passed": False,
                "detail": "No new backup to inspect for content."
            })
    except Exception as e:
        checks.append({
            "name": "archive_contains_actual_skill_files",
            "passed": False,
            "detail": f"Exception: {e}"
        })

    # ── SCORING ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0
    overall = passed_count >= 5  # must pass at least 5/6

    return {
        "passed": overall,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))