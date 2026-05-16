import sys
import json
import os
import re
import datetime
from pathlib import Path

workspace = sys.argv[1]

checks = []
total_score = 0.0
weights = {
    "backups_dir_exists": 0.15,
    "backup_file_naming_convention": 0.30,
    "backup_created_before_or_with_modification": 0.10,
    "config_port_changed": 0.20,
    "config_ssl_enabled_added": 0.20,
    "backup_still_present": 0.05,
}

# --- Check 1: backups/ directory exists ---
backups_dir = Path(workspace) / "backups"
if backups_dir.is_dir():
    checks.append({"name": "backups_dir_exists", "passed": True, "detail": "backups/ directory exists as required by the backup workflow."})
    total_score += weights["backups_dir_exists"]
else:
    checks.append({"name": "backups_dir_exists", "passed": False, "detail": f"backups/ directory not found at {backups_dir}. Agent must create backups/ before modifying config.json."})

# --- Check 2: Backup file follows exact naming convention: backups/config.json.YYYY-MM-DD.bak ---
today = datetime.date.today().strftime("%Y-%m-%d")
expected_backup_name = f"config.json.{today}.bak"
expected_backup_path = backups_dir / expected_backup_name

backup_found_exactly = expected_backup_path.exists()
# Also search for any .bak file matching the pattern (in case date is slightly off or backup was not deleted)
any_bak_files = list(backups_dir.glob("config.json.*.bak")) if backups_dir.is_dir() else []

naming_detail = ""
if backup_found_exactly:
    naming_detail = f"Backup file correctly named '{expected_backup_name}' found in backups/."
    checks.append({"name": "backup_file_naming_convention", "passed": True, "detail": naming_detail})
    total_score += weights["backup_file_naming_convention"]
elif any_bak_files:
    found_names = [f.name for f in any_bak_files]
    # Partial credit check: does it match the general pattern backups/config.json.<date>.bak?
    pattern = re.compile(r'^config\.json\.\d{4}-\d{2}-\d{2}\.bak$')
    if any(pattern.match(f.name) for f in any_bak_files):
        naming_detail = f"Backup file found with correct pattern but unexpected date: {found_names}. Expected date: {today}."
        checks.append({"name": "backup_file_naming_convention", "passed": True, "detail": naming_detail})
        total_score += weights["backup_file_naming_convention"]
    else:
        naming_detail = f"Backup file(s) found but do not follow required naming convention 'config.json.YYYY-MM-DD.bak': {found_names}"
        checks.append({"name": "backup_file_naming_convention", "passed": False, "detail": naming_detail})
else:
    naming_detail = f"No backup file found in backups/. Expected: '{expected_backup_name}'. The skill requires creating a backup before any modification."
    checks.append({"name": "backup_file_naming_convention", "passed": False, "detail": naming_detail})

# --- Check 3: Backup contains original config content (proving it was created before modification) ---
original_port = 8443
backup_content_valid = False
backup_check_detail = ""

candidate_backups = [expected_backup_path] + [f for f in any_bak_files if f != expected_backup_path]
for bak_file in candidate_backups:
    if bak_file.exists():
        try:
            with open(bak_file, "r") as f:
                bak_data = json.load(f)
            if bak_data.get("gateway_port") == original_port:
                backup_content_valid = True
                backup_check_detail = f"Backup file '{bak_file.name}' contains original gateway_port={original_port}, confirming backup was taken before modification."
                break
            else:
                backup_check_detail = f"Backup file '{bak_file.name}' exists but gateway_port={bak_data.get('gateway_port')} != {original_port}. Backup may have been taken after modification."
        except (json.JSONDecodeError, Exception) as e:
            backup_check_detail = f"Backup file found but could not be parsed as JSON: {e}"

if not candidate_backups or not any(f.exists() for f in candidate_backups):
    backup_check_detail = "No backup file present to verify content."

if backup_content_valid:
    checks.append({"name": "backup_created_before_or_with_modification", "passed": True, "detail": backup_check_detail})
    total_score += weights["backup_created_before_or_with_modification"]
else:
    checks.append({"name": "backup_created_before_or_with_modification", "passed": False, "detail": backup_check_detail})

# --- Check 4: config.json was modified — gateway_port changed from 8443 to 9443 ---
config_path = Path(workspace) / "config.json"
config_port_changed = False
config_data = None
port_detail = ""

try:
    with open(config_path, "r") as f:
        config_data = json.load(f)
    new_port = config_data.get("gateway_port")
    if new_port == 9443:
        config_port_changed = True
        port_detail = f"gateway_port correctly updated to 9443."
    else:
        port_detail = f"gateway_port is {new_port}, expected 9443."
except FileNotFoundError:
    port_detail = "config.json not found in workspace root."
except json.JSONDecodeError as e:
    port_detail = f"config.json is not valid JSON: {e}"
except Exception as e:
    port_detail = f"Unexpected error reading config.json: {e}"

checks.append({"name": "config_port_changed", "passed": config_port_changed, "detail": port_detail})
if config_port_changed:
    total_score += weights["config_port_changed"]

# --- Check 5: config.json has ssl_enabled: true added ---
ssl_added = False
ssl_detail = ""

if config_data is not None:
    ssl_val = config_data.get("ssl_enabled")
    if ssl_val is True:
        ssl_added = True
        ssl_detail = "ssl_enabled field correctly set to true in config.json."
    elif ssl_val is not None:
        ssl_detail = f"ssl_enabled field present but value is {ssl_val!r}, expected true (boolean)."
    else:
        ssl_detail = "ssl_enabled field not found in config.json."
else:
    ssl_detail = "config.json could not be loaded; ssl_enabled check skipped."

checks.append({"name": "config_ssl_enabled_added", "passed": ssl_added, "detail": ssl_detail})
if ssl_added:
    total_score += weights["config_ssl_enabled_added"]

# --- Check 6: Backup is still present (no user confirmation was given, so backup must NOT be deleted) ---
# Since no user confirmation file/signal is present, the backup MUST remain.
backup_still_there = any(f.exists() for f in candidate_backups) if candidate_backups else False
if backup_still_there:
    checks.append({"name": "backup_still_present", "passed": True, "detail": "Backup retained as required — user has not yet confirmed deletion. Skill mandates 'confirm before delete'."})
    total_score += weights["backup_still_present"]
else:
    checks.append({"name": "backup_still_present", "passed": False, "detail": "Backup was deleted without user confirmation. The skill requires explicit user confirmation ('可以删除备份') before removing the backup."})

# --- Final result ---
passed = total_score >= 0.70

result = {
    "passed": passed,
    "score": round(total_score, 4),
    "checks": checks
}

print(json.dumps(result, indent=2, ensure_ascii=False))