import sys
import json
import math
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score_parts = []


def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    score_parts.append((passed, weight))


# ── Load reference values ────────────────────────────────────────────────────
try:
    ref = json.loads((workspace / "data/cache/reference_values.json").read_text())
    REF_MA20       = ref["ma20_last"]
    REF_CLOSE      = ref["latest_close"]
    REF_NET_MARGIN = ref["latest_net_margin"]
    REF_SECTOR_CNT = ref["sector_stock_count"]
    REF_MEDIAN_PE  = ref["sector_median_pe"]
    REF_CLOSES     = ref["closes"]
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0,
                      "checks": [{"name": "reference_load", "passed": False,
                                  "detail": str(e)}]}))
    sys.exit(0)

# ── Locate the output report ─────────────────────────────────────────────────
report_candidates = list(workspace.rglob("analysis_report.json"))
if not report_candidates:
    add_check("output_file_exists", False, "analysis_report.json not found anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

report_path = report_candidates[0]
add_check("output_file_exists", True, f"Found at {report_path.relative_to(workspace)}")

# ── Parse the report ─────────────────────────────────────────────────────────
try:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    add_check("report_valid_json", True, "JSON parsed successfully")
except Exception as e:
    add_check("report_valid_json", False, f"JSON parse error: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Check 1: 20-day MA of closing price (qfq-adjusted) ───────────────────────
# The agent must have used adjust="qfq"; if they used raw, MA will differ by ~5%
try:
    reported_ma20 = float(report.get("ma20_close") or report.get("ma20") or
                          report.get("moving_average_20") or report.get("ma_20_close") or
                          report["ma20_last_close"])
    tolerance = 0.01  # 1% tolerance
    rel_err = abs(reported_ma20 - REF_MA20) / REF_MA20
    if rel_err <= tolerance:
        add_check("ma20_qfq_correct", True,
                  f"MA20={reported_ma20:.4f}, expected≈{REF_MA20:.4f} (err={rel_err:.4%})", weight=2.0)
    else:
        # Check if they used raw data (error ~5%) - that means wrong adjust param
        import numpy as np
        raw_closes = [round(c * 1.05, 2) for c in REF_CLOSES]
        raw_ma20 = round(float(sum(raw_closes[-20:]) / 20), 4)
        raw_rel_err = abs(reported_ma20 - raw_ma20) / raw_ma20
        if raw_rel_err <= tolerance:
            add_check("ma20_qfq_correct", False,
                      f"MA20={reported_ma20:.4f} matches RAW data (adjust=''), not QFQ-adjusted. "
                      f"Must use adjust='qfq'. Expected≈{REF_MA20:.4f}", weight=2.0)
        else:
            add_check("ma20_qfq_correct", False,
                      f"MA20={reported_ma20:.4f}, expected≈{REF_MA20:.4f} (err={rel_err:.4%})", weight=2.0)
except (KeyError, TypeError, ValueError) as e:
    add_check("ma20_qfq_correct", False, f"Could not find/parse MA20 field: {e}", weight=2.0)

# ── Check 2: Latest closing price matches qfq data ────────────────────────────
try:
    reported_close = float(report.get("latest_close") or report.get("latest_close_price") or
                           report.get("close_price") or report.get("last_close"))
    tol = 0.01
    rel_err = abs(reported_close - REF_CLOSE) / REF_CLOSE
    passed = rel_err <= tol
    add_check("latest_close_qfq", passed,
              f"latest_close={reported_close:.2f}, expected≈{REF_CLOSE:.2f} (err={rel_err:.4%})",
              weight=1.0)
except (KeyError, TypeError, ValueError) as e:
    add_check("latest_close_qfq", False, f"Could not find/parse latest_close field: {e}", weight=1.0)

# ── Check 3: Net profit margin from financial indicator ───────────────────────
try:
    reported_npm = float(report.get("net_profit_margin") or report.get("net_margin") or
                         report.get("净利率") or report.get("latest_net_margin"))
    tol = 0.5  # allow 0.5 percentage point tolerance
    passed = abs(reported_npm - REF_NET_MARGIN) <= tol
    add_check("net_profit_margin_correct", passed,
              f"net_margin={reported_npm}, expected={REF_NET_MARGIN} (diff={abs(reported_npm-REF_NET_MARGIN):.2f})",
              weight=2.0)
except (KeyError, TypeError, ValueError) as e:
    add_check("net_profit_margin_correct", False,
              f"Could not find/parse net_profit_margin field: {e}", weight=2.0)

# ── Check 4: Sector constituent count ────────────────────────────────────────
try:
    reported_cnt = int(report.get("sector_stock_count") or report.get("baijiu_stock_count") or
                       report.get("industry_count") or report.get("sector_count"))
    passed = reported_cnt == REF_SECTOR_CNT
    add_check("sector_count_correct", passed,
              f"sector_count={reported_cnt}, expected={REF_SECTOR_CNT}", weight=1.5)
except (KeyError, TypeError, ValueError) as e:
    add_check("sector_count_correct", False,
              f"Could not find/parse sector_stock_count field: {e}", weight=1.5)

# ── Check 5: Sector median P/E ratio ─────────────────────────────────────────
try:
    reported_pe = float(report.get("sector_median_pe") or report.get("median_pe") or
                        report.get("industry_median_pe") or report.get("baijiu_median_pe"))
    tol = 0.5
    passed = abs(reported_pe - REF_MEDIAN_PE) <= tol
    add_check("sector_median_pe_correct", passed,
              f"median_pe={reported_pe:.2f}, expected={REF_MEDIAN_PE:.2f}", weight=1.5)
except (KeyError, TypeError, ValueError) as e:
    add_check("sector_median_pe_correct", False,
              f"Could not find/parse sector_median_pe field: {e}", weight=1.5)

# ── Check 6: Source script uses correct proprietary API calls ─────────────────
# Look for a Python script the agent wrote
py_candidates = [p for p in workspace.rglob("*.py")
                 if p.stat().st_size > 200
                 and "deprecated" not in str(p)
                 and "wrong_api" not in str(p)
                 and "mock_packages" not in str(p)
                 and "tushare_helper" not in str(p)
                 and "old_analysis" not in str(p)]

script_text = ""
for pc in py_candidates:
    try:
        t = pc.read_text(encoding="utf-8", errors="ignore")
        if "stock_zh_a_hist" in t or "stock_financial_analysis_indicator" in t:
            script_text += t + "\n"
    except Exception:
        pass

if not script_text:
    add_check("uses_akshare_hist_api", False,
              "No Python script found containing akshare API calls", weight=2.0)
    add_check("uses_qfq_adjust_param", False,
              "Cannot verify adjust param - no script found", weight=2.5)
    add_check("uses_financial_indicator_api", False,
              "No script found", weight=1.5)
    add_check("uses_board_industry_cons_api", False,
              "No script found", weight=1.5)
else:
    # 6a: uses stock_zh_a_hist
    passed = "stock_zh_a_hist" in script_text
    add_check("uses_akshare_hist_api", passed,
              "Found stock_zh_a_hist call" if passed else "Missing stock_zh_a_hist", weight=2.0)

    # 6b: uses adjust="qfq" (the proprietary trap - not "hfq", not "")
    import re
    qfq_pattern = re.search(r'adjust\s*=\s*["\']qfq["\']', script_text)
    passed = bool(qfq_pattern)
    add_check("uses_qfq_adjust_param", passed,
              'Found adjust="qfq"' if passed else
              'Missing adjust="qfq" - agent may have used wrong adjust value or omitted it',
              weight=2.5)

    # 6c: uses stock_financial_analysis_indicator
    passed = "stock_financial_analysis_indicator" in script_text
    add_check("uses_financial_indicator_api", passed,
              "Found stock_financial_analysis_indicator call" if passed else
              "Missing stock_financial_analysis_indicator", weight=1.5)

    # 6d: uses stock_board_industry_cons_em with 白酒
    board_pattern = re.search(r'stock_board_industry_cons_em', script_text)
    baijiu_pattern = re.search(r'白酒', script_text)
    passed = bool(board_pattern) and bool(baijiu_pattern)
    add_check("uses_board_industry_cons_api", passed,
              "Found stock_board_industry_cons_em with 白酒" if passed else
              f"board_api={'found' if board_pattern else 'missing'}, "
              f"白酒={'found' if baijiu_pattern else 'missing'}",
              weight=1.5)

# ── Final score ───────────────────────────────────────────────────────────────
total_weight = sum(w for _, w in score_parts)
earned_weight = sum(w for p, w in score_parts if p)
score = round(earned_weight / total_weight, 4) if total_weight > 0 else 0.0
passed_overall = score >= 0.75 and checks[0]["passed"]  # must have file

print(json.dumps({
    "passed": passed_overall,
    "score": score,
    "checks": checks
}, ensure_ascii=False, indent=2))