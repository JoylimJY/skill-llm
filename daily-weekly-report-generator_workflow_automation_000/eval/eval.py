import sys
import json
import re
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    candidates = list(Path(workspace).rglob("weekly_performance_report.md"))
    if candidates:
        return candidates[0]
    return None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    checks = []

    # --- Find file ---
    report_path = find_report(workspace)
    if report_path is None:
        checks.append(check("file_exists", False, "weekly_performance_report.md not found anywhere in workspace"))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append(check("file_exists", True, f"Found at {report_path}"))

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, f"Cannot read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("file_readable", True, f"File is readable, length={len(content)} chars"))

    content_lower = content.lower()

    # ----------------------------------------------------------------
    # CHECK 1: All 5 Output Contract sections present and non-empty
    # ----------------------------------------------------------------
    required_sections = [
        ("metric_definition_clarification", ["metric definition", "metric clarif", "kpi definition", "definition clarif"]),
        ("query_plan", ["query plan", "query spec", "data query"]),
        ("result_summary", ["result summary", "results summary", "performance summary", "summary of result"]),
        ("interpretation_and_caveats", ["interpretation", "caveat", "interpretation and caveat"]),
        ("decision_recommendation", ["decision recommendation", "recommendation", "next action", "action recommendation"]),
    ]

    for section_key, keywords in required_sections:
        found = any(kw in content_lower for kw in keywords)
        # Also check section has content after it (at least 50 chars after the keyword)
        detail = f"Section '{section_key}' "
        if found:
            for kw in keywords:
                idx = content_lower.find(kw)
                if idx != -1:
                    trailing = content[idx:idx+200].strip()
                    if len(trailing) >= 50:
                        checks.append(check(f"section_{section_key}", True, f"Found and non-empty near: '{trailing[:60]}...'"))
                    else:
                        checks.append(check(f"section_{section_key}", False, f"Found keyword '{kw}' but section appears empty or too short"))
                    break
        else:
            checks.append(check(f"section_{section_key}", False, f"None of {keywords} found in report"))

    # ----------------------------------------------------------------
    # CHECK 2: Attribution window — BOTH 1d-click and 7d-click shown for Meta
    # ----------------------------------------------------------------
    has_1d = bool(re.search(r'1[\s\-_]?d(?:ay)?[\s\-_]?click|1d_click|1-day click', content_lower))
    has_7d = bool(re.search(r'7[\s\-_]?d(?:ay)?[\s\-_]?click|7d_click|7-day click', content_lower))
    both_attribution = has_1d and has_7d
    checks.append(check(
        "attribution_both_windows_shown",
        both_attribution,
        f"1d-click found={has_1d}, 7d-click found={has_7d}. Both must be present for Meta."
    ))

    # ----------------------------------------------------------------
    # CHECK 3: Canonical metric definition locked before analysis
    # ----------------------------------------------------------------
    lock_patterns = [
        r'lock|canonical|agreed.upon|single.definition|standardiz|defined as|we.will.use|reporting on',
    ]
    lock_found = any(re.search(p, content_lower) for p in lock_patterns)
    checks.append(check(
        "metric_definition_locked",
        lock_found,
        "Report must lock/canonicalize one ROAS definition before analysis (Decision Rules requirement)"
    ))

    # ----------------------------------------------------------------
    # CHECK 4: Platform-specific, non-collapsed recommendations
    # ----------------------------------------------------------------
    meta_mentioned = bool(re.search(r'\bmeta\b|\bfacebook\b|\binstagram\b', content_lower))
    google_mentioned = bool(re.search(r'\bgoogle\b|\bsearch\b|\bpmax\b|\bperformance max\b', content_lower))
    amazon_mentioned = bool(re.search(r'\bamazon\b|\bsponsored product\b|\bsponsored brand\b', content_lower))

    checks.append(check("platform_meta_mentioned", meta_mentioned, "Meta/Facebook/Instagram explicitly discussed"))
    checks.append(check("platform_google_mentioned", google_mentioned, "Google Ads/Search/PMax explicitly discussed"))
    checks.append(check("platform_amazon_mentioned", amazon_mentioned, "Amazon Ads explicitly discussed"))

    all_platforms = meta_mentioned and google_mentioned and amazon_mentioned
    checks.append(check(
        "platforms_not_collapsed",
        all_platforms,
        "All three platforms (Meta, Google, Amazon) must have distinct mentions — not collapsed into one generic plan"
    ))

    # ----------------------------------------------------------------
    # CHECK 5: Creative testing guidance for Meta (platform-specific behavior)
    # ----------------------------------------------------------------
    meta_creative = bool(re.search(r'(meta|facebook|instagram).{0,300}(creative|creative test|ad creative|creative cadence)', content_lower, re.DOTALL))
    if not meta_creative:
        # Also check reversed order
        meta_creative = bool(re.search(r'(creative|creative test|ad creative).{0,300}(meta|facebook|instagram)', content_lower, re.DOTALL))
    checks.append(check(
        "meta_creative_testing_guidance",
        meta_creative,
        "Platform Notes: For Meta, report must prioritize/mention creative testing cadence"
    ))

    # ----------------------------------------------------------------
    # CHECK 6: Demand-capture / query/listing intent for Google or Amazon
    # ----------------------------------------------------------------
    demand_capture = bool(re.search(r'demand.capture|query intent|listing intent|intent.based|keyword intent|search intent', content_lower))
    checks.append(check(
        "google_amazon_demand_capture_guidance",
        demand_capture,
        "Platform Notes: Google/Amazon must reference demand-capture or query/listing intent"
    ))

    # ----------------------------------------------------------------
    # CHECK 7: Rollback / stop-loss condition present (spend risk exists)
    # ----------------------------------------------------------------
    stoplos_pattern = r'stop.loss|rollback|stopping rule|kill switch|pause|exit condition|if.*underperform|threshold.*pause|below.*roas.*pause|roas.*below.*stop'
    has_stoploss = bool(re.search(stoplos_pattern, content_lower))
    checks.append(check(
        "rollback_or_stoploss_condition",
        has_stoploss,
        "Constraints: At least one rollback/stop-loss condition required when spend risk exists (budget shift scenario)"
    ))

    # ----------------------------------------------------------------
    # CHECK 8: Amazon low-sample results marked directional / not conclusive
    # ----------------------------------------------------------------
    directional_pattern = r'directional|not conclusive|low sample|insufficient sample|small sample|inconclusive'
    has_directional = bool(re.search(directional_pattern, content_lower))
    checks.append(check(
        "amazon_low_sample_flagged_directional",
        has_directional,
        "Decision Rules: Amazon Generic SP & SB Video low order counts must be marked 'directional not conclusive'"
    ))

    # ----------------------------------------------------------------
    # CHECK 9: No fabricated metrics — report must reference actual data values
    # ----------------------------------------------------------------
    # Check that real values from the CSVs appear in the report (at least some)
    known_values = ["14200", "18900", "3100", "4200", "12800", "9100", "3200", "8900", "4700",
                    "3.67", "1.34", "30,000", "30000"]
    values_found = [v for v in known_values if v in content]
    has_real_data = len(values_found) >= 4
    checks.append(check(
        "real_data_values_referenced",
        has_real_data,
        f"Report must reference actual spend/metric values from raw exports. Found {len(values_found)}/4+ required: {values_found[:5]}"
    ))

    # ----------------------------------------------------------------
    # CHECK 10: Confidence level / confidence marking present
    # ----------------------------------------------------------------
    confidence_pattern = r'confidence|high confidence|low confidence|confidence level|directional|with confidence'
    has_confidence = bool(re.search(confidence_pattern, content_lower))
    checks.append(check(
        "confidence_level_stated",
        has_confidence,
        "Workflow step 4: Summarize findings with confidence level explicitly"
    ))

    # ----------------------------------------------------------------
    # SCORING
    # ----------------------------------------------------------------
    # Weight critical checks more heavily
    critical_checks = {
        "section_metric_definition_clarification": 2,
        "section_query_plan": 1,
        "section_result_summary": 2,
        "section_interpretation_and_caveats": 2,
        "section_decision_recommendation": 2,
        "attribution_both_windows_shown": 3,
        "metric_definition_locked": 2,
        "platforms_not_collapsed": 2,
        "meta_creative_testing_guidance": 1,
        "google_amazon_demand_capture_guidance": 1,
        "rollback_or_stoploss_condition": 3,
        "amazon_low_sample_flagged_directional": 2,
        "real_data_values_referenced": 2,
        "confidence_level_stated": 1,
    }

    total_weight = sum(critical_checks.values())
    earned_weight = 0
    for c in checks:
        if c["name"] in critical_checks and c["passed"]:
            earned_weight += critical_checks[c["name"]]

    # file_exists and file_readable contribute to base
    if any(c["name"] == "file_exists" and c["passed"] for c in checks):
        earned_weight += 1
        total_weight += 1

    score = round(earned_weight / total_weight, 3) if total_weight > 0 else 0.0

    # Must pass all critical checks to truly pass
    critical_failed = [
        c["name"] for c in checks
        if c["name"] in critical_checks and not c["passed"]
    ]
    passed = len(critical_failed) <= 2 and score >= 0.70  # allow at most 2 minor misses

    return {
        "passed": passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, indent=2))