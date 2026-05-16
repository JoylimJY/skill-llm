import sys
import json
import subprocess
from pathlib import Path
from datetime import date

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── 1. Find the output JSON file ──────────────────────────────────────────
    # Agent should produce window_report.json (as specified in the prompt)
    json_candidates = list(workspace.rglob("window_report.json"))
    if not json_candidates:
        # Also accept any *windows*.json produced in the skill dir
        json_candidates = list(workspace.rglob("*windows*.json")) + list(workspace.rglob("*window*.json"))

    if not json_candidates:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "No window_report.json (or *windows*.json) file found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = json_candidates[0]
    total_score += add("output_file_exists", True,
                       f"Found report file: {report_path.relative_to(workspace)}")

    # ── 2. Parse JSON ─────────────────────────────────────────────────────────
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        total_score += add("json_valid", True, "Report is valid JSON.")
    except Exception as e:
        total_score += add("json_valid", False, f"JSON parse error: {e}")
        return {"passed": False, "score": total_score / 9, "checks": checks}

    # ── 3. Check 'windows' key exists and has ≥ 3 entries ────────────────────
    windows = data.get("windows", [])
    if isinstance(windows, list) and len(windows) >= 3:
        total_score += add("windows_count", True,
                           f"Found {len(windows)} windows (≥3 required).")
    else:
        total_score += add("windows_count", False,
                           f"Expected at least 3 windows, got {len(windows)}.")

    # ── 4. First window must be 2026-04-07 ───────────────────────────────────
    try:
        first_date = windows[0].get("date", "")
        passed = first_date == "2026-04-07"
        total_score += add("first_window_date", passed,
                           f"First window date: '{first_date}' (expected '2026-04-07').")
    except (IndexError, AttributeError) as e:
        total_score += add("first_window_date", False, f"Could not read first window date: {e}")

    # ── 5. Window interval must use CHINESE working days (10 wd) ─────────────
    #       We verify windows 1→2 and 2→3 span exactly 10 Chinese working days.
    #       2026-04-07 + 10 Chinese workdays. 
    #       Key Chinese holidays in April 2026: Labour Day golden week falls in May.
    #       April 2026 has no major national holidays (Qingming is April 5 which is before our start).
    #       So 10 working days from 2026-04-07 (Mon): 
    #         Week of Apr 7: 7(Mon),8(Tue),9(Wed),10(Thu),11(Fri) = 5 days
    #         Week of Apr 14: 14(Mon),15(Tue),16(Wed),17(Thu),18(Fri) = 5 days  → total 10
    #         → 2nd window = 2026-04-21 (Tue)
    #       From 2026-04-21 + 10 wd:
    #         Week of Apr 21: 21(Tue),22(Wed),23(Thu),24(Fri) = 4 days
    #         Week of Apr 28: 28(Mon),29(Tue),30(Wed) = 3 days (no holiday)
    #         Week of May 4:  but May 1-3 is Labour Day holiday (3 days)
    #                         May 4(Mon) might be workday, May 7 is a make-up day sometimes
    #         Actually for 2026: May 1-5 is Labour Day holiday per typical Chinese calendar
    #         So May 4,5 may be off. Let's not hardcode - we just check the tool output
    #         vs a naive Mon-Fri calculation (they MUST differ around holiday periods).
    #
    #   The key check: second window date must be "2026-04-21" 
    #   (no holidays between Apr 7-21 that affect calculation)
    try:
        second_date = windows[1].get("date", "") if len(windows) > 1 else ""
        passed_2nd = second_date == "2026-04-21"
        total_score += add("second_window_date", passed_2nd,
                           f"Second window date: '{second_date}' (expected '2026-04-21' — 10 Chinese workdays from Apr 7).")
    except Exception as e:
        total_score += add("second_window_date", False, f"Error checking second window: {e}")

    # ── 6. Third window — must account for May Day (Labour Day) holiday ───────
    #   From 2026-04-21, add 10 Chinese workdays.
    #   Apr 21(Tue),22(Wed),23(Thu),24(Fri) = 4 wd
    #   Apr 27(Mon),28(Tue),29(Wed),30(Thu) = 4 wd  → 8 wd
    #   May 1 is Labour Day → holiday; May 2,3,4,5 also holiday (golden week typically)
    #   Makeup day (补班): often April 26 (Sun) is a makeup workday
    #   In 2026: Labour Day is May 1-5 (5 days off), with Apr 26 as a makeup day.
    #   So Apr 26 (Sun) IS a workday in 2026.
    #   Revised from Apr 21:
    #     Apr 21(Tue),22(Wed),23(Thu),24(Fri),26(Sun-makeup) = 5 wd
    #     Apr 27(Mon),28(Tue),29(Wed),30(Thu) = 4 wd → 9 wd
    #     May 6(Wed) or 7(Thu) would be wd 10
    #   → 3rd window ≈ 2026-05-06 or 2026-05-07
    #   The naive Mon-Fri calculator would give: Apr21+10wd = May 5 (skipping Apr 25 Sat, May 2-3 Sat-Sun)
    #   Actually naive: Apr21,22,23,24,27,28,29,30,May1,May4 = May 4
    #   Chinese calendar: May 1-5 off, Apr 26 makeup = different result
    #   We verify the third date is NOT "2026-05-05" (naive result) and is after Labour Day.
    try:
        third_date_str = windows[2].get("date", "") if len(windows) > 2 else ""
        if third_date_str:
            third_date = date.fromisoformat(third_date_str)
            # Must be after May 5 (end of Labour Day holiday) OR equal to May 6 or 7
            # Also must NOT be the naive answer of May 5 or earlier
            # We accept May 6 or May 7 as the correct chinese-workdays answer
            not_naive = third_date_str not in ("2026-05-05", "2026-05-04", "2026-05-03")
            is_after_holiday = third_date >= date(2026, 5, 6)
            passed_3rd = not_naive and is_after_holiday
            total_score += add("third_window_uses_chinese_holidays", passed_3rd,
                               f"Third window: '{third_date_str}'. Must reflect Chinese Labour Day "
                               f"holiday (≥2026-05-06, not naive Mon-Fri result). "
                               f"not_naive={not_naive}, is_after_holiday={is_after_holiday}.")
        else:
            total_score += add("third_window_uses_chinese_holidays", False,
                               "Third window date missing.")
    except Exception as e:
        total_score += add("third_window_uses_chinese_holidays", False,
                           f"Error checking third window: {e}")

    # ── 7. Config must be fixed (start_date=2026-04-07, interval=10) ──────────
    try:
        cfg = data.get("config", {})
        cfg_start_ok = cfg.get("start_date") == "2026-04-07"
        cfg_interval_ok = int(cfg.get("window_interval", 0)) == 10
        cfg_ok = cfg_start_ok and cfg_interval_ok
        total_score += add("config_correct_in_report", cfg_ok,
                           f"Config in report: start_date='{cfg.get('start_date')}' "
                           f"(need '2026-04-07'), window_interval={cfg.get('window_interval')} "
                           f"(need 10). Both correct: {cfg_ok}.")
    except Exception as e:
        total_score += add("config_correct_in_report", False,
                           f"Error reading config from report: {e}")

    # ── 8. config.yaml in skill dir must be corrected ─────────────────────────
    config_yaml_path = workspace / "oil-price-monitor" / "config.yaml"
    try:
        import yaml
        with open(config_yaml_path, "r", encoding="utf-8") as f:
            cfg_yaml = yaml.safe_load(f) or {}
        yaml_start_ok = cfg_yaml.get("start_date") == "2026-04-07"
        yaml_interval_ok = int(cfg_yaml.get("window_interval", 0)) == 10
        yaml_ok = yaml_start_ok and yaml_interval_ok
        total_score += add("config_yaml_corrected", yaml_ok,
                           f"config.yaml: start_date='{cfg_yaml.get('start_date')}' "
                           f"(need '2026-04-07'), window_interval={cfg_yaml.get('window_interval')} "
                           f"(need 10). Both correct: {yaml_ok}.")
    except Exception as e:
        total_score += add("config_yaml_corrected", False,
                           f"Could not validate config.yaml: {e}")

    # ── 9. Index values must be sequential (1, 2, 3, ...) ────────────────────
    try:
        indices = [w.get("index") for w in windows[:5]]
        expected = list(range(1, len(indices) + 1))
        seq_ok = indices == expected
        total_score += add("window_indices_sequential", seq_ok,
                           f"Window indices: {indices} (expected {expected}).")
    except Exception as e:
        total_score += add("window_indices_sequential", False,
                           f"Error checking indices: {e}")

    # ── Summary ───────────────────────────────────────────────────────────────
    max_score = 9.0
    score = total_score / max_score
    all_critical = (
        checks[0]["passed"] and  # file exists
        checks[3]["passed"] and  # first date correct
        checks[4]["passed"] and  # second date correct
        checks[5]["passed"]       # third date uses Chinese holidays
    )
    passed = all_critical and score >= 0.70

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "args", "passed": False,
                                      "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)

    result = run_checks(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))