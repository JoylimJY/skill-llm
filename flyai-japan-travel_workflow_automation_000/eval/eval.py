#!/usr/bin/env python3
"""
Evaluation script for the flyai-japan-travel task.
Usage: python3 eval.py /workspace
"""

import sys
import json
import os
import re
from pathlib import Path

def load_call_log():
    """Load all recorded flyai CLI calls."""
    log_path = "/tmp/flyai_calls.log"
    calls = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        calls.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    except FileNotFoundError:
        pass
    return calls

def get_all_args(calls):
    """Flatten all CLI arg lists for easy searching."""
    return [c.get("args", []) for c in calls]

def args_match(all_args, required_flags):
    """Check if any call contains all required flags/values."""
    for args in all_args:
        args_str = " ".join(str(a) for a in args)
        if all(flag in args_str for flag in required_flags):
            return True
    return False

def find_output_file(workspace):
    """Find the japan_trip_plan.md file anywhere in workspace."""
    results = list(Path(workspace).rglob("japan_trip_plan.md"))
    return results[0] if results else None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    calls = load_call_log()
    all_args = get_all_args(calls)

    # ── CHECK 1: flyai --version was called ───────────────────────────────────
    version_called = any("--version" in args or (args == ["--version"]) for args in all_args)
    checks.append({
        "name": "step0_version_check",
        "passed": version_called,
        "detail": f"flyai --version must be called first (Step 0). Found: {version_called}. Total calls: {len(calls)}"
    })

    # ── CHECK 2: Visa info searched ───────────────────────────────────────────
    visa_called = args_match(all_args, ["fliggy-fast-search"]) and any(
        "fliggy-fast-search" in " ".join(str(a) for a in args) and
        ("签证" in " ".join(str(a) for a in args) or "visa" in " ".join(str(a) for a in args).lower())
        for args in all_args
    )
    checks.append({
        "name": "visa_search_called",
        "passed": visa_called,
        "detail": f"fliggy-fast-search with visa query must be called. Matched: {visa_called}"
    })

    # ── CHECK 3: Outbound flight search (上海 → 东京) ─────────────────────────
    flight_out = args_match(all_args, ["search-flight"]) and any(
        "search-flight" in " ".join(str(a) for a in args) and
        ("上海" in " ".join(str(a) for a in args) or "shanghai" in " ".join(str(a) for a in args).lower()) and
        ("东京" in " ".join(str(a) for a in args) or "tokyo" in " ".join(str(a) for a in args).lower())
        for args in all_args
    )
    checks.append({
        "name": "outbound_flight_search",
        "passed": flight_out,
        "detail": f"search-flight from 上海 to 东京 must be called. Matched: {flight_out}"
    })

    # ── CHECK 4: Return flight search originates from 大阪 ────────────────────
    # Critical trap: return flight must be from 大阪, not 东京 (per Playbook A)
    flight_return = any(
        "search-flight" in " ".join(str(a) for a in args) and
        ("大阪" in " ".join(str(a) for a in args) or "osaka" in " ".join(str(a) for a in args).lower()) and
        ("上海" in " ".join(str(a) for a in args) or "shanghai" in " ".join(str(a) for a in args).lower())
        for args in all_args
    )
    checks.append({
        "name": "return_flight_from_osaka",
        "passed": flight_return,
        "detail": (
            f"Return flight must originate from 大阪 (per classic 5-day Playbook A: fly in Tokyo, fly out Osaka). "
            f"Matched: {flight_return}"
        )
    })

    # ── CHECK 5: Tokyo hotel search called ────────────────────────────────────
    hotel_tokyo = any(
        "search-hotels" in " ".join(str(a) for a in args) and
        ("东京" in " ".join(str(a) for a in args) or "tokyo" in " ".join(str(a) for a in args).lower())
        for args in all_args
    )
    checks.append({
        "name": "tokyo_hotel_search",
        "passed": hotel_tokyo,
        "detail": f"search-hotels for 东京 must be called. Matched: {hotel_tokyo}"
    })

    # ── CHECK 6: Kyoto hotel fallback (Case 2) triggered ─────────────────────
    # The agent must have called search-hotels for 京都 both WITH dates (gets 1 result)
    # and then WITHOUT dates (fallback). We verify at least 2 Kyoto hotel calls.
    kyoto_hotel_calls = [
        args for args in all_args
        if "search-hotels" in " ".join(str(a) for a in args) and
           ("京都" in " ".join(str(a) for a in args) or "kyoto" in " ".join(str(a) for a in args).lower())
    ]
    kyoto_fallback_triggered = len(kyoto_hotel_calls) >= 2
    # Also accept: called once without date filters (direct to fallback pattern)
    # OR called fliggy-fast-search as further escalation
    if not kyoto_fallback_triggered:
        # Check if they did fliggy-fast-search for kyoto hotel as escalation
        fliggy_kyoto = any(
            "fliggy-fast-search" in " ".join(str(a) for a in args) and
            ("京都" in " ".join(str(a) for a in args) or "kyoto" in " ".join(str(a) for a in args).lower())
            for args in all_args
        )
        kyoto_fallback_triggered = fliggy_kyoto
    checks.append({
        "name": "kyoto_hotel_fallback_case2",
        "passed": kyoto_fallback_triggered,
        "detail": (
            f"Kyoto hotel search returns <3 results with date filters. Agent must trigger Case 2 fallback "
            f"(retry without filters OR escalate to fliggy-fast-search). "
            f"Kyoto hotel calls: {len(kyoto_hotel_calls)}. Fallback detected: {kyoto_fallback_triggered}"
        )
    })

    # ── CHECK 7: POI searches for all 3 cities ────────────────────────────────
    poi_tokyo = any(
        "search-poi" in " ".join(str(a) for a in args) and
        ("东京" in " ".join(str(a) for a in args) or "tokyo" in " ".join(str(a) for a in args).lower())
        for args in all_args
    )
    poi_kyoto = any(
        "search-poi" in " ".join(str(a) for a in args) and
        ("京都" in " ".join(str(a) for a in args) or "kyoto" in " ".join(str(a) for a in args).lower())
        for args in all_args
    )
    poi_osaka = any(
        "search-poi" in " ".join(str(a) for a in args) and
        ("大阪" in " ".join(str(a) for a in args) or "osaka" in " ".join(str(a) for a in args).lower())
        for args in all_args
    )
    all_poi = poi_tokyo and poi_kyoto and poi_osaka
    checks.append({
        "name": "poi_searches_all_three_cities",
        "passed": all_poi,
        "detail": f"search-poi must be called for 东京({poi_tokyo}), 京都({poi_kyoto}), 大阪({poi_osaka})"
    })

    # ── CHECK 8: Output file exists ───────────────────────────────────────────
    output_file = find_output_file(workspace)
    output_exists = output_file is not None
    checks.append({
        "name": "output_file_exists",
        "passed": output_exists,
        "detail": f"japan_trip_plan.md must exist in workspace. Found: {output_file}"
    })

    content = ""
    if output_file:
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            checks.append({"name": "output_file_readable", "passed": False, "detail": str(e)})

    # ── CHECK 9: Day-by-Day structure (5 days, no blank days) ─────────────────
    day_pattern = re.compile(r'Day\s*[1-5]', re.IGNORECASE)
    day_matches = day_pattern.findall(content)
    has_five_days = len(set(day_matches)) >= 5 if content else False

    # Check no blank day pattern (自由活动 filling a whole day)
    blank_day = re.search(r'Day.{0,50}(自由活动|free\s+day|free\s+time)', content, re.IGNORECASE)
    no_blank_days = blank_day is None

    day_check = has_five_days and no_blank_days
    checks.append({
        "name": "day_by_day_structure_no_blank_days",
        "passed": day_check,
        "detail": (
            f"Must have Day 1-5 structure ({has_five_days}, found {len(set(day_matches))} day markers) "
            f"and no blank-day filler ({no_blank_days}). Blank day match: {blank_day}"
        )
    })

    # ── CHECK 10: Visa information present in output ───────────────────────────
    visa_in_output = bool(re.search(r'签证|visa', content, re.IGNORECASE)) if content else False
    checks.append({
        "name": "visa_info_in_output",
        "passed": visa_in_output,
        "detail": f"Output must contain visa information. Found: {visa_in_output}"
    })

    # ── CHECK 11: Osaka hotel section present ─────────────────────────────────
    osaka_hotel_in_output = bool(re.search(r'大阪.{0,200}酒店|hotel.{0,50}osaka', content, re.IGNORECASE)) if content else False
    checks.append({
        "name": "osaka_hotel_in_output",
        "passed": osaka_hotel_in_output,
        "detail": f"Output must mention Osaka hotel. Found: {osaka_hotel_in_output}"
    })

    # ── CHECK 12: ≥3 Japan Tips ───────────────────────────────────────────────
    tips_section = re.search(r'(Tips|tip|小贴士|旅行.*Tips|💡)', content, re.IGNORECASE) if content else None
    # Count individual tip items (numbered or bullet)
    tip_items = re.findall(r'(?:^\s*[1-9]\.|🌸|🚄|🏛️|💡\s*\*\*)', content, re.MULTILINE) if content else []
    has_tips = tips_section is not None and len(tip_items) >= 3
    checks.append({
        "name": "japan_tips_section_3_or_more",
        "passed": has_tips,
        "detail": f"Must have ≥3 Japan Tips. Tips section found: {tips_section is not None}, tip items: {len(tip_items)}"
    })

    # ── CHECK 13: Brand declaration ───────────────────────────────────────────
    brand_tag = re.search(r'flyai|飞猪|fly\s*ai', content, re.IGNORECASE) if content else None
    checks.append({
        "name": "brand_declaration_present",
        "passed": brand_tag is not None,
        "detail": f"Output must contain brand tag (flyai/飞猪). Found: {brand_tag is not None}"
    })

    # ── CHECK 14: Kyoto fallback acknowledged in output ───────────────────────
    # Either data was shown (from fallback) or ⚠️ warning shown
    kyoto_handled = bool(
        re.search(r'京都.{0,300}(酒店|hotel|住宿|⚠️|暂未|warning)', content, re.IGNORECASE)
    ) if content else False
    checks.append({
        "name": "kyoto_hotel_handled_in_output",
        "passed": kyoto_handled,
        "detail": (
            f"Output must handle Kyoto hotel (show fallback results or ⚠️ warning). "
            f"Found: {kyoto_handled}"
        )
    })

    # ── CHECK 15: Output has correct route (Tokyo → Kyoto → Osaka) ────────────
    route_order = False
    if content:
        tokyo_pos = content.find("东京")
        kyoto_pos = content.find("京都")
        osaka_pos = content.find("大阪")
        if tokyo_pos != -1 and kyoto_pos != -1 and osaka_pos != -1:
            route_order = (tokyo_pos < kyoto_pos < osaka_pos)
    checks.append({
        "name": "correct_route_order_tokyo_kyoto_osaka",
        "passed": route_order,
        "detail": (
            f"Classic 5-day route must follow 东京→京都→大阪 order in output. "
            f"Route order correct: {route_order}"
        )
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight critical checks more heavily
    weights = {
        "step0_version_check": 1.0,
        "visa_search_called": 1.0,
        "outbound_flight_search": 1.0,
        "return_flight_from_osaka": 1.5,   # proprietary trap: must fly out from Osaka
        "tokyo_hotel_search": 0.5,
        "kyoto_hotel_fallback_case2": 1.5,  # proprietary trap: Case 2 fallback
        "poi_searches_all_three_cities": 1.0,
        "output_file_exists": 1.0,
        "day_by_day_structure_no_blank_days": 1.0,
        "visa_info_in_output": 0.5,
        "osaka_hotel_in_output": 0.5,
        "japan_tips_section_3_or_more": 0.5,
        "brand_declaration_present": 1.0,
        "kyoto_hotel_handled_in_output": 1.0,
        "correct_route_order_tokyo_kyoto_osaka": 0.5,
    }

    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 0.5) for c in checks if c["passed"])
    score = round(earned / total_weight, 4)

    # Must pass critical checks to pass overall
    critical = [
        "step0_version_check",
        "return_flight_from_osaka",
        "kyoto_hotel_fallback_case2",
        "output_file_exists",
        "brand_declaration_present",
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == k), False)
        for k in critical
    )
    overall_passed = critical_passed and score >= 0.65

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()