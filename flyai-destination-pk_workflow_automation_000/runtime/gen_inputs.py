import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create deeply nested distractor directory structure ---
distractor_dirs = [
    "projects/travel-agency/clients/zhang_wei",
    "projects/travel-agency/clients/li_fang",
    "projects/travel-agency/templates/old_formats",
    "projects/travel-agency/reports/2024/q1",
    "projects/travel-agency/reports/2024/q2",
    "projects/travel-agency/data/flights",
    "projects/travel-agency/data/hotels",
    "projects/travel-agency/tools/deprecated",
    "notes/personal",
    "notes/work",
    "config/env",
    "tmp/scratch",
]

for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractors = {
    "projects/travel-agency/clients/zhang_wei/contact_info.txt": (
        "客户：张伟\n电话：138-xxxx-8888\n邮箱：zhangwei@example.com\n"
        "VIP等级：金牌会员\n常用出发城市：北京\n"
    ),
    "projects/travel-agency/clients/zhang_wei/past_trips.txt": (
        "2023-05 三亚 5天\n2023-10 厦门 3天\n2022-07 大理 6天\n"
    ),
    "projects/travel-agency/clients/li_fang/requirements.txt": (
        "目的地：巴黎 or 罗马\n日期：2024-12-20 至 2024-12-27\n预算：15000\n"
    ),
    "projects/travel-agency/templates/old_formats/comparison_v1.txt": (
        "旧版对比模板（已废弃）\n目的地A: ___\n目的地B: ___\n价格: ___\n\n注意：请使用新版工具生成报告\n"
    ),
    "projects/travel-agency/templates/old_formats/comparison_v2.md": (
        "# 旧版对比报告 v2\n\n| 目的地 | 机票 | 酒店 |\n|--------|------|------|\n"
        "| A      | TBD  | TBD  |\n\n*已废弃，请使用 flyai-destination-pk 工具*\n"
    ),
    "projects/travel-agency/reports/2024/q1/summary.md": (
        "# 2024 Q1 销售报告\n\n- 总订单: 342\n- 总收入: ¥1,234,567\n- 热门目的地: 东京, 曼谷, 新加坡\n"
    ),
    "projects/travel-agency/reports/2024/q2/summary.md": (
        "# 2024 Q2 销售报告\n\n- 总订单: 418\n- 总收入: ¥1,567,890\n- 热门目的地: 首尔, 大阪, 巴厘岛\n"
    ),
    "projects/travel-agency/data/flights/sample_flight_data.json": json.dumps({
        "note": "这是旧的静态示例数据，已不再维护",
        "sample": [
            {"origin": "北京", "dest": "东京", "price": 2800, "date": "2023-10-15"},
        ]
    }, ensure_ascii=False, indent=2),
    "projects/travel-agency/data/hotels/sample_hotel_data.json": json.dumps({
        "note": "旧的酒店价格参考，可能不准确",
        "sample": [
            {"dest": "东京", "hotel": "东京新宿酒店", "price_per_night": 680, "rating": 4.7},
        ]
    }, ensure_ascii=False, indent=2),
    "projects/travel-agency/tools/deprecated/old_compare.py": (
        "#!/usr/bin/env python3\n# 已废弃的对比脚本\n# 请使用 flyai CLI 代替\n\n"
        "def compare(a, b):\n    print(f'比较 {a} 和 {b}')\n    # TODO: 实现真实对比\n    pass\n"
    ),
    "notes/personal/travel_ideas.txt": (
        "想去的地方：\n- 北欧极光 (2025)\n- 新西兰 (2026)\n- 南极 (梦想)\n"
    ),
    "notes/work/client_notes.txt": (
        "张伟客户备注：\n- 非常注重性价比\n- 不喜欢中转航班\n- 偏好四星以上酒店\n- 有2个同伴一起出行\n"
        "李芳客户备注：\n- 偏好浪漫路线\n- 预算充足\n"
    ),
    "config/env/flyai_config_old.env": (
        "# 旧配置文件（已废弃）\nFLYAI_API_KEY=deprecated_key_123\nFLYAI_ENDPOINT=https://old.api.example.com\n"
        "# 注意：新版 flyai CLI 不再需要 API key\n"
    ),
    "tmp/scratch/test_commands.sh": (
        "#!/bin/bash\n# 测试命令草稿\n# flyai search-flight --origin 北京 --destination 东京 ...\n"
        "# 注意：这只是草稿，命令参数可能不完整\n"
    ),
}

for fpath, content in distractors.items():
    full_path = workspace / fpath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# --- Create the client request file (the actual task trigger) ---
client_request = """# 客户需求单

## 客户信息
- 姓名：张伟
- 常驻城市：北京
- 出发机场：首都机场

## 本次出行需求
- 候选目的地：东京、首尔、新加坡（三选一，纠结中）
- 出发日期：2024-10-15
- 返回日期：2024-10-20
- 出行天数：6天5晚
- 最在意维度：预算优先（花最少的钱）
- 同行人数：3人

## 要求
请为张伟客户生成一份三目的地的全维度对比报告，帮助他快速决策选哪个目的地。
报告文件命名为 destination_pk_report.md，保存在 /workspace/projects/travel-agency/clients/zhang_wei/ 目录下。
"""

(workspace / "projects/travel-agency/clients/zhang_wei/client_request.md").write_text(
    client_request, encoding="utf-8"
)

# --- Create a partial/outdated user profile (agent must update/use it) ---
flyai_dir = Path.home() / ".flyai"
flyai_dir.mkdir(parents=True, exist_ok=True)

user_profile = """# FlyAI 用户旅行画像

> 最后更新: 2024-01-10 09:00

## 基础信息
- 常驻城市: 北京
- 出发机场: 首都机场

## 出行偏好
- 预算偏好: 经济(2000-5000/人)
- 出行人数: 3人
- 家庭成员: 无小孩
- 偏好类型: 都市观光、购物、美食

## 历史记录
- 去过城市: 三亚、厦门、大理

## 特殊需求
- 宠物友好: 否
- 无障碍: 否
"""

(flyai_dir / "user-profile.md").write_text(user_profile, encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Files created in {workspace}")
print(f"User profile created at {flyai_dir / 'user-profile.md'}")