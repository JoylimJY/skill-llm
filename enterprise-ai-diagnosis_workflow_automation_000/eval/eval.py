import sys
import json
import re
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    """Find the diagnosis report file."""
    candidates = list(Path(workspace).rglob("ai_diagnosis_report.md"))
    if candidates:
        return candidates[0]
    # Also accept slight variations
    for p in Path(workspace).rglob("*.md"):
        name = p.name.lower()
        if "diagnosis" in name or "诊断" in name or ("ai" in name and "report" in name):
            return p
    return None


def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}


def run_eval(workspace: str) -> dict:
    checks = []

    # ── 0. File existence ────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        checks.append(check("report_file_exists", False, "No ai_diagnosis_report.md (or equivalent) found in workspace."))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append(check("report_file_exists", True, f"Found report at: {report_path}"))

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("report_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("report_readable", True, f"Report length: {len(content)} characters"))

    # ── 1. Company context present ───────────────────────────────────────────
    company_mentioned = "顺达" in content or "shunda" in content.lower() or "物流" in content
    checks.append(check(
        "company_context_present",
        company_mentioned,
        "Report references the company (顺达/物流)" if company_mentioned else "Report does not mention the subject company."
    ))

    # ── 2. Enterprise Assessment section ────────────────────────────────────
    has_assessment = bool(re.search(
        r'(企业.*?评估|现状.*?分析|assessment|评估问卷|业务.*?流程)',
        content, re.IGNORECASE
    ))
    checks.append(check(
        "section_enterprise_assessment",
        has_assessment,
        "Found enterprise assessment section." if has_assessment else "Missing enterprise assessment / current state analysis section."
    ))

    # ── 3. AI Applicability Scores (0-100) per department/process ───────────
    # Must find numeric scores in 0-100 range tied to departments/processes
    score_patterns = re.findall(r'(\d{1,3})\s*[分/]?100|适用性.*?(\d{1,3})\s*分|(\d{1,3})\s*分.*?适用|score.*?(\d{1,3})', content, re.IGNORECASE)
    numeric_scores = re.findall(r'(\d{1,3})\s*[分/]?\s*(?:/\s*100|分)', content)
    valid_scores = [int(s) for s in numeric_scores if 0 <= int(s) <= 100]

    # Also look for patterns like "85分" or "72/100" or "适用性: 78"
    alt_scores = re.findall(r'(?:适用性|得分|评分|score)[：:]\s*(\d{1,3})', content, re.IGNORECASE)
    all_scores = valid_scores + [int(s) for s in alt_scores if 0 <= int(s) <= 100]

    has_scores = len(all_scores) >= 3  # At least 3 department scores
    checks.append(check(
        "ai_applicability_scores_0_to_100",
        has_scores,
        f"Found {len(all_scores)} valid 0-100 scores for business processes/departments." if has_scores
        else f"Missing per-department AI applicability scores (0-100). Found only {len(all_scores)} valid scores (need ≥3)."
    ))

    # ── 4. ROI Calculation section ───────────────────────────────────────────
    has_roi_section = bool(re.search(r'ROI|投资回报|回报率|return on investment', content, re.IGNORECASE))
    checks.append(check(
        "section_roi_present",
        has_roi_section,
        "ROI section found." if has_roi_section else "No ROI section found."
    ))

    # ROI must include costs (tool + training + time)
    has_cost_breakdown = bool(re.search(
        r'(工具.*?成本|培训.*?成本|时间.*?成本|tool.*?cost|training.*?cost|投入.*?成本|成本.*?分析)',
        content, re.IGNORECASE
    ))
    checks.append(check(
        "roi_cost_breakdown",
        has_cost_breakdown,
        "Cost breakdown (tools/training/time) found in ROI section." if has_cost_breakdown
        else "ROI section missing cost breakdown (tools + training + time investment)."
    ))

    # ROI must include benefits (labor savings + efficiency + error reduction)
    has_benefit_breakdown = bool(re.search(
        r'(人力.*?节省|效率.*?提升|错误.*?减少|节省人力|效率提升|labor.*?sav|efficiency|error.*?reduc)',
        content, re.IGNORECASE
    ))
    checks.append(check(
        "roi_benefit_breakdown",
        has_benefit_breakdown,
        "Benefit breakdown (labor savings/efficiency/error reduction) found." if has_benefit_breakdown
        else "ROI section missing benefit breakdown (人力节省+效率提升+错误减少)."
    ))

    # Payback period must be mentioned
    has_payback = bool(re.search(
        r'(回报周期|回本周期|payback|回本.*?月|个月.*?回|投资回收|回收期)',
        content, re.IGNORECASE
    ))
    checks.append(check(
        "roi_payback_period",
        has_payback,
        "Payback period prediction found." if has_payback else "Missing payback period prediction in ROI section."
    ))

    # ── 5. Three-phase implementation plan ──────────────────────────────────
    has_phase_1_2_week = bool(re.search(r'1[-–—]?2\s*周|第一.*?周|week\s*1[-–—]?2|1.2.*?week', content, re.IGNORECASE))
    has_phase_1_month = bool(re.search(r'1\s*个月|第.*?月|one\s*month|1.*?month', content, re.IGNORECASE))
    has_phase_3_month = bool(re.search(r'3\s*个月|三个月|three\s*month|3.*?month', content, re.IGNORECASE))

    three_phase = has_phase_1_2_week and has_phase_1_month and has_phase_3_month
    checks.append(check(
        "implementation_three_phases",
        three_phase,
        f"Three-phase plan found (1-2周:{has_phase_1_2_week}, 1个月:{has_phase_1_month}, 3个月:{has_phase_3_month})."
        if three_phase else
        f"Missing complete 3-phase implementation plan. Phases found — 1-2周:{has_phase_1_2_week}, 1个月:{has_phase_1_month}, 3个月:{has_phase_3_month}."
    ))

    # ── 6. Tool recommendations with free/low-cost/professional categories ──
    has_free_tools = bool(re.search(r'(免费|free|开源|open.?source)', content, re.IGNORECASE))
    has_paid_tools = bool(re.search(r'(低成本|专业|professional|低价|付费|收费|pro版)', content, re.IGNORECASE))
    has_tool_recs = bool(re.search(r'(工具推荐|recommended.*?tool|推荐工具|tool.*?recommend)', content, re.IGNORECASE))

    tool_categories = has_free_tools and has_paid_tools
    checks.append(check(
        "tool_recommendations_with_categories",
        tool_categories,
        "Tool recommendations include free and paid/professional options." if tool_categories
        else f"Tool recommendations missing free/paid categorization. Has free:{has_free_tools}, Has paid/professional:{has_paid_tools}."
    ))

    # ── 7. Week-1 execution checklist ───────────────────────────────────────
    has_checklist = bool(re.search(
        r'(第1周|第一周|week\s*1|执行清单|checklist|任务清单|行动.*?清单)',
        content, re.IGNORECASE
    ))
    # Checklist should have actionable items (bullet points or numbered list)
    has_list_items = len(re.findall(r'^[\s]*[-*•✓□☐\d]+[\s.、)].+', content, re.MULTILINE)) >= 5
    checklist_ok = has_checklist and has_list_items
    checks.append(check(
        "week1_execution_checklist",
        checklist_ok,
        f"Week-1 execution checklist found with actionable items." if checklist_ok
        else f"Missing Week-1 execution checklist (has_checklist:{has_checklist}, has_list_items:{has_list_items})."
    ))

    # ── 8. Risk section ──────────────────────────────────────────────────────
    has_risk = bool(re.search(r'(风险|risk|挑战|challenge|注意事项|应对)', content, re.IGNORECASE))
    checks.append(check(
        "risk_section_present",
        has_risk,
        "Risk/challenge section found." if has_risk else "No risk or mitigation section found."
    ))

    # ── 9. Markdown format quality ───────────────────────────────────────────
    has_headers = len(re.findall(r'^#{1,3}\s+.+', content, re.MULTILINE)) >= 5
    checks.append(check(
        "markdown_structure_quality",
        has_headers,
        f"Found {len(re.findall(r'^#{1,3} .+', content, re.MULTILINE))} markdown headers (≥5 required)."
        if has_headers else "Insufficient markdown structure (fewer than 5 headers)."
    ))

    # ── 10. Quantitative ROI numbers present ────────────────────────────────
    # Must have at least some monetary or percentage figures
    monetary_figures = re.findall(r'[¥￥]\s*[\d,]+|[\d,]+\s*万元|[\d.]+%|[\d,]+\s*元', content)
    has_quant_roi = len(monetary_figures) >= 3
    checks.append(check(
        "quantitative_figures_in_roi",
        has_quant_roi,
        f"Found {len(monetary_figures)} quantitative figures (monetary/percentage) — meets ≥3 threshold."
        if has_quant_roi else
        f"Insufficient quantitative figures in report (found {len(monetary_figures)}, need ≥3). ROI must include actual numbers."
    ))

    # ── Scoring ──────────────────────────────────────────────────────────────
    weights = {
        "report_file_exists": 5,
        "report_readable": 2,
        "company_context_present": 5,
        "section_enterprise_assessment": 10,
        "ai_applicability_scores_0_to_100": 15,
        "section_roi_present": 8,
        "roi_cost_breakdown": 10,
        "roi_benefit_breakdown": 10,
        "roi_payback_period": 8,
        "implementation_three_phases": 12,
        "tool_recommendations_with_categories": 5,
        "week1_execution_checklist": 5,
        "risk_section_present": 3,
        "markdown_structure_quality": 5,
        "quantitative_figures_in_roi": 7,
    }

    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)

    # Must pass critical checks to be considered passing
    critical_checks = [
        "report_file_exists",
        "ai_applicability_scores_0_to_100",
        "section_roi_present",
        "roi_cost_breakdown",
        "roi_benefit_breakdown",
        "roi_payback_period",
        "implementation_three_phases",
        "quantitative_figures_in_roi",
    ]
    critical_passed = all(
        any(c["name"] == cc and c["passed"] for c in checks)
        for cc in critical_checks
    )

    passed = critical_passed and score >= 0.70

    return {
        "passed": passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))