import sys
import json
import re
import subprocess
import math
from pathlib import Path

def run_checks(workspace_dir: str):
    ws = Path(workspace_dir)
    checks = []
    
    # ── Find the report file ──────────────────────────────────────────────────
    report_files = list(ws.rglob("longxin_budget_report.md")) + \
                   list(ws.rglob("longxin_budget_report.txt"))
    
    if not report_files:
        # Also accept any file with 隆鑫 in name ending in .md or .txt
        report_files = [f for f in ws.rglob("*") 
                        if ("隆鑫" in f.name or "longxin" in f.name.lower()) 
                        and f.suffix in (".md", ".txt") 
                        and "draft" not in f.name.lower()
                        and "incomplete" not in f.name.lower()]
    
    if not report_files:
        checks.append({"name": "report_file_exists", "passed": False, 
                        "detail": "No report file found. Expected 'longxin_budget_report.md' or similar."})
        return checks
    
    # Use the most recently modified one
    report_file = sorted(report_files, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    
    try:
        content = report_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_file_readable", "passed": False, "detail": str(e)})
        return checks
    
    checks.append({"name": "report_file_exists", "passed": True, 
                    "detail": f"Found: {report_file.relative_to(ws)}"})
    
    # ── CHECK 1: Report contains company name ─────────────────────────────────
    has_company = "隆鑫精密" in content
    checks.append({"name": "company_name_present", "passed": has_company,
                    "detail": "Report must reference '隆鑫精密'"})
    
    # ── CHECK 2: Required sections present ───────────────────────────────────
    required_sections = ["企业画像", "预算估算", "预算构成", "采购周期", "销售建议", "置信度"]
    missing = [s for s in required_sections if s not in content]
    checks.append({
        "name": "required_sections_present",
        "passed": len(missing) == 0,
        "detail": f"Missing sections: {missing}" if missing else "All required sections present"
    })
    
    # ── CHECK 3: Industry correctly identified as manufacturing ───────────────
    mfg_keywords = ["制造", "manufacturing", "精密加工", "汽车供应链"]
    has_industry = any(kw in content for kw in mfg_keywords)
    checks.append({"name": "industry_manufacturing", "passed": has_industry,
                    "detail": "Industry must be identified as manufacturing/制造业"})
    
    # ── CHECK 4: Budget_engine.py was called with correct method(s) ──────────
    # The correct approach: revenue=48.3亿, industry=manufacturing
    # Method A: it_lo=48.3*0.01=0.483亿, it_hi=48.3*0.03=1.449亿
    # Digital: lo=0.483*0.30=0.1449亿, hi=1.449*0.50=0.7245亿
    # Method B: tech_headcount=280, cost_per_head=40万, total=11200万=1.12亿
    # Method D: bid_total=1670万, it_lo=1670*3=5010万, it_hi=1670*5=8350万
    
    # We check that budget numbers are in realistic range for manufacturing company
    # IT budget should be in range ~0.48-1.45亿 for revenue method
    # Look for numbers indicating budget was computed (not just made up)
    
    # Run budget_engine ourselves to get expected values
    try:
        result_a = json.loads(subprocess.check_output(
            ["python3", "/workspace/tools/budget_engine.py", 
             "--method", "A", "--revenue", "48.3", "--industry", "manufacturing"],
            stderr=subprocess.DEVNULL
        ))
        result_b = json.loads(subprocess.check_output(
            ["python3", "/workspace/tools/budget_engine.py",
             "--method", "B", "--tech_headcount", "280", "--industry", "manufacturing"],
            stderr=subprocess.DEVNULL
        ))
        result_d = json.loads(subprocess.check_output(
            ["python3", "/workspace/tools/budget_engine.py",
             "--method", "D", "--bid_total", "1670", "--industry", "manufacturing"],
            stderr=subprocess.DEVNULL
        ))
        engine_ok = True
    except Exception as e:
        engine_ok = False
        checks.append({"name": "budget_engine_reference_calc", "passed": False,
                        "detail": f"Could not run budget_engine for reference: {e}"})
    
    if engine_ok:
        # Expected IT budget ranges (亿元):
        # Method A: 0.483 - 1.449
        # Method B: 1.12 - 1.12
        # Method D: 0.501 - 0.835
        # Merged (A+B+D): avg of lows, avg of highs
        merged_it_lo = (result_a["it_budget_yi"][0] + result_b["it_budget_yi"][0] + result_d["it_budget_yi"][0]) / 3
        merged_it_hi = (result_a["it_budget_yi"][1] + result_b["it_budget_yi"][1] + result_d["it_budget_yi"][1]) / 3
        merged_dg_lo = (result_a["digital_budget_yi"][0] + result_b["digital_budget_yi"][0] + result_d["digital_budget_yi"][0]) / 3
        merged_dg_hi = (result_a["digital_budget_yi"][1] + result_b["digital_budget_yi"][1] + result_d["digital_budget_yi"][1]) / 3
        
        # Convert to 万元 for easier text matching
        it_lo_wan = round(merged_it_lo * 10000)
        it_hi_wan = round(merged_it_hi * 10000)
        dg_lo_wan = round(merged_dg_lo * 10000)
        dg_hi_wan = round(merged_dg_hi * 10000)
        
        # Check that report contains numbers in reasonable range of expected budget
        # Look for any numeric pattern that's in range ±30% of expected
        numbers_in_content = [float(x.replace(',', '')) for x in re.findall(r'[\d,]+(?:\.\d+)?', content) if float(x.replace(',','')) > 100]
        
        # IT budget in report should include values around it_lo_wan to it_hi_wan
        it_range_lo = it_lo_wan * 0.5  # allow 50% tolerance for merged averages
        it_range_hi = it_hi_wan * 2.0
        
        budget_numbers_found = any(it_range_lo <= n <= it_range_hi for n in numbers_in_content)
        checks.append({
            "name": "budget_numbers_in_expected_range",
            "passed": budget_numbers_found,
            "detail": f"Expected IT budget around {it_lo_wan:.0f}-{it_hi_wan:.0f}万元. "
                      f"Numbers found in report: {sorted(numbers_in_content)[:10]}"
        })
        
        checks.append({
            "name": "budget_engine_reference_calc",
            "passed": True,
            "detail": f"Method A IT: {result_a['it_budget_yi']}亿 | "
                      f"Method B IT: {result_b['it_budget_yi']}亿 | "
                      f"Method D IT: {result_d['it_budget_yi']}亿"
        })
    
    # ── CHECK 5: Multiple estimation methods used ─────────────────────────────
    method_indicators = ["营收比例", "人员比例", "招投标", "方法A", "方法B", "方法D",
                         "Method A", "Method B", "Method D", "revenue", "headcount"]
    methods_mentioned = sum(1 for m in method_indicators if m.lower() in content.lower())
    checks.append({
        "name": "multiple_methods_used",
        "passed": methods_mentioned >= 2,
        "detail": f"Found {methods_mentioned} method references. Expected at least 2 different estimation methods."
    })
    
    # ── CHECK 6: Confidence score present and reasonable ─────────────────────
    # With 3 sources (financial_report, bid_record, job_posting), confidence should be computed
    # Expected: weighted_avg * 0.95 (3 sources)
    # With sources: financial(0.95), bid(0.85), job_posting(0.50) and weights ~equal
    # weighted_avg ≈ (0.95+0.85+0.50)/3 ≈ 0.767, × 0.95 ≈ 0.728 → ~70-75%
    # Range: 60-85% would be reasonable
    
    confidence_patterns = re.findall(r'(\d{1,3})%', content)
    confidence_values = [int(v) for v in confidence_patterns if 30 <= int(v) <= 99]
    
    reasonable_confidence = any(55 <= v <= 88 for v in confidence_values)
    checks.append({
        "name": "confidence_score_present_and_reasonable",
        "passed": reasonable_confidence,
        "detail": f"Confidence percentages found: {confidence_values}. "
                  f"Expected a value in 55-88% range (manufacturing, 3 data sources)."
    })
    
    # ── CHECK 7: 15+ budget subcategories present ─────────────────────────────
    subcategory_keywords = [
        "云服务", "计算", "存储", "数据库", "大模型", "AI", "开发工具",
        "数据分析", "安全", "网络", "ERP", "MES", "IoT", "工业互联",
        "低代码", "运维", "监控", "协同", "培训", "咨询"
    ]
    subcats_found = sum(1 for kw in subcategory_keywords if kw in content)
    checks.append({
        "name": "fifteen_plus_budget_subcategories",
        "passed": subcats_found >= 10,
        "detail": f"Found {subcats_found} subcategory keywords. Expected 10+ (targeting 15+ per SKILL.md spec)."
    })
    
    # ── CHECK 8: Vendor landscape present ────────────────────────────────────
    known_vendors = ["SAP", "阿里云", "华为", "海康", "帆软", "钉钉", "炬光"]
    vendors_found = [v for v in known_vendors if v in content]
    checks.append({
        "name": "vendor_landscape_present",
        "passed": len(vendors_found) >= 3,
        "detail": f"Vendors mentioned: {vendors_found}. Expected at least 3 known vendors from research data."
    })
    
    # ── CHECK 9: Decision makers section with star ratings ───────────────────
    has_decision_makers = any(name in content for name in ["王建国", "李华", "陈敏", "赵强", "CTO", "信息化总监"])
    has_star_ratings = "⭐" in content or "★" in content or "stars" in content.lower()
    checks.append({
        "name": "decision_makers_with_ratings",
        "passed": has_decision_makers and has_star_ratings,
        "detail": f"Decision makers found: {has_decision_makers}, Star ratings present: {has_star_ratings}"
    })
    
    # ── CHECK 10: Sales recommendations with specific timing ─────────────────
    month_patterns = re.findall(r'(\d{1,2})月|Q[1-4]|[Qq]uarter', content)
    has_timing = len(month_patterns) >= 2
    has_pricing = "¥" in content or "万" in content
    checks.append({
        "name": "sales_recommendations_with_timing_pricing",
        "passed": has_timing and has_pricing,
        "detail": f"Month/quarter references: {month_patterns[:5]}, Has pricing: {has_pricing}"
    })
    
    # ── CHECK 11: Data sources cited with confidence explanation ─────────────
    source_types = ["工商", "招投标", "招聘", "新闻", "财报", "annual", "bid", "job"]
    sources_cited = sum(1 for s in source_types if s.lower() in content.lower())
    checks.append({
        "name": "data_sources_cited",
        "passed": sources_cited >= 3,
        "detail": f"Data source references found: {sources_cited}. Expected at least 3."
    })
    
    # ── CHECK 12: Budget range format (interval not single number) ────────────
    # Look for patterns like XXX-XXX万 or XXX~XXX
    range_patterns = re.findall(r'[\d,]+\s*[-~]\s*[\d,]+\s*万', content)
    has_ranges = len(range_patterns) >= 3
    checks.append({
        "name": "budget_expressed_as_ranges",
        "passed": has_ranges,
        "detail": f"Budget range patterns found: {range_patterns[:5]}. "
                  f"Expected intervals (e.g., 500-1200万) not single numbers."
    })
    
    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_execution", "passed": False, "detail": f"Eval crashed: {e}"}]
    
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total if total > 0 else 0.0
    overall_passed = score >= 0.75
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()