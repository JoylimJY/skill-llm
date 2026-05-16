#!/usr/bin/env python3
"""
Evaluation script for the authentication system onboarding task.
Usage: python3 eval_script.py /workspace
"""
import sys
import json
import os
import stat
from pathlib import Path
from datetime import datetime

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
data_dir = Path("/data")
auth_dir = data_dir / "auth"

results = []

def check(name, passed, detail=""):
    results.append({"name": name, "passed": passed, "detail": detail})
    return passed

def read_json(path):
    with open(path) as f:
        return json.load(f)

def get_octal_perms(path):
    return oct(stat.S_IMODE(os.stat(path).st_mode))

# -----------------------------------------------------------------------
# CHECK 1: elena.k user directory structure created correctly
# -----------------------------------------------------------------------
try:
    elena_dir = auth_dir / "users" / "elena.k"
    has_profile = (elena_dir / "profile.json").exists()
    has_credentials = (elena_dir / "credentials.json").exists()
    has_permissions = (elena_dir / "permissions.json").exists()
    has_sessions = (elena_dir / "sessions").is_dir()
    has_2fa = (elena_dir / "2fa").is_dir()
    all_exist = has_profile and has_credentials and has_permissions and has_sessions and has_2fa
    check(
        "elena.k: complete directory structure (profile, credentials, permissions, sessions/, 2fa/)",
        all_exist,
        f"profile={has_profile}, credentials={has_credentials}, permissions={has_permissions}, "
        f"sessions_dir={has_sessions}, 2fa_dir={has_2fa}"
    )
except Exception as e:
    check("elena.k: complete directory structure", False, str(e))

# -----------------------------------------------------------------------
# CHECK 2: elena.k profile.json correctness
# -----------------------------------------------------------------------
try:
    profile = read_json(auth_dir / "users" / "elena.k" / "profile.json")
    correct_role = profile.get("role") == "assistant"
    correct_status = profile.get("status") == "active"
    correct_name = "Elena Kyriakou" in profile.get("full_name", "")
    correct_email = "elena.k" in profile.get("email", "")
    pw_change = profile.get("password_change_required") == True
    twofa = profile.get("2fa_enabled") == False
    passed = correct_role and correct_status and correct_name and pw_change
    check(
        "elena.k: profile.json has correct role=assistant, status=active, password_change_required=true",
        passed,
        f"role={profile.get('role')}, status={profile.get('status')}, "
        f"full_name={profile.get('full_name')}, password_change_required={profile.get('password_change_required')}, "
        f"2fa_enabled={profile.get('2fa_enabled')}"
    )
except Exception as e:
    check("elena.k: profile.json correctness", False, str(e))

# -----------------------------------------------------------------------
# CHECK 3: elena.k credentials.json has password_change_required=true
# -----------------------------------------------------------------------
try:
    creds = read_json(auth_dir / "users" / "elena.k" / "credentials.json")
    has_hash = bool(creds.get("password_hash"))
    pw_change = creds.get("password_change_required") == True
    has_set_at = bool(creds.get("password_set_at"))
    passed = has_hash and pw_change and has_set_at
    check(
        "elena.k: credentials.json has password_hash, password_set_at, and password_change_required=true",
        passed,
        f"password_hash_present={has_hash}, password_change_required={creds.get('password_change_required')}, "
        f"password_set_at={bool(creds.get('password_set_at'))}"
    )
except Exception as e:
    check("elena.k: credentials.json correctness", False, str(e))

# -----------------------------------------------------------------------
# CHECK 4: elena.k permissions.json exact structure {role, custom:[]}
# -----------------------------------------------------------------------
try:
    perms = read_json(auth_dir / "users" / "elena.k" / "permissions.json")
    has_role_key = "role" in perms
    correct_role_val = perms.get("role") == "assistant"
    has_custom_key = "custom" in perms
    custom_is_list = isinstance(perms.get("custom"), list)
    passed = has_role_key and correct_role_val and has_custom_key and custom_is_list
    check(
        "elena.k: permissions.json has exact structure {role: 'assistant', custom: []}",
        passed,
        f"keys={list(perms.keys())}, role={perms.get('role')}, custom={perms.get('custom')}"
    )
except Exception as e:
    check("elena.k: permissions.json structure", False, str(e))

# -----------------------------------------------------------------------
# CHECK 5: stavros.m user directory structure
# -----------------------------------------------------------------------
try:
    stavros_dir = auth_dir / "users" / "stavros.m"
    has_profile = (stavros_dir / "profile.json").exists()
    has_credentials = (stavros_dir / "credentials.json").exists()
    has_permissions = (stavros_dir / "permissions.json").exists()
    has_sessions = (stavros_dir / "sessions").is_dir()
    has_2fa = (stavros_dir / "2fa").is_dir()
    all_exist = has_profile and has_credentials and has_permissions and has_sessions and has_2fa
    check(
        "stavros.m: complete directory structure",
        all_exist,
        f"profile={has_profile}, credentials={has_credentials}, permissions={has_permissions}, "
        f"sessions_dir={has_sessions}, 2fa_dir={has_2fa}"
    )
except Exception as e:
    check("stavros.m: complete directory structure", False, str(e))

# -----------------------------------------------------------------------
# CHECK 6: stavros.m profile has role=accountant
# -----------------------------------------------------------------------
try:
    profile = read_json(auth_dir / "users" / "stavros.m" / "profile.json")
    correct_role = profile.get("role") == "accountant"
    correct_status = profile.get("status") == "active"
    correct_name = "Stavros Mitropoulos" in profile.get("full_name", "")
    pw_change = profile.get("password_change_required") == True
    passed = correct_role and correct_status and correct_name and pw_change
    check(
        "stavros.m: profile.json has role=accountant, status=active, password_change_required=true",
        passed,
        f"role={profile.get('role')}, status={profile.get('status')}, "
        f"full_name={profile.get('full_name')}, password_change_required={profile.get('password_change_required')}"
    )
except Exception as e:
    check("stavros.m: profile.json correctness", False, str(e))

# -----------------------------------------------------------------------
# CHECK 7: stavros.m permissions.json exact structure
# -----------------------------------------------------------------------
try:
    perms = read_json(auth_dir / "users" / "stavros.m" / "permissions.json")
    has_role_key = "role" in perms
    correct_role_val = perms.get("role") == "accountant"
    has_custom_key = "custom" in perms
    custom_is_list = isinstance(perms.get("custom"), list)
    passed = has_role_key and correct_role_val and has_custom_key and custom_is_list
    check(
        "stavros.m: permissions.json has exact structure {role: 'accountant', custom: []}",
        passed,
        f"keys={list(perms.keys())}, role={perms.get('role')}, custom={perms.get('custom')}"
    )
except Exception as e:
    check("stavros.m: permissions.json structure", False, str(e))

# -----------------------------------------------------------------------
# CHECK 8: client_assignments.json has elena.k with correct 3 clients
# -----------------------------------------------------------------------
try:
    assignments = read_json(auth_dir / "access" / "client_assignments.json")
    elena_entry = assignments.get("elena.k", {})
    expected_clients = {"EL801234567", "EL802345678", "EL803456789"}
    actual_clients = set(elena_entry.get("clients", []))
    not_all = elena_entry.get("all_clients") != True  # should NOT be all_clients for assistant
    clients_match = expected_clients.issubset(actual_clients)
    passed = clients_match
    check(
        "client_assignments.json: elena.k assigned exactly her 3 clients",
        passed,
        f"elena_entry={elena_entry}, expected_clients={expected_clients}, actual_clients={actual_clients}"
    )
except Exception as e:
    check("client_assignments.json: elena.k clients", False, str(e))

# -----------------------------------------------------------------------
# CHECK 9: client_assignments.json has stavros.m with correct 2 clients
# -----------------------------------------------------------------------
try:
    assignments = read_json(auth_dir / "access" / "client_assignments.json")
    stavros_entry = assignments.get("stavros.m", {})
    expected_clients = {"EL804567890", "EL805678901"}
    actual_clients = set(stavros_entry.get("clients", []))
    clients_match = expected_clients.issubset(actual_clients)
    passed = clients_match
    check(
        "client_assignments.json: stavros.m assigned his 2 clients",
        passed,
        f"stavros_entry={stavros_entry}, expected_clients={expected_clients}, actual_clients={actual_clients}"
    )
except Exception as e:
    check("client_assignments.json: stavros.m clients", False, str(e))

# -----------------------------------------------------------------------
# CHECK 10: File system permission hardening - auth dir is 700
# -----------------------------------------------------------------------
try:
    auth_perms = get_octal_perms(auth_dir)
    passed = auth_perms == "0o700"
    check(
        "Security hardening: /data/auth/ directory has chmod 700",
        passed,
        f"actual permissions: {auth_perms}"
    )
except Exception as e:
    check("Security hardening: /data/auth/ chmod 700", False, str(e))

# -----------------------------------------------------------------------
# CHECK 11: credentials.json files have chmod 600
# -----------------------------------------------------------------------
try:
    cred_files = list((auth_dir / "users").rglob("credentials.json"))
    if not cred_files:
        check("Security hardening: credentials.json files have chmod 600", False, "No credentials.json files found")
    else:
        wrong = []
        for cf in cred_files:
            p = get_octal_perms(cf)
            if p != "0o600":
                wrong.append(f"{cf}: {p}")
        passed = len(wrong) == 0
        check(
            "Security hardening: all credentials.json files have chmod 600",
            passed,
            f"Checked {len(cred_files)} files. Wrong perms: {wrong if wrong else 'none'}"
        )
except Exception as e:
    check("Security hardening: credentials.json chmod 600", False, str(e))

# -----------------------------------------------------------------------
# CHECK 12: Role files have chmod 644
# -----------------------------------------------------------------------
try:
    role_files = list((auth_dir / "roles").glob("*.json"))
    if not role_files:
        check("Security hardening: role files have chmod 644", False, "No role JSON files found")
    else:
        wrong = []
        for rf in role_files:
            p = get_octal_perms(rf)
            if p != "0o644":
                wrong.append(f"{rf}: {p}")
        passed = len(wrong) == 0
        check(
            "Security hardening: all /data/auth/roles/*.json files have chmod 644",
            passed,
            f"Checked {len(role_files)} role files. Wrong perms: {wrong if wrong else 'none'}"
        )
except Exception as e:
    check("Security hardening: role files chmod 644", False, str(e))

# -----------------------------------------------------------------------
# CHECK 13: Session files have chmod 600
# -----------------------------------------------------------------------
try:
    session_files = list((auth_dir / "users").rglob("sessions/*.json"))
    if not session_files:
        # It's okay if newly created users have no sessions yet, but admin does
        check("Security hardening: session files have chmod 600", True, "No session files to check (acceptable)")
    else:
        wrong = []
        for sf in session_files:
            p = get_octal_perms(sf)
            if p != "0o600":
                wrong.append(f"{sf}: {p}")
        passed = len(wrong) == 0
        check(
            "Security hardening: session files have chmod 600",
            passed,
            f"Checked {len(session_files)} session files. Wrong perms: {wrong if wrong else 'none'}"
        )
except Exception as e:
    check("Security hardening: session files chmod 600", False, str(e))

# -----------------------------------------------------------------------
# CHECK 14: Admin audit log entry exists for user_created events
# -----------------------------------------------------------------------
try:
    admin_log_dir = auth_dir / "logs" / "admin"
    log_files = list(admin_log_dir.glob("*.json"))
    if not log_files:
        check("Audit log: admin log entries exist for user_created events", False, "No log files found in /data/auth/logs/admin/")
    else:
        all_entries = []
        for lf in log_files:
            try:
                with open(lf) as f:
                    content = f.read().strip()
                # May be NDJSON (newline-delimited)
                for line in content.split('\n'):
                    line = line.strip()
                    if line:
                        try:
                            all_entries.append(json.loads(line))
                        except Exception:
                            pass
            except Exception:
                pass
        
        # Check for user_created events for both new users
        elena_created = any(
            e.get("event_type", "").endswith("user_created") and
            ("elena.k" in str(e.get("target", "")) or "elena.k" in str(e.get("details", "")))
            for e in all_entries
        )
        stavros_created = any(
            e.get("event_type", "").endswith("user_created") and
            ("stavros.m" in str(e.get("target", "")) or "stavros.m" in str(e.get("details", "")))
            for e in all_entries
        )
        
        # Check event format has required fields
        required_fields = {"timestamp", "event_type", "username", "result"}
        entries_with_fields = [
            e for e in all_entries
            if required_fields.issubset(set(e.keys()))
        ]
        
        passed = elena_created and stavros_created and len(entries_with_fields) > 0
        check(
            "Audit log: admin log has user_created entries for elena.k and stavros.m with required fields",
            passed,
            f"elena_created={elena_created}, stavros_created={stavros_created}, "
            f"total_entries={len(all_entries)}, entries_with_required_fields={len(entries_with_fields)}"
        )
except Exception as e:
    check("Audit log: admin log entries", False, str(e))

# -----------------------------------------------------------------------
# CHECK 15: Audit log entries have ISO 8601 timestamps
# -----------------------------------------------------------------------
try:
    admin_log_dir = auth_dir / "logs" / "admin"
    log_files = list(admin_log_dir.glob("*.json"))
    all_entries = []
    for lf in log_files:
        try:
            with open(lf) as f:
                content = f.read().strip()
            for line in content.split('\n'):
                line = line.strip()
                if line:
                    try:
                        all_entries.append(json.loads(line))
                    except Exception:
                        pass
        except Exception:
            pass
    
    if not all_entries:
        check("Audit log: timestamps are ISO 8601", False, "No log entries found")
    else:
        invalid_ts = []
        for e in all_entries:
            ts = e.get("timestamp", "")
            # Check ISO 8601 format: YYYY-MM-DDTHH:MM:SS (with optional timezone)
            if ts and not (len(ts) >= 19 and ts[4] == '-' and ts[7] == '-' and 'T' in ts):
                invalid_ts.append(ts)
        passed = len(invalid_ts) == 0 and len(all_entries) > 0
        check(
            "Audit log: all log entries have ISO 8601 timestamps",
            passed,
            f"Total entries: {len(all_entries)}, invalid timestamps: {invalid_ts}"
        )
except Exception as e:
    check("Audit log: ISO 8601 timestamps", False, str(e))

# -----------------------------------------------------------------------
# CHECK 16: nikos.p admin user preserved and unchanged
# -----------------------------------------------------------------------
try:
    profile = read_json(auth_dir / "users" / "nikos.p" / "profile.json")
    correct_role = profile.get("role") == "senior_accountant"
    correct_status = profile.get("status") == "active"
    passed = correct_role and correct_status
    check(
        "Existing admin nikos.p: profile preserved with role=senior_accountant, status=active",
        passed,
        f"role={profile.get('role')}, status={profile.get('status')}"
    )
except Exception as e:
    check("Existing admin nikos.p: profile preserved", False, str(e))

# -----------------------------------------------------------------------
# SCORING
# -----------------------------------------------------------------------
total = len(results)
passed_count = sum(1 for r in results if r["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = score >= 0.85

output = {
    "passed": overall_passed,
    "score": score,
    "checks": results
}

print(json.dumps(output, indent=2))