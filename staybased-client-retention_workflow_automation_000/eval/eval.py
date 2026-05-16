import sys
import json
import re
from pathlib import Path

def find_file(workspace, filename):
    """Search recursively for a file by exact name."""
    matches = list(Path(workspace).rglob(filename))
    return matches[0] if matches else None

def read_file(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace").lower()
    except Exception:
        return ""

def run_checks(workspace):
    checks = []
    workspace = Path(workspace)

    # =========================================================
    # FILE 1: monthly_value_report.txt (or .md)
    # =========================================================
    report_file = find_file(workspace, "monthly_value_report.txt") or \
                  find_file(workspace, "monthly_value_report.md") or \
                  find_file(workspace, "monthly_report.txt") or \
                  find_file(workspace, "monthly_report.md")

    if report_file is None:
        # Try broader search
        candidates = list(Path(workspace).rglob("*monthly*report*")) + list(Path(workspace).rglob("*value_report*"))
        report_file = candidates[0] if candidates else None

    report_text = read_file(report_file) if report_file else ""

    # Check 1.1: Monthly report file exists
    checks.append({
        "name": "monthly_value_report_exists",
        "passed": report_file is not None and report_file.stat().st_size > 50,
        "detail": f"Found at {report_file}" if report_file else "No monthly value report file found in workspace/artifacts/"
    })

    # Check 1.2: Report contains real numbers (messages handled, bookings)
    has_real_numbers = bool(
        re.search(r'\b(9|47|63|71|2)\b', report_text) or
        re.search(r'message', report_text) or
        re.search(r'booking', report_text)
    )
    checks.append({
        "name": "monthly_report_contains_real_metrics",
        "passed": has_real_numbers,
        "detail": f"Report should reference real usage metrics (messages, bookings). Content snippet: {report_text[:300]}"
    })

    # Check 1.3: Report contains ROI / investment / value reference
    has_roi = bool(
        re.search(r'roi', report_text) or
        re.search(r'return', report_text) or
        (re.search(r'149', report_text) and re.search(r'value', report_text)) or
        re.search(r'investment', report_text)
    )
    checks.append({
        "name": "monthly_report_contains_roi_or_investment",
        "passed": has_roi,
        "detail": f"Report must show ROI, investment, or value delivered vs cost. Content: {report_text[:300]}"
    })

    # Check 1.4: Report ends with a question (CRITICAL proprietary rule from Pillar 2)
    # Strip trailing whitespace and check last non-empty lines
    report_raw = read_file(report_file) if report_file else ""
    lines = [l.strip() for l in report_raw.split('\n') if l.strip()]
    last_200_chars = report_raw[-400:].strip() if report_raw else ""
    ends_with_question = last_200_chars.endswith('?') or bool(re.search(r'\?[\s]*$', last_200_chars))
    checks.append({
        "name": "monthly_report_ends_with_question",
        "passed": ends_with_question,
        "detail": f"SKILL.md Pillar 2 mandates report ALWAYS ends with a question. Last chars: '{last_200_chars[-100:]}'"
    })

    # =========================================================
    # FILE 2: churn_prevention_plan.txt (or .md)
    # =========================================================
    churn_file = find_file(workspace, "churn_prevention_plan.txt") or \
                 find_file(workspace, "churn_prevention_plan.md") or \
                 find_file(workspace, "churn_response_plan.txt") or \
                 find_file(workspace, "churn_plan.txt") or \
                 find_file(workspace, "churn_plan.md")

    if churn_file is None:
        candidates = list(Path(workspace).rglob("*churn*")) + list(Path(workspace).rglob("*retention_plan*"))
        churn_file = candidates[0] if candidates else None

    churn_text = read_file(churn_file) if churn_file else ""

    # Check 2.1: Churn plan file exists
    checks.append({
        "name": "churn_prevention_plan_exists",
        "passed": churn_file is not None and churn_file.stat().st_size > 100,
        "detail": f"Found at {churn_file}" if churn_file else "No churn prevention plan found in workspace/artifacts/"
    })

    # Check 2.2: Addresses the specific churn signals from the client data
    # Signals: key contact (Sarah) left, usage dropped, asked about contract terms, no reply to check-in
    signals_covered = (
        bool(re.search(r'(sarah|contact.*left|key.*contact|left.*company)', churn_text)) and
        bool(re.search(r'(usage|drop|declin|low)', churn_text))
    ) or (
        bool(re.search(r'(contract|terms|cancel)', churn_text)) and
        bool(re.search(r'(no.*reply|not.*respond|silent|disengag)', churn_text))
    ) or (
        # At least 2 of the 4 signals
        sum([
            bool(re.search(r'(sarah|contact.*left|key.*contact)', churn_text)),
            bool(re.search(r'(usage.*drop|drop.*usage|9 message|low usage)', churn_text)),
            bool(re.search(r'(contract.*term|cancel|what.*the.*term)', churn_text)),
            bool(re.search(r'(no.*reply|not.*respond|silent)', churn_text)),
        ]) >= 2
    )
    checks.append({
        "name": "churn_plan_addresses_detected_signals",
        "passed": signals_covered,
        "detail": f"Plan must address the specific churn signals: key contact left, usage drop, asked about contract terms, no check-in reply. Content: {churn_text[:400]}"
    })

    # Check 2.3: PAUSE option explicitly offered (CRITICAL proprietary rule — Pause > Cancel)
    has_pause_option = bool(re.search(r'pause', churn_text))
    checks.append({
        "name": "churn_plan_includes_pause_option",
        "passed": has_pause_option,
        "detail": f"SKILL.md mandates: 'Always offer a pause option before cancellation. Pause > Cancel.' Word 'pause' not found. Content: {churn_text[:400]}"
    })

    # Check 2.4: Quantifies what client will lose (step 4 of 5-step playbook)
    has_quantification = bool(
        re.search(r'(\$|usd|dollar)', churn_text) and
        re.search(r'(booking|captured|value|revenue|lose|losing|lost)', churn_text)
    )
    # Also accept if they mention the booking math: 22 bookings * $180 = $3,960 or similar
    has_quantification = has_quantification or bool(
        re.search(r'(3,?960|3960|2,?160|2160|7,?200|7200|captured)', churn_text)
    )
    checks.append({
        "name": "churn_plan_quantifies_value_at_risk",
        "passed": has_quantification,
        "detail": f"Step 4 of churn playbook: 'Quantify what they'll lose' — must include dollar value of captured bookings. Content: {churn_text[:400]}"
    })

    # Check 2.5: Gracious exit / feedback collection if they still leave (step 5)
    has_gracious_exit = bool(
        re.search(r'(gracious|understand|feedback|what.*could.*done|if.*still.*want|let them go)', churn_text)
    )
    checks.append({
        "name": "churn_plan_includes_gracious_exit",
        "passed": has_gracious_exit,
        "detail": f"Step 5 of churn playbook: Be gracious if they leave and ask for feedback. Content: {churn_text[:400]}"
    })

    # =========================================================
    # FILE 3: revenue_model_recommendation.txt (or .md)
    # =========================================================
    rev_file = find_file(workspace, "revenue_model_recommendation.txt") or \
               find_file(workspace, "revenue_model_recommendation.md") or \
               find_file(workspace, "annual_plan_recommendation.txt") or \
               find_file(workspace, "recurring_revenue_model.txt") or \
               find_file(workspace, "revenue_recommendation.md") or \
               find_file(workspace, "revenue_recommendation.txt")

    if rev_file is None:
        candidates = list(Path(workspace).rglob("*revenue*model*")) + \
                     list(Path(workspace).rglob("*annual*plan*")) + \
                     list(Path(workspace).rglob("*recurring*revenue*"))
        rev_file = candidates[0] if candidates else None

    rev_text = read_file(rev_file) if rev_file else ""

    # Check 3.1: Revenue model file exists
    checks.append({
        "name": "revenue_model_recommendation_exists",
        "passed": rev_file is not None and rev_file.stat().st_size > 100,
        "detail": f"Found at {rev_file}" if rev_file else "No revenue model recommendation file found in workspace/artifacts/"
    })

    # Check 3.2: Annual price of $1,490 specifically mentioned (proprietary math from SKILL.md)
    has_annual_price = bool(re.search(r'1[,.]?490', rev_text))
    checks.append({
        "name": "revenue_model_specifies_1490_annual_price",
        "passed": has_annual_price,
        "detail": f"SKILL.md specifies exact annual price: $1,490/year. Must appear in recommendation. Content: {rev_text[:400]}"
    })

    # Check 3.3: 17% discount explicitly mentioned (proprietary savings figure from SKILL.md)
    has_17pct = bool(re.search(r'17\s*%|17-?percent|save.*17|17.*sav', rev_text))
    checks.append({
        "name": "revenue_model_specifies_17pct_discount",
        "passed": has_17pct,
        "detail": f"SKILL.md specifies exact 17% annual discount. Must appear. Content: {rev_text[:400]}"
    })

    # Check 3.4: Timing advice — offer annual AFTER value demonstrated (month 2-3) 
    # (but note: client is at 4 months now — agent should note they're past that window or adapt)
    has_timing_advice = bool(
        re.search(r'(month 2|month 3|month two|month three|after.*value|value.*demonstrat|already.*demonstrat|4 month|four month|been.*active)', rev_text)
    )
    checks.append({
        "name": "revenue_model_includes_timing_advice",
        "passed": has_timing_advice,
        "detail": f"SKILL.md says offer annual at month 2-3 once value shown. Agent must reference this timing. Content: {rev_text[:400]}"
    })

    # =========================================================
    # BONUS: Onboarding milestones referenced anywhere
    # =========================================================
    # Check if any artifact mentions the Day 1 / Day 7 / Day 14 / Day 30 framework
    all_artifacts_text = ""
    artifacts_dir = workspace / "workspace" / "artifacts"
    if artifacts_dir.exists():
        for f in artifacts_dir.rglob("*"):
            if f.is_file():
                all_artifacts_text += read_file(f) + "\n"

    has_onboarding_milestones = (
        bool(re.search(r'day\s*1\b', all_artifacts_text)) and
        bool(re.search(r'day\s*(7|seven)', all_artifacts_text)) and
        bool(re.search(r'day\s*(14|fourteen)', all_artifacts_text)) and
        bool(re.search(r'day\s*(30|thirty)', all_artifacts_text))
    )
    checks.append({
        "name": "onboarding_day_milestones_referenced",
        "passed": has_onboarding_milestones,
        "detail": "SKILL.md Pillar 1 specifies Day 1, Day 7, Day 14, Day 30 milestones. At least one artifact should reference this framework."
    })

    # =========================================================
    # SCORING
    # =========================================================
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)

    # Overall pass: must pass core checks
    core_checks = [
        "monthly_value_report_exists",
        "monthly_report_ends_with_question",
        "churn_prevention_plan_exists",
        "churn_plan_includes_pause_option",
        "churn_plan_quantifies_value_at_risk",
        "revenue_model_recommendation_exists",
        "revenue_model_specifies_1490_annual_price",
        "revenue_model_specifies_17pct_discount",
    ]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)

    return {
        "passed": core_passed and score >= 0.75,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))