import sys
import json
import os
import re
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    total_score = 0.0
    total_weight = 0.0

    def check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score, total_weight
        total_weight += weight
        if passed:
            total_score += weight

    # Find the output file
    target_filename = "daily_summary_2026-03-15.txt"
    found_files = list(Path(workspace).rglob(target_filename))

    if not found_files:
        check("file_exists", False, f"File '{target_filename}' not found anywhere in workspace.", weight=2.0)
        final_score = 0.0
        return {"passed": False, "score": final_score, "checks": checks}
    
    check("file_exists", True, f"Found file at: {found_files[0]}", weight=2.0)
    
    try:
        content = found_files[0].read_text(encoding="utf-8")
    except Exception as e:
        check("file_readable", False, f"Could not read file: {e}", weight=2.0)
        return {"passed": False, "score": 0.0, "checks": checks}

    check("file_readable", True, "File is readable.", weight=1.0)

    # Expected values based on data for 2026-03-15:
    # kcal=1800, protein=130, carbs=200, fat=45
    # delta_kcal = 1800 - 2200 = -400
    # delta_protein = 130 - 165 = -35
    # delta_carbs = 200 - 275 = -75
    # delta_fat = 45 - 55 = -10
    # fiber=18, sugar=35, sodium=2100, sat_fat=12
    # water=1600ml, target=2000ml
    # exercise=45min
    # weight=69.8kg, sleep=7.5h

    # CHECK 1: Header line with date
    header_pattern = r'📊.*2026-03-15'
    header_match = bool(re.search(header_pattern, content))
    check("header_with_date", header_match,
          f"Expected '📊 ... 2026-03-15' header. Content starts with: {content[:80]!r}",
          weight=2.0)

    # CHECK 2: Nutrition line with kcal=1800
    # Must match: 🍽 栄養: 1,800kcal / P 130g / C 200g / F 45g
    # Allow flexible number formatting for kcal (1,800 or 1800)
    nutrition_kcal = bool(re.search(r'🍽', content))
    check("nutrition_emoji_present", nutrition_kcal,
          "Expected 🍽 emoji on nutrition line.",
          weight=1.5)

    kcal_pattern = bool(re.search(r'1[,.]?800\s*kcal', content))
    check("kcal_value_1800", kcal_pattern,
          f"Expected 1,800kcal or 1800kcal in content.",
          weight=2.0)

    protein_pattern = bool(re.search(r'P\s*130g', content))
    check("protein_value_130g", protein_pattern,
          "Expected 'P 130g' in nutrition line.",
          weight=1.5)

    carbs_pattern = bool(re.search(r'C\s*200g', content))
    check("carbs_value_200g", carbs_pattern,
          "Expected 'C 200g' in nutrition line.",
          weight=1.5)

    fat_pattern = bool(re.search(r'F\s*45g', content))
    check("fat_value_45g", fat_pattern,
          "Expected 'F 45g' in nutrition line.",
          weight=1.5)

    # CHECK 3: Delta line
    # delta_kcal = -400, delta_protein = -35, delta_carbs = -75, delta_fat = -10
    delta_kcal = bool(re.search(r'kcal\s*-400', content))
    check("delta_kcal_minus400", delta_kcal,
          "Expected 'kcal -400' delta in content.",
          weight=2.0)

    delta_protein = bool(re.search(r'P\s*-35g', content))
    check("delta_protein_minus35", delta_protein,
          "Expected 'P -35g' delta in content.",
          weight=1.5)

    delta_carbs = bool(re.search(r'C\s*-75g', content))
    check("delta_carbs_minus75", delta_carbs,
          "Expected 'C -75g' delta in content.",
          weight=1.5)

    delta_fat = bool(re.search(r'F\s*-10g', content))
    check("delta_fat_minus10", delta_fat,
          "Expected 'F -10g' delta in content.",
          weight=1.5)

    # CHECK 4: Detailed nutrition line
    # 🥦 詳細栄養: Fiber 18g / Sugar 35g / Na 2,100mg / SatFat 12g
    detail_emoji = bool(re.search(r'🥦', content))
    check("detail_nutrition_emoji", detail_emoji,
          "Expected 🥦 emoji on detailed nutrition line.",
          weight=1.5)

    fiber_pattern = bool(re.search(r'Fiber\s*18g', content))
    check("fiber_value_18g", fiber_pattern,
          "Expected 'Fiber 18g' in detailed nutrition.",
          weight=1.5)

    sugar_pattern = bool(re.search(r'Sugar\s*35g', content))
    check("sugar_value_35g", sugar_pattern,
          "Expected 'Sugar 35g' in detailed nutrition.",
          weight=1.5)

    sodium_pattern = bool(re.search(r'Na\s*2[,.]?100mg', content))
    check("sodium_value_2100", sodium_pattern,
          "Expected 'Na 2,100mg' or 'Na 2100mg' in detailed nutrition.",
          weight=1.5)

    satfat_pattern = bool(re.search(r'SatFat\s*12g', content))
    check("satfat_value_12g", satfat_pattern,
          "Expected 'SatFat 12g' in detailed nutrition.",
          weight=1.5)

    # CHECK 5: Water line
    # 💧 水分: 1,600ml（目標: 2,000ml）
    water_emoji = bool(re.search(r'💧', content))
    check("water_emoji_present", water_emoji,
          "Expected 💧 emoji on water line.",
          weight=1.5)

    water_actual = bool(re.search(r'1[,.]?600\s*ml', content))
    check("water_actual_1600ml", water_actual,
          "Expected '1,600ml' or '1600ml' for actual water intake.",
          weight=2.0)

    water_target = bool(re.search(r'2[,.]?000\s*ml', content))
    check("water_target_2000ml", water_target,
          "Expected '2,000ml' or '2000ml' as water target.",
          weight=1.5)

    # CHECK 6: Exercise line
    # 🏃 運動: 45分
    exercise_emoji = bool(re.search(r'🏃', content))
    check("exercise_emoji_present", exercise_emoji,
          "Expected 🏃 emoji on exercise line.",
          weight=1.5)

    exercise_min = bool(re.search(r'45\s*分', content))
    check("exercise_45min", exercise_min,
          "Expected '45分' for exercise duration.",
          weight=2.0)

    # CHECK 7: Weight and sleep line
    # ⚖️ 体重: 69.8kg / 😴 睡眠: 7.5h
    weight_emoji = bool(re.search(r'⚖️', content))
    check("weight_emoji_present", weight_emoji,
          "Expected ⚖️ emoji on weight line.",
          weight=1.5)

    weight_val = bool(re.search(r'69\.8\s*kg', content))
    check("weight_value_69_8kg", weight_val,
          "Expected '69.8kg' for latest weight.",
          weight=2.0)

    sleep_emoji = bool(re.search(r'😴', content))
    check("sleep_emoji_present", sleep_emoji,
          "Expected 😴 emoji on sleep line.",
          weight=1.5)

    sleep_val = bool(re.search(r'7\.5\s*h', content))
    check("sleep_value_7_5h", sleep_val,
          "Expected '7.5h' for latest sleep.",
          weight=2.0)

    # CHECK 8: Verify content comes from actual script output (not hardcoded)
    # The agent must have used the proprietary --date= flag format
    # We verify by checking that the script is not modified to hardcode values
    try:
        script_path = Path(workspace) / "scripts" / "health_summary.js"
        script_content = script_path.read_text(encoding="utf-8")
        has_date_flag = '--date=' in script_content
        check("script_uses_date_flag_syntax", has_date_flag,
              "The health_summary.js script uses '--date=' flag syntax as per SKILL.md.",
              weight=1.0)
    except Exception as e:
        check("script_integrity", False, f"Could not verify script: {e}", weight=1.0)

    # Compute final score
    final_score = total_score / total_weight if total_weight > 0 else 0.0
    
    # Must pass critical checks to be considered passing
    critical_checks = [
        "file_exists", "kcal_value_1800", "delta_kcal_minus400",
        "weight_value_69_8kg", "exercise_45min", "water_actual_1600ml"
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    overall_passed = critical_passed and final_score >= 0.70

    return {
        "passed": overall_passed,
        "score": round(final_score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))