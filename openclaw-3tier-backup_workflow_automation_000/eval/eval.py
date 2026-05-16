import sys
import json
import re
import subprocess
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 1: daily-backup.ps1 exists somewhere in workspace
    # ══════════════════════════════════════════════════════════════════════════
    backup_scripts = list(workspace.rglob("daily-backup.ps1"))
    if backup_scripts:
        backup_script = backup_scripts[0]
        score = add_check(
            "daily-backup.ps1 exists",
            True,
            f"Found at: {backup_script.relative_to(workspace)}"
        )
        total_score += score
        try:
            content = backup_script.read_text(errors="replace")
        except Exception as e:
            content = ""
            add_check("daily-backup.ps1 readable", False, str(e))
    else:
        total_score += add_check(
            "daily-backup.ps1 exists",
            False,
            "No file named 'daily-backup.ps1' found anywhere in workspace"
        )
        content = ""

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 2: WorkspacePath configured to /workspace/ai_workspace
    # ══════════════════════════════════════════════════════════════════════════
    try:
        has_workspace = bool(re.search(
            r'\$WorkspacePath\s*=\s*["\']?/workspace/ai_workspace["\']?',
            content, re.IGNORECASE
        ))
        total_score += add_check(
            "$WorkspacePath set to /workspace/ai_workspace",
            has_workspace,
            "$WorkspacePath correctly configured" if has_workspace
            else f"$WorkspacePath not set to /workspace/ai_workspace. Content snippet: {content[:300]}"
        )
    except Exception as e:
        total_score += add_check("$WorkspacePath set", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 3: BackupDir configured to /workspace/backups_dir
    # ══════════════════════════════════════════════════════════════════════════
    try:
        has_backupdir = bool(re.search(
            r'\$BackupDir\s*=\s*["\']?/workspace/backups_dir["\']?',
            content, re.IGNORECASE
        ))
        total_score += add_check(
            "$BackupDir set to /workspace/backups_dir",
            has_backupdir,
            "$BackupDir correctly configured" if has_backupdir
            else "$BackupDir not set to /workspace/backups_dir"
        )
    except Exception as e:
        total_score += add_check("$BackupDir set", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 4: MirrorPath configured to /workspace/mirror_drive
    # ══════════════════════════════════════════════════════════════════════════
    try:
        has_mirror = bool(re.search(
            r'\$MirrorPath\s*=\s*["\']?/workspace/mirror_drive["\']?',
            content, re.IGNORECASE
        ))
        total_score += add_check(
            "$MirrorPath set to /workspace/mirror_drive",
            has_mirror,
            "$MirrorPath correctly configured" if has_mirror
            else "$MirrorPath not set to /workspace/mirror_drive"
        )
    except Exception as e:
        total_score += add_check("$MirrorPath set", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 5: RetentionDays = 7 (the exact default from the skill)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        has_retention = bool(re.search(
            r'\$RetentionDays\s*=\s*7\b',
            content, re.IGNORECASE
        ))
        total_score += add_check(
            "$RetentionDays set to 7",
            has_retention,
            "$RetentionDays = 7 found" if has_retention
            else "$RetentionDays not set to 7 (the skill default). Check if it's missing or set to another value."
        )
    except Exception as e:
        total_score += add_check("$RetentionDays set", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 6: Backup zip named with backup-YYYY-MM-DD.zip pattern
    # ══════════════════════════════════════════════════════════════════════════
    try:
        # Must see the naming pattern from the SKILL.md restore procedure
        has_zip_naming = bool(re.search(
            r'backup-.*\.(zip)',
            content, re.IGNORECASE
        ))
        # Also accept format strings that would produce this pattern
        has_format_str = bool(re.search(
            r'backup-.*(?:yyyy|MM|dd|Get-Date|date)',
            content, re.IGNORECASE
        ))
        passed_naming = has_zip_naming or has_format_str
        total_score += add_check(
            "Backup zip uses 'backup-YYYY-MM-DD.zip' naming pattern",
            passed_naming,
            "Correct zip naming convention found" if passed_naming
            else "Zip naming pattern 'backup-YYYY-MM-DD.zip' not found in script"
        )
    except Exception as e:
        total_score += add_check("Zip naming pattern", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 7: Retention deletion logic present (removing old backups)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        # Should have Remove-Item or deletion logic based on age/RetentionDays
        has_delete_logic = bool(re.search(
            r'Remove-Item|Delete\(|\.Delete\b',
            content, re.IGNORECASE
        ))
        has_age_check = bool(re.search(
            r'RetentionDays|AddDays|LastWriteTime|CreationTime',
            content, re.IGNORECASE
        ))
        passed_retention_logic = has_delete_logic and has_age_check
        total_score += add_check(
            "Retention deletion logic present",
            passed_retention_logic,
            "Retention logic (Remove-Item + age check) found" if passed_retention_logic
            else f"Missing retention logic. Delete found: {has_delete_logic}, Age check found: {has_age_check}"
        )
    except Exception as e:
        total_score += add_check("Retention deletion logic", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 8: robocopy /MIR used for mirror sync
    # ══════════════════════════════════════════════════════════════════════════
    try:
        has_robocopy = bool(re.search(
            r'robocopy',
            content, re.IGNORECASE
        ))
        has_mir_flag = bool(re.search(
            r'/MIR\b',
            content, re.IGNORECASE
        ))
        passed_mirror = has_robocopy and has_mir_flag
        total_score += add_check(
            "robocopy /MIR used for drive mirror",
            passed_mirror,
            "robocopy /MIR found" if passed_mirror
            else f"robocopy /MIR not found. robocopy present: {has_robocopy}, /MIR present: {has_mir_flag}"
        )
    except Exception as e:
        total_score += add_check("robocopy /MIR", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 9: register-task.ps1 exists somewhere in workspace
    # ══════════════════════════════════════════════════════════════════════════
    reg_scripts = list(workspace.rglob("register-task.ps1"))
    if reg_scripts:
        reg_script = reg_scripts[0]
        total_score += add_check(
            "register-task.ps1 exists",
            True,
            f"Found at: {reg_script.relative_to(workspace)}"
        )
        try:
            reg_content = reg_script.read_text(errors="replace")
        except Exception as e:
            reg_content = ""
            add_check("register-task.ps1 readable", False, str(e))
    else:
        total_score += add_check(
            "register-task.ps1 exists",
            False,
            "No file named 'register-task.ps1' found in workspace"
        )
        reg_content = ""

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 10: Task name is exactly "AI Workspace Backup"
    # ══════════════════════════════════════════════════════════════════════════
    try:
        has_task_name = bool(re.search(
            r'AI Workspace Backup',
            reg_content
        ))
        total_score += add_check(
            'TaskName is exactly "AI Workspace Backup"',
            has_task_name,
            'Correct TaskName "AI Workspace Backup" found' if has_task_name
            else 'TaskName "AI Workspace Backup" not found in register-task.ps1'
        )
    except Exception as e:
        total_score += add_check("TaskName check", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 11: Trigger is -Daily -At 3AM (not 2AM, not midnight)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        has_daily_trigger = bool(re.search(
            r'New-ScheduledTaskTrigger',
            reg_content, re.IGNORECASE
        ))
        has_3am = bool(re.search(
            r'-At\s+["\']?3AM["\']?|-At\s+["\']?03:00["\']?|-At\s+["\']?3:00\s*AM["\']?',
            reg_content, re.IGNORECASE
        ))
        has_daily = bool(re.search(r'-Daily\b', reg_content, re.IGNORECASE))
        passed_trigger = has_daily_trigger and has_3am and has_daily
        total_score += add_check(
            "Trigger is -Daily -At 3AM",
            passed_trigger,
            "Correct daily 3AM trigger found" if passed_trigger
            else f"Trigger mismatch. New-ScheduledTaskTrigger: {has_daily_trigger}, -Daily: {has_daily}, -At 3AM: {has_3am}"
        )
    except Exception as e:
        total_score += add_check("Trigger check", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 12: Correct cmdlets: New-ScheduledTaskAction, Register-ScheduledTask
    # ══════════════════════════════════════════════════════════════════════════
    try:
        has_action = bool(re.search(r'New-ScheduledTaskAction', reg_content, re.IGNORECASE))
        has_register = bool(re.search(r'Register-ScheduledTask', reg_content, re.IGNORECASE))
        passed_cmdlets = has_action and has_register
        total_score += add_check(
            "Correct PowerShell cmdlets used (New-ScheduledTaskAction, Register-ScheduledTask)",
            passed_cmdlets,
            "Both cmdlets found" if passed_cmdlets
            else f"Missing cmdlets. New-ScheduledTaskAction: {has_action}, Register-ScheduledTask: {has_register}"
        )
    except Exception as e:
        total_score += add_check("Cmdlets check", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 13: register-task.ps1 references daily-backup.ps1
    # ══════════════════════════════════════════════════════════════════════════
    try:
        refs_backup_script = bool(re.search(
            r'daily-backup\.ps1',
            reg_content, re.IGNORECASE
        ))
        total_score += add_check(
            "register-task.ps1 references daily-backup.ps1",
            refs_backup_script,
            "daily-backup.ps1 referenced in task registration" if refs_backup_script
            else "daily-backup.ps1 not referenced in register-task.ps1"
        )
    except Exception as e:
        total_score += add_check("Script reference check", False, str(e))

    # ══════════════════════════════════════════════════════════════════════════
    # FINAL SCORE
    # ══════════════════════════════════════════════════════════════════════════
    num_checks = len(checks)
    score = total_score / num_checks if num_checks > 0 else 0.0
    passed = score >= 0.75  # Must pass at least 75% of checks

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument check", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, indent=2))