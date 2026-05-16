#!/bin/bash
set -e

WORKSPACE="/workspace"

# Create the scripts directory and the main script
mkdir -p "$WORKSPACE/scripts"

cat > "$WORKSPACE/scripts/script.sh" << 'SCRIPT_EOF'
#!/usr/bin/env bash
set -euo pipefail

DIET_DIR="$HOME/.diet"
MEALS_FILE="$DIET_DIR/meals.json"
WATER_FILE="$DIET_DIR/water.json"

mkdir -p "$DIET_DIR"

# Initialize files if they don't exist
[ -f "$MEALS_FILE" ] || echo "[]" > "$MEALS_FILE"
[ -f "$WATER_FILE" ] || echo "[]" > "$WATER_FILE"

TODAY=$(date +%Y-%m-%d)

cmd="${1:-}"
shift || true

case "$cmd" in

  log)
    food_item="${1:?food_item required}"
    calories="${2:?calories required}"
    protein="${3:?protein_g required}"
    carbs="${4:?carbs_g required}"
    fat="${5:?fat_g required}"
    meal_type="${6:-snack}"

    python3 - <<PYEOF
import json, datetime

with open("$MEALS_FILE") as f:
    data = json.load(f)

entry = {
    "date": "$TODAY",
    "food": "$food_item",
    "calories": float("$calories"),
    "protein_g": float("$protein"),
    "carbs_g": float("$carbs"),
    "fat_g": float("$fat"),
    "meal_type": "$meal_type"
}

data.append(entry)

with open("$MEALS_FILE", "w") as f:
    json.dump(data, f, indent=2)

print(f"Logged: $food_item ({meal_type}) — $calories kcal | P:${protein}g C:${carbs}g F:${fat}g")
PYEOF
    ;;

  calories)
    date_arg="${1:-$TODAY}"
    python3 - <<PYEOF
import json

with open("$MEALS_FILE") as f:
    data = json.load(f)

total = sum(e["calories"] for e in data if e.get("date") == "$date_arg")
print(f"Total calories on $date_arg: {total:.0f} kcal")
PYEOF
    ;;

  macros)
    date_arg="${1:-$TODAY}"
    python3 - <<PYEOF
import json

with open("$MEALS_FILE") as f:
    data = json.load(f)

entries = [e for e in data if e.get("date") == "$date_arg"]
protein = sum(e["protein_g"] for e in entries)
carbs   = sum(e["carbs_g"]   for e in entries)
fat     = sum(e["fat_g"]     for e in entries)
total_cal = protein*4 + carbs*4 + fat*9

if total_cal == 0:
    print(f"No data for $date_arg")
else:
    print(f"Macros for $date_arg:")
    print(f"  Protein : {protein:.1f}g  ({protein*4/total_cal*100:.1f}%)")
    print(f"  Carbs   : {carbs:.1f}g  ({carbs*4/total_cal*100:.1f}%)")
    print(f"  Fat     : {fat:.1f}g  ({fat*9/total_cal*100:.1f}%)")
PYEOF
    ;;

  water)
    ml="${1:?ml required}"
    date_arg="${2:-$TODAY}"
    python3 - <<PYEOF
import json

with open("$WATER_FILE") as f:
    data = json.load(f)

entry = {"date": "$date_arg", "ml": float("$ml")}
data.append(entry)

with open("$WATER_FILE", "w") as f:
    json.dump(data, f, indent=2)

print(f"Logged ${ml}ml of water on $date_arg")
PYEOF
    ;;

  plan)
    target_cal="${1:?target_calories required}"
    days="${2:?days required}"
    python3 - <<PYEOF
import json, random

random.seed(0)

with open("$MEALS_FILE") as f:
    data = json.load(f)

if not data:
    print("No logged foods available to build a plan.")
    exit(0)

print(f"Meal Plan — Target: $target_cal kcal/day for $days day(s)")
print("=" * 50)

for day in range(1, int("$days") + 1):
    print(f"\nDay {day}:")
    remaining = float("$target_cal")
    meal_types = ["breakfast", "lunch", "dinner", "snack"]
    for mtype in meal_types:
        candidates = [e for e in data if e.get("meal_type") == mtype]
        if not candidates:
            candidates = data
        pick = random.choice(candidates)
        print(f"  {mtype.capitalize():12s}: {pick['food']} ({pick['calories']:.0f} kcal)")
        remaining -= pick["calories"]
    print(f"  Estimated daily total variance: {abs(remaining):.0f} kcal from target")
PYEOF
    ;;

  report)
    report_type="${1:-daily}"
    date_arg="${2:-$TODAY}"
    python3 - <<PYEOF
import json, datetime

with open("$MEALS_FILE") as f:
    meals = json.load(f)
with open("$WATER_FILE") as f:
    water = json.load(f)

def day_summary(d):
    entries = [e for e in meals if e.get("date") == d]
    cal = sum(e["calories"] for e in entries)
    prot = sum(e["protein_g"] for e in entries)
    carbs = sum(e["carbs_g"] for e in entries)
    fat = sum(e["fat_g"] for e in entries)
    w = sum(e["ml"] for e in water if e.get("date") == d)
    return {"date": d, "calories": cal, "protein_g": prot, "carbs_g": carbs, "fat_g": fat, "water_ml": w, "meals": len(entries)}

if "$report_type" == "weekly":
    base = datetime.date.fromisoformat("$date_arg")
    dates = [(base - datetime.timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    print(f"Weekly Nutrition Report (7 days ending $date_arg)")
    print("=" * 60)
    for d in dates:
        s = day_summary(d)
        print(f"  {d}: {s['calories']:.0f} kcal | P:{s['protein_g']:.1f}g C:{s['carbs_g']:.1f}g F:{s['fat_g']:.1f}g | Water:{s['water_ml']:.0f}ml | Meals:{s['meals']}")
else:
    s = day_summary("$date_arg")
    print(f"Daily Nutrition Report for $date_arg")
    print("=" * 40)
    print(f"  Calories : {s['calories']:.0f} kcal")
    print(f"  Protein  : {s['protein_g']:.1f}g")
    print(f"  Carbs    : {s['carbs_g']:.1f}g")
    print(f"  Fat      : {s['fat_g']:.1f}g")
    print(f"  Water    : {s['water_ml']:.0f}ml")
    print(f"  Meals    : {s['meals']}")
PYEOF
    ;;

  *)
    echo "Unknown command: $cmd"
    echo "Usage: script.sh [log|calories|macros|water|plan|report] ..."
    exit 1
    ;;
esac
SCRIPT_EOF

chmod +x "$WORKSPACE/scripts/script.sh"

# Ensure ~/.diet doesn't pre-exist
rm -rf "$HOME/.diet"

echo "Setup complete. Script ready at /workspace/scripts/script.sh"