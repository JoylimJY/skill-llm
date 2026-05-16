import sys
import json
import re
from pathlib import Path

def find_report_file(workspace: str) -> Path | None:
    """Search for the required report markdown file."""
    ws = Path(workspace)
    # Try exact name first
    candidates = list(ws.rglob("000858_report.md")) + list(ws.rglob("五粮液_report.md")) + \
                 list(ws.rglob("000858*.md")) + list(ws.rglob("五粮液*.md")) + \
                 list(ws.rglob("wuliangye*.md"))
    # Also accept any .md file in output/ that mentions 五粮液
    output_dir = ws / "output"
    if output_dir.exists():
        for f in output_dir.glob("*.md"):
            candidates.append(f)
    # Deduplicate
    seen = set()
    unique = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique[0] if unique else None

def run_eval(workspace: str):
    checks = []

    # ── locate the output file ───────────────────────────────────────
    report_path = find_report_file(workspace)
    file_found = report_path is not None and report_path.exists()

    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found: {report_path}" if file_found else "No report .md file found in workspace"
    })

    if not file_found:
        return checks, False

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return checks, False

    checks.append({"name": "file_readable", "passed": True, "detail": f"Read {len(content)} chars"})

    # ── check 1: top-level heading matches required format ───────────
    # Must be: ## 五粮液 财报速读
    heading_ok = bool(re.search(r"##\s+五粮液\s+财报速读", content))
    checks.append({
        "name": "heading_format_correct",
        "passed": heading_ok,
        "detail": "Found '## 五粮液 财报速读'" if heading_ok else "Missing or malformed heading '## 五粮液 财报速读'"
    })

    # ── check 2: 核心数据 section with correct table headers ─────────
    # Must have: | 指标 | Q3 | Q2 | Q1 | 全年 |
    table_header_ok = bool(re.search(r"\|\s*指标\s*\|\s*Q3\s*\|\s*Q2\s*\|\s*Q1\s*\|\s*全年\s*\|", content))
    checks.append({
        "name": "table_header_correct",
        "passed": table_header_ok,
        "detail": "Table header '| 指标 | Q3 | Q2 | Q1 | 全年 |' found" if table_header_ok
                  else "Missing required table header with columns: 指标, Q3, Q2, Q1, 全年"
    })

    # ── check 3: 营收 row present with values in 亿 ──────────────────
    revenue_row_ok = bool(re.search(r"\|\s*营收\s*\|.*亿.*\|.*亿.*\|.*亿.*\|.*亿.*\|", content))
    checks.append({
        "name": "revenue_row_present",
        "passed": revenue_row_ok,
        "detail": "营收 row with 亿 values found" if revenue_row_ok else "营收 row missing or values not in 亿 format"
    })

    # ── check 4: 净利 row present with values in 亿 ──────────────────
    net_profit_row_ok = bool(re.search(r"\|\s*净利\s*\|.*亿.*\|.*亿.*\|.*亿.*\|.*亿.*\|", content))
    checks.append({
        "name": "net_profit_row_present",
        "passed": net_profit_row_ok,
        "detail": "净利 row with 亿 values found" if net_profit_row_ok else "净利 row missing or values not in 亿 format"
    })

    # ── check 5: ROE row present with % values ───────────────────────
    roe_row_ok = bool(re.search(r"\|\s*ROE\s*\|.*%.*\|.*%.*\|.*%.*\|.*%.*\|", content))
    checks.append({
        "name": "roe_row_present",
        "passed": roe_row_ok,
        "detail": "ROE row with % values found" if roe_row_ok else "ROE row missing or values not in % format"
    })

    # ── check 6: 趋势判断 section present ────────────────────────────
    trend_section_ok = bool(re.search(r"###\s*趋势判断", content))
    checks.append({
        "name": "trend_section_present",
        "passed": trend_section_ok,
        "detail": "### 趋势判断 section found" if trend_section_ok else "Missing ### 趋势判断 section"
    })

    # ── check 7: 增长性 uses allowed vocabulary ───────────────────────
    # Must be one of: 加速 / 稳定 / 减速
    growth_match = re.search(r"增长性\s*[:：]\s*[\[【]?(加速|稳定|减速)", content)
    growth_vocab_ok = bool(growth_match)
    growth_value = growth_match.group(1) if growth_match else "NOT FOUND"
    checks.append({
        "name": "growth_trend_valid_vocab",
        "passed": growth_vocab_ok,
        "detail": f"增长性 value: '{growth_value}'" if growth_vocab_ok
                  else "增长性 missing or uses invalid value (must be one of: 加速/稳定/减速)"
    })

    # ── check 8: 增长性 value is correct given data ──────────────────
    # Revenue YoY: Q1=12.5%, Q2=14.2%, Q3=15.8% → accelerating → 加速
    if growth_vocab_ok:
        growth_correct = growth_value == "加速"
        checks.append({
            "name": "growth_trend_correct_value",
            "passed": growth_correct,
            "detail": f"增长性='加速' is correct (rev growth Q1→Q3: 12.5%→14.2%→15.8% is accelerating)" 
                      if growth_correct else 
                      f"增长性='{growth_value}' is WRONG; data shows accelerating revenue (should be '加速')"
        })
    else:
        checks.append({
            "name": "growth_trend_correct_value",
            "passed": False,
            "detail": "Cannot verify correctness; 增长性 not found with valid vocab"
        })

    # ── check 9: 盈利质量 uses allowed vocabulary ─────────────────────
    # Must be one of: 优 / 良 / 中 / 差
    quality_match = re.search(r"盈利质量\s*[:：]\s*[\[【]?(优|良|中|差)", content)
    quality_vocab_ok = bool(quality_match)
    quality_value = quality_match.group(1) if quality_match else "NOT FOUND"
    checks.append({
        "name": "profit_quality_valid_vocab",
        "passed": quality_vocab_ok,
        "detail": f"盈利质量 value: '{quality_value}'" if quality_vocab_ok
                  else "盈利质量 missing or uses invalid value (must be one of: 优/良/中/差)"
    })

    # ── check 10: 盈利质量 correct given thresholds ───────────────────
    # ROE Q3=19.8% (>15% healthy), OCF/net=1.12 (>0.8 healthy), net margin Q3=32.9% (>10% healthy)
    # All KPIs are healthy → should be 优 or 良
    if quality_vocab_ok:
        quality_correct = quality_value in ("优", "良")
        checks.append({
            "name": "profit_quality_correct_value",
            "passed": quality_correct,
            "detail": f"盈利质量='{quality_value}' is correct (ROE 19.8%>15%, OCF/净利 1.12>0.8, 净利率 32.9%>10%)"
                      if quality_correct else
                      f"盈利质量='{quality_value}' is WRONG; all KPIs are above healthy thresholds (should be 优 or 良)"
        })
    else:
        checks.append({
            "name": "profit_quality_correct_value",
            "passed": False,
            "detail": "Cannot verify correctness; 盈利质量 not found"
        })

    # ── check 11: 风险点 section present and non-empty ───────────────
    risk_match = re.search(r"风险点\s*[:：]\s*(.{5,})", content)
    risk_ok = bool(risk_match)
    checks.append({
        "name": "risk_point_present_and_substantive",
        "passed": risk_ok,
        "detail": f"风险点 content: {risk_match.group(1)[:80] if risk_match else 'N/A'}" if risk_ok
                  else "风险点 missing or has fewer than 5 characters of content"
    })

    # ── check 12: 投资观点 section present ───────────────────────────
    opinion_section_ok = bool(re.search(r"###\s*投资观点", content))
    checks.append({
        "name": "investment_opinion_section_present",
        "passed": opinion_section_ok,
        "detail": "### 投资观点 section found" if opinion_section_ok
                  else "Missing ### 投资观点 section"
    })

    # ── check 13: correct stock data used (000858, not 600519) ───────
    # The report should NOT be about 贵州茅台 (600519)
    not_wrong_stock = not bool(re.search(r"贵州茅台|600519", content))
    # The report SHOULD mention 五粮液
    correct_stock = bool(re.search(r"五粮液|000858", content))
    stock_ok = correct_stock and not_wrong_stock
    checks.append({
        "name": "correct_stock_analyzed",
        "passed": stock_ok,
        "detail": "Report is about 五粮液 (000858) and not 贵州茅台 (600519)" if stock_ok
                  else f"Wrong stock: 五粮液 mentioned={correct_stock}, 贵州茅台 mentioned={not not_wrong_stock}"
    })

    # ── check 14: debt ratio mentioned and correct assessment ─────────
    # debt_ratio = 28.3% → <60% → healthy, not a red flag
    debt_ok = bool(re.search(r"资产负债率|负债率|28\.?\d*%?", content))
    checks.append({
        "name": "debt_ratio_referenced",
        "passed": debt_ok,
        "detail": "Asset-liability ratio (资产负债率 28.3%) referenced" if debt_ok
                  else "No mention of 资产负债率 or its value"
    })

    # ── check 15: OCF/net profit ratio mentioned ─────────────────────
    # 1.12 → well above 0.8 threshold → healthy
    ocf_ok = bool(re.search(r"经营现金流|现金流.*净利|ocf|1\.1[0-9]", content, re.IGNORECASE))
    checks.append({
        "name": "ocf_net_profit_ratio_referenced",
        "passed": ocf_ok,
        "detail": "OCF/净利润 ratio (1.12) referenced" if ocf_ok
                  else "No mention of 经营现金流/净利润 ratio (should be ~1.12)"
    })

    # ── compute score ────────────────────────────────────────────────
    # Weight critical checks more heavily
    weights = {
        "output_file_exists": 1.0,
        "file_readable": 0.5,
        "heading_format_correct": 1.5,
        "table_header_correct": 1.5,
        "revenue_row_present": 1.0,
        "net_profit_row_present": 1.0,
        "roe_row_present": 1.0,
        "trend_section_present": 1.0,
        "growth_trend_valid_vocab": 1.5,
        "growth_trend_correct_value": 2.0,
        "profit_quality_valid_vocab": 1.5,
        "profit_quality_correct_value": 2.0,
        "risk_point_present_and_substantive": 1.0,
        "investment_opinion_section_present": 1.0,
        "correct_stock_analyzed": 2.0,
        "debt_ratio_referenced": 0.5,
        "ocf_net_profit_ratio_referenced": 0.5,
    }

    total_weight = sum(weights.get(c["name"], 1.0) for c in checks)
    earned_weight = sum(weights.get(c["name"], 1.0) for c in checks if c["passed"])
    score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0

    # Must pass critical checks to be considered overall passing
    critical_checks = [
        "output_file_exists",
        "heading_format_correct",
        "table_header_correct",
        "growth_trend_valid_vocab",
        "growth_trend_correct_value",
        "profit_quality_valid_vocab",
        "profit_quality_correct_value",
        "correct_stock_analyzed",
    ]
    critical_pass = all(
        next((c["passed"] for c in checks if c["name"] == name), False)
        for name in critical_checks
    )

    passed = critical_pass and score >= 0.70

    return checks, passed, score


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    try:
        checks, passed, score = run_eval(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }))
        sys.exit(1)

    print(json.dumps({"passed": passed, "score": score, "checks": checks},
                     ensure_ascii=False, indent=2))