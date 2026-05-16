import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic deeply nested directory structure with distractor files
dirs = [
    "workspace/travel_platform/products/guides",
    "workspace/travel_platform/products/templates",
    "workspace/travel_platform/products/archived",
    "workspace/travel_platform/data/destinations",
    "workspace/travel_platform/data/user_profiles",
    "workspace/travel_platform/assets/icons",
    "workspace/travel_platform/assets/css",
    "workspace/travel_platform/backend/routes",
    "workspace/travel_platform/backend/config",
    "workspace/marketing/campaigns/q4",
    "workspace/marketing/campaigns/q3_archive",
]

for d in dirs:
    os.makedirs(os.path.join("/", d), exist_ok=True)

# Distractor files - realistic but irrelevant
distractors = {
    "workspace/travel_platform/products/guides/japan_hiking_guide.txt": """Japan Hiking Guide
Difficulty: Intermediate
Best season: Spring/Autumn
Popular trails: Nakasendo, Kumano Kodo
""",
    "workspace/travel_platform/products/guides/europe_rail_pass.txt": """Europe Rail Pass Information
Eurail Pass coverage: 33 countries
Types: Global, Regional, One-Country
Reservation required for high-speed trains
""",
    "workspace/travel_platform/products/templates/hotel_booking_template.html": """<!DOCTYPE html>
<html><head><title>Hotel Booking</title></head>
<body><h1>Hotel Booking Confirmation</h1></body></html>
""",
    "workspace/travel_platform/products/archived/old_car_rental_v1.html": """<!DOCTYPE html>
<html><head><title>Old Car Rental Guide</title></head>
<body><h1>Outdated Car Rental Info - DO NOT USE</h1>
<p>This template is deprecated as of 2022.</p>
</body></html>
""",
    "workspace/travel_platform/data/destinations/norway_fjords.json": """{
  "destination": "Norway",
  "region": "Fjords",
  "highlights": ["Geirangerfjord", "Nærøyfjord", "Hardangerfjord"],
  "best_months": ["June", "July", "August"]
}
""",
    "workspace/travel_platform/data/destinations/southeast_asia.json": """{
  "destination": "Southeast Asia",
  "countries": ["Thailand", "Vietnam", "Cambodia", "Indonesia"],
  "travel_style": "backpacker"
}
""",
    "workspace/travel_platform/data/user_profiles/premium_users.csv": """user_id,age,travel_style,preferred_destination
1001,34,adventure,Europe
1002,28,luxury,Asia
1003,45,family,Americas
1004,31,backpacker,Southeast Asia
""",
    "workspace/travel_platform/assets/css/main.css": """body { font-family: Arial, sans-serif; }
.card { border-radius: 8px; padding: 16px; }
.header { background: #003366; color: white; }
""",
    "workspace/travel_platform/assets/icons/map_pin.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
</svg>
""",
    "workspace/travel_platform/backend/routes/api_routes.py": """# API Routes
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/destinations')
def get_destinations():
    return jsonify({'destinations': ['Norway', 'Japan', 'France']})
""",
    "workspace/travel_platform/backend/config/db_config.yaml": """database:
  host: localhost
  port: 5432
  name: travel_db
  pool_size: 10
""",
    "workspace/marketing/campaigns/q4/car_rental_promotion.txt": """Q4 Car Rental Promotion Plan
Target: Family travelers
Discount: 15% off SUV category
Markets: Norway, Iceland, New Zealand
Budget: $50,000 USD
""",
    "workspace/marketing/campaigns/q3_archive/summer_deals.txt": """Summer 2023 Deals - ARCHIVED
Europe road trips promotion
Key performance: 2,400 bookings
Average trip: 8 days
""",
    "workspace/travel_platform/products/guides/new_zealand_self_drive_notes.txt": """New Zealand Self-Drive Notes (DRAFT - incomplete)
- Drive on left side of road
- International Driving Permit may be required
- Freedom camping regulations vary
- Alpine roads can close in winter
NOTE: This is a rough draft, do not publish.
""",
}

for filepath, content in distractors.items():
    full_path = os.path.join("/", filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# The actual task request file - written as a product manager's brief
task_brief = """产品需求简报
====================
项目：租车自驾行前计划页面
请求人：产品经理 - 出行体验组
日期：2024-01-15

背景：
我们的平台需要为即将前往挪威自驾的用户生成一份完整的行前计划指南页面。

用户画像：
- 目的地：挪威（Norway）
- 行程时长：10天
- 出行人群：带小孩的家庭（含儿童）
- 驾驶经验：新手（第一次在境外自驾）
- 路线类型：跨区域路线（计划从挪威跨入瑞典）
- 驾车偏好：自动挡
- 出行风格：以风景为主，希望多看峡湾和自然风光

输出要求：
请生成一份完整的HTML页面，文件名为 norway_selfdrive_plan.html
该页面将直接嵌入我们的产品中，供用户在出发前查阅。

备注：
- 确保覆盖所有必要的行前准备信息
- 内容需要适合带孩子的新手司机
- 跨境相关的注意事项需要特别处理
"""

with open("/workspace/task_brief.txt", "w", encoding="utf-8") as f:
    f.write(task_brief)

print("Workspace initialized successfully.")
print(f"Task brief written to /workspace/task_brief.txt")
print(f"Created {len(distractors)} distractor files.")