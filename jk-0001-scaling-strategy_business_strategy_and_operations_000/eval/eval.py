import sys
import json
import re
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    ws = Path(workspace)

    # --- Find the output file ---
    candidates = list(ws.rglob("scaling_plan.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "scaling_plan.md not found anywhere in workspace"}]
        }

    output_file = candidates[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_file}"})

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_readable", "passed": False, "detail": str(e)}]
        }

    content_lower = content.lower()

    # =========================================================
    # CHECK 1: Correct Bottleneck Identification
    # The data shows: leads are plentiful (18-21/mo), close rate is fine,
    # but owner works 70+ hrs/week, declining projects due to capacity.
    # Correct bottleneck: "Delivery capacity" (or "Your time")
    # =========================================================
    bottleneck_keywords = [
        "delivery capacity", "deliverable capacity", "capacity",
        "your time", "time bottleneck", "delivery bottleneck",
        "cannot deliver", "can't deliver", "turning down work",
        "declining work", "declined"
    ]
    # Must NOT identify lead gen or conversion as the bottleneck
    false_bottleneck_keywords = [
        "lead generation is the bottleneck",
        "conversion rate is the bottleneck",
        "cash flow is the bottleneck",
        "not enough prospects"
    ]
    bottleneck_found = any(kw in content_lower for kw in bottleneck_keywords)
    false_bottleneck_found = any(kw in content_lower for kw in false_bottleneck_keywords)
    bottleneck_passed = bottleneck_found and not false_bottleneck_found
    checks.append({
        "name": "correct_bottleneck_identified",
        "passed": bottleneck_passed,
        "detail": f"Correct bottleneck keywords found: {bottleneck_found}. False bottleneck wrongly stated: {false_bottleneck_found}. Content excerpt (first 500 chars): {content[:500]}"
    })

    # =========================================================
    # CHECK 2: Automation ROI Threshold Applied Correctly
    # Rule: task >= 15 min AND >= 10x/month → automate
    # thumbnail_creation: 25min, 15x/month → YES automate
    # send_invoice: 20min, 15x/month → YES automate
    # upload_and_tag_video: 18min, 15x/month → YES automate
    # client_strategy_call_prep: 30min, 6x/month → NO (frequency too low)
    # reply_to_client_slack: 10min, 40x/month → NO (time too short)
    # weekly_revenue_report: 20min, 4x/month → NO (frequency too low)
    # =========================================================
    automate_correct = []
    # At least 2 of the 3 correct tasks should be recommended for automation
    if "thumbnail" in content_lower and any(w in content_lower for w in ["automat", "automat"]):
        automate_correct.append("thumbnail_creation")
    if "invoice" in content_lower and "automat" in content_lower:
        automate_correct.append("send_invoice")
    if "upload" in content_lower and "automat" in content_lower:
        automate_correct.append("upload_and_tag_video")

    # Stronger check: ensure thumbnail or invoice is explicitly called out for automation
    thumbnail_automated = "thumbnail" in content_lower and "automat" in content_lower
    invoice_automated = "invoice" in content_lower and "automat" in content_lower
    at_least_two_correct_automations = sum([thumbnail_automated, invoice_automated,
                                             "upload" in content_lower and "automat" in content_lower]) >= 2
    checks.append({
        "name": "automation_roi_threshold_applied",
        "passed": at_least_two_correct_automations,
        "detail": f"Correctly identified for automation: {automate_correct}. Need at least 2 of [thumbnail_creation, send_invoice, upload_and_tag_video]."
    })

    # Check that client_strategy_call_prep is NOT recommended for automation
    # (30 min but only 6x/month - fails frequency test)
    strategy_call_wrongly_automated = bool(re.search(
        r'(strategy.call|client.strategy|call.prep).{0,60}automat',
        content_lower, re.DOTALL
    ))
    checks.append({
        "name": "automation_false_positive_avoided",
        "passed": not strategy_call_wrongly_automated,
        "detail": f"client_strategy_call_prep should NOT be flagged for automation (only 6x/month, fails 10x threshold). Wrong recommendation found: {strategy_call_wrongly_automated}"
    })

    # =========================================================
    # CHECK 3: Contractor vs Employee Decision
    # Rough cut editing: ~45 hrs/month consistently
    # SKILL.md rule: Hire Employee only if 30+ hours/week needed
    # 45 hrs/MONTH = ~11 hrs/week → below 30hrs/week → CONTRACTOR
    # =========================================================
    # Look for contractor recommendation for editing
    contractor_rec = any(kw in content_lower for kw in [
        "contractor", "freelancer", "freelance editor",
        "hire a contractor", "contract editor"
    ])
    # The recommendation should be contractor, NOT employee (45hrs/month ≠ 30hrs/week)
    employee_wrongly_rec = bool(re.search(
        r'(hire|bring on).{0,30}(employee|full.time|full time).{0,60}(edit|video)',
        content_lower, re.DOTALL
    ))
    contractor_check_passed = contractor_rec and not employee_wrongly_rec
    checks.append({
        "name": "contractor_vs_employee_decision_correct",
        "passed": contractor_check_passed,
        "detail": f"Contractor recommended: {contractor_rec}. Employee wrongly recommended for editing: {employee_wrongly_rec}. (45hrs/month = ~11hrs/week < 30hrs/week threshold → contractor, not employee)"
    })

    # =========================================================
    # CHECK 4: SOP Present with Correct Structure
    # Required sections per SKILL.md template:
    # TASK, OWNER, FREQUENCY, TOOLS NEEDED, STEPS, COMMON ISSUES AND SOLUTIONS, CHECKLIST
    # =========================================================
    sop_sections = {
        "TASK":                       bool(re.search(r'\bTASK\s*:', content, re.IGNORECASE)),
        "OWNER":                      bool(re.search(r'\bOWNER\s*:', content, re.IGNORECASE)),
        "FREQUENCY":                  bool(re.search(r'\bFREQUENCY\s*:', content, re.IGNORECASE)),
        "TOOLS NEEDED":               bool(re.search(r'TOOLS\s+NEEDED\s*:', content, re.IGNORECASE)),
        "STEPS":                      bool(re.search(r'\bSTEPS\s*:', content, re.IGNORECASE)),
        "COMMON ISSUES AND SOLUTIONS":bool(re.search(r'COMMON\s+ISSUES?\s+AND\s+SOLUTIONS?\s*:', content, re.IGNORECASE)),
        "CHECKLIST":                  bool(re.search(r'\bCHECKLIST\s*:', content, re.IGNORECASE)),
    }
    all_sections_present = all(sop_sections.values())
    missing_sections = [k for k, v in sop_sections.items() if not v]
    checks.append({
        "name": "sop_all_required_sections_present",
        "passed": all_sections_present,
        "detail": f"SOP sections found: {sop_sections}. Missing: {missing_sections}"
    })

    # CHECK 4b: CHECKLIST uses checkbox format (- [ ])
    checklist_format = bool(re.search(r'-\s*\[\s*\]', content))
    checks.append({
        "name": "sop_checklist_checkbox_format",
        "passed": checklist_format,
        "detail": f"Checklist uses '- [ ]' checkbox format: {checklist_format}"
    })

    # CHECK 4c: COMMON ISSUES section uses Issue:/Solution: sub-format
    issue_solution_format = bool(re.search(r'issue\s*:', content, re.IGNORECASE)) and \
                            bool(re.search(r'solution\s*:', content, re.IGNORECASE))
    checks.append({
        "name": "sop_issue_solution_subformat",
        "passed": issue_solution_format,
        "detail": f"COMMON ISSUES uses 'Issue:' and 'Solution:' labels: {issue_solution_format}"
    })

    # =========================================================
    # CHECK 5: "Double revenue before doubling team" principle referenced
    # SKILL.md Step 7 rule: Revenue growth should always lead team growth
    # =========================================================
    revenue_leads_team = any(kw in content_lower for kw in [
        "double revenue", "revenue before", "revenue should lead",
        "revenue growth should lead", "revenue first", "scale revenue before",
        "revenue lead", "team growth", "revenue lead"
    ])
    checks.append({
        "name": "revenue_leads_team_principle",
        "passed": revenue_leads_team,
        "detail": f"'Double revenue before doubling team' / revenue-leads-team principle mentioned: {revenue_leads_team}"
    })

    # =========================================================
    # CHECK 6: Scaling trap or sustainable growth rate mentioned
    # SKILL.md: grow 20-30% per quarter, not 100% overnight
    # =========================================================
    growth_rate_mentioned = bool(re.search(
        r'(20.{0,5}30\s*%|twenty.{0,5}thirty\s*percent|gradual|sustainable growth|not.{0,20}overnight)',
        content_lower
    ))
    checks.append({
        "name": "sustainable_growth_rate_mentioned",
        "passed": growth_rate_mentioned,
        "detail": f"20-30% quarterly growth guideline or sustainable growth rate mentioned: {growth_rate_mentioned}"
    })

    # =========================================================
    # SCORING
    # =========================================================
    critical_checks = [
        "correct_bottleneck_identified",
        "automation_roi_threshold_applied",
        "automation_false_positive_avoided",
        "contractor_vs_employee_decision_correct",
        "sop_all_required_sections_present",
        "sop_checklist_checkbox_format",
        "sop_issue_solution_subformat",
    ]
    bonus_checks = [
        "revenue_leads_team_principle",
        "sustainable_growth_rate_mentioned",
    ]

    check_dict = {c["name"]: c["passed"] for c in checks}

    critical_passed = sum(check_dict.get(c, False) for c in critical_checks)
    bonus_passed = sum(check_dict.get(c, False) for c in bonus_checks)

    total_critical = len(critical_checks)
    total_bonus = len(bonus_checks)

    # Score: critical checks worth 85%, bonus worth 15%
    score = (critical_passed / total_critical) * 0.85 + (bonus_passed / total_bonus) * 0.15

    # Must pass ALL critical checks to be considered "passed"
    overall_passed = (critical_passed == total_critical) and (bonus_passed >= 1)

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2))