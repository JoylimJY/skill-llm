import os
import random
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
distractor_dirs = [
    "skills/jable/scripts",
    "skills/jable/tests",
    "skills/other_skill/scripts",
    "config/environments",
    "logs/runs",
    "data/cache",
    "reports/archive",
    "docs/internal",
    "tools/helpers",
    "tmp/scratch",
]
for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "skills/other_skill/scripts/run.py": "# placeholder\nprint('other skill')\n",
    "config/environments/prod.yaml": "env: production\napi_timeout: 30\n",
    "config/environments/staging.yaml": "env: staging\napi_timeout: 10\n",
    "logs/runs/run_2024_01_01.log": "INFO: run completed\nERROR: timeout on page 4\n",
    "logs/runs/run_2024_01_02.log": "INFO: run completed successfully\n",
    "data/cache/old_results.json": json.dumps({"cached": True, "results": []}),
    "reports/archive/weekly_2024_W01.txt": "Weekly report placeholder\n",
    "docs/internal/notes.txt": "TODO: update thresholds\n",
    "tools/helpers/utils.py": "def noop(): pass\n",
    "tmp/scratch/debug.txt": "scratch space\n",
    "skills/jable/tests/test_placeholder.py": "# tests go here\n",
}
for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.write_text(content)

# ── Build mock server data ───────────────────────────────────────────────────
# We define 8 videos; some are within 24h, some are older.
now = datetime.now(timezone.utc)

videos = [
    {
        "id": "ABC-001",
        "title": "Crystal Waters Adventure",
        "url": "https://jable.tv/videos/abc-001/",
        "pub_offset_hours": 5,       # within 24h ✓
        "likes": 3200,
        "in_pages": True,
    },
    {
        "id": "DEF-002",
        "title": "Midnight Breeze Collection",
        "url": "https://jable.tv/videos/def-002/",
        "pub_offset_hours": 12,      # within 24h ✓
        "likes": 5800,
        "in_pages": True,
    },
    {
        "id": "GHI-003",
        "title": "Golden Horizon Series",
        "url": "https://jable.tv/videos/ghi-003/",
        "pub_offset_hours": 20,      # within 24h ✓
        "likes": 4100,
        "in_pages": True,
    },
    {
        "id": "JKL-004",
        "title": "Velvet Storm Episode",
        "url": "https://jable.tv/videos/jkl-004/",
        "pub_offset_hours": 22,      # within 24h ✓
        "likes": 6700,
        "in_pages": True,
    },
    {
        "id": "MNO-005",
        "title": "Sapphire Dreams Showcase",
        "url": "https://jable.tv/videos/mno-005/",
        "pub_offset_hours": 23,      # within 24h ✓
        "likes": 2900,
        "in_pages": True,
    },
    {
        "id": "PQR-006",
        "title": "Ember Glow Feature",
        "url": "https://jable.tv/videos/pqr-006/",
        "pub_offset_hours": 18,      # within 24h ✓ BUT not in pages → should be SKIPPED
        "likes": 9999,
        "in_pages": False,           # <-- KEY TRAP: high likes but not scanned → skipped
    },
    {
        "id": "STU-007",
        "title": "Silver Dusk Anthology",
        "url": "https://jable.tv/videos/stu-007/",
        "pub_offset_hours": 30,      # OLDER than 24h → excluded
        "likes": 7500,
        "in_pages": True,
    },
    {
        "id": "VWX-008",
        "title": "Twilight Cascade Edition",
        "url": "https://jable.tv/videos/vwx-008/",
        "pub_offset_hours": 48,      # OLDER than 24h → excluded
        "likes": 8800,
        "in_pages": True,
    },
]

# ── RSS feed mock data ───────────────────────────────────────────────────────
rss_items = []
for v in videos:
    pub_time = now - timedelta(hours=v["pub_offset_hours"])
    pub_str = pub_time.strftime("%a, %d %b %Y %H:%M:%S +0000")
    rss_items.append({
        "id": v["id"],
        "title": v["title"],
        "url": v["url"],
        "pub_date": pub_str,
    })

rss_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Jable Latest Updates</title>
    <link>https://jable.tv</link>
    <description>Latest videos</description>
"""
for item in rss_items:
    rss_xml += f"""    <item>
      <title>{item['title']}</title>
      <link>{item['url']}</link>
      <guid>{item['url']}</guid>
      <pubDate>{item['pub_date']}</pubDate>
    </item>
"""
rss_xml += """  </channel>
</rss>"""

# ── Latest-updates pages mock data ──────────────────────────────────────────
# Only 3 pages will be scanned (--pages 3).
# We put videos with in_pages=True into page HTML, except PQR-006.
# Videos STU-007 and VWX-008 are in pages but excluded by time filter.
page_videos = [v for v in videos if v["in_pages"]]

def make_page_html(page_videos_subset):
    items_html = ""
    for v in page_videos_subset:
        items_html += f"""
        <div class="video-img-box">
          <a href="{v['url']}">
            <img alt="{v['title']}" />
          </a>
          <div class="detail">
            <h6 class="title"><a href="{v['url']}">{v['title']}</a></h6>
            <span class="like-count">{v['likes']}</span>
          </div>
        </div>
        """
    return f"""<!DOCTYPE html><html><body>
    <div class="container">
      {items_html}
    </div>
    </body></html>"""

# Distribute across 3 pages
page1_vids = page_videos[0:3]
page2_vids = page_videos[3:5]
page3_vids = page_videos[5:]  # STU-007, VWX-008

page_htmls = {
    1: make_page_html(page1_vids),
    2: make_page_html(page2_vids),
    3: make_page_html(page3_vids),
}

# ── Write mock data to files for the mock server to read ────────────────────
mock_data_dir = workspace / "mock_server_data"
mock_data_dir.mkdir(exist_ok=True)

(mock_data_dir / "rss.xml").write_text(rss_xml, encoding="utf-8")
for pnum, html in page_htmls.items():
    (mock_data_dir / f"page_{pnum}.html").write_text(html, encoding="utf-8")

# Write video metadata as JSON for eval reference
(mock_data_dir / "video_metadata.json").write_text(
    json.dumps(videos, indent=2), encoding="utf-8"
)

# ── Write the mock Flask server script ──────────────────────────────────────
mock_server_script = r'''#!/usr/bin/env python3
"""Mock server simulating jable.tv endpoints."""
import sys
import os
from pathlib import Path
from flask import Flask, Response, abort

app = Flask(__name__)
DATA_DIR = Path("/workspace/mock_server_data")

@app.route("/rss/")
def rss():
    content = (DATA_DIR / "rss.xml").read_text(encoding="utf-8")
    return Response(content, mimetype="application/rss+xml")

@app.route("/latest-updates/")
def latest_updates_page1():
    content = (DATA_DIR / "page_1.html").read_text(encoding="utf-8")
    return Response(content, mimetype="text/html")

@app.route("/latest-updates/<int:page>/")
def latest_updates_page(page):
    pfile = DATA_DIR / f"page_{page}.html"
    if not pfile.exists():
        abort(404)
    content = pfile.read_text(encoding="utf-8")
    return Response(content, mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
'''
(workspace / "mock_server_data" / "mock_server.py").write_text(mock_server_script)

# ── Write the actual skill script (top_liked_recent.py) ─────────────────────
# This is the script "already in workspace" per SKILL.md
skill_script = r'''#!/usr/bin/env python3
"""
Jable top-liked recent videos script.
Reads publish times from RSS and like counts from latest-updates pages.
"""
import argparse
import sys
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup

BASE_URL = os.environ.get("JABLE_BASE_URL", "https://jable.tv")

import os

def fetch_rss(base_url):
    url = f"{base_url}/rss/"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "xml")
    items = []
    for item in soup.find_all("item"):
        title = item.find("title").text.strip() if item.find("title") else ""
        link = item.find("link").text.strip() if item.find("link") else ""
        pub_date_str = item.find("pubDate").text.strip() if item.find("pubDate") else ""
        try:
            pub_dt = parsedate_to_datetime(pub_date_str)
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        except Exception:
            pub_dt = None
        items.append({"title": title, "url": link, "pub_dt": pub_dt})
    return items


def fetch_latest_updates_page(base_url, page):
    if page == 1:
        url = f"{base_url}/latest-updates/"
    else:
        url = f"{base_url}/latest-updates/{page}/"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.text


def parse_likes_from_pages(base_url, num_pages):
    """Returns dict: url -> like_count"""
    likes_map = {}
    for p in range(1, num_pages + 1):
        try:
            html = fetch_latest_updates_page(base_url, p)
        except Exception:
            break
        soup = BeautifulSoup(html, "html.parser")
        boxes = soup.find_all("div", class_="video-img-box")
        for box in boxes:
            a = box.find("a", href=True)
            like_span = box.find("span", class_="like-count")
            if a and like_span:
                href = a["href"].rstrip("/")
                try:
                    count = int(like_span.text.strip().replace(",", ""))
                except ValueError:
                    count = 0
                likes_map[href] = count
    return likes_map


def main():
    parser = argparse.ArgumentParser(description="Jable top liked recent videos")
    parser.add_argument("--hours", type=int, default=48, help="Recent window in hours")
    parser.add_argument("--top", type=int, default=3, help="Number of top results")
    parser.add_argument("--pages", type=int, default=10, help="Pages to scan for likes")
    args = parser.parse_args()

    base_url = os.environ.get("JABLE_BASE_URL", "https://jable.tv")
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=args.hours)

    # Step 1: get recent RSS items
    rss_items = fetch_rss(base_url)
    recent = [v for v in rss_items if v["pub_dt"] and v["pub_dt"] >= cutoff]

    # Step 2: get likes from latest-updates pages
    likes_map = parse_likes_from_pages(base_url, args.pages)

    # Step 3: merge — skip items with no like data
    enriched = []
    for v in recent:
        url_key = v["url"].rstrip("/")
        if url_key in likes_map:
            enriched.append({
                "title": v["title"],
                "url": v["url"],
                "likes": likes_map[url_key],
            })

    # Step 4: sort descending
    enriched.sort(key=lambda x: x["likes"], reverse=True)

    # Step 5: top N
    top = enriched[: args.top]

    # Output
    emoji_nums = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    for i, item in enumerate(top):
        num_emoji = emoji_nums[i] if i < len(emoji_nums) else f"{i+1}."
        print(f"{num_emoji} {item['title']}")
        print(f"❤️ {item['likes']}")
        print(f"🔗 {item['url']}")
        if i < len(top) - 1:
            print()


if __name__ == "__main__":
    main()
'''
(workspace / "skills" / "jable" / "scripts" / "top_liked_recent.py").write_text(skill_script)

print("Workspace initialized successfully.")
print(f"Videos created: {len(videos)}")
print(f"Within 24h: {sum(1 for v in videos if v['pub_offset_hours'] < 24)}")
print(f"In pages (scanned): {sum(1 for v in videos if v['in_pages'])}")