import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── locate the output file ───────────────────────────────────────────────
    candidates = list(workspace.rglob("taster_box_plan.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                         "detail": "taster_box_plan.md not found anywhere in workspace."}]
        }

    target = candidates[0]
    try:
        content = target.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False,
                         "detail": f"Could not read file: {e}"}]
        }

    content_lower = content.lower()

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 1: file exists and is non-trivial
    # ────────────────────────────────────────────────────────────────────────
    file_ok = len(content.strip()) >= 400
    checks.append({
        "name": "file_exists_and_substantial",
        "passed": file_ok,
        "detail": f"File found at {target}, length={len(content)} chars. Need >=400."
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 2: Summary section present with 3–5 bullet points
    # ────────────────────────────────────────────────────────────────────────
    # Must have a summary section and it must contain bullet-like items
    has_summary_section = bool(re.search(r'(?i)(summary|team\s+summary)', content))
    # Count bullet lines (lines starting with - or *)
    summary_block_match = re.search(
        r'(?i)(summary.*?)(?=\n#{1,3}\s|\Z)', content, re.DOTALL)
    summary_bullets = 0
    if summary_block_match:
        block = summary_block_match.group(1)
        summary_bullets = len(re.findall(r'^\s*[-*]\s+\S', block, re.MULTILINE))
    summary_ok = has_summary_section and (3 <= summary_bullets <= 5)
    checks.append({
        "name": "summary_section_3_to_5_bullets",
        "passed": summary_ok,
        "detail": (f"has_summary={has_summary_section}, bullet_count={summary_bullets}. "
                   "Need a Summary section with 3–5 bullet points per skill spec.")
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 3: All 6 required sections present
    # ────────────────────────────────────────────────────────────────────────
    required_sections = [
        (r'(?i)(subscription\s+box\s+structure|what.{0,10}inside)',          "subscription_box_structure"),
        (r'(?i)(surprise\s+gift\s+logic|gift\s+logic)',                       "surprise_gift_logic"),
        (r'(?i)(subscriber\s+experience|unboxing|pause.{0,10}skip)',          "subscriber_experience"),
        (r'(?i)(fulfillment\s+guardrail|fulfilment\s+guardrail)',              "fulfillment_guardrails"),
        (r'(?i)(metrics|validation\s+plan)',                                   "metrics_and_validation"),
    ]
    section_results = []
    for pattern, label in required_sections:
        found = bool(re.search(pattern, content))
        section_results.append((label, found))

    all_sections_ok = all(r for _, r in section_results)
    checks.append({
        "name": "all_required_sections_present",
        "passed": all_sections_ok,
        "detail": "; ".join(f"{lbl}={'✓' if ok else '✗'}" for lbl, ok in section_results)
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 4: Subscription box structure contains a markdown table
    # ────────────────────────────────────────────────────────────────────────
    # Must have at least one markdown pipe-table
    has_box_table = bool(re.search(r'\|.*Component.*\||\|.*Format.*\||\|.*Coffee\s+count.*\|',
                                    content, re.IGNORECASE))
    checks.append({
        "name": "subscription_box_table_present",
        "passed": has_box_table,
        "detail": ("Subscription box structure must include a markdown table with "
                   "Component/Format/Coffee count columns per skill spec.")
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 5: Curation rule — no-repeat-within-2-months
    # ────────────────────────────────────────────────────────────────────────
    no_repeat_rule = bool(re.search(
        r'(?i)(repeat|same\s+coffee).{0,60}(2\s*months?|two\s*months?)',
        content
    ))
    checks.append({
        "name": "curation_no_repeat_2_months_rule",
        "passed": no_repeat_rule,
        "detail": ("Must state the proprietary curation rule: avoid repeating "
                   "the same coffee within 2 months. Not found.")
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 6: Surprise gift rules table with at least 3 triggers
    # ────────────────────────────────────────────────────────────────────────
    # Look for gift triggers: first box, month 3, at-risk / low engagement
    gift_trigger_first   = bool(re.search(r'(?i)first\s*box', content))
    gift_trigger_month3  = bool(re.search(r'(?i)(month\s*3|3rd\s*month)', content))
    gift_trigger_atrisk  = bool(re.search(r'(?i)(at.{0,5}risk|low\s*engag)', content))
    gift_triggers_ok = gift_trigger_first and gift_trigger_month3 and gift_trigger_atrisk
    checks.append({
        "name": "gift_triggers_first_month3_atrisk",
        "passed": gift_triggers_ok,
        "detail": (f"first_box={gift_trigger_first}, month3={gift_trigger_month3}, "
                   f"at_risk={gift_trigger_atrisk}. All three required per skill spec.")
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 7: Gift guardrail — "do not promise gifts every month"
    # ────────────────────────────────────────────────────────────────────────
    gift_guardrail_ok = bool(re.search(
        r'(?i)(do\s+not\s+promis|not\s+promis|avoid\s+promis).{0,60}(every\s*month|each\s*month|gift)',
        content
    ))
    # Also accept: "unless guaranteed" phrasing
    gift_guardrail_ok = gift_guardrail_ok or bool(re.search(
        r'(?i)(gift|promis).{0,80}(unless.{0,20}guarant|unless.{0,20}fulfil)',
        content
    ))
    checks.append({
        "name": "gift_guardrail_no_promise_every_month",
        "passed": gift_guardrail_ok,
        "detail": ("Must include the guardrail: do not promise gifts every month "
                   "unless guaranteed/consistently fulfillable. Skill spec requirement.")
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 8: Copy blocks — at least 2 of 3 (welcome, next-box preview, milestone)
    # ────────────────────────────────────────────────────────────────────────
    copy_welcome  = bool(re.search(r'(?i)(welcome\s+to|taster\s+club|first\s+box\s+ships)', content))
    copy_preview  = bool(re.search(r'(?i)(next\s+box|preview)', content))
    copy_milestone = bool(re.search(r'(?i)(milestone|thank.{0,10}you|small\s+gift)', content))
    copy_count = sum([copy_welcome, copy_preview, copy_milestone])
    copy_ok = copy_count >= 2
    checks.append({
        "name": "copy_blocks_at_least_2_of_3",
        "passed": copy_ok,
        "detail": (f"welcome={copy_welcome}, next_box_preview={copy_preview}, "
                   f"milestone={copy_milestone}. Need at least 2 of 3 copy blocks.")
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 9: Metrics — primary metrics all present
    # ────────────────────────────────────────────────────────────────────────
    metric_conversion = bool(re.search(r'(?i)(subscription\s+conversion|conversion\s+rate)', content))
    metric_retention  = bool(re.search(r'(?i)(month.1.{0,20}month.2|first.to.second|m1.{0,10}m2)', content))
    metric_churn      = bool(re.search(r'(?i)(monthly\s+churn|churn\s+rate)', content))
    metric_pause      = bool(re.search(r'(?i)(pause.{0,10}skip|skip.{0,10}rate)', content))
    metrics_ok = metric_conversion and metric_retention and metric_churn and metric_pause
    checks.append({
        "name": "primary_metrics_all_four_present",
        "passed": metrics_ok,
        "detail": (f"conversion={metric_conversion}, month1→2_retention={metric_retention}, "
                   f"churn={metric_churn}, pause/skip={metric_pause}. All four required.")
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 10: 30/60/90-day plan present
    # ────────────────────────────────────────────────────────────────────────
    plan_ok = bool(re.search(r'(?i)(30.{0,10}day|30.{0,20}60.{0,20}90)', content))
    checks.append({
        "name": "30_60_90_day_plan_present",
        "passed": plan_ok,
        "detail": "Must include a 30/60/90-day validation plan per skill spec."
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 11: Surprise gift ROI metric (churn delta for gifted vs non-gifted)
    # ────────────────────────────────────────────────────────────────────────
    gift_roi_ok = bool(re.search(
        r'(?i)(gift\s+roi|churn\s+delta|gifted.{0,30}non.{0,10}gifted|gift\s+cost\s+per\s+retained)',
        content
    ))
    checks.append({
        "name": "surprise_gift_roi_metric_present",
        "passed": gift_roi_ok,
        "detail": ("Must define surprise gift ROI as churn delta for gifted vs non-gifted "
                   "cohorts or gift cost per retained subscriber. Skill spec requirement.")
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 12: Rijoy mention (Shopify + loyalty context)
    # ────────────────────────────────────────────────────────────────────────
    rijoy_ok = bool(re.search(r'(?i)rijoy', content))
    checks.append({
        "name": "rijoy_platform_cited",
        "passed": rijoy_ok,
        "detail": ("Rijoy must be cited as the loyalty/campaign platform for Shopify merchants. "
                   "Brand is on Shopify (config/shopify_settings_stub.yaml confirms this).")
    })

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 13: Fulfillment substitution rule present
    # ────────────────────────────────────────────────────────────────────────
    sub_rule_ok = bool(re.search(
        r'(?i)(substitut|same\s+roast|similar\s+origin)',
        content
    ))
    checks.append({
        "name": "fulfillment_substitution_rule",
        "passed": sub_rule_ok,
        "detail": "Must define substitution rules (same roast profile / similar origin) per skill spec."
    })

    # ────────────────────────────────────────────────────────────────────────
    # Scoring
    # ────────────────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)

    # Require at minimum: file exists + all 6 sections + gift triggers + curation rule
    hard_gates = [
        "file_exists_and_substantial",
        "all_required_sections_present",
        "gift_triggers_first_month3_atrisk",
        "curation_no_repeat_2_months_rule",
    ]
    hard_passed = all(
        next((c["passed"] for c in checks if c["name"] == g), False)
        for g in hard_gates
    )
    overall_passed = hard_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))