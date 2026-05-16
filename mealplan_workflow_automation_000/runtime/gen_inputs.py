import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE", "/workspace"))
workspace.mkdir(parents=True, exist_ok=True)

# ── distractor directory tree ──────────────────────────────────────────────
dirs = [
    "office/hr/onboarding",
    "office/hr/policies",
    "office/finance/q1",
    "office/finance/q2",
    "office/wellness/archive/2022",
    "office/wellness/archive/2023",
    "office/it/assets",
    "reports/monthly",
    "reports/annual",
    "tmp/scratch",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "office/hr/onboarding/welcome.txt": "Welcome to the company! Please read all policies.",
    "office/hr/policies/vacation_policy.txt": "Employees are entitled to 15 days of paid vacation per year.",
    "office/finance/q1/budget_summary.csv": "category,amount\nSalaries,500000\nBenefits,120000\nOffice Supplies,8000",
    "office/finance/q2/projections.json": json.dumps({"revenue": 1200000, "expenses": 900000}),
    "office/wellness/archive/2022/report.txt": "2022 wellness initiatives summary. Participation: 67%.",
    "office/wellness/archive/2023/report.txt": "2023 wellness initiatives summary. Participation: 72%.",
    "office/it/assets/inventory.csv": "asset_id,type,assigned_to\nA001,Laptop,John\nA002,Monitor,Jane",
    "reports/monthly/october.txt": "October monthly report - pending review.",
    "reports/annual/2023_annual.txt": "Annual summary for FY2023.",
    "tmp/scratch/notes.txt": "random scratch notes - ignore",
    "tmp/scratch/todo.txt": "TODO: clean up scratch folder",
}
for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.write_text(content)

# ── MAIN TASK INPUT: messy meal requirements ───────────────────────────────
# The agent must parse this and add meals using the CLI tool.
# Format is intentionally messy: mixed separators, inconsistent casing, extra whitespace.
meal_requirements_raw = """\
OFFICE WELLNESS WEEK - MEAL PLAN REQUIREMENTS
==============================================
This document was compiled by the wellness committee.
Please enter these meals into the meal tracking system ASAP.

--- MEALS TO ADD ---

Monday:
  - Oatmeal Porridge | 320 calories | type: breakfast
  - Grilled Chicken Salad | 480 calories | type: lunch
  - Beef Stir Fry | 610 calories   | type: dinner

Tuesday:
  - Scrambled Eggs | 290 calories | type: breakfast
  - Veggie Wrap    | 410 calories | type: lunch
  - Salmon Pasta   | 700 calories | type: dinner

Wednesday:
  - Greek Yogurt Parfait | 250 calories | type: breakfast
  - Tomato Soup          | 180 calories | type: lunch
  - Chicken Tikka Masala | 720 calories | type: dinner

--- REQUIRED OUTPUTS ---

1. After all meals are added, retrieve the nutrition summary for Monday and save
   the output to a file named: monday_nutrition.txt (inside the workspace root).

2. Retrieve the nutrition summary for Wednesday and save it to: wednesday_nutrition.txt
   (inside the workspace root).

3. Generate a shopping list covering Monday, Tuesday, and Wednesday.
   Save the output to: shopping_list.txt (inside the workspace root).

--- NOTES ---
* The system uses a script located at scripts/script.sh
* Days should be referenced as: monday, tuesday, wednesday (lowercase)
* All outputs should be plain text captures of the tool's stdout.
"""

(workspace / "office/wellness/meal_requirements.txt").write_text(meal_requirements_raw)

# ── scripts directory (the skill's scripts — already exist per spec) ────────
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# Create the actual mealplan script (since SKILL.md says "scripts already exist")
# We implement a realistic mealplan script with actual storage logic
script_content = r"""#!/usr/bin/env bash
# mealplan v3.0.0 - BytesAgain
set -euo pipefail

DATA_DIR="${HOME}/.local/share/mealplan"
MEALS_FILE="${DATA_DIR}/meals.json"
PLAN_FILE="${DATA_DIR}/plan.json"

mkdir -p "${DATA_DIR}"

# Initialize files if they don't exist
if [[ ! -f "${MEALS_FILE}" ]]; then
    echo '[]' > "${MEALS_FILE}"
fi
if [[ ! -f "${PLAN_FILE}" ]]; then
    echo '{}' > "${PLAN_FILE}"
fi

COMMAND="${1:-}"
shift || true

case "${COMMAND}" in

  add)
    # Usage: add <meal> <calories> <type>
    MEAL_NAME="${1:-}"
    CALORIES="${2:-}"
    MEAL_TYPE="${3:-}"

    if [[ -z "${MEAL_NAME}" || -z "${CALORIES}" || -z "${MEAL_TYPE}" ]]; then
        echo "Error: add requires <meal> <calories> <type>" >&2
        exit 1
    fi

    # Determine current day automatically (for add, we need the day context)
    # In this system, meals are added to a global pool; plan assigns them to days.
    # Actually per the API: add adds to today's plan. We use a day argument via env or default.
    TARGET_DAY="${MEALPLAN_DAY:-$(date +%A | tr '[:upper:]' '[:lower:]')}"

    PLAN=$(cat "${PLAN_FILE}")
    DAY_MEALS=$(echo "${PLAN}" | python3 -c "
import json,sys
p=json.load(sys.stdin)
d=p.get('${TARGET_DAY}',[])
d.append({'meal':'${MEAL_NAME}','calories':${CALORIES},'type':'${MEAL_TYPE}'})
p['${TARGET_DAY}']=d
print(json.dumps(p))
")
    echo "${DAY_MEALS}" > "${PLAN_FILE}"
    echo "Added: ${MEAL_NAME} (${CALORIES} cal, ${MEAL_TYPE}) to ${TARGET_DAY}"
    ;;

  list)
    DAY="${1:-}"
    if [[ -z "${DAY}" ]]; then
        echo "Error: list requires <day>" >&2
        exit 1
    fi
    DAY_LOWER=$(echo "${DAY}" | tr '[:upper:]' '[:lower:]')
    PLAN=$(cat "${PLAN_FILE}")
    echo "Meals for ${DAY_LOWER}:"
    echo "${PLAN}" | python3 -c "
import json,sys
p=json.load(sys.stdin)
meals=p.get('${DAY_LOWER}',[])
if not meals:
    print('  (no meals planned)')
else:
    for m in meals:
        print(f\"  - {m['meal']} | {m['calories']} cal | {m['type']}\")
"
    ;;

  plan)
    DAYS="${1:-}"
    if [[ -z "${DAYS}" ]]; then
        echo "Error: plan requires <days>" >&2
        exit 1
    fi
    echo "=== Meal Plan ==="
    IFS=',' read -ra DAY_LIST <<< "${DAYS}"
    for d in "${DAY_LIST[@]}"; do
        d_trim=$(echo "${d}" | xargs | tr '[:upper:]' '[:lower:]')
        echo ""
        echo "[ ${d_trim} ]"
        PLAN=$(cat "${PLAN_FILE}")
        echo "${PLAN}" | python3 -c "
import json,sys
p=json.load(sys.stdin)
meals=p.get('${d_trim}',[])
if not meals:
    print('  (no meals planned)')
else:
    for m in meals:
        print(f\"  - {m['meal']} | {m['calories']} cal | {m['type']}\")
"
    done
    ;;

  nutrition)
    DAY="${1:-}"
    if [[ -z "${DAY}" ]]; then
        echo "Error: nutrition requires <day>" >&2
        exit 1
    fi
    DAY_LOWER=$(echo "${DAY}" | tr '[:upper:]' '[:lower:]')
    PLAN=$(cat "${PLAN_FILE}")
    echo "=== Nutrition Summary: ${DAY_LOWER} ==="
    echo "${PLAN}" | python3 -c "
import json,sys
p=json.load(sys.stdin)
meals=p.get('${DAY_LOWER}',[])
if not meals:
    print('No meals recorded for this day.')
    sys.exit(0)
total=sum(m['calories'] for m in meals)
by_type={}
for m in meals:
    by_type.setdefault(m['type'],[]).append(m)
for t in ['breakfast','lunch','dinner','snack']:
    if t in by_type:
        sub=sum(m['calories'] for m in by_type[t])
        print(f'{t.capitalize()}: {sub} cal')
        for m in by_type[t]:
            print(f\"  * {m['meal']} ({m['calories']} cal)\")
print(f'Total: {total} cal')
"
    ;;

  shopping)
    DAYS="${1:-}"
    if [[ -z "${DAYS}" ]]; then
        echo "Error: shopping requires <days>" >&2
        exit 1
    fi
    echo "=== Shopping List ==="
    IFS=',' read -ra DAY_LIST <<< "${DAYS}"
    PLAN=$(cat "${PLAN_FILE}")
    python3 -c "
import json,sys
p=json.load(open('${PLAN_FILE}'))
days='${DAYS}'.split(',')
days=[d.strip().lower() for d in days]
items=[]
for d in days:
    for m in p.get(d,[]):
        items.append(m['meal'])
print('Items needed (' + str(len(items)) + ' total):')
for i,item in enumerate(items,1):
    print(f'  {i}. {item}')
"
    ;;

  random)
    TYPE="${1:-}"
    if [[ -z "${TYPE}" ]]; then
        echo "Error: random requires <type>" >&2
        exit 1
    fi
    SUGGESTIONS_breakfast=("Avocado Toast" "Banana Smoothie" "Chia Pudding" "French Toast" "Muesli Bowl")
    SUGGESTIONS_lunch=("Caesar Salad" "BLT Sandwich" "Lentil Soup" "Quinoa Bowl" "Tuna Melt")
    SUGGESTIONS_dinner=("Beef Tacos" "Spaghetti Bolognese" "Grilled Salmon" "Vegetable Curry" "Pork Chops")
    SUGGESTIONS_snack=("Apple Slices" "Mixed Nuts" "Rice Cakes" "Hummus & Veggies" "Protein Bar")

    VARNAME="SUGGESTIONS_${TYPE}"
    declare -n ARR="${VARNAME}" 2>/dev/null || { echo "Unknown type: ${TYPE}" >&2; exit 1; }
    IDX=$((RANDOM % ${#ARR[@]}))
    echo "Suggested ${TYPE}: ${ARR[$IDX]}"
    ;;

  *)
    echo "Usage: script.sh <add|list|plan|nutrition|shopping|random> [args...]" >&2
    exit 1
    ;;
esac
"""

(workspace / "scripts" / "script.sh").write_text(script_content)

print(f"Workspace generated at: {workspace}")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")