import sys
import json
import os
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON parse error in {path}: {e}"
    except Exception as e:
        return None, f"Unexpected error reading {path}: {e}"

checks = []

# ----- Check 1: ~/.openclaw/openclaw.json exists -----
config_path = Path.home() / ".openclaw" / "openclaw.json"
config, err = load_json_safe(config_path)
check1_passed = config is not None
checks.append({
    "name": "openclaw.json exists at ~/.openclaw/openclaw.json",
    "passed": check1_passed,
    "detail": err if err else f"Found at {config_path}"
})

# ----- Check 2: Model routing set to Haiku (not Sonnet/Opus) -----
check2_passed = False
check2_detail = "openclaw.json missing or malformed"
if config:
    try:
        primary_model = config["agents"]["defaults"]["model"]["primary"]
        if "haiku" in primary_model.lower():
            check2_passed = True
            check2_detail = f"Primary model correctly set to '{primary_model}' (Haiku routing active)"
        else:
            check2_detail = f"Primary model is '{primary_model}', expected a Haiku model"
    except KeyError as e:
        check2_detail = f"Missing key in config: {e}"
checks.append({
    "name": "Model routing set to Haiku",
    "passed": check2_passed,
    "detail": check2_detail
})

# ----- Check 3: Prompt caching enabled -----
check3_passed = False
check3_detail = "openclaw.json missing or malformed"
if config:
    try:
        cache_enabled = config["agents"]["defaults"]["cache"]["enabled"]
        if cache_enabled is True:
            check3_passed = True
            check3_detail = "Cache enabled: true"
        else:
            check3_detail = f"Cache enabled is '{cache_enabled}', expected true"
    except KeyError as e:
        check3_detail = f"Missing cache config key: {e}"
checks.append({
    "name": "Prompt caching enabled",
    "passed": check3_passed,
    "detail": check3_detail
})

# ----- Check 4: Heartbeat provider set to 'ollama' -----
check4_passed = False
check4_detail = "openclaw.json missing or malformed"
if config:
    try:
        provider = config["heartbeat"]["provider"]
        if provider.lower() == "ollama":
            check4_passed = True
            check4_detail = f"Heartbeat provider correctly set to '{provider}'"
        else:
            check4_detail = f"Heartbeat provider is '{provider}', expected 'ollama'"
    except KeyError as e:
        check4_detail = f"Missing heartbeat.provider key: {e}"
checks.append({
    "name": "Heartbeat provider set to 'ollama'",
    "passed": check4_passed,
    "detail": check4_detail
})

# ----- Check 5: Heartbeat model references ollama -----
check5_passed = False
check5_detail = "openclaw.json missing or malformed"
if config:
    try:
        hb_model = config["heartbeat"]["model"]
        if "ollama" in hb_model.lower():
            check5_passed = True
            check5_detail = f"Heartbeat model set to '{hb_model}' (Ollama model)"
        else:
            check5_detail = f"Heartbeat model is '{hb_model}', expected an ollama/* model"
    except KeyError as e:
        check5_detail = f"Missing heartbeat.model key: {e}"
checks.append({
    "name": "Heartbeat model uses Ollama model string",
    "passed": check5_passed,
    "detail": check5_detail
})

# ----- Check 6: Budget controls present -----
check6_passed = False
check6_detail = "openclaw.json missing or malformed"
if config:
    try:
        daily = config["budgets"]["daily"]
        monthly = config["budgets"]["monthly"]
        if isinstance(daily, (int, float)) and isinstance(monthly, (int, float)):
            check6_passed = True
            check6_detail = f"Budget controls set: daily=${daily}, monthly=${monthly}"
        else:
            check6_detail = f"Budget values have wrong types: daily={daily}, monthly={monthly}"
    except KeyError as e:
        check6_detail = f"Missing budgets key: {e}"
checks.append({
    "name": "Budget controls (daily + monthly) present",
    "passed": check6_passed,
    "detail": check6_detail
})

# ----- Check 7: Backup exists in ~/.openclaw/backups/ -----
backups_dir = Path.home() / ".openclaw" / "backups"
check7_passed = False
check7_detail = f"No backups found in {backups_dir}"
try:
    if backups_dir.exists():
        backup_files = list(backups_dir.glob("*.json")) + list(backups_dir.glob("*.bak"))
        # Also check any files recursively
        all_backups = list(backups_dir.rglob("*"))
        all_backups = [f for f in all_backups if f.is_file()]
        if all_backups:
            check7_passed = True
            check7_detail = f"Found {len(all_backups)} backup file(s) in {backups_dir}: {[f.name for f in all_backups[:3]]}"
        else:
            check7_detail = f"Backups directory exists but is empty: {backups_dir}"
    else:
        check7_detail = f"Backups directory does not exist: {backups_dir}"
except Exception as e:
    check7_detail = f"Error checking backups: {e}"
checks.append({
    "name": "Config backup created in ~/.openclaw/backups/",
    "passed": check7_passed,
    "detail": check7_detail
})

# ----- Check 8: --apply flag was actually used (changes are real, not dry-run) -----
# We verify this indirectly: the config file MUST exist AND contain the expected structure.
# If agent only ran dry-run, ~/.openclaw/openclaw.json would not exist.
# This check is a composite of checks 1+2+4 but explicit about the --apply requirement.
check8_passed = check1_passed and check2_passed and check4_passed
check8_detail = (
    "All --apply changes confirmed: config exists with Haiku routing and Ollama heartbeat."
    if check8_passed
    else "Changes appear to be dry-run only (config missing or incomplete). Agent likely forgot --apply flag."
)
checks.append({
    "name": "--apply flag used (not just dry-run preview)",
    "passed": check8_passed,
    "detail": check8_detail
})

# ----- Scoring -----
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4)

# Task passes only if all core checks pass
critical_checks = [1, 2, 4, 5, 6, 7]  # 0-indexed
critical_passed = all(checks[i]["passed"] for i in critical_checks)
overall_passed = critical_passed and passed_count >= 6

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))