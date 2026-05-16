import os
import random
from pathlib import Path

random.seed(42)

# ── Base workspace ──────────────────────────────────────────────────────────
nutrition = Path.home() / "nutrition"

# Create the full prescribed directory structure
for d in [
    nutrition / "daily" / "2024-01",
    nutrition / "daily" / "2024-02",
    nutrition / "daily" / "2024-03",
    nutrition / "foods",
    nutrition / "archive" / "2023",
    nutrition / "archive" / "2023-12",
    nutrition / "tmp",
    nutrition / "exports",
    nutrition / "reports",
    nutrition / "plans",
]:
    d.mkdir(parents=True, exist_ok=True)

# ── Existing daily logs (distractor files with correct structure) ────────────
log_jan_15 = nutrition / "daily" / "2024-01" / "2024-01-15.md"
log_jan_15.write_text("""\
# 2024-01-15

## Breakfast — 7:30 AM
Scrambled eggs with toast
- Eggs 2x: 140 cal, 12g protein, 0g carbs, 10g fat
- Whole wheat toast 2 slices: 160 cal, 6g protein, 30g carbs, 2g fat
- Butter 5g: 36 cal, 0g protein, 0g carbs, 4g fat

## Lunch — 12:30 PM
Turkey sandwich
- Turkey 100g: 135 cal, 30g protein, 0g carbs, 1g fat
- Bread 2 slices: 160 cal, 6g protein, 30g carbs, 2g fat
- Lettuce 30g: 5 cal, 0g protein, 1g carbs, 0g fat

## Daily Totals
Calories: 636
Protein: 54g | Carbs: 61g | Fat: 19g

## Micronutrients Notable
- Iron: turkey
- B vitamins: whole wheat toast
""")

log_jan_28 = nutrition / "daily" / "2024-01" / "2024-01-28.md"
log_jan_28.write_text("""\
# 2024-01-28

## Breakfast — 8:00 AM
Greek yogurt parfait
- Greek yogurt 200g: 133 cal, 23g protein, 8g carbs, 1g fat
- Granola 40g: 180 cal, 4g protein, 28g carbs, 6g fat
- Blueberries 80g: 46 cal, 1g protein, 11g carbs, 0g fat

## Dinner — 7:00 PM
Beef stir fry
- Beef sirloin 150g: 300 cal, 38g protein, 0g carbs, 16g fat
- Mixed vegetables 200g: 60 cal, 3g protein, 12g carbs, 0g fat
- Soy sauce 15ml: 9 cal, 1g protein, 1g carbs, 0g fat

## Daily Totals
Calories: 728
Protein: 70g | Carbs: 60g | Fat: 23g

## Micronutrients Notable
- Iron: beef sirloin (high)
- Antioxidants: blueberries
- Zinc: beef sirloin
""")

log_feb_10 = nutrition / "daily" / "2024-02" / "2024-02-10.md"
log_feb_10.write_text("""\
# 2024-02-10

## Breakfast — 8:00 AM
Oatmeal with banana
- Oats 80g: 300 cal, 10g protein, 54g carbs, 5g fat
- Banana: 105 cal, 1g protein, 27g carbs, 0g fat
- Almond milk 200ml: 30 cal, 1g protein, 1g carbs, 2.5g fat

## Lunch — 1:00 PM
Chicken salad
- Chicken breast 150g: 165 cal, 31g protein, 0g carbs, 3.6g fat
- Mixed greens 100g: 20 cal, 2g protein, 3g carbs, 0g fat
- Olive oil 15ml: 120 cal, 0g protein, 0g carbs, 14g fat

## Daily Totals
Calories: 740
Protein: 45g | Carbs: 85g | Fat: 25g

## Micronutrients Notable
- Potassium: banana
- Vitamin E: almond milk
""")

log_feb_11 = nutrition / "daily" / "2024-02" / "2024-02-11.md"
log_feb_11.write_text("""\
# 2024-02-11

## Breakfast — 8:00 AM
Oatmeal with banana
- Oats 80g: 300 cal, 10g protein, 54g carbs, 5g fat
- Banana: 105 cal, 1g protein, 27g carbs, 0g fat
- Almond milk 200ml: 30 cal, 1g protein, 1g carbs, 2.5g fat

## Lunch — 1:00 PM
Chicken salad
- Chicken breast 150g: 165 cal, 31g protein, 0g carbs, 3.6g fat
- Mixed greens 100g: 20 cal, 2g protein, 3g carbs, 0g fat
- Olive oil 15ml: 120 cal, 0g protein, 0g carbs, 14g fat

## Dinner — 7:30 PM
Salmon with vegetables
- Salmon 200g: 400 cal, 40g protein, 0g carbs, 25g fat
- Broccoli 150g: 50 cal, 4g protein, 10g carbs, 0.5g fat

## Snacks
- Apple: 95 cal, 0g protein, 25g carbs, 0g fat
- Greek yogurt 150g: 100 cal, 17g protein, 6g carbs, 0.7g fat

## Daily Totals
Calories: 1,385
Protein: 106g | Carbs: 126g | Fat: 51g

## Micronutrients Notable
- Vitamin D: salmon (high)
- Potassium: banana, salmon
- Vitamin C: broccoli
- Omega-3: salmon (high)
""")

log_mar_01 = nutrition / "daily" / "2024-03" / "2024-03-01.md"
log_mar_01.write_text("""\
# 2024-03-01

## Breakfast — 7:00 AM
Protein shake
- Whey protein 30g: 120 cal, 25g protein, 3g carbs, 1g fat
- Oat milk 250ml: 130 cal, 4g protein, 25g carbs, 3g fat

## Daily Totals
Calories: 250
Protein: 29g | Carbs: 28g | Fat: 4g

## Micronutrients Notable
- Calcium: oat milk
""")

# ── Existing targets.md ──────────────────────────────────────────────────────
targets = nutrition / "targets.md"
targets.write_text("""\
# targets.md
## Daily Goals
Calories: 2,000
Protein: 150g
Carbs: 200g
Fat: 65g

## Micronutrient Focus
- Vitamin D: 600 IU (often low)
- Iron: 8mg
- Omega-3: 1,000mg

## Notes
Higher protein for muscle building
Limiting added sugars to 25g
""")

# ── Existing supplements.md ──────────────────────────────────────────────────
supplements = nutrition / "supplements.md"
supplements.write_text("""\
# supplements.md
## Daily
- Vitamin D3: 2000 IU (morning)
- Omega-3: 1000mg (with food)

## As Needed
- Magnesium: before bed if needed
""")

# ── Existing insights.md (has 2 existing entries) ────────────────────────────
insights = nutrition / "insights.md"
insights.write_text("""\
# insights.md
## Patterns
- Usually low on Vitamin D without supplements
- Protein higher on workout days
- Weekends: higher calories, less consistent

## Adjustments
- Added salmon twice weekly for Omega-3
- Morning eggs improved protein start
""")

# ── Existing foods/common.md ─────────────────────────────────────────────────
foods_common = nutrition / "foods" / "common.md"
foods_common.write_text("""\
# foods/common.md
## Quick Reference
| Food | Cal | Protein | Carbs | Fat |
|------|-----|---------|-------|-----|
| Egg | 70 | 6g | 0g | 5g |
| Chicken 100g | 165 | 31g | 0g | 3.6g |
| Rice 100g cooked | 130 | 2.7g | 28g | 0.3g |
| Banana | 105 | 1g | 27g | 0g |

## Micronutrient Stars
- Vitamin D: salmon, eggs, fortified milk
- Iron: red meat, spinach, lentils
- Vitamin C: citrus, peppers, broccoli
- Potassium: bananas, potatoes, salmon
- Omega-3: salmon, sardines, walnuts
""")

# ── Archive / distractor files ───────────────────────────────────────────────
archive_2023 = nutrition / "archive" / "2023"
(archive_2023 / "summary.txt").write_text("2023 annual summary: average 1850 cal/day\n")
(archive_2023 / "weight_log.csv").write_text("date,weight_kg\n2023-01-01,80.2\n2023-06-01,78.5\n2023-12-31,77.1\n")

archive_dec = nutrition / "archive" / "2023-12"
(archive_dec / "2023-12-25.md").write_text("""\
# 2023-12-25
## Holiday meal - estimated totals only
Calories: 2800
Protein: 95g | Carbs: 310g | Fat: 120g
""")

(nutrition / "exports" / "macros_export_jan2024.csv").write_text(
    "date,calories,protein,carbs,fat\n2024-01-15,636,54,61,19\n2024-01-28,728,70,60,23\n"
)
(nutrition / "reports" / "weekly_jan_w3.txt").write_text(
    "Week of Jan 15: avg 682 cal — well below 2000 target\n"
)
(nutrition / "plans" / "cutting_plan.md").write_text("""\
# Cutting Plan - Feb 2024
Target: 1800 cal/day
Increase protein to 160g
Reduce carbs to 180g
""")
(nutrition / "tmp" / "scratch_notes.txt").write_text(
    "TODO: log last Tuesday's lunch\nMaybe add lentil soup to common foods\n"
)
(nutrition / "foods" / "meal_prep_ideas.md").write_text("""\
# Meal Prep Ideas
- Batch cook quinoa on Sundays
- Pre-portion chicken breast
- Overnight oats for weekday breakfasts
""")

print("Sandbox workspace generated successfully.")
print(f"Nutrition workspace: {nutrition}")
print("Files created:")
for f in sorted(nutrition.rglob("*")):
    if f.is_file():
        print(f"  {f}")