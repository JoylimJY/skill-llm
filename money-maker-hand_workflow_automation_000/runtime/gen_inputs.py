import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure (distractor files) ──────────────────────────────────
dirs = [
    "data/raw",
    "data/processed",
    "reports/archive",
    "reports/drafts",
    "config",
    "scripts",
    "notes/research",
    "notes/ideas",
    "logs",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "data/raw/zhihu_scrape_raw.txt": (
        "爆款: 便利店故事 -- 浏览量: 12万\n"
        "科幻短篇: 月球基地 -- 浏览量: 4万\n"
        "悬疑: 邻居失踪 -- 浏览量: 8万\n"
    ),
    "data/raw/xiaohongshu_notes.txt": (
        "AI工具教程 笔记爆款 -- 点赞: 3000\n"
        "效率提升分享 -- 点赞: 1500\n"
        "副业指南 -- 点赞: 800\n"
    ),
    "data/processed/dedup_records.csv": (
        "id,source,amount\n1,zhihu,0\n2,xiaohongshu,0\n3,skill,0\n"
    ),
    "config/app_config.toml": (
        "[income]\n"
        "income_goal = 10000\n"
        "income_sources = [\"知乎盐选\", \"小红书\", \"Skill 开发\", \"外包\"]\n"
        "[report]\n"
        "report_schedule = \"weekly_sunday\"\n"
        "min_opportunity_score = 60\n"
        "max_opportunities = 10\n"
        "output_format = \"markdown\"\n"
    ),
    "scripts/fetch_upwork.py": (
        "# placeholder fetch script\nprint('upwork data fetched')\n"
    ),
    "notes/research/upwork_search.txt": (
        "AI content writing: $25-80/hr, high demand\n"
        "Python automation: $30-100/hr, medium demand\n"
        "Translation CN-EN: $15-25/hr, medium demand\n"
        "Data labeling: $10-20/hr, low demand\n"
    ),
    "notes/research/clawhub_skills.txt": (
        "自媒体文案 Skill: 定价 199 元, 销量 50+\n"
        "爆款标题生成: 定价 99 元, 销量 120+\n"
        "短视频脚本: 定价 299 元, 销量 30+\n"
    ),
    "notes/ideas/brainstorm_20240101.txt": (
        "想法1: 知乎专栏付费\n想法2: 微信公众号广告\n想法3: 视频号带货\n"
    ),
    "logs/activity_log.txt": (
        "2024-01-01: 完成知乎盐选投稿\n"
        "2024-01-02: 开始小红书账号注册\n"
        "2024-01-03: 调研 ClawHub 定价\n"
    ),
    "tmp/scratch.txt": "临时笔记: 记得跟进审核结果\n",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── The MESSY, INCOMPLETE income_database.json (problem input) ───────────────
# This is intentionally malformed: missing fields, wrong schema, no scoring done
income_database = {
    "meta": {
        "version": "0.9",
        "last_updated": "2024-01-02",
        "notes": "draft - needs scoring and completion"
    },
    "income_sources": [
        {
            "name": "知乎盐选",
            "target": 5000,
            "current": 0,
            "status": "审核中"
        },
        {
            "name": "小红书",
            "target": 3000,
            "current": 0,
            "status": "待发布"
        },
        {
            "name": "Skill 开发",
            "target": 2000,
            "current": 0,
            "status": "准备中"
        },
        {
            "name": "外包接单",
            "target": 1000,
            "current": 0,
            "status": "待启动"
        }
    ],
    "opportunities_raw": [
        {
            "name": "知乎盐选投稿",
            "notes": "便利店夜班已投稿，等审核。搜索量大，竞争激烈。单篇稿费500-5000元。技能完全匹配。已完成，零追加投入。",
            "market_demand_raw": 28,
            "monetization_raw": 27,
            "entry_barrier_raw": 18,
            "time_investment_raw": 19
        },
        {
            "name": "小红书起号",
            "notes": "AI工具教程，搜索热度高，竞争中等。月入1000-10000元。需学习平台规则。每天2小时。",
            "market_demand_raw": 25,
            "monetization_raw": 26,
            "entry_barrier_raw": 14,
            "time_investment_raw": 15
        },
        {
            "name": "Skill 开发外包",
            "notes": "为OpenClaw用户开发Skills，需求稳定但量少。500-2000元/个。技术门槛中等。1-2天/个。",
            "market_demand_raw": 18,
            "monetization_raw": 22,
            "entry_barrier_raw": 13,
            "time_investment_raw": 15
        },
        {
            "name": "知乎问答带货",
            "notes": "AI工具推荐+分销，搜索量中等，竞争较多。月入100-1000元。入门门槛低。每天1小时。",
            "market_demand_raw": 20,
            "monetization_raw": 14,
            "entry_barrier_raw": 16,
            "time_investment_raw": 15
        },
        {
            "name": "技术文档翻译",
            "notes": "OpenClaw中文文档维护，需求小众。月入500-1000元。语言要求高。每周2小时轻量。",
            "market_demand_raw": 12,
            "monetization_raw": 12,
            "entry_barrier_raw": 10,
            "time_investment_raw": 17
        },
        {
            "name": "数据标注兼职",
            "notes": "平台需求低，价格压低。月入200-500元。无门槛。时间消耗大。",
            "market_demand_raw": 10,
            "monetization_raw": 8,
            "entry_barrier_raw": 18,
            "time_investment_raw": 5
        },
        {
            "name": "视频号带货",
            "notes": "流量红利期但竞争极大，入门难。月入不稳定。需要出镜。每天3小时以上。",
            "market_demand_raw": 22,
            "monetization_raw": 18,
            "entry_barrier_raw": 5,
            "time_investment_raw": 6
        }
    ],
    "dashboard": {}
}

with open(os.path.join(workspace, "income_database.json"), "w", encoding="utf-8") as f:
    json.dump(income_database, f, ensure_ascii=False, indent=2)

# ── Partial/stale dashboard file ─────────────────────────────────────────────
stale_dashboard = {
    "money_maker_income_month": 0,
    "money_maker_income_goal": 10000,
    "money_maker_progress_percent": 0,
    "money_maker_days_remaining": 28,
    "money_maker_daily_target": 0,
    "money_maker_opportunities_found": 0,
    "money_maker_reports_generated": 0,
    "money_maker_last_report_date": None
}

with open(os.path.join(workspace, "dashboard_metrics.json"), "w", encoding="utf-8") as f:
    json.dump(stale_dashboard, f, ensure_ascii=False, indent=2)

# ── State memory stub ─────────────────────────────────────────────────────────
state_stub = {
    "state_key": "money_maker_state",
    "last_phase_completed": 2,
    "initialized": True,
    "run_count": 1
}

with open(os.path.join(workspace, "money_maker_state.json"), "w", encoding="utf-8") as f:
    json.dump(state_stub, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")