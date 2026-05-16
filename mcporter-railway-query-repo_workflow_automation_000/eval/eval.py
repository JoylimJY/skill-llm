#!/usr/bin/env python3
"""
Evaluation script for the mcporter railway ticket query task.
Usage: python3 eval_script.py <workspace_dir>
"""
import sys
import json
import os
from pathlib import Path

def load_call_record():
    """Load the mcporter call log."""
    path = "/tmp/mcporter_call_record.json"
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return []

def find_output_file(workspace):
    """Find train_options.json anywhere in workspace."""
    matches = list(Path(workspace).rglob("train_options.json"))
    return matches[0] if matches else None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    
    calls = load_call_record()

    # ── Check 1: get-station-code-of-citys was called ──────────────────────────
    station_calls = [c for c in calls if c.get("tool") == "12306.get-station-code-of-citys"]
    check1_passed = False
    check1_detail = "No call to 12306.get-station-code-of-citys found."
    if station_calls:
        for sc in station_calls:
            citys = sc.get("args", {}).get("citys", "")
            # Must use pipe-separated format and include both cities
            if "|" in citys:
                parts = set(p.strip() for p in citys.split("|"))
                if "成都东" in parts and "西安北" in parts:
                    check1_passed = True
                    check1_detail = f"Correctly called get-station-code-of-citys with citys='{citys}' (pipe-separated, both cities included)."
                    break
            # Also accept individual calls for each city
            if "成都东" in citys or "西安北" in citys:
                # partial credit: check if both cities are queried across calls
                pass
        if not check1_passed:
            # Check if individual calls cover both cities
            all_citys = " ".join(sc.get("args", {}).get("citys", "") for sc in station_calls)
            if "成都东" in all_citys and "西安北" in all_citys:
                check1_passed = True
                check1_detail = f"Station codes queried for both 成都东 and 西安北 across multiple calls."
            else:
                check1_detail = f"Station code query found but did not cover both 成都东 and 西安北. Got: citys values = {[sc.get('args',{}).get('citys','') for sc in station_calls]}"
    checks.append({"name": "station_code_lookup", "passed": check1_passed, "detail": check1_detail})

    # ── Check 2: get-tickets called with correct station codes ─────────────────
    ticket_calls = [c for c in calls if c.get("tool") == "12306.get-tickets"]
    check2_passed = False
    check2_detail = "No call to 12306.get-tickets found."
    correct_ticket_call = None
    if ticket_calls:
        for tc in ticket_calls:
            a = tc.get("args", {})
            from_st = a.get("fromStation", "").upper()
            to_st   = a.get("toStation", "").upper()
            date    = a.get("date", "")
            if from_st == "CDW" and to_st == "ENH" and date == "2026-03-15":
                check2_passed = True
                check2_detail = f"Correctly called get-tickets with fromStation=CDW, toStation=ENH, date=2026-03-15."
                correct_ticket_call = tc
                break
        if not check2_passed:
            sample = [(c.get("args",{}).get("fromStation"), c.get("args",{}).get("toStation"), c.get("args",{}).get("date")) for c in ticket_calls]
            check2_detail = f"get-tickets called but with wrong params. Calls: {sample}"
    checks.append({"name": "correct_station_codes_in_query", "passed": check2_passed, "detail": check2_detail})

    # ── Check 3: trainFilterFlags includes both G and D (not just G) ──────────
    check3_passed = False
    check3_detail = "No correct ticket call found to check trainFilterFlags."
    if correct_ticket_call:
        a = correct_ticket_call.get("args", {})
        flags = a.get("trainFilterFlags", "")
        # GD means both G and D; empty string also means all (G+D+C), but skill says GD = G+D
        # The task requires "high-speed or bullet trains only" → trainFilterFlags="GD"
        if "G" in flags.upper() and "D" in flags.upper():
            check3_passed = True
            check3_detail = f"trainFilterFlags='{flags}' correctly includes both G (高铁) and D (动车) trains."
        elif flags == "":
            check3_passed = False
            check3_detail = "trainFilterFlags is empty (would include C trains too). Task requires GD for high-speed+bullet only."
        else:
            check3_detail = f"trainFilterFlags='{flags}' does not include both G and D. Expected 'GD'."
    checks.append({"name": "train_filter_flags_GD", "passed": check3_passed, "detail": check3_detail})

    # ── Check 4: Time window 08:00-14:00 ──────────────────────────────────────
    check4_passed = False
    check4_detail = "No correct ticket call found to check time window."
    if correct_ticket_call:
        a = correct_ticket_call.get("args", {})
        try:
            earliest = int(a.get("earliestStartTime", 0))
            latest   = int(a.get("latestStartTime", 24))
            if earliest == 8 and latest == 14:
                check4_passed = True
                check4_detail = f"Time window correctly set: earliestStartTime={earliest}, latestStartTime={latest}."
            else:
                check4_detail = f"Time window incorrect: earliestStartTime={earliest}, latestStartTime={latest}. Expected 8 and 14."
        except (ValueError, TypeError) as e:
            check4_detail = f"Could not parse time params: {e}"
    checks.append({"name": "time_window_08_to_14", "passed": check4_passed, "detail": check4_detail})

    # ── Check 5: sortFlag=duration ─────────────────────────────────────────────
    check5_passed = False
    check5_detail = "No correct ticket call found to check sortFlag."
    if correct_ticket_call:
        a = correct_ticket_call.get("args", {})
        sort_flag = a.get("sortFlag", "")
        if sort_flag == "duration":
            check5_passed = True
            check5_detail = "sortFlag='duration' correctly used to minimize travel time."
        else:
            check5_detail = f"sortFlag='{sort_flag}' is incorrect. Expected 'duration' to get fastest trains."
    checks.append({"name": "sort_by_duration", "passed": check5_passed, "detail": check5_detail})

    # ── Check 6: limitedNum=5 ─────────────────────────────────────────────────
    check6_passed = False
    check6_detail = "No correct ticket call found to check limitedNum."
    if correct_ticket_call:
        a = correct_ticket_call.get("args", {})
        try:
            limit = int(a.get("limitedNum", 0))
            if limit == 5:
                check6_passed = True
                check6_detail = "limitedNum=5 correctly set to return top 5 results."
            else:
                check6_detail = f"limitedNum={limit}. Expected 5."
        except (ValueError, TypeError) as e:
            check6_detail = f"Could not parse limitedNum: {e}"
    checks.append({"name": "limit_5_results", "passed": check6_passed, "detail": check6_detail})

    # ── Check 7: format=json ──────────────────────────────────────────────────
    check7_passed = False
    check7_detail = "No correct ticket call found to check format."
    if correct_ticket_call:
        a = correct_ticket_call.get("args", {})
        fmt = a.get("format", "text")
        if fmt == "json":
            check7_passed = True
            check7_detail = "format='json' correctly used for JSON output."
        else:
            check7_detail = f"format='{fmt}'. Expected 'json' since output must be a JSON file."
    checks.append({"name": "output_format_json", "passed": check7_passed, "detail": check7_detail})

    # ── Check 8: train_options.json exists and has 5 entries ──────────────────
    check8_passed = False
    check8_detail = "train_options.json not found in workspace."
    output_file = find_output_file(workspace)
    train_data = None
    if output_file:
        try:
            with open(output_file) as f:
                content = f.read().strip()
            train_data = json.loads(content)
            if isinstance(train_data, list) and len(train_data) == 5:
                check8_passed = True
                check8_detail = f"train_options.json found at {output_file} with exactly 5 entries."
            else:
                check8_detail = f"train_options.json found but has {len(train_data) if isinstance(train_data, list) else 'non-list'} entries. Expected 5."
        except json.JSONDecodeError as e:
            check8_detail = f"train_options.json found but is not valid JSON: {e}"
        except Exception as e:
            check8_detail = f"Error reading train_options.json: {e}"
    checks.append({"name": "output_file_exists_with_5_entries", "passed": check8_passed, "detail": check8_detail})

    # ── Check 9: Results are sorted by duration (shortest first) ──────────────
    check9_passed = False
    check9_detail = "Cannot verify sort order (train_options.json missing or invalid)."
    if train_data and isinstance(train_data, list) and len(train_data) >= 2:
        # The mock returns duration_minutes-sorted data when sortFlag=duration
        # Check that durations are in ascending order by parsing duration strings
        import re
        def parse_duration(d):
            """Parse '3h20m' or '4h28m' to minutes."""
            try:
                h = int(re.search(r'(\d+)h', d).group(1)) if 'h' in d else 0
                m_match = re.search(r'(\d+)m', d)
                m = int(m_match.group(1)) if m_match else 0
                return h * 60 + m
            except Exception:
                return 9999
        try:
            durations = [parse_duration(t.get("duration", "")) for t in train_data]
            if all(durations[i] <= durations[i+1] for i in range(len(durations)-1)):
                check9_passed = True
                check9_detail = f"Results correctly sorted by duration ascending: {[t.get('duration') for t in train_data]}"
            else:
                check9_detail = f"Results NOT sorted by duration. Durations found: {[t.get('duration') for t in train_data]}"
        except Exception as e:
            check9_detail = f"Error checking sort order: {e}"
    checks.append({"name": "results_sorted_by_duration", "passed": check9_passed, "detail": check9_detail})

    # ── Check 10: Results contain only G/D trains (no C trains) ───────────────
    check10_passed = False
    check10_detail = "Cannot verify train types (train_options.json missing or invalid)."
    if train_data and isinstance(train_data, list) and len(train_data) > 0:
        try:
            train_nos = [t.get("train_no", "") for t in train_data]
            has_c_trains = any(n.startswith("C") for n in train_nos)
            all_gd = all(n.startswith("G") or n.startswith("D") for n in train_nos)
            if all_gd and not has_c_trains:
                check10_passed = True
                check10_detail = f"All 5 results are G or D trains: {train_nos}"
            else:
                check10_detail = f"Results contain unexpected train types: {train_nos}"
        except Exception as e:
            check10_detail = f"Error checking train types: {e}"
    checks.append({"name": "only_G_D_trains_in_results", "passed": check10_passed, "detail": check10_detail})

    # ── Check 11: --config flag used correctly ────────────────────────────────
    check11_passed = False
    check11_detail = "No ticket call with --config flag found."
    if correct_ticket_call:
        a = correct_ticket_call.get("args", {})
        cfg = a.get("__config", "")
        if "mcporter.json" in cfg:
            check11_passed = True
            check11_detail = f"--config flag correctly used: {cfg}"
        else:
            check11_detail = f"--config not set or missing mcporter.json reference. Got: '{cfg}'"
    checks.append({"name": "config_flag_used", "passed": check11_passed, "detail": check11_detail})

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)

    # Overall pass: must pass core checks (2,3,4,5,6,7,8 = indices 1-7)
    core_checks = [checks[1], checks[2], checks[3], checks[4], checks[5], checks[6], checks[7]]
    overall_passed = all(c["passed"] for c in core_checks)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()