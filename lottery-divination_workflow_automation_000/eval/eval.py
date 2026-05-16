#!/usr/bin/env python3
"""
Evaluation script for the lottery divination task.
Checks that the agent correctly:
1. Ran divination.py with type=dlt and timestamp=2026-07-18-20
2. Used lottery.format field from the JSON output
3. Included all required sections (本卦/互卦/变卦 hexagram info)
4. Included the mandatory disclaimer
5. Output is written to prediction_report.txt
"""
import sys
import json
import subprocess
import re
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    score = 0.0

    # ── Get ground truth from divination.py ─────────────────────────────────
    try:
        result = subprocess.run(
            ["python3", str(ws / "scripts" / "divination.py"), "dlt", "2026-07-18-20"],
            capture_output=True, text=True, timeout=15
        )
        ground_truth = json.loads(result.stdout)
        div = ground_truth["divination"]
        lottery = ground_truth["lottery"]
        gt_format = lottery["format"]          # e.g. "前区: 03 11 ..."
        gt_main = div["main_hexagram"]["name"]
        gt_mutual = div["mutual_hexagram"]["name"]
        gt_changed = div["changed_hexagram"]["name"]
        gt_main_sym = div["main_hexagram"]["symbol"]
        gt_mutual_sym = div["mutual_hexagram"]["symbol"]
        gt_changed_sym = div["changed_hexagram"]["symbol"]
        gt_moving_yao = div["changed_hexagram"]["moving_yao"]
        gt_year_num = div["year_num"]
        gt_month_num = div["month_num"]
        gt_day_num = div["day_num"]
        gt_hour_num = div["hour_num"]
    except Exception as e:
        checks.append({
            "name": "ground_truth_generation",
            "passed": False,
            "detail": f"Failed to generate ground truth from divination.py: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "ground_truth_generation",
        "passed": True,
        "detail": f"Ground truth generated. Lottery format: {gt_format}"
    })

    # ── Find the output file ──────────────────────────────────────────────────
    report_files = list(ws.rglob("prediction_report.txt"))
    if not report_files:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "prediction_report.txt not found anywhere in workspace"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Could not read prediction_report.txt: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found at {report_path}"
    })

    # ── Check 1: lottery type is 大乐透 (not 双色球) ──────────────────────────
    is_dlt = "大乐透" in content or "dlt" in content.lower() or ("前区" in content and "后区" in content)
    is_ssq = "双色球" in content and "红球" in content and "蓝球" in content and "大乐透" not in content
    dlt_check = is_dlt and not is_ssq
    checks.append({
        "name": "correct_lottery_type_dlt",
        "passed": dlt_check,
        "detail": f"Report contains 大乐透/前区/后区: {is_dlt}, wrongly contains 双色球-only format: {is_ssq}"
    })
    if dlt_check:
        score += 0.15

    # ── Check 2: lottery.format content is present verbatim ──────────────────
    # The format string contains numbers like "前区: 03 11 ..." — check key numbers
    # We extract the numbers from gt_format and verify they appear in the report
    front_match = re.search(r"前区[:：]\s*([\d\s]+)", gt_format)
    back_match = re.search(r"后区[:：]\s*([\d\s]+)", gt_format)

    format_present = False
    if front_match and back_match:
        front_nums = front_match.group(1).strip()
        back_nums = back_match.group(1).strip()
        # Check all individual numbers appear in report
        all_front_ok = all(num in content for num in front_nums.split())
        all_back_ok = all(num in content for num in back_nums.split())
        format_present = all_front_ok and all_back_ok

    checks.append({
        "name": "lottery_format_numbers_present",
        "passed": format_present,
        "detail": (
            f"Expected numbers from lottery.format ({gt_format}) "
            f"{'found' if format_present else 'NOT found'} in report"
        )
    })
    if format_present:
        score += 0.25

    # ── Check 3: 本卦 (main hexagram) name and symbol present ─────────────────
    main_hex_ok = gt_main in content and gt_main_sym in content
    checks.append({
        "name": "main_hexagram_present",
        "passed": main_hex_ok,
        "detail": f"本卦 name '{gt_main}' and symbol '{gt_main_sym}' in report: {main_hex_ok}"
    })
    if main_hex_ok:
        score += 0.10

    # ── Check 4: 互卦 (mutual hexagram) present ───────────────────────────────
    mutual_hex_ok = gt_mutual in content and gt_mutual_sym in content
    checks.append({
        "name": "mutual_hexagram_present",
        "passed": mutual_hex_ok,
        "detail": f"互卦 name '{gt_mutual}' and symbol '{gt_mutual_sym}' in report: {mutual_hex_ok}"
    })
    if mutual_hex_ok:
        score += 0.10

    # ── Check 5: 变卦 (changed hexagram) + 动爻 present ──────────────────────
    changed_hex_ok = gt_changed in content and gt_changed_sym in content and gt_moving_yao in content
    checks.append({
        "name": "changed_hexagram_with_moving_yao",
        "passed": changed_hex_ok,
        "detail": (
            f"变卦 name '{gt_changed}', symbol '{gt_changed_sym}', moving_yao '{gt_moving_yao}' "
            f"in report: {changed_hex_ok}"
        )
    })
    if changed_hex_ok:
        score += 0.10

    # ── Check 6: divination basis numbers (year/month/day/hour) ───────────────
    nums_ok = (
        str(gt_year_num) in content and
        str(gt_month_num) in content and
        str(gt_day_num) in content and
        str(gt_hour_num) in content
    )
    checks.append({
        "name": "divination_basis_numbers",
        "passed": nums_ok,
        "detail": (
            f"Year_num={gt_year_num}, month_num={gt_month_num}, "
            f"day_num={gt_day_num}, hour_num={gt_hour_num} all in report: {nums_ok}"
        )
    })
    if nums_ok:
        score += 0.10

    # ── Check 7: mandatory disclaimer ─────────────────────────────────────────
    disclaimer_keywords = ["免责声明", "娱乐", "随机概率", "切勿沉迷"]
    disclaimer_ok = all(kw in content for kw in disclaimer_keywords)
    checks.append({
        "name": "mandatory_disclaimer_present",
        "passed": disclaimer_ok,
        "detail": (
            f"Disclaimer keywords {disclaimer_keywords} "
            f"{'all found' if disclaimer_ok else 'some missing'} in report"
        )
    })
    if disclaimer_ok:
        score += 0.10

    # ── Check 8: 2026-07-18 (target date) referenced ─────────────────────────
    date_ok = ("2026" in content) and (("07" in content or "7" in content))
    checks.append({
        "name": "target_date_referenced",
        "passed": date_ok,
        "detail": f"Target year 2026 and month 07 referenced in report: {date_ok}"
    })
    if date_ok:
        score += 0.05

    # ── Check 9: amount suggestion present ────────────────────────────────────
    amount_ok = any(hint in content for hint in ["10", "20", "娱乐", "量力而行", "10～20", "10~20"])
    checks.append({
        "name": "amount_or_entertainment_hint",
        "passed": amount_ok,
        "detail": f"Amount/entertainment hint present: {amount_ok}"
    })
    if amount_ok:
        score += 0.05

    # ── Overall pass criterion ─────────────────────────────────────────────────
    critical_passed = (
        dlt_check and
        format_present and
        main_hex_ok and
        disclaimer_ok
    )

    return {
        "passed": critical_passed,
        "score": round(min(score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                       "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))