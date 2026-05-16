import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "reports",
    "templates",
    "cache",
    "logs",
    "config",
    "data/raw",
    "data/processed",
    "archive/2024",
    "archive/2025",
    "tests",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = r"""---
name: news-aggregator-skill
description: "Comprehensive news aggregator that fetches, filters, and deeply analyzes real-time content from 8 major sources: Hacker News, GitHub Trending, Product Hunt, 36Kr, Tencent News, WallStreetCN, V2EX, and Weibo. Best for 'daily scans', 'tech news briefings', 'finance updates', and 'deep interpretations' of hot topics."
---

# News Aggregator Skill

Fetch real-time hot news from multiple sources.

## Tools

### fetch_news.py

**Usage:**

### Single Source (Limit 10)
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
- `--limit`: Â Max items per source (default 10).
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
(workspace / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ── templates.md ──────────────────────────────────────────────────────────────
templates_md = """# Available Commands

1. Daily Global Scan - `python3 scripts/fetch_news.py --source all --limit 15 --deep`
2. HackerNews AI Deep Dive - `python3 scripts/fetch_news.py --source hackernews --limit 20 --keyword "AI,LLM,GPT" --deep`
3. GitHub Trending - `python3 scripts/fetch_news.py --source github --limit 10`
4. Finance Update - `python3 scripts/fetch_news.py --source wallstreetcn --limit 10 --keyword "Finance,Stock,Market" --deep`
5. Weibo Hot - `python3 scripts/fetch_news.py --source weibo --limit 10`
"""
(workspace / "templates" / "templates.md").write_text(templates_md, encoding="utf-8")

# ── Mock fetch_news.py ────────────────────────────────────────────────────────
# This mock script captures exactly what arguments were passed and writes
# them to cache/last_invocation.json, then outputs deterministic fake news JSON.
mock_script = r'''#!/usr/bin/env python3
"""
Mock fetch_news.py — Records invocation args and outputs deterministic fake news JSON.
"""
import argparse
import json
import sys
import os
from datetime import datetime, timezone

parser = argparse.ArgumentParser()
parser.add_argument("--source", default="hackernews")
parser.add_argument("--limit", type=int, default=10)
parser.add_argument("--keyword", default=None)
parser.add_argument("--deep", action="store_true")
args = parser.parse_args()

# Record invocation
invocation = {
    "source": args.source,
    "limit": args.limit,
    "keyword": args.keyword,
    "deep": args.deep,
    "timestamp": datetime.now(timezone.utc).isoformat()
}

log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")
os.makedirs(log_dir, exist_ok=True)

# Append to invocation log
log_path = os.path.join(log_dir, "invocations.jsonl")
with open(log_path, "a") as f:
    f.write(json.dumps(invocation) + "\n")

# Also write last invocation for easy access
with open(os.path.join(log_dir, "last_invocation.json"), "w") as f:
    json.dump(invocation, f, indent=2)

# Generate deterministic fake news items
sources_map = {
    "hackernews": ["hackernews"],
    "github": ["github"],
    "producthunt": ["producthunt"],
    "36kr": ["36kr"],
    "tencent": ["tencent"],
    "wallstreetcn": ["wallstreetcn"],
    "v2ex": ["v2ex"],
    "weibo": ["weibo"],
    "all": ["hackernews", "github", "producthunt", "36kr", "tencent", "wallstreetcn", "v2ex", "weibo"],
}

source_list = sources_map.get(args.source, ["hackernews"])

ai_items = [
    {"title": "GPT-5 Technical Report Released", "url": "https://openai.com/gpt5", "source": "hackernews", "score": 4200, "time": "2h ago", "content": "OpenAI releases the full technical report for GPT-5, showing significant improvements in reasoning and coding benchmarks over GPT-4."},
    {"title": "LLM RAG Architecture Deep Dive", "url": "https://blog.langchain.dev/rag-architecture", "source": "hackernews", "score": 2800, "time": "3h ago", "content": "Comprehensive analysis of Retrieval-Augmented Generation architectures and their trade-offs in production deployments."},
    {"title": "Claude 3.5 Sonnet Outperforms GPT-4 on MMLU", "url": "https://anthropic.com/claude-3-5", "source": "36kr", "score": 3100, "time": "4h ago", "content": "Anthropic releases benchmark results showing Claude 3.5 Sonnet achieving new SOTA on multiple academic evaluations."},
    {"title": "Generative AI Code Review Tools Compared", "url": "https://devtools.io/ai-review", "source": "producthunt", "score": 1900, "time": "5h ago", "content": "Detailed comparison of AI-powered code review tools including GitHub Copilot, Cursor, and new entrants."},
    {"title": "Machine Learning Model Compression Techniques 2025", "url": "https://arxiv.org/ml-compression", "source": "v2ex", "score": 1500, "time": "6h ago", "content": "Survey of quantization, pruning, and distillation techniques for deploying large models on edge devices."},
    {"title": "Agent Framework Benchmark: LangGraph vs AutoGen", "url": "https://github.com/bench/agent", "source": "hackernews", "score": 2200, "time": "7h ago", "content": "Community benchmark comparing major agentic AI frameworks on complex multi-step reasoning tasks."},
]

github_items = [
    {"title": "ollama/ollama: Local LLM runner", "url": "https://github.com/ollama/ollama", "source": "github", "score": 8900, "time": "trending", "content": "Run Llama 3, Mistral, Gemma locally on macOS/Linux/Windows with a simple CLI."},
    {"title": "microsoft/autogen: Multi-agent framework", "url": "https://github.com/microsoft/autogen", "source": "github", "score": 7200, "time": "trending", "content": "Framework for building multi-agent AI applications with conversational patterns."},
    {"title": "run-llama/llama_index: Data framework for LLMs", "url": "https://github.com/run-llama/llama_index", "source": "github", "score": 6800, "time": "trending", "content": "A flexible data framework for connecting LLMs with external knowledge sources."},
]

other_items = [
    {"title": "NVIDIA H100 Supply Shortage Impacts AI Startups", "url": "https://wallstreetcn.com/nvidia", "source": "wallstreetcn", "score": 2100, "time": "8h ago", "content": "GPU supply constraints continue to limit compute access for AI companies, driving up cloud GPU costs by 40%."},
    {"title": "Tencent Releases Open-Source Multimodal Model", "url": "https://tencent.com/hunyuan", "source": "tencent", "score": 3300, "time": "2h ago", "content": "Tencent open-sources HunYuan, a 72B parameter multimodal model competitive with GPT-4V."},
    {"title": "Weibo Hot: AI写作工具使用率激增300%", "url": "https://weibo.com/hot/ai-writing", "source": "weibo", "score": 5500, "time": "1h ago", "content": "AI写作辅助工具在中国市场的使用量在过去半年内激增300%，引发内容行业广泛讨论。"},
]

all_items = ai_items + github_items + other_items

# Filter by source
if args.source == "all":
    output_items = all_items
elif args.source == "github":
    output_items = github_items
else:
    output_items = [item for item in all_items if item["source"] == args.source]
    if not output_items:
        output_items = ai_items[:3]

# Apply keyword filter if specified
if args.keyword:
    keywords = [k.strip().lower() for k in args.keyword.split(",")]
    filtered = []
    for item in output_items:
        item_text = (item["title"] + " " + item.get("content", "")).lower()
        if any(kw in item_text for kw in keywords):
            filtered.append(item)
    output_items = filtered if filtered else output_items[:2]

# Apply limit
output_items = output_items[:args.limit]

# If --deep not set, remove content field
if not args.deep:
    for item in output_items:
        item.pop("content", None)

print(json.dumps(output_items, ensure_ascii=False, indent=2))
'''
script_path = workspace / "scripts" / "fetch_news.py"
script_path.write_text(mock_script, encoding="utf-8")
script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "config/sources.yaml": "sources:\n  - hackernews\n  - github\n  - weibo\n",
    "config/settings.ini": "[general]\ndefault_limit=10\noutput_dir=reports\n",
    "data/raw/sample_hn.json": json.dumps([{"title": "Old HN item", "url": "https://hn.com/1", "score": 100}]),
    "data/raw/sample_github.json": json.dumps([{"title": "Old repo", "url": "https://github.com/x/y", "stars": 500}]),
    "data/processed/old_report_20240101.md": "# Old Report\n\nThis is an outdated report from 2024.\n",
    "logs/fetch.log": "2024-12-01 10:00:00 INFO Fetched 10 items from hackernews\n2024-12-01 10:01:00 INFO Done\n",
    "logs/errors.log": "2025-01-15 08:23:11 ERROR Connection timeout for source weibo\n",
    "archive/2024/report_20241201.md": "# December 2024 Report\n\nArchived content.\n",
    "archive/2025/report_20250101.md": "# January 2025 Report\n\nFirst report of the year.\n",
    "tests/test_fetch.py": "import subprocess\ndef test_basic():\n    result = subprocess.run(['python3', 'scripts/fetch_news.py', '--source', 'hackernews'], capture_output=True)\n    assert result.returncode == 0\n",
    "cache/.gitkeep": "",
}
for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")