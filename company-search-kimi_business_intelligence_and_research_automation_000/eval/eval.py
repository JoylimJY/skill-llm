import sys
import json
import re
from pathlib import Path

def find_report(workspace):
    """Find the company research report file."""
    candidates = list(Path(workspace).rglob("company_research_report.md"))
    if not candidates:
        return None
    # Return the most recently modified
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []
    
    try:
        report_path = find_report(workspace)
        if report_path is None:
            checks.append(check("report_file_exists", False, "company_research_report.md not found anywhere in workspace"))
            return False, 0.0, checks
        
        content = report_path.read_text(encoding="utf-8")
        checks.append(check("report_file_exists", True, f"Found at {report_path}"))
    except Exception as e:
        checks.append(check("report_file_exists", False, f"Error reading report: {e}"))
        return False, 0.0, checks

    # ---- CHECK 1: Report header with company name ----
    try:
        has_header = "顺达物流科技" in content and "公司调研报告" in content
        checks.append(check(
            "report_header_company_name",
            has_header,
            "Report header should contain '顺达物流科技' and '公司调研报告'" if not has_header else "OK"
        ))
    except Exception as e:
        checks.append(check("report_header_company_name", False, str(e)))

    # ---- CHECK 2: Report metadata (generation date, primary entity, credit code) ----
    try:
        has_date = bool(re.search(r'报告生成时间[：:]\s*\d{4}-\d{2}-\d{2}', content))
        has_entity = "主体口径" in content or "Primary Entity" in content or "顺达物流科技有限公司" in content
        checks.append(check("report_metadata_date", has_date, "Missing '报告生成时间: YYYY-MM-DD'" if not has_date else "OK"))
        checks.append(check("report_metadata_entity", has_entity, "Missing primary entity declaration" if not has_entity else "OK"))
    except Exception as e:
        checks.append(check("report_metadata", False, str(e)))

    # ---- CHECK 3: Entity disambiguation section (Step 0) ----
    try:
        has_disambiguation = (
            ("调查主体" in content or "候选主体" in content or "0️⃣" in content or "实体" in content)
            and ("顺达货运" in content or "候选" in content or "消歧" in content or "Primary" in content)
        )
        has_primary_selection = (
            "Primary" in content or "主主体" in content or "选定" in content or "本报告" in content
        )
        checks.append(check(
            "entity_disambiguation_section",
            has_disambiguation,
            "Missing entity disambiguation section (Step 0) comparing 顺达物流科技 vs 顺达货运" if not has_disambiguation else "OK"
        ))
        checks.append(check(
            "entity_primary_selection",
            has_primary_selection,
            "Missing primary entity selection statement" if not has_primary_selection else "OK"
        ))
    except Exception as e:
        checks.append(check("entity_disambiguation_section", False, str(e)))

    # ---- CHECK 4: Basic info section with markdown table ----
    try:
        has_basic_section = "基本信息" in content or "1️⃣" in content
        # Check for markdown table structure in basic info area
        has_table = bool(re.search(r'\|[^|]+\|[^|]+\|[^|]+\|[^|]+\|', content))
        
        # Check key fields
        has_credit_code = "91440300" in content or "统一社会信用代码" in content
        has_legal_rep = "张建国" in content
        has_capital = "8000" in content
        has_founded = "2016" in content
        has_status = "存续" in content
        
        checks.append(check("basic_info_section", has_basic_section, "Missing basic info section" if not has_basic_section else "OK"))
        checks.append(check("basic_info_table", has_table, "Missing markdown table in report" if not has_table else "OK"))
        checks.append(check("basic_info_legal_rep", has_legal_rep, "Missing legal representative 张建国" if not has_legal_rep else "OK"))
        checks.append(check("basic_info_capital", has_capital, "Missing registered capital 8000万" if not has_capital else "OK"))
        checks.append(check("basic_info_founded", has_founded, "Missing founding year 2016" if not has_founded else "OK"))
        checks.append(check("basic_info_status", has_status, "Missing company status '存续'" if not has_status else "OK"))
    except Exception as e:
        checks.append(check("basic_info_section", False, str(e)))

    # ---- CHECK 5: Credibility ratings A/B/C ----
    try:
        has_grade_a = bool(re.search(r'\bA\b', content)) or "可信度.*A" in content or "| A |" in content
        has_grade_b = bool(re.search(r'\| B \|', content)) or "可信度.*B" in content
        has_grade_c = bool(re.search(r'\| C \|', content)) or "可信度.*C" in content
        
        # More flexible check: A/B/C appear in table cells
        credibility_abc = bool(re.search(r'\|\s*[ABC]\s*\|', content))
        
        checks.append(check(
            "credibility_ratings_present",
            credibility_abc or (has_grade_a and has_grade_b),
            "Missing credibility ratings A/B/C in table columns" if not (credibility_abc or (has_grade_a and has_grade_b)) else "OK"
        ))
    except Exception as e:
        checks.append(check("credibility_ratings_present", False, str(e)))

    # ---- CHECK 6: Shareholder structure section ----
    try:
        has_shareholder = "股权" in content or "股东" in content or "2️⃣" in content
        has_shareholders_data = "深圳顺科投资" in content or "60%" in content
        has_zhang = "张建国" in content and ("25%" in content or "股东" in content)
        has_wang = "王芳" in content and "15%" in content
        
        checks.append(check("shareholder_section", has_shareholder, "Missing shareholder/equity section" if not has_shareholder else "OK"))
        checks.append(check("shareholder_data", has_shareholders_data, "Missing shareholder 深圳顺科投资 or 60% stake data" if not has_shareholders_data else "OK"))
        checks.append(check("shareholder_zhang", has_zhang, "Missing shareholder 张建国 with ~25% stake" if not has_zhang else "OK"))
    except Exception as e:
        checks.append(check("shareholder_section", False, str(e)))

    # ---- CHECK 7: Judicial risk section ----
    try:
        has_judicial = "司法" in content or "裁判" in content or "6️⃣" in content or "诉讼" in content
        has_case = "4412" in content or "买卖合同" in content or "328" in content
        has_executed = "执行" in content
        
        checks.append(check("judicial_section", has_judicial, "Missing judicial risk section" if not has_judicial else "OK"))
        checks.append(check("judicial_case_data", has_case, "Missing key case data (case 4412, 买卖合同纠纷, 328万)" if not has_case else "OK"))
    except Exception as e:
        checks.append(check("judicial_section", False, str(e)))

    # ---- CHECK 8: Administrative penalty section ----
    try:
        has_admin = "行政处罚" in content or "7️⃣" in content or "经营风险" in content
        has_penalty = "交通" in content or "超载" in content or "3万" in content or "30000" in content or "2022" in content
        
        checks.append(check("admin_penalty_section", has_admin, "Missing administrative penalty/operational risk section" if not has_admin else "OK"))
        checks.append(check("admin_penalty_data", has_penalty, "Missing 2022 traffic penalty data (超载, 3万元)" if not has_penalty else "OK"))
    except Exception as e:
        checks.append(check("admin_penalty_section", False, str(e)))

    # ---- CHECK 9: Financing section ----
    try:
        has_financing = "融资" in content or "5️⃣" in content or "资本运作" in content
        has_round_a = "A轮" in content and ("1.5亿" in content or "15000" in content or "启明" in content)
        
        checks.append(check("financing_section", has_financing, "Missing financing section" if not has_financing else "OK"))
        checks.append(check("financing_series_a", has_round_a, "Missing Series A data (A轮, 1.5亿, 启明创投)" if not has_round_a else "OK"))
    except Exception as e:
        checks.append(check("financing_section", False, str(e)))

    # ---- CHECK 10: Missing field annotation ----
    try:
        has_missing_annotation = (
            "未检索到" in content or 
            "未披露" in content or 
            "需付费" in content or 
            "疑似需付费" in content or
            "无法确认" in content or
            "不可见" in content
        )
        checks.append(check(
            "missing_field_annotation",
            has_missing_annotation,
            "Report must annotate unavailable fields with '未检索到/未披露/需付费' etc." if not has_missing_annotation else "OK"
        ))
    except Exception as e:
        checks.append(check("missing_field_annotation", False, str(e)))

    # ---- CHECK 11: Risk disclaimer section (⚠️ or 风险提示) ----
    try:
        has_disclaimer = "⚠️" in content or "风险提示" in content or "Important" in content
        has_disclaimer_content = (
            "公开检索" in content or 
            "付费数据库" in content or 
            "非付费" in content
        )
        checks.append(check("risk_disclaimer", has_disclaimer, "Missing risk disclaimer section (⚠️ 风险提示)" if not has_disclaimer else "OK"))
        checks.append(check("disclaimer_content", has_disclaimer_content, "Disclaimer must mention limitations vs paid databases" if not has_disclaimer_content else "OK"))
    except Exception as e:
        checks.append(check("risk_disclaimer", False, str(e)))

    # ---- CHECK 12: Executive summary section ----
    try:
        has_summary = "总结" in content or "Executive Summary" in content or "✅" in content
        has_summary_bullets = bool(re.search(r'[1-5][）)\.]\s*.{5,}', content))
        
        checks.append(check("executive_summary", has_summary, "Missing executive summary / 总结 section" if not has_summary else "OK"))
    except Exception as e:
        checks.append(check("executive_summary", False, str(e)))

    # ---- CHECK 13: Source URLs cited ----
    try:
        has_gov_urls = "gsxt.gov.cn" in content or "court.gov.cn" in content or "jtys.sz.gov.cn" in content
        has_urls = bool(re.search(r'http[s]?://', content))
        
        checks.append(check(
            "source_urls_cited",
            has_urls and has_gov_urls,
            "Report must cite source URLs, including government sources" if not (has_urls and has_gov_urls) else "OK"
        ))
    except Exception as e:
        checks.append(check("source_urls_cited", False, str(e)))

    # ---- CHECK 14: IP / patents section ----
    try:
        has_ip = "知识产权" in content or "8️⃣" in content or "商标" in content or "专利" in content
        has_trademark = "顺达智运" in content or "SHUNDA LOGISTICS" in content or "商标" in content
        has_patent = "专利" in content and ("18" in content or "发明" in content)
        
        checks.append(check("ip_section", has_ip, "Missing IP/intellectual property section" if not has_ip else "OK"))
    except Exception as e:
        checks.append(check("ip_section", False, str(e)))

    # ---- CHECK 15: Subsidiary/investment section ----
    try:
        has_subsidiary = "子公司" in content or "对外投资" in content or "3️⃣" in content
        has_subsidiary_data = "上海顺达" in content or "成都顺达" in content or "北京顺达" in content
        
        checks.append(check("subsidiary_section", has_subsidiary, "Missing subsidiary/investment section" if not has_subsidiary else "OK"))
        checks.append(check("subsidiary_data", has_subsidiary_data, "Missing subsidiary data (上海顺达/成都顺达/北京顺达)" if not has_subsidiary_data else "OK"))
    except Exception as e:
        checks.append(check("subsidiary_section", False, str(e)))

    # ---- CHECK 16: Numbered/emoji section headers indicating proper structure ----
    try:
        emoji_headers = [e for e in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣"] if e in content]
        numbered_headers = len(re.findall(r'###\s+\d+[️⃣]?', content))
        
        has_structured_headers = len(emoji_headers) >= 4 or numbered_headers >= 4 or (
            len(re.findall(r'###.+(信息|股权|司法|风险|融资|投资|知识产权)', content)) >= 4
        )
        checks.append(check(
            "structured_section_headers",
            has_structured_headers,
            f"Report needs structured numbered/emoji section headers (found {len(emoji_headers)} emoji headers, {numbered_headers} numbered headers)" 
            if not has_structured_headers else f"OK: {len(emoji_headers)} emoji headers found"
        ))
    except Exception as e:
        checks.append(check("structured_section_headers", False, str(e)))

    # ---- Calculate score ----
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total if total > 0 else 0.0
    
    # Overall pass: need at least 75% of checks
    overall_passed = score >= 0.75
    
    return overall_passed, round(score, 3), checks

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        passed, score, checks = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_runtime_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0)
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))