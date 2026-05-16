import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, "r") as f:
        return json.load(f)

def find_config_file(workspace):
    candidates = list(Path(workspace).rglob("lists_config.json"))
    if not candidates:
        return None
    return candidates[0]

def check(name, condition, detail_pass, detail_fail):
    passed = bool(condition)
    return {"name": name, "passed": passed, "detail": detail_pass if passed else detail_fail}

def run_eval(workspace):
    checks = []
    score = 0.0
    total_checks = 26

    # Find the file
    config_path = find_config_file(workspace)
    if not config_path:
        checks.append({"name": "lists_config.json exists", "passed": False, "detail": "File not found anywhere in workspace"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "lists_config.json exists", "passed": True, "detail": f"Found at {config_path}"})

    try:
        data = load_json_file(config_path)
    except Exception as e:
        checks.append({"name": "JSON parseable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "JSON parseable", "passed": True, "detail": "Valid JSON"})

    # Must be a dict with a "lists" key containing a list
    try:
        lists = data.get("lists", [])
        assert isinstance(lists, list)
    except Exception as e:
        checks.append({"name": "Has 'lists' array", "passed": False, "detail": f"Missing or invalid 'lists' key: {e}"})
        print(json.dumps({"passed": False, "score": len([c for c in checks if c["passed"]]) / total_checks, "checks": checks}))
        return

    checks.append(check("Has 'lists' array", True, "lists array found", ""))

    # Helper: normalize strings
    def norm(s):
        return str(s).lower().strip()

    def find_list(lists, name_fragment):
        for l in lists:
            if name_fragment.lower() in norm(l.get("name", "")):
                return l
        return None

    def list_contains_filter(lst, field_fragment, value_fragment=None, operator_fragment=None):
        """Recursively search for a filter matching field and optionally value."""
        raw = json.dumps(lst).lower()
        field_match = field_fragment.lower() in raw
        value_match = (value_fragment is None) or (value_fragment.lower() in raw)
        op_match = (operator_fragment is None) or (operator_fragment.lower() in raw)
        return field_match and value_match and op_match

    # CHECK 1: Exactly 10 lists
    checks.append(check(
        "Exactly 10 lists defined",
        len(lists) == 10,
        f"Found {len(lists)} lists",
        f"Found {len(lists)} lists, expected 10"
    ))

    # CHECK 2: All lists are active (dynamic), not static
    all_active = all(
        "active" in norm(str(l.get("type", ""))) or "dynamic" in norm(str(l.get("type", "")))
        for l in lists
    )
    checks.append(check(
        "All lists are type 'active' (dynamic)",
        all_active,
        "All lists marked as active/dynamic",
        "One or more lists are not marked as active/dynamic"
    ))

    # --- LIST 1: Marketable - Active ---
    l1 = find_list(lists, "marketable")
    checks.append(check("List 1: Marketable - Active exists", l1 is not None, "Found", "Not found"))

    if l1:
        raw1 = json.dumps(l1).lower()
        # Must have marketing contact status filter
        checks.append(check(
            "List 1: marketing contact status filter",
            "marketing contact" in raw1,
            "marketing contact filter present",
            "Missing marketing contact status filter"
        ))
        # Must have unsubscribed filter
        checks.append(check(
            "List 1: unsubscribed filter",
            "unsubscribed" in raw1,
            "unsubscribed filter present",
            "Missing unsubscribed filter"
        ))
        # Must have hard bounce reason is unknown (proprietary HubSpot filter - not just "bounced")
        checks.append(check(
            "List 1: hard bounce reason is unknown (proprietary filter)",
            ("hard bounce" in raw1 or "hard_bounce" in raw1) and ("unknown" in raw1),
            "hard bounce reason > is unknown filter present",
            "Missing 'hard bounce reason is unknown' filter — agent likely used generic 'not bounced' instead"
        ))
        # Must have email is known
        checks.append(check(
            "List 1: email is known filter",
            "email" in raw1 and ("is_known" in raw1 or "is known" in raw1 or "known" in raw1),
            "email is known filter present",
            "Missing email is known filter"
        ))
        # Must have email quarantined filter (often missed)
        checks.append(check(
            "List 1: email quarantined filter",
            "quarantined" in raw1,
            "email quarantined filter present",
            "Missing email quarantined filter — common omission"
        ))

    # --- LIST 2: ICP Tier 1 ---
    l2 = find_list(lists, "tier 1")
    checks.append(check("List 2: ICP Tier 1 Contacts exists", l2 is not None, "Found", "Not found"))

    if l2:
        raw2 = json.dumps(l2).lower()
        checks.append(check(
            "List 2: uses list membership to Marketable - Active (dependency chain)",
            ("list membership" in raw2 or "member of" in raw2 or "marketable" in raw2),
            "List membership / marketable dependency present",
            "Missing list membership filter referencing Marketable - Active — must NOT re-implement deliverability logic"
        ))
        checks.append(check(
            "List 2: ICP Tier filter = Tier 1",
            "tier 1" in raw2 or "tier-1" in raw2 or "primary icp" in raw2,
            "Tier 1 filter present",
            "Missing ICP Tier 1 filter"
        ))

    # --- LIST 3: ICP Tier 2 ---
    l3 = find_list(lists, "tier 2")
    checks.append(check("List 3: ICP Tier 2 Contacts exists", l3 is not None, "Found", "Not found"))

    if l3:
        raw3 = json.dumps(l3).lower()
        checks.append(check(
            "List 3: uses list membership to Marketable - Active",
            ("list membership" in raw3 or "member of" in raw3 or "marketable" in raw3),
            "List membership / marketable dependency present",
            "Missing list membership filter — must chain from List 1"
        ))

    # --- LIST 4: Engaged (Active Window) - 90 days, OR logic ---
    l4 = find_list(lists, "engaged")
    if l4 is None:
        l4 = find_list(lists, "active window")
    checks.append(check("List 4: Engaged list exists", l4 is not None, "Found", "Not found"))

    if l4:
        raw4 = json.dumps(l4).lower()
        # Must use 90 days (from company profile)
        checks.append(check(
            "List 4: engagement window is 90 days",
            "90" in raw4,
            "90-day window present",
            "Missing 90-day engagement window — must use company_profile.json value"
        ))
        # Must have OR logic
        checks.append(check(
            "List 4: OR logic between filter groups",
            ("or" in raw4) and ("logic" in raw4 or "group" in raw4 or "operator" in raw4 or "condition" in raw4 or raw4.count('"or"') > 0 or "\"or\"" in json.dumps(l4).lower() or "'or'" in raw4),
            "OR logic present",
            "Missing OR logic between engagement filter groups"
        ))
        # Must have sessions / website
        checks.append(check(
            "List 4: includes website sessions filter",
            "session" in raw4 or "website" in raw4,
            "Sessions filter present",
            "Missing website sessions filter"
        ))

    # --- LIST 7: Re-engagement Needed - 180 days, AND logic, List 1 dependency ---
    l7 = find_list(lists, "re-engagement")
    if l7 is None:
        l7 = find_list(lists, "re engagement")
    if l7 is None:
        l7 = find_list(lists, "reengagement")
    checks.append(check("List 7: Re-engagement Needed exists", l7 is not None, "Found", "Not found"))

    if l7:
        raw7 = json.dumps(l7).lower()
        # Must use 180 days (from company profile)
        checks.append(check(
            "List 7: re-engagement window is 180 days",
            "180" in raw7,
            "180-day window present",
            "Missing 180-day re-engagement window — must use company_profile.json value"
        ))
        # Must have 5+ emails delivered threshold
        checks.append(check(
            "List 7: 5+ emails delivered threshold",
            "5" in raw7 and ("delivered" in raw7 or "emails" in raw7),
            "5 emails delivered threshold present",
            "Missing '5+ emails delivered' filter"
        ))
        # Must use list membership to Marketable - Active
        checks.append(check(
            "List 7: uses list membership to Marketable - Active",
            ("list membership" in raw7 or "member of" in raw7 or "marketable" in raw7),
            "List membership dependency present",
            "Missing Marketable - Active dependency in Re-engagement list"
        ))

    # --- LIST 8: Senior Decision Makers - must use company profile titles ---
    l8 = find_list(lists, "senior decision")
    if l8 is None:
        l8 = find_list(lists, "decision maker")
    checks.append(check("List 8: Senior Decision Makers exists", l8 is not None, "Found", "Not found"))

    if l8:
        raw8 = json.dumps(l8).lower()
        # Must include company-specific titles from profile
        has_cto = "cto" in raw8 or "chief technology" in raw8
        has_vp_ops = "vp of operations" in raw8 or "operations" in raw8
        has_procurement = "procurement" in raw8
        checks.append(check(
            "List 8: uses company-profile job titles (CTO, VP of Operations, Director of Procurement)",
            has_cto and has_vp_ops and has_procurement,
            "Company-specific titles found",
            f"Missing expected titles — CTO:{has_cto}, VP Ops:{has_vp_ops}, Procurement:{has_procurement}"
        ))

    # --- LIST 9: Industry Leaders - must use company profile industries ---
    l9 = find_list(lists, "industry")
    checks.append(check("List 9: Industry Leaders exists", l9 is not None, "Found", "Not found"))

    if l9:
        raw9 = json.dumps(l9).lower()
        has_manufacturing = "manufacturing" in raw9
        has_logistics = "logistics" in raw9
        checks.append(check(
            "List 9: uses company-profile industries (Manufacturing, Logistics)",
            has_manufacturing and has_logistics,
            "Company-specific industries found",
            f"Missing industries — Manufacturing:{has_manufacturing}, Logistics:{has_logistics}"
        ))

    # --- LIST 10: Content Engaged - OR logic, form submissions + conversion keywords ---
    l10 = find_list(lists, "content")
    checks.append(check("List 10: Content Engaged exists", l10 is not None, "Found", "Not found"))

    if l10:
        raw10 = json.dumps(l10).lower()
        checks.append(check(
            "List 10: includes form submissions filter",
            "form submission" in raw10 or "form_submission" in raw10 or "submissions" in raw10,
            "Form submissions filter present",
            "Missing form submissions filter"
        ))
        # Must include content keywords from company profile
        has_keywords = any(kw.lower() in raw10 for kw in ["download", "guide", "whitepaper", "checklist", "e-book", "ebook"])
        checks.append(check(
            "List 10: includes content keywords (Download, Guide, Whitepaper, etc.)",
            has_keywords,
            "Content keywords present",
            "Missing content keywords — must reference company_profile.json content_keywords"
        ))

    # Score
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total_checks, 4)
    overall_passed = score >= 0.80

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)