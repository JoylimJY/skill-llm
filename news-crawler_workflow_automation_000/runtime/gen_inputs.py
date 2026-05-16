import os
import json
import random
import string

random.seed(42)

# Create directory structure
dirs = [
    "scripts",
    "references",
    "logs",
    "cache",
    "cache/html",
    "cache/rss",
    "reports/archive",
    "reports/drafts",
    "config",
    "data/raw",
    "data/processed",
    "tmp",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ─── Distractor files ───────────────────────────────────────────────────────

# references/rss_sources.md
with open("references/rss_sources.md", "w") as f:
    f.write("""# RSS Sources Reference

## Technology
- Solidot: https://www.solidot.org/index.rss
- TechWeb: https://www.techweb.com.cn/rss/all.xml
- 36kr: https://36kr.com/feed
- Hacker News: https://news.ycombinator.com/rss
- TechCrunch: https://techcrunch.com/feed/
- The Verge: https://www.theverge.com/rss/index.xml
- Wired: https://www.wired.com/feed/rss

## Finance
- Bloomberg: https://feeds.bloomberg.com/technology/news.rss
- Reuters: https://feeds.reuters.com/reuters/technologyNews

## Local Mock (for testing)
- Local Test Feed: http://localhost:8765/feed.rss
""")

# config/crawler_config.json
with open("config/crawler_config.json", "w") as f:
    json.dump({
        "default_max_items": 10,
        "default_max_length": 5000,
        "retry_attempts": 3,
        "delay_seconds": 1,
        "user_agent": "NewsCrawler/1.0"
    }, f, indent=2)

# logs/crawler.log (distractor)
with open("logs/crawler.log", "w") as f:
    f.write("""2024-01-15 08:00:01 INFO Starting crawler
2024-01-15 08:00:02 INFO Fetching RSS from https://www.solidot.org/index.rss
2024-01-15 08:00:05 INFO Got 10 items
2024-01-15 08:00:06 INFO Crawling article 1/10
2024-01-15 08:00:08 WARNING Slow response from server
2024-01-15 08:00:45 INFO Completed crawl cycle
""")

# reports/archive/report_20240114.json (old report, distractor)
with open("reports/archive/report_20240114.json", "w") as f:
    json.dump({
        "date": "2024-01-14",
        "articles": [
            {"title": "Old Article 1", "url": "http://example.com/1", "summary": "Old summary 1"},
            {"title": "Old Article 2", "url": "http://example.com/2", "summary": "Old summary 2"},
        ]
    }, f, indent=2)

# reports/drafts/template.txt
with open("reports/drafts/template.txt", "w") as f:
    f.write("""Daily News Report Template
==========================
Date: {date}
Source: {source}
Articles: {count}

[Article List]
""")

# data/raw/sample_feed.xml (distractor - malformed/old format)
with open("data/raw/sample_feed.xml", "w") as f:
    f.write("""<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>Sample Old Feed</title>
    <item><title>Stale Article</title><link>http://old.example.com/1</link></item>
  </channel>
</rss>
""")

# cache/rss/cached_feed.json (distractor)
with open("cache/rss/cached_feed.json", "w") as f:
    json.dump({"cached_at": "2024-01-13T00:00:00Z", "items": [], "count": 0}, f)

# data/processed/articles_processed.csv (distractor)
with open("data/processed/articles_processed.csv", "w") as f:
    f.write("id,title,url,processed_at\n")
    f.write("1,Test Article,http://example.com,2024-01-13\n")

# tmp/scratch.txt
with open("tmp/scratch.txt", "w") as f:
    f.write("temporary notes\ndo not use\n")

# config/sources.yaml (distractor)
with open("config/sources.yaml", "w") as f:
    f.write("""sources:
  - name: solidot
    url: https://www.solidot.org/index.rss
    category: tech
  - name: hackernews
    url: https://news.ycombinator.com/rss
    category: tech
""")

# ─── Actual scripts (rss_fetcher.py and crawl.py) ──────────────────────────

rss_fetcher_code = '''#!/usr/bin/env python3
"""
RSS Fetcher - Fetches news items from an RSS feed.

Usage:
    python3 scripts/rss_fetcher.py                        # list default sources
    python3 scripts/rss_fetcher.py <rss_url> [max_items]  # fetch from URL

Output JSON format:
    {
      "items": [
        {
          "title": "Article title",
          "link": "Article URL",
          "description": "Short description",
          "published": "Publication datetime string"
        }
      ],
      "count": N
    }
"""

import sys
import json
import feedparser

DEFAULT_SOURCES = [
    {"name": "Solidot", "url": "https://www.solidot.org/index.rss"},
    {"name": "Hacker News", "url": "https://news.ycombinator.com/rss"},
    {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
]

def fetch_rss(url, max_items=10):
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:max_items]:
        item = {
            "title": getattr(entry, "title", ""),
            "link": getattr(entry, "link", ""),
            "description": getattr(entry, "summary", getattr(entry, "description", "")),
            "published": getattr(entry, "published", getattr(entry, "updated", "")),
        }
        items.append(item)
    result = {"items": items, "count": len(items)}
    return result

def main():
    if len(sys.argv) == 1:
        print("Available RSS sources:")
        for src in DEFAULT_SOURCES:
            print(f"  {src[\'name\']}: {src[\'url\']}")
        print()
        print("Usage: python3 scripts/rss_fetcher.py <rss_url> [max_items]")
        return

    url = sys.argv[1]
    max_items = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    result = fetch_rss(url, max_items)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
'''

crawl_code = '''#!/usr/bin/env python3
"""
Web Crawler - Fetches and extracts content from a web page.

Usage:
    python3 scripts/crawl.py <url> [max_length]

Arguments:
    url         - The URL to crawl
    max_length  - Maximum number of characters to return (default: 5000)

Output JSON format:
    {
      "url": "original URL",
      "title": "page title",
      "content": "extracted text content",
      "length": N
    }
"""

import sys
import json
import requests
from bs4 import BeautifulSoup

def crawl(url, max_length=5000):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; NewsCrawler/1.0)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Remove script and style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Extract text
        content = soup.get_text(separator=" ", strip=True)
        # Normalize whitespace
        import re
        content = re.sub(r"\\s+", " ", content).strip()

        # Apply max_length limit
        if len(content) > max_length:
            content = content[:max_length]

        result = {
            "url": url,
            "title": title,
            "content": content,
            "length": len(content),
        }
        return result

    except Exception as e:
        return {
            "url": url,
            "title": "",
            "content": f"Error fetching content: {str(e)}",
            "length": 0,
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/crawl.py <url> [max_length]")
        sys.exit(1)

    url = sys.argv[1]
    max_length = int(sys.argv[2]) if len(sys.argv) > 2 else 5000

    result = crawl(url, max_length)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
'''

with open("scripts/rss_fetcher.py", "w", encoding="utf-8") as f:
    f.write(rss_fetcher_code)

with open("scripts/crawl.py", "w", encoding="utf-8") as f:
    f.write(crawl_code)

# ─── Mock server script ──────────────────────────────────────────────────────

mock_server_code = '''#!/usr/bin/env python3
"""Local mock HTTP server for testing the news crawler pipeline."""

from flask import Flask, Response
import json

app = Flask(__name__)

ARTICLES = [
    {
        "id": 1,
        "title": "Quantum Computing Breakthrough Achieved at MIT",
        "published": "Mon, 15 Jan 2024 09:00:00 GMT",
        "description": "Researchers claim a new milestone.",
        "content": """Scientists at MIT have achieved a significant breakthrough in quantum computing,
demonstrating a 1000-qubit processor capable of solving optimization problems
that would take classical computers centuries. The team used a novel error-correction
algorithm called SurfaceCode-X that reduces decoherence rates by 99.7 percent.
The processor operates at temperatures near absolute zero and uses superconducting
Josephson junctions. Dr. Emily Zhang, lead researcher, stated that commercial
applications in drug discovery and financial modeling could be available within
five years. The research was published in Nature Quantum Information and has
been peer-reviewed by three independent teams. Funding was provided by DARPA
and the NSF under a 50 million dollar grant awarded in 2022. The team plans
to scale the system to 10000 qubits by 2026, which would represent a genuine
quantum advantage over all known classical algorithms. Industry observers note
this could accelerate AI training by orders of magnitude.""" * 3,
    },
    {
        "id": 2,
        "title": "OpenAI Unveils GPT-5 with Multimodal Reasoning",
        "published": "Mon, 15 Jan 2024 10:30:00 GMT",
        "description": "OpenAI releases its most powerful model yet.",
        "content": """OpenAI has officially unveiled GPT-5, describing it as a major leap forward
in artificial intelligence capabilities. The model demonstrates unprecedented
performance on reasoning benchmarks, scoring 97 percent on the MATH dataset
and achieving human-level performance on the bar exam across all jurisdictions.
GPT-5 features native multimodal input processing, able to analyze text, images,
audio, and video simultaneously. The context window has been extended to 2 million
tokens, enabling the model to process entire codebases or books in a single pass.
CEO Sam Altman noted that safety testing took 18 months before release, involving
over 500 external red teamers. The model introduces a new alignment technique
called Constitutional Reinforcement Learning that allows fine-grained control
over model behavior. Enterprise pricing starts at 30 dollars per million tokens.
Competitors including Google DeepMind and Anthropic are expected to respond
with their own announcements later this quarter.""" * 3,
    },
    {
        "id": 3,
        "title": "Global Chip Shortage Eases as TSMC Expands Capacity",
        "published": "Mon, 15 Jan 2024 11:00:00 GMT",
        "description": "TSMC announces new fab in Arizona.",
        "content": """Taiwan Semiconductor Manufacturing Company has announced the completion of
its second fabrication plant in Phoenix, Arizona, adding 60000 wafer starts
per month to global chip supply. The facility, built with 40 billion dollars
in investment co-funded by the US CHIPS Act, will produce 3nm chips beginning
in Q3 2024. This development is expected to significantly ease the semiconductor
shortage that has plagued the automotive and consumer electronics industries
since 2021. TSMC Chairman Mark Liu stated the Arizona fabs will eventually
employ over 20000 skilled workers. Apple, NVIDIA, and AMD have already secured
long-term supply contracts. Analysts predict GPU prices will drop by 25 percent
by year end. The US government views this as a critical step toward reducing
dependence on Asian chip manufacturing for national security applications.
Intel and Samsung are also expanding domestic capacity in response to CHIPS Act incentives.""" * 3,
    },
    {
        "id": 4,
        "title": "SpaceX Starship Completes First Orbital Test Flight",
        "published": "Mon, 15 Jan 2024 12:00:00 GMT",
        "description": "Historic launch marks new era in space travel.",
        "content": """SpaceX successfully completed the first full orbital test flight of its Starship
vehicle, marking a historic milestone in commercial space exploration. The 120-meter
tall rocket reached orbit and successfully re-entered the atmosphere, with the
Super Heavy booster returning to the launch mount in a precision catch maneuver.
Elon Musk called it the greatest engineering achievement in human history.
NASA is counting on Starship to serve as the lunar lander for the Artemis III
mission planned for 2026. The vehicle can carry up to 150 tonnes to low Earth orbit,
making it the most capable rocket ever built. The test flight lasted 90 minutes
and covered approximately half the globe. SpaceX engineers will now analyze
data from over 5000 sensors before proceeding to the next test phase.
The FAA cleared the launch after an extended environmental review process.""" * 3,
    },
    {
        "id": 5,
        "title": "Cybersecurity Alert: New Ransomware Targets Healthcare Systems",
        "published": "Mon, 15 Jan 2024 13:00:00 GMT",
        "description": "CISA issues emergency alert for hospitals.",
        "content": """The US Cybersecurity and Infrastructure Security Agency has issued an emergency
alert warning healthcare organizations about a sophisticated new ransomware strain
dubbed BlackPhoenix. The malware exploits a zero-day vulnerability in widely used
medical device management software. At least 47 hospitals across 12 states have
been affected in the past 72 hours, with attackers demanding ransoms ranging from
500000 to 5 million dollars in Bitcoin. Patient care disruptions have been reported
as electronic health record systems were taken offline. CISA recommends immediate
network segmentation and application of emergency patches released by the vendor.
The FBI has linked the attacks to a group operating from Eastern Europe. Healthcare
cybersecurity spending is expected to increase by 35 percent in 2024 as a result.
Congress is considering emergency legislation to mandate minimum cybersecurity
standards for medical device manufacturers.""" * 3,
    },
]

RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Tech Intelligence Daily</title>
    <link>http://localhost:8765</link>
    <description>Daily technology news briefing</description>
    {items}
  </channel>
</rss>"""

ITEM_TEMPLATE = """    <item>
      <title>{title}</title>
      <link>http://localhost:8765/article/{id}</link>
      <description>{description}</description>
      <pubDate>{published}</pubDate>
    </item>"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head><title>{title}</title></head>
<body>
<h1>{title}</h1>
<p class="date">{published}</p>
<article>
{content}
</article>
</body>
</html>"""

@app.route("/feed.rss")
def rss_feed():
    items_xml = "\\n".join(
        ITEM_TEMPLATE.format(
            title=a["title"],
            id=a["id"],
            description=a["description"],
            published=a["published"],
        )
        for a in ARTICLES
    )
    xml = RSS_TEMPLATE.format(items=items_xml)
    return Response(xml, mimetype="application/rss+xml")

@app.route("/article/<int:article_id>")
def article(article_id):
    for a in ARTICLES:
        if a["id"] == article_id:
            html = HTML_TEMPLATE.format(
                title=a["title"],
                published=a["published"],
                content=a["content"],
            )
            return Response(html, mimetype="text/html")
    return Response("Not Found", status=404)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
'''

with open("scripts/mock_server.py", "w", encoding="utf-8") as f:
    f.write(mock_server_code)

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("."):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")