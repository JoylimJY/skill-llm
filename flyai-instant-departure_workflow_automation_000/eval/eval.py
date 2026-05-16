import json
import sys
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    workspace_path = Path(workspace)
    checks = []

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── 1. Read mock call log ────────────────────────────────────────────────
    log_path = workspace_path / ".flyai_mock_logs" / "calls.log"
    log_content = ""
    try:
        log_content = log_path.read_text(encoding="utf-8")
        add_check(
            "flyai_cli_was_invoked",
            True,
            f"Call log found with {len(log_content.splitlines())} lines."
        )
    except Exception as e:
        add_check("flyai_cli_was_invoked", False, f"Call log not found or unreadable: {e}")

    # ── 2. Check NODE_TLS_REJECT_UNAUTHORIZED=0 was used ────────────────────
    try:
        tls_lines = [l for l in log_content.splitlines() if "TLS_REJECT=0" in l]
        passed = len(tls_lines) >= 1
        add_check(
            "tls_reject_unauthorized_set",
            passed,
            f"Found {len(tls_lines)} calls with NODE_TLS_REJECT_UNAUTHORIZED=0. "
            "Required by workflow.md for SSL bypass."
        )
    except Exception as e:
        add_check("tls_reject_unauthorized_set", False, f"Error checking TLS flag: {e}")

    # ── 3. search-flight with --sort-type 6 ─────────────────────────────────
    try:
        sort_type_lines = [l for l in log_content.splitlines()
                           if "FLIGHT_SORT_TYPE" in l and "|6" in l]
        passed = len(sort_type_lines) >= 1
        add_check(
            "flight_sort_type_6_used",
            passed,
            f"Found {len(sort_type_lines)} flight searches with --sort-type 6. "
            "This is the proprietary sort parameter from workflow.md."
        )
    except Exception as e:
        add_check("flight_sort_type_6_used", False, f"Error checking sort-type: {e}")

    # ── 4. search-hotel with --sort rate_desc ───────────────────────────────
    try:
        hotel_sort_lines = [l for l in log_content.splitlines()
                            if "HOTEL_SORT" in l and "rate_desc" in l]
        passed = len(hotel_sort_lines) >= 1
        add_check(
            "hotel_sort_rate_desc_used",
            passed,
            f"Found {len(hotel_sort_lines)} hotel searches with --sort rate_desc. "
            "Required by workflow.md step 3.3."
        )
    except Exception as e:
        add_check("hotel_sort_rate_desc_used", False, f"Error checking hotel sort: {e}")

    # ── 5. search-poi with --poi-level 4 ────────────────────────────────────
    try:
        poi_level_lines = [l for l in log_content.splitlines()
                           if "POI_LEVEL" in l and "|4" in l]
        passed = len(poi_level_lines) >= 1
        add_check(
            "poi_level_4_used",
            passed,
            f"Found {len(poi_level_lines)} POI searches with --poi-level 4. "
            "Required by workflow.md step 3.4."
        )
    except Exception as e:
        add_check("poi_level_4_used", False, f"Error checking poi-level: {e}")

    # ── 6. At least 2 destinations searched for flights ─────────────────────
    try:
        flight_dest_lines = [l for l in log_content.splitlines() if "FLIGHT_DEST|" in l]
        destinations = set()
        for line in flight_dest_lines:
            parts = line.split("FLIGHT_DEST|")
            if len(parts) > 1:
                destinations.add(parts[1].strip())
        passed = len(destinations) >= 2
        add_check(
            "multiple_destinations_searched",
            passed,
            f"Agent searched {len(destinations)} distinct destinations: {destinations}. "
            "Workflow requires searching multiple hot destinations for 北京 departure."
        )
    except Exception as e:
        add_check("multiple_destinations_searched", False, f"Error checking destinations: {e}")

    # ── 7. Output file exists ────────────────────────────────────────────────
    output_file = None
    try:
        candidates = list(workspace_path.rglob("instant_departure_plan.md"))
        if candidates:
            output_file = candidates[0]
            add_check(
                "output_file_exists",
                True,
                f"Found output file at: {output_file}"
            )
        else:
            add_check(
                "output_file_exists",
                False,
                "No file named 'instant_departure_plan.md' found anywhere in workspace."
            )
    except Exception as e:
        add_check("output_file_exists", False, f"Error searching for output file: {e}")

    # ── 8–14: Content checks on output file ─────────────────────────────────
    plan_content = ""
    if output_file:
        try:
            plan_content = output_file.read_text(encoding="utf-8")
        except Exception as e:
            add_check("output_file_readable", False, f"Cannot read output file: {e}")

    # 8. Contains the ━━━ separator (proprietary format)
    try:
        has_separator = "━━━" in plan_content
        add_check(
            "output_has_separator_format",
            has_separator,
            "Output must contain ━━━ separator lines as specified in workflow.md template."
        )
    except Exception as e:
        add_check("output_has_separator_format", False, str(e))

    # 9. Contains departure city 北京
    try:
        has_beijing = "北京" in plan_content
        add_check(
            "output_mentions_departure_city",
            has_beijing,
            "Output must reference 北京 as departure city (from user profile ~/.flyai/user-profile.md)."
        )
    except Exception as e:
        add_check("output_mentions_departure_city", False, str(e))

    # 10. Contains flight booking link (jumpUrl from fliggy.com)
    try:
        has_flight_link = "fliggy.com/flight" in plan_content or "jumpUrl" in plan_content
        add_check(
            "output_contains_flight_jumpurl",
            has_flight_link,
            "Output must contain flight booking links (jumpUrl from search-flight results)."
        )
    except Exception as e:
        add_check("output_contains_flight_jumpurl", False, str(e))

    # 11. Contains hotel booking link
    try:
        has_hotel_link = "fliggy.com/hotel" in plan_content or (
            "jumpUrl" in plan_content and ("酒店" in plan_content or "hotel" in plan_content.lower())
        )
        add_check(
            "output_contains_hotel_jumpurl",
            has_hotel_link,
            "Output must contain hotel booking links (jumpUrl from search-hotel results)."
        )
    except Exception as e:
        add_check("output_contains_hotel_jumpurl", False, str(e))

    # 12. Contains POI / attractions information
    try:
        has_poi = any(kw in plan_content for kw in [
            "fliggy.com/poi", "景点", "📍", "可玩", "历史", "文化", "街", "博物馆"
        ])
        add_check(
            "output_contains_poi_info",
            has_poi,
            "Output must contain POI/attraction information from search-poi results."
        )
    except Exception as e:
        add_check("output_contains_poi_info", False, str(e))

    # 13. Contains price / 总计 summary
    try:
        has_price = any(kw in plan_content for kw in ["¥", "总计", "价格", "总价", "元"])
        add_check(
            "output_contains_price_summary",
            has_price,
            "Output must include total price estimate per person."
        )
    except Exception as e:
        add_check("output_contains_price_summary", False, str(e))

    # 14. Contains at least one destination section with emoji markers
    try:
        emoji_patterns = ["1️⃣", "2️⃣", "✈️", "🏨"]
        has_emoji = any(ep in plan_content for ep in emoji_patterns)
        add_check(
            "output_uses_emoji_format",
            has_emoji,
            "Output must use emoji markers as defined in the workflow.md output template "
            "(e.g., 1️⃣, ✈️, 🏨, 📍)."
        )
    except Exception as e:
        add_check("output_uses_emoji_format", False, str(e))

    # 15. User profile was read (profile mentions Beijing, output should reflect it)
    try:
        # The user profile has 偏好类型: 历史文化、美食、城市探索
        # A proper agent reading the profile would note these preferences
        profile_reflected = (
            "历史" in plan_content or
            "文化" in plan_content or
            "美食" in plan_content or
            "首都" in plan_content or
            "北京" in plan_content
        )
        add_check(
            "user_profile_read_and_reflected",
            profile_reflected,
            "Output should reflect user profile data read from ~/.flyai/user-profile.md "
            "(e.g., 北京 as home city, 历史文化/美食 preferences)."
        )
    except Exception as e:
        add_check("user_profile_read_and_reflected", False, str(e))

    # 16. npm install was attempted (check if node_modules or npm cache indicates install)
    # We check if any CALL line shows flyai being invoked (indirect evidence install happened)
    # More direct: check if "npm" appears in shell history or if the package was actually attempted
    # We'll check via the log - if flyai was called multiple times, install was done first
    try:
        call_lines = [l for l in log_content.splitlines() if l.startswith("CALL|")]
        passed = len(call_lines) >= 3  # At minimum: flight x1, hotel x1, poi x1
        add_check(
            "minimum_three_api_calls_made",
            passed,
            f"Agent made {len(call_lines)} total flyai CLI calls. "
            "Expected at least 3 (search-flight, search-hotel, search-poi)."
        )
    except Exception as e:
        add_check("minimum_three_api_calls_made", False, str(e))

    # ── Final scoring ────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])

    # Weight critical checks more heavily
    critical_checks = [
        "flyai_cli_was_invoked",
        "flight_sort_type_6_used",
        "hotel_sort_rate_desc_used",
        "poi_level_4_used",
        "output_file_exists",
        "output_has_separator_format",
        "output_contains_flight_jumpurl",
    ]
    critical_passed = sum(
        1 for c in checks if c["name"] in critical_checks and c["passed"]
    )
    critical_total = len(critical_checks)

    # Score: 50% weight on critical, 50% on all
    score = 0.5 * (critical_passed / critical_total) + 0.5 * (passed_count / total)
    overall_passed = critical_passed >= 5 and passed_count >= int(total * 0.7)

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(ws)
    print(json.dumps(result, ensure_ascii=False, indent=2))