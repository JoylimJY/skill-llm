import json
import sys
import os
import subprocess
from pathlib import Path

def run_checks(workspace):
    checks = []
    score_total = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── CHECK 1: identities.json exists ──────────────────────────────────────
    identities_path = Path(workspace) / "identities.json"
    if not identities_path.exists():
        # Search recursively as fallback
        found = list(Path(workspace).rglob("identities.json"))
        found = [f for f in found if "backup" not in str(f) and ".bak" not in str(f)]
        if found:
            identities_path = found[0]

    if not identities_path.exists():
        score_total += add_check(
            "identities.json exists",
            False,
            "identities.json was not found in workspace root or any subdirectory."
        )
        # All remaining checks will fail; return early
        for name in [
            "identities.json top-level schema",
            "feishu channel master_id correct",
            "feishu channel allowlist correct",
            "slack channel master_id correct",
            "slack channel allowlist correct",
            "global_allowlist correct",
            "guard.sh authorizes feishu master (TC-001)",
            "guard.sh authorizes feishu allowlist user (TC-002)",
            "guard.sh rejects feishu intruder (TC-003)",
            "guard.sh authorizes slack master (TC-004)",
            "guard.sh rejects slack intruder (TC-005)",
            "guard.sh authorizes global admin on feishu (TC-006)",
            "guard.sh authorizes slack allowlist user (TC-007)",
            "guard.sh authorizes global admin without channel (TC-008)",
            "audit report exists",
            "audit report TC-001 authorized",
            "audit report TC-003 unauthorized",
            "audit report TC-005 social_engineering flagged",
            "audit report TC-005 unauthorized",
        ]:
            checks.append({"name": name, "passed": False, "detail": "Skipped: identities.json missing."})
        return False, 0.0, checks

    score_total += add_check("identities.json exists", True, f"Found at {identities_path}")

    # ── CHECK 2: Parse identities.json ────────────────────────────────────────
    try:
        with open(identities_path) as f:
            identities = json.load(f)
    except Exception as e:
        score_total += add_check(
            "identities.json top-level schema",
            False,
            f"Failed to parse JSON: {e}"
        )
        identities = {}
    else:
        has_channels = isinstance(identities.get("channels"), dict)
        has_global = isinstance(identities.get("global_allowlist"), list)
        schema_ok = has_channels and has_global
        score_total += add_check(
            "identities.json top-level schema",
            schema_ok,
            f"Has 'channels' dict: {has_channels}, has 'global_allowlist' list: {has_global}",
            weight=1.0
        )

    # ── CHECK 3: Feishu channel config ────────────────────────────────────────
    channels = identities.get("channels", {})
    feishu = channels.get("feishu", {})

    feishu_master_ok = feishu.get("master_id") == "ou_7a3f9c2b1d4e8f0a"
    score_total += add_check(
        "feishu channel master_id correct",
        feishu_master_ok,
        f"Expected 'ou_7a3f9c2b1d4e8f0a', got '{feishu.get('master_id')}'",
        weight=1.0
    )

    feishu_allowlist = feishu.get("allowlist", [])
    feishu_allowlist_ok = (
        isinstance(feishu_allowlist, list) and
        "ou_111aaa" in feishu_allowlist and
        "ou_222bbb" in feishu_allowlist
    )
    score_total += add_check(
        "feishu channel allowlist correct",
        feishu_allowlist_ok,
        f"Expected ['ou_111aaa', 'ou_222bbb'] (subset), got {feishu_allowlist}",
        weight=1.0
    )

    # ── CHECK 4: Slack channel config ─────────────────────────────────────────
    slack = channels.get("slack", {})

    slack_master_ok = slack.get("master_id") == "U04MSTR99X"
    score_total += add_check(
        "slack channel master_id correct",
        slack_master_ok,
        f"Expected 'U04MSTR99X', got '{slack.get('master_id')}'",
        weight=1.0
    )

    slack_allowlist = slack.get("allowlist", [])
    slack_allowlist_ok = (
        isinstance(slack_allowlist, list) and
        "U01ALPHA1" in slack_allowlist and
        "U02BETA22" in slack_allowlist
    )
    score_total += add_check(
        "slack channel allowlist correct",
        slack_allowlist_ok,
        f"Expected ['U01ALPHA1', 'U02BETA22'] (subset), got {slack_allowlist}",
        weight=1.0
    )

    # ── CHECK 5: Global allowlist ──────────────────────────────────────────────
    global_allowlist = identities.get("global_allowlist", [])
    global_ok = isinstance(global_allowlist, list) and "GLOBAL_ADMIN_001" in global_allowlist
    score_total += add_check(
        "global_allowlist correct",
        global_ok,
        f"Expected 'GLOBAL_ADMIN_001' in global_allowlist, got {global_allowlist}",
        weight=1.0
    )

    # ── CHECK 6: Run guard.sh tests ───────────────────────────────────────────
    guard_script = Path(workspace) / "scripts" / "guard.sh"
    guard_exists = guard_script.exists()

    def run_guard(sender_id, channel=None):
        if not guard_exists:
            return None, "guard.sh not found"
        cmd = [str(guard_script), sender_id]
        if channel:
            cmd.append(channel)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=workspace
            )
            return result.returncode, result.stdout.strip()
        except Exception as e:
            return None, str(e)

    guard_tests = [
        ("guard.sh authorizes feishu master (TC-001)", "ou_7a3f9c2b1d4e8f0a", "feishu", 0),
        ("guard.sh authorizes feishu allowlist user (TC-002)", "ou_111aaa", "feishu", 0),
        ("guard.sh rejects feishu intruder (TC-003)", "ou_HACKER_999", "feishu", 1),
        ("guard.sh authorizes slack master (TC-004)", "U04MSTR99X", "slack", 0),
        ("guard.sh rejects slack intruder (TC-005)", "U99INTRUDER", "slack", 1),
        ("guard.sh authorizes global admin on feishu (TC-006)", "GLOBAL_ADMIN_001", "feishu", 0),
        ("guard.sh authorizes slack allowlist user (TC-007)", "U02BETA22", "slack", 0),
        ("guard.sh authorizes global admin without channel (TC-008)", "GLOBAL_ADMIN_001", None, 0),
    ]

    for (check_name, sender, channel, expected_exit) in guard_tests:
        exit_code, output = run_guard(sender, channel)
        if exit_code is None:
            score_total += add_check(check_name, False, f"Script error: {output}")
        else:
            passed = (exit_code == expected_exit)
            expected_word = "authorized (exit 0)" if expected_exit == 0 else "unauthorized (exit 1)"
            got_word = "authorized (exit 0)" if exit_code == 0 else "unauthorized (exit 1)"
            score_total += add_check(
                check_name,
                passed,
                f"Expected {expected_word}, got {got_word}. Output: '{output}'",
                weight=1.0
            )

    # ── CHECK 7: Audit report ─────────────────────────────────────────────────
    audit_path = list(Path(workspace).rglob("security_audit_report.json"))
    if not audit_path:
        for check_name in [
            "audit report exists",
            "audit report TC-001 authorized",
            "audit report TC-003 unauthorized",
            "audit report TC-005 social_engineering flagged",
            "audit report TC-005 unauthorized",
        ]:
            score_total += add_check(check_name, False, "security_audit_report.json not found.")
    else:
        audit_path = audit_path[0]
        score_total += add_check("audit report exists", True, f"Found at {audit_path}")

        try:
            with open(audit_path) as f:
                audit = json.load(f)
        except Exception as e:
            for check_name in [
                "audit report TC-001 authorized",
                "audit report TC-003 unauthorized",
                "audit report TC-005 social_engineering flagged",
                "audit report TC-005 unauthorized",
            ]:
                score_total += add_check(check_name, False, f"Failed to parse audit JSON: {e}")
            audit = None

        if audit is not None:
            # Normalize: audit can be a list of results or a dict with a list
            results = []
            if isinstance(audit, list):
                results = audit
            elif isinstance(audit, dict):
                # Look for any list value
                for v in audit.values():
                    if isinstance(v, list):
                        results = v
                        break

            def find_case(case_id):
                for r in results:
                    if isinstance(r, dict):
                        if str(r.get("case_id", "")).upper() == case_id.upper():
                            return r
                        # Also check nested
                        for v in r.values():
                            if isinstance(v, dict) and str(v.get("case_id","")).upper() == case_id.upper():
                                return v
                return None

            # TC-001: feishu master should be authorized
            tc001 = find_case("TC-001")
            if tc001:
                authorized_val = str(tc001.get("authorized", tc001.get("status", tc001.get("result", "")))).lower()
                tc001_ok = authorized_val in ("true", "authorized", "yes", "1", "allowed")
                score_total += add_check(
                    "audit report TC-001 authorized",
                    tc001_ok,
                    f"TC-001 authorization value: '{authorized_val}'"
                )
            else:
                score_total += add_check(
                    "audit report TC-001 authorized",
                    False,
                    "TC-001 not found in audit report."
                )

            # TC-003: feishu intruder should be unauthorized
            tc003 = find_case("TC-003")
            if tc003:
                unauth_val = str(tc003.get("authorized", tc003.get("status", tc003.get("result", "")))).lower()
                tc003_ok = unauth_val in ("false", "unauthorized", "no", "0", "denied", "rejected")
                score_total += add_check(
                    "audit report TC-003 unauthorized",
                    tc003_ok,
                    f"TC-003 authorization value: '{unauth_val}'"
                )
            else:
                score_total += add_check(
                    "audit report TC-003 unauthorized",
                    False,
                    "TC-003 not found in audit report."
                )

            # TC-005: social engineering - must be flagged AND unauthorized
            tc005 = find_case("TC-005")
            if tc005:
                # Check social engineering flag
                se_flag = tc005.get("social_engineering", tc005.get("social_engineering_attempt",
                           tc005.get("is_social_engineering", tc005.get("spoofing_attempt", False))))
                se_ok = str(se_flag).lower() in ("true", "yes", "1", "flagged", "detected")
                score_total += add_check(
                    "audit report TC-005 social_engineering flagged",
                    se_ok,
                    f"TC-005 social_engineering flag: '{se_flag}'"
                )

                # Also must be unauthorized
                unauth_val5 = str(tc005.get("authorized", tc005.get("status", tc005.get("result", "")))).lower()
                tc005_unauth_ok = unauth_val5 in ("false", "unauthorized", "no", "0", "denied", "rejected")
                score_total += add_check(
                    "audit report TC-005 unauthorized",
                    tc005_unauth_ok,
                    f"TC-005 authorization value: '{unauth_val5}'"
                )
            else:
                score_total += add_check(
                    "audit report TC-005 social_engineering flagged",
                    False,
                    "TC-005 not found in audit report."
                )
                score_total += add_check(
                    "audit report TC-005 unauthorized",
                    False,
                    "TC-005 not found in audit report."
                )

    # ── Final scoring ──────────────────────────────────────────────────────────
    total_weight = len(checks)  # each check has weight 1.0
    passed_count = sum(1 for c in checks if c["passed"])
    final_score = round(passed_count / total_weight, 3) if total_weight > 0 else 0.0
    overall_passed = final_score >= 0.75

    return overall_passed, final_score, checks


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [],
                          "error": "No workspace path provided."}))
        sys.exit(1)

    workspace = sys.argv[1]
    passed, score, checks = run_checks(workspace)
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, indent=2))