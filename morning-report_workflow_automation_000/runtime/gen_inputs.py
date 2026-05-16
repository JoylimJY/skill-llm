import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── distractor directory structure ──────────────────────────────────────────
dirs = [
    "archive/2024/Q1",
    "archive/2024/Q2",
    "archive/2024/Q3",
    "logs/cron",
    "logs/push",
    "config",
    "scripts/utils",
    "scripts/search",
    "data/competitors",
    "data/market",
    "templates/old",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "archive/2024/Q1/report_20240115.md": "# 晨报 2024-01-15\n旧版格式，仅供归档。",
    "archive/2024/Q2/report_20240410.md": "# 晨报 2024-04-10\n数据已过期。",
    "archive/2024/Q3/report_20240701.md": "# 旧晨报\n不符合当前模板。",
    "logs/cron/cron.log": "2025-01-10 07:30:01 morning-report triggered\n2025-01-11 07:30:00 morning-report triggered\n",
    "logs/push/dingtalk.log": "2025-01-11 07:31:22 SENT target=2735046220840628 status=200\n",
    "config/cron_config.yaml": "schedule: '30 7 * * *'\ncommand: run morning-report\ntimezone: Asia/Shanghai\n",
    "config/dingtalk_target.txt": "2735046220840628",
    "scripts/utils/date_helper.py": "import datetime\ndef get_weekday_cn(dt):\n    days=['周一','周二','周三','周四','周五','周六','周日']\n    return days[dt.weekday()]\n",
    "scripts/search/tavily_wrapper.py": "# wrapper for tavily search\ndef search(query, max_results=5):\n    raise NotImplementedError('use live tavily client')\n",
    "data/competitors/product_list.json": json.dumps([
        {"name": "Last War: Survival", "developer": "Century Games", "alias": "Last War"},
        {"name": "Whiteout Survival", "developer": "Century Games", "alias": "Whiteout"},
        {"name": "Kingshot", "developer": "Unknown", "alias": "Kingshot"},
        {"name": "Last Z: Shooter", "developer": "Unknown", "alias": "Last Z"},
    ], ensure_ascii=False, indent=2),
    "data/market/slg_top20_template.json": json.dumps({"note": "模板文件，非实时数据", "top20": []}, ensure_ascii=False),
    "templates/old/morning_report_v1.md": "**晨报**\n日期：{date}\n（旧模板，已废弃）\n",
}

for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.write_text(content, encoding="utf-8")

# ── raw search result data for the agent to use ─────────────────────────────
raw_data_dir = workspace / "raw_data"
raw_data_dir.mkdir(exist_ok=True)

# Section 1: AI & Game Industry News (has data)
section1 = {
    "section": "AI与游戏行业前沿资讯",
    "query_date": "2025-07-14",
    "results": [
        {
            "title": "Unity Announces AI-Powered NPC Dialogue System",
            "summary": "Unity Technologies unveiled a new AI-driven NPC dialogue generation tool at GDC, allowing developers to create dynamic conversations without scripting.",
            "source_name": "GameDeveloper",
            "url": "https://www.gamedeveloper.com/unity-ai-npc-2025",
            "date": "2025-07-13"
        },
        {
            "title": "Tencent's AI Game Testing Framework Goes Open Source",
            "summary": "腾讯宣布将其内部AI自动化测试框架开源，支持移动端游戏自动化回归测试，已在多款SLG产品中验证。",
            "source_name": "36kr",
            "url": "https://36kr.com/p/tencent-ai-test-2025",
            "date": "2025-07-13"
        },
        {
            "title": "Google DeepMind Partners with EA for Procedural Content Generation",
            "summary": "Google DeepMind and EA announced a research collaboration to apply generative AI for creating procedural game maps and mission structures.",
            "source_name": "TechCrunch",
            "url": "https://techcrunch.com/deepmind-ea-pcg-2025",
            "date": "2025-07-12"
        }
    ]
}

# Section 2: Competitor monitoring (has partial data — Kingshot and Last Z have no updates)
section2 = {
    "section": "竞品监控",
    "query_date": "2025-07-14",
    "products": {
        "Last War: Survival": {
            "ranking_ios": "#3",
            "ranking_gp": "#5",
            "trend": "↑",
            "ad_change": "新增末日风格视频素材，重点投放美区和中东",
            "version_update": "v2.18.0 上线，新增公会战2.0玩法",
            "source_url": "https://sensortower.com/last-war-july-2025",
            "source_name": "SensorTower"
        },
        "Whiteout Survival": {
            "ranking_ios": "#7",
            "ranking_gp": "#9",
            "trend": "→",
            "ad_change": "近期无明显变动",
            "version_update": "近期无明显变动",
            "source_url": "https://data.ai/whiteout-survival-2025-07",
            "source_name": "data.ai"
        },
        "Kingshot": {
            "ranking_ios": None,
            "ranking_gp": None,
            "trend": None,
            "ad_change": None,
            "version_update": None,
            "source_url": None,
            "source_name": None
        },
        "Last Z: Shooter": {
            "ranking_ios": None,
            "ranking_gp": None,
            "trend": None,
            "ad_change": None,
            "version_update": None,
            "source_url": None,
            "source_name": None
        }
    }
}

# Section 3: Competitor sentiment (has data for 2, missing for 2)
section3 = {
    "section": "竞品舆情",
    "query_date": "2025-07-14",
    "products": {
        "Last War: Survival": {
            "positive": {
                "original": "The new guild war update is absolutely fantastic. Finally a mode that requires real coordination instead of just spending money.",
                "platform": "Reddit",
                "url": "https://reddit.com/r/LastWarSurvival/comments/abc123"
            },
            "negative": {
                "original": "Energy system is completely broken after the update. I spent 3000 gems and got reset back to zero with no compensation.",
                "platform": "Reddit",
                "url": "https://reddit.com/r/LastWarSurvival/comments/def456"
            }
        },
        "Whiteout Survival": {
            "positive": {
                "original": "The winter event rewards are very generous this time, got two legendary equipment pieces from event shop alone.",
                "platform": "App Store",
                "url": "https://apps.apple.com/us/app/whiteout-survival/id123456"
            },
            "negative": {
                "original": "匹配系统太不公平了，我一个新手一直被老服玩家打，完全没有体验感，打算卸载。",
                "platform": "TapTap",
                "url": "https://www.taptap.cn/app/whiteout-survival/review/789"
            }
        },
        "Kingshot": {
            "positive": None,
            "negative": None
        },
        "Last Z: Shooter": {
            "positive": None,
            "negative": None
        }
    }
}

# Section 4: New SLG tests (has data)
section4 = {
    "section": "SLG新品测试",
    "query_date": "2025-07-14",
    "results": [
        {
            "name": "Iron Throne: Rise of Kingdoms",
            "developer": "Nexon",
            "stage": "CBT",
            "region": "北美、欧洲",
            "gameplay": "历史SLG，引入可动态变化的地图地形系统，城池攻防受地形影响",
            "url": "https://irothrone-cbt.nexon.com"
        }
    ]
}

# Section 5: Steam new games (EMPTY — triggers fallback)
section5 = {
    "section": "STEAM新游与新玩法",
    "query_date": "2025-07-14",
    "results": []
}

# Section 6: Reference data (partial — rankings available, CPM not available)
section6 = {
    "section": "参考数据",
    "query_date": "2025-07-14",
    "store_trends": "策略品类畅销榜Top10：Last War: Survival保持前5，Whiteout Survival小幅下滑，Rise of Kingdoms稳定在#12附近。",
    "store_source": "SensorTower公开数据",
    "store_url": None,
    "ad_cpi_cpm": None
}

# Task metadata
task_meta = {
    "report_date": "2025-07-14",
    "weekday_cn": "星期一",
    "instructions": (
        "请根据 raw_data/ 目录下的6个JSON数据文件，生成一份完整的每日晨报。"
        "按照团队的晨报规范（参见SKILL.md / morning-report skill文档）输出钉钉兼容的Markdown格式。"
        "输出文件名为 morning_report.md，保存在工作目录根目录下。"
    )
}

sections = [
    ("section1_ai_news.json", section1),
    ("section2_competitor_monitor.json", section2),
    ("section3_competitor_sentiment.json", section3),
    ("section4_slg_new_tests.json", section4),
    ("section5_steam_games.json", section5),
    ("section6_reference_data.json", section6),
]

for fname, data in sections:
    (raw_data_dir / fname).write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

(raw_data_dir / "task_meta.json").write_text(
    json.dumps(task_meta, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Files created under: {workspace}")