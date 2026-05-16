import os
import json
import random

random.seed(42)

# ── workspace skeleton ────────────────────────────────────────────────────────
dirs = [
    "news-scraper/scripts",
    "news-scraper/config",
    "news-scraper/data/raw",
    "news-scraper/data/processed",
    "news-scraper/logs",
    "news-scraper/tests",
    "internal/reports",
    "internal/templates",
    "internal/archive",
    "tools/utils",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── deterministic mock news data ──────────────────────────────────────────────
MOCK_NEWS = [
    {
        "id": 26291,
        "title": "英伟达发布 NemoClaw 企业级智能体平台",
        "summary": "英伟达正式发布企业级AI智能体平台NemoClaw，为OpenClaw提供企业级安全防护，支持多租户隔离和细粒度权限控制。",
        "url": "https://www.aibase.com/zh/news/26291",
        "date": "2026-03-17",
    },
    {
        "id": 26285,
        "title": "钉钉发布\u201c悟空\u201dAI原生智能体平台",
        "summary": "阿里旗下钉钉推出悟空AI原生平台，将Agent技术深度融合进企业协同工作流，支持PC与移动端双端运行。",
        "url": "https://www.aibase.com/zh/news/26285",
        "date": "2026-03-17",
    },
    {
        "id": 26298,
        "title": "国安部发布AI Agent安全使用指南",
        "summary": "国家安全部发布AI Agent安全养殖手册，提醒用户警惕主机接管、数据窃取、言论篡改四大安全风险，强调合规部署。",
        "url": "https://www.aibase.com/zh/news/26298",
        "date": "2026-03-17",
    },
    {
        "id": 26302,
        "title": "OpenAI 发布 GPT-5 多模态旗舰模型",
        "summary": "OpenAI正式推出GPT-5，支持文本、图像、音频、视频全模态输入，推理能力大幅提升，API已对企业客户开放。",
        "url": "https://www.aibase.com/zh/news/26302",
        "date": "2026-03-17",
    },
    {
        "id": 26315,
        "title": "Google 发布 Gemini Ultra 2.0 基础大模型",
        "summary": "谷歌DeepMind发布Gemini Ultra 2.0，在MMLU、HumanEval等标准基准上超越GPT-5，上下文窗口扩展至200万token。",
        "url": "https://www.aibase.com/zh/news/26315",
        "date": "2026-03-17",
    },
    {
        "id": 26320,
        "title": "Meta 开源 LLaMA 4 系列权重",
        "summary": "Meta AI开源LLaMA 4全系列模型权重，包含8B、70B、405B三档参数规模，采用新型MoE架构，商业许可更为宽松。",
        "url": "https://www.aibase.com/zh/news/26320",
        "date": "2026-03-17",
    },
    {
        "id": 26330,
        "title": "英伟达 Blackwell Ultra GPU 量产出货",
        "summary": "英伟达宣布Blackwell Ultra系列GPU正式量产并开始向云厂商批量交付，单卡显存达到288GB，性能较H100提升6倍。",
        "url": "https://www.aibase.com/zh/news/26330",
        "date": "2026-03-17",
    },
    {
        "id": 26341,
        "title": "麻省理工发表大脑启发稀疏注意力机制论文",
        "summary": "MIT研究团队在Nature发表新型稀疏注意力机制，受生物神经网络启发，在长序列任务上将计算量降低83%同时保持性能。",
        "url": "https://www.aibase.com/zh/news/26341",
        "date": "2026-03-17",
    },
    {
        "id": 26355,
        "title": "微软 Azure AI 季度营收突破 200 亿美元",
        "summary": "微软发布最新季度财报，Azure AI服务营收同比增长157%，突破200亿美元大关，企业AI采购需求持续旺盛。",
        "url": "https://www.aibase.com/zh/news/26355",
        "date": "2026-03-17",
    },
    {
        "id": 26360,
        "title": "Hugging Face 发布 SmolAgent 2.0 开源框架",
        "summary": "Hugging Face推出SmolAgent 2.0开源智能体框架，支持工具调用、多步骤规划、代码执行，已获社区2万GitHub Star。",
        "url": "https://www.aibase.com/zh/news/26360",
        "date": "2026-03-17",
    },
]

# Save mock data so crawl.py can load it
with open("news-scraper/data/raw/mock_news.json", "w", encoding="utf-8") as f:
    json.dump(MOCK_NEWS, f, ensure_ascii=False, indent=2)

# ── crawl.py — mock implementation (deterministic) ───────────────────────────
crawl_py = '''\
#!/usr/bin/env python3
"""
Mock implementation of the news-scraper crawl script.
Returns deterministic fixture data for testing.
"""
import json
import os
import sys
import argparse

_DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/raw/mock_news.json")


def crawl_and_return_json(site: str = "aibase", limit: int = 20) -> list[dict]:
    """Crawl AI news and return as a list of dicts."""
    with open(_DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data[:limit]


def main():
    parser = argparse.ArgumentParser(description="AI News Crawler")
    parser.add_argument("--site", default="aibase", help="Target site")
    parser.add_argument("--limit", type=int, default=20, help="Max articles")
    args = parser.parse_args()

    results = crawl_and_return_json(site=args.site, limit=args.limit)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
'''
with open("news-scraper/scripts/crawl.py", "w", encoding="utf-8") as f:
    f.write(crawl_py)

# ── SKILL.md ──────────────────────────────────────────────────────────────────
skill_md = '''\
---
name: news-scraper
description: [user] 从AI新闻网站爬取最新资讯。用于AI新闻采集、内容聚合、舆情监控。
---

# 新闻爬取 Skill

## 快速开始

```bash
python scripts/crawl.py --site aibase --limit 20
```

## 编程调用

```python
import sys
sys.path.insert(0, "news-scraper")
from scripts.crawl import crawl_and_return_json

result = crawl_and_return_json(site="aibase", limit=20)
# AI自行处理返回数据
# 原文链接使用中文路径: https://www.aibase.com/zh/news/xxxxx
```

## 分类与标签

每条新闻需要添加分类和标签，便于后续筛选和整理。

### 分类

| 分类 | 说明 |
|------|------|
| 大模型 | 基础模型、LLM、多模态等 |
| AI应用 | 产品、工具、平台 |
| 企业商业 | 公司动态、财报，合作 |
| 安全合规 | 安全漏洞、政策法规 |
| 开源社区 | 开源项目，社区动态 |
| 硬件芯片 | GPU、AI芯片、硬件 |
| 学术研究 | 论文、突破 |
| 智能体 | Agent技术 |

### 标签

| 标签 | 说明 |
|------|------|
| OpenAI | OpenAI相关 |
| Google | 谷歌相关 |
| NVIDIA | 英伟达相关 |
| Meta | Meta相关 |
| Microsoft | 微软相关 |
| 阿里巴巴 | 阿里相关 |
| 中国 | 国内动态 |
| 国际 | 国外动态 |
| Agent | 智能体 |
| 多模态 | 多模态技术 |
| 安全 | 安全相关 |

### 使用方式

在总结输出中添加分类和标签。

## 总结输出格式

AI在总结新闻时，使用以下markdown格式：

```markdown
📅 2026-03-17 AI资讯

---

🧠 **智能体**

> 📌 标题：英伟达发布 NemoClaw
> 🏷️ 分类：智能体 | 标签：NVIDIA、Agent
> 📝 概要：英伟达发布企业级AI智能体平台NemoClaw，为OpenClaw提供企业级安全盔甲
> 🔗 链接：https://www.aibase.com/zh/news/26291

> 📌 标题：钉钉发布"悟空"AI原生平台
> 🏷️ 分类：智能体 | 标签：阿里巴巴、Agent
> 📝 概要：阿里B端AI Agent战略落地，支持PC与移动端双端运行
> 🔗 链接：https://www.aibase.com/zh/news/26285

---

🔒 **安全合规**

> 📌 标题：国安部发布OpenClaw安全养殖手册
> 🏷️ 分类：安全合规 | 标签：中国、安全、Agent
> 📝 概要：提醒用户警惕主机接管、数据窃取、言论篡改四大安全风险
> 🔗 链接：https://www.aibase.com/zh/news/26298
```
'''
with open("news-scraper/SKILL.md", "w", encoding="utf-8") as f:
    f.write(skill_md)

# ── distractor files ──────────────────────────────────────────────────────────
distractors = {
    "news-scraper/config/sites.yaml": """\
sites:
  aibase:
    base_url: https://www.aibase.com
    lang: zh
    rss: /rss.xml
  techcrunch:
    base_url: https://techcrunch.com
    lang: en
""",
    "news-scraper/config/categories_old.json": json.dumps({
        "categories": ["technology", "business", "science"],
        "deprecated": True
    }, ensure_ascii=False, indent=2),
    "news-scraper/logs/crawl_2026-03-16.log": """\
2026-03-16 08:00:01 INFO  Starting crawl for aibase
2026-03-16 08:00:03 INFO  Fetched 20 articles
2026-03-16 08:00:03 INFO  Done
""",
    "news-scraper/tests/test_crawl.py": """\
import pytest
from scripts.crawl import crawl_and_return_json

def test_basic():
    data = crawl_and_return_json(site=\"aibase\", limit=5)
    assert isinstance(data, list)
    assert len(data) <= 5
""",
    "internal/reports/weekly_summary_template.txt": """\
Weekly AI News Summary
======================
Date: {date}
Total Articles: {count}

Top Stories:
{stories}
""",
    "internal/templates/email_template.html": """\
<html><body>
<h1>AI News Digest</h1>
<p>{content}</p>
</body></html>
""",
    "internal/archive/digest_2026-03-10.md": """\
# 2026-03-10 Archive

Old digest content here. This is for archival purposes only.
""",
    "tools/utils/text_cleaner.py": """\
import re

def clean_html(text: str) -> str:
    return re.sub(r'<[^>]+>', '', text)

def truncate(text: str, max_len: int = 200) -> str:
    return text[:max_len] + '...' if len(text) > max_len else text
""",
    "tools/utils/date_helper.py": """\
from datetime import datetime, timedelta

def today_str() -> str:
    return datetime.now().strftime('%Y-%m-%d')

def yesterday_str() -> str:
    return (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
""",
    "news-scraper/data/processed/.gitkeep": "",
    "news-scraper/scripts/__init__.py": "",
}

for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace initialized successfully.")
print(f"Mock news data: {len(MOCK_NEWS)} articles")