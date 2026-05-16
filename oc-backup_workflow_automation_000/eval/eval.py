import sys
import json
import os
import tarfile
import re
from pathlib import Path
from datetime import datetime, timedelta

def main(workspace_dir):
    checks = []
    BACKUP_DIR = Path("/root/backups/openclaw")
    HOME = Path("/root")

    # ── Check 1: A new backup tar.gz exists with 'system' AND 'workspace' in the type ──
    def check_new_backup_exists():
        try:
            files = list(BACKUP_DIR.glob("openclaw-backup-*.tar.gz"))
            # Filter files created recently (not the old ones we pre-seeded)
            cutoff = datetime.now() - timedelta(days=2)
            recent = [f for f in files if f.stat().st_mtime > cutoff.timestamp()]
            
            if not recent:
                return False, f"No new tar.gz backup found in {BACKUP_DIR}. Found: {[f.name for f in files]}"
            
            # Check that at least one has both 'system' and 'workspace' in the type
            combined = [f for f in recent if 'system' in f.name and 'workspace' in f.name]
            if not combined:
                return False, (
                    f"No backup with combined 'system-workspace' type found. "
                    f"Recent backups: {[f.name for f in recent]}. "
                    "Expected a backup using --system --workspace flags (not --full)."
                )
            return True, f"Found combined backup: {combined[0].name}"
        except Exception as e:
            return False, f"Exception checking backup: {e}"

    passed, detail = check_new_backup_exists()
    checks.append({"name": "new_combined_system_workspace_backup_exists", "passed": passed, "detail": detail})

    # ── Check 2: The corresponding JSON manifest exists and has correct 'type' ──
    def check_manifest():
        try:
            files = list(BACKUP_DIR.glob("openclaw-backup-*.json"))
            cutoff = datetime.now() - timedelta(days=2)
            recent = [f for f in files if f.stat().st_mtime > cutoff.timestamp()]
            
            combined_json = [f for f in recent if 'system' in f.name and 'workspace' in f.name]
            if not combined_json:
                return False, f"No recent combined JSON manifest found. Recent manifests: {[f.name for f in recent]}"
            
            manifest_path = combined_json[0]
            with open(manifest_path) as fp:
                manifest = json.load(fp)
            
            mtype = manifest.get("type", "")
            if "system" not in mtype or "workspace" not in mtype:
                return False, f"Manifest 'type' field is '{mtype}', expected it to contain both 'system' and 'workspace'"
            
            cats = manifest.get("categories", [])
            if "system" not in cats or "workspace" not in cats:
                return False, f"Manifest 'categories' is {cats}, expected ['system', 'workspace']"
            
            file_count = manifest.get("fileCount", 0)
            if file_count < 5:
                return False, f"Manifest fileCount={file_count} seems too low for system+workspace backup (expected >=5 backed-up files)"
            
            # Check .env is marked sensitive
            env_entry = [e for e in manifest.get("files", []) if str(e.get("path","")).endswith(".env")]
            if env_entry and not env_entry[0].get("sensitive", False):
                return False, ".env file should be marked as sensitive=true in manifest"
            
            return True, f"Manifest OK: type='{mtype}', categories={cats}, fileCount={file_count}"
        except json.JSONDecodeError as e:
            return False, f"Manifest JSON parse error: {e}"
        except Exception as e:
            return False, f"Exception checking manifest: {e}"

    passed, detail = check_manifest()
    checks.append({"name": "json_manifest_correct_type_and_content", "passed": passed, "detail": detail})

    # ── Check 3: Output was placed in the correct custom directory ──
    def check_output_directory():
        try:
            # The task asks to output to /root/backups/openclaw (or custom path per task)
            # We verify backup files exist in BACKUP_DIR (the default or custom path)
            tar_files = list(BACKUP_DIR.glob("openclaw-backup-*.tar.gz"))
            cutoff = datetime.now() - timedelta(days=2)
            recent = [f for f in tar_files if f.stat().st_mtime > cutoff.timestamp()]
            if recent:
                return True, f"Backup correctly placed in {BACKUP_DIR} ({len(recent)} recent tar.gz files)"
            return False, f"No recent backups found in expected output dir {BACKUP_DIR}"
        except Exception as e:
            return False, f"Exception: {e}"

    passed, detail = check_output_directory()
    checks.append({"name": "backup_in_correct_output_directory", "passed": passed, "detail": detail})

    # ── Check 4: Old backups (>7 days) were deleted by --retain 7 ──
    def check_old_backups_cleaned():
        try:
            cutoff_7d = datetime.now() - timedelta(days=7)
            all_files = list(BACKUP_DIR.glob("openclaw-backup-*"))
            
            old_files = [f for f in all_files if f.stat().st_mtime < cutoff_7d.timestamp()]
            
            if old_files:
                return False, (
                    f"Found {len(old_files)} backup file(s) older than 7 days that should have been deleted by --retain 7: "
                    f"{[f.name for f in old_files]}"
                )
            return True, "All backups older than 7 days were successfully cleaned up."
        except Exception as e:
            return False, f"Exception checking old backups: {e}"

    passed, detail = check_old_backups_cleaned()
    checks.append({"name": "old_backups_cleaned_by_retain_7", "passed": passed, "detail": detail})

    # ── Check 5: The tar.gz is a valid archive containing system and workspace files ──
    def check_tarball_contents():
        try:
            files = list(BACKUP_DIR.glob("openclaw-backup-*.tar.gz"))
            cutoff = datetime.now() - timedelta(days=2)
            recent = [f for f in files if f.stat().st_mtime > cutoff.timestamp()]
            combined = [f for f in recent if 'system' in f.name and 'workspace' in f.name]
            
            if not combined:
                return False, "No combined tar.gz to inspect."
            
            tar_path = combined[0]
            with tarfile.open(tar_path, "r:gz") as tf:
                members = [m.name for m in tf.getmembers()]
            
            # Check for system config files
            system_files = [m for m in members if "openclaw.json" in m or "exec-approvals.json" in m]
            workspace_files = [m for m in members if any(x in m for x in ["AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md"])]
            
            if not system_files:
                return False, f"Tar has no system config files. Members: {members[:15]}"
            if not workspace_files:
                return False, f"Tar has no workspace core files. Members: {members[:15]}"
            
            return True, f"Tar contains system files: {system_files[:3]} and workspace files: {workspace_files[:3]}"
        except tarfile.TarError as e:
            return False, f"Tar read error: {e}"
        except Exception as e:
            return False, f"Exception: {e}"

    passed, detail = check_tarball_contents()
    checks.append({"name": "tarball_contains_system_and_workspace_files", "passed": passed, "detail": detail})

    # ── Check 6: RECOVERY_GUIDE.md was generated ──
    def check_recovery_guide():
        try:
            guide = BACKUP_DIR / "RECOVERY_GUIDE.md"
            if not guide.exists():
                return False, f"RECOVERY_GUIDE.md not found in {BACKUP_DIR}"
            content = guide.read_text()
            if len(content) < 20:
                return False, "RECOVERY_GUIDE.md is suspiciously short/empty"
            return True, "RECOVERY_GUIDE.md exists and has content."
        except Exception as e:
            return False, f"Exception: {e}"

    passed, detail = check_recovery_guide()
    checks.append({"name": "recovery_guide_generated", "passed": passed, "detail": detail})

    # ── Final scoring ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    result = {
        "passed": all(c["passed"] for c in checks),
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/root"
    main(ws)