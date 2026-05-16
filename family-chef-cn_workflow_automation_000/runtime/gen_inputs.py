import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Deeply nested distractor directory structure ---

# Distractor: old meal plans in wrong format
old_plans_dir = workspace / "archive" / "old_meal_plans" / "2023"
old_plans_dir.mkdir(parents=True, exist_ok=True)

with open(old_plans_dir / "jan_menu.txt", "w", encoding="utf-8") as f:
    f.write("周一: 红烧肉, 炒青菜\n周二: 番茄炒蛋, 米饭\n周三: 蒸鱼\n")

with open(old_plans_dir / "feb_menu.txt", "w", encoding="utf-8") as f:
    f.write("周一: 饺子\n周二: 炒面\n周三: 清蒸排骨\n")

# Distractor: corrupted profile with WRONG keys (English-only, missing 忌口)
wrong_profile_dir = workspace / "archive" / "profiles"
wrong_profile_dir.mkdir(parents=True, exist_ok=True)

with open(wrong_profile_dir / "old_profile.json", "w", encoding="utf-8") as f:
    json.dump({
        "familySize": 3,
        "weeklyBudget": 400,
        "location": "北京",
        "taste": "辣",
        "restrictions": "花生"
    }, f, ensure_ascii=False, indent=2)

# Distractor: a fake nutrition CSV with DIFFERENT values from the skill's table
nutrition_dir = workspace / "data" / "nutrition"
nutrition_dir.mkdir(parents=True, exist_ok=True)

with open(nutrition_dir / "nutrition_usda.csv", "w", encoding="utf-8") as f:
    f.write("food,calories_per_100g,protein_g,fat_g\n")
    f.write("鸡蛋,155,13.0,11.0\n")  # WRONG - USDA value, not skill's value (70 kcal)
    f.write("鸡胸肉,120,22.5,2.6\n")  # WRONG
    f.write("西红柿,18,0.9,0.2\n")
    f.write("米饭,130,2.7,0.3\n")  # WRONG

with open(nutrition_dir / "README_nutrition.txt", "w", encoding="utf-8") as f:
    f.write("This file uses USDA nutrition data. Values may differ from local Chinese databases.\n")

# Distractor: grocery price history
price_dir = workspace / "data" / "prices" / "shanghai"
price_dir.mkdir(parents=True, exist_ok=True)

with open(price_dir / "price_history_2023q4.json", "w", encoding="utf-8") as f:
    json.dump({
        "市场": "上海农贸市场",
        "数据日期": "2023-10-01",
        "价格": {
            "大白菜": "1.5元/斤",
            "胡萝卜": "2.0元/斤",
            "土豆": "1.8元/斤"
        }
    }, f, ensure_ascii=False, indent=2)

# Distractor: a partial/wrong weekly_meal_plan.json that the agent must OVERWRITE
with open(workspace / "weekly_meal_plan.json", "w", encoding="utf-8") as f:
    json.dump({
        "note": "This is an incomplete draft - do not use",
        "days": ["Monday", "Tuesday"]  # WRONG format, English, incomplete
    }, f, ensure_ascii=False, indent=2)

# Distractor: various config and log files
config_dir = workspace / "config"
config_dir.mkdir(parents=True, exist_ok=True)

with open(config_dir / "app_settings.json", "w", encoding="utf-8") as f:
    json.dump({
        "language": "zh-CN",
        "currency": "CNY",
        "default_servings": 4
    }, f, ensure_ascii=False, indent=2)

with open(config_dir / "db_config.yaml", "w", encoding="utf-8") as f:
    f.write("database:\n  host: localhost\n  port: 5432\n  name: chef_db\n")

logs_dir = workspace / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

with open(logs_dir / "access.log", "w", encoding="utf-8") as f:
    f.write("2024-10-01 10:00:00 - User query: 帮我规划菜单\n")
    f.write("2024-10-01 10:01:00 - Profile loaded\n")
    f.write("2024-10-01 10:02:00 - Menu generated\n")

with open(logs_dir / "error.log", "w", encoding="utf-8") as f:
    f.write("2024-10-01 09:59:00 - WARN: Profile file not found, starting fresh\n")

# Distractor: seasonal data in wrong/different format
seasonal_dir = workspace / "data" / "seasonal"
seasonal_dir.mkdir(parents=True, exist_ok=True)

with open(seasonal_dir / "veggies_spring_summer.txt", "w", encoding="utf-8") as f:
    f.write("春: 菠菜 芹菜 韭菜\n夏: 黄瓜 西红柿 茄子\n")

# Distractor: a template shopping list in wrong schema
shopping_dir = workspace / "templates"
shopping_dir.mkdir(parents=True, exist_ok=True)

with open(shopping_dir / "shopping_template.csv", "w", encoding="utf-8") as f:
    f.write("item,quantity,unit,estimated_price\n")
    f.write("template_item_1,1,kg,0\n")

# Distractor: README in English (not the skill's README)
with open(workspace / "NOTES.txt", "w", encoding="utf-8") as f:
    f.write("Project notes:\n- Do not use USDA nutrition values\n- Price data is outdated\n- Old profile format is deprecated\n")

# Distractor: a requirements.txt with unrelated packages
with open(workspace / "requirements.txt", "w") as f:
    f.write("requests==2.31.0\npandas==2.0.0\nnumpy==1.24.0\n")

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")
print("Distractor files:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p}")