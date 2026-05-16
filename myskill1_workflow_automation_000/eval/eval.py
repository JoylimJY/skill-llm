import sys
import os
import re
import json
import csv
import datetime

def evaluate(workspace):
    checks = []
    score = 0.0
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    two_days_ago = (datetime.date.today() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")

    # Expected mock values
    EXPECTED_CNBC = 4.334
    EXPECTED_TREASURY = 4.31

    # -----------------------------------------------------------------------
    # CHECK 1: CSV file exists at the correct location
    # -----------------------------------------------------------------------
    csv_path = os.path.join(workspace, "testdata/us_treasury_10y.csv")
    csv_exists = os.path.exists(csv_path)
    checks.append({
        "name": "csv_file_exists_at_correct_path",
        "passed": csv_exists,
        "detail": f"Expected CSV at testdata/us_treasury_10y.csv — {'found' if csv_exists else 'NOT found'}"
    })

    # -----------------------------------------------------------------------
    # CHECK 2: CSV has correct headers
    # -----------------------------------------------------------------------
    csv_rows = []
    csv_headers_ok = False
    try:
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            expected_fields = {"Date", "CNBC_10Y", "Treasury_10Y"}
            actual_fields = set(reader.fieldnames or [])
            csv_headers_ok = expected_fields == actual_fields
            csv_rows = list(reader)
    except Exception as e:
        csv_headers_ok = False

    checks.append({
        "name": "csv_correct_headers",
        "passed": csv_headers_ok,
        "detail": f"CSV must have exactly: Date, CNBC_10Y, Treasury_10Y. Headers found: {actual_fields if csv_rows is not None else 'file unreadable'}"
    })

    # -----------------------------------------------------------------------
    # CHECK 3: CSV retains old data (previous days preserved)
    # -----------------------------------------------------------------------
    old_dates_preserved = False
    try:
        dates_in_csv = [row["Date"] for row in csv_rows]
        old_dates_preserved = (two_days_ago in dates_in_csv) and (yesterday in dates_in_csv)
    except Exception as e:
        old_dates_preserved = False

    checks.append({
        "name": "csv_preserves_historical_rows",
        "passed": old_dates_preserved,
        "detail": f"Old entries for {two_days_ago} and {yesterday} must be preserved. Dates in CSV: {dates_in_csv if csv_rows else []}"
    })

    # -----------------------------------------------------------------------
    # CHECK 4: CSV contains today's entry
    # -----------------------------------------------------------------------
    today_row = None
    today_entry_exists = False
    try:
        for row in csv_rows:
            if row["Date"] == today_str:
                today_row = row
                today_entry_exists = True
                break
    except Exception as e:
        today_entry_exists = False

    checks.append({
        "name": "csv_has_today_entry",
        "passed": today_entry_exists,
        "detail": f"CSV must contain a row for today ({today_str}). Found: {today_row}"
    })

    # -----------------------------------------------------------------------
    # CHECK 5: Today's CSV values match mock data (CNBC=4.334, Treasury=4.31)
    # -----------------------------------------------------------------------
    csv_values_correct = False
    try:
        if today_row:
            cnbc_val = float(today_row["CNBC_10Y"])
            treasury_val = float(today_row["Treasury_10Y"])
            cnbc_ok = abs(cnbc_val - EXPECTED_CNBC) < 0.001
            treasury_ok = abs(treasury_val - EXPECTED_TREASURY) < 0.001
            csv_values_correct = cnbc_ok and treasury_ok
    except Exception as e:
        csv_values_correct = False

    checks.append({
        "name": "csv_today_values_match_mock",
        "passed": csv_values_correct,
        "detail": f"Expected CNBC_10Y=4.334, Treasury_10Y=4.31. Got: {today_row}"
    })

    # -----------------------------------------------------------------------
    # CHECK 6: Only one row per day (no duplicates for today)
    # -----------------------------------------------------------------------
    no_today_duplicates = False
    try:
        today_count = sum(1 for row in csv_rows if row["Date"] == today_str)
        no_today_duplicates = (today_count == 1)
    except Exception as e:
        no_today_duplicates = False

    checks.append({
        "name": "csv_no_duplicate_today_rows",
        "passed": no_today_duplicates,
        "detail": f"Must have exactly 1 row for today ({today_str}). Found: {today_count if csv_rows else 'unknown'}"
    })

    # -----------------------------------------------------------------------
    # CHECK 7: Log file exists at correct path
    # -----------------------------------------------------------------------
    log_path = os.path.join(workspace, "skills/us-treasury-tracker/logs/fetch.log")
    log_exists = os.path.exists(log_path)
    checks.append({
        "name": "log_file_exists_at_correct_path",
        "passed": log_exists,
        "detail": f"Expected log at skills/us-treasury-tracker/logs/fetch.log — {'found' if log_exists else 'NOT found'}"
    })

    # -----------------------------------------------------------------------
    # CHECK 8: Log contains at least two new entries for today
    # (first 'append', then 'overwrite') indicating script was run twice
    # -----------------------------------------------------------------------
    log_append_found = False
    log_overwrite_found = False
    today_log_lines = []
    log_line_pattern = re.compile(
        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (append|overwrite) \| (success|partial|fail) \| cnbc=([\d.]+|N/A) treasury=([\d.]+|N/A)$'
    )

    try:
        with open(log_path, "r") as f:
            all_lines = f.readlines()

        # Filter only new entries added today (timestamp date matches today)
        for line in all_lines:
            line = line.strip()
            m = log_line_pattern.match(line)
            if m:
                timestamp_date = m.group(1)[:10]  # Extract YYYY-MM-DD from timestamp
                if timestamp_date == today_str:
                    today_log_lines.append(line)

        # Check we have at least 2 today-entries: one append, one overwrite
        actions_today = []
        for line in today_log_lines:
            m = log_line_pattern.match(line)
            if m:
                actions_today.append(m.group(2))

        log_append_found = "append" in actions_today
        log_overwrite_found = "overwrite" in actions_today

    except Exception as e:
        log_append_found = False
        log_overwrite_found = False

    checks.append({
        "name": "log_has_append_entry_today",
        "passed": log_append_found,
        "detail": f"Log must contain an 'append' entry for today ({today_str}). Today's log lines: {today_log_lines}"
    })

    checks.append({
        "name": "log_has_overwrite_entry_today",
        "passed": log_overwrite_found,
        "detail": f"Log must contain an 'overwrite' entry for today ({today_str}), proving script was run at least twice. Today's log lines: {today_log_lines}"
    })

    # -----------------------------------------------------------------------
    # CHECK 9: Log format is correct (all today's lines match the pattern)
    # -----------------------------------------------------------------------
    log_format_correct = False
    try:
        if today_log_lines:
            all_match = all(log_line_pattern.match(line) for line in today_log_lines)
            log_format_correct = all_match
        else:
            log_format_correct = False
    except Exception as e:
        log_format_correct = False

    checks.append({
        "name": "log_format_correct",
        "passed": log_format_correct,
        "detail": f"All today's log lines must match: 'YYYY-MM-DD HH:MM:SS | action | status | cnbc=X treasury=Y'. Lines: {today_log_lines}"
    })

    # -----------------------------------------------------------------------
    # CHECK 10: Log values match mock data
    # -----------------------------------------------------------------------
    log_values_correct = False
    try:
        for line in today_log_lines:
            m = log_line_pattern.match(line)
            if m and m.group(2) == "overwrite":  # Check the overwrite entry
                cnbc_log_val = float(m.group(4))
                treasury_log_val = float(m.group(5))
                if abs(cnbc_log_val - EXPECTED_CNBC) < 0.001 and abs(treasury_log_val - EXPECTED_TREASURY) < 0.001:
                    log_values_correct = True
                    break
        # If overwrite not found, check append
        if not log_values_correct:
            for line in today_log_lines:
                m = log_line_pattern.match(line)
                if m and m.group(2) == "append":
                    cnbc_log_val = float(m.group(4))
                    treasury_log_val = float(m.group(5))
                    if abs(cnbc_log_val - EXPECTED_CNBC) < 0.001 and abs(treasury_log_val - EXPECTED_TREASURY) < 0.001:
                        log_values_correct = True
                        break
    except Exception as e:
        log_values_correct = False

    checks.append({
        "name": "log_values_match_mock_data",
        "passed": log_values_correct,
        "detail": f"Log must show cnbc=4.334 treasury=4.31. Today log lines: {today_log_lines}"
    })

    # -----------------------------------------------------------------------
    # Score calculation
    # -----------------------------------------------------------------------
    # Weights: critical checks get higher weight
    weights = {
        "csv_file_exists_at_correct_path": 0.05,
        "csv_correct_headers": 0.05,
        "csv_preserves_historical_rows": 0.10,
        "csv_has_today_entry": 0.10,
        "csv_today_values_match_mock": 0.10,
        "csv_no_duplicate_today_rows": 0.10,
        "log_file_exists_at_correct_path": 0.05,
        "log_has_append_entry_today": 0.10,
        "log_has_overwrite_entry_today": 0.15,
        "log_format_correct": 0.10,
        "log_values_match_mock_data": 0.10,
    }

    total_score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.0)
        if check["passed"]:
            total_score += w

    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": round(total_score, 3),
        "checks": checks
    }

    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)