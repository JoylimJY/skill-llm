#!/usr/bin/env python3
"""
Evaluation script for the codex-account-switcher task.
Checks:
  1. ~/.codex/auth.json is now elise's token
  2. ~/.codex/account-activity.jsonl has a new entry for elise
  3. OpenClaw auth-profiles.json has email-based keys for all 3 accounts
  4. Old name-based codex keys are removed from OpenClaw profiles
  5. quota_analysis.json exists and contains correct scores + winner
"""

import sys
import json
import pathlib
import os
import base64
import re
import math

workspace = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/workspace")
HOME = pathlib.Path(os.path.expanduser("~"))

checks = []
overall_passed = True


def fail(name: str, detail: str):
    checks.append({"name": name, "passed": False, "detail": detail})
    global overall_passed
    overall_passed = False


def ok(name: str, detail: str):
    checks.append({"name": name, "passed": True, "detail": detail})


def decode_jwt_payload(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid JWT")
    payload_b64 = parts[1]
    padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


# ─────────────────────────────────────────────────────────────
# CHECK 1: auth.json is now elise's token
# ─────────────────────────────────────────────────────────────
try:
    auth_path = HOME / ".codex" / "auth.json"
    if not auth_path.exists():
        fail("auth_json_switched_to_elise", "~/.codex/auth.json does not exist")
    else:
        auth_data = json.loads(auth_path.read_text())
        active_email = auth_data.get("email", "")
        
        # Also try to extract from JWT
        jwt_email = ""
        try:
            payload = decode_jwt_payload(auth_data.get("id_token", ""))
            jwt_email = payload.get("email", "")
        except Exception:
            pass
        
        effective_email = active_email or jwt_email
        
        if "elise" in effective_email.lower() or effective_email == "elise@drobnik.com":
            ok("auth_json_switched_to_elise",
               f"auth.json correctly shows elise: {effective_email}")
        else:
            fail("auth_json_switched_to_elise",
                 f"auth.json email is '{effective_email}', expected elise@drobnik.com. "
                 "Did you run the 'use elise' command?")
except Exception as e:
    fail("auth_json_switched_to_elise", f"Exception reading auth.json: {e}")


# ─────────────────────────────────────────────────────────────
# CHECK 2: account-activity.jsonl has a new entry for elise
# ─────────────────────────────────────────────────────────────
try:
    activity_path = HOME / ".codex" / "account-activity.jsonl"
    if not activity_path.exists():
        fail("activity_log_has_elise_entry", "~/.codex/account-activity.jsonl does not exist")
    else:
        lines = [l.strip() for l in activity_path.read_text().splitlines() if l.strip()]
        entries = [json.loads(l) for l in lines]
        elise_entries = [e for e in entries if e.get("account") == "elise"]
        
        if not elise_entries:
            fail("activity_log_has_elise_entry",
                 f"No entry for 'elise' in account-activity.jsonl. "
                 f"Found entries for: {[e.get('account') for e in entries]}")
        else:
            latest = elise_entries[-1]
            has_timestamp = isinstance(latest.get("timestamp"), int)
            has_user_id = bool(latest.get("user_id"))
            if has_timestamp and has_user_id:
                ok("activity_log_has_elise_entry",
                   f"activity.jsonl has elise entry: ts={latest['timestamp']}, "
                   f"user_id={latest['user_id']}")
            else:
                fail("activity_log_has_elise_entry",
                     f"Elise entry found but missing fields: {latest}")
except Exception as e:
    fail("activity_log_has_elise_entry", f"Exception reading activity log: {e}")


# ─────────────────────────────────────────────────────────────
# CHECK 3: OpenClaw auth-profiles.json has email-based keys for all accounts
# CHECK 4: Old name-based codex keys removed
# ─────────────────────────────────────────────────────────────
EXPECTED_EMAILS = {
    "oliver@drobnik.com",
    "elise@drobnik.com",
    "sylvia@drobnik.com",
}
EXPECTED_EMAIL_KEYS = {f"openai-codex:{e}" for e in EXPECTED_EMAILS}
OLD_NAME_KEYS = {"openai-codex:oliver", "openai-codex:elise", "openai-codex:sylvia"}

openclaw_agents_dir = HOME / ".openclaw" / "agents"
agent_dirs = []
if openclaw_agents_dir.exists():
    for ad in openclaw_agents_dir.iterdir():
        inner = ad / "agent"
        if inner.is_dir():
            agent_dirs.append(inner)

if not agent_dirs:
    fail("openclaw_email_based_keys_present", "No OpenClaw agent directories found")
    fail("openclaw_old_name_keys_removed", "No OpenClaw agent directories found")
else:
    all_profiles_ok = True
    all_old_removed = True
    details_profiles = []
    details_old = []
    
    for agent_dir in sorted(agent_dirs):
        profiles_path = agent_dir / "auth-profiles.json"
        try:
            if not profiles_path.exists():
                all_profiles_ok = False
                details_profiles.append(f"{agent_dir.parent.name}: auth-profiles.json missing")
                continue
            
            profiles = json.loads(profiles_path.read_text())
            present_keys = set(profiles.keys())
            
            # Check email-based keys
            missing_email_keys = EXPECTED_EMAIL_KEYS - present_keys
            if missing_email_keys:
                all_profiles_ok = False
                details_profiles.append(
                    f"{agent_dir.parent.name}: missing keys {missing_email_keys}"
                )
            else:
                details_profiles.append(
                    f"{agent_dir.parent.name}: all email-based keys present ✓"
                )
                # Verify each profile has required fields
                for key in EXPECTED_EMAIL_KEYS:
                    p = profiles[key]
                    required = {"type", "provider", "access", "refresh", "expires", "accountId", "email"}
                    missing_fields = required - set(p.keys())
                    if missing_fields:
                        all_profiles_ok = False
                        details_profiles.append(
                            f"{agent_dir.parent.name}/{key}: missing fields {missing_fields}"
                        )
            
            # Check old name-based keys are removed
            lingering_old = OLD_NAME_KEYS & present_keys
            if lingering_old:
                all_old_removed = False
                details_old.append(
                    f"{agent_dir.parent.name}: old name-based keys still present: {lingering_old}"
                )
            else:
                details_old.append(
                    f"{agent_dir.parent.name}: no stale name-based codex keys ✓"
                )
            
            # Verify non-codex keys preserved
            non_codex = {k: v for k, v in profiles.items() if not k.startswith("openai-codex:")}
            if "github:someuser" not in non_codex:
                details_profiles.append(
                    f"WARNING {agent_dir.parent.name}: non-codex key 'github:someuser' was removed (should be preserved)"
                )
        
        except Exception as e:
            all_profiles_ok = False
            details_profiles.append(f"{agent_dir.parent.name}: exception: {e}")
    
    if all_profiles_ok:
        ok("openclaw_email_based_keys_present", "; ".join(details_profiles))
    else:
        fail("openclaw_email_based_keys_present", "; ".join(details_profiles))
    
    if all_old_removed:
        ok("openclaw_old_name_keys_removed", "; ".join(details_old))
    else:
        fail("openclaw_old_name_keys_removed", "; ".join(details_old))


# ─────────────────────────────────────────────────────────────
# CHECK 5: quota_analysis.json exists with correct scoring + winner
# ─────────────────────────────────────────────────────────────

# Expected values:
# elapsed_hours = 104
# budget = (104/168)*100 = 61.904...%
# oliver:  weekly=55, 5h=80 → penalty=+10 (75-89%), score=(55-61.904)+10 = +3.096
# elise:   weekly=48, 5h=40 → penalty=0,           score=(48-61.904)+0  = -13.904
# sylvia:  weekly=90, 5h=15 → penalty=0,           score=(90-61.904)+0  = +28.095
# winner: elise (lowest score)

ELAPSED_HOURS = 104.0
BUDGET = (ELAPSED_HOURS / 168.0) * 100.0
EXPECTED_SCORES = {
    "oliver":  round((55.0 - BUDGET) + 10.0, 4),   # ~+3.095
    "elise":   round((48.0 - BUDGET) + 0.0,  4),   # ~-13.905
    "sylvia":  round((90.0 - BUDGET) + 0.0,  4),   # ~+28.095
}
EXPECTED_WINNER = "elise"

# Find quota_analysis.json anywhere in workspace
qa_files = list(workspace.rglob("quota_analysis.json"))
# Also check home dir
if not qa_files:
    qa_files = list(HOME.rglob("quota_analysis.json"))

if not qa_files:
    fail("quota_analysis_file_exists",
         "quota_analysis.json not found anywhere under /workspace or home directory")
    fail("quota_analysis_scores_correct",
         "quota_analysis.json missing — cannot check scores")
    fail("quota_analysis_winner_correct",
         "quota_analysis.json missing — cannot check winner")
else:
    qa_path = qa_files[0]
    ok("quota_analysis_file_exists", f"Found quota_analysis.json at {qa_path}")
    
    try:
        qa = json.loads(qa_path.read_text())
    except Exception as e:
        fail("quota_analysis_scores_correct", f"Could not parse quota_analysis.json: {e}")
        fail("quota_analysis_winner_correct", f"Could not parse quota_analysis.json: {e}")
        qa = None
    
    if qa is not None:
        # ── Check scores ──────────────────────────────────────────
        TOLERANCE = 0.5  # allow rounding difference
        score_details = []
        scores_ok = True
        
        # The file may use various structures. We look for score values.
        # Accept: {"accounts": {"oliver": {"score": X}, ...}} or flat {"oliver": {"score": X}}
        def find_scores(data):
            """Try to extract per-account scores from various JSON shapes."""
            accounts_section = data.get("accounts", data)
            result = {}
            for name in ["oliver", "elise", "sylvia"]:
                if name in accounts_section:
                    entry = accounts_section[name]
                    if isinstance(entry, dict):
                        for k in ["score", "Score", "total_score", "final_score"]:
                            if k in entry:
                                result[name] = float(entry[k])
                                break
            return result
        
        found_scores = find_scores(qa)
        
        if len(found_scores) < 3:
            fail("quota_analysis_scores_correct",
                 f"Could not find scores for all 3 accounts. Found: {found_scores}. "
                 f"Expected keys: oliver, elise, sylvia with a 'score' field. "
                 f"File content: {str(qa)[:500]}")
        else:
            for name, expected_score in EXPECTED_SCORES.items():
                actual = found_scores.get(name)
                if actual is None:
                    scores_ok = False
                    score_details.append(f"{name}: score not found")
                elif abs(actual - expected_score) > TOLERANCE:
                    scores_ok = False
                    score_details.append(
                        f"{name}: score={actual:.3f}, expected≈{expected_score:.3f} "
                        f"(budget={BUDGET:.2f}%, penalty rules apply)"
                    )
                else:
                    score_details.append(f"{name}: score={actual:.3f} ✓")
            
            if scores_ok:
                ok("quota_analysis_scores_correct", "; ".join(score_details))
            else:
                fail("quota_analysis_scores_correct",
                     "; ".join(score_details) +
                     f" | budget={(ELAPSED_HOURS/168*100):.3f}% for {ELAPSED_HOURS}h elapsed")
        
        # ── Check winner ──────────────────────────────────────────
        winner_found = None
        # Look in multiple possible locations
        for k in ["winner", "recommended", "best_account", "selected", "auto_select"]:
            if k in qa:
                val = qa[k]
                if isinstance(val, str):
                    winner_found = val.lower()
                elif isinstance(val, dict):
                    winner_found = val.get("name", val.get("account", "")).lower()
                break
        
        # Also check top-level "account" key
        if not winner_found and "account" in qa:
            winner_found = str(qa["account"]).lower()
        
        # Check within accounts section for a "winner" flag
        if not winner_found:
            accounts_section = qa.get("accounts", qa)
            for name in ["oliver", "elise", "sylvia"]:
                entry = accounts_section.get(name, {})
                if isinstance(entry, dict):
                    if entry.get("winner") or entry.get("recommended") or entry.get("selected"):
                        winner_found = name.lower()
                        break
        
        if not winner_found:
            fail("quota_analysis_winner_correct",
                 f"Could not find winner/recommended field in quota_analysis.json. "
                 f"Keys found: {list(qa.keys())}")
        elif EXPECTED_WINNER in winner_found:
            ok("quota_analysis_winner_correct",
               f"Winner correctly identified as '{winner_found}' "
               f"(elise has lowest score ≈{EXPECTED_SCORES['elise']:.2f})")
        else:
            fail("quota_analysis_winner_correct",
                 f"Winner is '{winner_found}', expected '{EXPECTED_WINNER}'. "
                 f"Elise has the lowest budget-adjusted score ({EXPECTED_SCORES['elise']:.2f}) "
                 f"because: weekly=48% is below budget={BUDGET:.1f}%, and 5h=40% avoids penalty.")


# ─────────────────────────────────────────────────────────────
# Final scoring
# ─────────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
score = len(passed_checks) / len(checks) if checks else 0.0

result = {
    "passed": overall_passed,
    "score": round(score, 3),
    "checks": checks,
}
print(json.dumps(result, indent=2))