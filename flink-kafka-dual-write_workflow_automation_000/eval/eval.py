#!/usr/bin/env python3
"""
Evaluation script for Task 37: Bus_RouteCapacity_KafkaToStarRock_37
Checks that the agent correctly:
1. Created SkynetLogRouteCapacityMessageModel.java with list field 'segments'
2. Created SkynetLogRouteCapacityPo.java with correct field order (st first, year/month/day last)
3. Created Bus_RouteCapacity_KafkaToStarRock_37.java with:
   - MODULE constant = "BUS_PUBLIC_ROUTE_CAPACITY_MONITOR" (hardcoded, not from config)
   - FlatMapFunction pattern (list expansion, 35/36 style)
   - logTime A-scheme: LOG.error + return/null on failure
   - id from skyNetVo.getId() with UUID fallback
   - list null/empty guard (return if null or empty)
   - cnt = 1
   - safe() on string fields
   - year/month/day appended at end
4. All 4 config.properties files updated with correct key patterns
"""

import sys
import json
import re
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None

def find_file(workspace, filename):
    results = list(Path(workspace).rglob(filename))
    if results:
        return results[0].read_text(encoding='utf-8'), str(results[0])
    return None, None

def check(name, passed, detail=""):
    return {"name": name, "passed": passed, "detail": detail}

def evaluate(workspace):
    checks = []
    ws = Path(workspace)

    # ── 1. MessageModel file ──────────────────────────────────────────────────
    mm_content, mm_path = find_file(workspace, "SkynetLogRouteCapacityMessageModel.java")
    if mm_content is None:
        checks.append(check("MessageModel file exists", False, "SkynetLogRouteCapacityMessageModel.java not found"))
    else:
        checks.append(check("MessageModel file exists", True, mm_path))

        # Must be in correct package path
        correct_pkg = "com.ly.tms.po.carSupply" in mm_content
        checks.append(check("MessageModel package correct", correct_pkg,
                           "Expected package com.ly.tms.po.carSupply"))

        # Must have a list field for segments (the business list to expand)
        has_list = bool(re.search(r'List\s*<', mm_content))
        checks.append(check("MessageModel has List<> field for expansion", has_list,
                           "Expected a List<> field (segments or similar) in MessageModel"))

        # SkyNetVo inner class with id field
        has_skynetvo = bool(re.search(r'class\s+SkyNetVo', mm_content))
        checks.append(check("MessageModel has SkyNetVo inner class", has_skynetvo, ""))

        # Must have logTime, apmtraceid, module, traceid, message fields
        required_fields = ['logTime', 'apmtraceid', 'module', 'traceid', 'message']
        for field in required_fields:
            has_f = field in mm_content
            checks.append(check(f"MessageModel has field '{field}'", has_f, ""))

    # ── 2. Po file ────────────────────────────────────────────────────────────
    po_content, po_path = find_file(workspace, "SkynetLogRouteCapacityPo.java")
    if po_content is None:
        checks.append(check("Po file exists", False, "SkynetLogRouteCapacityPo.java not found"))
    else:
        checks.append(check("Po file exists", True, po_path))

        # Correct package
        correct_pkg = "com.ly.tms.po.carSupply" in po_content
        checks.append(check("Po package correct", correct_pkg, ""))

        # st must appear before other fields
        st_pos = po_content.find('private LocalDateTime st')
        if st_pos == -1:
            st_pos = po_content.find('private LocalDateTime st;')
        apmtraceid_pos = po_content.find('apmtraceid')
        st_first = st_pos != -1 and apmtraceid_pos != -1 and st_pos < apmtraceid_pos
        checks.append(check("Po: st is first business field (before apmtraceid)", st_first,
                           f"st_pos={st_pos}, apmtraceid_pos={apmtraceid_pos}"))

        # year/month/day must be at end (after business fields)
        year_pos = po_content.rfind('private String year')
        month_pos = po_content.rfind('private String month')
        day_pos = po_content.rfind('private String day')
        # Find last business field (not year/month/day)
        # Check that year, month, day appear in that order at the end
        ymد_ordered = (year_pos != -1 and month_pos != -1 and day_pos != -1 and
                       year_pos < month_pos < day_pos)
        checks.append(check("Po: year, month, day fields exist and ordered", ymد_ordered,
                           f"year={year_pos}, month={month_pos}, day={day_pos}"))

        # cnt must be Integer
        has_cnt = bool(re.search(r'private\s+Integer\s+cnt', po_content))
        checks.append(check("Po: cnt is Integer type", has_cnt, ""))

        # id must be String
        has_id = bool(re.search(r'private\s+String\s+id', po_content))
        checks.append(check("Po: id is String type", has_id, ""))

    # ── 3. Job file ───────────────────────────────────────────────────────────
    job_content, job_path = find_file(workspace, "Bus_RouteCapacity_KafkaToStarRock_37.java")
    if job_content is None:
        checks.append(check("Job file exists", False, "Bus_RouteCapacity_KafkaToStarRock_37.java not found"))
    else:
        checks.append(check("Job file exists", True, job_path))

        # Correct package
        correct_pkg = "com.ly.tms.job" in job_content
        checks.append(check("Job package correct", correct_pkg, ""))

        # MODULE constant must be hardcoded (not read from config/properties)
        module_const = bool(re.search(
            r'(static\s+final\s+String\s+MODULE\s*=\s*"BUS_PUBLIC_ROUTE_CAPACITY_MONITOR"'
            r'|MODULE\s*=\s*"BUS_PUBLIC_ROUTE_CAPACITY_MONITOR")',
            job_content))
        checks.append(check("Job: MODULE constant hardcoded as BUS_PUBLIC_ROUTE_CAPACITY_MONITOR",
                           module_const,
                           "MODULE must be a static final String constant in the Job class, not from config"))

        # Must use FlatMapFunction (list-expansion pattern, like 35/36)
        has_flatmap = bool(re.search(r'FlatMapFunction', job_content))
        checks.append(check("Job: uses FlatMapFunction (list-expansion pattern)", has_flatmap,
                           "Task has segments list, must use flatMap expansion like tasks 35/36"))

        # logTime A-scheme: LOG.error present for logTime failure
        has_logerror_logtime = bool(re.search(
            r'LOG\.error.*logTime', job_content, re.DOTALL))
        checks.append(check("Job: LOG.error on logTime parse failure (A-scheme)", has_logerror_logtime,
                           "Must log error and discard on logTime parse failure, not silently skip"))

        # id from skyNetVo.getId() with UUID fallback
        has_id_logic = bool(re.search(r'skyNetVo.*getId\(\)', job_content, re.DOTALL) or
                           re.search(r'getId\(\).*UUID', job_content, re.DOTALL))
        has_uuid_fallback = 'UUID.randomUUID()' in job_content
        checks.append(check("Job: id from skyNetVo.getId()", has_id_logic, ""))
        checks.append(check("Job: UUID fallback when id is null", has_uuid_fallback, ""))

        # List null/empty guard - must check for null or empty list before iterating
        has_null_guard = bool(re.search(
            r'(null\s*\|\|\s*.*\.isEmpty\(\)|\.isEmpty\(\)\s*\)\s*return)',
            job_content))
        checks.append(check("Job: list null/empty guard before iteration", has_null_guard,
                           "Must return/skip if segments list is null or empty"))

        # cnt = 1
        has_cnt_1 = bool(re.search(r'\.setCnt\s*\(\s*1\s*\)', job_content))
        checks.append(check("Job: cnt set to 1", has_cnt_1, ""))

        # safe() used for string fields
        has_safe = 'SafeUtil.safe(' in job_content or 'safe(' in job_content
        checks.append(check("Job: safe() used for string fields", has_safe, ""))

        # year/month/day set at end of po construction (appear after business field setters)
        year_set_pos = job_content.rfind('.setYear(')
        month_set_pos = job_content.rfind('.setMonth(')
        day_set_pos = job_content.rfind('.setDay(')
        # They should all exist and be in order
        ymd_set_ordered = (year_set_pos != -1 and month_set_pos != -1 and day_set_pos != -1 and
                          year_set_pos < month_set_pos < day_set_pos)
        checks.append(check("Job: setYear/setMonth/setDay called in order at end", ymd_set_ordered,
                           f"year={year_set_pos}, month={month_set_pos}, day={day_set_pos}"))

        # message null check
        has_message_check = bool(re.search(r'getMessage\(\)\s*(==\s*null|!=\s*null)', job_content) or
                                 'getMessage()' in job_content and 'isEmpty()' in job_content)
        checks.append(check("Job: message null/empty guard", has_message_check, ""))

    # ── 4. All 4 config.properties updated ───────────────────────────────────
    config_paths = [
        ws / "src/main/resources/config.properties",
        ws / "src/main/resources/dev/config.properties",
        ws / "src/main/resources/product/config.properties",
        ws / "src/main/resources/stage/config.properties",
    ]

    # Determine what biz key name should look like (flexible: routeCapacity or similar camelCase)
    # The agent must add 4 keys per config file
    for cfg_path in config_paths:
        cfg_name = str(cfg_path.relative_to(ws))
        cfg_content = load_file(cfg_path)
        if cfg_content is None:
            checks.append(check(f"Config exists: {cfg_name}", False, "File not found"))
            continue
        checks.append(check(f"Config exists: {cfg_name}", True, ""))

        # Topic key pattern: kafka.bus.{something}.topic = skynet_log_...route...capacity... (case-insensitive)
        has_topic_key = bool(re.search(
            r'kafka\.bus\.\w+\.topic\s*=\s*skynet_log.*[Rr]oute.*[Cc]apacity',
            cfg_content, re.IGNORECASE) or
            re.search(r'kafka\.bus\.\w+\.topic\s*=\s*skynet_log.*[Cc]apacity.*[Rr]oute',
                     cfg_content, re.IGNORECASE) or
            re.search(r'kafka\.bus\.routeCapacity\.topic', cfg_content) or
            re.search(r'kafka\.bus\.\w*[Rr]oute\w*\.topic', cfg_content) or
            re.search(r'kafka\.bus\.\w*[Cc]apacity\w*\.topic', cfg_content))
        checks.append(check(f"Config {cfg_name}: topic key added (kafka.bus.*.topic)", has_topic_key,
                           "Expected kafka.bus.{bizName}.topic key for route capacity topic"))

        # Group key pattern: travel.car.{something}.group
        has_group_key = bool(re.search(
            r'travel\.car\.\w+\.group\s*=\s*.+[Rr]oute.*[Cc]apacity',
            cfg_content, re.IGNORECASE) or
            re.search(r'travel\.car\.routeCapacity\.group', cfg_content) or
            re.search(r'travel\.car\.\w*[Rr]oute\w*\.group', cfg_content) or
            re.search(r'travel\.car\.\w*[Cc]apacity\w*\.group', cfg_content))
        checks.append(check(f"Config {cfg_name}: group key added (travel.car.*.group)", has_group_key,
                           "Expected travel.car.{bizName}.group key"))

        # StarRocks key: starrocks.fe.travel.common.{something}Monitor
        has_sr_key = bool(re.search(
            r'starrocks\.fe\.travel\.common\.\w*[Rr]oute\w*',
            cfg_content) or
            re.search(r'starrocks\.fe\.travel\.common\.\w*[Cc]apacity\w*',
                     cfg_content))
        checks.append(check(f"Config {cfg_name}: StarRocks key added (starrocks.fe.travel.common.*)", has_sr_key,
                           "Expected starrocks.fe.travel.common.{bizName}Monitor key"))

        # Hive key: hive.hive_train_ops.{something}Monitor
        has_hive_key = bool(re.search(
            r'hive\.hive_train_ops\.\w*[Rr]oute\w*',
            cfg_content) or
            re.search(r'hive\.hive_train_ops\.\w*[Cc]apacity\w*',
                     cfg_content))
        checks.append(check(f"Config {cfg_name}: Hive key added (hive.hive_train_ops.*)", has_hive_key,
                           "Expected hive.hive_train_ops.{bizName}Monitor key"))

    # ── 5. Naming convention checks ───────────────────────────────────────────
    # Job must be in src/main/java/com/ly/tms/job/
    if job_path:
        job_in_correct_dir = "com/ly/tms/job" in job_path or "com\\ly\\tms\\job" in job_path
        checks.append(check("Job file in correct directory (com/ly/tms/job/)", job_in_correct_dir, job_path))

    # MessageModel must be in po/carSupply/
    if mm_path:
        mm_in_correct_dir = "po/carSupply" in mm_path or "po\\carSupply" in mm_path
        checks.append(check("MessageModel in correct directory (po/carSupply/)", mm_in_correct_dir, mm_path))

    # Po must be in po/carSupply/
    if po_path:
        po_in_correct_dir = "po/carSupply" in po_path or "po\\carSupply" in po_path
        checks.append(check("Po in correct directory (po/carSupply/)", po_in_correct_dir, po_path))

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 3) if total > 0 else 0.0

    # Overall pass: must pass critical checks
    critical = [
        "MessageModel file exists",
        "Po file exists",
        "Job file exists",
        "Job: MODULE constant hardcoded as BUS_PUBLIC_ROUTE_CAPACITY_MONITOR",
        "Job: uses FlatMapFunction (list-expansion pattern)",
        "Job: LOG.error on logTime parse failure (A-scheme)",
        "Job: UUID fallback when id is null",
        "Job: list null/empty guard before iteration",
        "Job: cnt set to 1",
        "Job: setYear/setMonth/setDay called in order at end",
        "Po: st is first business field (before apmtraceid)",
        "Po: year, month, day fields exist and ordered",
    ]

    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )
    config_checks_passed = sum(
        1 for c in checks
        if "Config" in c["name"] and "topic key" in c["name"] and c["passed"]
    )
    all_4_configs_have_topic = config_checks_passed >= 4

    overall_passed = critical_passed and all_4_configs_have_topic and score >= 0.70

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))