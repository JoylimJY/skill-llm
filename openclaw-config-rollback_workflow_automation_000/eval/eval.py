#!/usr/bin/env python3
"""
Evaluation script for the openclaw-config-rollback task.
Checks that the agent correctly:
1. Ran prepare-config-change.sh (backup exists, state file exists, PENDING_VERIFICATION.md updated)
2. Modified openclaw.json to enable the payment-processor skill
3. Installed the rollback-guardian cron job with the correct path and schedule
"""

import sys
import os
import json
import re
import subprocess
from pathlib import Path

def run_check(name: str, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

HOME = Path(os.path.expanduser("~"))
OPENCLAW_DIR = HOME / ".openclaw"

checks = []

# -----------------------------------------------------------------------
# CHECK 1: Backup file was created by prepare-config-change.sh
# The script creates backups in ~/.openclaw/backups/openclaw_YYYYMMDD_HHMMSS.json
# There should be at least one NEW backup (beyond the old 20260115 one).
# -----------------------------------------------------------------------
def check_backup_created():
    backup_dir = OPENCLAW_DIR / "backups"
    if not backup_dir.exists():
        return False, "Backup directory does not exist"
    
    json_backups = list(backup_dir.glob("openclaw_*.json"))
    # Filter out the pre-existing old backup (20260115)
    new_backups = [b for b in json_backups if "20260115" not in b.name]
    
    if not new_backups:
        return False, f"No new backup JSON files found in {backup_dir}. Files: {[b.name for b in json_backups]}"
    
    # Verify the backup is valid JSON and looks like an openclaw config
    try:
        with open(new_backups[0]) as f:
            data = json.load(f)
        if "version" not in data or "gateway" not in data:
            return False, f"Backup file {new_backups[0].name} doesn't look like a valid openclaw config"
    except Exception as e:
        return False, f"Backup file is not valid JSON: {e}"
    
    return True, f"Backup created: {new_backups[0].name}"

checks.append(run_check("backup_file_created", check_backup_created))

# -----------------------------------------------------------------------
# CHECK 2: State file .config-modified-state was created
# -----------------------------------------------------------------------
def check_state_file():
    state_file = OPENCLAW_DIR / ".config-modified-state"
    if not state_file.exists():
        return False, f"State file {state_file} does not exist. prepare-config-change.sh was likely not run."
    
    content = state_file.read_text()
    if "DESCRIPTION=" not in content:
        return False, f"State file exists but missing DESCRIPTION field. Content: {content[:200]}"
    if "BACKUP_FILE=" not in content:
        return False, f"State file exists but missing BACKUP_FILE field. Content: {content[:200]}"
    if "DEADLINE=" not in content:
        return False, f"State file exists but missing DEADLINE field. Content: {content[:200]}"
    
    return True, f"State file exists with required fields. Content preview: {content[:150]}"

checks.append(run_check("state_file_created", check_state_file))

# -----------------------------------------------------------------------
# CHECK 3: PENDING_VERIFICATION.md was updated with verification items
# It should contain at least one verification item added by the script,
# related to the payment-processor change.
# -----------------------------------------------------------------------
def check_pending_verification():
    pending_file = OPENCLAW_DIR / "docs" / "PENDING_VERIFICATION.md"
    if not pending_file.exists():
        return False, f"PENDING_VERIFICATION.md not found at {pending_file}"
    
    content = pending_file.read_text()
    
    # Should have more content than the initial template
    if len(content) < 200:
        return False, f"PENDING_VERIFICATION.md seems unchanged (too short: {len(content)} chars)"
    
    # Should contain checkbox items (verification items were added)
    if "- [ ]" not in content:
        return False, "PENDING_VERIFICATION.md has no checkbox items (verification items not added)"
    
    # Should mention the change (payment-processor or similar description)
    lower = content.lower()
    if "payment" not in lower and "enable" not in lower and "skill" not in lower:
        return False, f"PENDING_VERIFICATION.md doesn't mention the expected change context. Content: {content[:300]}"
    
    return True, f"PENDING_VERIFICATION.md updated with change info and verification items."

checks.append(run_check("pending_verification_updated", check_pending_verification))

# -----------------------------------------------------------------------
# CHECK 4: openclaw.json was modified to enable payment-processor
# The agent must move "payment-processor" from disabled to enabled list,
# or otherwise add it to enabled skills.
# -----------------------------------------------------------------------
def check_config_modified():
    config_file = OPENCLAW_DIR / "openclaw.json"
    if not config_file.exists():
        return False, "openclaw.json does not exist"
    
    try:
        with open(config_file) as f:
            data = json.load(f)
    except Exception as e:
        return False, f"openclaw.json is not valid JSON: {e}"
    
    skills = data.get("skills", {})
    enabled = skills.get("enabled", [])
    disabled = skills.get("disabled", [])
    
    if "payment-processor" not in enabled:
        return False, f"payment-processor is not in enabled skills list. enabled={enabled}, disabled={disabled}"
    
    if "payment-processor" in disabled:
        return False, f"payment-processor is still in disabled skills list. Must be moved to enabled."
    
    # Verify original skills are preserved
    if "obsidian-sync" not in enabled and "obsidian-sync" not in disabled:
        return False, "Original skill obsidian-sync seems to have been removed entirely"
    
    return True, f"openclaw.json correctly enables payment-processor. enabled={enabled}"

checks.append(run_check("config_payment_processor_enabled", check_config_modified))

# -----------------------------------------------------------------------
# CHECK 5: Crontab contains rollback-guardian.sh with correct schedule
# Must be: */1 * * * * ~/.openclaw/workspace/skills/config-rollback/scripts/rollback-guardian.sh
# (manual install path from SKILL.md)
# -----------------------------------------------------------------------
def check_crontab_installed():
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True, text=True, timeout=10
        )
        crontab_content = result.stdout
    except Exception as e:
        return False, f"Failed to run 'crontab -l': {e}"
    
    if not crontab_content.strip():
        return False, "Crontab is empty. rollback-guardian cron job was not installed."
    
    # Check for rollback-guardian.sh in crontab
    if "rollback-guardian.sh" not in crontab_content:
        return False, f"rollback-guardian.sh not found in crontab. Crontab content:\n{crontab_content}"
    
    # Check the schedule is */1 * * * * (every minute)
    lines = [l.strip() for l in crontab_content.splitlines() if "rollback-guardian.sh" in l]
    if not lines:
        return False, "rollback-guardian.sh line not found in crontab"
    
    guardian_line = lines[0]
    
    # Must have */1 * * * * schedule
    schedule_pattern = re.compile(r'\*/1\s+\*\s+\*\s+\*\s+\*')
    if not schedule_pattern.search(guardian_line):
        return False, f"Cron schedule is incorrect. Expected '*/1 * * * *'. Found line: {guardian_line}"
    
    # Must reference the workspace path (manual install path per SKILL.md)
    if "workspace/skills/config-rollback/scripts/rollback-guardian.sh" not in guardian_line:
        return False, (
            f"Cron job uses wrong script path. Expected path containing "
            f"'workspace/skills/config-rollback/scripts/rollback-guardian.sh'. "
            f"Found: {guardian_line}"
        )
    
    return True, f"Cron job correctly installed: {guardian_line}"

checks.append(run_check("crontab_guardian_installed", check_crontab_installed))

# -----------------------------------------------------------------------
# CHECK 6: The guardian script itself is executable at workspace path
# (manual install step: chmod +x)
# -----------------------------------------------------------------------
def check_guardian_executable():
    guardian_path = OPENCLAW_DIR / "workspace" / "skills" / "config-rollback" / "scripts" / "rollback-guardian.sh"
    if not guardian_path.exists():
        return False, f"rollback-guardian.sh not found at {guardian_path}"
    
    if not os.access(guardian_path, os.X_OK):
        return False, f"rollback-guardian.sh exists but is not executable at {guardian_path}"
    
    return True, f"rollback-guardian.sh is executable at {guardian_path}"

checks.append(run_check("guardian_script_executable", check_guardian_executable))

# -----------------------------------------------------------------------
# Final scoring
# -----------------------------------------------------------------------
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
all_passed = passed_count == total

output = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(output, indent=2))
sys.exit(0 if all_passed else 1)