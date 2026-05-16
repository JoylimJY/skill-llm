import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create directory structure ---
dirs = [
    "report",
    "plans",
    "archive/2023",
    "archive/2024",
    "archive/2024/q1",
    "archive/2024/q2",
    "data/raw",
    "data/processed",
    "templates",
    "logs",
    "tools",
    "config",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

# 1. A stale old report (wrong format, wrong naming)
(workspace / "report" / "old_report_nev_2023.md").write_text(
    """# NEV Market Overview 2023
Some old data here. This is NOT in the correct format.
Sources: Various.
""", encoding="utf-8"
)

# 2. A fake template
(workspace / "templates" / "report_template.md").write_text(
    """# [TITLE]
## Introduction
## Analysis
## Conclusion
""", encoding="utf-8"
)

# 3. A fake index with existing entries (agent must APPEND, not overwrite)
(workspace / "index.md").write_text(
    """# Research Index

## Completed Reports

- [Global Semiconductor Supply Chain Analysis](report/ds_global_semiconductor_supply_chain_20240101_120000.md)
- [Renewable Energy Policy Comparison](report/ds_renewable_energy_policy_comparison_20240215_083000.md)

""", encoding="utf-8"
)

# 4. Archive distractor files
(workspace / "archive" / "2023" / "market_brief.txt").write_text(
    "Old market brief. NEV sales were 6.8M in 2022.\n", encoding="utf-8"
)

(workspace / "archive" / "2024" / "q1" / "draft_nev.md").write_text(
    "Draft notes. BYD, NIO, Li Auto. Not a real report.\n", encoding="utf-8"
)

(workspace / "archive" / "2024" / "q2" / "competitor_notes.txt").write_text(
    "Tesla China Q2 delivery notes - incomplete.\n", encoding="utf-8"
)

# 5. Data files (distractors)
(workspace / "data" / "raw" / "nev_sales_2024.csv").write_text(
    "month,brand,units\n2024-01,BYD,201493\n2024-02,BYD,122307\n2024-03,BYD,301042\n",
    encoding="utf-8"
)

(workspace / "data" / "processed" / "summary_stats.json").write_text(
    json.dumps({"total_nev_2024_q1": 624842, "top_brand": "BYD"}, indent=2),
    encoding="utf-8"
)

# 6. Logs
(workspace / "logs" / "search_log_20240510.txt").write_text(
    "2024-05-10 10:00:00 INFO Search executed: 新能源汽车\n2024-05-10 10:00:05 INFO 15 results returned\n",
    encoding="utf-8"
)

# 7. Config
(workspace / "config" / "settings.json").write_text(
    json.dumps({"language": "zh-CN", "max_results": 20, "timeout": 30}, indent=2),
    encoding="utf-8"
)

# 8. Tools distractor
(workspace / "tools" / "url_validator.py").write_text(
    """#!/usr/bin/env python3
# Utility: validates URLs
import sys
print(f"Validating: {sys.argv[1]}")
""", encoding="utf-8"
)

# 9. Another distractor plan (wrong format, already done)
(workspace / "plans" / "old_plan_20230801.json").write_text(
    json.dumps({
        "title": "旧调研计划",
        "status": "completed",
        "questions": ["旧问题"],
        "report_path": "report/old.md"
    }, indent=2), encoding="utf-8"
)

# --- THE ACTUAL RESEARCH PLAN (in Chinese, as required to trigger bilingual search) ---
research_plan = {
    "title": "中国新能源汽车市场竞争格局深度分析",
    "language": "zh-CN",
    "research_questions": [
        {
            "id": "q1",
            "question": "2024年中国新能源汽车市场的主要参与者有哪些？各品牌的市场份额和销量数据是多少？",
            "priority": "high"
        },
        {
            "id": "q2",
            "question": "中国新能源汽车市场的关键技术趋势是什么？包括电池技术、智能驾驶和充电基础设施。",
            "priority": "high"
        },
        {
            "id": "q3",
            "question": "中国政府对新能源汽车行业的最新政策支持和监管框架有哪些？",
            "priority": "medium"
        },
        {
            "id": "q4",
            "question": "中国新能源汽车品牌的海外扩张战略和出口表现如何？",
            "priority": "medium"
        }
    ],
    "scope": {
        "include": [
            "市场份额数据（2023-2024）",
            "主要OEM厂商分析：比亚迪、特斯拉中国、蔚来、小鹏、理想、华为问界",
            "电池技术对比（磷酸铁锂 vs 三元锂）",
            "政府补贴政策和双积分制度",
            "海外出口数据和市场进入策略"
        ],
        "exclude": [
            "燃油车市场",
            "2022年以前的数据",
            "摩托车和电动自行车"
        ]
    },
    "report_requirements": {
        "sections": [
            "Executive Summary",
            "Market Overview and Key Players",
            "Technology Trends",
            "Government Policy and Regulatory Framework",
            "International Expansion Strategies",
            "Competitive Landscape Analysis",
            "Conclusion and Outlook"
        ],
        "depth": "comprehensive",
        "min_sources": 12,
        "citation_format": "footnote"
    },
    "output": {
        "report_path_dir": "report/",
        "index_file": "index.md"
    }
}

(workspace / "plans" / "nev_research_plan.json").write_text(
    json.dumps(research_plan, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# 10. A misleadingly-named file to confuse agents
(workspace / "plans" / "research_plan_TEMPLATE.json").write_text(
    json.dumps({
        "title": "TEMPLATE - DO NOT USE",
        "language": "en",
        "research_questions": [],
        "scope": {},
        "report_requirements": {"sections": [], "depth": "shallow", "min_sources": 0},
        "output": {"report_path_dir": "report/", "index_file": "index.md"}
    }, indent=2), encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Research plan: {workspace / 'plans' / 'nev_research_plan.json'}")
print(f"Index file: {workspace / 'index.md'}")
print(f"Report dir: {workspace / 'report'}")