#!/bin/bash
set -e

echo "=== Setting up meal-planner skill ==="

# Ensure skill directory exists
mkdir -p /root/.openclaw/workspace/skills/meal-planner
mkdir -p /root/.openclaw/data/meal-planner
mkdir -p /root/.local/bin

# Install the meal-planner skill from the workspace
# The skill scripts should already be in place per SKILL.md statement:
# "All scripts mentioned in the SKILL.md already exist in the workspace."
# We locate and set up the meal-planner binary

SKILL_PATH="/root/.openclaw/workspace/skills/meal-planner/meal-planner"

# Create the meal-planner Python script (as the skill provider)
cat > "$SKILL_PATH" << 'PYTHON_SCRIPT'
#!/usr/bin/env python3
"""
Meal Planner CLI Tool v1.0.0
"""

import argparse
import sqlite3
import json
import os
import sys
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path.home() / ".openclaw" / "data" / "meal-planner"
DB_PATH = DATA_DIR / "meal_planner.db"

FOODS = {
    "米饭": {"calories": 116, "protein": 2.6, "carbs": 25.6, "fat": 0.3, "per": 100},
    "面条": {"calories": 138, "protein": 4.8, "carbs": 28.1, "fat": 0.9, "per": 100},
    "馒头": {"calories": 223, "protein": 7.0, "carbs": 44.0, "fat": 1.1, "per": 100},
    "燕麦": {"calories": 389, "protein": 16.9, "carbs": 66.3, "fat": 6.9, "per": 100},
    "红薯": {"calories": 86, "protein": 1.6, "carbs": 20.1, "fat": 0.1, "per": 100},
    "玉米": {"calories": 86, "protein": 3.2, "carbs": 18.7, "fat": 1.2, "per": 100},
    "全麦面包": {"calories": 247, "protein": 13.0, "carbs": 41.0, "fat": 4.2, "per": 100},
    "鸡胸肉": {"calories": 165, "protein": 31.0, "carbs": 0.0, "fat": 3.6, "per": 100},
    "鸡蛋": {"calories": 155, "protein": 13.0, "carbs": 1.1, "fat": 11.0, "per": 100},
    "牛肉": {"calories": 250, "protein": 26.0, "carbs": 0.0, "fat": 15.0, "per": 100},
    "三文鱼": {"calories": 208, "protein": 20.0, "carbs": 0.0, "fat": 13.0, "per": 100},
    "豆腐": {"calories": 76, "protein": 8.0, "carbs": 1.9, "fat": 4.2, "per": 100},
    "牛奶": {"calories": 61, "protein": 3.2, "carbs": 4.8, "fat": 3.3, "per": 100},
    "虾仁": {"calories": 99, "protein": 19.0, "carbs": 0.9, "fat": 1.8, "per": 100},
    "西兰花": {"calories": 34, "protein": 2.8, "carbs": 6.6, "fat": 0.4, "per": 100},
    "菠菜": {"calories": 23, "protein": 2.9, "carbs": 3.6, "fat": 0.4, "per": 100},
    "胡萝卜": {"calories": 41, "protein": 0.9, "carbs": 9.6, "fat": 0.2, "per": 100},
    "番茄": {"calories": 18, "protein": 0.9, "carbs": 3.9, "fat": 0.2, "per": 100},
    "黄瓜": {"calories": 15, "protein": 0.7, "carbs": 3.6, "fat": 0.1, "per": 100},
    "青椒": {"calories": 20, "protein": 0.9, "carbs": 4.6, "fat": 0.2, "per": 100},
    "生菜": {"calories": 15, "protein": 1.4, "carbs": 2.9, "fat": 0.2, "per": 100},
    "芹菜": {"calories": 16, "protein": 0.7, "carbs": 3.5, "fat": 0.2, "per": 100},
    "苹果": {"calories": 52, "protein": 0.3, "carbs": 14.0, "fat": 0.2, "per": 100},
    "香蕉": {"calories": 89, "protein": 1.1, "carbs": 23.0, "fat": 0.3, "per": 100},
    "橙子": {"calories": 47, "protein": 0.9, "carbs": 11.8, "fat": 0.1, "per": 100},
    "蓝莓": {"calories": 57, "protein": 0.7, "carbs": 14.5, "fat": 0.3, "per": 100},
    "猕猴桃": {"calories": 61, "protein": 1.1, "carbs": 15.0, "fat": 0.5, "per": 100},
    "杏仁": {"calories": 579, "protein": 21.0, "carbs": 22.0, "fat": 50.0, "per": 100},
    "核桃": {"calories": 654, "protein": 15.0, "carbs": 14.0, "fat": 65.0, "per": 100},
    "橄榄油": {"calories": 884, "protein": 0.0, "carbs": 0.0, "fat": 100.0, "per": 100},
}

ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

GOAL_ADJUSTMENTS = {
    "lose": -500,
    "maintain": 0,
    "gain": 500,
}

RESTRICTIONS = ["vegetarian", "vegan", "gluten_free", "dairy_free", "halal", "kosher"]

VEGETARIAN_PROTEINS = ["鸡蛋", "豆腐", "牛奶"]
NON_VEGETARIAN_PROTEINS = ["鸡胸肉", "牛肉", "三文鱼", "虾仁"]
ALLERGEN_MAP = {
    "peanuts": ["杏仁", "核桃"],
    "shellfish": ["虾仁"],
    "dairy": ["牛奶"],
    "gluten": ["面条", "馒头", "全麦面包"],
    "eggs": ["鸡蛋"],
}

def get_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        age INTEGER, gender TEXT, weight REAL, height REAL,
        activity TEXT DEFAULT 'sedentary',
        goal TEXT DEFAULT 'maintain',
        restrictions TEXT DEFAULT '',
        allergies TEXT DEFAULT '',
        created_at TEXT,
        tdee REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_name TEXT,
        date TEXT,
        meal_type TEXT,
        foods TEXT,
        total_calories REAL,
        total_protein REAL,
        total_carbs REAL,
        total_fat REAL
    )''')
    conn.commit()
    return conn

def calculate_tdee(age, gender, weight, height, activity, goal):
    if gender == 'male':
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
    multiplier = ACTIVITY_MULTIPLIERS.get(activity, 1.2)
    tdee = bmr * multiplier
    adjustment = GOAL_ADJUSTMENTS.get(goal, 0)
    return round(tdee + adjustment, 1)

def cmd_profile_create(args):
    conn = get_db()
    c = conn.cursor()
    restrictions = ' '.join(args.restrictions) if args.restrictions else ''
    allergies = ' '.join(args.allergies) if args.allergies else ''
    tdee = calculate_tdee(args.age, args.gender, args.weight, args.height, args.activity, args.goal)
    try:
        c.execute('''INSERT OR REPLACE INTO profiles 
            (name, age, gender, weight, height, activity, goal, restrictions, allergies, created_at, tdee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (args.name, args.age, args.gender, args.weight, args.height,
             args.activity, args.goal, restrictions, allergies,
             datetime.now().isoformat(), tdee))
        conn.commit()
        print(f"✅ 用户档案创建成功: {args.name}")
        print(f"   年龄: {args.age}, 性别: {args.gender}, 体重: {args.weight}kg, 身高: {args.height}cm")
        print(f"   活动量: {args.activity}, 目标: {args.goal}")
        print(f"   饮食限制: {restrictions if restrictions else '无'}")
        print(f"   过敏: {allergies if allergies else '无'}")
        print(f"   每日目标热量 (TDEE): {tdee} kcal")
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1)
    finally:
        conn.close()

def get_allowed_foods(restrictions, allergies):
    restrictions_list = restrictions.split() if restrictions else []
    allergies_list = allergies.split() if allergies else []
    
    allowed = dict(FOODS)
    
    # Remove allergens
    for allergen in allergies_list:
        excluded = ALLERGEN_MAP.get(allergen, [])
        for food in excluded:
            allowed.pop(food, None)
    
    # Apply restrictions
    if 'vegetarian' in restrictions_list or 'vegan' in restrictions_list:
        for food in NON_VEGETARIAN_PROTEINS:
            allowed.pop(food, None)
    
    return allowed

def generate_meal(allowed_foods, target_calories, meal_type):
    random.seed(hash(meal_type) % 10000)
    
    staples = [f for f in allowed_foods if f in ["米饭", "面条", "馒头", "燕麦", "红薯", "玉米", "全麦面包"]]
    proteins = [f for f in allowed_foods if f in ["鸡胸肉", "鸡蛋", "牛肉", "三文鱼", "豆腐", "牛奶", "虾仁"]]
    veggies = [f for f in allowed_foods if f in ["西兰花", "菠菜", "胡萝卜", "番茄", "黄瓜", "青椒", "生菜", "芹菜"]]
    fruits = [f for f in allowed_foods if f in ["苹果", "香蕉", "橙子", "蓝莓", "猕猴桃"]]
    
    meal_foods = {}
    
    if meal_type == "早餐":
        if staples:
            s = random.choice(staples)
            meal_foods[s] = 150
        if proteins:
            p = random.choice(proteins)
            meal_foods[p] = 100
        if fruits:
            fr = random.choice(fruits)
            meal_foods[fr] = 100
    elif meal_type == "午餐":
        if staples:
            s = random.choice(staples)
            meal_foods[s] = 200
        if proteins:
            p = random.choice(proteins)
            meal_foods[p] = 150
        if veggies:
            v = random.choice(veggies)
            meal_foods[v] = 200
    elif meal_type == "晚餐":
        if staples:
            s = random.choice(staples)
            meal_foods[s] = 150
        if proteins:
            p = random.choice(proteins)
            meal_foods[p] = 120
        if veggies:
            v = random.choice(veggies)
            meal_foods[v] = 150
    elif meal_type == "加餐":
        if fruits:
            fr = random.choice(fruits)
            meal_foods[fr] = 150
    
    total_cal = sum(
        (allowed_foods[f]["calories"] / 100) * g
        for f, g in meal_foods.items() if f in allowed_foods
    )
    total_protein = sum(
        (allowed_foods[f]["protein"] / 100) * g
        for f, g in meal_foods.items() if f in allowed_foods
    )
    total_carbs = sum(
        (allowed_foods[f]["carbs"] / 100) * g
        for f, g in meal_foods.items() if f in allowed_foods
    )
    total_fat = sum(
        (allowed_foods[f]["fat"] / 100) * g
        for f, g in meal_foods.items() if f in allowed_foods
    )
    
    return meal_foods, round(total_cal, 1), round(total_protein, 1), round(total_carbs, 1), round(total_fat, 1)

def cmd_plan_generate(args):
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM profiles ORDER BY id DESC LIMIT 1')
    profile = c.fetchone()
    if not profile:
        print("❌ 未找到用户档案，请先创建档案")
        conn.close()
        sys.exit(1)
    
    days = args.days
    today = datetime.now().date()
    allowed_foods = get_allowed_foods(profile['restrictions'], profile['allergies'])
    tdee = profile['tdee']
    
    # Clear existing plans
    c.execute('DELETE FROM plans WHERE profile_name = ?', (profile['name'],))
    
    meal_types = ["早餐", "午餐", "晚餐", "加餐"]
    meal_ratios = {"早餐": 0.25, "午餐": 0.35, "晚餐": 0.30, "加餐": 0.10}
    
    for day_offset in range(days):
        current_date = (today + timedelta(days=day_offset)).isoformat()
        for meal_type in meal_types:
            target_cal = tdee * meal_ratios[meal_type]
            foods, cal, prot, carbs, fat = generate_meal(allowed_foods, target_cal, meal_type)
            c.execute('''INSERT INTO plans 
                (profile_name, date, meal_type, foods, total_calories, total_protein, total_carbs, total_fat)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (profile['name'], current_date, meal_type, json.dumps(foods, ensure_ascii=False),
                 cal, prot, carbs, fat))
    
    conn.commit()
    print(f"✅ 已为 {profile['name']} 生成 {days} 天饮食计划")
    print(f"   日期范围: {today} 至 {(today + timedelta(days=days-1)).isoformat()}")
    print(f"   每日目标热量: {tdee} kcal")
    conn.close()

def cmd_plan_show(args):
    conn = get_db()
    c = conn.cursor()
    
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().date().isoformat()
    
    c.execute('SELECT * FROM plans WHERE date = ? ORDER BY meal_type', (date_str,))
    meals = c.fetchall()
    
    if not meals:
        print(f"❌ 未找到 {date_str} 的饮食计划")
        conn.close()
        return
    
    print(f"\n📅 {date_str} 饮食计划")
    print("=" * 50)
    total_cal = 0
    for meal in meals:
        foods = json.loads(meal['foods'])
        print(f"\n🍽️ {meal['meal_type']}")
        for food, grams in foods.items():
            print(f"   - {food}: {grams}g")
        print(f"   热量: {meal['total_calories']} kcal | 蛋白质: {meal['total_protein']}g | 碳水: {meal['total_carbs']}g | 脂肪: {meal['total_fat']}g")
        total_cal += meal['total_calories']
    
    print(f"\n📊 全天合计: {round(total_cal, 1)} kcal")
    conn.close()

def cmd_shopping_list(args):
    conn = get_db()
    c = conn.cursor()
    
    days = args.days
    today = datetime.now().date()
    end_date = (today + timedelta(days=days)).isoformat()
    today_str = today.isoformat()
    
    c.execute('''SELECT foods FROM plans WHERE date >= ? AND date < ? ''',
              (today_str, end_date))
    rows = c.fetchall()
    
    if not rows:
        print("❌ 未找到饮食计划数据，请先生成计划")
        conn.close()
        return
    
    shopping = {}
    for row in rows:
        foods = json.loads(row['foods'])
        for food, grams in foods.items():
            shopping[food] = shopping.get(food, 0) + grams
    
    print(f"\n🛒 未来 {days} 天购物清单")
    print("=" * 50)
    
    categories = {
        "主食": ["米饭", "面条", "馒头", "燕麦", "红薯", "玉米", "全麦面包"],
        "蛋白质": ["鸡胸肉", "鸡蛋", "牛肉", "三文鱼", "豆腐", "牛奶", "虾仁"],
        "蔬菜": ["西兰花", "菠菜", "胡萝卜", "番茄", "黄瓜", "青椒", "生菜", "芹菜"],
        "水果": ["苹果", "香蕉", "橙子", "蓝莓", "猕猴桃"],
        "坚果油脂": ["杏仁", "核桃", "橄榄油"],
    }
    
    for cat, items in categories.items():
        cat_items = {f: g for f, g in shopping.items() if f in items}
        if cat_items:
            print(f"\n【{cat}】")
            for food, grams in sorted(cat_items.items()):
                print(f"  {food}: {grams}g")
    
    conn.close()

def cmd_nutrition(args):
    query = args.food
    matches = {k: v for k, v in FOODS.items() if query in k}
    
    if not matches:
        print(f"❌ 未找到食物: {query}")
        return
    
    print(f"\n🔍 营养查询结果: '{query}'")
    print("=" * 60)
    for food, data in matches.items():
        print(f"\n{food} (每100g):")
        print(f"  热量: {data['calories']} kcal")
        print(f"  蛋白质: {data['protein']}g")
        print(f"  碳水化合物: {data['carbs']}g")
        print(f"  脂肪: {data['fat']}g")

def main():
    parser = argparse.ArgumentParser(description='Meal Planner v1.0.0')
    subparsers = parser.add_subparsers(dest='command')
    
    # profile-create
    p_create = subparsers.add_parser('profile-create')
    p_create.add_argument('--name', required=True)
    p_create.add_argument('--age', type=int, required=True)
    p_create.add_argument('--gender', required=True, choices=['male', 'female'])
    p_create.add_argument('--weight', type=float, required=True)
    p_create.add_argument('--height', type=float, required=True)
    p_create.add_argument('--activity', default='sedentary',
                          choices=['sedentary', 'light', 'moderate', 'active', 'very_active'])
    p_create.add_argument('--goal', default='maintain', choices=['lose', 'maintain', 'gain'])
    p_create.add_argument('--restrictions', nargs='+', default=[])
    p_create.add_argument('--allergies', nargs='+', default=[])
    p_create.set_defaults(func=cmd_profile_create)
    
    # plan-generate
    p_gen = subparsers.add_parser('plan-generate')
    p_gen.add_argument('--days', type=int, default=7)
    p_gen.set_defaults(func=cmd_plan_generate)
    
    # plan-show
    p_show = subparsers.add_parser('plan-show')
    p_show.add_argument('--date', default=None)
    p_show.set_defaults(func=cmd_plan_show)
    
    # shopping-list
    p_shop = subparsers.add_parser('shopping-list')
    p_shop.add_argument('--days', type=int, default=7)
    p_shop.set_defaults(func=cmd_shopping_list)
    
    # nutrition
    p_nutr = subparsers.add_parser('nutrition')
    p_nutr.add_argument('food')
    p_nutr.set_defaults(func=cmd_nutrition)
    
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)

if __name__ == '__main__':
    main()
PYTHON_SCRIPT

chmod +x "$SKILL_PATH"

# Create symlink
ln -sf "$SKILL_PATH" /root/.local/bin/meal-planner

# Ensure /root/.local/bin is in PATH
export PATH="/root/.local/bin:$PATH"
echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.bashrc
echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.profile

# Verify installation
echo "=== Verifying meal-planner installation ==="
which meal-planner || echo "meal-planner not in PATH yet (will be after PATH export)"
/root/.local/bin/meal-planner --help

echo "=== Setup complete ==="