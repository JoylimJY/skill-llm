#!/usr/bin/env python3
"""
Evaluation script for the TrueTime pharmaceutical scheduling task.
Checks that schedule_report.json was produced with correct structure and
adherence to TrueTime SKILL.md constraints.
"""

import sys
import json
import math
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta

checks = []
total_score = 0.0


def c(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0


def find_report(workspace):
    candidates = list(Path(workspace).rglob("schedule_report.json"))
    return candidates[0] if candidates else None


def load_json(path):
    with open(path) as f:
        return json.load(f)


def parse_iso(s):
    if not s:
        return None
    try:
        s2 = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s2)
    except Exception:
        return None


def is_utc_iso(s):
    if not s:
        return False
    return bool(re.search(r"(\+00:00$|Z$)", s))


def within_minutes(dt_str, minutes=10):
    """Check the timestamp is within `minutes` of now (reasonable freshness)."""
    dt = parse_iso(dt_str)
    if dt is None:
        return False
    now = datetime.now(timezone.utc)
    diff = abs((now - dt.astimezone(timezone.utc)).total_seconds())
    return diff < minutes * 60


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    score = 0.0

    # ── Find output file ──────────────────────────────────────────────────────
    report_path = find_report(workspace)
    found = report_path is not None
    score += c("output_file_exists", found, f"schedule_report.json {'found at ' + str(report_path) if found else 'NOT FOUND'}", 1.0)
    if not found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        data = load_json(report_path)
        score += c("valid_json", True, "File is valid JSON", 0.5)
    except Exception as e:
        score += c("valid_json", False, f"JSON parse error: {e}", 0.5)
        print(json.dumps({"passed": False, "score": score / 10.0, "checks": checks}))
        return

    # ── Top-level structure ───────────────────────────────────────────────────
    has_checkpoints = isinstance(data.get("checkpoints"), list) and len(data["checkpoints"]) >= 3
    score += c("has_three_checkpoints", has_checkpoints,
               f"Top-level 'checkpoints' list with >=3 entries: {has_checkpoints}", 0.5)

    if not has_checkpoints:
        print(json.dumps({"passed": False, "score": score / 10.0, "checks": checks}))
        return

    cps = {cp.get("id"): cp for cp in data["checkpoints"] if isinstance(cp, dict)}

    # ════════════════════════════════════════════════════════════════════════════
    # CP-1: Calendar-based quality review (2.5 months, Europe/Berlin)
    # ════════════════════════════════════════════════════════════════════════════
    cp1 = cps.get("CP-1", {})

    cp1_has_required = all(k in cp1 for k in [
        "now_utc", "target_utc", "target_user_tz",
        "delta_milliseconds", "time_source", "now_lunar", "target_lunar"
    ])
    score += c("cp1_required_fields", cp1_has_required,
               f"CP-1 has all required fields: {cp1_has_required}", 1.0)

    # now_utc should be recent
    cp1_now_fresh = within_minutes(cp1.get("now_utc"), 30)
    score += c("cp1_now_utc_is_recent", cp1_now_fresh,
               f"CP-1 now_utc is a real recent timestamp: {cp1.get('now_utc')}", 0.5)

    # target_utc should be roughly 2.5 months (75-78 days) from now_utc
    cp1_now = parse_iso(cp1.get("now_utc"))
    cp1_target = parse_iso(cp1.get("target_utc"))
    if cp1_now and cp1_target:
        cp1_now_utc = cp1_now.astimezone(timezone.utc)
        cp1_target_utc = cp1_target.astimezone(timezone.utc)
        cp1_delta_days = (cp1_target_utc - cp1_now_utc).total_seconds() / 86400
        # 2.5 months ≈ 75–78 days (calendar-aware, so depends on months involved)
        cp1_delta_ok = 70 <= cp1_delta_days <= 82
        score += c("cp1_target_approx_2point5months",
                   cp1_delta_ok,
                   f"CP-1 delta ~2.5 months: {cp1_delta_days:.1f} days (expected 70-82)", 1.5)
    else:
        score += c("cp1_target_approx_2point5months", False,
                   f"CP-1 cannot parse now_utc or target_utc", 1.5)

    # delta_milliseconds must be consistent with now_utc / target_utc
    if cp1_now and cp1_target:
        expected_ms = int((cp1_target_utc - cp1_now_utc).total_seconds() * 1000)
        reported_ms = cp1.get("delta_milliseconds")
        if isinstance(reported_ms, (int, float)):
            ms_diff = abs(int(reported_ms) - expected_ms)
            cp1_ms_ok = ms_diff < 2000  # within 2 seconds tolerance
            score += c("cp1_delta_ms_consistent", cp1_ms_ok,
                       f"CP-1 delta_ms consistent: reported={reported_ms}, expected={expected_ms}, diff={ms_diff}ms", 1.0)
        else:
            score += c("cp1_delta_ms_consistent", False,
                       f"CP-1 delta_milliseconds missing or not numeric: {reported_ms}", 1.0)

    # target_user_tz should reflect Europe/Berlin offset (UTC+1 or UTC+2 depending on DST)
    cp1_user_tz_str = cp1.get("target_user_tz", "")
    # Berlin in July/August area would be CEST = UTC+2; allow either +01 or +02
    cp1_tz_ok = bool(re.search(r"\+0[12]:00", cp1_user_tz_str))
    score += c("cp1_target_user_tz_berlin_offset", cp1_tz_ok,
               f"CP-1 target_user_tz has Berlin offset (+01 or +02): {cp1_user_tz_str}", 0.5)

    # time_source should be 'server' (default, NTP not requested)
    cp1_ts = cp1.get("time_source", "")
    score += c("cp1_time_source_server", cp1_ts == "server",
               f"CP-1 time_source is 'server': {cp1_ts}", 0.5)

    # lunar fields non-empty
    cp1_lunar_ok = bool(cp1.get("now_lunar")) and bool(cp1.get("target_lunar"))
    score += c("cp1_lunar_fields_present", cp1_lunar_ok,
               f"CP-1 lunar fields populated: now={cp1.get('now_lunar')}, target={cp1.get('target_lunar')}", 0.5)

    # ════════════════════════════════════════════════════════════════════════════
    # CP-2: Absolute cross-timezone (2026-09-15 10:00 Asia/Tokyo -> America/Chicago)
    # ════════════════════════════════════════════════════════════════════════════
    cp2 = cps.get("CP-2", {})

    cp2_has_required = all(k in cp2 for k in [
        "now_utc", "target_utc", "target_user_tz",
        "delta_milliseconds", "time_source", "now_lunar", "target_lunar"
    ])
    score += c("cp2_required_fields", cp2_has_required,
               f"CP-2 has all required fields: {cp2_has_required}", 1.0)

    # target_utc must be 2026-09-15T01:00:00Z (Tokyo UTC+9, so 10:00 local = 01:00 UTC)
    cp2_target_str = cp2.get("target_utc", "")
    cp2_target_dt = parse_iso(cp2_target_str)
    if cp2_target_dt:
        cp2_target_utc = cp2_target_dt.astimezone(timezone.utc)
        expected_utc = datetime(2026, 9, 15, 1, 0, 0, tzinfo=timezone.utc)
        cp2_utc_ok = cp2_target_utc == expected_utc
        score += c("cp2_target_utc_correct",
                   cp2_utc_ok,
                   f"CP-2 target_utc == 2026-09-15T01:00:00Z: got {cp2_target_utc.isoformat()}", 1.5)
    else:
        score += c("cp2_target_utc_correct", False,
                   f"CP-2 cannot parse target_utc: {cp2_target_str}", 1.5)

    # target_user_tz should be 2026-09-15T:20:00 CDT (UTC-5) = 2026-09-14T20:00:00-05:00
    # America/Chicago in September: CDT = UTC-5
    cp2_user_tz_str = cp2.get("target_user_tz", "")
    # 2026-09-15 01:00 UTC in Chicago CDT (UTC-5) = 2026-09-14 20:00 CDT
    # Accept either -05:00 offset with date 2026-09-14 at 20:00
    cp2_tz_ok = bool(re.search(r"2026-09-14T20:00:00-05:00", cp2_user_tz_str))
    score += c("cp2_target_user_tz_chicago_cdt",
               cp2_tz_ok,
               f"CP-2 target_user_tz is 2026-09-14T20:00:00-05:00 (Chicago CDT): got {cp2_user_tz_str}", 1.5)

    cp2_lunar_ok = bool(cp2.get("now_lunar")) and bool(cp2.get("target_lunar"))
    score += c("cp2_lunar_fields_present", cp2_lunar_ok,
               f"CP-2 lunar fields populated", 0.5)

    # ════════════════════════════════════════════════════════════════════════════
    # CP-3: NTP-verified +45 minutes, America/Chicago
    # ════════════════════════════════════════════════════════════════════════════
    cp3 = cps.get("CP-3", {})

    cp3_has_required = all(k in cp3 for k in [
        "now_utc", "target_utc", "target_user_tz",
        "delta_milliseconds", "time_source", "ntp_server",
        "now_lunar", "target_lunar"
    ])
    score += c("cp3_required_fields", cp3_has_required,
               f"CP-3 has all required fields (incl ntp_server): {cp3_has_required}", 1.0)

    # time_source MUST be 'ntp'
    cp3_ts = cp3.get("time_source", "")
    score += c("cp3_time_source_ntp", cp3_ts == "ntp",
               f"CP-3 time_source is 'ntp': {cp3_ts}", 1.5)

    # ntp_server must be non-empty
    cp3_ntp_srv = cp3.get("ntp_server", "")
    score += c("cp3_ntp_server_specified", bool(cp3_ntp_srv),
               f"CP-3 ntp_server is specified: {cp3_ntp_srv}", 0.5)

    # delta_milliseconds should be ~2700000 (45 min = 2,700,000 ms), allow ±60s
    cp3_ms = cp3.get("delta_milliseconds")
    if isinstance(cp3_ms, (int, float)):
        cp3_ms_ok = abs(cp3_ms - 2700000) < 60000
        score += c("cp3_delta_ms_45min", cp3_ms_ok,
                   f"CP-3 delta_ms ~2700000 (45min): got {cp3_ms}", 1.5)
    else:
        score += c("cp3_delta_ms_45min", False,
                   f"CP-3 delta_milliseconds missing or non-numeric: {cp3_ms}", 1.5)

    # now_utc should be recent
    cp3_now_fresh = within_minutes(cp3.get("now_utc"), 30)
    score += c("cp3_now_utc_is_recent", cp3_now_fresh,
               f"CP-3 now_utc is recent: {cp3.get('now_utc')}", 0.5)

    # target_user_tz should have a Chicago offset (-05:00 CDT or -06:00 CST depending on date)
    cp3_user_tz_str = cp3.get("target_user_tz", "")
    cp3_tz_ok = bool(re.search(r"-0[56]:00", cp3_user_tz_str))
    score += c("cp3_target_user_tz_chicago_offset", cp3_tz_ok,
               f"CP-3 target_user_tz has Chicago offset: {cp3_user_tz_str}", 0.5)

    cp3_lunar_ok = bool(cp3.get("now_lunar")) and bool(cp3.get("target_lunar"))
    score += c("cp3_lunar_fields_present", cp3_lunar_ok,
               f"CP-3 lunar fields populated", 0.5)

    # ── Final scoring ──────────────────────────────────────────────────────────
    max_score = 17.5
    final_score = min(1.0, score / max_score)
    passed = final_score >= 0.70

    print(json.dumps({
        "passed": passed,
        "score": round(final_score, 4),
        "checks": checks,
        "_debug": {
            "raw_score": score,
            "max_score": max_score,
            "report_path": str(report_path)
        }
    }, indent=2))


if __name__ == "__main__":
    main()