#!/usr/bin/env python3
"""
Evaluation script for buddy-bills May 2025 closing task.
Usage: python eval_script.py /workspace
"""

import sys
import json
import re
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

def load_yaml_safe(path: Path):
    """Load a YAML file, stripping markdown-style comment/header lines first."""
    if not path.exists():
        return None
    raw = path.read_text(encoding="utf-8")
    if yaml is None:
        return raw  # fallback: return raw string
    # Strip lines starting with # that aren't valid YAML comments embedded in data
    try:
        return yaml.safe_load(raw)
    except Exception:
        # Try stripping comment lines and re-parse
        cleaned = "\n".join(
            line for line in raw.splitlines()
            if not (line.strip().startswith("#") or line.strip().startswith("##") or line.strip().startswith("###"))
        )
        try:
            return yaml.safe_load(cleaned)
        except Exception:
            return None

def read_raw(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

checks = []

def add_check(name: str, passed: bool, detail: str):
    checks.append({"name": name, "passed": passed, "detail": detail})

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    fr = workspace / "finance-records"

    # ════════════════════════════════════════════════════════════
    # CHECK 1: 餐饮/2025/05.yaml — two entries (外卖 62 + 咖啡 38)
    # ════════════════════════════════════════════════════════════
    canteen_may = fr / "餐饮/2025/05.yaml"
    try:
        raw = read_raw(canteen_may)
        data = load_yaml_safe(canteen_may)
        # Look for 62 and 38 in raw text as fallback
        has_62 = "62" in raw
        has_38 = "38" in raw
        has_waimai = "外卖" in raw or "美团" in raw
        has_ruixin = "瑞幸" in raw or "咖啡" in raw

        total_ok = False
        if data and isinstance(data, dict):
            total = data.get("月度汇总", {}).get("总计", 0)
            try:
                total_ok = abs(float(total) - 100.0) < 0.01
            except Exception:
                pass
        # fallback: search raw
        if not total_ok:
            total_ok = "100" in raw

        entry_ok = has_62 and has_38 and has_waimai and has_ruixin
        passed = entry_ok and total_ok
        add_check(
            "餐饮/2025/05.yaml — two entries (62+38=100)",
            passed,
            f"has_62={has_62}, has_38={has_38}, has_waimai={has_waimai}, has_ruixin={has_ruixin}, total_100={total_ok}"
        )
    except Exception as e:
        add_check("餐饮/2025/05.yaml — two entries (62+38=100)", False, f"Exception: {e}")

    # ════════════════════════════════════════════════════════════
    # CHECK 2: 生活购物/2025/05.yaml — 218 元
    # ════════════════════════════════════════════════════════════
    shopping_may = fr / "生活购物/2025/05.yaml"
    try:
        raw = read_raw(shopping_may)
        has_218 = "218" in raw
        has_jd = "京东" in raw
        add_check(
            "生活购物/2025/05.yaml — 218元 from 京东",
            has_218 and has_jd,
            f"has_218={has_218}, has_jd={has_jd}"
        )
    except Exception as e:
        add_check("生活购物/2025/05.yaml — 218元 from 京东", False, f"Exception: {e}")

    # ════════════════════════════════════════════════════════════
    # CHECK 3: 医疗/2025/05.yaml — 280 元疫苗
    # ════════════════════════════════════════════════════════════
    medical_may = fr / "医疗/2025/05.yaml"
    try:
        raw = read_raw(medical_may)
        has_280 = "280" in raw
        has_vacc = "疫苗" in raw or "医院" in raw
        add_check(
            "医疗/2025/05.yaml — 280元疫苗",
            has_280 and has_vacc,
            f"has_280={has_280}, has_vacc={has_vacc}"
        )
    except Exception as e:
        add_check("医疗/2025/05.yaml — 280元疫苗", False, f"Exception: {e}")

    # ════════════════════════════════════════════════════════════
    # CHECK 4: 家庭转账/2025/05.yaml — 2000 元
    # ════════════════════════════════════════════════════════════
    transfer_may = fr / "家庭转账/2025/05.yaml"
    try:
        raw = read_raw(transfer_may)
        has_2000 = "2000" in raw
        add_check(
            "家庭转账/2025/05.yaml — 2000元",
            has_2000,
            f"has_2000={has_2000}"
        )
    except Exception as e:
        add_check("家庭转账/2025/05.yaml — 2000元", False, f"Exception: {e}")

    # ════════════════════════════════════════════════════════════
    # CHECK 5: 房贷/2025/05.yaml — auto-ingested 8500 元 on day 10
    # ════════════════════════════════════════════════════════════
    mortgage_may = fr / "房贷/2025/05.yaml"
    try:
        raw = read_raw(mortgage_may)
        has_8500 = "8500" in raw
        has_date = "2025-05-10" in raw or "05-10" in raw or "5月10" in raw
        add_check(
            "房贷/2025/05.yaml — auto 8500元 on 2025-05-10",
            has_8500 and has_date,
            f"has_8500={has_8500}, has_date_10={has_date}"
        )
    except Exception as e:
        add_check("房贷/2025/05.yaml — auto 8500元 on 2025-05-10", False, f"Exception: {e}")

    # ════════════════════════════════════════════════════════════
    # CHECK 6: 医保/2025/05.yaml — auto-ingested 650 元 on day 15
    # ════════════════════════════════════════════════════════════
    insur_may = fr / "医保/2025/05.yaml"
    try:
        raw = read_raw(insur_may)
        has_650 = "650" in raw
        has_date15 = "2025-05-15" in raw or "05-15" in raw or "5月15" in raw
        add_check(
            "医保/2025/05.yaml — auto 650元 on 2025-05-15",
            has_650 and has_date15,
            f"has_650={has_650}, has_date_15={has_date15}"
        )
    except Exception as e:
        add_check("医保/2025/05.yaml — auto 650元 on 2025-05-15", False, f"Exception: {e}")

    # ════════════════════════════════════════════════════════════
    # CHECK 7: 收入/2025/05.yaml — 18000 元工资 on day 25
    # ════════════════════════════════════════════════════════════
    income_may = fr / "收入/2025/05.yaml"
    try:
        raw = read_raw(income_may)
        has_18k = "18000" in raw
        has_date25 = "2025-05-25" in raw or "05-25" in raw or "5月25" in raw
        add_check(
            "收入/2025/05.yaml — 18000元工资 on 2025-05-25",
            has_18k and has_date25,
            f"has_18000={has_18k}, has_date_25={has_date25}"
        )
    except Exception as e:
        add_check("收入/2025/05.yaml — 18000元工资 on 2025-05-25", False, f"Exception: {e}")

    # ════════════════════════════════════════════════════════════
    # CHECK 8: Root index.yaml updated with 2025/05 entry
    # ════════════════════════════════════════════════════════════
    root_idx = fr / "index.yaml"
    try:
        raw = read_raw(root_idx)
        # Must have both 2025/04 (preserved) and 2025/05 (new)
        has_apr = "04" in raw and "3680" in raw  # April 结余
        has_may = "05" in raw
        # May 总支出: 8500+650+100+218+280+2000 = 11748
        has_may_total = any(x in raw for x in ["11748", "11,748"])
        # May 收入 18000
        has_may_income = "18000" in raw
        add_check(
            "index.yaml — 2025/05 entry present with correct figures",
            has_apr and has_may and has_may_total and has_may_income,
            f"has_apr_preserved={has_apr}, has_may={has_may}, has_may_total_11748={has_may_total}, has_income_18000={has_may_income}"
        )
    except Exception as e:
        add_check("index.yaml — 2025/05 entry present with correct figures", False, f"Exception: {e}")

    # ════════════════════════════════════════════════════════════
    # CHECK 9: Category index.yaml files updated (餐饮, 房贷, 医保, 收入)
    # ════════════════════════════════════════════════════════════
    cat_indexes_ok = True
    cat_idx_details = []
    for cat, expected_may_total in [
        ("餐饮", "100"),
        ("房贷", "8500"),
        ("医保", "650"),
        ("收入", "18000"),
        ("生活购物", "218"),
        ("医疗", "280"),
        ("家庭转账", "2000"),
    ]:
        idx_path = fr / cat / "index.yaml"
        raw = read_raw(idx_path)
        has_05 = "05" in raw
        has_val = expected_may_total in raw
        ok = has_05 and has_val
        if not ok:
            cat_indexes_ok = False
        cat_idx_details.append(f"{cat}(has_05={has_05},has_{expected_may_total}={has_val})")

    add_check(
        "Category index.yaml files — all updated with May 2025 data",
        cat_indexes_ok,
        "; ".join(cat_idx_details)
    )

    # ════════════════════════════════════════════════════════════
    # CHECK 10: summary/2025/05.yaml exists with required sections
    # ════════════════════════════════════════════════════════════
    summary_may = fr / "summary/2025/05.yaml"
    try:
        raw = read_raw(summary_may)
        exists = len(raw) > 100

        # Required section markers from the proprietary schema
        sec1 = "收支总览" in raw
        sec2 = "每周总结" in raw
        sec3 = "支出明细汇总" in raw
        sec4 = "统计分析" in raw
        sec5 = "环比对比" in raw or "上月结余" in raw

        # Financial correctness
        has_income = "18000" in raw
        # Total expenditure: 8500+650+100+218+280+2000 = 11748
        has_total_exp = any(x in raw for x in ["11748", "11,748"])
        # 结余: 18000 - 11748 = 6252
        has_surplus = any(x in raw for x in ["6252", "6,252"])
        # 储蓄率 must appear
        has_savings_rate = "储蓄率" in raw

        # 上月结余 should reference April's 3680
        has_prev_month = "3680" in raw

        all_sections = sec1 and sec2 and sec3 and sec4 and sec5
        financials_ok = has_income and has_total_exp and has_surplus and has_savings_rate

        add_check(
            "summary/2025/05.yaml — all 6 sections present",
            exists and all_sections,
            f"exists={exists}, sec1={sec1}, sec2={sec2}, sec3={sec3}, sec4={sec4}, sec5={sec5}"
        )
        add_check(
            "summary/2025/05.yaml — financial figures correct (income/expense/surplus/savings_rate)",
            exists and financials_ok,
            f"has_income_18000={has_income}, has_total_exp_11748={has_total_exp}, has_surplus_6252={has_surplus}, has_savings_rate={has_savings_rate}"
        )
        add_check(
            "summary/2025/05.yaml — 环比对比 references April 结余 3680",
            exists and has_prev_month,
            f"has_apr_3680={has_prev_month}"
        )
    except Exception as e:
        add_check("summary/2025/05.yaml — all 6 sections present", False, f"Exception: {e}")
        add_check("summary/2025/05.yaml — financial figures correct", False, f"Exception: {e}")
        add_check("summary/2025/05.yaml — 环比对比 references April 结余 3680", False, f"Exception: {e}")

    # ════════════════════════════════════════════════════════════
    # CHECK 11: April data in index.yaml is PRESERVED (not overwritten)
    # ════════════════════════════════════════════════════════════
    try:
        raw = read_raw(root_idx)
        apr_preserved = "3680" in raw and "14320" in raw
        add_check(
            "index.yaml — April 2025 data preserved (not overwritten)",
            apr_preserved,
            f"has_apr_surplus_3680={apr_preserved}"
        )
    except Exception as e:
        add_check("index.yaml — April 2025 data preserved (not overwritten)", False, f"Exception: {e}")

    # ════════════════════════════════════════════════════════════
    # Scoring
    # ════════════════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = passed_count == total

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()