import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0

    # --- Locate the output file ---
    report_files = list(Path(workspace_dir).rglob("china_rivers_report.json"))

    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "china_rivers_report.json not found anywhere in workspace"}]
        }

    report_path = report_files[0]

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_parseable", "passed": False, "detail": f"Failed to parse JSON: {e}"}]
        }

    checks.append({"name": "file_exists_and_parseable", "passed": True, "detail": str(report_path)})
    total_score += 5.0

    # ================================================================
    # CHECK 1: seven_systems array presence and count
    # ================================================================
    try:
        systems = data.get("seven_systems", [])
        has_seven = isinstance(systems, list) and len(systems) == 7
        checks.append({
            "name": "seven_systems_count",
            "passed": has_seven,
            "detail": f"Found {len(systems)} systems, expected 7"
        })
        if has_seven:
            total_score += 10.0
    except Exception as e:
        checks.append({"name": "seven_systems_count", "passed": False, "detail": str(e)})

    # ================================================================
    # CHECK 2: Correct north-to-south ordering of systems
    # ================================================================
    EXPECTED_ORDER = ["松花江水系", "辽河水系", "海河水系", "黄河水系", "淮河水系", "长江水系", "珠江水系"]
    try:
        systems = data.get("seven_systems", [])
        # Extract names, allowing flexible field names
        def get_name(item):
            for key in ["name", "system_name", "水系", "系统名", "名称"]:
                if key in item:
                    return item[key]
            return str(item)

        actual_names = [get_name(s) for s in systems]
        order_correct = True
        order_detail = []
        for i, (expected, actual) in enumerate(zip(EXPECTED_ORDER, actual_names)):
            match = expected in actual or actual in expected
            if not match:
                order_correct = False
                order_detail.append(f"Position {i+1}: expected '{expected}', got '{actual}'")

        checks.append({
            "name": "seven_systems_north_to_south_order",
            "passed": order_correct and len(actual_names) == 7,
            "detail": f"Order issues: {order_detail}" if order_detail else f"Correct order: {actual_names}"
        })
        if order_correct and len(actual_names) == 7:
            total_score += 15.0
    except Exception as e:
        checks.append({"name": "seven_systems_north_to_south_order", "passed": False, "detail": str(e)})

    # ================================================================
    # CHECK 3: Exact basin area values for all 7 systems
    # ================================================================
    EXPECTED_AREAS = {
        "松花江水系": 55.68,
        "辽河水系": 22.9,
        "海河水系": 26.46,
        "黄河水系": 75.2,
        "淮河水系": 27.0,
        "长江水系": 180.0,
        "珠江水系": 45.37,
    }

    try:
        systems = data.get("seven_systems", [])
        area_matches = 0
        area_details = []
        for item in systems:
            item_str = json.dumps(item, ensure_ascii=False)
            for sys_name, expected_area in EXPECTED_AREAS.items():
                if sys_name in item_str or any(part in item_str for part in sys_name.split("水系")):
                    # Try to find the area value
                    found_area = None
                    for key in ["basin_area", "area", "basin_area_km2", "流域面积", "面积"]:
                        if key in item:
                            try:
                                found_area = float(str(item[key]).replace("万km²", "").replace("万", "").strip())
                            except:
                                pass
                    if found_area is not None:
                        if abs(found_area - expected_area) < 0.01:
                            area_matches += 1
                            area_details.append(f"{sys_name}: ✓ ({found_area})")
                        else:
                            area_details.append(f"{sys_name}: ✗ (got {found_area}, expected {expected_area})")
                    break

        area_passed = area_matches >= 6  # Allow 1 miss
        checks.append({
            "name": "basin_area_values_accuracy",
            "passed": area_passed,
            "detail": f"{area_matches}/7 correct. Details: {'; '.join(area_details)}"
        })
        if area_matches == 7:
            total_score += 20.0
        elif area_matches >= 6:
            total_score += 15.0
        elif area_matches >= 4:
            total_score += 8.0
    except Exception as e:
        checks.append({"name": "basin_area_values_accuracy", "passed": False, "detail": str(e)})

    # ================================================================
    # CHECK 4: All 7 systems flow into Pacific Ocean (太平洋)
    # ================================================================
    try:
        systems = data.get("seven_systems", [])
        pacific_count = 0
        for item in systems:
            item_str = json.dumps(item, ensure_ascii=False)
            if "太平洋" in item_str:
                pacific_count += 1

        pacific_passed = pacific_count == 7
        checks.append({
            "name": "all_systems_flow_to_pacific",
            "passed": pacific_passed,
            "detail": f"{pacific_count}/7 systems correctly marked as flowing to 太平洋"
        })
        if pacific_passed:
            total_score += 10.0
    except Exception as e:
        checks.append({"name": "all_systems_flow_to_pacific", "passed": False, "detail": str(e)})

    # ================================================================
    # CHECK 5: major_rivers_detail - presence of 长江, 黄河, 珠江
    # ================================================================
    try:
        major = data.get("major_rivers_detail", {})
        has_changjiang = any("长江" in str(k) or "长江" in str(v) for k, v in major.items()) if isinstance(major, dict) else "长江" in json.dumps(major, ensure_ascii=False)
        has_huanghe = any("黄河" in str(k) or "黄河" in str(v) for k, v in major.items()) if isinstance(major, dict) else "黄河" in json.dumps(major, ensure_ascii=False)
        has_zhujiang = any("珠江" in str(k) or "珠江" in str(v) for k, v in major.items()) if isinstance(major, dict) else "珠江" in json.dumps(major, ensure_ascii=False)

        major_present = has_changjiang and has_huanghe and has_zhujiang
        checks.append({
            "name": "major_rivers_detail_presence",
            "passed": major_present,
            "detail": f"长江:{has_changjiang}, 黄河:{has_huanghe}, 珠江:{has_zhujiang}"
        })
        if major_present:
            total_score += 5.0
    except Exception as e:
        checks.append({"name": "major_rivers_detail_presence", "passed": False, "detail": str(e)})

    # ================================================================
    # CHECK 6: Correct ocean/sea names for the 3 major rivers
    # 长江 -> 东海, 黄河 -> 渤海, 珠江 -> 南海
    # ================================================================
    data_str = json.dumps(data, ensure_ascii=False)

    try:
        # 黄河 -> 渤海 (NOT 黄海 - common mistake)
        major = data.get("major_rivers_detail", {})
        major_str = json.dumps(major, ensure_ascii=False)

        # Check for 渤海 (Bohai Sea) for 黄河
        huanghe_bohai = False
        huanghe_huanghai_wrong = False
        changjiang_donghai = False
        zhujiang_nanhai = False

        # Search in full data for these associations
        # Look for 黄河 entry and 渤海
        if isinstance(major, dict):
            for k, v in major.items():
                v_str = json.dumps(v, ensure_ascii=False)
                if "黄河" in k or "黄河" in v_str:
                    if "渤海" in v_str:
                        huanghe_bohai = True
                    if "黄海" in v_str:
                        huanghe_huanghai_wrong = True
                if "长江" in k or "长江" in v_str:
                    if "东海" in v_str:
                        changjiang_donghai = True
                if "珠江" in k or "珠江" in v_str:
                    if "南海" in v_str:
                        zhujiang_nanhai = True
        else:
            # Try list format
            for item in (major if isinstance(major, list) else []):
                item_str = json.dumps(item, ensure_ascii=False)
                if "黄河" in item_str and "渤海" in item_str:
                    huanghe_bohai = True
                if "长江" in item_str and "东海" in item_str:
                    changjiang_donghai = True
                if "珠江" in item_str and "南海" in item_str:
                    zhujiang_nanhai = True

        # Also check if they appear in close proximity in the full JSON
        # (in case structure is different)
        # Fallback: search in full data_str for co-occurrence
        import re
        # Find 黄河 context
        huanghe_contexts = [m.start() for m in re.finditer("黄河", data_str)]
        for pos in huanghe_contexts:
            context = data_str[max(0, pos-100):pos+200]
            if "渤海" in context:
                huanghe_bohai = True
            if "黄海" in context:
                huanghe_huanghai_wrong = True

        changjiang_contexts = [m.start() for m in re.finditer("长江", data_str)]
        for pos in changjiang_contexts:
            context = data_str[max(0, pos-100):pos+200]
            if "东海" in context:
                changjiang_donghai = True

        zhujiang_contexts = [m.start() for m in re.finditer("珠江", data_str)]
        for pos in zhujiang_contexts:
            context = data_str[max(0, pos-100):pos+200]
            if "南海" in context:
                zhujiang_nanhai = True

        ocean_correct = huanghe_bohai and not huanghe_huanghai_wrong and changjiang_donghai and zhujiang_nanhai

        checks.append({
            "name": "correct_ocean_sea_names",
            "passed": ocean_correct,
            "detail": (
                f"黄河->渤海: {huanghe_bohai} (wrong 黄海: {huanghe_huanghai_wrong}), "
                f"长江->东海: {changjiang_donghai}, "
                f"珠江->南海: {zhujiang_nanhai}"
            )
        })
        if ocean_correct:
            total_score += 15.0
        elif huanghe_bohai and not huanghe_huanghai_wrong:
            total_score += 5.0  # At least got the hard one right
    except Exception as e:
        checks.append({"name": "correct_ocean_sea_names", "passed": False, "detail": str(e)})

    # ================================================================
    # CHECK 7: 长江 length = 6300km, 黄河 = 5464km, 珠江 = 2320km
    # ================================================================
    try:
        correct_lengths = 0
        length_details = []

        RIVER_LENGTHS = {
            "长江": 6300,
            "黄河": 5464,
            "珠江": 2320,
        }

        for river, expected_len in RIVER_LENGTHS.items():
            river_contexts = [m.start() for m in __import__('re').finditer(river, data_str)]
            found = False
            for pos in river_contexts:
                context = data_str[max(0, pos-50):pos+300]
                matches = __import__('re').findall(r'\b(\d{4,5})\b', context)
                for m in matches:
                    if abs(int(m) - expected_len) < 5:
                        found = True
                        break
                if found:
                    break
            if found:
                correct_lengths += 1
                length_details.append(f"{river}({expected_len}km): ✓")
            else:
                length_details.append(f"{river}({expected_len}km): ✗")

        lengths_passed = correct_lengths == 3
        checks.append({
            "name": "river_lengths_accuracy",
            "passed": lengths_passed,
            "detail": f"{correct_lengths}/3 correct. {'; '.join(length_details)}"
        })
        if correct_lengths == 3:
            total_score += 10.0
        elif correct_lengths >= 2:
            total_score += 5.0
    except Exception as e:
        checks.append({"name": "river_lengths_accuracy", "passed": False, "detail": str(e)})

    # ================================================================
    # CHECK 8: 额尔齐斯河 identified as Arctic Ocean river
    # ================================================================
    try:
        has_arctic_river = "额尔齐斯河" in data_str
        has_arctic_ocean = "北冰洋" in data_str
        arctic_associated = False

        if has_arctic_river and has_arctic_ocean:
            import re
            erqisi_positions = [m.start() for m in re.finditer("额尔齐斯河", data_str)]
            for pos in erqisi_positions:
                context = data_str[max(0, pos-100):pos+200]
                if "北冰洋" in context:
                    arctic_associated = True
                    break

        checks.append({
            "name": "arctic_ocean_river_identification",
            "passed": arctic_associated,
            "detail": f"额尔齐斯河 present: {has_arctic_river}, 北冰洋 present: {has_arctic_ocean}, associated: {arctic_associated}"
        })
        if arctic_associated:
            total_score += 5.0
    except Exception as e:
        checks.append({"name": "arctic_ocean_river_identification", "passed": False, "detail": str(e)})

    # ================================================================
    # CHECK 9: Flow statistics - external 65%, internal 35%
    # ================================================================
    try:
        stats = data.get("flow_statistics", data.get("basin_statistics", data.get("statistics", {})))
        stats_str = json.dumps(stats, ensure_ascii=False) if stats else ""

        # Also check in full data
        import re
        has_65 = bool(re.search(r'\b65\b', data_str))
        has_35 = bool(re.search(r'\b35\b', data_str))

        # Check for external/internal labels near these numbers
        external_correct = False
        internal_correct = False

        contexts_65 = [m.start() for m in re.finditer(r'\b65\b', data_str)]
        for pos in contexts_65:
            ctx = data_str[max(0, pos-150):pos+150]
            if any(w in ctx for w in ["外流", "external", "外部"]):
                external_correct = True

        contexts_35 = [m.start() for m in re.finditer(r'\b35\b', data_str)]
        for pos in contexts_35:
            ctx = data_str[max(0, pos-150):pos+150]
            if any(w in ctx for w in ["内流", "internal", "内部"]):
                internal_correct = True

        flow_stats_passed = external_correct and internal_correct
        checks.append({
            "name": "flow_statistics_percentages",
            "passed": flow_stats_passed,
            "detail": f"External 65%: {external_correct}, Internal 35%: {internal_correct}"
        })
        if flow_stats_passed:
            total_score += 5.0
    except Exception as e:
        checks.append({"name": "flow_statistics_percentages", "passed": False, "detail": str(e)})

    # ================================================================
    # FINAL SCORING
    # ================================================================
    max_score = 100.0
    # Normalize score to 0-1
    normalized_score = min(total_score / max_score, 1.0)

    # Pass threshold: must pass critical checks
    critical_passed = (
        any(c["passed"] for c in checks if c["name"] == "seven_systems_count") and
        any(c["passed"] for c in checks if c["name"] == "seven_systems_north_to_south_order") and
        any(c["passed"] for c in checks if c["name"] == "correct_ocean_sea_names")
    )

    overall_passed = critical_passed and normalized_score >= 0.65

    return {
        "passed": overall_passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))