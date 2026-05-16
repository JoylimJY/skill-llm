import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor structure
dirs = [
    "projects/travel-app/src/components",
    "projects/travel-app/src/utils",
    "projects/travel-app/tests",
    "projects/travel-app/docs",
    "data/cities/hangzhou",
    "data/cities/chengdu",
    "data/cities/beijing",
    "config/environments",
    "scripts/automation",
    "logs/2024",
    "cache/poi",
    ".flyai",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "projects/travel-app/src/components/MapView.jsx": "// MapView component\nexport default function MapView({ pois }) {\n  return <div>{pois.map(p => p.name)}</div>;\n}",
    "projects/travel-app/src/components/FilterPanel.jsx": "// FilterPanel\nexport default function FilterPanel() { return null; }",
    "projects/travel-app/src/utils/geo.js": "function haversine(lat1, lon1, lat2, lon2) { return 0; }\nmodule.exports = { haversine };",
    "projects/travel-app/src/utils/format.js": "function formatDate(d) { return d.toISOString(); }\nmodule.exports = { formatDate };",
    "projects/travel-app/tests/geo.test.js": "const { haversine } = require('../src/utils/geo');\ntest('haversine', () => { expect(haversine(0,0,0,0)).toBe(0); });",
    "projects/travel-app/docs/api.md": "# API Documentation\n\nSee endpoints below.",
    "data/cities/hangzhou/overview.json": json.dumps({
        "city": "杭州",
        "province": "浙江",
        "population": 12000000,
        "famous_for": ["西湖", "龙井茶", "电子商务"]
    }, ensure_ascii=False, indent=2),
    "data/cities/chengdu/overview.json": json.dumps({
        "city": "成都",
        "province": "四川",
        "population": 20000000,
        "famous_for": ["熊猫", "火锅", "宽窄巷子"]
    }, ensure_ascii=False, indent=2),
    "data/cities/beijing/overview.json": json.dumps({
        "city": "北京",
        "province": "北京市",
        "population": 21500000,
        "famous_for": ["故宫", "长城", "天安门"]
    }, ensure_ascii=False, indent=2),
    "config/environments/dev.json": json.dumps({
        "env": "development",
        "api_base": "https://dev-api.flyai.example.com",
        "timeout": 30
    }, indent=2),
    "config/environments/prod.json": json.dumps({
        "env": "production",
        "api_base": "https://api.flyai.example.com",
        "timeout": 10
    }, indent=2),
    "scripts/automation/sync_pois.sh": "#!/bin/bash\n# Sync POI data from remote\necho 'Syncing...'",
    "logs/2024/app.log": "2024-01-15 10:23:11 INFO  Server started\n2024-01-15 10:23:12 INFO  Connected to DB\n2024-01-15 10:24:00 WARN  Slow query detected",
    "cache/poi/last_sync.json": json.dumps({"last_sync": "2024-01-15T10:00:00Z", "count": 0}, indent=2),
    ".flyai/user-profile.md": """# FlyAI 用户旅行画像

> 最后更新: 2024-03-01 09:00

## 基础信息
- 常驻城市: 杭州
- 出发机场: 萧山机场

## 出行偏好
- 预算偏好: 中等(3000-8000/人)
- 出行人数: 4人
- 家庭成员: 有小孩(2岁)
- 偏好类型: 亲子、自然风光
- 住宿偏好: 四星及以上

## 历史记录
- 去过城市: 三亚、厦门

## 特殊需求
- 宠物友好: 否
- 无障碍: 是
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create the task brief file
task_brief = """# 旅行推荐任务说明

## 客户信息
- 客户姓名: 李女士
- 目的地: 杭州
- 出行天数: 3天
- 出发时间: 下个月

## 同行人组成
- 李女士本人（成人）
- 丈夫（成人）
- 女儿（2岁，婴幼儿）
- 婆婆（70岁，腿脚不便，需要轮椅辅助）

## 需求
需要根据同行人特点，从 FlyAI 搜索杭州景点，
为这个特殊家庭组合生成专属推荐报告。
"""

with open(os.path.join(workspace, "task_brief.md"), "w", encoding="utf-8") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1} files in {workspace}")