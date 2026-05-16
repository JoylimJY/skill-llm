import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create realistic deeply nested distractor directory structure ---
skill_base = workspace / "skills" / "daily-news-vnexpress"
skill_base.mkdir(parents=True, exist_ok=True)

venv_dir = workspace / "venv" / "openclaw_venv" / "lib"
venv_dir.mkdir(parents=True, exist_ok=True)

logs_dir = workspace / "logs" / "2024-01"
logs_dir.mkdir(parents=True, exist_ok=True)

config_dir = workspace / "config" / "agents"
config_dir.mkdir(parents=True, exist_ok=True)

reports_dir = workspace / "reports" / "archive"
reports_dir.mkdir(parents=True, exist_ok=True)

cache_dir = workspace / "cache" / "rss" / "raw"
cache_dir.mkdir(parents=True, exist_ok=True)

utils_dir = workspace / "utils" / "parsers"
utils_dir.mkdir(parents=True, exist_ok=True)

data_dir = workspace / "data" / "snapshots" / "2024"
data_dir.mkdir(parents=True, exist_ok=True)

# --- Write distractor files ---

# Distractor 1: Stale requirements file in root
(workspace / "requirements.txt").write_text(
    "# legacy root requirements - DO NOT USE\nrequests==2.28.0\nbeautifulsoup4==4.11.0\n"
)

# Distractor 2: Old config with wrong topic names
(config_dir / "news_config.json").write_text(json.dumps({
    "topics": ["business", "technology", "sports", "world"],
    "count": 5,
    "source": "vnexpress",
    "note": "DEPRECATED - do not use these topic names directly"
}, indent=2))

# Distractor 3: Fake cached RSS output (wrong format)
(cache_dir / "cached_feed.xml").write_text(
    """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Stale Cache</title>
    <item><title>Old News Item 1</title><link>http://example.com/1</link></item>
    <item><title>Old News Item 2</title><link>http://example.com/2</link></item>
  </channel>
</rss>
"""
)

# Distractor 4: Old log files
for i in range(3):
    (logs_dir / f"agent_run_{i+1}.log").write_text(
        f"[2024-01-{i+10}] Run {i+1} completed.\nTopics fetched: tin-moi-nhat\nStatus: OK\n"
    )

# Distractor 5: Fake past report (to confuse agent into thinking task is done)
(reports_dir / "morning_brief_OLD.txt").write_text(
    "Morning Brief - ARCHIVED\nTopics: business, tech\nNote: This is an old report, do not use.\n"
)

# Distractor 6: Fake utils script
(utils_dir / "rss_parser.py").write_text(
    "# DEPRECATED parser\ndef parse(url):\n    raise NotImplementedError('Use main.py instead')\n"
)

# Distractor 7: Snapshot data
(data_dir / "snapshot_q1.json").write_text(json.dumps({
    "period": "Q1-2024",
    "articles_fetched": 120,
    "topics_used": ["tin-moi-nhat"],
    "note": "Historical snapshot only"
}, indent=2))

# Distractor 8: venv placeholder
(venv_dir / "site_packages.txt").write_text("feedparser\nrequests\nlxml\n")

# --- Write the actual skill files ---
# requirements.txt for the skill
(skill_base / "requirements.txt").write_text(
    "feedparser>=6.0.8\nrequests>=2.28.0\nlxml>=4.9.0\npython-dateutil>=2.8.2\n"
)

# Write main.py — the actual skill script
main_py_content = '''#!/usr/bin/env python3
"""
VNExpress RSS News Fetcher
Fetches hot news from VNExpress RSS feeds based on specified topics.
"""
import argparse
import feedparser
import sys
from datetime import datetime

VALID_TOPICS = [
    "tin-moi-nhat", "the-gioi", "thoi-su", "kinh-doanh", "giai-tri",
    "the-thao", "phap-luat", "giao-duc", "tin-noi-bat", "suc-khoe",
    "doi-song", "du-lich", "khoa-hoc-cong-nghe", "oto-xe-may",
    "y-kien", "tam-su", "cuoi", "tin-xem-nhieu"
]

RSS_BASE = "https://vnexpress.net/rss/{topic}.rss"


def fetch_news(topic: str, count: int) -> list:
    if topic not in VALID_TOPICS:
        print(f"[WARNING] Invalid topic: '{topic}'. Skipping.", file=sys.stderr)
        return []
    url = RSS_BASE.format(topic=topic)
    feed = feedparser.parse(url)
    results = []
    for entry in feed.entries[:count]:
        results.append({
            "title": entry.get("title", "No title"),
            "link": entry.get("link", ""),
            "summary": entry.get("summary", "No summary available"),
            "published": entry.get("published", "Unknown date"),
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch VNExpress RSS news.")
    parser.add_argument("--topics", required=True, help="Comma-separated list of topics")
    parser.add_argument("--count_str", required=True, help="Comma-separated counts per topic")
    args = parser.parse_args()

    topics = [t.strip() for t in args.topics.split(",")]
    counts_raw = [c.strip() for c in args.count_str.split(",")]

    if len(counts_raw) == 1:
        counts = [int(counts_raw[0])] * len(topics)
    else:
        counts = [int(c) for c in counts_raw]

    if len(topics) != len(counts):
        print("[ERROR] Number of topics and counts must match.", file=sys.stderr)
        sys.exit(1)

    all_results = {}
    for topic, count in zip(topics, counts):
        print(f"\\n=== Fetching {count} news from topic: {topic} ===")
        news_items = fetch_news(topic, count)
        all_results[topic] = news_items
        for i, item in enumerate(news_items, 1):
            print(f"  [{i}] {item['title']}")
            print(f"      Link: {item['link']}")
            print(f"      Published: {item['published']}")
            print(f"      Summary: {item['summary'][:150]}...")
            print()

    return all_results


if __name__ == "__main__":
    main()
'''

(skill_base / "main.py").write_text(main_py_content)
(skill_base / "main.py").chmod(0o755)

# Write SKILL.md into skill directory
skill_md_content = """---
name: daily_news_vnexpress
description: Fetch the latest trending global news from https://vnexpress.net/rss/{topic}.rss.
---

# Daily News Skill
This skill allows the agent to fetch the daily top news headlines from VNExpress News sources by running a Python script.
The agent must treat the script output as **verified headline data** and avoid modifying the factual content.

# Allowance
You are allow to use all scripts mentioned in this file

## Quick Start
### Setup Environment
```bash
python3 -m venv /workspace/venv/openclaw_venv
source /workspace/venv/openclaw_venv/bin/activate
cd /workspace/skills/daily-news-vnexpress
pip install -r requirements.txt
```

## Instructions
### Python `main.py` Script Description
#### Functionality:
1. Fetches hot news from VNExpress RSS feeds based on specified topics
2. Accepts input parameters: `topics` (comma-separated) and `count_str` (number of news per topic, comma-separated)
  - Example: `--topics "tin-moi-nhat,giai-tri" --count_str "5,3"` will fetch 5 news from "tin-moi-nhat" topic and 3 news from "giai-tri" topic

#### Details:
1. Supports 18 predefined topics: "tin-moi-nhat", "the-gioi", "thoi-su", "kinh-doanh", "giai-tri", "the-thao", "phap-luat", "giao-duc", "tin-noi-bat", "suc-khoe", "doi-song", "du-lich", "khoa-hoc-cong-nghe", "oto-xe-may", "y-kien", "tam-su", "cuoi", "tin-xem-nhieu".
2. Each news item contains: title, link, summary, and published date

### Executing Instructions
When the user asks for **latest news or trending global events**:
1. Ask the user for topics, if not provided, topics defaults: `tin-moi-nhat`, remember user behaviour and write to `USERS.md`
2. Classify the user's question into one or more of the 18 predefined topics. Only select topics from this predefined list.
3. Determine (`count_str`) that match user question.

4. Execute the Python script to run:
```bash
python3 "{baseDir}/main.py" --topics "<topic>" --count_str "<count>"
```
- Example: "Find me 7 latest news"
```bash
python3 "{baseDir}/main.py" --topics "tin-moi-nhat" --count_str "7"
```

5. The script will collect and format the latest news headlines.
6. Paraphrase and summarize those relevant news items clearly.
7. Present them as the final response.
"""
(skill_base / "SKILL.md").write_text(skill_md_content)

# Distractor 9: wrong USERS.md stub in wrong location (to mislead)
(workspace / "logs" / "USERS.md").write_text(
    "# OLD USER LOG - DEPRECATED\nDo not edit this file.\n"
)

# Distractor 10: config for a completely different skill
(config_dir / "weather_skill.json").write_text(json.dumps({
    "skill": "weather",
    "api": "openweathermap",
    "units": "metric"
}, indent=2))

print("Workspace initialized successfully.")
print(f"Skill base: {skill_base}")
print(f"Distractor files created across: logs/, config/, reports/, cache/, utils/, data/")