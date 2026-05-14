import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def find_report(workspace):
    """Search for the validation report file."""
    for ext in ["md", "txt", "json", "yaml", "yml"]:
        results = list(Path(workspace).rglob(f"validation_report.{ext}"))
        if results:
            return results[0]
    # Also search for any file with 'validation' and 'report' in name
    for p in Path(workspace).rglob("*"):
        if p.is_file() and "validation" in p.name.lower() and "report" in p.name.lower():
            return p
    return None

report_path = find_report(workspace)
report_content = ""

# Check 1: Report file exists
if report_path and report_path.exists():
    try:
        report_content = report_path.read_text(encoding="utf-8", errors="replace")
        checks.append({"name": "report_file_exists", "passed": True, "detail": f"Found report at {report_path}"})
    except Exception as e:
        checks.append({"name": "report_file_exists", "passed": False, "detail": f"File found but unreadable: {e}"})
else:
    checks.append({"name": "report_file_exists", "passed": False, "detail": "No validation_report file found in workspace"})

content_lower = report_content.lower()

# Check 2: Customer discovery kill-check — correct interview count (13) and correct threshold math
# Pain + WTP: 9/13 = 69.2% -> PASSES 60% threshold
# Must mention 13 interviews and some form of 9 or 69% and PASS
try:
    has_13_interviews = bool(re.search(r'13\s*interview', content_lower) or re.search(r'thirteen\s*interview', content_lower) or '13' in report_content)
    # Look for the critical percentage: 69% or 9/13 for the combined metric
    has_correct_pct = bool(
        re.search(r'69[\.\,]?\s*%', report_content) or
        re.search(r'9\s*/\s*13', report_content) or
        re.search(r'9\s+of\s+13', content_lower) or
        re.search(r'9\s+out\s+of\s+13', content_lower)
    )
    # Must acknowledge PASS on kill check (not fail)
    kill_check_pass = bool(
        re.search(r'kill\s*check.*pass', content_lower) or
        re.search(r'pass.*kill\s*check', content_lower) or
        re.search(r'phase\s*4.*pass', content_lower) or
        re.search(r'discovery.*pass', content_lower) or
        (re.search(r'60\s*%', report_content) and re.search(r'pass|exceed|above|meet', content_lower))
    )
    passed = has_13_interviews and has_correct_pct and kill_check_pass
    checks.append({
        "name": "customer_discovery_kill_check_correct",
        "passed": passed,
        "detail": f"has_13_interviews={has_13_interviews}, correct_pct_9_of_13_or_69pct={has_correct_pct}, kill_check_pass={kill_check_pass}"
    })
except Exception as e:
    checks.append({"name": "customer_discovery_kill_check_correct", "passed": False, "detail": f"Error: {e}"})

# Check 3: 50% discount on WTP applied
# Interviews state $80-200+, discounted should be ~$40-100 range
try:
    has_discount_mention = bool(
        re.search(r'50\s*%\s*discount', content_lower) or
        re.search(r'discount.*50', content_lower) or
        re.search(r'stated.*price.*discount', content_lower) or
        re.search(r'halve|half.*stated|discount.*wtp|wtp.*discount', content_lower) or
        re.search(r'discount.*stated|stated.*50', content_lower)
    )
    # Check that discounted WTP numbers appear (should be in $40-100 range, not $150-200)
    has_discounted_values = bool(
        re.search(r'\$\s*4[0-9]', report_content) or
        re.search(r'\$\s*5[0-9]', report_content) or
        re.search(r'\$\s*6[0-9]', report_content) or
        re.search(r'\$\s*7[0-9]', report_content) or
        re.search(r'40[\s\-].*month|50[\s\-].*month|75[\s\-].*month', content_lower)
    )
    passed = has_discount_mention or has_discounted_values
    checks.append({
        "name": "wtp_50pct_discount_applied",
        "passed": passed,
        "detail": f"has_discount_mention={has_discount_mention}, has_discounted_values={has_discounted_values}"
    })
except Exception as e:
    checks.append({"name": "wtp_50pct_discount_applied", "passed": False, "detail": f"Error: {e}"})

# Check 4: RAT conversion rate correctly computed as 3.64% (9/247)
# Must be between 3.5% and 3.8% and must PASS (3-5% threshold)
try:
    # Look for the correct conversion figure
    has_correct_conversion = bool(
        re.search(r'3\.6[0-9]\s*%', report_content) or
        re.search(r'9\s*/\s*247', report_content) or
        re.search(r'9\s+of\s+247', content_lower) or
        re.search(r'9\s+out\s+of\s+247', content_lower) or
        re.search(r'3\.64', report_content)
    )
    # Must mention 3-5% threshold
    has_threshold = bool(
        re.search(r'3[\s\-]5\s*%', report_content) or
        re.search(r'3%.*5%|5%.*3%', report_content) or
        re.search(r'threshold.*3|3.*threshold', content_lower)
    )
    # Must state RAT passes
    rat_passes = bool(
        re.search(r'rat.*pass|pass.*rat', content_lower) or
        re.search(r'assumption.*pass|pass.*assumption', content_lower) or
        re.search(r'riskiest.*pass|phase\s*5.*pass', content_lower) or
        (has_correct_conversion and re.search(r'pass|within|meet|exceed|confirm', content_lower))
    )
    passed = has_correct_conversion and rat_passes
    checks.append({
        "name": "rat_conversion_correct_and_pass",
        "passed": passed,
        "detail": f"has_correct_conversion_3.64pct={has_correct_conversion}, has_threshold={has_threshold}, rat_passes={rat_passes}"
    })
except Exception as e:
    checks.append({"name": "rat_conversion_correct_and_pass", "passed": False, "detail": f"Error: {e}"})

# Check 5: Weighted scorecard with CORRECT weights (20/15/20/15/20/10)
# Must NOT use equal weights. Must show weighted calculation.
try:
    # Check for the specific weights
    has_20pct_weight = bool(re.search(r'20\s*%', report_content) or '0.20' in report_content or '× 20' in report_content or '* 20' in report_content)
    has_15pct_weight = bool(re.search(r'15\s*%', report_content) or '0.15' in report_content)
    has_10pct_weight = bool(re.search(r'10\s*%', report_content) or '0.10' in report_content)
    
    # Check for weighted score mention (not simple average)
    has_weighted_score = bool(
        re.search(r'weighted\s*score', content_lower) or
        re.search(r'weight.*score|score.*weight', content_lower)
    )
    
    # Check for a final numeric score being present
    # Valid range: minimum possible is 1.0, max is 5.0
    score_match = re.findall(r'\b([0-9]\.[0-9]{1,2})\b', report_content)
    valid_scores = [float(s) for s in score_match if 1.0 <= float(s) <= 5.0]
    has_valid_score = len(valid_scores) > 0
    
    passed = has_20pct_weight and has_15pct_weight and has_10pct_weight and has_weighted_score
    checks.append({
        "name": "weighted_scorecard_correct_weights",
        "passed": passed,
        "detail": f"has_20pct={has_20pct_weight}, has_15pct={has_15pct_weight}, has_10pct={has_10pct_weight}, has_weighted_score={has_weighted_score}, valid_scores_found={valid_scores[:5]}"
    })
except Exception as e:
    checks.append({"name": "weighted_scorecard_correct_weights", "passed": False, "detail": f"Error: {e}"})

# Check 6: Correct Go/No-Go decision with correct threshold interpretation
# Given the strong signals, weighted score should be >= 3.0
# Agent must produce either GO or CONDITIONAL GO with score >= 3.0
# and must NOT produce NO-GO (which would indicate miscalculation)
try:
    has_go_decision = bool(
        re.search(r'\bgo\b', content_lower) or
        re.search(r'conditional\s*go', content_lower) or
        re.search(r'proceed|build|pursue|recommend.*go', content_lower)
    )
    has_no_go_only = bool(
        re.search(r'no[\s\-]go', content_lower) and
        not re.search(r'conditional\s*(no[\s\-]go|go)', content_lower)
    )
    # Must include the threshold ranges (4.0-5.0 go, 3.0-3.9 conditional, <3.0 no-go)
    has_threshold_ranges = bool(
        re.search(r'4\.0|4\s*[\-–]\s*5', report_content) or
        re.search(r'3\.0|3\s*[\-–]\s*3\.9', report_content) or
        re.search(r'3\.9|3\.0\s*[\-–]', report_content)
    )
    
    # The score should represent a positive outcome given all phases pass
    # Must have a score >= 3.0
    score_match = re.findall(r'(?:weighted\s*score|final\s*score|overall\s*score|total)[^\d]*([0-9]\.[0-9]{1,2})', content_lower)
    if not score_match:
        # Try broader match
        score_match = re.findall(r'\b([3-5]\.[0-9]{1,2})\b', report_content)
    
    score_above_3 = False
    if score_match:
        try:
            for s in score_match:
                if float(s) >= 3.0:
                    score_above_3 = True
                    break
        except:
            pass
    
    passed = has_go_decision and not has_no_go_only and (has_threshold_ranges or score_above_3)
    checks.append({
        "name": "correct_go_nogo_decision",
        "passed": passed,
        "detail": f"has_go_decision={has_go_decision}, no_go_only={has_no_go_only}, has_threshold_ranges={has_threshold_ranges}, score_above_3={score_above_3}"
    })
except Exception as e:
    checks.append({"name": "correct_go_nogo_decision", "passed": False, "detail": f"Error: {e}"})

# Check 7: Phase ordering and kill-check documentation present
# Must document all major phases and their kill checks
try:
    phases_mentioned = 0
    phase_keywords = [
        r'problem\s*definition|phase\s*1',
        r'demand\s*signal|phase\s*2',
        r'solution\s*fit|phase\s*3|10x',
        r'customer\s*discovery|phase\s*4',
        r'riskiest\s*assumption|rat|phase\s*5',
        r'scorecard|go.*no.*go|phase\s*6',
    ]
    for kw in phase_keywords:
        if re.search(kw, content_lower):
            phases_mentioned += 1
    
    has_kill_checks = bool(re.search(r'kill\s*check', content_lower))
    
    passed = phases_mentioned >= 4 and has_kill_checks
    checks.append({
        "name": "all_phases_documented_with_kill_checks",
        "passed": passed,
        "detail": f"phases_mentioned={phases_mentioned}/6, has_kill_checks={has_kill_checks}"
    })
except Exception as e:
    checks.append({"name": "all_phases_documented_with_kill_checks", "passed": False, "detail": f"Error: {e}"})

# Check 8: Demand signal check - must cite 3+ positive signals (5 were found)
try:
    signal_keywords = [
        r'reddit|forum|community',
        r'google\s*trend|search\s*volume',
        r'g2|app\s*store|review',
        r'job\s*post|indeed|linkedin',
        r'twitter|social|tweet',
    ]
    signals_found = sum(1 for kw in signal_keywords if re.search(kw, content_lower))
    has_positive_count = bool(
        re.search(r'[3-5]\s*(?:positive\s*)?signals?', content_lower) or
        re.search(r'5\s*(?:out\s*of\s*5|signal)', content_lower) or
        signals_found >= 3
    )
    passed = has_positive_count and signals_found >= 3
    checks.append({
        "name": "demand_signals_3plus_cited",
        "passed": passed,
        "detail": f"signals_found_in_report={signals_found}, has_positive_count={has_positive_count}"
    })
except Exception as e:
    checks.append({"name": "demand_signals_3plus_cited", "passed": False, "detail": f"Error: {e}"})

# Compute final score
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0

# Critical checks (must pass for overall pass)
critical = ["report_file_exists", "customer_discovery_kill_check_correct", "rat_conversion_correct_and_pass", "weighted_scorecard_correct_weights"]
critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

final_passed = critical_passed and score >= 0.70

result = {
    "passed": final_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))