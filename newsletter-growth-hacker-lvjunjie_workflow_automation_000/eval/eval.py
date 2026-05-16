import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]
checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ── 1. Find the output file ──────────────────────────────────────────────────
output_files = list(Path(workspace).rglob("quarterly_review.json"))
if not output_files:
    print(json.dumps({
        "passed": False,
        "score": 0.0,
        "checks": [make_check("output_file_exists", False, "quarterly_review.json not found anywhere in workspace")]
    }))
    sys.exit(0)

output_path = output_files[0]
checks.append(make_check("output_file_exists", True, f"Found at {output_path}"))

# ── 2. Parse JSON ────────────────────────────────────────────────────────────
try:
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    checks.append(make_check("valid_json", True, "File parses as valid JSON"))
except Exception as e:
    checks.append(make_check("valid_json", False, f"JSON parse error: {e}"))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 3. Top-level keys ───────────────────────────────────────────────────────
required_keys = ["growth_projections", "campaign_report", "ab_test_variants"]
missing_keys = [k for k in required_keys if k not in data]
if missing_keys:
    checks.append(make_check("top_level_keys", False, f"Missing keys: {missing_keys}"))
else:
    checks.append(make_check("top_level_keys", True, "All three top-level keys present"))

# ── 4. growth_projections ────────────────────────────────────────────────────
try:
    gp = data["growth_projections"]
    assert isinstance(gp, list), "growth_projections must be a list"
    # Must be exactly 4 months
    assert len(gp) == 4, f"Expected 4 projections, got {len(gp)}"
    # Each entry must have 'period' and 'projected_subscribers'
    for entry in gp:
        assert "period" in entry, f"Missing 'period' in projection entry: {entry}"
        assert "projected_subscribers" in entry, f"Missing 'projected_subscribers' in projection entry: {entry}"
    # Periods should start from 2026-04 (after 2026-03)
    periods = [e["period"] for e in gp]
    assert periods[0] == "2026-04", f"First projected period should be 2026-04, got {periods[0]}"
    assert periods[-1] == "2026-07", f"Last projected period should be 2026-07, got {periods[-1]}"
    # Subscriber counts should be increasing and in reasonable range (above 6160)
    subs = [e["projected_subscribers"] for e in gp]
    assert all(subs[i] < subs[i+1] for i in range(len(subs)-1)), "Projected subscribers should be increasing"
    assert subs[0] > 6160, f"First projection should exceed current 6160, got {subs[0]}"
    checks.append(make_check("growth_projections_correct", True,
        f"4 projections from {periods[0]} to {periods[-1]}, starting at {subs[0]} subs"))
except Exception as e:
    checks.append(make_check("growth_projections_correct", False, str(e)))

# ── 5. campaign_report ───────────────────────────────────────────────────────
try:
    cr = data["campaign_report"]
    assert isinstance(cr, dict), "campaign_report must be a dict"
    # Must contain campaign_name
    assert "campaign_name" in cr, "Missing campaign_name"
    assert "FinTech Weekly Q1 2026" in str(cr["campaign_name"]), \
        f"campaign_name should reference FinTech Weekly Q1 2026, got: {cr['campaign_name']}"
    # Must have metrics sub-dict
    assert "metrics" in cr, "Missing metrics in campaign_report"
    metrics = cr["metrics"]
    # Check key derived metrics are present and plausible
    assert "open_rate" in metrics, "Missing open_rate in metrics"
    assert "click_rate" in metrics, "Missing click_rate in metrics"
    assert "delivery_rate" in metrics, "Missing delivery_rate in metrics"
    assert "spam_rate" in metrics, "Missing spam_rate"
    # Validate computed values from known inputs:
    # sent=52000, delivered=51168, opened=13815, clicked=2764
    expected_open_rate = round(13815 / 51168, 4)
    actual_open_rate = metrics["open_rate"]
    assert abs(actual_open_rate - expected_open_rate) < 0.001, \
        f"open_rate mismatch: expected ~{expected_open_rate}, got {actual_open_rate}"
    # Must have ratings
    assert "ratings" in cr, "Missing ratings in campaign_report"
    # Must have insights list
    assert "insights" in cr, "Missing insights in campaign_report"
    # Must have action_items list
    assert "action_items" in cr, "Missing action_items in campaign_report"
    checks.append(make_check("campaign_report_correct", True,
        f"campaign_report valid, open_rate={actual_open_rate} (expected {expected_open_rate})"))
except Exception as e:
    checks.append(make_check("campaign_report_correct", False, str(e)))

# ── 6. Spam complaints mapping ───────────────────────────────────────────────
try:
    cr = data["campaign_report"]
    metrics = cr["metrics"]
    # spam_complaints in JSON was "26", delivered=51168 → spam_rate=26/51168≈0.000508
    expected_spam_rate = round(26 / 51168, 4)
    actual_spam = metrics.get("spam_rate", None)
    assert actual_spam is not None, "spam_rate missing from metrics"
    assert abs(actual_spam - expected_spam_rate) < 0.001, \
        f"spam_rate mismatch: expected ~{expected_spam_rate}, got {actual_spam}. " \
        f"Agent likely failed to map 'Spam_Complaints' field correctly."
    checks.append(make_check("spam_complaints_field_mapped", True,
        f"Spam_Complaints correctly mapped; spam_rate={actual_spam}"))
except Exception as e:
    checks.append(make_check("spam_complaints_field_mapped", False, str(e)))

# ── 7. ab_test_variants ──────────────────────────────────────────────────────
try:
    abt = data["ab_test_variants"]
    assert isinstance(abt, list), "ab_test_variants must be a list"
    # Must be exactly 4 variants
    assert len(abt) == 4, f"Expected exactly 4 AB test variants, got {len(abt)}"
    # Each variant must have required fields
    for v in abt:
        assert "subject_line" in v, f"Missing subject_line in variant: {v}"
        assert "style" in v, f"Missing style in variant: {v}"
        assert "predicted_open_rate" in v, f"Missing predicted_open_rate in variant: {v}"
    # Check topic appears in subject lines (at least some should reference 市场波动)
    all_subjects = " ".join(v.get("subject_line", "") for v in abt)
    assert "市场波动" in all_subjects or "理财" in all_subjects, \
        f"Subject lines don't seem to reference the topic '市场波动中的理财策略'. Got: {all_subjects}"
    # All variant letters should be unique A, B, C, D
    variant_ids = [v.get("variant", "") for v in abt]
    assert len(set(variant_ids)) == 4, f"Expected 4 unique variant IDs, got: {variant_ids}"
    checks.append(make_check("ab_test_variants_correct", True,
        f"4 variants present. Styles: {[v['style'] for v in abt]}"))
except Exception as e:
    checks.append(make_check("ab_test_variants_correct", False, str(e)))

# ── 8. Growth data correctness (6 periods loaded) ───────────────────────────
try:
    gp = data["growth_projections"]
    # The avg growth rate is calculated from last 3 of 6 periods.
    # Periods 2025-10..2026-03 data from CSV.
    # Last 3: 2026-01, 2026-02, 2026-03
    # 2026-01: new=345, lost=73, net=272, prev=5344 → rate=272/5344≈0.0509
    # 2026-02: new=398, lost=126, net=272, prev=5616 → rate=272/5616≈0.0484
    # 2026-03: new=430, lost=158, net=272, prev=5888 → rate=272/5888≈0.0462
    # avg_rate ≈ (0.0509+0.0484+0.0462)/3 ≈ 0.0485
    avg_rate_approx = 0.0485
    # projected 2026-04: int(6160 * (1 + avg_rate))
    expected_first_proj = int(6160 * (1 + avg_rate_approx))
    actual_first_proj = gp[0]["projected_subscribers"]
    # allow tolerance of ±20 for rounding differences across implementations
    assert abs(actual_first_proj - expected_first_proj) < 50, \
        f"First projection subscribers ~{expected_first_proj} expected, got {actual_first_proj}"
    checks.append(make_check("growth_rate_calculation_correct", True,
        f"First projection {actual_first_proj} is close to expected {expected_first_proj}"))
except Exception as e:
    checks.append(make_check("growth_rate_calculation_correct", False, str(e)))

# ── Final scoring ────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3)
overall_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": overall_passed,
    "score": score,
    "checks": checks
}, ensure_ascii=False, indent=2))