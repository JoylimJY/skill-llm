#!/usr/bin/env python3
"""
Generate the sandbox workspace for the news aggregator skill evaluation.
Creates a realistic project structure with distractor files and a mock fetch_news.py
that simulates the real tool's behavior (returns deterministic JSON).
"""

import os
import json
import random
import sys
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

# ─── Directory Structure ────────────────────────────────────────────────────
dirs = [
    "scripts",
    "reports",
    "templates",
    "data/raw",
    "data/processed",
    "data/cache",
    "config",
    "logs",
    "archive/2024",
    "archive/2025",
    "notebooks",
    "tests",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor Files ────────────────────────────────────────────────────────
(WORKSPACE / "config" / "sources.yaml").write_text(
    "sources:\n  - hackernews\n  - github\n  - wallstreetcn\n  - 36kr\ndefault_limit: 10\n"
)
(WORKSPACE / "config" / "schedule.json").write_text(
    json.dumps({"cron": "0 8 * * *", "timezone": "Asia/Shanghai", "enabled": True}, indent=2)
)
(WORKSPACE / "logs" / "fetch_2025_06_01.log").write_text(
    "[INFO] Fetching hackernews... OK (12 items)\n[INFO] Fetching github... OK (15 items)\n[WARN] wallstreetcn timeout\n"
)
(WORKSPACE / "logs" / "fetch_2025_06_02.log").write_text(
    "[INFO] Fetching all sources... OK\n[INFO] Total: 87 items\n"
)
(WORKSPACE / "data" / "raw" / "hn_dump_20250601.json").write_text(
    json.dumps([{"id": i, "title": f"Story {i}", "score": random.randint(10, 500)} for i in range(20)], indent=2)
)
(WORKSPACE / "data" / "processed" / "finance_trends_june.csv").write_text(
    "date,topic,mentions\n2025-06-01,AI,342\n2025-06-01,Crypto,87\n2025-06-02,LLM,201\n"
)
(WORKSPACE / "data" / "cache" / ".gitkeep").write_text("")
(WORKSPACE / "notebooks" / "analysis.py").write_text(
    "# Trend Analysis\nimport pandas as pd\ndf = pd.read_csv('../data/processed/finance_trends_june.csv')\nprint(df.describe())\n"
)
(WORKSPACE / "tests" / "test_fetch.py").write_text(
    "import subprocess\ndef test_help():\n    r = subprocess.run(['python3','scripts/fetch_news.py','--help'], capture_output=True)\n    assert r.returncode == 0\n"
)
(WORKSPACE / "archive" / "2024" / "report_20241201.md").write_text(
    "# December 2024 Briefing\n## Top Stories\n- Item A\n- Item B\n"
)
(WORKSPACE / "archive" / "2025" / "report_20250101.md").write_text(
    "# January 2025 Briefing\n## Top Stories\n- New Year AI Boom\n"
)
(WORKSPACE / "templates" / "report_template.md").write_text(
    "# {title}\n**Date**: {date}\n**Sources**: {sources}\n\n{body}\n"
)
(WORKSPACE / "templates" / "email_template.html").write_text(
    "<html><body><h1>{title}</h1><p>{summary}</p></body></html>\n"
)

# ─── SKILL.md ───────────────────────────────────────────────────────────────
skill_md = r"""---
name: news-aggregator-skill
description: "Comprehensive news aggregator that fetches, filters, and deeply analyzes real-time content from 8 major sources: Hacker News, GitHub Trending, Product Hunt, 36Kr, Tencent News, WallStreetCN, V2EX, and Weibo. Best for 'daily scans', 'tech news briefings', 'finance updates', and 'deep interpretations' of hot topics."
---

# News Aggregator Skill

Fetch real-time hot news from multiple sources.

## Tools

### fetch_news.py

**Usage:**

```bash
### Single Source (Limit 10)
```bash
### Global Scan (Option 12) - **Broad Fetch Strategy**
> **NOTE**: This strategy is specifically for the "Global Scan" scenario where we want to catch all trends.

```bash
#  1. Fetch broadly (Massive pool for Semantic Filtering)
python3 scripts/fetch_news.py --source all --limit 15 --deep

# 2. SEMANTIC FILTERING:
# Agent manually filters the broad list (approx 120 items) for user's topics.
```

### Single Source & Combinations (Smart Keyword Expansion)
**CRITICAL**: You MUST automatically expand the user's simple keywords to cover the entire domain field.
*   User: "AI" -> Agent uses: `--keyword "AI,LLM,GPT,Claude,Generative,Machine Learning,RAG,Agent"`
*   User: "Android" -> Agent uses: `--keyword "Android,Kotlin,Google,Mobile,App"`
*   User: "Finance" -> Agent uses: `--keyword "Finance,Stock,Market,Economy,Crypto,Gold"`

```bash
# Example: User asked for "AI news from HN" (Note the expanded keywords)
python3 scripts/fetch_news.py --source hackernews --limit 20 --keyword "AI,LLM,GPT,DeepSeek,Agent" --deep
```

### Specific Keyword Search
Only use `--keyword` for very specific, unique terms (e.g., "DeepSeek", "OpenAI").
```bash
python3 scripts/fetch_news.py --source all --limit 10 --keyword "DeepSeek" --deep
```

**Arguments:**

- `--source`: One of `hackernews`, `weibo`, `github`, `36kr`, `producthunt`, `v2ex`, `tencent`, `wallstreetcn`, `all`.
- `--limit`: Maximum items per source (default 10).
- `--keyword`: Comma-separated filters (e.g. "AI,GPT").
- `--deep`: **[NEW]** Enable deep fetching. Downloads and extracts the main text content of the articles.

**Output:**
JSON array. If `--deep` is used, items will contain a `content` field associated with the article text.

## Interactive Menu

When the user says **"news-aggregator-skill 如意如意"** (or similar "menu/help" triggers):
1.  **READ** the content of `templates.md` in the skill directory.
2.  **DISPLAY** the list of available commands to the user exactly as they appear in the file.
3.  **GUIDE** the user to select a number or copy the command to execute.

### Smart Time Filtering & Reporting (CRITICAL)
If the user requests a specific time window (e.g., "past X hours") and the results are sparse (< 5 items):
1.  **Prioritize User Window**: First, list all items that strictly fall within the user's requested time (Time < X).
2.  **Smart Fill**: If the list is short, you MUST include high-value/high-heat items from a wider range (e.g. past 24h) to ensure the report provides at least 5 meaningful insights.
2.  **Annotation**: Clearly mark these older items (e.g., "⚠️ 18h ago", "🔥 24h Hot") so the user knows they are supplementary.
3.  **High Value**: Always prioritize "SOTA", "Major Release", or "High Heat" items even if they slightly exceed the time window.
4.  **GitHub Trending Exception**: For purely list-based sources like **GitHub Trending**, strictly return the valid items from the fetched list (e.g. Top 10). **List ALL fetched items**. Do **NOT** perform "Smart Fill".
    *   **Deep Analysis (Required)**: For EACH item, you **MUST** leverage your AI capabilities to analyze:
        *   **Core Value (核心价值)**: What specific problem does it solve? Why is it trending?
        *   **Inspiration (启发思考)**: What technical or product insights can be drawn?
        *   **Scenarios (场景标签)**: 3-5 keywords (e.g. `#RAG #LocalFirst #Rust`).

### 6. Response Guidelines (CRITICAL)

**Format & Style:**
- **Language**: Simplified Chinese (简体中文).
- **Style**: Magazine/Newsletter style (e.g., "The Economist" or "Morning Brew" vibe). Professional, concise, yet engaging.
- **Structure**:
    - **Global Headlines**: Top 3-5 most critical stories across all domains.
    - **Tech & AI**: Specific section for AI, LLM, and Tech items.
    - **Finance / Social**: Other strong categories if relevant.
- **Item Format**:
    - **Title**: **MUST be a Markdown Link** to the original URL.
        - ✅ Correct: `### 1. [OpenAI Releases GPT-5](https://...)`
        - ❌ Incorrect: `### 1. OpenAI Releases GPT-5`
    - **Metadata Line**: Must include Source, **Time/Date**, and Heat/Score.
    - **1-Liner Summary**: A punchy, "so what?" summary.
    - **Deep Interpretation (Bulleted)**: 2-3 bullet points explaining *why* this matters, technical details, or context. (Required for "Deep Scan").

**Output Artifact:**
- Always save the full report to `reports/` directory with a timestamped filename (e.g., `reports/hn_news_YYYYMMDD_HHMM.md`).
- Present the full report content to the user in the chat.
"""

(WORKSPACE / "SKILL.md").write_text(skill_md)

# ─── Mock fetch_news.py ──────────────────────────────────────────────────────
# This simulates the real tool. Returns deterministic but realistic JSON.
mock_fetch = r'''#!/usr/bin/env python3
"""
Mock implementation of fetch_news.py for sandbox evaluation.
Accepts the same CLI arguments as the real tool and returns deterministic JSON.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
import random

random.seed(99)

GITHUB_ITEMS = [
    {"id":"gh1","title":"mem0ai/mem0","url":"https://github.com/mem0ai/mem0","source":"github",
     "time": (datetime.now()-timedelta(hours=3)).isoformat(),
     "score":2847,"content":"mem0 is a memory layer for AI assistants enabling persistent context across conversations using vector databases and graph memory."},
    {"id":"gh2","title":"browser-use/browser-use","url":"https://github.com/browser-use/browser-use","source":"github",
     "time": (datetime.now()-timedelta(hours=5)).isoformat(),
     "score":1923,"content":"browser-use makes it simple for AI agents to control a browser, enabling web automation via LLMs with minimal code."},
    {"id":"gh3","title":"microsoft/OmniParser","url":"https://github.com/microsoft/OmniParser","source":"github",
     "time": (datetime.now()-timedelta(hours=2)).isoformat(),
     "score":1654,"content":"OmniParser is a screen parsing tool that converts UI screenshots into structured elements for use with LLM agents."},
    {"id":"gh4","title":"ggerganov/llama.cpp","url":"https://github.com/ggerganov/llama.cpp","source":"github",
     "time": (datetime.now()-timedelta(hours=6)).isoformat(),
     "score":1432,"content":"llama.cpp enables running LLaMA-family models locally in pure C++ with quantization support for CPU and Apple Silicon."},
    {"id":"gh5","title":"hiyouga/LLaMA-Factory","url":"https://github.com/hiyouga/LLaMA-Factory","source":"github",
     "time": (datetime.now()-timedelta(hours=4)).isoformat(),
     "score":1287,"content":"LLaMA-Factory provides a unified training framework for fine-tuning 100+ LLMs including LoRA, QLoRA, and full fine-tuning."},
]

FINANCE_ITEMS = [
    {"id":"fin1","title":"美联储暗示年内降息窗口收窄 市场预期大幅调整","url":"https://wallstreetcn.com/articles/fin1","source":"wallstreetcn",
     "time": (datetime.now()-timedelta(hours=2)).isoformat(),
     "score":987,"content":"Federal Reserve officials signaled fewer rate cuts in 2025 amid persistent inflation. Markets repriced rate expectations sharply lower."},
    {"id":"fin2","title":"黄金价格突破3500美元创历史新高","url":"https://wallstreetcn.com/articles/fin2","source":"wallstreetcn",
     "time": (datetime.now()-timedelta(hours=1)).isoformat(),
     "score":1243,"content":"Gold surged past $3500/oz driven by dollar weakness, geopolitical tensions, and central bank buying demand."},
    {"id":"fin3","title":"比特币重返10万美元 机构持仓创纪录","url":"https://36kr.com/articles/fin3","source":"36kr",
     "time": (datetime.now()-timedelta(hours=3)).isoformat(),
     "score":1876,"content":"Bitcoin reclaimed the $100k level as institutional ETF inflows hit record highs and on-chain metrics showed accumulation patterns."},
    {"id":"fin4","title":"A股市场科技股集体上涨 AI板块领涨","url":"https://tencent.com/articles/fin4","source":"tencent",
     "time": (datetime.now()-timedelta(hours=4)).isoformat(),
     "score":765,"content":"China A-shares tech sector rallied led by AI-related stocks as policy support and domestic LLM adoption accelerated."},
    {"id":"fin5","title":"OpenAI估值突破3000亿美元 新一轮融资完成","url":"https://36kr.com/articles/fin5","source":"36kr",
     "time": (datetime.now()-timedelta(hours=5)).isoformat(),
     "score":2134,"content":"OpenAI closed a new funding round valuing it at over $300 billion, the highest private tech valuation in history."},
    {"id":"fin6","title":"全球股市震荡 经济衰退担忧再起","url":"https://wallstreetcn.com/articles/fin6","source":"wallstreetcn",
     "time": (datetime.now()-timedelta(hours=7)).isoformat(),
     "score":543,"content":"Global equities declined on renewed recession fears as manufacturing PMI data fell below expectations in the US and Europe."},
]

AI_ITEMS = [
    {"id":"ai1","title":"Claude 4 Sonnet benchmarks leak: beats GPT-4o on coding","url":"https://news.ycombinator.com/item?id=ai1","source":"hackernews",
     "time": (datetime.now()-timedelta(hours=1)).isoformat(),
     "score":1432,"content":"Leaked Claude 4 Sonnet benchmarks show 15% improvement on HumanEval and SWE-bench, surpassing GPT-4o in coding tasks."},
    {"id":"ai2","title":"Show HN: RAG pipeline with sub-100ms latency using Rust","url":"https://news.ycombinator.com/item?id=ai2","source":"hackernews",
     "time": (datetime.now()-timedelta(hours=2)).isoformat(),
     "score":876,"content":"A Rust-based RAG pipeline achieves sub-100ms end-to-end latency using SIMD-optimized vector search and streaming LLM inference."},
    {"id":"ai3","title":"Google DeepMind releases Gemini 2.5 Ultra with 1M context","url":"https://news.ycombinator.com/item?id=ai3","source":"hackernews",
     "time": (datetime.now()-timedelta(hours=3)).isoformat(),
     "score":2341,"content":"Gemini 2.5 Ultra introduces a 1M token context window with improved retrieval accuracy for long-document understanding tasks."},
    {"id":"ai4","title":"LLM Agents: the architecture that's eating software engineering","url":"https://news.ycombinator.com/item?id=ai4","source":"hackernews",
     "time": (datetime.now()-timedelta(hours=4)).isoformat(),
     "score":1987,"content":"Analysis of how LLM agent architectures with tool use and memory are replacing traditional software engineering workflows."},
]

def filter_by_keyword(items, keywords):
    if not keywords:
        return items
    kw_list = [k.strip().lower() for k in keywords.split(',')]
    result = []
    for item in items:
        text = (item.get('title','') + ' ' + item.get('content','')).lower()
        if any(kw in text for kw in kw_list):
            result.append(item)
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default='hackernews')
    parser.add_argument('--limit', type=int, default=10)
    parser.add_argument('--keyword', default='')
    parser.add_argument('--deep', action='store_true')
    args = parser.parse_args()

    source = args.source.lower()
    pool = []

    if source == 'github':
        pool = GITHUB_ITEMS
    elif source == 'wallstreetcn':
        pool = [i for i in FINANCE_ITEMS if i['source'] == 'wallstreetcn']
    elif source == '36kr':
        pool = [i for i in FINANCE_ITEMS if i['source'] == '36kr']
    elif source == 'hackernews':
        pool = AI_ITEMS
    elif source == 'all':
        pool = GITHUB_ITEMS + FINANCE_ITEMS + AI_ITEMS
    else:
        pool = AI_ITEMS + FINANCE_ITEMS

    if args.keyword:
        pool = filter_by_keyword(pool, args.keyword)

    pool = pool[:args.limit]

    if not args.deep:
        pool = [{k: v for k, v in item.items() if k != 'content'} for item in pool]

    print(json.dumps(pool, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
'''

(WORKSPACE / "scripts" / "fetch_news.py").write_text(mock_fetch)
(WORKSPACE / "scripts" / "fetch_news.py").chmod(0o755)

print(f"[gen_inputs] Workspace created at {WORKSPACE}")
print(f"[gen_inputs] Directories: {[str(d) for d in WORKSPACE.iterdir()]}")