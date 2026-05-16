import json
import os
import random

random.seed(42)

# ---- Directory structure ----
dirs = [
    "scripts",
    "config",
    "data",
    "data/archive",
    "data/archive/2025",
    "logs",
    "reports",
    "reports/weekly",
    "reports/monthly",
    "docs",
    "tests",
    "node_modules/.cache",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ---- Distractor files ----
distractors = {
    "docs/onboarding.md": "# Onboarding\nPlease read the internal wiki for setup instructions.",
    "docs/data_schema.md": "# Data Schema\nSee confluence for latest schema definitions.",
    "logs/app.log": "2026-03-14 12:00:00 INFO server started\n2026-03-14 12:01:00 INFO request processed\n",
    "logs/error.log": "2026-03-10 08:00:00 ERROR db connection timeout\n",
    "reports/weekly/week_2026_10.json": json.dumps({"week": 10, "avg_kcal": 1800}),
    "reports/monthly/march_2026_partial.json": json.dumps({"month": "2026-03", "entries": 14}),
    "data/archive/2025/food_log_2025.json": json.dumps([{"date": "2025-12-31", "kcal": 2100}]),
    "tests/test_placeholder.js": "// TODO: add unit tests\nconsole.log('no tests yet');",
    "node_modules/.cache/dummy": "cache",
    "config/app_config.json": json.dumps({"version": "1.0.0", "env": "production", "timezone": "Asia/Tokyo"}),
    ".env.example": "NODE_ENV=production\nPORT=3000\n",
}
for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# ---- health_targets.json (default lean_mass_gain mode) ----
targets = {
    "mode": "lean_mass_gain",
    "kcal": 2200,
    "protein": 165,
    "carbs": 275,
    "fat": 55,
    "water": 2000,
    "fiber": 25,
    "sugar_limit": 50,
    "sodium_limit": 2300,
    "sat_fat_limit": 16
}
with open("config/health_targets.json", "w") as f:
    json.dump(targets, f, indent=2)

# ---- food_log.json ----
# Target date is 2026-03-15. We create entries for multiple dates.
food_entries = []

# 2026-03-15: total kcal=1800, protein=130, carbs=200, fat=45, fiber=18, sugar=35, sodium=2100, sat_fat=12
meals_0315 = [
    {"date": "2026-03-15", "meal": "breakfast", "item": "Oatmeal with berries",
     "kcal": 350, "protein": 10, "carbs": 60, "fat": 6, "fiber": 5, "sugar": 12, "sodium": 150, "sat_fat": 1},
    {"date": "2026-03-15", "meal": "lunch", "item": "Grilled chicken salad",
     "kcal": 550, "protein": 55, "carbs": 30, "fat": 18, "fiber": 6, "sugar": 8, "sodium": 700, "sat_fat": 4},
    {"date": "2026-03-15", "meal": "dinner", "item": "Salmon with brown rice",
     "kcal": 650, "protein": 48, "carbs": 80, "fat": 15, "fiber": 5, "sugar": 10, "sodium": 900, "sat_fat": 5},
    {"date": "2026-03-15", "meal": "snack", "item": "Protein bar",
     "kcal": 250, "protein": 17, "carbs": 30, "fat": 6, "fiber": 2, "sugar": 5, "sodium": 350, "sat_fat": 2},
]
food_entries.extend(meals_0315)

# Other dates (distractors)
other_dates = ["2026-03-10", "2026-03-11", "2026-03-12", "2026-03-13", "2026-03-14", "2026-03-16", "2026-03-17"]
for d in other_dates:
    food_entries.append({
        "date": d, "meal": "lunch", "item": "Mixed meal",
        "kcal": random.randint(1600, 2400), "protein": random.randint(100, 180),
        "carbs": random.randint(150, 300), "fat": random.randint(40, 70),
        "fiber": random.randint(15, 30), "sugar": random.randint(20, 60),
        "sodium": random.randint(1200, 2800), "sat_fat": random.randint(8, 20)
    })

with open("data/food_log.json", "w") as f:
    json.dump(food_entries, f, indent=2)

# ---- weight_log.json ----
weight_entries = [
    {"date": "2026-03-10", "weight_kg": 70.5},
    {"date": "2026-03-11", "weight_kg": 70.3},
    {"date": "2026-03-12", "weight_kg": 70.4},
    {"date": "2026-03-13", "weight_kg": 70.2},
    {"date": "2026-03-14", "weight_kg": 70.1},
    {"date": "2026-03-15", "weight_kg": 69.8},
    {"date": "2026-03-16", "weight_kg": 69.9},
]
with open("data/weight_log.json", "w") as f:
    json.dump(weight_entries, f, indent=2)

# ---- sleep_log.json ----
sleep_entries = [
    {"date": "2026-03-10", "hours": 7.5},
    {"date": "2026-03-11", "hours": 6.5},
    {"date": "2026-03-12", "hours": 8.0},
    {"date": "2026-03-13", "hours": 7.0},
    {"date": "2026-03-14", "hours": 6.0},
    {"date": "2026-03-15", "hours": 7.5},
    {"date": "2026-03-16", "hours": 8.0},
]
with open("data/sleep_log.json", "w") as f:
    json.dump(sleep_entries, f, indent=2)

# ---- exercise_log.json ----
exercise_entries = [
    {"date": "2026-03-10", "minutes": 45},
    {"date": "2026-03-11", "minutes": 0},
    {"date": "2026-03-12", "minutes": 60},
    {"date": "2026-03-13", "minutes": 30},
    {"date": "2026-03-14", "minutes": 20},
    {"date": "2026-03-15", "minutes": 45},
    {"date": "2026-03-16", "minutes": 30},
]
with open("data/exercise_log.json", "w") as f:
    json.dump(exercise_entries, f, indent=2)

# ---- water_log.json ----
water_entries = [
    {"date": "2026-03-10", "ml": 2200},
    {"date": "2026-03-11", "ml": 1800},
    {"date": "2026-03-12", "ml": 2500},
    {"date": "2026-03-13", "ml": 1900},
    {"date": "2026-03-14", "ml": 1700},
    {"date": "2026-03-15", "ml": 1600},
    {"date": "2026-03-16", "ml": 2100},
]
with open("data/water_log.json", "w") as f:
    json.dump(water_entries, f, indent=2)

# ---- scripts/health_summary.js ----
# This is the proprietary script defined by SKILL.md
health_summary_js = r"""
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const mode = args[0]; // today, week, month
let targetDate = null;

for (const arg of args) {
  if (arg.startsWith('--date=')) {
    targetDate = arg.split('=')[1];
  }
}

if (!targetDate && mode === 'today') {
  const now = new Date();
  targetDate = now.toISOString().split('T')[0];
}

function loadJSON(file) {
  const fullPath = path.join(process.cwd(), file);
  return JSON.parse(fs.readFileSync(fullPath, 'utf-8'));
}

const targets = loadJSON('config/health_targets.json');
const foodLog = loadJSON('data/food_log.json');
const weightLog = loadJSON('data/weight_log.json');
const sleepLog = loadJSON('data/sleep_log.json');
const exerciseLog = loadJSON('data/exercise_log.json');
const waterLog = loadJSON('data/water_log.json');

function getDateRange(mode, targetDate) {
  if (mode === 'today') {
    return [targetDate, targetDate];
  } else if (mode === 'week') {
    const end = targetDate || new Date().toISOString().split('T')[0];
    const endDt = new Date(end);
    const startDt = new Date(endDt);
    startDt.setDate(startDt.getDate() - 6);
    return [startDt.toISOString().split('T')[0], end];
  } else if (mode === 'month') {
    const ref = targetDate || new Date().toISOString().split('T')[0];
    const [y, m] = ref.split('-');
    const start = `${y}-${m}-01`;
    const lastDay = new Date(parseInt(y), parseInt(m), 0).getDate();
    const end = `${y}-${m}-${String(lastDay).padStart(2, '0')}`;
    return [start, end];
  }
  return [targetDate, targetDate];
}

const [startDate, endDate] = getDateRange(mode, targetDate);

function inRange(date) {
  return date >= startDate && date <= endDate;
}

// Aggregate food
const filteredFood = foodLog.filter(e => inRange(e.date));
const totals = {
  kcal: 0, protein: 0, carbs: 0, fat: 0,
  fiber: 0, sugar: 0, sodium: 0, sat_fat: 0
};
for (const e of filteredFood) {
  totals.kcal += e.kcal || 0;
  totals.protein += e.protein || 0;
  totals.carbs += e.carbs || 0;
  totals.fat += e.fat || 0;
  totals.fiber += e.fiber || 0;
  totals.sugar += e.sugar || 0;
  totals.sodium += e.sodium || 0;
  totals.sat_fat += e.sat_fat || 0;
}

// Aggregate water
const filteredWater = waterLog.filter(e => inRange(e.date));
totals.water_ml = filteredWater.reduce((s, e) => s + (e.ml || 0), 0);

// Aggregate exercise
const filteredExercise = exerciseLog.filter(e => inRange(e.date));
totals.exercise_min = filteredExercise.reduce((s, e) => s + (e.minutes || 0), 0);

// Latest weight (on or before endDate)
const weightBefore = weightLog.filter(e => e.date <= endDate).sort((a,b) => b.date.localeCompare(a.date));
const latestWeight = weightBefore.length > 0 ? weightBefore[0].weight_kg : null;

// Latest sleep (on or before endDate)
const sleepBefore = sleepLog.filter(e => e.date <= endDate).sort((a,b) => b.date.localeCompare(a.date));
const latestSleep = sleepBefore.length > 0 ? sleepBefore[0].hours : null;

const result = {
  period: { mode, start: startDate, end: endDate },
  totals,
  targets: {
    kcal: targets.kcal,
    protein: targets.protein,
    carbs: targets.carbs,
    fat: targets.fat,
    water_ml: targets.water,
    fiber: targets.fiber,
    sugar_limit: targets.sugar_limit,
    sodium_limit: targets.sodium_limit,
    sat_fat_limit: targets.sat_fat_limit
  },
  deltas: {
    kcal: totals.kcal - targets.kcal,
    protein: totals.protein - targets.protein,
    carbs: totals.carbs - targets.carbs,
    fat: totals.fat - targets.fat,
    water_ml: totals.water_ml - targets.water,
    fiber: totals.fiber - targets.fiber,
    sugar: totals.sugar - targets.sugar_limit,
    sodium: totals.sodium - targets.sodium_limit,
    sat_fat: totals.sat_fat - targets.sat_fat_limit
  },
  latest_weight: latestWeight,
  latest_sleep: latestSleep
};

console.log(JSON.stringify(result, null, 2));
"""

with open("scripts/health_summary.js", "w") as f:
    f.write(health_summary_js)

print("Workspace setup complete.")
print("Key data for 2026-03-15:")
print("  Food totals: kcal=1800, protein=130, carbs=200, fat=45, fiber=18, sugar=35, sodium=2100, sat_fat=12")
print("  Water: 1600ml, Exercise: 45min, Weight: 69.8kg, Sleep: 7.5h")