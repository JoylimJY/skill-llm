FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple

# Create the scripts directory and the fetch_hn.py script that reads from cache or HN API
RUN mkdir -p /workspace/scripts

# Write the fetch_hn.py script that mirrors the SKILL.md specification
RUN cat > /workspace/scripts/fetch_hn.py << 'PYEOF'
#!/usr/bin/env python3
"""Hacker News Daily - Fetch top stories with filtering and caching."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

CACHE_DIR = Path.home() / ".cache" / "hn-daily"
CACHE_FILE = CACHE_DIR / "hn_cache.json"
CACHE_TTL = 4 * 3600  # 4 hours

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

DEFAULT_KEYWORDS = [
    "ai", "llm", "gpt", "claude", "openai", "programming", "python", "rust",
    "startup", "machine learning", "github", "typescript", "javascript",
    "kubernetes", "linux", "open source", "neural", "deep learning",
    "data", "cloud", "security", "crypto", "blockchain", "web", "api",
]


def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE) as f:
            data = json.load(f)
        if time.time() - data.get("timestamp", 0) < CACHE_TTL:
            return data.get("stories", [])
    return None


def save_cache(stories):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump({"timestamp": time.time(), "stories": stories}, f)


def fetch_stories(limit=30):
    ids = requests.get(HN_TOP_URL, timeout=10).json()[:100]
    stories = []
    for sid in ids:
        try:
            item = requests.get(HN_ITEM_URL.format(sid), timeout=10).json()
            if item and item.get("type") == "story":
                stories.append({
                    "id": item.get("id"),
                    "title": item.get("title", ""),
                    "url": item.get("url", f"https://news.ycombinator.com/item?id={item.get('id')}"),
                    "score": item.get("score", 0),
                    "by": item.get("by", ""),
                    "descendants": item.get("descendants", 0),
                    "time": item.get("time", 0),
                })
                if len(stories) >= limit:
                    break
        except Exception:
            continue
    return stories


def filter_stories(stories, keywords=None, min_score=0):
    if keywords is None:
        keywords = DEFAULT_KEYWORDS
    result = []
    for s in stories:
        title_lower = s.get("title", "").lower()
        if any(kw in title_lower for kw in keywords):
            if s.get("score", 0) >= min_score:
                result.append(s)
    return result


def format_text(stories):
    lines = ["📰 Hacker News 精选", ""]
    for i, s in enumerate(stories, 1):
        tag = ""
        title_lower = s.get("title", "").lower()
        if any(k in title_lower for k in ["ai", "llm", "gpt", "claude", "openai", "machine learning", "neural", "deep learning"]):
            tag = "[AI] "
        elif any(k in title_lower for k in ["python", "rust", "javascript", "typescript", "programming"]):
            tag = "[Programming] "
        elif any(k in title_lower for k in ["startup", "crypto", "blockchain"]):
            tag = "[Startup] "
        lines.append(f"{i}. {tag}{s['title']}")
        lines.append(f"   🔗 {s.get('url', '')}")
        lines.append(f"   👍 {s.get('score', 0)} 分 | 💬 {s.get('descendants', 0)} 评论")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Hacker News Daily")
    parser.add_argument("--limit", type=int, default=10, help="Number of stories to return")
    parser.add_argument("--min-score", type=int, default=0, help="Minimum score threshold")
    parser.add_argument("--no-cache", action="store_true", help="Force fresh fetch")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    stories = None
    if not args.no_cache:
        stories = load_cache()

    if stories is None:
        stories = fetch_stories(limit=100)
        save_cache(stories)

    filtered = filter_stories(stories, min_score=args.min_score)
    limited = filtered[:args.limit]

    if args.format == "json":
        print(json.dumps(limited, indent=2))
    else:
        print(format_text(limited))


if __name__ == "__main__":
    main()
PYEOF

RUN chmod +x /workspace/scripts/fetch_hn.py

WORKDIR /workspace