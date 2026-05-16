import sys
import json
import re
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── 1. Find the output JSON file ──────────────────────────────────────────
    target_filename = "spring_festival_comparison.json"
    found_files = list(workspace.rglob(target_filename))

    if not found_files:
        add_check("output_file_exists", False,
                  f"'{target_filename}' not found anywhere under {workspace_dir}")
        return {"passed": False, "score": 0.0, "checks": checks}

    output_file = found_files[0]
    add_check("output_file_exists", True, f"Found at: {output_file}")

    # ── 2. Parse JSON ─────────────────────────────────────────────────────────
    try:
        raw = output_file.read_text(encoding="utf-8")
        data = json.loads(raw)
        add_check("valid_json", True, "File is valid JSON")
    except Exception as e:
        add_check("valid_json", False, f"JSON parse error: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 3. Check 2025 cache was force-refreshed ───────────────────────────────
    # The correct 2025 data says 春节 is 8 days (共8天) starting Jan 28 (除夕).
    # The stale cache says 6 days starting Jan 29. If the agent used cache,
    # the data will reflect 6 days / Jan 29 — that's a failure.
    try:
        cache_2025 = (workspace / "skills" / "china-holidays" / "assets" / "2025.md").read_text(encoding="utf-8")
        # After force-refresh, the cache file should contain the correct data
        correct_2025_refresh = "1月28日" in cache_2025 and "8天" in cache_2025
        stale_still_present = "1月29日" in cache_2025 and "6天" in cache_2025 and "草案" in cache_2025
        if correct_2025_refresh:
            add_check("2025_cache_was_force_refreshed", True,
                      "assets/2025.md contains correct data (1月28日, 8天) — force refresh was used")
        elif stale_still_present:
            add_check("2025_cache_was_force_refreshed", False,
                      "assets/2025.md still contains stale draft data — agent did NOT use --force for 2025")
        else:
            add_check("2025_cache_was_force_refreshed", False,
                      f"assets/2025.md content is ambiguous or unexpected. Preview: {cache_2025[:200]}")
    except Exception as e:
        add_check("2025_cache_was_force_refreshed", False, f"Could not read 2025 cache: {e}")

    # ── 4. Validate 2025 春节 data in JSON output ─────────────────────────────
    try:
        raw_str = json.dumps(data, ensure_ascii=False)

        # Must contain correct 2025 春节 start date
        has_2025_correct_date = "1月28日" in raw_str or "28日" in raw_str
        # Must contain correct 2025 duration: 8 days
        has_2025_correct_days = "8" in raw_str
        # Must NOT reflect the stale 6-day figure prominently as the 2025 answer
        # (we check: if "6天" appears paired with 2025 spring festival, that's wrong)
        stale_6days_for_2025 = bool(re.search(r'2025.{0,60}6天', raw_str)) or \
                                bool(re.search(r'6天.{0,60}2025', raw_str))

        if has_2025_correct_date and has_2025_correct_days and not stale_6days_for_2025:
            add_check("2025_spring_festival_correct", True,
                      "2025 春节 data is correct: 8 days starting Jan 28 (除夕)")
        elif stale_6days_for_2025:
            add_check("2025_spring_festival_correct", False,
                      "Output contains stale 6-day figure for 2025 春节 — agent used stale cache")
        else:
            add_check("2025_spring_festival_correct", False,
                      f"2025 春节 data missing or incorrect. has_date={has_2025_correct_date}, "
                      f"has_8days={has_2025_correct_days}")
    except Exception as e:
        add_check("2025_spring_festival_correct", False, f"Error checking 2025 data: {e}")

    # ── 5. Validate 2026 春节 data in JSON output ─────────────────────────────
    try:
        raw_str = json.dumps(data, ensure_ascii=False)

        has_2026_date = "2月15日" in raw_str or "15日" in raw_str
        has_2026_days = "9" in raw_str
        # makeup work days for 2026 spring festival
        has_2026_makeup = "2月14日" in raw_str or "2月28日" in raw_str

        if has_2026_date and has_2026_days:
            add_check("2026_spring_festival_correct", True,
                      "2026 春节 data is correct: 9 days starting Feb 15")
        else:
            add_check("2026_spring_festival_correct", False,
                      f"2026 春节 data incorrect. has_date={has_2026_date}, has_9days={has_2026_days}")
    except Exception as e:
        add_check("2026_spring_festival_correct", False, f"Error checking 2026 data: {e}")

    # ── 6. JSON has comparative structure (both years present) ────────────────
    try:
        raw_str = json.dumps(data, ensure_ascii=False)
        has_2025_key = "2025" in raw_str
        has_2026_key = "2026" in raw_str
        has_spring = "春节" in raw_str

        if has_2025_key and has_2026_key and has_spring:
            add_check("json_has_comparative_structure", True,
                      "JSON contains both 2025 and 2026 年春节 comparison data")
        else:
            add_check("json_has_comparative_structure", False,
                      f"JSON missing keys: has_2025={has_2025_key}, has_2026={has_2026_key}, "
                      f"has_春节={has_spring}")
    except Exception as e:
        add_check("json_has_comparative_structure", False, f"Error: {e}")

    # ── 7. Cross-year difference mentioned (9-8=1 day difference) ────────────
    try:
        raw_str = json.dumps(data, ensure_ascii=False)
        # The comparison should reflect that 2026 has 1 more day than 2025
        # We look for either a numeric difference or both day counts present
        has_diff_indication = (
            ("8" in raw_str and "9" in raw_str) or
            "多1天" in raw_str or
            "多放1天" in raw_str or
            "差1天" in raw_str or
            "1天" in raw_str
        )
        if has_diff_indication:
            add_check("cross_year_difference_noted", True,
                      "JSON reflects difference between 2025 (8 days) and 2026 (9 days)")
        else:
            add_check("cross_year_difference_noted", False,
                      "JSON does not clearly reflect the 1-day difference between years")
    except Exception as e:
        add_check("cross_year_difference_noted", False, f"Error: {e}")

    # ── Score ─────────────────────────────────────────────────────────────────
    critical_checks = [
        "output_file_exists",
        "valid_json",
        "2025_cache_was_force_refreshed",
        "2025_spring_festival_correct",
        "2026_spring_festival_correct",
        "json_has_comparative_structure",
    ]
    all_checks_map = {c["name"]: c["passed"] for c in checks}

    critical_passed = sum(1 for c in critical_checks if all_checks_map.get(c, False))
    total_passed = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)

    score = round(total_passed / total_checks, 3) if total_checks > 0 else 0.0
    # Must pass all critical checks to pass overall
    overall_passed = all(all_checks_map.get(c, False) for c in critical_checks)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = run_eval(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))