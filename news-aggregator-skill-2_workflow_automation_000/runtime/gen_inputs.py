import os
import json
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "reports",
    "templates",
    "logs",
    "config",
    "data/raw",
    "data/processed",
    "archive/2024",
    "archive/2023",
    "tools",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "config/settings.yaml": "# App settings\nenv: production\ndebug: false\nmax_retries: 3\n",
    "config/sources.json": json.dumps({"sources": ["hackernews", "github", "weibo", "36kr"], "default_limit": 10}),
    "logs/fetch_2024_0101.log": "2024-01-01 00:00:01 INFO Starting fetch...\n2024-01-01 00:00:05 INFO Done.\n",
    "logs/fetch_2024_0102.log": "2024-01-02 00:00:01 INFO Starting fetch...\n2024-01-02 00:00:06 ERROR Timeout on weibo\n",
    "data/raw/sample_hn.json": json.dumps([{"id": 999, "title": "Old HN item", "url": "https://example.com/old", "score": 5}]),
    "data/processed/cleaned_20240101.json": json.dumps({"items": [], "processed_at": "2024-01-01T00:00:00Z"}),
    "archive/2024/report_20240315_0900.md": "# Old Report\nThis is an archived report from March 2024.\n",
    "archive/2023/report_20231201_0800.md": "# Old Report Dec 2023\nContent here.\n",
    "templates/report_template.md": "# {title}\n\n## Section\n{content}\n",
    "tools/parser.py": "# Utility parser\ndef parse_json(s):\n    import json\n    return json.loads(s)\n",
    "data/raw/sample_github.json": json.dumps([{"repo": "trending/repo", "stars": 100}]),
}

for path, content in distractor_files.items():
    (workspace / path).write_text(content)

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
(workspace / "SKILL.md").write_text(skill_md)

# ── Mock fetch_news.py ────────────────────────────────────────────────────────
# This script returns deterministic data simulating a global --source all --limit 15 --deep call.
# Times are relative to a fixed anchor: 2025-07-10 12:00:00 UTC
# The script itself ignores most flags but checks for --source all and --deep.

now_anchor = datetime(2025, 7, 10, 12, 0, 0, tzinfo=timezone.utc)

def ts(hours_ago):
    """Return ISO timestamp string for N hours ago from anchor."""
    t = now_anchor - timedelta(hours=hours_ago)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")

mock_data = [
    # ── GitHub Trending items (source: github) — all are "old" by design ──
    {
        "id": "gh-001",
        "source": "github",
        "title": "microsoft/phi-4-mini: A compact yet powerful LLM for edge devices",
        "url": "https://github.com/microsoft/phi-4-mini",
        "score": 3200,
        "published_at": ts(10),
        "content": "Phi-4-mini is Microsoft's latest small language model optimized for on-device inference with 4B parameters achieving GPT-3.5 level performance.",
    },
    {
        "id": "gh-002",
        "source": "github",
        "title": "google/gemma-3n: Multimodal open model from Google DeepMind",
        "url": "https://github.com/google/gemma-3n",
        "score": 2800,
        "published_at": ts(12),
        "content": "Gemma 3n brings multimodal capabilities to the open-weights Gemma family, supporting text, image, and audio inputs.",
    },
    {
        "id": "gh-003",
        "source": "github",
        "title": "ggerganov/llama.cpp: LLM inference in C/C++ — now with Vulkan backend",
        "url": "https://github.com/ggerganov/llama.cpp",
        "score": 5100,
        "published_at": ts(8),
        "content": "llama.cpp adds a Vulkan GPU backend enabling cross-platform GPU acceleration without CUDA dependency.",
    },
    {
        "id": "gh-004",
        "source": "github",
        "title": "stanford-oval/storm: AI system for writing Wikipedia-like articles",
        "url": "https://github.com/stanford-oval/storm",
        "score": 1950,
        "published_at": ts(15),
        "content": "STORM is a multi-agent research pipeline that generates structured, citation-backed long-form articles from scratch.",
    },
    {
        "id": "gh-005",
        "source": "github",
        "title": "rustls/rustls: A modern TLS library written in Rust",
        "url": "https://github.com/rustls/rustls",
        "score": 1200,
        "published_at": ts(20),
        "content": "Rustls provides a memory-safe TLS implementation without OpenSSL dependency, now hitting 1.0 stable.",
    },

    # ── Hacker News items: 2 within 3h window, rest older ──
    {
        "id": "hn-001",
        "source": "hackernews",
        "title": "OpenAI announces o3-mini with 50% cost reduction",
        "url": "https://openai.com/blog/o3-mini-launch",
        "score": 890,
        "published_at": ts(1.5),
        "content": "OpenAI's o3-mini model cuts inference costs by half while maintaining o3-level reasoning on math and coding benchmarks.",
    },
    {
        "id": "hn-002",
        "source": "hackernews",
        "title": "Anthropic releases Claude 3.7 Sonnet with extended thinking",
        "url": "https://anthropic.com/news/claude-3-7-sonnet",
        "score": 760,
        "published_at": ts(2.8),
        "content": "Claude 3.7 Sonnet introduces a visible chain-of-thought reasoning mode that users can inspect and verify.",
    },
    {
        "id": "hn-003",
        "source": "hackernews",
        "title": "SQLite turns 25: A retrospective on the most deployed database",
        "url": "https://sqlite.org/25years.html",
        "score": 1340,
        "published_at": ts(7),
        "content": "SQLite celebrates 25 years of operation with over 1 trillion deployed instances, a technical retrospective from its creator.",
    },
    {
        "id": "hn-004",
        "source": "hackernews",
        "title": "Show HN: I built a Rust-based terminal markdown renderer",
        "url": "https://github.com/user/termdown-rs",
        "score": 430,
        "published_at": ts(9),
        "content": "A fast, zero-dependency terminal markdown renderer written in Rust supporting tables and syntax highlighting.",
    },

    # ── WallStreetCN items: 1 within 3h window ──
    {
        "id": "ws-001",
        "source": "wallstreetcn",
        "title": "美联储暗示2025年仅降息一次，美元指数急涨",
        "url": "https://wallstreetcn.com/articles/fed-2025-rate-cut",
        "score": 520,
        "published_at": ts(2.1),
        "content": "Federal Reserve minutes signal cautious stance; markets reprice rate-cut expectations from three cuts to one in 2025.",
    },
    {
        "id": "ws-002",
        "source": "wallstreetcn",
        "title": "黄金突破3200美元创历史新高",
        "url": "https://wallstreetcn.com/articles/gold-record-3200",
        "score": 980,
        "published_at": ts(6),
        "content": "Gold surpasses $3200/oz driven by dollar weakness and geopolitical uncertainty; analysts see potential for $3500.",
    },
    {
        "id": "ws-003",
        "source": "wallstreetcn",
        "title": "英伟达市值重返3万亿美元，AI芯片需求持续爆发",
        "url": "https://wallstreetcn.com/articles/nvidia-3t",
        "score": 1200,
        "published_at": ts(18),
        "content": "NVIDIA reclaims $3T market cap as hyperscaler capex for AI infrastructure accelerates into 2026.",
    },

    # ── 36Kr items: 0 within 3h window, older items ──
    {
        "id": "36k-001",
        "source": "36kr",
        "title": "字节跳动豆包大模型日调用量突破3亿，超GPT-4",
        "url": "https://36kr.com/p/douyin-doubao-3b",
        "score": 670,
        "published_at": ts(5),
        "content": "ByteDance's Doubao LLM processes 300M daily API calls, surpassing GPT-4 usage in Chinese enterprise market.",
    },
    {
        "id": "36k-002",
        "source": "36kr",
        "title": "Kimi k2 发布：月之暗面最强推理模型挑战 o3",
        "url": "https://36kr.com/p/moonshot-kimi-k2",
        "score": 810,
        "published_at": ts(11),
        "content": "Moonshot AI's Kimi k2 claims SOTA on AIME 2025 benchmark, positioning itself as direct o3 competitor.",
    },

    # ── Weibo items: older ──
    {
        "id": "wb-001",
        "source": "weibo",
        "title": "马斯克宣布xAI完成60亿美元新一轮融资",
        "url": "https://weibo.com/xai-funding-6b",
        "score": 340,
        "published_at": ts(14),
        "content": "Elon Musk's xAI raises $6B Series C, valuing the Grok AI startup at $50B ahead of rumored IPO.",
    },
    {
        "id": "wb-002",
        "source": "weibo",
        "title": "苹果WWDC 2025：Apple Intelligence全面登陆中国",
        "url": "https://weibo.com/apple-wwdc-china-ai",
        "score": 890,
        "published_at": ts(16),
        "content": "Apple Intelligence features officially launch in mainland China at WWDC 2025 with Baidu partnership for local LLM.",
    },
]

fetch_script = r'''#!/usr/bin/env python3
"""
Mock fetch_news.py - Returns deterministic data for sandbox evaluation.
Simulates: python3 scripts/fetch_news.py --source all --limit 15 --deep
"""
import argparse
import json
import sys
import os

# Load mock data from adjacent JSON file
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(SCRIPT_DIR, "_mock_news_data.json")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="hackernews")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--keyword", default=None)
    parser.add_argument("--deep", action="store_true")
    args = parser.parse_args()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        all_items = json.load(f)

    # Filter by source if not "all"
    if args.source != "all":
        filtered = [x for x in all_items if x.get("source") == args.source]
    else:
        filtered = all_items

    # Apply keyword filter if provided
    if args.keyword:
        keywords = [k.strip().lower() for k in args.keyword.split(",")]
        def matches(item):
            text = (item.get("title","") + " " + item.get("content","")).lower()
            return any(kw in text for kw in keywords)
        filtered = [x for x in filtered if matches(x)]

    # Apply limit per source
    if args.source == "all":
        from collections import defaultdict
        by_source = defaultdict(list)
        for item in filtered:
            by_source[item["source"]].append(item)
        result = []
        for src_items in by_source.values():
            result.extend(src_items[:args.limit])
    else:
        result = filtered[:args.limit]

    # Remove content field if --deep not specified
    if not args.deep:
        for item in result:
            item.pop("content", None)

    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
'''

(workspace / "scripts" / "fetch_news.py").write_text(fetch_script)
(workspace / "scripts" / "_mock_news_data.json").write_text(
    json.dumps(mock_data, ensure_ascii=False, indent=2)
)

# ── templates.md ─────────────────────────────────────────────────────────────
templates_md = """# News Aggregator Commands Menu

1. Global Scan (All Sources, Deep) — `python3 scripts/fetch_news.py --source all --limit 15 --deep`
2. Hacker News AI Deep Scan — `python3 scripts/fetch_news.py --source hackernews --limit 20 --keyword "AI,LLM,GPT,DeepSeek,Agent" --deep`
3. Finance Update — `python3 scripts/fetch_news.py --source wallstreetcn --limit 10 --keyword "Finance,Stock,Market,Economy,Crypto,Gold" --deep`
4. GitHub Trending — `python3 scripts/fetch_news.py --source github --limit 15 --deep`
5. Full Report (All Sources) — Run Global Scan then compile full report.
"""
(workspace / "templates" / "templates.md").write_text(templates_md)

# ── Anchor timestamp file (for eval to compute relative times) ───────────────
anchor_info = {
    "anchor_utc": "2025-07-10T12:00:00Z",
    "note": "All mock news items' published_at timestamps are relative to this anchor."
}
(workspace / "data" / "raw" / "anchor.json").write_text(json.dumps(anchor_info, indent=2))

print("Workspace initialized successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")