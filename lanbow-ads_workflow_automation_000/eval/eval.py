import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the output file ---
    candidates = list(workspace.rglob("campaign_ops_brief.md"))
    if not candidates:
        # Also accept .txt with exact name
        candidates = list(workspace.rglob("campaign_ops_brief.txt"))

    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named 'campaign_ops_brief.md' or 'campaign_ops_brief.txt'" if file_found else "No file named 'campaign_ops_brief.md' or 'campaign_ops_brief.txt' found anywhere in workspace"
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = candidates[0].read_text(encoding="utf-8")
        content_lower = content.lower()
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"File read successfully ({len(content)} chars) from {candidates[0]}"})

    # --- Check 1: All 5 required output sections present ---
    required_sections = [
        ("campaign action plan", "Campaign Action Plan"),
        ("bidding and budget policy", "Bidding and Budget Policy"),
        ("ab test and scale model", "AB Test and Scale Model"),
        ("monitoring and alert plan", "Monitoring and Alert Plan"),
        ("operator handoff checklist", "Operator Handoff Checklist"),
    ]
    section_results = []
    for key, label in required_sections:
        found = key in content_lower
        section_results.append((label, found))

    all_sections_present = all(found for _, found in section_results)
    checks.append({
        "name": "all_five_output_sections_present",
        "passed": all_sections_present,
        "detail": f"Section presence: {[(lbl, found) for lbl, found in section_results]}"
    })

    # --- Check 2: CPA ceiling $42 referenced ---
    cpa_ref = bool(re.search(r'\$?42\b', content) or "cpa.*42" in content_lower or "42.*cpa" in content_lower)
    checks.append({
        "name": "cpa_ceiling_42_referenced",
        "passed": cpa_ref,
        "detail": "CPA ceiling of $42 must be explicitly referenced in the policy" if not cpa_ref else "CPA ceiling $42 found"
    })

    # --- Check 3: ROAS floor 2.5 referenced ---
    roas_ref = bool(re.search(r'2\.5', content))
    checks.append({
        "name": "roas_floor_2_5_referenced",
        "passed": roas_ref,
        "detail": "ROAS floor of 2.5 must be explicitly referenced" if not roas_ref else "ROAS floor 2.5 found"
    })

    # --- Check 4: Alert trigger rule — BOTH conditions (roas_drop_pct > 20 AND spend_up_pct > 25) ---
    # Must reference a drop of 20% for ROAS AND a surge of 25% for spend, together
    roas_drop_trigger = bool(re.search(r'20\s*%|roas.{0,40}drop.{0,20}20|20.{0,20}roas.{0,40}drop', content_lower))
    spend_surge_trigger = bool(re.search(r'25\s*%|spend.{0,40}(up|surge|increas).{0,20}25|25.{0,20}spend', content_lower))
    alert_rule_present = roas_drop_trigger and spend_surge_trigger
    checks.append({
        "name": "alert_trigger_rule_both_conditions_present",
        "passed": alert_rule_present,
        "detail": f"Alert rule requires BOTH roas_drop>20% AND spend_up>25%. Found: roas_drop_20={roas_drop_trigger}, spend_25={spend_surge_trigger}"
    })

    # --- Check 5: Containment-first response (anomaly risk → containment before scale) ---
    containment_keywords = ["containment", "contain", "cap budget", "cap_budget", "pause", "halt spend", "freeze spend", "reduce spend"]
    containment_found = any(kw in content_lower for kw in containment_keywords)
    checks.append({
        "name": "containment_first_action_present",
        "passed": containment_found,
        "detail": "High anomaly risk scenario requires containment actions before any scale decisions" if not containment_found else "Containment action found"
    })

    # --- Check 6: Tracking/measurement improvement required before scale ---
    # Decision rule: if measurement confidence is low, limit scale and improve tracking first
    tracking_fix_keywords = [
        "pixel", "tracking", "measurement confidence", "fire rate",
        "server-side", "capi", "events api", "tiktok events", "fix tracking",
        "resolve pixel", "tracking health"
    ]
    tracking_fix_found = any(kw in content_lower for kw in tracking_fix_keywords)
    checks.append({
        "name": "tracking_improvement_required_before_scale",
        "passed": tracking_fix_found,
        "detail": "Low measurement confidence requires tracking fix before scale — must be mentioned" if not tracking_fix_found else "Tracking fix requirement found"
    })

    # --- Check 7: Staged scale / budget mode mentioned ---
    staged_scale_found = bool(
        "staged" in content_lower or
        "staged_scale" in content_lower or
        "stage" in content_lower and "budget" in content_lower or
        "incremental" in content_lower and "budget" in content_lower or
        "phased" in content_lower and "budget" in content_lower
    )
    checks.append({
        "name": "staged_scale_budget_mode_referenced",
        "passed": staged_scale_found,
        "detail": "Budget mode should be staged_scale per campaign spec" if not staged_scale_found else "Staged scale budget mode found"
    })

    # --- Check 8: Rollback conditions attached to recommendations ---
    rollback_keywords = ["rollback", "roll back", "roll-back", "revert", "undo", "fallback", "fall back", "if performance", "if roas", "if cpa exceeds"]
    rollback_found = any(kw in content_lower for kw in rollback_keywords)
    checks.append({
        "name": "rollback_conditions_present",
        "passed": rollback_found,
        "detail": "Constraints require no irreversible changes without rollback conditions" if not rollback_found else "Rollback conditions found"
    })

    # --- Check 9: A/B test concurrency reduction (CPA unstable → reduce experiment concurrency) ---
    ab_concurrency_keywords = [
        "reduce concurrency", "pause test", "hold test", "delay test", "hold a/b", "pause a/b",
        "not launch.*test", "defer.*test", "test.*defer", "cpa.*unstable.*test",
        "unstable.*experiment", "reduce.*experiment", "limit.*test", "suspend.*test"
    ]
    ab_concurrency_found = any(re.search(kw, content_lower) for kw in ab_concurrency_keywords)
    # Also check for general recommendation to NOT launch the AB test while CPA is above ceiling
    ab_hold_found = bool(
        re.search(r"(ab|a/b|a-b).{0,60}(hold|wait|pause|defer|not.*launch|delay)", content_lower) or
        re.search(r"(hold|wait|pause|defer|delay).{0,60}(ab|a/b|a-b|test)", content_lower) or
        "concurrency" in content_lower
    )
    ab_check_passed = ab_concurrency_found or ab_hold_found
    checks.append({
        "name": "ab_test_concurrency_reduction_when_cpa_unstable",
        "passed": ab_check_passed,
        "detail": "CPA is unstable (above ceiling) — decision rules require reducing experiment concurrency; A/B test launch should be deferred" if not ab_check_passed else "A/B test concurrency/deferral handled correctly"
    })

    # --- Check 10: All 3 channels (Meta, Google Ads, TikTok) addressed ---
    meta_found = "meta" in content_lower or "facebook" in content_lower or "instagram" in content_lower
    google_found = "google" in content_lower
    tiktok_found = "tiktok" in content_lower or "tik tok" in content_lower
    all_channels = meta_found and google_found and tiktok_found
    checks.append({
        "name": "all_three_channels_addressed",
        "passed": all_channels,
        "detail": f"Meta={meta_found}, Google={google_found}, TikTok={tiktok_found}. All three channels must be addressed."
    })

    # --- Score calculation ---
    passed_count = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_count / total_checks, 4)
    overall_passed = passed_count >= 9  # Must pass at least 9 of the checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation_error", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))