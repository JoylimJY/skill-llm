#!/usr/bin/env python3
"""
Generate the sandbox workspace: creates the skill script, mock server data,
distractor files, and the overall directory structure.
"""
import os
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "skills/jable/scripts",
    "skills/jable/tests",
    "skills/jable/config",
    "skills/rss_reader/scripts",
    "skills/video_downloader/scripts",
    "data/raw/feeds",
    "data/processed",
    "logs",
    "reports/archive",
    "mock_server",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
(WORKSPACE / "skills/rss_reader/scripts/fetch_rss.py").write_text(
    "# Generic RSS fetcher - not related to jable skill\nimport feedparser\n"
)
(WORKSPACE / "skills/video_downloader/scripts/download.py").write_text(
    "# Video downloader stub\ndef download(url): pass\n"
)
(WORKSPACE / "skills/jable/config/settings.yaml").write_text(
    "default_hours: 48\ndefault_top: 3\ndefault_pages: 10\n"
)
(WORKSPACE / "skills/jable/tests/test_parser.py").write_text(
    "# Unit tests placeholder\nimport unittest\n\nclass TestParser(unittest.TestCase):\n    pass\n"
)
(WORKSPACE / "data/raw/feeds/sample_rss.xml").write_text(
    "<?xml version='1.0'?><rss version='2.0'><channel><title>Sample</title></channel></rss>\n"
)
(WORKSPACE / "data/processed/output_template.json").write_text(
    '{"results": [], "generated_at": "", "filter": {}}\n'
)
(WORKSPACE / "logs/app.log").write_text(
    "[2024-01-01 00:00:00] INFO: Service started\n[2024-01-01 00:01:00] INFO: Fetching feeds\n"
)
(WORKSPACE / "reports/archive/weekly_summary.txt").write_text(
    "Week 1: 12 videos processed\nWeek 2: 8 videos processed\n"
)
(WORKSPACE / "skills/jable/config/ignore_list.txt").write_text(
    "# Domains to skip\nexample.com\ntest.tv\n"
)
(WORKSPACE / "data/raw/feeds/old_backup.rss").write_text(
    "# Old format backup - deprecated\n"
)
(WORKSPACE / "skills/jable/tests/fixtures/mock_response.html").write_text(
    "<html><body><!-- old fixture, outdated --></body></html>\n"
)
Path(WORKSPACE / "skills/jable/tests/fixtures").mkdir(parents=True, exist_ok=True)
(WORKSPACE / "skills/jable/tests/fixtures/mock_response.html").write_text(
    "<html><body><!-- old fixture, outdated --></body></html>\n"
)

# ── Build mock server data ───────────────────────────────────────────────────
# We'll generate 15 video entries with realistic data.
# The mock server will serve these.

now = datetime.now(timezone.utc)

# Format for RSS pubDate: "Mon, 01 Jan 2024 12:00:00 +0000"
def rfc2822(dt):
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

# Video entries: (id, title, hours_ago, likes, in_latest_pages)
# hours_ago < 24 => within window; >= 24 => outside window
# in_latest_pages: whether this video appears in /latest-updates/ scrape
videos = [
    # id,  title,                              hours_ago, likes, in_pages
    ("aaa-001", "Studio Romance Collection Vol.3",  2,   4521,  True),
    ("bbb-002", "Midnight Encounter Series Ep.7",   5,   7830,  True),
    ("ccc-003", "Afternoon Delight Anthology",       8,   1200,  True),
    ("ddd-004", "Classic Beauty Showcase 2024",     12,   9100,  True),
    ("eee-005", "Urban Lifestyle Features Part 2",  15,   3344,  True),
    ("fff-006", "Seaside Summer Special Edition",   18,   5500,  True),
    ("ggg-007", "Winter Warmth Collection Ep.1",    20,   8200,  True),
    ("hhh-008", "Spring Festival Highlights",       22,   6750,  True),
    # This one is within 24h but NOT in latest pages -> should be skipped
    ("iii-009", "Hidden Gem Exclusive Preview",     10,      0,  False),
    # Outside 24h window -> should be excluded
    ("jjj-010", "Golden Era Classics Vol.12",       25,  15000,  True),
    ("kkk-011", "Vintage Collection Remastered",    30,  12000,  True),
    ("lll-012", "Archive Special Feature 99",       48,   9999,  True),
    ("mmm-013", "Retro Showcase Episode 44",        72,   8888,  True),
    # Within 24h, in pages, low likes
    ("nnn-014", "New Release Preview Vol.1",         1,    500,  True),
    ("ooo-015", "Daily Update Morning Edition",      3,   2100,  True),
]

# ── RSS XML ───────────────────────────────────────────────────────────────────
rss_items = []
for vid_id, title, hours_ago, likes, in_pages in videos:
    pub_time = now - timedelta(hours=hours_ago)
    url = f"http://localhost:18888/videos/{vid_id}/"
    rss_items.append(f"""    <item>
      <title>{title}</title>
      <link>{url}</link>
      <pubDate>{rfc2822(pub_time)}</pubDate>
      <guid>{url}</guid>
    </item>""")

rss_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Jable Latest Updates</title>
    <link>http://localhost:18888/</link>
    <description>Latest updates from Jable</description>
{chr(10).join(rss_items)}
  </channel>
</rss>"""

# ── Latest-updates HTML pages ─────────────────────────────────────────────────
# We'll split "in_pages" videos across 3 pages (5 per page)
# Pages mimic the structure that top_liked_recent.py will parse
# The script will look for video cards with like counts.
# We'll use a simple but realistic HTML structure.

in_page_videos = [(vid_id, title, likes) for vid_id, title, _, likes, in_pages in videos if in_pages]
# Shuffle deterministically
random.shuffle(in_page_videos)

PAGE_SIZE = 5
pages_html = {}
for page_num in range(1, 4):
    start = (page_num - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    chunk = in_page_videos[start:end]
    items_html = []
    for vid_id, title, likes in chunk:
        url = f"http://localhost:18888/videos/{vid_id}/"
        items_html.append(f"""      <div class="video-img-box">
        <div class="img-box">
          <a href="{url}">
            <img src="/thumb/{vid_id}.jpg" alt="{title}" />
          </a>
        </div>
        <div class="detail-box">
          <h6 class="title">
            <a href="{url}">{title}</a>
          </h6>
          <div class="metadata">
            <span class="icon-area">
              <i class="far fa-heart"></i>
              <span class="like-count">{likes}</span>
            </span>
          </div>
        </div>
      </div>""")
    page_content = "\n".join(items_html)
    pages_html[page_num] = f"""<!DOCTYPE html>
<html>
<head><title>Latest Updates - Page {page_num}</title></head>
<body>
  <div class="container">
    <div class="row">
{page_content}
    </div>
  </div>
</body>
</html>"""

# Save mock data for the server
mock_data_dir = WORKSPACE / "mock_server" / "data"
mock_data_dir.mkdir(parents=True, exist_ok=True)

(mock_data_dir / "rss.xml").write_text(rss_xml, encoding="utf-8")
for pnum, html in pages_html.items():
    (mock_data_dir / f"latest_updates_page{pnum}.html").write_text(html, encoding="utf-8")

# ── Mock server Flask app ─────────────────────────────────────────────────────
mock_server_script = '''#!/usr/bin/env python3
"""Local mock server simulating jable.tv endpoints."""
from flask import Flask, Response, request
from pathlib import Path
import sys

app = Flask(__name__)
DATA_DIR = Path(__file__).parent / "data"

@app.route("/rss/")
def rss():
    content = (DATA_DIR / "rss.xml").read_text(encoding="utf-8")
    return Response(content, mimetype="application/rss+xml")

@app.route("/latest-updates/")
def latest_updates():
    page = request.args.get("p", "1")
    try:
        page_num = int(page)
    except ValueError:
        page_num = 1
    fname = DATA_DIR / f"latest_updates_page{page_num}.html"
    if fname.exists():
        content = fname.read_text(encoding="utf-8")
    else:
        content = "<html><body><div class=\\'container\\'></div></body></html>"
    return Response(content, mimetype="text/html")

@app.route("/videos/<path:vid_id>/")
def video(vid_id):
    return Response(f"<html><body><h1>Video {vid_id}</h1></body></html>", mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=18888, debug=False)
'''
(WORKSPACE / "mock_server" / "server.py").write_text(mock_server_script)

# ── The actual skill script (top_liked_recent.py) ────────────────────────────
# This is the script referenced in SKILL.md.
# It uses JABLE_BASE_URL env var to allow local testing.
skill_script = '''#!/usr/bin/env python3
"""
Fetch and rank Jable latest-update videos by likes within a recent time window.
Usage: python3 top_liked_recent.py --hours 48 --top 3 --pages 10
"""
import argparse
import os
import sys
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin

import requests
import feedparser
from bs4 import BeautifulSoup

BASE_URL = os.environ.get("JABLE_BASE_URL", "https://jable.tv").rstrip("/")
RSS_URL = f"{BASE_URL}/rss/"
LATEST_URL = f"{BASE_URL}/latest-updates/"


def fetch_rss_items(hours: int):
    """Return dict of {url: publish_datetime} for items within the time window."""
    try:
        resp = requests.get(RSS_URL, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR: Could not fetch RSS: {e}", file=sys.stderr)
        sys.exit(1)

    feed = feedparser.parse(resp.text)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = {}
    for entry in feed.entries:
        try:
            pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            continue
        if pub >= cutoff:
            link = entry.link.rstrip("/") + "/"
            recent[link] = pub
    return recent


def fetch_likes_from_pages(pages: int):
    """Return dict of {url: (title, likes)} scraped from latest-updates pages."""
    result = {}
    for page_num in range(1, pages + 1):
        try:
            params = {} if page_num == 1 else {"p": str(page_num)}
            resp = requests.get(LATEST_URL, params=params, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"WARN: Could not fetch page {page_num}: {e}", file=sys.stderr)
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        boxes = soup.select("div.video-img-box")
        if not boxes:
            break  # No more pages

        for box in boxes:
            a_tag = box.select_one("h6.title a")
            like_tag = box.select_one("span.like-count")
            if not a_tag or not like_tag:
                continue
            url = a_tag["href"].rstrip("/") + "/"
            title = a_tag.get_text(strip=True)
            try:
                likes = int(like_tag.get_text(strip=True).replace(",", ""))
            except ValueError:
                likes = 0
            result[url] = (title, likes)
    return result


def main():
    parser = argparse.ArgumentParser(description="Top liked recent Jable videos")
    parser.add_argument("--hours", type=int, default=48, help="Recent window in hours")
    parser.add_argument("--top", type=int, default=3, help="Number of results")
    parser.add_argument("--pages", type=int, default=10, help="Pages to scan")
    args = parser.parse_args()

    recent_items = fetch_rss_items(args.hours)
    if not recent_items:
        print("No recent items found in RSS feed.")
        sys.exit(0)

    likes_data = fetch_likes_from_pages(args.pages)

    # Join: only keep items that appear in both sources
    candidates = []
    for url, pub_time in recent_items.items():
        if url in likes_data:
            title, likes = likes_data[url]
            candidates.append((title, likes, url))

    if not candidates:
        print("No recent items with like data found.")
        sys.exit(0)

    # Sort by likes descending
    candidates.sort(key=lambda x: x[1], reverse=True)

    # Output top N
    emojis = ["1\\ufe0f\\u20e3", "2\\ufe0f\\u20e3", "3\\ufe0f\\u20e3", "4\\ufe0f\\u20e3",
              "5\\ufe0f\\u20e3", "6\\ufe0f\\u20e3", "7\\ufe0f\\u20e3", "8\\ufe0f\\u20e3",
              "9\\ufe0f\\u20e3", "\\U0001f51f"]
    
    output_lines = []
    for idx, (title, likes, url) in enumerate(candidates[:args.top]):
        num_emoji = emojis[idx] if idx < len(emojis) else f"{idx+1}."
        output_lines.append(f"{num_emoji} {title}")
        output_lines.append(f"\\u2764\\ufe0f {likes}")
        output_lines.append(f"\\U0001f517 {url}")
        output_lines.append("")  # blank line separator

    print("\\n".join(output_lines).rstrip())


if __name__ == "__main__":
    main()
'''

# Fix the unicode escapes - write them as actual unicode
skill_script_fixed = """#!/usr/bin/env python3
\"\"\"
Fetch and rank Jable latest-update videos by likes within a recent time window.
Usage: python3 top_liked_recent.py --hours 48 --top 3 --pages 10
\"\"\"
import argparse
import os
import sys
from datetime import datetime, timezone, timedelta

import requests
import feedparser
from bs4 import BeautifulSoup

BASE_URL = os.environ.get("JABLE_BASE_URL", "https://jable.tv").rstrip("/")
RSS_URL = f"{BASE_URL}/rss/"
LATEST_URL = f"{BASE_URL}/latest-updates/"


def fetch_rss_items(hours: int):
    \"\"\"Return dict of {url: publish_datetime} for items within the time window.\"\"\"
    try:
        resp = requests.get(RSS_URL, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR: Could not fetch RSS: {e}", file=sys.stderr)
        sys.exit(1)

    feed = feedparser.parse(resp.text)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent = {}
    for entry in feed.entries:
        try:
            pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except Exception:
            continue
        if pub >= cutoff:
            link = entry.link.rstrip("/") + "/"
            recent[link] = pub
    return recent


def fetch_likes_from_pages(pages: int):
    \"\"\"Return dict of {url: (title, likes)} scraped from latest-updates pages.\"\"\"
    result = {}
    for page_num in range(1, pages + 1):
        try:
            params = {} if page_num == 1 else {"p": str(page_num)}
            resp = requests.get(LATEST_URL, params=params, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"WARN: Could not fetch page {page_num}: {e}", file=sys.stderr)
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        boxes = soup.select("div.video-img-box")
        if not boxes:
            break

        for box in boxes:
            a_tag = box.select_one("h6.title a")
            like_tag = box.select_one("span.like-count")
            if not a_tag or not like_tag:
                continue
            url = a_tag["href"].rstrip("/") + "/"
            title = a_tag.get_text(strip=True)
            try:
                likes = int(like_tag.get_text(strip=True).replace(",", ""))
            except ValueError:
                likes = 0
            result[url] = (title, likes)
    return result


def main():
    parser = argparse.ArgumentParser(description="Top liked recent Jable videos")
    parser.add_argument("--hours", type=int, default=48, help="Recent window in hours")
    parser.add_argument("--top", type=int, default=3, help="Number of results")
    parser.add_argument("--pages", type=int, default=10, help="Pages to scan")
    args = parser.parse_args()

    recent_items = fetch_rss_items(args.hours)
    if not recent_items:
        print("No recent items found in RSS feed.")
        sys.exit(0)

    likes_data = fetch_likes_from_pages(args.pages)

    # Join: only keep items that appear in both sources
    candidates = []
    for url, pub_time in recent_items.items():
        if url in likes_data:
            title, likes = likes_data[url]
            candidates.append((title, likes, url))

    if not candidates:
        print("No recent items with like data found.")
        sys.exit(0)

    # Sort by likes descending
    number_emojis = [
        "1\\ufe0f\\u20e3", "2\\ufe0f\\u20e3", "3\\ufe0f\\u20e3", "4\\ufe0f\\u20e3",
        "5\\ufe0f\\u20e3", "6\\ufe0f\\u20e3", "7\\ufe0f\\u20e3", "8\\ufe0f\\u20e3",
        "9\\ufe0f\\u20e3", "\\U0001f51f"
    ]

    candidates.sort(key=lambda x: x[1], reverse=True)

    lines = []
    for idx, (title, likes, url) in enumerate(candidates[:args.top]):
        num_emoji = number_emojis[idx] if idx < len(number_emojis) else f"{idx+1}."
        lines.append(f"{num_emoji} {title}")
        lines.append(f"\\u2764\\ufe0f {likes}")
        lines.append(f"\\U0001f517 {url}")
        lines.append("")

    print("\\n".join(lines).rstrip())


if __name__ == "__main__":
    main()
"""

# Write with actual unicode interpretation
import codecs

def unescape(s):
    return s.encode('utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8')

# Actually, let's just write it properly with real unicode
skill_script_proper = (
'#!/usr/bin/env python3\n'
'"""\n'
'Fetch and rank Jable latest-update videos by likes within a recent time window.\n'
'Usage: python3 top_liked_recent.py --hours 48 --top 3 --pages 10\n'
'"""\n'
'import argparse\n'
'import os\n'
'import sys\n'
'from datetime import datetime, timezone, timedelta\n'
'\n'
'import requests\n'
'import feedparser\n'
'from bs4 import BeautifulSoup\n'
'\n'
'BASE_URL = os.environ.get("JABLE_BASE_URL", "https://jable.tv").rstrip("/")\n'
'RSS_URL = f"{BASE_URL}/rss/"\n'
'LATEST_URL = f"{BASE_URL}/latest-updates/"\n'
'\n'
'\n'
'def fetch_rss_items(hours: int):\n'
'    """Return dict of {url: publish_datetime} for items within the time window."""\n'
'    try:\n'
'        resp = requests.get(RSS_URL, timeout=15)\n'
'        resp.raise_for_status()\n'
'    except Exception as e:\n'
'        print(f"ERROR: Could not fetch RSS: {e}", file=sys.stderr)\n'
'        sys.exit(1)\n'
'\n'
'    feed = feedparser.parse(resp.text)\n'
'    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)\n'
'    recent = {}\n'
'    for entry in feed.entries:\n'
'        try:\n'
'            pub = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)\n'
'        except Exception:\n'
'            continue\n'
'        if pub >= cutoff:\n'
'            link = entry.link.rstrip("/") + "/"\n'
'            recent[link] = pub\n'
'    return recent\n'
'\n'
'\n'
'def fetch_likes_from_pages(pages: int):\n'
'    """Return dict of {url: (title, likes)} scraped from latest-updates pages."""\n'
'    result = {}\n'
'    for page_num in range(1, pages + 1):\n'
'        try:\n'
'            params = {} if page_num == 1 else {"p": str(page_num)}\n'
'            resp = requests.get(LATEST_URL, params=params, timeout=15)\n'
'            resp.raise_for_status()\n'
'        except Exception as e:\n'
'            print(f"WARN: Could not fetch page {page_num}: {e}", file=sys.stderr)\n'
'            continue\n'
'\n'
'        soup = BeautifulSoup(resp.text, "lxml")\n'
'        boxes = soup.select("div.video-img-box")\n'
'        if not boxes:\n'
'            break\n'
'\n'
'        for box in boxes:\n'
'            a_tag = box.select_one("h6.title a")\n'
'            like_tag = box.select_one("span.like-count")\n'
'            if not a_tag or not like_tag:\n'
'                continue\n'
'            url = a_tag["href"].rstrip("/") + "/"\n'
'            title = a_tag.get_text(strip=True)\n'
'            try:\n'
'                likes = int(like_tag.get_text(strip=True).replace(",", ""))\n'
'            except ValueError:\n'
'                likes = 0\n'
'            result[url] = (title, likes)\n'
'    return result\n'
'\n'
'\n'
'def main():\n'
'    parser = argparse.ArgumentParser(description="Top liked recent Jable videos")\n'
'    parser.add_argument("--hours", type=int, default=48, help="Recent window in hours")\n'
'    parser.add_argument("--top", type=int, default=3, help="Number of results")\n'
'    parser.add_argument("--pages", type=int, default=10, help="Pages to scan")\n'
'    args = parser.parse_args()\n'
'\n'
'    recent_items = fetch_rss_items(args.hours)\n'
'    if not recent_items:\n'
'        print("No recent items found in RSS feed.")\n'
'        sys.exit(0)\n'
'\n'
'    likes_data = fetch_likes_from_pages(args.pages)\n'
'\n'
'    # Join: only keep items that appear in both sources\n'
'    candidates = []\n'
'    for url, pub_time in recent_items.items():\n'
'        if url in likes_data:\n'
'            title, likes = likes_data[url]\n'
'            candidates.append((title, likes, url))\n'
'\n'
'    if not candidates:\n'
'        print("No recent items with like data found.")\n'
'        sys.exit(0)\n'
'\n'
'    # Sort by likes descending\n'
'    candidates.sort(key=lambda x: x[1], reverse=True)\n'
'\n'
'    number_emojis = [\n'
'        "1\ufe0f\u20e3", "2\ufe0f\u20e3", "3\ufe0f\u20e3", "4\ufe0f\u20e3",\n'
'        "5\ufe0f\u20e3", "6\ufe0f\u20e3", "7\ufe0f\u20e3", "8\ufe0f\u20e3",\n'
'        "9\ufe0f\u20e3", "\U0001f51f"\n'
'    ]\n'
'\n'
'    lines = []\n'
'    for idx, (title, likes, url) in enumerate(candidates[:args.top]):\n'
'        num_emoji = number_emojis[idx] if idx < len(number_emojis) else f"{idx+1}."\n'
'        lines.append(f"{num_emoji} {title}")\n'
'        lines.append(f"\u2764\ufe0f {likes}")\n'
'        lines.append(f"\U0001f517 {url}")\n'
'        lines.append("")\n'
'\n'
'    print("\\n".join(lines).rstrip())\n'
'\n'
'\n'
'if __name__ == "__main__":\n'
'    main()\n'
)

(WORKSPACE / "skills/jable/scripts/top_liked_recent.py").write_text(
    skill_script_proper, encoding="utf-8"
)
(WORKSPACE / "skills/jable/scripts/__init__.py").write_text("")

# ── SKILL.md in the workspace ─────────────────────────────────────────────────
skill_md = """---
name: jable
description: Fetch and rank Jable latest-update videos by likes within a recent time window (default 48h). Use when asked to pull Jable recent updates, sort by likes/popularity, and return top N links in a formatted list.
user-invocable: true
---

# Jable

Use this skill to produce "recent + top liked" lists from Jable quickly and repeatably.

## Install

From ClawHub:

```bash
clawhub install jable
```

(If you keep it in GitHub instead, clone/copy this folder into your OpenClaw workspace as `skills/jable/`.)

## Quick Start

Run:

```bash
python3 skills/jable/scripts/top_liked_recent.py --hours 48 --top 3 --pages 10
```

Parameters:
- `--hours`: recent window in hours (default `48`)
- `--top`: number of items to output (default `3`)
- `--pages`: number of `latest-updates` pages to scan for like counts (default `10`)

## Workflow

1. Read publish times from `https://jable.tv/rss/`.
2. Read like counts from `https://jable.tv/latest-updates/` pages.
3. Keep only videos inside the requested recent window.
4. Sort by likes descending.
5. Return top N with title, likes, and URL.

## Usage (in chat)

Ask for a list like:
- "Pull Jable latest updates and show top 5 by likes from last 24h"

## Output Format

Use this style when replying to users:

```text
1️⃣ <title>
❤️ <likes>
🔗 <url>

2️⃣ <title>
❤️ <likes>
🔗 <url>
```

## Notes

- If a recent RSS item does not appear in scanned latest pages, it may miss like data and be skipped.
- Increase `--pages` when needed.
"""
(WORKSPACE / "skills/jable/SKILL.md").write_text(skill_md, encoding="utf-8")

# ── README for workspace root - deliberately unhelpful ────────────────────────
# NO hints allowed per directive
(WORKSPACE / "workspace_notes.txt").write_text(
    "Various automation skills and data pipelines.\nSee individual skill directories for details.\n"
)

print("Workspace generated successfully.")
print(f"  Skill script: {WORKSPACE}/skills/jable/scripts/top_liked_recent.py")
print(f"  Mock server:  {WORKSPACE}/mock_server/server.py")
print(f"  Mock data:    {WORKSPACE}/mock_server/data/")