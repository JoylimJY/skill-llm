import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def find_report():
        candidates = list(workspace.rglob("competitor_research_report.md"))
        if not candidates:
            candidates = list(workspace.rglob("competitor_research_report.txt"))
        return candidates[0] if candidates else None

    report_path = find_report()

    # CHECK 0: File exists
    file_exists = report_path is not None and report_path.is_file()
    checks.append({
        "name": "report_file_exists",
        "passed": file_exists,
        "detail": f"Found at {report_path}" if file_exists else "competitor_research_report.md not found anywhere in workspace"
    })
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    # CHECK 1: Executive Summary section present with top 3 findings + top 3 recommendations
    has_exec_summary = bool(re.search(r"executive\s+summary", content_lower))
    checks.append({
        "name": "section_executive_summary_present",
        "passed": has_exec_summary,
        "detail": "Executive Summary section found" if has_exec_summary else "Missing 'Executive Summary' section"
    })
    if has_exec_summary:
        total_score += 0.08

    # Check for exactly top 3 findings (key findings, not just any list)
    findings_match = re.search(
        r"(key\s+finding|top\s+3\s+finding|finding\s+[123]|#1|#2|#3|finding\s+1|finding\s+2|finding\s+3)",
        content_lower
    )
    has_top3_findings = findings_match is not None
    checks.append({
        "name": "executive_summary_top3_findings",
        "passed": has_top3_findings,
        "detail": "Top 3 findings found in Executive Summary" if has_top3_findings else "No enumerated top-3 findings found"
    })
    if has_top3_findings:
        total_score += 0.07

    rec_match = re.search(
        r"(top\s+3\s+rec|recommendation\s+[123]|#1.*rec|rec.*#1|recommendation\s+1|recommendation\s+2|recommendation\s+3)",
        content_lower
    )
    has_top3_recs_exec = rec_match is not None
    checks.append({
        "name": "executive_summary_top3_recommendations",
        "passed": has_top3_recs_exec,
        "detail": "Top 3 recommendations found in Executive Summary" if has_top3_recs_exec else "No enumerated top-3 recommendations in Executive Summary"
    })
    if has_top3_recs_exec:
        total_score += 0.07

    # CHECK 2: Competitor Overview section
    has_comp_overview = bool(re.search(r"competitor\s+overview", content_lower))
    checks.append({
        "name": "section_competitor_overview",
        "passed": has_comp_overview,
        "detail": "Competitor Overview section present" if has_comp_overview else "Missing 'Competitor Overview' section"
    })
    if has_comp_overview:
        total_score += 0.05

    # Must contain: category, market position, key strength fields
    overview_fields = {
        "category": bool(re.search(r"\bcategory\b", content_lower)),
        "market_position": bool(re.search(r"market\s+position", content_lower)),
        "key_strength": bool(re.search(r"key\s+strength", content_lower)),
    }
    all_overview_fields = all(overview_fields.values())
    checks.append({
        "name": "competitor_overview_required_fields",
        "passed": all_overview_fields,
        "detail": f"Fields present: {overview_fields}" 
    })
    if all_overview_fields:
        total_score += 0.06

    # CHECK 3: Product Comparison section
    has_product_comp = bool(re.search(r"product\s+comparison", content_lower))
    checks.append({
        "name": "section_product_comparison",
        "passed": has_product_comp,
        "detail": "Product Comparison section present" if has_product_comp else "Missing 'Product Comparison' section"
    })
    if has_product_comp:
        total_score += 0.05

    # CHECK 4: SWOT Analysis section with competitor deep dives
    has_swot = bool(re.search(r"swot", content_lower))
    checks.append({
        "name": "section_swot_analysis",
        "passed": has_swot,
        "detail": "SWOT Analysis section present" if has_swot else "Missing SWOT Analysis section"
    })
    if has_swot:
        total_score += 0.05

    swot_elements = {
        "strengths": bool(re.search(r"\bstrength", content_lower)),
        "weaknesses": bool(re.search(r"\bweakness", content_lower)),
        "opportunities": bool(re.search(r"\bopportunity\b|\bopportunities\b", content_lower)),
        "threats": bool(re.search(r"\bthreat", content_lower)),
    }
    has_all_swot = all(swot_elements.values())
    checks.append({
        "name": "swot_all_four_elements",
        "passed": has_all_swot,
        "detail": f"SWOT elements: {swot_elements}"
    })
    if has_all_swot:
        total_score += 0.05

    # CHECK 5: Marketing & Messaging section
    has_mktg = bool(re.search(r"marketing\s*(and|&)\s*messaging", content_lower))
    checks.append({
        "name": "section_marketing_messaging",
        "passed": has_mktg,
        "detail": "Marketing & Messaging section present" if has_mktg else "Missing 'Marketing & Messaging' section"
    })
    if has_mktg:
        total_score += 0.05

    # Must contain: value prop, target audience, key channels
    mktg_fields = {
        "value_prop": bool(re.search(r"value\s+prop", content_lower)),
        "target_audience": bool(re.search(r"target\s+audience", content_lower)),
        "key_channels": bool(re.search(r"key\s+channel", content_lower)),
    }
    all_mktg_fields = all(mktg_fields.values())
    checks.append({
        "name": "marketing_messaging_required_fields",
        "passed": all_mktg_fields,
        "detail": f"Marketing fields: {mktg_fields}"
    })
    if all_mktg_fields:
        total_score += 0.05

    # CHECK 6: Gaps & Opportunities section
    has_gaps = bool(re.search(r"gap[s]?\s*(and|&)\s*opportunit", content_lower))
    checks.append({
        "name": "section_gaps_opportunities",
        "passed": has_gaps,
        "detail": "Gaps & Opportunities section present" if has_gaps else "Missing 'Gaps & Opportunities' section"
    })
    if has_gaps:
        total_score += 0.05

    # Must have: gap, opportunity, priority columns/fields
    gap_fields = {
        "gap": bool(re.search(r"\bgap\b", content_lower)),
        "opportunity": bool(re.search(r"\bopportunit", content_lower)),
        "priority": bool(re.search(r"\bpriority\b|\bpriorities\b", content_lower)),
    }
    all_gap_fields = all(gap_fields.values())
    checks.append({
        "name": "gaps_opportunities_required_fields",
        "passed": all_gap_fields,
        "detail": f"Gap fields: {gap_fields}"
    })
    if all_gap_fields:
        total_score += 0.05

    # CHECK 7: Prioritized Recommendations section — must have impact, effort, owner
    has_prio_rec = bool(re.search(r"prioritized\s+recommendation", content_lower))
    checks.append({
        "name": "section_prioritized_recommendations",
        "passed": has_prio_rec,
        "detail": "Prioritized Recommendations section present" if has_prio_rec else "Missing 'Prioritized Recommendations' section"
    })
    if has_prio_rec:
        total_score += 0.05

    rec_fields = {
        "impact": bool(re.search(r"\bimpact\b", content_lower)),
        "effort": bool(re.search(r"\beffort\b", content_lower)),
        "owner": bool(re.search(r"\bowner\b", content_lower)),
    }
    all_rec_fields = all(rec_fields.values())
    checks.append({
        "name": "prioritized_recommendations_required_fields",
        "passed": all_rec_fields,
        "detail": f"Recommendation fields: {rec_fields}"
    })
    if all_rec_fields:
        total_score += 0.06

    # CHECK 8: Actual competitor names from the Excel file are in the report
    competitors = ["asana", "monday", "clickup", "notion", "basecamp"]
    found_competitors = [c for c in competitors if c in content_lower]
    has_multiple_competitors = len(found_competitors) >= 3
    checks.append({
        "name": "competitor_data_parsed_from_excel",
        "passed": has_multiple_competitors,
        "detail": f"Found {len(found_competitors)} competitor names in report: {found_competitors}"
    })
    if has_multiple_competitors:
        total_score += 0.06

    # CHECK 9: Research types are covered (keyword, content, backlink)
    research_types = {
        "keyword_gap": bool(re.search(r"keyword\s*(gap|opportunit|overlap)", content_lower)),
        "content_gap": bool(re.search(r"content\s*gap", content_lower)),
        "backlink_link_gap": bool(re.search(r"(link\s*gap|backlink|referring\s*domain|linking\s*site)", content_lower)),
        "pricing": bool(re.search(r"pricing|freemium|per\s*user", content_lower)),
    }
    covered_types = sum(research_types.values())
    has_research_types = covered_types >= 3
    checks.append({
        "name": "multiple_research_types_covered",
        "passed": has_research_types,
        "detail": f"{covered_types}/4 research types covered: {research_types}"
    })
    if has_research_types:
        total_score += 0.07

    # CHECK 10: SERP overlap / keyword opportunity data referenced (rank #4-10 is opportunity)
    has_serp_data = bool(re.search(r"(serp|organic\s+rank|rank\s+[0-9]|keyword\s+rank|agile\s+project\s+management|team\s+task)", content_lower))
    checks.append({
        "name": "serp_overlap_data_referenced",
        "passed": has_serp_data,
        "detail": "SERP overlap / ranking data referenced" if has_serp_data else "No SERP or keyword ranking data found in report"
    })
    if has_serp_data:
        total_score += 0.04

    # CHECK 11: Link gap data referenced (unique linking sites / referring domains)
    has_link_gap = bool(re.search(r"(link\s+gap|referring\s+domain|unique\s+linking|sites\s+not\s+linking|44.?000|61.?000|31.?000)", content_lower))
    checks.append({
        "name": "link_gap_data_present",
        "passed": has_link_gap,
        "detail": "Link gap / referring domain data present" if has_link_gap else "No link gap data found"
    })
    if has_link_gap:
        total_score += 0.04

    # CHECK 12: Content length benchmarks from the Excel data
    has_content_length = bool(re.search(r"(avg\s+content|content\s+length|word\s+count|2[,.]?[0-9]{3}\s*words?|1[,.]?[0-9]{3}\s*words?)", content_lower))
    checks.append({
        "name": "content_length_benchmarks",
        "passed": has_content_length,
        "detail": "Content length benchmarks referenced" if has_content_length else "No content length / word count data found"
    })
    if has_content_length:
        total_score += 0.04

    # CHECK 13: TaskFlow Pro (company name) appears in the report
    has_company_name = bool(re.search(r"taskflow\s+pro|taskflowpro", content_lower))
    checks.append({
        "name": "company_context_used",
        "passed": has_company_name,
        "detail": "Company name TaskFlow Pro found in report" if has_company_name else "Company name not found; project-context.md may not have been read"
    })
    if has_company_name:
        total_score += 0.06

    # Final pass/fail: must score at least 0.60 and have all 7 required sections
    required_sections = [
        has_exec_summary, has_comp_overview, has_product_comp,
        has_swot, has_mktg, has_gaps, has_prio_rec
    ]
    all_sections_present = all(required_sections)
    checks.append({
        "name": "all_seven_sections_present",
        "passed": all_sections_present,
        "detail": f"All 7 required sections: {all_sections_present}. Sections: exec={has_exec_summary}, overview={has_comp_overview}, product={has_product_comp}, swot={has_swot}, mktg={has_mktg}, gaps={has_gaps}, recs={has_prio_rec}"
    })
    if all_sections_present:
        total_score += 0.06

    # Cap score at 1.0
    final_score = min(round(total_score, 4), 1.0)
    passed = final_score >= 0.60 and all_sections_present and file_exists

    return {"passed": passed, "score": final_score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2))