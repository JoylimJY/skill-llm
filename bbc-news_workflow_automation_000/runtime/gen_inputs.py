import os
import json
import random

random.seed(42)

base = "/workspace"

# Create directory structure with distractor files
dirs = [
    "scripts",
    "references",
    "reports/archive",
    "reports/drafts",
    "data/raw",
    "data/processed",
    "config",
    "logs",
    "tools/parsers",
    "tools/exporters",
    "docs/internal",
]

for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Create the actual BBC news script
bbc_news_script = '''#!/usr/bin/env python3
"""BBC News RSS Feed CLI Tool"""
import argparse
import json
import sys
import feedparser

FEEDS = {
    "top": "http://feeds.bbci.co.uk/news/rss.xml",
    "uk": "http://feeds.bbci.co.uk/news/uk/rss.xml",
    "world": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "business": "http://feeds.bbci.co.uk/news/business/rss.xml",
    "politics": "http://feeds.bbci.co.uk/news/politics/rss.xml",
    "health": "http://feeds.bbci.co.uk/news/health/rss.xml",
    "education": "http://feeds.bbci.co.uk/news/education/rss.xml",
    "science": "http://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
    "technology": "http://feeds.bbci.co.uk/news/technology/rss.xml",
    "entertainment": "http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",
    "england": "http://feeds.bbci.co.uk/news/england/rss.xml",
    "scotland": "http://feeds.bbci.co.uk/news/scotland/rss.xml",
    "wales": "http://feeds.bbci.co.uk/news/wales/rss.xml",
    "northern-ireland": "http://feeds.bbci.co.uk/news/northern_ireland/rss.xml",
    "africa": "http://feeds.bbci.co.uk/news/world/africa/rss.xml",
    "asia": "http://feeds.bbci.co.uk/news/world/asia/rss.xml",
    "australia": "http://feeds.bbci.co.uk/news/world/asia_pacific/rss.xml",
    "europe": "http://feeds.bbci.co.uk/news/world/europe/rss.xml",
    "latin-america": "http://feeds.bbci.co.uk/news/world/latin_america/rss.xml",
    "middle-east": "http://feeds.bbci.co.uk/news/world/middle_east/rss.xml",
    "us-canada": "http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml",
}

def fetch_stories(section, limit=None):
    url = FEEDS.get(section)
    if not url:
        print(f"Unknown section: {section}", file=sys.stderr)
        sys.exit(1)
    feed = feedparser.parse(url)
    entries = feed.entries
    if limit:
        entries = entries[:limit]
    stories = []
    for entry in entries:
        story = {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": entry.get("summary", ""),
        }
        stories.append(story)
    return stories

def main():
    parser = argparse.ArgumentParser(description="Fetch BBC News stories")
    parser.add_argument("section", nargs="?", default="top", help="News section")
    parser.add_argument("--limit", type=int, help="Limit number of stories")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--list", action="store_true", help="List available sections")
    args = parser.parse_args()

    if args.list:
        print("Available sections:")
        for key in FEEDS:
            print(f"  {key}")
        return

    stories = fetch_stories(args.section, args.limit)

    if args.json:
        print(json.dumps(stories, indent=2))
    else:
        for i, story in enumerate(stories, 1):
            print(f"{i}. {story[\'title\']}")
            if story["published"]:
                print(f"   Published: {story[\'published\']}")
            if story["summary"]:
                print(f"   {story[\'summary\'][:150]}...")
            print()

if __name__ == "__main__":
    main()
'''

with open(os.path.join(base, "scripts", "bbc_news.py"), "w") as f:
    f.write(bbc_news_script)

# Create references/feeds.md
feeds_md = """# BBC News RSS Feeds

## Main Sections
- Top Stories: http://feeds.bbci.co.uk/news/rss.xml
- UK: http://feeds.bbci.co.uk/news/uk/rss.xml
- World: http://feeds.bbci.co.uk/news/world/rss.xml
- Business: http://feeds.bbci.co.uk/news/business/rss.xml
- Politics: http://feeds.bbci.co.uk/news/politics/rss.xml
- Health: http://feeds.bbci.co.uk/news/health/rss.xml
- Education: http://feeds.bbci.co.uk/news/education/rss.xml
- Science & Environment: http://feeds.bbci.co.uk/news/science_and_environment/rss.xml
- Technology: http://feeds.bbci.co.uk/news/technology/rss.xml
- Entertainment & Arts: http://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml

## UK Regional
- England: http://feeds.bbci.co.uk/news/england/rss.xml
- Scotland: http://feeds.bbci.co.uk/news/scotland/rss.xml
- Wales: http://feeds.bbci.co.uk/news/wales/rss.xml
- Northern Ireland: http://feeds.bbci.co.uk/news/northern_ireland/rss.xml

## World Regions
- Africa: http://feeds.bbci.co.uk/news/world/africa/rss.xml
- Asia: http://feeds.bbci.co.uk/news/world/asia/rss.xml
- Australia: http://feeds.bbci.co.uk/news/world/asia_pacific/rss.xml
- Europe: http://feeds.bbci.co.uk/news/world/europe/rss.xml
- Latin America: http://feeds.bbci.co.uk/news/world/latin_america/rss.xml
- Middle East: http://feeds.bbci.co.uk/news/world/middle_east/rss.xml
- US & Canada: http://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml
"""

with open(os.path.join(base, "references", "feeds.md"), "w") as f:
    f.write(feeds_md)

# Create SKILL.md
skill_md = """---
name: bbc-news
description: Fetch and display BBC News stories from various sections and regions via RSS feeds.
---

# BBC News

Fetch top stories from BBC News across different sections and regions.

## Quick Start

Fetch top stories:
```bash
python3 scripts/bbc_news.py
```

Fetch from specific section:
```bash
python3 scripts/bbc_news.py uk
python3 scripts/bbc_news.py world
python3 scripts/bbc_news.py technology
```

List all available sections:
```bash
python3 scripts/bbc_news.py --list
```

## Available Sections

### Main Sections
- `top` - Top stories (default)
- `uk` - UK news
- `world` - World news
- `business` - Business news
- `politics` - Politics
- `health` - Health news
- `education` - Education
- `science` - Science & Environment
- `technology` - Technology news
- `entertainment` - Entertainment & Arts

### UK Regional
- `england` - England news
- `scotland` - Scotland news
- `wales` - Wales news
- `northern-ireland` - Northern Ireland news

### World Regions
- `africa` - Africa news
- `asia` - Asia news
- `australia` - Australia news
- `europe` - Europe news
- `latin-america` - Latin America news
- `middle-east` - Middle East news
- `us-canada` - US & Canada news

## Options

**Limit number of stories:**
```bash
python3 scripts/bbc_news.py world --limit 5
```

**JSON output:**
```bash
python3 scripts/bbc_news.py technology --json
```

## Examples

Get top 5 UK stories:
```bash
python3 scripts/bbc_news.py uk --limit 5
```

Get Scotland news in JSON:
```bash
python3 scripts/bbc_news.py scotland --json
```

Get latest technology headlines:
```bash
python3 scripts/bbc_news.py technology --limit 3
```

## Dependencies

Requires `feedparser`:
```bash
pip3 install feedparser
```
"""

with open(os.path.join(base, "SKILL.md"), "w") as f:
    f.write(skill_md)

# Distractor files
distractor_configs = {
    "config/news_sources.yaml": "# Legacy news source configuration\nsources:\n  - reuters\n  - ap\n  - guardian\nformat: xml\nmax_items: 20\n",
    "config/regions.json": json.dumps({"regions": ["EMEA", "APAC", "Americas"], "legacy": True}, indent=2),
    "data/raw/sample_feed.xml": "<?xml version='1.0'?><rss><channel><title>Old Feed</title></channel></rss>",
    "data/processed/archive_2023.json": json.dumps([{"id": 1, "headline": "Old story", "region": "uk"}], indent=2),
    "logs/fetch_errors.log": "2023-01-01 ERROR: Connection timeout\n2023-01-02 ERROR: Feed not found\n",
    "tools/parsers/xml_parser.py": "# Legacy XML parser - deprecated\ndef parse(xml_str):\n    pass\n",
    "tools/exporters/csv_exporter.py": "# CSV export utility\nimport csv\ndef export(data, path):\n    pass\n",
    "docs/internal/news_workflow.md": "# Internal News Workflow\nFetch -> Parse -> Store -> Display\nSee legacy system docs for RSS format details.\n",
    "reports/archive/q1_2023_digest.json": json.dumps({"quarter": "Q1 2023", "sections": ["world", "uk"], "stories": []}, indent=2),
    "reports/drafts/template.json": json.dumps({"digest": {"generated_at": "", "sections": {}}, "version": "0.1"}, indent=2),
}

for path, content in distractor_configs.items():
    full_path = os.path.join(base, path)
    with open(full_path, "w") as f:
        f.write(content)

# Additional distractors
with open(os.path.join(base, "tools", "parsers", "rss_v1.py"), "w") as f:
    f.write("# Old RSS parser - do not use\n# Replaced by scripts/bbc_news.py\n")

with open(os.path.join(base, "data", "raw", "region_codes.csv"), "w") as f:
    f.write("code,name\nUK,United Kingdom\nUS,United States\nEU,Europe\nME,Middle East\nLA,Latin America\n")

print("Workspace generated successfully.")