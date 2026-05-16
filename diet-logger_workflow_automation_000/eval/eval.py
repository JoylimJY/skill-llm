import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    TARGET_DATE = "2026-04-05"
    SAVE_DIR = Path("/mnt/c/Users/loong/iCloudDrive/iCloud~md~obsidian/HomeMo.Art/05-Daily")
    TARGET_FILE = SAVE_DIR / f"饮食记录-{TARGET_DATE}.md"

    EXPECTED_MEALS = {
        "早饭": ["燕麦粥", "水煮蛋", "橙汁"],
        "中饭": ["番茄牛腩", "白米饭", "紫菜汤"],
        "晚饭": ["清炒时蔬", "豆腐"],
        "加餐": ["苹果", "坚果"],
    }
    MEAL_ORDER = ["早饭", "中饭", "晚饭", "加餐"]

    # --- Check 1: File exists at exact proprietary path ---
    try:
        exists = TARGET_FILE.exists()
        checks.append({
            "name": "file_exists_at_correct_path",
            "passed": exists,
            "detail": f"Expected file at: {TARGET_FILE}. {'Found.' if exists else 'NOT FOUND.'}"
        })
        if exists:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "file_exists_at_correct_path", "passed": False, "detail": str(e)})

    # --- Check 2: Filename uses Chinese characters and correct date ---
    try:
        correct_name = TARGET_FILE.name == f"饮食记录-{TARGET_DATE}.md"
        checks.append({
            "name": "filename_format_correct",
            "passed": correct_name,
            "detail": f"Filename: {TARGET_FILE.name}. Expected: 饮食记录-{TARGET_DATE}.md"
        })
        if correct_name:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "filename_format_correct", "passed": False, "detail": str(e)})

    # --- Read content ---
    content = ""
    try:
        if TARGET_FILE.exists():
            content = TARGET_FILE.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        content = ""

    # --- Check 3: Correct H1 header ---
    try:
        expected_header = f"# {TARGET_DATE} 饮食记录"
        has_header = expected_header in content
        checks.append({
            "name": "correct_h1_header",
            "passed": has_header,
            "detail": f"Expected header '{expected_header}'. {'Found.' if has_header else 'NOT found in content.'}"
        })
        if has_header:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "correct_h1_header", "passed": False, "detail": str(e)})

    # --- Check 4: All four meal sections present (including empty ones) ---
    try:
        all_sections_present = all(f"## {meal}" in content for meal in MEAL_ORDER)
        missing = [meal for meal in MEAL_ORDER if f"## {meal}" not in content]
        checks.append({
            "name": "all_four_meal_sections_present",
            "passed": all_sections_present,
            "detail": f"All meal headers present: {all_sections_present}. Missing: {missing}"
        })
        if all_sections_present:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "all_four_meal_sections_present", "passed": False, "detail": str(e)})

    # --- Check 5: Correct meal items per section ---
    def extract_meal_items(content: str, meal: str) -> list:
        """Extract items under a ## meal section."""
        pattern = rf"## {re.escape(meal)}\n((?:- .+\n?)*)"
        match = re.search(pattern, content)
        if not match:
            return []
        items_block = match.group(1)
        return [line[2:].strip() for line in items_block.splitlines() if line.startswith("- ")]

    meal_check_passed = True
    meal_details = []
    try:
        for meal, expected_items in EXPECTED_MEALS.items():
            actual_items = extract_meal_items(content, meal)
            # Sort-insensitive comparison
            matched = sorted(actual_items) == sorted(expected_items)
            if not matched:
                meal_check_passed = False
            meal_details.append(f"{meal}: expected={expected_items}, actual={actual_items}, match={matched}")
        checks.append({
            "name": "meal_items_correct",
            "passed": meal_check_passed,
            "detail": " | ".join(meal_details)
        })
        if meal_check_passed:
            total_score += 2.0
    except Exception as e:
        checks.append({"name": "meal_items_correct", "passed": False, "detail": str(e)})

    # --- Check 6: Footer separator and 记录时间 present ---
    try:
        has_separator = "\n---\n" in content or content.strip().find("\n---") != -1
        has_record_time = re.search(r"\*记录时间: \d{4}-\d{2}-\d{2} \d{2}:\d{2}\*", content) is not None
        footer_ok = has_separator and has_record_time
        checks.append({
            "name": "footer_format_correct",
            "passed": footer_ok,
            "detail": f"Has '---' separator: {has_separator}. Has '记录时间' timestamp: {has_record_time}."
        })
        if footer_ok:
            total_score += 1.0
    except Exception as e:
        checks.append({"name": "footer_format_correct", "passed": False, "detail": str(e)})

    # --- Check 7: Meal section order is correct (早饭 before 中饭 before 晚饭 before 加餐) ---
    try:
        positions = {}
        for meal in MEAL_ORDER:
            pos = content.find(f"## {meal}")
            positions[meal] = pos if pos != -1 else float('inf')
        order_correct = all(
            positions[MEAL_ORDER[i]] < positions[MEAL_ORDER[i+1]]
            for i in range(len(MEAL_ORDER) - 1)
            if positions[MEAL_ORDER[i]] != float('inf') and positions[MEAL_ORDER[i+1]] != float('inf')
        )
        checks.append({
            "name": "meal_section_order_correct",
            "passed": order_correct,
            "detail": f"Section positions: { {m: p for m, p in positions.items()} }. Order correct: {order_correct}"
        })
        if order_correct:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "meal_section_order_correct", "passed": False, "detail": str(e)})

    # --- Check 8: No wrong meal name used (e.g., 午饭 instead of 中饭) ---
    try:
        wrong_name_used = "## 午饭" in content
        checks.append({
            "name": "no_incorrect_meal_names",
            "passed": not wrong_name_used,
            "detail": f"'## 午饭' found (incorrect): {wrong_name_used}. Correct term is '中饭'."
        })
        if not wrong_name_used:
            total_score += 0.5
    except Exception as e:
        checks.append({"name": "no_incorrect_meal_names", "passed": False, "detail": str(e)})

    max_score = 7.0
    normalized_score = round(total_score / max_score, 4)
    overall_passed = all(c["passed"] for c in checks)

    result = {
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/home/user/workspace"
    evaluate(workspace_dir)