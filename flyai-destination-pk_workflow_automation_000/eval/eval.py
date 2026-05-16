import sys
import json
import re
import os
from pathlib import Path

def run_checks(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # =========================================================
    # CHECK 1: Report file exists at the specified location
    # =========================================================
    report_path = workspace / "projects/travel-agency/clients/zhang_wei/destination_pk_report.md"
    
    # Also search recursively in case agent placed it elsewhere
    found_reports = list(workspace.rglob("destination_pk_report.md"))
    
    report_content = ""
    report_found = False
    
    try:
        if report_path.exists():
            report_content = report_path.read_text(encoding="utf-8")
            report_found = True
            checks.append({
                "name": "report_file_at_correct_location",
                "passed": True,
                "detail": f"destination_pk_report.md found at expected path: {report_path}"
            })
            total_score += 0.10
        elif found_reports:
            report_content = found_reports[0].read_text(encoding="utf-8")
            report_found = True
            checks.append({
                "name": "report_file_at_correct_location",
                "passed": False,
                "detail": f"File found at {found_reports[0]} but expected at {report_path}"
            })
        else:
            checks.append({
                "name": "report_file_at_correct_location",
                "passed": False,
                "detail": "destination_pk_report.md not found anywhere in workspace"
            })
    except Exception as e:
        checks.append({
            "name": "report_file_at_correct_location",
            "passed": False,
            "detail": f"Error reading report file: {e}"
        })

    if not report_found:
        # Cannot proceed with content checks
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    # =========================================================
    # CHECK 2: All three destinations present in report
    # =========================================================
    destinations = ["东京", "首尔", "新加坡"]
    dest_found = [d for d in destinations if d in report_content]
    try:
        all_dests_present = len(dest_found) == 3
        checks.append({
            "name": "all_three_destinations_present",
            "passed": all_dests_present,
            "detail": f"Found destinations: {dest_found}. Expected all of: {destinations}"
        })
        if all_dests_present:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "all_three_destinations_present", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 3: Proper border/separator characters used (━━━ and ─────)
    # =========================================================
    try:
        has_thick_border = "━" in report_content
        has_thin_border = "─" in report_content
        border_check = has_thick_border and has_thin_border
        checks.append({
            "name": "proprietary_border_characters",
            "passed": border_check,
            "detail": f"Has ━ borders: {has_thick_border}, Has ─ borders: {has_thin_border}. "
                      f"The skill requires specific Unicode box-drawing chars (━━━ and ─────)."
        })
        if border_check:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "proprietary_border_characters", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 4: Flight data (✈) present for each destination
    # =========================================================
    try:
        has_flight_section = "✈" in report_content or "机票" in report_content
        has_flight_prices = bool(re.search(r'¥[\d,]+', report_content))
        flight_check = has_flight_section and has_flight_prices
        checks.append({
            "name": "flight_data_included",
            "passed": flight_check,
            "detail": f"Flight section present: {has_flight_section}, Price data present: {has_flight_prices}"
        })
        if flight_check:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "flight_data_included", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 5: Hotel data (🏨) present
    # =========================================================
    try:
        has_hotel_section = "🏨" in report_content or "酒店" in report_content
        checks.append({
            "name": "hotel_data_included",
            "passed": has_hotel_section,
            "detail": f"Hotel section present: {has_hotel_section}"
        })
        if has_hotel_section:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "hotel_data_included", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 6: POI/Attraction data (📍) present with counts
    # =========================================================
    try:
        has_poi_section = "📍" in report_content or "景点" in report_content or "POI" in report_content
        has_poi_counts = bool(re.search(r'(6[0-9]|5[0-9]|[0-9]+)\s*(个|个POI)', report_content))
        poi_check = has_poi_section
        checks.append({
            "name": "poi_data_included",
            "passed": poi_check,
            "detail": f"POI section present: {has_poi_section}, POI count data present: {has_poi_counts}"
        })
        if poi_check:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "poi_data_included", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 7: Star ratings (⭐) for attraction categories
    # =========================================================
    try:
        star_count = report_content.count("⭐")
        has_stars = star_count >= 5  # At least 5 star ratings across categories
        category_keywords = ["寺庙", "自然", "网红", "水上"]
        found_categories = [k for k in category_keywords if k in report_content]
        stars_check = has_stars and len(found_categories) >= 2
        checks.append({
            "name": "star_ratings_for_categories",
            "passed": stars_check,
            "detail": f"Star count: {star_count}, Attraction categories found: {found_categories}. "
                      f"Requires ⭐ ratings for attraction type categories per core-workflow.md step 3."
        })
        if stars_check:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "star_ratings_for_categories", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 8: Total cost estimate present (💰)
    # =========================================================
    try:
        has_total_cost = "💰" in report_content or "预估总花费" in report_content or "总花费" in report_content
        has_cost_note = "餐饮" in report_content or "不含" in report_content
        cost_check = has_total_cost
        checks.append({
            "name": "total_cost_estimate_with_note",
            "passed": cost_check,
            "detail": f"Total cost section: {has_total_cost}, Excludes dining note: {has_cost_note}. "
                      f"Per core-workflow.md, must show 预估总花费 and note 不含餐饮购物."
        })
        if cost_check:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "total_cost_estimate_with_note", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 9: Budget-preference recommendation - 首尔 should win
    # (首尔 has cheapest flights ¥1350-1680 and cheapest hotels ¥180-980)
    # =========================================================
    try:
        has_recommendation = "🏆" in report_content or "推荐" in report_content or "综合推荐" in report_content
        has_budget_winner = (
            ("预算" in report_content and "首尔" in report_content) or
            ("经济" in report_content and "首尔" in report_content) or
            re.search(r'预算[^。\n]*首尔|首尔[^。\n]*预算', report_content) is not None
        )
        # Check that the recommendation section exists and mentions Seoul for budget
        rec_check = has_recommendation and has_budget_winner
        checks.append({
            "name": "budget_recommendation_correct",
            "passed": rec_check,
            "detail": f"Recommendation section: {has_recommendation}, "
                      f"首尔 recommended for budget: {has_budget_winner}. "
                      f"Per core-workflow.md step 5: for 预算优先, must recommend lowest total cost (首尔)."
        })
        if rec_check:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "budget_recommendation_correct", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 10: 🆚 header and "vs" format present (3-way PK format)
    # =========================================================
    try:
        has_vs_header = "🆚" in report_content and "vs" in report_content.lower()
        has_pk_label = "PK" in report_content or "全维度" in report_content
        format_check = has_vs_header and has_pk_label
        checks.append({
            "name": "three_way_pk_header_format",
            "passed": format_check,
            "detail": f"🆚 vs header: {has_vs_header}, PK/全维度 label: {has_pk_label}. "
                      f"Per SKILL.md 三地对比扩展格式, 3-way comparison needs 🆚 ... vs ... · 全维度PK header."
        })
        if format_check:
            total_score += 0.10
    except Exception as e:
        checks.append({"name": "three_way_pk_header_format", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 11: User profile file exists and was read
    # =========================================================
    try:
        profile_path = Path.home() / ".flyai" / "user-profile.md"
        profile_exists = profile_path.exists()
        checks.append({
            "name": "user_profile_file_accessible",
            "passed": profile_exists,
            "detail": f"~/.flyai/user-profile.md exists: {profile_exists}. "
                      f"Per user-profile-storage.md, agent should read file-mode profile."
        })
        # This is a bonus/informational check, partial score
        if profile_exists:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "user_profile_file_accessible", "passed": False, "detail": str(e)})

    # =========================================================
    # CHECK 12: Next steps action buttons present
    # =========================================================
    try:
        has_next_steps = "下一步" in report_content or "具体航班" in report_content or "高分酒店" in report_content
        checks.append({
            "name": "next_steps_section_present",
            "passed": has_next_steps,
            "detail": f"Next steps / action buttons section present: {has_next_steps}. "
                      f"Per core-workflow.md Step 4 output template, must include 👉 下一步 action section."
        })
        if has_next_steps:
            total_score += 0.05
    except Exception as e:
        checks.append({"name": "next_steps_section_present", "passed": False, "detail": str(e)})

    # =========================================================
    # Normalize score to [0,1]
    # =========================================================
    total_score = min(total_score, 1.0)
    passed_checks = sum(1 for c in checks if c["passed"])
    all_passed = passed_checks >= 9  # Pass if at least 9/12 checks pass

    return {
        "passed": all_passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))