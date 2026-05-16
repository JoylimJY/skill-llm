#!/usr/bin/env python3
"""
Evaluation script for OpenClaw diagnostics task.
Checks that the agent produced a correct, well-structured diagnostic report
referencing proper slugs, issue categories, and correctly avoiding the
groupPolicy "open" false-positive trap.
"""
import sys
import json
import re
from pathlib import Path

def load_report(workspace: str):
    """Find diagnostic_report.json anywhere in the workspace."""
    hits = list(Path(workspace).rglob("diagnostic_report.json"))
    if not hits:
        return None, "diagnostic_report.json not found in workspace"
    if len(hits) > 1:
        # prefer /workspace/reports/ if exists, else first
        for h in hits:
            if "reports" in str(h):
                return h, None
        return hits[0], None
    return hits[0], None

def check_json_parseable(path):
    try:
        data = json.loads(path.read_text())
        return data, None
    except Exception as e:
        return None, f"JSON parse error: {e}"

def run_checks(workspace: str):
    checks = []
    total_score = 0.0

    # ── CHECK 1: Report file exists ──────────────────────────────────────────
    path, err = load_report(workspace)
    c1 = {"name": "report_file_exists", "passed": False, "detail": ""}
    if err or path is None:
        c1["detail"] = err or "File not found"
        checks.append(c1)
        # Early exit — nothing else to check
        return checks, 0.0
    c1["passed"] = True
    c1["detail"] = f"Found at {path}"
    checks.append(c1)

    # ── CHECK 2: Valid JSON ───────────────────────────────────────────────────
    data, err = check_json_parseable(path)
    c2 = {"name": "valid_json", "passed": False, "detail": ""}
    if err:
        c2["detail"] = err
        checks.append(c2)
        return checks, 0.1
    c2["passed"] = True
    c2["detail"] = "Parses as valid JSON"
    checks.append(c2)

    # ── CHECK 3: Report has issues array ─────────────────────────────────────
    c3 = {"name": "has_issues_array", "passed": False, "detail": ""}
    issues = None
    try:
        # Accept both {"issues": [...]} and a bare list
        if isinstance(data, list):
            issues = data
        elif isinstance(data, dict):
            # Try common keys
            for key in ["issues", "findings", "diagnostics", "results"]:
                if key in data and isinstance(data[key], list):
                    issues = data[key]
                    break
        if issues is not None and len(issues) > 0:
            c3["passed"] = True
            c3["detail"] = f"Found {len(issues)} issue(s) under key"
        else:
            c3["detail"] = f"No 'issues' array found or empty. Keys: {list(data.keys()) if isinstance(data, dict) else 'bare list'}"
    except Exception as e:
        c3["detail"] = f"Exception: {e}"
    checks.append(c3)

    if issues is None:
        # Try to work with whatever structure we have for slug checks
        issues = []
        raw_text = path.read_text()
    else:
        raw_text = path.read_text()

    # ── CHECK 4: groupPolicy "open" NOT flagged as misconfiguration ───────────
    # This is the proprietary trap: groupPolicy open is VALID
    c4 = {"name": "no_false_positive_group_policy_open", "passed": False, "detail": ""}
    try:
        raw_lower = raw_text.lower()
        # Detect if agent wrongly marks groupPolicy:open as a problem
        false_positive_patterns = [
            r'grouppolicy.*open.*misconfigur',
            r'grouppolicy.*open.*issue',
            r'grouppolicy.*open.*problem',
            r'grouppolicy.*open.*fix',
            r'grouppolicy.*open.*broken',
            r'grouppolicy.*open.*error',
            r'grouppolicy.*open.*invalid',
            r'"is_misconfiguration":\s*true[^}]*grouppolicy',
            r'grouppolicy[^}]*"is_misconfiguration":\s*true',
        ]
        # Also check issue entries: if any issue has category/root_cause mentioning "open" groupPolicy as a fault
        flagged = False
        for pat in false_positive_patterns:
            if re.search(pat, raw_lower):
                flagged = True
                break

        # Check structured issues too
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            issue_str = json.dumps(issue).lower()
            # If an issue references groupPolicy AND marks it as misconfiguration
            if "grouppolicy" in issue_str or "group_policy" in issue_str or "group-policy" in issue_str:
                is_misconfig = issue.get("is_misconfiguration", None)
                if is_misconfig is True:
                    # Check if root cause / description mentions "open"
                    if "open" in issue_str:
                        flagged = True

        if not flagged:
            c4["passed"] = True
            c4["detail"] = "groupPolicy 'open' correctly NOT flagged as a misconfiguration"
        else:
            c4["detail"] = "FAIL: groupPolicy 'open' was incorrectly flagged as a misconfiguration — this is valid config per SKILL.md"
    except Exception as e:
        c4["detail"] = f"Exception during check: {e}"
    checks.append(c4)

    # ── CHECK 5: Group messaging issue identified with slug 008888be ──────────
    c5 = {"name": "group_messaging_issue_with_correct_slug", "passed": False, "detail": ""}
    try:
        has_slug = "008888be" in raw_text
        # Check that the group messaging issue is present AND correctly attributed to ackReactionScope
        has_ack = "ackreactionscope" in raw_text.lower() or "ack_reaction_scope" in raw_text.lower() or "group-mentions" in raw_text.lower()
        # Must NOT be flagged as is_misconfiguration: true (it's a user behavior issue)
        # Check structured issues
        group_issue_correct = False
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            issue_str = json.dumps(issue).lower()
            slugs = issue.get("reference_slugs", issue.get("references", issue.get("slugs", [])))
            if not isinstance(slugs, list):
                slugs = [str(slugs)]
            has_008 = "008888be" in json.dumps(slugs)
            is_misc = issue.get("is_misconfiguration", None)
            category = str(issue.get("category", "")).lower()
            # Should be group-messaging category, reference 008888be, and is_misconfiguration should be false
            if has_008 and is_misc is False and ("group" in category or "group" in issue_str):
                group_issue_correct = True

        # Fallback: if structured check fails, at least verify slug presence + ack mention
        if group_issue_correct:
            c5["passed"] = True
            c5["detail"] = "Group messaging issue found: references slug 008888be, is_misconfiguration=false"
        elif has_slug and has_ack:
            c5["passed"] = True
            c5["detail"] = "Group messaging issue found: slug 008888be and ackReactionScope present (loose check)"
        else:
            missing = []
            if not has_slug:
                missing.append("slug 008888be")
            if not has_ack:
                missing.append("ackReactionScope/group-mentions reference")
            c5["detail"] = f"Missing: {', '.join(missing)}"
    except Exception as e:
        c5["detail"] = f"Exception: {e}"
    checks.append(c5)

    # ── CHECK 6: Cron job issue identified with slug b239629c ─────────────────
    c6 = {"name": "cron_issue_with_correct_slug", "passed": False, "detail": ""}
    try:
        has_cron_slug = "b239629c" in raw_text
        # Must identify at least one cron issue: gateway not running OR enabled: false
        has_gateway_cause = "gateway" in raw_text.lower() and (
            "stopped" in raw_text.lower() or "not running" in raw_text.lower() or "running" in raw_text.lower()
        )
        has_enabled_cause = "enabled" in raw_text.lower() and "false" in raw_text.lower()

        if has_cron_slug and (has_gateway_cause or has_enabled_cause):
            c6["passed"] = True
            detail_parts = ["slug b239629c present"]
            if has_gateway_cause:
                detail_parts.append("gateway running status identified as cause")
            if has_enabled_cause:
                detail_parts.append("enabled:false identified")
            c6["detail"] = "; ".join(detail_parts)
        else:
            missing = []
            if not has_cron_slug:
                missing.append("slug b239629c")
            if not has_gateway_cause and not has_enabled_cause:
                missing.append("root cause (gateway stopped or enabled=false)")
            c6["detail"] = f"Missing: {', '.join(missing)}"
    except Exception as e:
        c6["detail"] = f"Exception: {e}"
    checks.append(c6)

    # ── CHECK 7: WhatsApp/channel connection issue with slug d09047a0 or 919c126f ──
    c7 = {"name": "channel_connection_issue_identified", "passed": False, "detail": ""}
    try:
        has_wa_slug = "d09047a0" in raw_text or "919c126f" in raw_text or "87e3285b" in raw_text
        has_channel_context = (
            "whatsapp" in raw_text.lower() or "channel" in raw_text.lower()
        ) and (
            "disconnected" in raw_text.lower()
            or "session" in raw_text.lower()
            or "pair" in raw_text.lower()
            or "reconnect" in raw_text.lower()
            or "auth" in raw_text.lower()
        )
        if has_wa_slug and has_channel_context:
            c7["passed"] = True
            c7["detail"] = "Channel connection issue identified with relevant slug(s)"
        else:
            missing = []
            if not has_wa_slug:
                missing.append("relevant channel slug (d09047a0 or 919c126f or 87e3285b)")
            if not has_channel_context:
                missing.append("channel disconnect/session/auth context")
            c7["detail"] = f"Missing: {', '.join(missing)}"
    except Exception as e:
        c7["detail"] = f"Exception: {e}"
    checks.append(c7)

    # ── CHECK 8: Issues have required fields per common-issues.md ─────────────
    c8 = {"name": "issues_have_required_fields", "passed": False, "detail": ""}
    try:
        required_fields = {"issue_id", "category", "root_cause", "is_misconfiguration", "reference_slugs", "recommended_action"}
        # Also accept common variations
        field_aliases = {
            "issue_id": ["issue_id", "id", "issue"],
            "category": ["category", "type"],
            "root_cause": ["root_cause", "cause", "diagnosis"],
            "is_misconfiguration": ["is_misconfiguration", "misconfiguration", "is_config_issue"],
            "reference_slugs": ["reference_slugs", "references", "slugs", "docs"],
            "recommended_action": ["recommended_action", "action", "fix", "recommendation", "remedy"],
        }
        if issues:
            first = issues[0]
            if isinstance(first, dict):
                found_fields = set(first.keys())
                found_count = 0
                for canonical, aliases in field_aliases.items():
                    if any(a in found_fields for a in aliases):
                        found_count += 1
                if found_count >= 5:
                    c8["passed"] = True
                    c8["detail"] = f"Issue entries contain {found_count}/6 required fields"
                else:
                    c8["detail"] = f"Only {found_count}/6 required field types found. First issue keys: {list(found_fields)}"
            else:
                c8["detail"] = f"Issues are not dicts, type: {type(first)}"
        else:
            # Fallback: check raw text for field names
            raw_lower = raw_text.lower()
            found = sum(1 for aliases in field_aliases.values() if any(a in raw_lower for a in aliases))
            if found >= 5:
                c8["passed"] = True
                c8["detail"] = f"Required field names found in raw text ({found}/6)"
            else:
                c8["detail"] = f"Required fields not found in raw JSON (found {found}/6). No structured issues array."
    except Exception as e:
        c8["detail"] = f"Exception: {e}"
    checks.append(c8)

    # ── CHECK 9: ackReactionScope correctly identified as non-misconfiguration ─
    c9 = {"name": "ackReactionScope_not_flagged_as_bug", "passed": False, "detail": ""}
    try:
        # Find any issue related to group messaging
        flagged_as_bug = False
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            issue_str = json.dumps(issue).lower()
            if "ackreactionscope" in issue_str or "group-mentions" in issue_str or "group_mention" in issue_str:
                is_misc = issue.get("is_misconfiguration", None)
                if is_misc is True:
                    flagged_as_bug = True

        if not flagged_as_bug:
            # Also check raw text for contradictory statements
            bad_patterns = [
                r'ackreactionscope.*group.mentions.*misconfigur',
                r'ackreactionscope.*group.mentions.*broken',
                r'ackreactionscope.*group.mentions.*bug',
                r'ackreactionscope.*group.mentions.*fix.*config',
            ]
            for pat in bad_patterns:
                if re.search(pat, raw_text.lower()):
                    flagged_as_bug = True
                    break

        if not flagged_as_bug:
            c9["passed"] = True
            c9["detail"] = "ackReactionScope 'group-mentions' correctly handled as non-misconfiguration (user behavior issue)"
        else:
            c9["detail"] = "FAIL: ackReactionScope 'group-mentions' incorrectly flagged as a config bug"
    except Exception as e:
        c9["detail"] = f"Exception: {e}"
    checks.append(c9)

    # ── CHECK 10: At least 3 distinct issues reported ─────────────────────────
    c10 = {"name": "at_least_three_issues_reported", "passed": False, "detail": ""}
    try:
        if len(issues) >= 3:
            c10["passed"] = True
            c10["detail"] = f"{len(issues)} issues found in report"
        else:
            # Check if report text covers all 3 incident types even if not in array
            coverage = sum([
                "group" in raw_text.lower() and "mention" in raw_text.lower(),
                "cron" in raw_text.lower() or "scheduled" in raw_text.lower(),
                "whatsapp" in raw_text.lower() or "channel" in raw_text.lower(),
            ])
            if coverage >= 3:
                c10["passed"] = True
                c10["detail"] = f"All 3 issue domains covered in report text (issues array has {len(issues)})"
            else:
                c10["detail"] = f"Only {len(issues)} structured issues, coverage of {coverage}/3 domains in text"
    except Exception as e:
        c10["detail"] = f"Exception: {e}"
    checks.append(c10)

    # ── Score calculation ─────────────────────────────────────────────────────
    weights = {
        "report_file_exists": 0.05,
        "valid_json": 0.05,
        "has_issues_array": 0.08,
        "no_false_positive_group_policy_open": 0.15,   # Proprietary trap
        "group_messaging_issue_with_correct_slug": 0.15,
        "cron_issue_with_correct_slug": 0.15,
        "channel_connection_issue_identified": 0.10,
        "issues_have_required_fields": 0.10,
        "ackReactionScope_not_flagged_as_bug": 0.12,  # Proprietary trap #2
        "at_least_three_issues_reported": 0.05,
    }
    score = sum(weights.get(c["name"], 0.0) for c in checks if c["passed"])
    return checks, round(score, 4)


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, score = run_checks(workspace)
    passed = score >= 0.70
    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    main()