import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Distractor directory structure ---
dirs = [
    "retail_project/raw_data/2026_Q1",
    "retail_project/raw_data/2026_Q2",
    "retail_project/reports/draft",
    "retail_project/reports/final",
    "retail_project/configs",
    "retail_project/logs/session_archive",
    "retail_project/templates",
    "retail_project/tools/scrapers",
    "retail_project/analysis/market",
    "retail_project/analysis/competitor",
    "system_cache/profiles",
    "system_cache/memory_store",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "retail_project/raw_data/2026_Q1/sales_raw.csv": "date,sku,qty,revenue\n2026-01-01,SKU001,120,3600\n2026-01-02,SKU002,85,2550\n",
    "retail_project/raw_data/2026_Q2/forecast.csv": "month,predicted_units\n2026-04,1500\n2026-05,1800\n",
    "retail_project/configs/pipeline.yaml": "pipeline:\n  steps:\n    - ingest\n    - normalize\n    - export\n",
    "retail_project/logs/session_archive/session_20260101.log": "[INFO] Session started\n[INFO] Module loaded\n[INFO] Session ended\n",
    "retail_project/logs/session_archive/session_20260210.log": "[INFO] Session started\n[WARN] Timeout in data fetch\n[INFO] Session ended\n",
    "retail_project/templates/report_template_v1.md": "# Report\n## Summary\n## Details\n## Recommendations\n",
    "retail_project/templates/report_template_v2.md": "# Executive Report\n## Key Findings\n## Action Items\n",
    "retail_project/tools/scrapers/weibo_scraper.py": "# Weibo scraper stub\ndef fetch(query): return []\n",
    "retail_project/tools/scrapers/zhihu_scraper.py": "# Zhihu scraper stub\ndef fetch(query): return []\n",
    "retail_project/analysis/market/segment_report.txt": "Market segment analysis for Q1 2026.\nKey segments: youth, urban professional.\n",
    "retail_project/analysis/competitor/comp_analysis.txt": "Competitor A: 32% market share\nCompetitor B: 18% market share\n",
    "system_cache/memory_store/old_session_dump.json": json.dumps({"session": "20260101", "status": "expired", "data": {}}),
}
for rel_path, content in distractors.items():
    with open(os.path.join(workspace, rel_path), "w") as f:
        f.write(content)

# --- CORE INPUT 1: User Profile (intentionally has realistic but tricky values) ---
# skip_rate = 0.72 (>0.60 → reduce confirmations)
# preferred_style = 'concise' (output concise)
# acceptance_rate = 0.82 (>0.70 → more recommendations)
# preferred_mode = 'parallel'
user_profile = {
    "user_id": "user_retail_007",
    "confirmation_habit": {
        "total_decisions": 50,
        "skip_count": 36,
        "skip_rate": 0.72,
        "avg_decision_time_ms": 420
    },
    "output_preference": {
        "detailed_count": 8,
        "concise_count": 22,
        "preferred_style": "concise"
    },
    "recommendation": {
        "total": 28,
        "accepted": 23,
        "acceptance_rate": 0.82
    },
    "execution": {
        "parallel_count": 31,
        "serial_count": 9,
        "preferred_mode": "parallel"
    },
    "module_preference": {
        "module_sequence_history": [
            "module_1->module_3->module_4",
            "module_1->module_2->module_4",
            "module_1->module_3",
            "module_1->module_4"
        ],
        "common_paths": ["module_1->module_3->module_4", "module_1->module_4"]
    },
    "updated_at": "2026-02-25T09:00:00Z"
}
with open(os.path.join(workspace, "system_cache/profiles/user_retail_007.json"), "w") as f:
    json.dump(user_profile, f, indent=2)

# --- CORE INPUT 2: Partial session log (messy, incomplete) ---
# The session has already run Module 1. The agent must continue the workflow.
partial_session = {
    "session_id": "session_20260225_retail_007",
    "user_id": "user_retail_007",
    "user_request": "帮我监控一下新茶饮行业的最新动态，顺便分析我们团队的工作状态，并且帮我们沉淀一下这次的工作流。不需要做内容创作。",
    "start_time": "2026-02-25T10:00:00Z",
    "current_module": "module_1",
    "execution_path": ["module_1"],
    "module_outputs": {
        "module_1": {
            "name": "AI信息守护者",
            "status": "completed",
            "output": {
                "A_grade": [
                    {"title": "新茶饮行业Q1融资热潮", "source": "36kr", "score": 9.1},
                    {"title": "蜜雪冰城海外扩张加速", "source": "华尔街见闻", "score": 8.8}
                ],
                "B_grade": [
                    {"title": "新茶饮门店坪效对比", "source": "知乎", "score": 7.2},
                    {"title": "原材料成本上涨影响分析", "source": "虎嗅", "score": 7.0}
                ],
                "C_grade": [
                    {"title": "网红茶饮排行榜", "source": "微博", "score": 5.5}
                ],
                "industry_trend": "新茶饮市场Q1资本活跃，出海赛道成新热点",
                "source_quality_score": 8.3
            },
            "memory_layer": "L0",
            "compress_target": "L2",
            "retention": "1小时"
        }
    },
    "user_choices": {},
    "status": "awaiting_continuation"
}
with open(os.path.join(workspace, "retail_project/logs/partial_session_20260225.json"), "w") as f:
    json.dump(partial_session, f, indent=2, ensure_ascii=False)

# --- CORE INPUT 3: A deliberately incomplete/wrong draft report (agent must NOT use this as-is) ---
# This is a distractor: wrong execution path, wrong memory layers, wrong adaptive decisions
wrong_draft = {
    "session_id": "session_20260225_retail_007",
    "NOTE": "THIS IS A DRAFT - DO NOT USE DIRECTLY - WRONG EXECUTION PATH",
    "execution_path_WRONG": "module_1 -> module_2 -> module_3 -> module_4",
    "adaptive_decisions_WRONG": {
        "reduce_confirmations": False,
        "output_style": "detailed",
        "more_recommendations": False,
        "preferred_execution": "serial"
    },
    "memory_summary_WRONG": {
        "stored_L0": 0,
        "stored_L2": 0,
        "stored_L3": 0,
        "stored_L4": 0
    }
}
with open(os.path.join(workspace, "retail_project/reports/draft/wrong_draft_report.json"), "w") as f:
    json.dump(wrong_draft, f, indent=2)

# Instruction file for agent
instruction = """# Task Brief

You are assisting the retail analytics team of a mid-size tea beverage chain.

A multi-agent AI assistant system has already started processing a market research session
for user `user_retail_007`. The session is partially complete (see logs/partial_session_20260225.json).

The user's request was: monitor new tea beverage (新茶饮) industry trends, analyze team 
status/growth insights, and consolidate the workflow — explicitly NO content creation needed.

The team's user behavioral profile is stored at: system_cache/profiles/user_retail_007.json

Your job is to produce the COMPLETE final session report as a file named `final_session_report.json`
in the `retail_project/reports/final/` directory.

This report must reflect:
1. The correct, complete execution path that the system should have taken for this request
2. The adaptive system decisions based on the user's behavioral profile  
3. The reflection evaluation scores for each module that was executed
4. The complete context data structure with correct memory layer assignments
5. The final memory summary (counts per layer) for the executed workflow
6. Reusable assets discovered and next-session recommendations

Base your work strictly on the system design documentation available in the workspace.
"""
with open(os.path.join(workspace, "TASK_BRIEF.md"), "w") as f:
    f.write(instruction)

print("Workspace initialized successfully.")