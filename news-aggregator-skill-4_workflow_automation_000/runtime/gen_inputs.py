#!/usr/bin/env python3
"""
Generate the sandbox workspace for the news-aggregator-skill evaluation task.
"""
import os
import json
import random
from pathlib import Path
from datetime import datetime, timezone

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "reports",
    "templates",
    "logs",
    "cache",
    "data/raw",
    "data/processed",
    "config",
    "tests",
    "docs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── 2. Distractor files ────────────────────────────────────────────────────────
distractor_files = {
    "config/settings.yaml": """\
app_name: news-aggregator
version: 2.1.4
log_level: INFO
cache_ttl: 3600
""",
    "config/sources.json": json.dumps({
        "enabled": ["hackernews", "github", "v2ex", "weibo"],
        "disabled": ["producthunt"],
        "rate_limits": {"hackernews": 60, "github": 30}
    }, indent=2),
    "logs/fetch_2024_0101.log": "2024-01-01 08:00:00 INFO Fetched 15 items from hackernews\n2024-01-01 08:01:00 INFO Fetched 10 items from github\n",
    "logs/errors.log": "2024-01-02 09:15:00 ERROR Connection timeout to weibo\n2024-01-02 09:16:00 WARN Retrying...\n",
    "data/raw/sample_hn.json": json.dumps([{"id": 1, "title": "Old HN item", "url": "https://example.com"}]),
    "data/processed/filtered_2024.json": json.dumps({"count": 42, "topics": ["AI", "crypto"]}),
    "cache/github_trending_cache.json": json.dumps({"timestamp": "2024-01-01T00:00:00Z", "items": []}),
    "tests/test_fetch.py": """\
import unittest
class TestFetch(unittest.TestCase):
    def test_placeholder(self):
        pass
""",
    "docs/architecture.md": """\
# Architecture

The news aggregator uses a plugin-based source system.
Each source implements a `fetch()` method returning a list of NewsItem objects.
""",
    "templates/legacy_template.txt": "OLD TEMPLATE - DO NOT USE\nDate: {{date}}\nTitle: {{title}}\n",
    "data/raw/old_report.md": "# Old Report 2024-01-01\nThis is a stale report from last month.\n",
}

for rel_path, content in distractor_files.items():
    fp = WORKSPACE / rel_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)

# ── 3. SKILL.md ────────────────────────────────────────────────────────────────
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
- `--limit`: Max items per source (default 10).
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

# ── 4. The MOCK fetch_news.py ──────────────────────────────────────────────────
# This is the key: a deterministic mock that returns realistic but fixed data.
# The mock returns:
#   - For --source hackernews or v2ex: items with timestamps, mostly > 3h old (sparse in-window)
#   - For --source github: 5 trending repos (no timestamps)
# This forces the agent to apply Smart Fill for HN/V2EX and GitHub Exception for github.

from datetime import datetime, timedelta, timezone

now_utc = datetime.now(timezone.utc)

# HN items: only 2 within 3h, 4 older (to trigger Smart Fill)
hn_items = [
    {
        "title": "LLM Agents Are Eating the World",
        "url": "https://news.ycombinator.com/item?id=40000001",
        "source": "hackernews",
        "score": 342,
        "time": (now_utc - timedelta(hours=1, minutes=20)).isoformat(),
        "content": "A deep dive into how LLM-powered agents are automating complex workflows previously requiring human judgment."
    },
    {
        "title": "RAG vs Fine-Tuning: A Practical Comparison",
        "url": "https://news.ycombinator.com/item?id=40000002",
        "source": "hackernews",
        "score": 278,
        "time": (now_utc - timedelta(hours=2, minutes=45)).isoformat(),
        "content": "Engineers at a mid-size startup benchmark RAG pipelines against fine-tuned models across 12 tasks."
    },
    # Older items (> 3h) — should appear as Smart Fill
    {
        "title": "GPT-4o Mini Outperforms Larger Models on Coding Benchmarks",
        "url": "https://news.ycombinator.com/item?id=40000003",
        "source": "hackernews",
        "score": 512,
        "time": (now_utc - timedelta(hours=8, minutes=10)).isoformat(),
        "content": "OpenAI's smaller model achieves SOTA results on HumanEval, raising questions about scaling laws."
    },
    {
        "title": "Claude 3.5 Sonnet Shows Strong Agentic Capabilities",
        "url": "https://news.ycombinator.com/item?id=40000004",
        "source": "hackernews",
        "score": 489,
        "time": (now_utc - timedelta(hours=12, minutes=5)).isoformat(),
        "content": "Anthropic's latest model demonstrates improved tool use and multi-step planning in agent evaluations."
    },
    {
        "title": "Generative AI Is Transforming Drug Discovery",
        "url": "https://news.ycombinator.com/item?id=40000005",
        "source": "hackernews",
        "score": 401,
        "time": (now_utc - timedelta(hours=18, minutes=30)).isoformat(),
        "content": "Major pharma companies report 30% reduction in early-stage discovery timelines using generative models."
    },
    {
        "title": "Machine Learning Engineers Are Now the Most Hired Roles in Tech",
        "url": "https://news.ycombinator.com/item?id=40000006",
        "source": "hackernews",
        "score": 375,
        "time": (now_utc - timedelta(hours=22, minutes=0)).isoformat(),
        "content": "LinkedIn data shows ML Engineer postings up 180% YoY, with Agent specialization emerging as a new sub-role."
    },
]

# V2EX items: only 1 within 3h
v2ex_items = [
    {
        "title": "分享：用 LangGraph 构建多 Agent 系统踩坑记录",
        "url": "https://www.v2ex.com/t/1001001",
        "source": "v2ex",
        "score": 95,
        "time": (now_utc - timedelta(hours=2, minutes=10)).isoformat(),
        "content": "实际项目中使用 LangGraph 构建多 Agent 协作系统时遇到的状态管理和并发问题。"
    },
    {
        "title": "国内有什么好用的开源 LLM 推理框架？",
        "url": "https://www.v2ex.com/t/1001002",
        "source": "v2ex",
        "score": 80,
        "time": (now_utc - timedelta(hours=9, minutes=0)).isoformat(),
        "content": "对比了 vLLM、SGLang、LMDeploy 等框架的性能和易用性。"
    },
    {
        "title": "RAG 应用中的 Reranker 选型指南",
        "url": "https://www.v2ex.com/t/1001003",
        "source": "v2ex",
        "score": 72,
        "time": (now_utc - timedelta(hours=15, minutes=20)).isoformat(),
        "content": "介绍了 Cohere Rerank、BGE Reranker 等在实际 RAG 系统中的对比测试结果。"
    },
]

# GitHub Trending items (no timestamps — always "current")
github_items = [
    {
        "title": "microsoft/graphrag",
        "url": "https://github.com/microsoft/graphrag",
        "source": "github",
        "score": 18420,
        "description": "A modular graph-based Retrieval-Augmented Generation (RAG) system",
        "language": "Python",
        "stars_today": 892,
        "content": "GraphRAG extends standard RAG with knowledge graph construction, enabling multi-hop reasoning across complex document sets."
    },
    {
        "title": "ollama/ollama",
        "url": "https://github.com/ollama/ollama",
        "source": "github",
        "score": 85100,
        "description": "Get up and running with Llama 3, Mistral, Gemma 2, and other large language models locally",
        "language": "Go",
        "stars_today": 654,
        "content": "Ollama provides a simple API for running LLMs locally, supporting quantized models and a growing library of community integrations."
    },
    {
        "title": "unslothai/unsloth",
        "url": "https://github.com/unslothai/unsloth",
        "source": "github",
        "score": 21300,
        "description": "Finetune Llama 3, Mistral & Gemma LLMs 2-5x faster with 80% less memory",
        "language": "Python",
        "stars_today": 541,
        "content": "Unsloth achieves dramatic speedups via custom Triton kernels and quantization-aware training without accuracy loss."
    },
    {
        "title": "pydantic/pydantic-ai",
        "url": "https://github.com/pydantic/pydantic-ai",
        "source": "github",
        "score": 9870,
        "description": "Agent Framework / shim to use Pydantic with LLMs",
        "language": "Python",
        "stars_today": 487,
        "content": "PydanticAI brings type-safe structured outputs and validation to LLM agent frameworks, reducing hallucination in tool calls."
    },
    {
        "title": "BerriAI/litellm",
        "url": "https://github.com/BerriAI/litellm",
        "source": "github",
        "score": 14200,
        "description": "Call 100+ LLMs using the OpenAI Input/Output Format",
        "language": "Python",
        "stars_today": 412,
        "content": "LiteLLM provides a unified interface across 100+ LLMs, enabling vendor-agnostic agent development with built-in cost tracking."
    },
]

# ── 5. Write the mock fetch_news.py ───────────────────────────────────────────
mock_script = '''#!/usr/bin/env python3
"""
MOCK fetch_news.py — Deterministic stub for evaluation sandbox.
Returns pre-seeded realistic news data.
"""
import argparse
import json
import sys

# ── Pre-seeded data ────────────────────────────────────────────────────────────
HN_ITEMS = ''' + json.dumps(hn_items, indent=2) + '''

V2EX_ITEMS = ''' + json.dumps(v2ex_items, indent=2) + '''

GITHUB_ITEMS = ''' + json.dumps(github_items, indent=2) + '''

ALL_ITEMS = HN_ITEMS + V2EX_ITEMS + GITHUB_ITEMS

SOURCE_MAP = {
    "hackernews": HN_ITEMS,
    "v2ex": V2EX_ITEMS,
    "github": GITHUB_ITEMS,
    "all": ALL_ITEMS,
    "weibo": [],
    "36kr": [],
    "producthunt": [],
    "tencent": [],
    "wallstreetcn": [],
}

def matches_keyword(item, keywords):
    if not keywords:
        return True
    text = (item.get("title","") + " " + item.get("description","") + " " + item.get("content","")).lower()
    return any(kw.strip().lower() in text for kw in keywords.split(","))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="all")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--keyword", default="")
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()

    items = SOURCE_MAP.get(args.source, ALL_ITEMS)
    
    if args.keyword:
        items = [i for i in items if matches_keyword(i, args.keyword)]
    
    items = items[:args.limit]
    
    if not args.deep:
        items = [{k: v for k, v in i.items() if k != "content"} for i in items]
    
    print(json.dumps(items, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
'''

(WORKSPACE / "scripts" / "fetch_news.py").write_text(mock_script)
(WORKSPACE / "scripts" / "fetch_news.py").chmod(0o755)

# ── 6. templates.md (referenced by SKILL.md interactive menu) ─────────────────
templates_md = """\
# News Aggregator — Available Commands

1. 全局扫描 (Global Scan): python3 scripts/fetch_news.py --source all --limit 15 --deep
2. HN AI 精选: python3 scripts/fetch_news.py --source hackernews --limit 20 --keyword "AI,LLM,GPT" --deep
3. GitHub Trending: python3 scripts/fetch_news.py --source github --limit 10 --deep
4. V2EX 热帖: python3 scripts/fetch_news.py --source v2ex --limit 10 --deep
5. 财经速递: python3 scripts/fetch_news.py --source wallstreetcn --limit 10 --keyword "Finance,Stock" --deep
"""
(WORKSPACE / "templates" / "templates.md").write_text(templates_md)

# ── 7. Verify setup ────────────────────────────────────────────────────────────
print("Workspace setup complete.")
print(f"HN items: {len(hn_items)} (2 within 3h, 4 older)")
print(f"V2EX items: {len(v2ex_items)} (1 within 3h, 2 older)")
print(f"GitHub items: {len(github_items)} (all trending, no timestamps)")
print("Mock fetch_news.py written to scripts/fetch_news.py")