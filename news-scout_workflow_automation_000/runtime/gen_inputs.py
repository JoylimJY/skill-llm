import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create the full news-scout directory structure
dirs = [
    "news-scout/scripts",
    "news-scout/resources",
    "news-scout/logs",
    "news-scout/cache",
    "news-scout/archive",
    "news-scout/tests",
    "news-scout/config",
    "internal/reports/2024",
    "internal/templates",
    "internal/drafts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
(workspace / "internal/reports/2024/q3_summary.txt").write_text("Q3 2024 市场总结报告草稿。")
(workspace / "internal/reports/2024/q4_outlook.txt").write_text("Q4 2024 展望分析。")
(workspace / "internal/templates/briefing_template_old.md").write_text("# 旧版简报模板（已废弃）\n不再使用。")
(workspace / "internal/drafts/draft_report_20241101.md").write_text("草稿内容，待审核。")
(workspace / "news-scout/logs/scout_2024_10_30.log").write_text("2024-10-30 11:00:00 - 抓取完成，共获取 47 条。")
(workspace / "news-scout/logs/scout_2024_10_31.log").write_text("2024-10-31 08:30:00 - 抓取失败，网络超时。")
(workspace / "news-scout/cache/last_run_meta.json").write_text(json.dumps({"last_run": "2024-10-31", "count": 0}))
(workspace / "news-scout/archive/briefing_20241029.md").write_text("# 旧简报\n这是10月29日的存档简报。")
(workspace / "news-scout/tests/test_scout.py").write_text("# 测试脚本\nimport unittest\n# TODO: 添加测试用例\n")
(workspace / "news-scout/config/settings.yaml").write_text("debug: false\ntimeout: 30\nmax_retries: 3\n")
(workspace / "internal/templates/email_template.txt").write_text("主题：每日简报\n正文：见附件。")

# The mock scout.py script that outputs realistic messy JSON
scout_py = r'''#!/usr/bin/env python3
"""
news-scout 新闻抓取脚本（Mock版本，用于离线测试）
"""
import json
import argparse
import sys
from datetime import datetime

# Mock news data - intentionally messy, with duplicates, HTTP URLs, varied sources
MOCK_NEWS = [
    # ===== INVESTING =====
    {
        "id": "inv001",
        "category": "investing",
        "title": "美联储暗示将在12月暂停加息，市场反应强烈",
        "url": "https://finance.yahoo.com/news/fed-pause-rate-hike-december",
        "source": "Yahoo Finance",
        "source_priority": "P0",
        "summary": "美联储主席鲍威尔在最新讲话中暗示，考虑到通胀数据改善，12月会议可能暂停加息决定。",
        "date": "2024-11-01T09:00:00Z",
        "hot_score": 95
    },
    {
        "id": "inv001b",
        "category": "investing",
        "title": "Fed Chair Powell Hints at December Rate Pause",
        "url": "https://www.cnbc.com/2024/11/01/powell-hints-december-pause.html",
        "source": "CNBC",
        "source_priority": "P1",
        "summary": "Powell suggested the Fed may pause rate hikes in December as inflation eases.",
        "date": "2024-11-01T09:30:00Z",
        "hot_score": 91
    },
    {
        "id": "inv001c",
        "category": "investing",
        "title": "Powell: Fed Considering December Rate Pause",
        "url": "http://www.wsj.com/articles/powell-fed-december-pause",
        "source": "WSJ",
        "source_priority": "P1",
        "summary": "The Wall Street Journal reports on Powell's remarks about potential December pause.",
        "date": "2024-11-01T10:00:00Z",
        "hot_score": 88
    },
    {
        "id": "inv002",
        "category": "investing",
        "title": "英伟达Q3财报超预期，AI芯片需求强劲推动营收创历史新高",
        "url": "https://finance.yahoo.com/news/nvidia-q3-earnings-beat",
        "source": "Yahoo Finance",
        "source_priority": "P0",
        "summary": "英伟达第三季度营收同比增长206%，AI数据中心业务成为核心增长引擎。",
        "date": "2024-11-01T21:00:00Z",
        "hot_score": 89
    },
    {
        "id": "inv002b",
        "category": "investing",
        "title": "Nvidia Q3 Earnings Crush Estimates on AI Chip Demand",
        "url": "https://www.cnbc.com/2024/11/01/nvidia-q3-earnings.html",
        "source": "CNBC",
        "source_priority": "P1",
        "summary": "Nvidia reported record revenues driven by surging AI chip demand.",
        "date": "2024-11-01T21:30:00Z",
        "hot_score": 85
    },
    {
        "id": "inv003",
        "category": "investing",
        "title": "苹果公司宣布500亿美元股票回购计划",
        "url": "https://finance.yahoo.com/news/apple-50b-buyback",
        "source": "Yahoo Finance",
        "source_priority": "P0",
        "summary": "苹果宣布新一轮大规模股票回购，显示公司对自身长期价值的高度信心。",
        "date": "2024-11-01T20:00:00Z",
        "hot_score": 78
    },
    # ===== GLOBAL AI =====
    {
        "id": "ai001",
        "category": "ai_global",
        "title": "OpenAI发布GPT-5技术预览，推理能力大幅超越前代",
        "url": "https://openai.com/blog/gpt-5-preview",
        "source": "OpenAI Official Blog",
        "source_priority": "P0",
        "summary": "OpenAI正式发布GPT-5技术预览版，在复杂推理、代码生成和多语言理解方面取得重大突破。",
        "date": "2024-11-01T16:00:00Z",
        "hot_score": 99
    },
    {
        "id": "ai001b",
        "category": "ai_global",
        "title": "OpenAI Unveils GPT-5 Preview with Breakthrough Reasoning",
        "url": "https://techcrunch.com/2024/11/01/openai-gpt5-preview/",
        "source": "TechCrunch",
        "source_priority": "P1",
        "summary": "TechCrunch covers the GPT-5 preview release showing major reasoning improvements.",
        "date": "2024-11-01T16:30:00Z",
        "hot_score": 94
    },
    {
        "id": "ai001c",
        "category": "ai_global",
        "title": "GPT-5 Preview Released: What You Need to Know",
        "url": "https://www.theverge.com/2024/11/01/gpt5-preview",
        "source": "The Verge",
        "source_priority": "P1",
        "summary": "The Verge analysis of the GPT-5 preview capabilities and implications.",
        "date": "2024-11-01T17:00:00Z",
        "hot_score": 90
    },
    {
        "id": "ai002",
        "category": "ai_global",
        "title": "Google DeepMind发布新一代AlphaFold 3，蛋白质结构预测精度再创新高",
        "url": "https://deepmind.google/research/alphafold3",
        "source": "Google DeepMind Official",
        "source_priority": "P0",
        "summary": "AlphaFold 3将蛋白质结构预测扩展至所有生物分子，对新药研发具有里程碑意义。",
        "date": "2024-11-01T12:00:00Z",
        "hot_score": 87
    },
    {
        "id": "ai003",
        "category": "ai_global",
        "title": "Anthropic Claude 3.5更新：新增计算机操控功能，自主完成复杂桌面任务",
        "url": "https://www.anthropic.com/news/claude-35-update",
        "source": "Anthropic Official",
        "source_priority": "P0",
        "summary": "Claude 3.5新增Computer Use功能，可自主控制鼠标键盘完成复杂桌面操作任务。",
        "date": "2024-11-01T14:00:00Z",
        "hot_score": 83
    },
    {
        "id": "ai004",
        "category": "ai_global",
        "title": "MIT研究人员开发出无需GPU的低功耗AI推理芯片",
        "url": "https://techcrunch.com/2024/11/01/mit-low-power-ai-chip/",
        "source": "TechCrunch",
        "source_priority": "P1",
        "summary": "MIT团队展示功耗降低99%的AI推理芯片，为边缘AI部署带来新可能。",
        "date": "2024-11-01T08:00:00Z",
        "hot_score": 72
    },
    # ===== CHINA AI =====
    {
        "id": "cn001",
        "category": "ai_china",
        "title": "百度文心大模型4.0发布，宣称多项指标超越GPT-4 Turbo",
        "url": "https://ai.baidu.com/blog/ernie-4-release",
        "source": "百度AI官方博客",
        "source_priority": "P0",
        "summary": "百度文心4.0在中文理解、逻辑推理和创意写作方面全面升级，宣称超越GPT-4 Turbo。",
        "date": "2024-11-01T10:00:00Z",
        "hot_score": 88
    },
    {
        "id": "cn001b",
        "category": "ai_china",
        "title": "百度发布文心4.0：指标超GPT-4 Turbo",
        "url": "https://www.jiqizhixin.com/articles/ernie-4-launch",
        "source": "机器之心",
        "source_priority": "P1",
        "summary": "机器之心深度评测文心4.0，分析其在多个基准测试中的表现。",
        "date": "2024-11-01T11:00:00Z",
        "hot_score": 82
    },
    {
        "id": "cn002",
        "category": "ai_china",
        "title": "华为盘古大模型3.0正式商用，面向政企客户开放API",
        "url": "https://www.huawei.com/cn/news/pangu-30-commercial",
        "source": "华为官网",
        "source_priority": "P0",
        "summary": "华为盘古3.0正式开放商业化，聚焦政务、金融、医疗等垂直领域落地应用。",
        "date": "2024-11-01T09:00:00Z",
        "hot_score": 81
    },
    {
        "id": "cn003",
        "category": "ai_china",
        "title": "科技部发布《人工智能安全治理框架》1.0版，明确AI安全底线要求",
        "url": "https://www.most.gov.cn/news/ai-safety-framework",
        "source": "科技部官网",
        "source_priority": "P0",
        "summary": "科技部发布AI安全治理框架，从技术安全、内容安全和数据安全三个维度规范AI发展。",
        "date": "2024-11-01T15:00:00Z",
        "hot_score": 76
    },
    {
        "id": "cn004",
        "category": "ai_china",
        "title": "阿里巴巴通义千问开源新版本，支持128K超长上下文窗口",
        "url": "https://qwenlm.github.io/blog/qwen-128k",
        "source": "阿里通义实验室",
        "source_priority": "P0",
        "summary": "通义千问新版本支持128K上下文，处理超长文档能力大幅提升。",
        "date": "2024-11-01T13:00:00Z",
        "hot_score": 74
    },
]

def main():
    parser = argparse.ArgumentParser(description='news-scout 新闻抓取')
    parser.add_argument('--category', default='ai,investing',
                        help='新闻类别: ai, investing, 或 ai,investing')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    args = parser.parse_args()

    categories = [c.strip() for c in args.category.split(',')]

    filtered = []
    for item in MOCK_NEWS:
        cat = item['category']
        if 'ai' in categories and cat in ('ai_global', 'ai_china'):
            filtered.append(item)
        if 'investing' in categories and cat == 'investing':
            filtered.append(item)

    if args.debug:
        print(f"[DEBUG] Total items before filter: {len(MOCK_NEWS)}", file=sys.stderr)
        print(f"[DEBUG] Items after filter: {len(filtered)}", file=sys.stderr)

    result = {
        "status": "success",
        "total": len(filtered),
        "items": filtered,
        "fetched_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
'''
(workspace / "news-scout/scripts/scout.py").write_text(scout_py)

# news_sources.json
sources_config = {
    "version": "2.1",
    "priorities": {
        "P0": ["openai.com", "deepmind.google", "anthropic.com", "federalreserve.gov", "finance.yahoo.com"],
        "P1": ["theverge.com", "techcrunch.com", "cnbc.com", "wsj.com", "jiqizhixin.com", "qbitai.com"],
        "P2": ["medium.com", "reddit.com", "hackernews.com"]
    },
    "rss_feeds": {
        "ai_global": [
            {"url": "https://techcrunch.com/feed/", "priority": "P1"},
            {"url": "https://www.theverge.com/rss/index.xml", "priority": "P1"}
        ],
        "ai_china": [
            {"url": "https://www.jiqizhixin.com/rss", "priority": "P1"}
        ],
        "investing": [
            {"url": "https://finance.yahoo.com/rss/", "priority": "P0"},
            {"url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "priority": "P1"}
        ]
    }
}
(workspace / "news-scout/resources/news_sources.json").write_text(
    json.dumps(sources_config, ensure_ascii=False, indent=2)
)

print("Workspace setup complete.")
print(f"Files created: {list(workspace.rglob('*'))}")