import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ─────────────────────────────────────────────
# CHECK 1: flight_monitor_task.json exists
# ─────────────────────────────────────────────
task_files = list(workspace.rglob("flight_monitor_task.json"))
if not task_files:
    checks.append(make_check("task_json_exists", False, "flight_monitor_task.json not found anywhere in workspace"))
    task_data = None
else:
    task_file = task_files[0]
    try:
        task_data = json.loads(task_file.read_text(encoding="utf-8"))
        checks.append(make_check("task_json_exists", True, f"Found at {task_file.relative_to(workspace)}"))
    except Exception as e:
        checks.append(make_check("task_json_exists", False, f"Found but failed to parse JSON: {e}"))
        task_data = None

# ─────────────────────────────────────────────
# CHECK 2: task name format
# Must be: "机票监控 - 成都 - 昆明 04-10" (or similar date variant)
# ─────────────────────────────────────────────
if task_data:
    name = task_data.get("name", "")
    # Must contain "机票监控" and mention 成都/CTU/Chengdu and 昆明/KMG/Kunming
    name_has_monitor_keyword = "机票监控" in name
    name_has_origin = any(x in name for x in ["成都", "CTU", "Chengdu"])
    name_has_dest = any(x in name for x in ["昆明", "KMG", "Kunming"])
    name_ok = name_has_monitor_keyword and name_has_origin and name_has_dest
    checks.append(make_check(
        "task_name_format",
        name_ok,
        f"Name='{name}'. Must contain '机票监控', origin (成都/CTU), and destination (昆明/KMG)"
    ))
else:
    checks.append(make_check("task_name_format", False, "task_data unavailable"))

# ─────────────────────────────────────────────
# CHECK 3: schedule schema - kind=cron, expr, tz=Asia/Shanghai
# ─────────────────────────────────────────────
if task_data:
    schedule = task_data.get("schedule", {})
    kind_ok = schedule.get("kind") == "cron"
    tz_ok = schedule.get("tz") == "Asia/Shanghai"
    expr = schedule.get("expr", "")
    # Every 6 hours starting at 9:00 - valid cron expressions:
    # "0 9,15,21,3 * * *" or "0 */6 * * *" or "0 3,9,15,21 * * *"
    # We accept any cron expression that represents a 6-hour interval
    expr_valid = False
    if expr:
        # Check for common 6-hour patterns
        six_hour_patterns = [
            r"0\s+\*/6\s+\*\s+\*\s+\*",           # 0 */6 * * *
            r"0\s+9,15,21,3\s+\*\s+\*\s+\*",       # 0 9,15,21,3 * * *
            r"0\s+3,9,15,21\s+\*\s+\*\s+\*",       # 0 3,9,15,21 * * *
            r"0\s+9,15,21,27\s+\*\s+\*\s+\*",      # unlikely but allow
            r"0\s+0/6\s+\*\s+\*\s+\*",             # 0 0/6 * * * (quartz style)
        ]
        for pat in six_hour_patterns:
            if re.match(pat, expr.strip()):
                expr_valid = True
                break
        # Also accept if it contains /6 or has 4 hour entries with gap of 6
        if not expr_valid and ("/6" in expr or "*/6" in expr):
            expr_valid = True

    schedule_ok = kind_ok and tz_ok and expr_valid
    checks.append(make_check(
        "schedule_schema",
        schedule_ok,
        f"kind={schedule.get('kind')}, tz={schedule.get('tz')}, expr='{expr}'. Need kind=cron, tz=Asia/Shanghai, 6h interval expr"
    ))
else:
    checks.append(make_check("schedule_schema", False, "task_data unavailable"))

# ─────────────────────────────────────────────
# CHECK 4: payload schema - kind=agentTurn, message mentioning the route
# ─────────────────────────────────────────────
if task_data:
    payload = task_data.get("payload", {})
    payload_kind_ok = payload.get("kind") == "agentTurn"
    message = payload.get("message", "")
    # Message should mention the route and price threshold
    msg_has_route = any(x in message for x in ["成都", "CTU", "昆明", "KMG"])
    msg_has_price = "800" in message
    msg_ok = payload_kind_ok and msg_has_route and msg_has_price
    checks.append(make_check(
        "payload_schema",
        msg_ok,
        f"payload.kind={payload.get('kind')}, message mentions route={msg_has_route}, price 800={msg_has_price}"
    ))
else:
    checks.append(make_check("payload_schema", False, "task_data unavailable"))

# ─────────────────────────────────────────────
# CHECK 5: sessionTarget = "isolated"
# ─────────────────────────────────────────────
if task_data:
    session_target = task_data.get("sessionTarget", "")
    st_ok = session_target == "isolated"
    checks.append(make_check(
        "session_target_isolated",
        st_ok,
        f"sessionTarget='{session_target}'. Must be 'isolated'"
    ))
else:
    checks.append(make_check("session_target_isolated", False, "task_data unavailable"))

# ─────────────────────────────────────────────
# CHECK 6: search_url.txt exists and has correct round-trip URL
# ─────────────────────────────────────────────
url_files = list(workspace.rglob("search_url.txt"))
if not url_files:
    checks.append(make_check("search_url_exists", False, "search_url.txt not found"))
    url_content = None
else:
    url_file = url_files[0]
    url_content = url_file.read_text(encoding="utf-8").strip()
    checks.append(make_check("search_url_exists", True, f"Found at {url_file.relative_to(workspace)}"))

if url_content:
    url = url_content.strip().strip('"').strip("'")
    # Must be round-trip: tripType=1
    trip_type_ok = "tripType=1" in url
    # Must use correct city codes from skill.md (NOT IATA standards)
    # Chengdu = CTU, Kunming = KMG (these happen to match IATA but agent still needs to use the table)
    dep_city_ok = "depCity=CTU" in url
    arr_city_ok = "arrCity=KMG" in url
    # Must have depDate with April 10 2026
    dep_date_ok = any(d in url for d in ["depDate=2026-04-10", "depDate=20260410"])
    # Must have arrDate with April 15 2026 (return date)
    arr_date_ok = any(d in url for d in ["arrDate=2026-04-15", "arrDate=20260415"])
    # Must use the correct domain
    domain_ok = "sjipiao.fliggy.com" in url
    # Must have flight_search_result.htm
    path_ok = "flight_search_result.htm" in url

    url_correct = trip_type_ok and dep_city_ok and arr_city_ok and dep_date_ok and arr_date_ok and domain_ok and path_ok
    checks.append(make_check(
        "search_url_correct",
        url_correct,
        f"tripType=1:{trip_type_ok}, depCity=CTU:{dep_city_ok}, arrCity=KMG:{arr_city_ok}, "
        f"depDate:{dep_date_ok}, arrDate:{arr_date_ok}, domain:{domain_ok}, path:{path_ok}"
    ))
else:
    checks.append(make_check("search_url_correct", False, "search_url.txt is empty or unavailable"))

# ─────────────────────────────────────────────
# CHECK 7: URL has city name parameters (depCityName, arrCityName) URL-encoded
# ─────────────────────────────────────────────
if url_content:
    url = url_content.strip().strip('"').strip("'")
    # Must have depCityName and arrCityName
    has_dep_name = "depCityName" in url
    has_arr_name = "arrCityName" in url
    # The values should be 成都 (url-encoded: %E6%88%90%E9%83%BD) or 昆明 (%E6%98%86%E6%98%8E)
    # Accept either encoded or raw (some systems pass raw unicode)
    dep_name_value = (
        "%E6%88%90%E9%83%BD" in url or  # 成都 encoded
        "成都" in url or
        "Chengdu" in url.lower()
    )
    arr_name_value = (
        "%E6%98%86%E6%98%8E" in url or  # 昆明 encoded
        "昆明" in url or
        "Kunming" in url.lower()
    )
    names_ok = has_dep_name and has_arr_name and dep_name_value and arr_name_value
    checks.append(make_check(
        "url_city_names_present",
        names_ok,
        f"depCityName present:{has_dep_name}(val:{dep_name_value}), arrCityName present:{has_arr_name}(val:{arr_name_value})"
    ))
else:
    checks.append(make_check("url_city_names_present", False, "url unavailable"))

# ─────────────────────────────────────────────
# CHECK 8: Memory file exists at correct path
# Expected: memory/flight-monitor/成都-昆明-04-10.md (or similar)
# ─────────────────────────────────────────────
memory_base = workspace / "memory" / "flight-monitor"
memory_files = []
if memory_base.exists():
    memory_files = list(memory_base.glob("*.md"))

memory_file_found = False
memory_file = None
for mf in memory_files:
    fname = mf.name
    # Must contain 成都 (or CTU) and 昆明 (or KMG) and date reference (04-10 or 04 or 2026)
    has_origin = "成都" in fname or "CTU" in fname
    has_dest = "昆明" in fname or "KMG" in fname
    if has_origin and has_dest:
        memory_file_found = True
        memory_file = mf
        break

checks.append(make_check(
    "memory_file_correct_path",
    memory_file_found,
    f"Expected a .md file in memory/flight-monitor/ with 成都 and 昆明 in name. Found files: {[f.name for f in memory_files]}"
))

# ─────────────────────────────────────────────
# CHECK 9: Memory file has correct structure
# Must have: 监控信息 section, 价格记录 table header, correct route/date/threshold info
# ─────────────────────────────────────────────
if memory_file_found and memory_file:
    try:
        content = memory_file.read_text(encoding="utf-8")
        has_title = "成都" in content and "昆明" in content
        has_monitor_section = "监控信息" in content or "Monitor" in content
        has_price_table = "价格记录" in content or "Price" in content
        has_threshold = "800" in content
        has_date = "04-10" in content or "2026-04-10" in content or "April 10" in content.lower()
        
        structure_ok = has_title and has_monitor_section and has_price_table and has_threshold and has_date
        checks.append(make_check(
            "memory_file_structure",
            structure_ok,
            f"title(成都/昆明):{has_title}, 监控信息:{has_monitor_section}, 价格记录:{has_price_table}, threshold 800:{has_threshold}, date:{has_date}"
        ))
    except Exception as e:
        checks.append(make_check("memory_file_structure", False, f"Error reading memory file: {e}"))
else:
    checks.append(make_check("memory_file_structure", False, "Memory file not found, cannot check structure"))

# ─────────────────────────────────────────────
# CHECK 10: Memory file mentions round-trip (往返)
# ─────────────────────────────────────────────
if memory_file_found and memory_file:
    try:
        content = memory_file.read_text(encoding="utf-8")
        has_roundtrip = any(x in content for x in ["往返", "round", "Round", "return", "tripType=1", "04-15", "2026-04-15"])
        checks.append(make_check(
            "memory_file_roundtrip",
            has_roundtrip,
            f"Memory file should reference the round-trip nature (往返, return date 04-15, etc). Found: {has_roundtrip}"
        ))
    except Exception as e:
        checks.append(make_check("memory_file_roundtrip", False, f"Error: {e}"))
else:
    checks.append(make_check("memory_file_roundtrip", False, "Memory file not found"))

# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
score = len(passed_checks) / len(checks)
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": round(score, 3),
    "checks": checks
}

print(json.dumps(result, ensure_ascii=False, indent=2))