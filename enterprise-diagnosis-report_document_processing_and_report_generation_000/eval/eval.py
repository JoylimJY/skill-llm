#!/usr/bin/env python3
"""
Evaluation script for the enterprise diagnosis report integration task.
Checks that the agent:
1. Used pdf_parser.py to parse the three PDFs (indirectly verified via output files)
2. Produced a综合诊断报告.md with correct structure
3. Followed format rules (number formatting, section headers, subsection numbering)
4. Flagged the data conflict (企业名称 discrepancy: 明远 vs 明源)
5. Included all five required sections
6. Included the mandatory disclaimer
7. Applied risk symbols (⚠️ ⚡ 💡)
"""

import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    total_score = 0.0
    max_score = 10.0

    # ── Find the output report ───────────────────────────────────────────────
    report_path = None
    candidates = list(Path(workspace).rglob("综合诊断报告.md"))
    if not candidates:
        # Also accept variations
        candidates = list(Path(workspace).rglob("*.md"))
        candidates = [p for p in candidates if "综合" in p.name or "诊断" in p.name or "report" in p.name.lower()]
        # Exclude template
        candidates = [p for p in candidates if "template" not in p.name.lower() and "report_template" not in p.name]

    if not candidates:
        checks.append({
            "name": "Report file exists",
            "passed": False,
            "detail": "No 综合诊断报告.md (or equivalent) found anywhere in workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = candidates[0]
    checks.append({
        "name": "Report file exists",
        "passed": True,
        "detail": f"Found report at: {report_path}"
    })
    total_score += 0.5

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "Report file readable",
            "passed": False,
            "detail": f"Could not read file: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "Report file readable",
        "passed": True,
        "detail": f"File size: {len(content)} characters"
    })
    total_score += 0.5

    # ── Check 1: Five required sections ─────────────────────────────────────
    required_sections = [
        ("一、企业概况", r"一[、.．]?\s*企业概况"),
        ("二、财务健康度分析", r"二[、.．]?\s*财务健康度分析"),
        ("三、税务合规性评估", r"三[、.．]?\s*税务合规性评估"),
        ("四、政策红利与补贴机会", r"四[、.．]?\s*政策红利"),
        ("五、综合诊断结论与建议", r"五[、.．]?\s*综合诊断结论"),
    ]
    sections_found = 0
    section_details = []
    for section_name, pattern in required_sections:
        found = bool(re.search(pattern, content))
        if found:
            sections_found += 1
        section_details.append(f"{'✓' if found else '✗'} {section_name}")

    section_pass = sections_found >= 4
    checks.append({
        "name": "Five required sections present",
        "passed": section_pass,
        "detail": f"Found {sections_found}/5 sections: " + "; ".join(section_details)
    })
    if section_pass:
        total_score += 1.5

    # ── Check 2: Subsection numbering (1.1, 1.2, etc.) ──────────────────────
    subsection_pattern = r"#{2,3}\s+\d+\.\d+"
    subsections = re.findall(subsection_pattern, content)
    subsection_pass = len(subsections) >= 4
    checks.append({
        "name": "Subsection numbering (e.g., 1.1, 1.2, 2.1)",
        "passed": subsection_pass,
        "detail": f"Found {len(subsections)} numbered subsections: {subsections[:8]}"
    })
    if subsection_pass:
        total_score += 0.5

    # ── Check 3: Number formatting (千分位 + 2 decimal places for amounts) ──
    # Look for amounts formatted with commas like 25,000,000.00
    amount_pattern = r"\d{1,3}(?:,\d{3})+\.\d{2}\s*[元万]"
    amounts_found = re.findall(amount_pattern, content)
    amount_pass = len(amounts_found) >= 3
    checks.append({
        "name": "Currency amounts use 千分位 with 2 decimal places",
        "passed": amount_pass,
        "detail": f"Found {len(amounts_found)} properly formatted amounts: {amounts_found[:5]}"
    })
    if amount_pass:
        total_score += 1.0

    # ── Check 4: Percentage formatting (2 decimal places) ───────────────────
    pct_pattern = r"\d+\.\d{2}%"
    pcts_found = re.findall(pct_pattern, content)
    pct_pass = len(pcts_found) >= 2
    checks.append({
        "name": "Percentages formatted to 2 decimal places",
        "passed": pct_pass,
        "detail": f"Found {len(pcts_found)} properly formatted percentages: {pcts_found[:5]}"
    })
    if pct_pass:
        total_score += 0.5

    # ── Check 5: Data conflict flagged (明远 vs 明源) ────────────────────────
    # The agent must notice the company name discrepancy between reports
    conflict_indicators = [
        r"明远.*明源",
        r"明源.*明远",
        r"[冲差异不一致]{2,}",  # words like 冲突, 差异, 不一致
        r"数据冲突",
        r"需.*确认",
        r"⚠️.*[名称冲突差异]",
        r"[名称].*[不一致冲突差异]",
        r"报告\s*[12一二].*[不同差异冲突]",
    ]
    conflict_found = any(re.search(p, content) for p in conflict_indicators)
    # Also check for a difference/conflict table
    has_conflict_table = bool(re.search(r"\|.*[字段名称].*\|.*报告.*\|", content) or
                              re.search(r"\|.*明远.*\|.*明源.*\|", content) or
                              re.search(r"\|.*明源.*\|.*明远.*\|", content))
    conflict_pass = conflict_found or has_conflict_table
    checks.append({
        "name": "Data conflict flagged (enterprise name discrepancy 明远/明源)",
        "passed": conflict_pass,
        "detail": (
            "Conflict table or flag found." if conflict_pass
            else "No mention of the enterprise name discrepancy (明远 vs 明源) between reports 1/3 and report 2."
        )
    })
    if conflict_pass:
        total_score += 1.5

    # ── Check 6: Risk symbols present ───────────────────────────────────────
    has_warning = "⚠️" in content
    has_medium_risk = "⚡" in content
    has_low_risk = "💡" in content
    risk_count = sum([has_warning, has_medium_risk, has_low_risk])
    risk_pass = risk_count >= 2
    checks.append({
        "name": "Risk symbols used (⚠️ ⚡ 💡)",
        "passed": risk_pass,
        "detail": f"Found: ⚠️={has_warning}, ⚡={has_medium_risk}, 💡={has_low_risk}"
    })
    if risk_pass:
        total_score += 0.5

    # ── Check 7: Mandatory disclaimer ───────────────────────────────────────
    disclaimer_pattern = r"免责声明"
    has_disclaimer = bool(re.search(disclaimer_pattern, content))
    checks.append({
        "name": "Mandatory disclaimer (免责声明) present",
        "passed": has_disclaimer,
        "detail": "免责声明 found." if has_disclaimer else "No 免责声明 section found at the end of report."
    })
    if has_disclaimer:
        total_score += 0.5

    # ── Check 8: Report header with dates ───────────────────────────────────
    date_pattern = r"\d{4}-\d{2}-\d{2}"
    dates_found = re.findall(date_pattern, content)
    header_pattern = r"报告生成日期"
    has_header_date = bool(re.search(header_pattern, content)) and len(dates_found) >= 2
    checks.append({
        "name": "Report header includes 报告生成日期 and YYYY-MM-DD dates",
        "passed": has_header_date,
        "detail": f"Has 报告生成日期: {bool(re.search(header_pattern, content))}, dates found: {dates_found[:5]}"
    })
    if has_header_date:
        total_score += 0.5

    # ── Check 9: Policy section mentions specific subsidies ─────────────────
    policy_keywords = ["广东省", "深圳", "科技", "补贴", "申报", "高新技术"]
    policy_hits = sum(1 for kw in policy_keywords if kw in content)
    policy_pass = policy_hits >= 4
    checks.append({
        "name": "Policy section contains relevant policy/subsidy details",
        "passed": policy_pass,
        "detail": f"Found {policy_hits}/6 policy keywords: {[kw for kw in policy_keywords if kw in content]}"
    })
    if policy_pass:
        total_score += 0.5

    # ── Check 10: Financial data present ────────────────────────────────────
    financial_keywords = ["营业收入", "净利润", "毛利率", "资产负债率"]
    fin_hits = sum(1 for kw in financial_keywords if kw in content)
    fin_pass = fin_hits >= 3
    checks.append({
        "name": "Financial indicators present in report",
        "passed": fin_pass,
        "detail": f"Found {fin_hits}/4 indicators: {[kw for kw in financial_keywords if kw in content]}"
    })
    if fin_pass:
        total_score += 0.5

    # ── Check 11: Evidence that pdf_parser.py was used ──────────────────────
    # Check for parsed text files in output/ dir
    parsed_files = list(Path(workspace).glob("output/report*.txt"))
    parsed_files += list(Path(workspace).glob("output/*.txt"))
    parser_used = len(parsed_files) >= 1
    checks.append({
        "name": "Evidence of pdf_parser.py usage (parsed .txt files in output/)",
        "passed": parser_used,
        "detail": f"Found {len(parsed_files)} parsed output files: {[str(p) for p in parsed_files[:5]]}"
    })
    if parser_used:
        total_score += 1.0

    # ── Check 12: SWOT analysis present ────────────────────────────────────
    swot_patterns = [r"SWOT", r"优势.*劣势", r"Strengths.*Weaknesses"]
    swot_found = any(re.search(p, content, re.DOTALL) for p in swot_patterns)
    checks.append({
        "name": "SWOT analysis included in Section 5",
        "passed": swot_found,
        "detail": "SWOT analysis found." if swot_found else "No SWOT analysis detected in report."
    })
    if swot_found:
        total_score += 0.5

    # ── Final score ──────────────────────────────────────────────────────────
    final_score = min(total_score / max_score, 1.0)

    # Pass threshold: at least 60% score AND conflict check AND sections check
    critical_checks = [c for c in checks if c["name"] in [
        "Five required sections present",
        "Data conflict flagged (enterprise name discrepancy 明远/明源)",
        "Report file exists"
    ]]
    critical_pass = all(c["passed"] for c in critical_checks)

    passed = final_score >= 0.6 and critical_pass

    return {
        "passed": passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))