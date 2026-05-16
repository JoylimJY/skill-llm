#!/usr/bin/env python3
"""
Generate the sandbox workspace for the news-aggregator evaluation task.
Creates a realistic project structure with distractor files and a MOCK fetch_news.py
that returns deterministic, controlled data for evaluation.
"""

import os
import json
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── Directory Structure ───────────────────────────────────────────────────────
dirs = [
    "scripts",
    "reports",
    "templates",
    "logs",
    "config",
    "archive/2024/Q4",
    "archive/2025/Q1",
    "data/raw",
    "data/processed",
    "docs",
    "tests",
    "src/parsers",
    "src/filters",
    "src/exporters",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor Files ─────────────────────────────────────────────────────────
distractor_files = {
    "config/sources.yaml": """\
sources:
  hackernews:
    base_url: https://hacker-news.firebaseio.com/v0
    rate_limit: 10
  github:
    base_url: https://github.com/trending
    rate_limit: 5
  weibo:
    base_url: https://weibo.com/hot
    rate_limit: 3
""",
    "config/filters.json": json.dumps({
        "blocked_domains": ["spam.com", "clickbait.net"],
        "min_score": 10,
        "max_age_hours": 48
    }, indent=2),
    "logs/fetch_2025_06_10.log": """\
[INFO] 2025-06-10 08:00:01 Starting fetch cycle
[INFO] 2025-06-10 08:00:03 hackernews: 15 items fetched
[INFO] 2025-06-10 08:00:07 github: 10 items fetched
[WARN] 2025-06-10 08:00:09 weibo: Rate limited, retrying...
[INFO] 2025-06-10 08:00:12 Cycle complete. 25 items total.
""",
    "logs/errors_2025_06_09.log": """\
[ERROR] 2025-06-09 22:15:33 ConnectionTimeout: 36kr failed after 3 retries
[ERROR] 2025-06-09 22:15:34 ParseError: Unexpected JSON structure in producthunt
""",
    "data/raw/hn_snapshot_20250609.json": json.dumps([
        {"id": 9001, "title": "Old HN Story", "url": "https://example.com/old", "score": 50, "time": 1749340000}
    ], indent=2),
    "data/processed/summary_20250609.txt": """\
Daily Summary - 2025-06-09
Total articles processed: 87
High-value items: 12
Filtered out: 75
""",
    "archive/2025/Q1/report_20250301_0800.md": """\
# Morning Briefing - 2025-03-01

## Top Stories
1. [Rust hits 2M developers](https://example.com) — *HackerNews* | Score: 342
""",
    "archive/2024/Q4/report_20241201_0900.md": """\
# Morning Briefing - 2024-12-01

## Top Stories
1. [OpenAI releases o1](https://openai.com) — *HackerNews* | Score: 891
""",
    "docs/architecture.md": """\
# News Aggregator Architecture

## Components
- **Fetcher**: `scripts/fetch_news.py`
- **Filter Engine**: `src/filters/`
- **Export Pipeline**: `src/exporters/`

## Data Flow
Raw Fetch → Filter → Rank → Export → Report
""",
    "tests/test_filters.py": """\
import pytest

def test_keyword_filter():
    from src.filters.keyword import filter_items
    items = [{'title': 'AI is cool'}, {'title': 'Rust lang'}]
    result = filter_items(items, keywords=['AI'])
    assert len(result) == 1
""",
    "src/parsers/hn_parser.py": """\
def parse_hn_item(raw):
    return {
        'id': raw.get('id'),
        'title': raw.get('title'),
        'url': raw.get('url', ''),
        'score': raw.get('score', 0),
        'time': raw.get('time'),
        'source': 'hackernews'
    }
""",
    "src/filters/keyword.py": """\
def filter_items(items, keywords):
    result = []
    for item in items:
        title = item.get('title', '').lower()
        if any(kw.lower() in title for kw in keywords):
            result.append(item)
    return result
""",
    "src/exporters/markdown.py": """\
def to_markdown(item):
    title = item.get('title', 'No Title')
    url = item.get('url', '#')
    return f'### [{title}]({url})'
""",
    "templates/daily_briefing.md": """\
# Daily Briefing Template

## Global Headlines
<!-- Top 3-5 cross-domain stories -->

## Tech & AI
<!-- AI, LLM, and tech items -->

## Finance / Social
<!-- Finance and social items if relevant -->
""",
}

for filepath, content in distractor_files.items():
    full_path = WORKSPACE / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# ─── SKILL.md ────────────────────────────────────────────────────────────────
skill_md = """\
---
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

# ─── Mock fetch_news.py ───────────────────────────────────────────────────────
# This is the critical mock: it returns deterministic data based on arguments.
# It simulates:
#   - hackernews: only 2 items in past 3h (triggers Smart Fill), rest older
#   - github: 5 items (GitHub Trending exception applies)
# The script records what arguments it was called with to a log file for eval.

now_ts = int(datetime.now(timezone.utc).timestamp())
# Items within 3 hours
hn_recent = [
    {
        "id": 40001,
        "title": "LLM agents can now autonomously browse the web",
        "url": "https://news.ycombinator.com/item?id=40001",
        "score": 287,
        "time": now_ts - 3600,   # 1 hour ago
        "source": "hackernews",
        "content": "Researchers have demonstrated that LLM-based agents using RAG and tool-calling can autonomously navigate complex web tasks with 78% success rate, surpassing previous SOTA by 12 points."
    },
    {
        "id": 40002,
        "title": "GPT-5 rumored to launch this quarter with multimodal reasoning",
        "url": "https://news.ycombinator.com/item?id=40002",
        "score": 412,
        "time": now_ts - 7000,   # ~2h ago
        "source": "hackernews",
        "content": "Multiple insider sources confirm OpenAI is preparing GPT-5 release. The model reportedly achieves near-human performance on ARC-AGI benchmark and includes native video understanding."
    },
]
# Older HN items (> 3h, high heat — for Smart Fill)
hn_older = [
    {
        "id": 40003,
        "title": "Google DeepMind releases Gemini 2.0 Ultra: SOTA on MMLU",
        "url": "https://news.ycombinator.com/item?id=40003",
        "score": 1203,
        "time": now_ts - 18*3600,  # 18h ago
        "source": "hackernews",
        "content": "DeepMind's Gemini 2.0 Ultra achieves 92.4% on MMLU, a new SOTA result. The model is now available via Google Cloud Vertex AI."
    },
    {
        "id": 40004,
        "title": "Anthropic's Claude 3.7 achieves 95% on HumanEval coding benchmark",
        "url": "https://news.ycombinator.com/item?id=40004",
        "score": 876,
        "time": now_ts - 20*3600,  # 20h ago
        "source": "hackernews",
        "content": "Claude 3.7 Sonnet sets new record on HumanEval. Anthropic claims significant improvements in multi-step reasoning and code generation tasks compared to Claude 3.5."
    },
    {
        "id": 40005,
        "title": "Machine Learning paper: RAG outperforms fine-tuning on knowledge-intensive tasks",
        "url": "https://news.ycombinator.com/item?id=40005",
        "score": 634,
        "time": now_ts - 22*3600,  # 22h ago
        "source": "hackernews",
        "content": "A comprehensive study comparing RAG vs fine-tuning across 12 datasets shows RAG achieves better performance on knowledge-intensive tasks while being more cost-effective."
    },
]
all_hn = hn_recent + hn_older

# GitHub Trending items (no time filter logic; list ALL)
github_items = [
    {
        "id": "g001",
        "title": "microsoft/phi-4-mini",
        "url": "https://github.com/microsoft/phi-4-mini",
        "score": 2341,
        "stars_today": 892,
        "time": now_ts - 12*3600,
        "source": "github",
        "content": "Phi-4-mini is a compact LLM from Microsoft achieving GPT-4-level performance on reasoning tasks with only 3.8B parameters. Uses a novel mixture-of-experts architecture.",
        "description": "Phi-4-mini: A compact yet powerful LLM for edge deployment"
    },
    {
        "id": "g002",
        "title": "ggerganov/llama.cpp",
        "url": "https://github.com/ggerganov/llama.cpp",
        "score": 1876,
        "stars_today": 743,
        "time": now_ts - 8*3600,
        "source": "github",
        "content": "llama.cpp enables running LLaMA models locally using pure C/C++ with no dependencies. Latest update adds support for Phi-4 and Gemma-3 architectures.",
        "description": "Run LLaMA models locally with pure C/C++"
    },
    {
        "id": "g003",
        "title": "langchain-ai/langgraph",
        "url": "https://github.com/langchain-ai/langgraph",
        "score": 1543,
        "stars_today": 612,
        "time": now_ts - 6*3600,
        "source": "github",
        "content": "LangGraph is a library for building stateful, multi-agent LLM applications as directed graphs. New v0.3 release adds support for human-in-the-loop workflows.",
        "description": "Build stateful multi-agent LLM apps as graphs"
    },
    {
        "id": "g004",
        "title": "qdrant/qdrant",
        "url": "https://github.com/qdrant/qdrant",
        "score": 987,
        "stars_today": 398,
        "time": now_ts - 10*3600,
        "source": "github",
        "content": "Qdrant is a vector database written in Rust, optimized for high-performance similarity search. New release adds hybrid sparse-dense search and on-disk payload indexing.",
        "description": "High-performance vector database for AI applications"
    },
    {
        "id": "g005",
        "title": "openai/swarm",
        "url": "https://github.com/openai/swarm",
        "score": 876,
        "stars_today": 356,
        "time": now_ts - 14*3600,
        "source": "github",
        "content": "OpenAI Swarm is an experimental multi-agent orchestration framework focusing on lightweight agent handoffs. It abstracts agent coordination into a simple Python interface.",
        "description": "Lightweight multi-agent orchestration by OpenAI"
    },
]

mock_script = '''#!/usr/bin/env python3
"""
Mock fetch_news.py for evaluation purposes.
Records call arguments and returns deterministic data based on source and keywords.
"""

import sys
import json
import argparse
import os
from datetime import datetime, timezone

# Log the exact command line call for eval inspection
log_path = "/workspace/logs/fetch_calls.log"
os.makedirs(os.path.dirname(log_path), exist_ok=True)
with open(log_path, "a") as f:
    f.write(json.dumps({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "argv": sys.argv[1:]
    }) + "\\n")

parser = argparse.ArgumentParser()
parser.add_argument("--source", default="all")
parser.add_argument("--limit", type=int, default=10)
parser.add_argument("--keyword", default=None)
parser.add_argument("--deep", action="store_true")
args = parser.parse_args()

NOW = int(datetime.now(timezone.utc).timestamp())

HN_ITEMS = ''' + json.dumps(all_hn) + '''

GITHUB_ITEMS = ''' + json.dumps(github_items) + '''

def keyword_match(item, keywords):
    if not keywords:
        return True
    text = (item.get("title","") + " " + item.get("description","") + " " + item.get("content","")).lower()
    return any(k.strip().lower() in text for k in keywords.split(","))

output = []

if args.source in ("hackernews", "all"):
    for item in HN_ITEMS:
        if keyword_match(item, args.keyword):
            out = dict(item)
            if not args.deep:
                out.pop("content", None)
            output.append(out)
        if len([x for x in output if x.get("source")=="hackernews"]) >= args.limit:
            break

if args.source in ("github", "all"):
    gh_count = 0
    for item in GITHUB_ITEMS:
        if keyword_match(item, args.keyword):
            out = dict(item)
            if not args.deep:
                out.pop("content", None)
            output.append(out)
            gh_count += 1
        if gh_count >= args.limit:
            break

print(json.dumps(output, ensure_ascii=False, indent=2))
'''

(WORKSPACE / "scripts/fetch_news.py").write_text(mock_script)
os.chmod(WORKSPACE / "scripts/fetch_news.py", 0o755)

# ─── templates.md ─────────────────────────────────────────────────────────────
templates_md = """\
# News Aggregator Command Menu

1. Global Scan (All Sources, Top 15, Deep)
   python3 scripts/fetch_news.py --source all --limit 15 --deep

2. Hacker News - AI Focus (Expanded Keywords)
   python3 scripts/fetch_news.py --source hackernews --limit 20 --keyword "AI,LLM,GPT,Claude,Generative,Machine Learning,RAG,Agent" --deep

3. GitHub Trending - Top 10
   python3 scripts/fetch_news.py --source github --limit 10 --deep

4. Finance Briefing (WallStreetCN + 36Kr)
   python3 scripts/fetch_news.py --source wallstreetcn --limit 10 --keyword "Finance,Stock,Market,Economy,Crypto,Gold" --deep

5. Specific Keyword Deep Dive
   python3 scripts/fetch_news.py --source all --limit 10 --keyword "<YOUR_KEYWORD>" --deep
"""
(WORKSPACE / "templates.md").write_text(templates_md)

# ─── Ensure reports/ is empty (agent must create files there) ─────────────────
(WORKSPACE / "reports/.gitkeep").write_text("")

print("✅ Workspace generation complete.")
print(f"   Workspace: {WORKSPACE}")
print(f"   Key files: SKILL.md, scripts/fetch_news.py, templates.md")
print(f"   Distractor files: {len(distractor_files)}")