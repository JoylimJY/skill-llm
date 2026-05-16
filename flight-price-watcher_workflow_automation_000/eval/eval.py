import sys
import json
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta

def load_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_task_file(workspace):
    """Find the monitoring task file (task_003 or similar)"""
    candidates = []
    for p in Path(workspace).rglob("*.json"):
        try:
            data = load_json_file(p)
            if isinstance(data, dict) and data.get("taskId") == "003":
                candidates.append(p)
        except Exception:
            pass
    return candidates

def find_alert_eval_file(workspace):
    """Find the alert evaluation / price check result file"""
    candidates = []
    keywords = ["alert", "check", "eval", "result", "snapshot", "trigger"]
    for p in Path(workspace).rglob("*.json"):
        name_lower = p.name.lower()
        if any(k in name_lower for k in keywords):
            try:
                data = load_json_file(p)
                if isinstance(data, (dict, list)):
                    candidates.append((p, data))
            except Exception:
                pass
    return candidates

def run_checks(workspace):
    checks = []
    score_total = 0.0
    max_score = 0.0

    # ── CHECK 1: Task file exists with correct taskId ────────────────────────
    max_score += 10
    task_files = find_task_file(workspace)
    if task_files:
        checks.append({"name": "task_file_exists_with_id_003", "passed": True,
                        "detail": f"Found task file at {task_files[0]}"})
        score_total += 10
    else:
        checks.append({"name": "task_file_exists_with_id_003", "passed": False,
                        "detail": "No JSON file found with taskId='003'"})

    if not task_files:
        # Can't do further checks
        for remaining in ["correct_route_fields", "top3_flights_selected",
                          "base_price_is_minimum", "base_flight_flag",
                          "jumpur_present_all_flights", "threshold_defaults",
                          "expires_at_7days", "status_active",
                          "alert_eval_day2_3u8501", "alert_eval_day3_no_24h_repeat",
                          "alert_eval_day3_ca4101", "alert_eval_day3_mu2301_rise"]:
            checks.append({"name": remaining, "passed": False,
                           "detail": "Skipped: task file not found"})
            max_score += 10
        total = score_total / max_score if max_score > 0 else 0.0
        return checks, total

    task_path = task_files[0]
    try:
        task = load_json_file(task_path)
    except Exception as e:
        checks.append({"name": "task_file_parseable", "passed": False,
                        "detail": str(e)})
        return checks, 0.0

    # ── CHECK 2: Route fields ────────────────────────────────────────────────
    max_score += 10
    from_ok = task.get("from", "") in ["北京", "PEK", "BJS"]
    to_ok = task.get("to", "") in ["成都", "CTU"]
    date_ok = task.get("date", "") == "2026-05-01"
    route_ok = from_ok and to_ok and date_ok
    checks.append({"name": "correct_route_fields", "passed": route_ok,
                   "detail": f"from={task.get('from')}, to={task.get('to')}, date={task.get('date')}"})
    if route_ok:
        score_total += 10

    # ── CHECK 3: Top 3 flights selected (by price order: 590, 610, 650) ──────
    # According to skill: take the first 3 flights from search results
    # The raw data order is: CA4101(680), 3U8501(650), MU2301(720), ZH9201(590), HU7601(610)
    # "Top 3" in skill means first 3 from results list (not sorted by price)
    # BUT pricing-strategy.md says "前3个符合条件的航班" = first 3 in list
    # So expected: CA4101(680), 3U8501(650), MU2301(720)
    max_score += 15
    flights = task.get("selectedFlights", [])
    if len(flights) == 0:
        checks.append({"name": "top3_flights_selected", "passed": False,
                        "detail": "No selectedFlights found in task"})
    else:
        flight_nos = {f.get("flightNo") for f in flights}
        # Accept either interpretation: first 3 from list OR 3 cheapest
        first3_nos = {"CA4101", "3U8501", "MU2301"}
        cheapest3_nos = {"ZH9201", "HU7601", "3U8501"}  # 590, 610, 650
        count_ok = len(flights) == 3
        # Accept either first-3 or cheapest-3 interpretation
        set_ok = (flight_nos == first3_nos) or (flight_nos == cheapest3_nos) or \
                 (len(flights) >= 3 and len(flights) <= 5)
        top3_ok = count_ok and (flight_nos.issubset(
            {"CA4101", "3U8501", "MU2301", "ZH9201", "HU7601"}))
        checks.append({"name": "top3_flights_selected", "passed": top3_ok,
                        "detail": f"Found {len(flights)} flights: {flight_nos}"})
        if top3_ok:
            score_total += 15

    # ── CHECK 4: basePrice is minimum of selected flights ────────────────────
    max_score += 15
    if flights:
        prices = [f.get("price", 9999) for f in flights]
        computed_min = min(prices)
        recorded_base = task.get("basePrice", -1)
        base_ok = recorded_base == computed_min
        checks.append({"name": "base_price_is_minimum", "passed": base_ok,
                        "detail": f"basePrice={recorded_base}, min of selected={computed_min}, prices={prices}"})
        if base_ok:
            score_total += 15
    else:
        checks.append({"name": "base_price_is_minimum", "passed": False,
                        "detail": "No flights to check basePrice against"})

    # ── CHECK 5: isBaseFlight=true on cheapest flight ────────────────────────
    max_score += 10
    if flights:
        min_price = min(f.get("price", 9999) for f in flights)
        base_flights = [f for f in flights if f.get("isBaseFlight") is True]
        base_price_flight = [f for f in flights if f.get("price") == min_price]
        flag_ok = (len(base_flights) == 1 and
                   base_flights[0].get("price") == min_price)
        checks.append({"name": "base_flight_flag", "passed": flag_ok,
                        "detail": f"isBaseFlight=True flights: {[f.get('flightNo') for f in base_flights]}, cheapest: {[f.get('flightNo') for f in base_price_flight]}"})
        if flag_ok:
            score_total += 10
    else:
        checks.append({"name": "base_flight_flag", "passed": False,
                        "detail": "No flights to check"})

    # ── CHECK 6: All selected flights have jumpUrl ───────────────────────────
    max_score += 10
    if flights:
        missing_url = [f.get("flightNo") for f in flights if not f.get("jumpUrl")]
        url_ok = len(missing_url) == 0
        checks.append({"name": "jumpurl_present_all_flights", "passed": url_ok,
                        "detail": f"Flights missing jumpUrl: {missing_url}"})
        if url_ok:
            score_total += 10
    else:
        checks.append({"name": "jumpurl_present_all_flights", "passed": False,
                        "detail": "No flights to check"})

    # ── CHECK 7: Default thresholds (10% and ¥200 for drops) ────────────────
    max_score += 10
    tp = task.get("thresholdPercent", -1)
    ta = task.get("thresholdAmount", -1)
    thresh_ok = (tp == 10) and (ta == 200)
    checks.append({"name": "threshold_defaults", "passed": thresh_ok,
                   "detail": f"thresholdPercent={tp}, thresholdAmount={ta}"})
    if thresh_ok:
        score_total += 10

    # ── CHECK 8: expiresAt is ~7 days after createdAt ────────────────────────
    max_score += 10
    created_str = task.get("createdAt", "")
    expires_str = task.get("expiresAt", "")
    expires_ok = False
    expires_detail = f"createdAt={created_str}, expiresAt={expires_str}"
    try:
        # Parse both dates
        created_dt = datetime.fromisoformat(created_str)
        expires_dt = datetime.fromisoformat(expires_str)
        diff_days = (expires_dt - created_dt).total_seconds() / 86400
        expires_ok = abs(diff_days - 7.0) < 0.1  # within ~2.4 hours
        expires_detail += f" (diff={diff_days:.2f} days)"
    except Exception as e:
        expires_detail += f" (parse error: {e})"
    checks.append({"name": "expires_at_7days", "passed": expires_ok,
                   "detail": expires_detail})
    if expires_ok:
        score_total += 10

    # ── CHECK 9: status = active ─────────────────────────────────────────────
    max_score += 5
    status_ok = task.get("status") == "active"
    checks.append({"name": "status_active", "passed": status_ok,
                   "detail": f"status={task.get('status')}"})
    if status_ok:
        score_total += 5

    # ── ALERT EVALUATION CHECKS ──────────────────────────────────────────────
    # Now find the alert evaluation output file
    alert_files = find_alert_eval_file(workspace)
    alert_data = None
    alert_path = None

    # Also check for a dedicated output in tasks/
    for p in Path(workspace).rglob("*.json"):
        try:
            d = load_json_file(p)
            # Look for a list of check results or a dict with alert info
            if isinstance(d, list) and len(d) >= 2:
                # Check if it looks like alert evaluation results
                if any("alert" in str(item).lower() or "trigger" in str(item).lower()
                       for item in d):
                    alert_data = d
                    alert_path = p
                    break
            elif isinstance(d, dict) and ("alerts" in d or "checks" in d or "results" in d):
                alert_data = d
                alert_path = p
                break
        except Exception:
            pass

    # If not found via content, try by name
    if alert_data is None:
        for p, d in alert_files:
            if p != task_path:
                alert_data = d
                alert_path = p
                break

    # ── CHECK 10: Day 2 alert triggered for 3U8501 ──────────────────────────
    # 3U8501 drops from 650 -> 440 = -210 (32.3%), exceeds BOTH -10% and -¥200
    max_score += 10
    # ── CHECK 11: Day 3 - 3U8501 should NOT alert again (24h rule) ──────────
    max_score += 10
    # ── CHECK 12: Day 3 - CA4101 should alert (680->450 = -230, 33.8%) ──────
    max_score += 10
    # ── CHECK 13: Day 3 - MU2301 should alert rise (720->900 = +180, 25%) ───
    max_score += 10

    if alert_data is None:
        for chk_name in ["alert_day2_3u8501_triggered",
                          "alert_day3_3u8501_no_repeat_24h",
                          "alert_day3_ca4101_triggered",
                          "alert_day3_mu2301_rise_triggered"]:
            checks.append({"name": chk_name, "passed": False,
                           "detail": "No alert evaluation file found"})
    else:
        alert_str = json.dumps(alert_data, ensure_ascii=False).lower()

        # Check 10: Day 2, 3U8501 triggered
        day2_trigger = (
            ("3u8501" in alert_str or "3U8501" in json.dumps(alert_data)) and
            ("day" in alert_str or "2026-04-11" in alert_str or "第2" in alert_str or
             "snapshot" in alert_str or "trigger" in alert_str)
        )
        # More flexible: just check 3U8501 appears as alerting
        d2_check = False
        try:
            raw_str = json.dumps(alert_data, ensure_ascii=False)
            # Look for day 2 + 3U8501 alert
            if "3U8501" in raw_str:
                if any(indicator in raw_str for indicator in
                       ["alert", "trigger", "降价", "drop", "True", "true", "ALERT"]):
                    d2_check = True
        except Exception:
            pass
        checks.append({"name": "alert_day2_3u8501_triggered", "passed": d2_check,
                       "detail": f"Checked alert_data at {alert_path} for day2 3U8501 trigger"})
        if d2_check:
            score_total += 10

        # Check 11: Day 3, 3U8501 should NOT alert again (24h anti-spam)
        # This is nuanced - we check that the data explicitly marks it as suppressed/no-alert
        d3_3u_no_repeat = False
        try:
            raw_str = json.dumps(alert_data, ensure_ascii=False)
            # Accept if: mentions 24h / no_alert / suppressed / skip / False for day3 3U8501
            if any(kw in raw_str for kw in
                   ["24h", "24小时", "suppress", "no_alert", "skip", "cooldown",
                    "lastAlertAt", "last_alert", "防骚扰"]):
                d3_3u_no_repeat = True
            # Or if it's a list and day3 entry for 3U8501 shows no alert
            if isinstance(alert_data, list):
                for item in alert_data:
                    item_str = json.dumps(item, ensure_ascii=False)
                    if ("3U8501" in item_str and
                        ("day3" in item_str or "2026-04-12" in item_str or "第3" in item_str)):
                        if any(neg in item_str for neg in
                               ["false", "False", "no_alert", "skip", "suppressed",
                                "24", "cooldown"]):
                            d3_3u_no_repeat = True
        except Exception:
            pass
        checks.append({"name": "alert_day3_3u8501_no_repeat_24h", "passed": d3_3u_no_repeat,
                       "detail": f"Checked for 24h anti-spam suppression of 3U8501 on day3"})
        if d3_3u_no_repeat:
            score_total += 10

        # Check 12: Day 3, CA4101 should alert (680->450, -230, -33.8%)
        d3_ca_alert = False
        try:
            raw_str = json.dumps(alert_data, ensure_ascii=False)
            if "CA4101" in raw_str:
                if any(indicator in raw_str for indicator in
                       ["alert", "trigger", "降价", "drop", "True", "true", "ALERT"]):
                    # And it's associated with day3 / 450
                    if any(kw in raw_str for kw in ["450", "day3", "2026-04-12", "第3"]):
                        d3_ca_alert = True
        except Exception:
            pass
        checks.append({"name": "alert_day3_ca4101_triggered", "passed": d3_ca_alert,
                       "detail": f"Checked for CA4101 drop alert on day3"})
        if d3_ca_alert:
            score_total += 10

        # Check 13: Day 3, MU2301 rises 720->900 (+180, +25%), exceeds rise thresholds (15%/¥300)
        d3_mu_rise = False
        try:
            raw_str = json.dumps(alert_data, ensure_ascii=False)
            if "MU2301" in raw_str:
                if any(indicator in raw_str for indicator in
                       ["alert", "trigger", "涨价", "rise", "up", "True", "true", "ALERT", "🔴"]):
                    if any(kw in raw_str for kw in ["900", "day3", "2026-04-12", "第3", "+180"]):
                        d3_mu_rise = True
        except Exception:
            pass
        checks.append({"name": "alert_day3_mu2301_rise_triggered", "passed": d3_mu_rise,
                       "detail": f"Checked for MU2301 rise alert on day3 (720->900, +25%)"})
        if d3_mu_rise:
            score_total += 10

    final_score = score_total / max_score if max_score > 0 else 0.0
    return checks, final_score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_script_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False))
        return

    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    overall_passed = score >= 0.70

    result = {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks,
        "summary": f"{passed_count}/{total_count} checks passed, score={score:.2%}"
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()