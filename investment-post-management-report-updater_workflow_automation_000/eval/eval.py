#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluation script for the investment post-management report update task.
Checks that the agent produced a valid Q4 2024 report with correct content.
"""

import sys
import json
import os
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── CHECK 1: Output report file exists ───────────────────────────────────
    # Search for a Q4 report docx file anywhere in the workspace
    q4_report_candidates = list(workspace_path.rglob("*2024Q4*报告*.docx")) + \
                           list(workspace_path.rglob("*Q4*2024*报告*.docx")) + \
                           list(workspace_path.rglob("*四季度*投后*.docx")) + \
                           list(workspace_path.rglob("*2024*第四季度*.docx")) + \
                           list(workspace_path.rglob("*云启科技*2024Q4*.docx")) + \
                           list(workspace_path.rglob("*云启*Q4*.docx"))
    
    # Exclude template inputs
    q4_report_candidates = [p for p in q4_report_candidates 
                             if "2024Q3" not in p.name and "archive" not in str(p)]
    
    if not q4_report_candidates:
        checks.append({
            "name": "output_report_exists",
            "passed": False,
            "detail": "No Q4 2024 report DOCX file found in workspace. Expected a file named like '云启科技2024Q4投后管理报告.docx'."
        })
        return checks, False
    
    report_path = q4_report_candidates[0]
    checks.append({
        "name": "output_report_exists",
        "passed": True,
        "detail": f"Found Q4 report: {report_path}"
    })

    # ── CHECK 2: Report is a valid DOCX and not the Q3 template ──────────────
    try:
        from docx import Document
        doc = Document(str(report_path))
        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        checks.append({
            "name": "valid_docx_with_content",
            "passed": len(full_text) > 200,
            "detail": f"Document has {len(full_text)} characters of text content."
        })
    except Exception as e:
        checks.append({
            "name": "valid_docx_with_content",
            "passed": False,
            "detail": f"Failed to open or read DOCX: {e}"
        })
        return checks, False

    # ── CHECK 3: Report contains timestamp (from generate_report.py) ─────────
    try:
        has_timestamp = "报告更新时间" in full_text
        checks.append({
            "name": "contains_update_timestamp",
            "passed": has_timestamp,
            "detail": "Document contains '报告更新时间' timestamp injected by generate_report.py." if has_timestamp
                      else "Missing '报告更新时间' timestamp. generate_report.py was likely not called."
        })
    except Exception as e:
        checks.append({"name": "contains_update_timestamp", "passed": False, "detail": str(e)})

    # ── CHECK 4: Financial data - Q4 revenue figures present ─────────────────
    # Q4 revenue is 6800 万元 (from the spreadsheet)
    try:
        has_q4_revenue = "6800" in full_text
        checks.append({
            "name": "financial_data_q4_revenue",
            "passed": has_q4_revenue,
            "detail": "Document contains Q4 revenue figure '6800' (万元)." if has_q4_revenue
                      else "Missing Q4 revenue figure '6800'. Financial data was likely not extracted or included."
        })
    except Exception as e:
        checks.append({"name": "financial_data_q4_revenue", "passed": False, "detail": str(e)})

    # ── CHECK 5: Growth rate calculations present (YoY or QoQ) ───────────────
    # YoY: (6800-5200)/5200 = 30.77% ≈ 30.8% or 30.77%
    # QoQ: (6800-5950)/5950 = 14.29% ≈ 14.3% or 14.29%
    try:
        import re
        # Look for growth percentages in the relevant range for YoY (around 30%) or QoQ (around 14%)
        # Accept values like 30%, 30.8%, 30.77%, 14%, 14.3%, 14.29%
        yoy_patterns = [r'30[\.\d]*\s*%', r'3[01][\.\d]*\s*%']
        qoq_patterns = [r'14[\.\d]*\s*%', r'1[34][\.\d]*\s*%']
        
        has_yoy = any(re.search(p, full_text) for p in yoy_patterns)
        has_qoq = any(re.search(p, full_text) for p in qoq_patterns)
        has_growth_rates = has_yoy or has_qoq
        
        checks.append({
            "name": "growth_rate_calculations",
            "passed": has_growth_rates,
            "detail": f"YoY growth (~30.8%) found: {has_yoy}, QoQ growth (~14.3%) found: {has_qoq}. "
                      "At least one growth rate calculation from the financial analysis guide is required."
        })
    except Exception as e:
        checks.append({"name": "growth_rate_calculations", "passed": False, "detail": str(e)})

    # ── CHECK 6: Business update content from interview transcript ────────────
    # Interview mentions: 385 customers, ACV 1200万, v3.2版本, 政务云
    try:
        business_keywords = ["385", "1200", "v3.2", "政务云", "B轮"]
        found_keywords = [kw for kw in business_keywords if kw in full_text]
        has_business_update = len(found_keywords) >= 2
        checks.append({
            "name": "business_update_from_interview",
            "passed": has_business_update,
            "detail": f"Found {len(found_keywords)}/5 business update keywords from interview transcript: {found_keywords}. "
                      "Need at least 2 to pass."
        })
    except Exception as e:
        checks.append({"name": "business_update_from_interview", "passed": False, "detail": str(e)})

    # ── CHECK 7: Industry analysis content from interview transcript ──────────
    # Interview mentions: 580亿, 18%, 7%, 竞争对手, 数字政府
    try:
        industry_keywords = ["580", "18%", "7%", "竞争对手", "数字政府", "工信部"]
        found_industry = [kw for kw in industry_keywords if kw in full_text]
        has_industry_update = len(found_industry) >= 2
        checks.append({
            "name": "industry_update_from_interview",
            "passed": has_industry_update,
            "detail": f"Found {len(found_industry)}/6 industry analysis keywords from interview transcript: {found_industry}. "
                      "Need at least 2 to pass."
        })
    except Exception as e:
        checks.append({"name": "industry_update_from_interview", "passed": False, "detail": str(e)})

    # ── CHECK 8: Net profit figure Q4 present ────────────────────────────────
    # Net profit: 1193.4 万元
    try:
        has_net_profit = "1193" in full_text
        checks.append({
            "name": "financial_data_net_profit",
            "passed": has_net_profit,
            "detail": "Document contains Q4 net profit figure '1193' (万元)." if has_net_profit
                      else "Missing net profit '1193'. Financial statement parsing appears incomplete."
        })
    except Exception as e:
        checks.append({"name": "financial_data_net_profit", "passed": False, "detail": str(e)})

    # ── CHECK 9: Report structure preserved (key headings present) ────────────
    try:
        section_keywords = ["财务", "经营情况", "行业"]
        found_sections = [kw for kw in section_keywords if kw in full_text]
        has_structure = len(found_sections) == len(section_keywords)
        checks.append({
            "name": "report_structure_preserved",
            "passed": has_structure,
            "detail": f"Found {len(found_sections)}/{len(section_keywords)} required section headings: {found_sections}."
        })
    except Exception as e:
        checks.append({"name": "report_structure_preserved", "passed": False, "detail": str(e)})

    # ── CHECK 10: Financial JSON was passed to generate_report.py (indirect) ──
    # The generate_report.py requires --financial-data as JSON.
    # We verify indirectly: if the report was generated via the script, it will
    # have the timestamp. We also check that financial metrics were parsed and included.
    try:
        # Asset total or liability data from balance sheet
        has_assets = "13090" in full_text or "2694" in full_text or "10395" in full_text
        checks.append({
            "name": "balance_sheet_data_included",
            "passed": has_assets,
            "detail": "Document contains balance sheet figures (total assets 13090 or liabilities 2694.5). "
                      "Confirms financial statement was parsed and financial data passed to report generator."
                      if has_assets else
                      "Missing balance sheet figures. Asset/liability data from the financial statement not included."
        })
    except Exception as e:
        checks.append({"name": "balance_sheet_data_included", "passed": False, "detail": str(e)})

    return checks, True


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks, _ = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_execution", "passed": False, "detail": f"Eval script crashed: {e}"}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    
    # Critical checks that MUST pass for overall pass
    critical_checks = {
        "output_report_exists",
        "valid_docx_with_content",
        "contains_update_timestamp",
        "financial_data_q4_revenue",
        "business_update_from_interview",
    }
    
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    score = passed_count / total if total > 0 else 0.0
    overall_passed = critical_passed and score >= 0.7

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()