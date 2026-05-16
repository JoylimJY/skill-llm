import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace):
    checks = []
    
    nutrition_root = Path(workspace) / "nutrition"
    
    # ── CHECK 1: Daily log file exists at the EXACT correct path ─────────────
    target_date = "2024-03-15"
    target_dir = nutrition_root / "daily" / "2024-03"
    target_file = target_dir / f"{target_date}.md"
    
    # Also accept if they used home directory directly
    home_target = Path.home() / "nutrition" / "daily" / "2024-03" / f"{target_date}.md"
    
    found_log = None
    if target_file.exists():
        found_log = target_file
    elif home_target.exists():
        found_log = home_target
    else:
        # Search broadly for the date
        for candidate in (Path(workspace).rglob(f"{target_date}.md")):
            found_log = candidate
            break
        if not found_log:
            for candidate in (Path.home().rglob(f"{target_date}.md")):
                found_log = candidate
                break
    
    if found_log is None:
        checks.append(check("daily_log_file_exists", False, 
            f"No file named {target_date}.md found anywhere under nutrition/daily/2024-03/"))
        # Can't continue most checks
        log_content = ""
    else:
        checks.append(check("daily_log_file_exists", True, 
            f"Found daily log at {found_log}"))
        try:
            log_content = found_log.read_text()
        except Exception as e:
            log_content = ""
            checks.append(check("daily_log_readable", False, str(e)))
    
    # ── CHECK 2: File is in correct subdirectory 2024-03/ ────────────────────
    if found_log is not None:
        correct_parent = "2024-03" in str(found_log)
        checks.append(check("daily_log_in_correct_month_dir", correct_parent,
            f"Path: {found_log} — expected .../daily/2024-03/{target_date}.md"))
    
    # ── CHECK 3: Meal sections present (Breakfast, Lunch, Dinner) ────────────
    if log_content:
        has_breakfast = bool(re.search(r'##\s+Breakfast', log_content, re.IGNORECASE))
        has_lunch = bool(re.search(r'##\s+Lunch', log_content, re.IGNORECASE))
        has_dinner = bool(re.search(r'##\s+Dinner', log_content, re.IGNORECASE))
        meal_sections_ok = has_breakfast and has_lunch and has_dinner
        checks.append(check("meal_sections_present", meal_sections_ok,
            f"Breakfast: {has_breakfast}, Lunch: {has_lunch}, Dinner: {has_dinner}"))
    else:
        checks.append(check("meal_sections_present", False, "No log content to parse"))
    
    # ── CHECK 4: Daily Totals section with correct format ─────────────────────
    # Must have "## Daily Totals" section
    # Calories line: "Calories: X,XXX" or "Calories: XXX" (with or without comma)
    # Macros line: "Protein: Xg | Carbs: Xg | Fat: Xg" (pipe-separated)
    if log_content:
        has_totals_section = bool(re.search(r'##\s+Daily Totals', log_content, re.IGNORECASE))
        
        # Parse the calories
        cal_match = re.search(r'Calories:\s*([\d,]+)', log_content)
        
        # Parse the pipe-separated macro line
        macro_line_match = re.search(
            r'Protein:\s*(\d+(?:\.\d+)?)g\s*\|\s*Carbs:\s*(\d+(?:\.\d+)?)g\s*\|\s*Fat:\s*(\d+(?:\.\d+)?)g',
            log_content, re.IGNORECASE
        )
        
        totals_format_ok = has_totals_section and cal_match is not None and macro_line_match is not None
        detail_parts = []
        if not has_totals_section:
            detail_parts.append("Missing '## Daily Totals' section")
        if cal_match is None:
            detail_parts.append("Missing 'Calories: X' line in Daily Totals")
        if macro_line_match is None:
            detail_parts.append("Missing pipe-separated macro line 'Protein: Xg | Carbs: Xg | Fat: Xg'")
        
        if totals_format_ok:
            parsed_cal = int(cal_match.group(1).replace(',', ''))
            parsed_protein = float(macro_line_match.group(1))
            parsed_carbs = float(macro_line_match.group(2))
            parsed_fat = float(macro_line_match.group(3))
            detail_parts.append(
                f"Parsed: Calories={parsed_cal}, Protein={parsed_protein}g, "
                f"Carbs={parsed_carbs}g, Fat={parsed_fat}g"
            )
        
        checks.append(check("daily_totals_format_correct", totals_format_ok,
            " | ".join(detail_parts) if detail_parts else "Format OK"))
    else:
        checks.append(check("daily_totals_format_correct", False, "No log content"))
        parsed_cal = parsed_protein = parsed_carbs = parsed_fat = None
    
    # ── CHECK 5: Daily Totals are numerically plausible for the given meal ───
    # The agent was given: 
    # Breakfast: scrambled eggs (3 eggs = ~210 cal, 18g P, 0g C, 15g F) + 
    #            oatmeal 80g (300 cal, 10g P, 54g C, 5g F)
    # Lunch: lentil soup (lentils 200g ~230 cal, 18g P, 40g C, 1g F, 
    #         tomatoes 100g ~18 cal, spinach 50g ~12 cal)
    # Dinner: chicken breast 200g (~330 cal, 62g P, 0g C, 7.2g F) + 
    #          sweet potato 150g (~130 cal, 2g P, 30g C, 0g F) +
    #          broccoli 100g (~34 cal, 3g P, 7g C, 0g F)
    # Total rough range: 1200-1800 cal, 80-120g P, 100-160g C, 25-50g F
    if log_content and totals_format_ok and cal_match and macro_line_match:
        cal_ok = 900 <= parsed_cal <= 2200
        protein_ok = 50 <= parsed_protein <= 160
        carbs_ok = 50 <= parsed_carbs <= 250
        fat_ok = 10 <= parsed_fat <= 90
        numeric_ok = cal_ok and protein_ok and carbs_ok and fat_ok
        checks.append(check("daily_totals_numerically_plausible", numeric_ok,
            f"Cal {parsed_cal} (900-2200): {cal_ok}, P {parsed_protein}g (50-160): {protein_ok}, "
            f"C {parsed_carbs}g (50-250): {carbs_ok}, F {parsed_fat}g (10-90): {fat_ok}"))
    else:
        checks.append(check("daily_totals_numerically_plausible", False,
            "Could not extract totals for numeric check"))
    
    # ── CHECK 6: Micronutrients Notable section present ───────────────────────
    if log_content:
        has_micro = bool(re.search(r'##\s+Micronutrients?\s+Notable', log_content, re.IGNORECASE))
        # Must have at least 2 bullet points
        micro_bullets = re.findall(r'-\s+\w+.*', log_content[log_content.lower().find('micronutrient'):] 
                                   if 'micronutrient' in log_content.lower() else "")
        has_micro_bullets = len(micro_bullets) >= 2
        micro_ok = has_micro and has_micro_bullets
        checks.append(check("micronutrients_notable_section", micro_ok,
            f"Section present: {has_micro}, Bullet count: {len(micro_bullets)} (need ≥2)"))
    else:
        checks.append(check("micronutrients_notable_section", False, "No log content"))
    
    # ── CHECK 7: Gap analysis / "what to surface" in log or separate output ──
    # The skill mandates surfacing gaps like "You've had Xg protein so far, Yg to go"
    # or "Weekly average: X cal, under target"
    # This might appear in the log file itself or in insights.md
    
    gap_texts_to_search = [log_content]
    
    # Also check insights.md
    insights_candidates = list(Path(workspace).rglob("insights.md")) + list(Path.home().rglob("insights.md"))
    insights_content = ""
    for ic in insights_candidates:
        try:
            insights_content = ic.read_text()
            break
        except:
            pass
    
    if insights_content:
        gap_texts_to_search.append(insights_content)
    
    combined_gap_text = "\n".join(gap_texts_to_search)
    
    # Check for gap language: "to go", "under target", "low on", "above target", or numeric comparison
    has_gap_language = bool(re.search(
        r'(to go|under target|above target|low on|gap|remaining|short|behind|over target)',
        combined_gap_text, re.IGNORECASE
    ))
    checks.append(check("gap_analysis_surfaced", has_gap_language,
        "Gap/target language found in log or insights" if has_gap_language 
        else "No gap analysis language detected (expected phrases like 'to go', 'low on X', 'under target')"))
    
    # ── CHECK 8: foods/common.md updated with at least one new food ──────────
    foods_candidates = list(Path(workspace).rglob("common.md")) + list(Path.home().rglob("common.md"))
    foods_content = ""
    for fc in foods_candidates:
        try:
            foods_content = fc.read_text()
            break
        except:
            pass
    
    original_foods = {"Egg", "Chicken 100g", "Rice 100g cooked", "Banana"}
    
    # Parse table rows
    table_rows = re.findall(r'\|\s*([^|]+?)\s*\|', foods_content)
    found_foods = set()
    for row in table_rows:
        row_stripped = row.strip()
        if row_stripped and row_stripped not in ('Food', '---', '', 'Cal', 'Protein', 'Carbs', 'Fat'):
            found_foods.add(row_stripped)
    
    new_foods = found_foods - original_foods - {'---', 'Food'}
    has_new_food = len(new_foods) > 0
    checks.append(check("foods_common_md_updated", has_new_food,
        f"New foods added: {new_foods}" if has_new_food 
        else f"No new foods found. Current foods: {found_foods}. Original: {original_foods}"))
    
    # ── CHECK 9: foods/common.md preserves pipe-table format ─────────────────
    if foods_content:
        table_header_ok = bool(re.search(r'\|\s*Food\s*\|\s*Cal\s*\|\s*Protein\s*\|\s*Carbs\s*\|\s*Fat\s*\|', 
                                          foods_content, re.IGNORECASE))
        # Check separator row
        table_separator_ok = bool(re.search(r'\|[-\s]+\|[-\s]+\|', foods_content))
        table_format_ok = table_header_ok and table_separator_ok
        checks.append(check("foods_table_format_preserved", table_format_ok,
            f"Header OK: {table_header_ok}, Separator OK: {table_separator_ok}"))
    else:
        checks.append(check("foods_table_format_preserved", False, "foods/common.md not found or empty"))
    
    # ── CHECK 10: insights.md updated (new pattern or adjustment) ────────────
    original_patterns = [
        "Usually low on Vitamin D without supplements",
        "Protein higher on workout days",
        "Weekends: higher calories, less consistent"
    ]
    original_adjustments = [
        "Added salmon twice weekly for Omega-3",
        "Morning eggs improved protein start"
    ]
    
    insights_updated = False
    insights_detail = "insights.md not found"
    
    if insights_content:
        # Count bullets
        all_bullets = re.findall(r'-\s+.+', insights_content)
        original_bullet_count = len(original_patterns) + len(original_adjustments)
        insights_updated = len(all_bullets) > original_bullet_count
        insights_detail = (
            f"Total bullet points: {len(all_bullets)} (original had {original_bullet_count}). "
            f"{'New entries found.' if insights_updated else 'No new entries detected.'}"
        )
    
    checks.append(check("insights_md_updated", insights_updated, insights_detail))
    
    # ── Scoring ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 7  # Must pass at least 7/10 checks
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else str(Path.home())
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))