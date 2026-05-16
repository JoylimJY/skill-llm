import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create deeply nested distractor directory structure
dirs = [
    "travel_ops/booking_logs/2024/Q1",
    "travel_ops/booking_logs/2024/Q2",
    "travel_ops/analytics/user_segments",
    "travel_ops/analytics/revenue",
    "product/roadmap/2025",
    "product/specs/legacy",
    "product/specs/current",
    "infra/monitoring/alerts",
    "infra/deployments/staging",
    "infra/deployments/prod",
    "marketing/campaigns/spring",
    "marketing/campaigns/summer",
    "data_pipelines/etl/flight_data",
    "data_pipelines/etl/hotel_data",
    "data_pipelines/reports",
    "reference",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files — realistic but irrelevant
distractor_files = {
    "travel_ops/booking_logs/2024/Q1/bookings_jan.csv": "booking_id,user_id,dest,amount\n1001,u42,SHA,3200\n1002,u17,CTU,5100\n",
    "travel_ops/booking_logs/2024/Q2/bookings_apr.csv": "booking_id,user_id,dest,amount\n2001,u88,XMN,2800\n2002,u55,SZX,4400\n",
    "travel_ops/analytics/user_segments/segments_v2.json": json.dumps({"segments": ["budget", "premium", "family", "solo"]}),
    "travel_ops/analytics/revenue/q1_summary.md": "# Q1 Revenue\nTotal: ¥4.2M\nFlight: ¥2.1M\nHotel: ¥1.8M\n",
    "product/roadmap/2025/q2_features.md": "# Q2 Features\n- Real-time seat alerts\n- Hotel bundle pricing\n- Group booking support\n",
    "product/specs/legacy/search_api_v1.md": "# Legacy Search API v1\nDeprecated. Use v3 instead.\n",
    "product/specs/current/search_api_v3.md": "# Search API v3\nEndpoint: /api/v3/search\nMethod: POST\nAuth: Bearer token\n",
    "infra/monitoring/alerts/pagerduty_config.yaml": "service: travel-search\nthreshold: 500ms\nescalation: oncall-team\n",
    "infra/deployments/staging/deploy_log.txt": "2025-06-01 03:12 - Deployed v2.3.1 to staging\n2025-06-02 11:45 - Rollback to v2.3.0\n",
    "infra/deployments/prod/deploy_log.txt": "2025-05-28 09:00 - Deployed v2.2.8 to prod\n",
    "marketing/campaigns/spring/email_list.txt": "user1@example.com\nuser2@example.com\n",
    "marketing/campaigns/summer/promo_codes.json": json.dumps({"codes": ["SUMMER20", "FLY50", "HOTEL30"]}),
    "data_pipelines/etl/flight_data/schema.json": json.dumps({"fields": ["flight_no", "origin", "dest", "dep_time", "price"]}),
    "data_pipelines/etl/hotel_data/schema.json": json.dumps({"fields": ["hotel_id", "name", "city", "price", "rating"]}),
    "data_pipelines/reports/weekly_kpi.md": "# Weekly KPI\nSearch requests: 12,400\nConversion rate: 3.2%\nAvg booking value: ¥3,800\n",
    "reference/deprecated_workflow_v1.md": "# Old Workflow (DEPRECATED)\nDo not use this file. Refer to the new workflow documentation.\n",
    "reference/internal_notes.txt": "NOTE: The sort-type parameter for hotel used to be 'price_asc', changed in v2. Check current docs.\n",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content, encoding="utf-8")

# Create the user profile file at ~/.flyai/user-profile.md
flyai_dir = Path.home() / ".flyai"
flyai_dir.mkdir(parents=True, exist_ok=True)

user_profile_content = """# FlyAI 用户旅行画像

> 最后更新: 2025-06-10 09:00

## 基础信息
- 常驻城市: 北京
- 出发机场: 首都国际机场

## 出行偏好
- 预算偏好: 中等(3000-8000/人)
- 出行人数: 1人
- 家庭成员: 单身
- 偏好类型: 历史文化、美食、城市探索
- 住宿偏好: 四星及以上

## 历史记录
- 去过城市: 上海、杭州、成都

## 特殊需求
- 宠物友好: 否
- 无障碍: 否
"""
(flyai_dir / "user-profile.md").write_text(user_profile_content, encoding="utf-8")

# Create the task brief file in workspace (the business scenario)
task_brief = """# 极限出发任务说明

## 场景
产品团队需要验证极限出发功能的端到端流程。

## 用户请求
用户：北京用户，当前时间2025年6月10日 10:00，3小时后可到机场，需要2天1晚行程，预算5000以内/人。

## 要求
请运行极限出发搜索，生成完整的出发方案，保存为 instant_departure_plan.md 文件。
"""
(workspace / "task_brief.md").write_text(task_brief, encoding="utf-8")

# Create a mock flyai call log directory
log_dir = workspace / ".flyai_mock_logs"
log_dir.mkdir(exist_ok=True)

print("Workspace generated successfully.")
print(f"User profile written to: {flyai_dir / 'user-profile.md'}")