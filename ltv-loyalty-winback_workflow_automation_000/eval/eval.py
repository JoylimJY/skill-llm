import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    # --- Find the output file ---
    candidates = list(workspace.rglob("winback_strategy.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [check("output_file_exists", False, "winback_strategy.md not found anywhere in workspace")]
        }

    output_file = candidates[0]
    try:
        content = output_file.read_text(encoding="utf-8")
        content_lower = content.lower()
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [check("output_file_readable", False, f"Could not read file: {e}")]
        }

    checks.append(check("output_file_exists", True, f"Found at {output_file}"))

    # --- CHECK 1: Risk summary section present ---
    has_risk_summary = bool(
        re.search(r"(risk\s+summar|silent\s+customer|churn\s+risk|non.repurchase|lapse|at.risk|high.risk)", content_lower)
    )
    checks.append(check(
        "risk_summary_present",
        has_risk_summary,
        "Risk summary section with silence/churn classification found" if has_risk_summary else "No risk summary or silence classification found"
    ))

    # --- CHECK 2: VIP branch present ---
    has_vip_branch = bool(
        re.search(r"(vip|high.value|platinum|gold\s+tier|top\s+decile|high\s+ltv)", content_lower)
    )
    checks.append(check(
        "vip_branch_present",
        has_vip_branch,
        "VIP/high-value segment branch found" if has_vip_branch else "No VIP or high-value branch found"
    ))

    # --- CHECK 3: Standard buyer branch present ---
    has_standard_branch = bool(
        re.search(r"(standard\s+buyer|standard\s+customer|standard\s+segment|standard\s+branch|non.vip|regular\s+customer)", content_lower)
    )
    checks.append(check(
        "standard_branch_present",
        has_standard_branch,
        "Standard buyer segment branch found" if has_standard_branch else "No standard buyer branch found"
    ))

    # --- CHECK 4: Win-back plan table with required columns ---
    # Must have: Segment, Silence signal, Action, Channel, Timing
    table_headers = ["segment", "silence signal", "action", "channel", "timing"]
    found_headers = [h for h in table_headers if h in content_lower]
    table_score = len(found_headers) / len(table_headers)
    has_table = table_score >= 0.8  # at least 4/5 columns
    checks.append(check(
        "winback_table_required_columns",
        has_table,
        f"Win-back table columns found: {found_headers} ({len(found_headers)}/{len(table_headers)})"
    ))

    # --- CHECK 5: Points expiry branch present (MANDATORY since points data exists with imminent expiry) ---
    has_points_branch = bool(
        re.search(r"(point[s]?\s+expir|expir.*point|redeem\s+nudge|pre.expir|points\s+at\s+risk|burn.*point|point.*burn)", content_lower)
    )
    checks.append(check(
        "points_expiry_branch_present",
        has_points_branch,
        "Points expiry branch/sequence found" if has_points_branch else "MISSING: No points expiry branch found despite imminent expiry data in tier_points.csv"
    ))

    # --- CHECK 6: VIP branch is NON-PRICE-FIRST (must mention concierge/early access/perk/bundle, not only discount) ---
    # Check that VIP section doesn't ONLY have discount language — must have non-price value
    non_price_vip_terms = [
        "concierge", "early access", "perk", "bundle", "white.glove", "named contact",
        "dedicated", "restock", "exclusive", "priority", "personal"
    ]
    has_non_price_vip = any(re.search(term, content_lower) for term in non_price_vip_terms)
    checks.append(check(
        "vip_non_price_first",
        has_non_price_vip,
        f"VIP branch includes non-price-first value (concierge/early access/perk/etc.)" if has_non_price_vip else "MISSING: VIP branch appears to only offer discounts, must include non-price-first value (concierge, early access, bundle, etc.)"
    ))

    # --- CHECK 7: Standard branch has time-bound offer ---
    has_timebound = bool(
        re.search(r"(time.bound|expires|end\s+date|valid\s+until|limited.time|deadline|code\s+expires|offer\s+ends|by\s+day|use\s+by)", content_lower)
    )
    checks.append(check(
        "standard_branch_timebound_offer",
        has_timebound,
        "Standard branch includes time-bound offer/deadline" if has_timebound else "MISSING: Standard branch needs a time-bound offer with end date"
    ))

    # --- CHECK 8: VIP escalation path present ---
    has_escalation = bool(
        re.search(r"(escalat|no\s+response|follow.up|if\s+no\s+reply|unanswered|second\s+touch|escalate)", content_lower)
    )
    checks.append(check(
        "vip_escalation_path",
        has_escalation,
        "VIP escalation path (if no response) found" if has_escalation else "MISSING: VIP branch requires escalation path if no response"
    ))

    # --- CHECK 9: Success metrics present ---
    success_metric_terms = ["reactivation rate", "incremental revenue", "unsubscribe", "complaint rate", "holdout", "success metric"]
    found_metrics = [t for t in success_metric_terms if t in content_lower]
    has_metrics = len(found_metrics) >= 2
    checks.append(check(
        "success_metrics_present",
        has_metrics,
        f"Success metrics found: {found_metrics}" if has_metrics else f"MISSING: Need at least 2 success metrics (reactivation rate, incremental revenue, unsubscribe/complaint rate). Found: {found_metrics}"
    ))

    # --- CHECK 10: Win-back table has VIP AND Standard AND Points rows ---
    has_vip_row = bool(re.search(r"(vip|platinum|gold).*\|.*\|", content_lower))
    has_standard_row = bool(re.search(r"(standard).*\|.*\|", content_lower))
    has_points_row = bool(re.search(r"(point[s]?\s+at\s+risk|expir.*\||\|\s*point)", content_lower))
    all_rows = has_vip_row and has_standard_row and has_points_row
    checks.append(check(
        "table_has_all_three_segment_rows",
        all_rows,
        f"Table rows: VIP={has_vip_row}, Standard={has_standard_row}, Points={has_points_row}" 
    ))

    # --- CHECK 11: Does NOT confuse with affiliate or checkout skill ---
    # Should not be primarily about affiliate or abandoned cart
    bad_focus = bool(re.search(r"(affiliate\s+commission|abandoned\s+cart|session\s+drop|checkout\s+abandon)", content_lower))
    checks.append(check(
        "no_wrong_skill_bleed",
        not bad_focus,
        "Document correctly scoped to post-purchase lapse (no affiliate/checkout confusion)" if not bad_focus else "WARNING: Document appears to include affiliate reconciliation or abandoned checkout content (wrong skill)"
    ))

    # --- CHECK 12: Channel specification in table rows ---
    channel_terms = ["email", "sms", "app push", "call", "push"]
    found_channels = [c for c in channel_terms if c in content_lower]
    has_channels = len(found_channels) >= 2
    checks.append(check(
        "channels_specified_in_plan",
        has_channels,
        f"Channels specified: {found_channels}" if has_channels else "MISSING: Win-back plan must specify channels (email, SMS, call, app push, etc.)"
    ))

    # --- Scoring ---
    critical_checks = [
        "risk_summary_present",
        "vip_branch_present",
        "standard_branch_present",
        "winback_table_required_columns",
        "points_expiry_branch_present",
        "vip_non_price_first",
        "standard_branch_timebound_offer",
        "vip_escalation_path",
        "success_metrics_present",
        "table_has_all_three_segment_rows",
    ]

    passed_checks = {c["name"]: c["passed"] for c in checks}
    critical_passed = sum(1 for c in critical_checks if passed_checks.get(c, False))
    total_passed = sum(1 for c in checks if c["passed"])

    score = round(critical_passed / len(critical_checks), 3)
    overall_passed = critical_passed >= 8  # must pass 8/10 critical checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))