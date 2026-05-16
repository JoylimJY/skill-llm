import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]
checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ── Find the output file ──────────────────────────────────────────────────────
output_file = None
for candidate in Path(workspace).rglob("q1_q2_newsletter_report.json"):
    output_file = candidate
    break

if output_file is None:
    print(json.dumps({
        "passed": False,
        "score": 0.0,
        "checks": [make_check("output_file_exists", False, "q1_q2_newsletter_report.json not found anywhere in workspace")]
    }))
    sys.exit(0)

try:
    with open(output_file, "r", encoding="utf-8") as f:
        report = json.load(f)
except Exception as e:
    print(json.dumps({
        "passed": False,
        "score": 0.0,
        "checks": [make_check("output_file_parseable", False, f"File found but could not parse JSON: {e}")]
    }))
    sys.exit(0)

checks.append(make_check("output_file_exists", True, f"Found at {output_file}"))

# ── CHECK 1: Growth Summary Section ──────────────────────────────────────────
try:
    gs = report.get("growth_summary", {})
    # Must have loaded all 3 periods
    total_periods = gs.get("total_periods", 0)
    c1_passed = total_periods == 3
    checks.append(make_check(
        "growth_summary_total_periods",
        c1_passed,
        f"Expected total_periods=3, got {total_periods}"
    ))
except Exception as e:
    checks.append(make_check("growth_summary_total_periods", False, str(e)))

try:
    gs = report.get("growth_summary", {})
    # start subscribers should be 5100 (Jan), end should be 5624 (Mar)
    start = gs.get("start_subscribers", None)
    end = gs.get("end_subscribers", None)
    c2_passed = start == 5100 and end == 5624
    checks.append(make_check(
        "growth_summary_subscriber_counts",
        c2_passed,
        f"Expected start=5100, end=5624; got start={start}, end={end}"
    ))
except Exception as e:
    checks.append(make_check("growth_summary_subscriber_counts", False, str(e)))

try:
    gs = report.get("growth_summary", {})
    # net growth: (310-48)+(298-36)+(330-68) = 262+262+262 = 786
    # Jan: 310-48=262, Feb: 298-36=262, Mar: 330-68=262
    total_net = gs.get("total_net_growth", None)
    c3_passed = total_net == 786
    checks.append(make_check(
        "growth_summary_net_growth",
        c3_passed,
        f"Expected total_net_growth=786 (262+262+262), got {total_net}"
    ))
except Exception as e:
    checks.append(make_check("growth_summary_net_growth", False, str(e)))

try:
    gs = report.get("growth_summary", {})
    # source totals: organic=140+130+155=425, referral=95+108+112=315, paid=75+60+63=198
    st = gs.get("source_totals", {})
    organic_ok = st.get("organic", 0) == 425
    referral_ok = st.get("referral", 0) == 315
    paid_ok = st.get("paid", 0) == 198
    c4_passed = organic_ok and referral_ok and paid_ok
    checks.append(make_check(
        "growth_summary_source_totals",
        c4_passed,
        f"Expected organic=425, referral=315, paid=198; got {st}"
    ))
except Exception as e:
    checks.append(make_check("growth_summary_source_totals", False, str(e)))

# ── CHECK 2: Growth Projections (6 months ahead) ─────────────────────────────
try:
    projections = report.get("growth_projections", [])
    c5_passed = isinstance(projections, list) and len(projections) == 6
    checks.append(make_check(
        "growth_projections_count",
        c5_passed,
        f"Expected 6 projection periods, got {len(projections)}"
    ))
except Exception as e:
    checks.append(make_check("growth_projections_count", False, str(e)))

try:
    projections = report.get("growth_projections", [])
    # avg net growth of last 3 periods: all are 262, avg=262
    # So after 6 periods from 5624: 5624 + 262*6 = 7196
    if len(projections) >= 6:
        final_proj = projections[-1].get("projected_subscribers", None)
        # Allow small rounding: expect 7196 or 7196.0
        c6_passed = final_proj is not None and abs(round(final_proj) - 7196) <= 2
        checks.append(make_check(
            "growth_projections_final_value",
            c6_passed,
            f"Expected final projected_subscribers≈7196, got {final_proj}"
        ))
    else:
        checks.append(make_check("growth_projections_final_value", False, "Not enough projections to check final value"))
except Exception as e:
    checks.append(make_check("growth_projections_final_value", False, str(e)))

# ── CHECK 3: Campaign Analytics Report ───────────────────────────────────────
try:
    camp = report.get("campaign_report", {})
    # Verify correct campaign name is present
    cname = camp.get("campaign_name", "")
    c7_passed = bool(cname)
    checks.append(make_check(
        "campaign_report_present",
        c7_passed,
        f"campaign_report.campaign_name present: '{cname}'"
    ))
except Exception as e:
    checks.append(make_check("campaign_report_present", False, str(e)))

try:
    camp = report.get("campaign_report", {})
    rates = camp.get("rates", {})
    # sent=5624, delivered=5501, opened=1430
    # open_rate = 1430/5501 ≈ 0.2599...
    open_rate = rates.get("open_rate", None)
    c8_passed = open_rate is not None and abs(open_rate - round(1430/5501, 4)) < 0.001
    checks.append(make_check(
        "campaign_report_open_rate",
        c8_passed,
        f"Expected open_rate≈{round(1430/5501,4)}, got {open_rate}"
    ))
except Exception as e:
    checks.append(make_check("campaign_report_open_rate", False, str(e)))

try:
    camp = report.get("campaign_report", {})
    # bounced should be total of hard+soft: 89+34=123
    metrics = camp.get("metrics", {})
    bounced = metrics.get("bounced", None)
    # spam_complaints must be 3 (from spam_reports)
    spam = metrics.get("spam_complaints", None)
    c9_passed = bounced == 123 and spam == 3
    checks.append(make_check(
        "campaign_report_bounced_and_spam",
        c9_passed,
        f"Expected bounced=123 (89+34), spam_complaints=3; got bounced={bounced}, spam_complaints={spam}"
    ))
except Exception as e:
    checks.append(make_check("campaign_report_bounced_and_spam", False, str(e)))

try:
    camp = report.get("campaign_report", {})
    ratings = camp.get("ratings", {})
    # open_rate = 1430/5501 ≈ 0.26 → "good" (>=0.25 but <0.30)
    open_rating = ratings.get("open_rate", "")
    c10_passed = open_rating == "good"
    checks.append(make_check(
        "campaign_report_open_rate_rating",
        c10_passed,
        f"Expected open_rate rating='good', got '{open_rating}'"
    ))
except Exception as e:
    checks.append(make_check("campaign_report_open_rate_rating", False, str(e)))

# ── CHECK 4: A/B Test Subject Lines ──────────────────────────────────────────
try:
    ab = report.get("ab_test", {})
    variants = ab.get("variants", [])
    # Q2 brief requests 4 variants
    c11_passed = len(variants) == 4
    checks.append(make_check(
        "ab_test_variant_count",
        c11_passed,
        f"Expected 4 AB test variants (as per Q2 brief), got {len(variants)}"
    ))
except Exception as e:
    checks.append(make_check("ab_test_variant_count", False, str(e)))

try:
    ab = report.get("ab_test", {})
    topic = ab.get("topic", "")
    goal = ab.get("goal", "")
    # Topic must relate to SaaS产品增长, goal to open rate
    c12_passed = "SaaS" in topic or "saas" in topic.lower() or "增长" in topic
    c12b_passed = "打开率" in goal or "open" in goal.lower() or "提升" in goal
    checks.append(make_check(
        "ab_test_topic_and_goal",
        c12_passed and c12b_passed,
        f"topic='{topic}', goal='{goal}'. Expected topic to contain SaaS/增长 and goal to reference 打开率/提升"
    ))
except Exception as e:
    checks.append(make_check("ab_test_topic_and_goal", False, str(e)))

try:
    ab = report.get("ab_test", {})
    variants = ab.get("variants", [])
    # Each variant must have predicted_open_rate and predicted_click_rate fields
    all_have_predictions = all(
        "predicted_open_rate" in v and "predicted_click_rate" in v
        for v in variants
    )
    c13_passed = len(variants) > 0 and all_have_predictions
    checks.append(make_check(
        "ab_test_variants_have_predictions",
        c13_passed,
        f"All {len(variants)} variants have predicted_open_rate and predicted_click_rate: {all_have_predictions}"
    ))
except Exception as e:
    checks.append(make_check("ab_test_variants_have_predictions", False, str(e)))

try:
    ab = report.get("ab_test", {})
    ts = ab.get("test_settings", {})
    min_sample = ts.get("min_sample_size_per_variant", 0)
    c14_passed = min_sample == 1000
    checks.append(make_check(
        "ab_test_settings_min_sample",
        c14_passed,
        f"Expected min_sample_size_per_variant=1000, got {min_sample}"
    ))
except Exception as e:
    checks.append(make_check("ab_test_settings_min_sample", False, str(e)))

# ── CHECK 5: Target Feasibility (bonus strategic check) ──────────────────────
try:
    # The brief asks if 7500 by end of Q2 (6 months) is achievable.
    # projection at 6 months = 7196 < 7500, so NOT achievable at current rate.
    # The report should contain some note about this.
    target_analysis = report.get("target_feasibility", report.get("q2_target_analysis", report.get("feasibility", None)))
    projections = report.get("growth_projections", [])
    if projections:
        final_proj = projections[-1].get("projected_subscribers", 0)
        # If the report has a feasibility note mentioning 7500 or not achievable, that's a bonus
        has_feasibility = target_analysis is not None
        # Also accept if it's embedded in a string field
        report_str = json.dumps(report, ensure_ascii=False)
        mentions_target = "7500" in report_str or "feasib" in report_str.lower() or "达成" in report_str or "可行" in report_str
        c15_passed = has_feasibility or mentions_target
        checks.append(make_check(
            "target_feasibility_noted",
            c15_passed,
            f"Report mentions 7500 target feasibility: {c15_passed}. Final projection: {final_proj}"
        ))
    else:
        checks.append(make_check("target_feasibility_noted", False, "No projections found to assess feasibility"))
except Exception as e:
    checks.append(make_check("target_feasibility_noted", False, str(e)))

# ── Final Scoring ─────────────────────────────────────────────────────────────
# Weight the checks: core checks are mandatory, feasibility is bonus
CORE_CHECKS = [
    "growth_summary_total_periods",
    "growth_summary_subscriber_counts",
    "growth_summary_net_growth",
    "growth_summary_source_totals",
    "growth_projections_count",
    "growth_projections_final_value",
    "campaign_report_present",
    "campaign_report_open_rate",
    "campaign_report_bounced_and_spam",
    "campaign_report_open_rate_rating",
    "ab_test_variant_count",
    "ab_test_topic_and_goal",
    "ab_test_variants_have_predictions",
    "ab_test_settings_min_sample",
]

core_passed = sum(1 for c in checks if c["name"] in CORE_CHECKS and c["passed"])
bonus_passed = sum(1 for c in checks if c["name"] not in CORE_CHECKS and c["name"] != "output_file_exists" and c["passed"])

score = round((core_passed / len(CORE_CHECKS)) * 0.9 + (bonus_passed / 1) * 0.1, 3)
all_passed = core_passed == len(CORE_CHECKS)

print(json.dumps({
    "passed": all_passed,
    "score": score,
    "checks": checks
}, ensure_ascii=False, indent=2))