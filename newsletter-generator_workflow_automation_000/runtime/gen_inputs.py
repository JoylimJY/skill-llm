import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ────────────────────────────────────────────────────────
dirs = [
    "scripts",
    "newsletters/drafts",
    "newsletters/archive",
    "data/feeds",
    "data/metrics",
    "data/segments",
    "config",
    "logs",
    "templates",
    "reports",
    "assets/images",
    "assets/fonts",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractors = {
    "config/app_config.yaml": """\
app:
  name: newsletter-generator
  version: 1.3.2
  debug: false
database:
  host: localhost
  port: 5432
  name: newsletters_db
cache:
  ttl: 3600
""",
    "config/smtp_config.yaml": """\
smtp:
  host: smtp.mailgun.org
  port: 587
  from_address: hello@fintech-weekly.com
  from_name: FinTech Weekly
""",
    "data/segments/subscribers.csv": """\
subscriber_id,email,segment,timezone,join_date
1001,alice@example.com,early_adopters,America/New_York,2023-01-15
1002,bob@example.com,investors,America/Chicago,2023-02-20
1003,carol@example.com,early_adopters,Europe/London,2023-03-10
1004,dave@example.com,founders,America/Los_Angeles,2023-04-05
""",
    "data/metrics/open_rates.json": json.dumps({
        "2024-01": {"open_rate": 0.28, "ctr": 0.042},
        "2024-02": {"open_rate": 0.31, "ctr": 0.038},
        "2024-03": {"open_rate": 0.25, "ctr": 0.051},
    }, indent=2),
    "data/metrics/affiliate_performance.json": json.dumps({
        "amazon": {"clicks": 340, "conversions": 12, "revenue": 87.50},
        "shareasale": {"clicks": 210, "conversions": 8, "revenue": 112.00},
    }, indent=2),
    "logs/generation.log": """\
2024-03-01 08:01:12 INFO Newsletter generated: daily_20240301.md
2024-03-01 08:01:15 INFO Affiliate links added: 3
2024-03-02 08:00:58 INFO Newsletter generated: daily_20240302.md
""",
    "newsletters/archive/daily_20240301.md": """\
# FinTech Daily - March 1, 2024

## Today's Top Stories

**Fed Signals Rate Pause**
Central bank hints at holding rates steady through Q2.
[Read more →](https://example.com/fed-rates)

---
*Affiliate Disclosure: This newsletter contains affiliate links.*
""",
    "newsletters/drafts/ideas.txt": """\
Ideas for upcoming newsletters:
- DeFi explained for beginners
- Best robo-advisors 2024
- How to read a balance sheet
- Top fintech APIs for developers
""",
    "templates/header.html": """\
<!DOCTYPE html>
<html>
<head><title>{{title}}</title></head>
<body>
<header><h1>FinTech Weekly</h1></header>
""",
    "templates/footer.html": """\
<footer>
<p>Unsubscribe | Privacy Policy</p>
</footer>
</body>
</html>
""",
    "reports/q1_summary.txt": """\
Q1 2024 Newsletter Performance Summary
Total newsletters sent: 13
Average open rate: 28.0%
Average CTR: 4.4%
Total affiliate revenue: $1,243.00
""",
    "assets/fonts/README.txt": "Font assets for HTML newsletter rendering.",
}

for rel_path, content in distractors.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content)

# ── Mock scripts that simulate the newsletter-generator toolchain ──────────────
# generate_newsletter.py
generate_newsletter = r'''#!/usr/bin/env python3
"""Mock generate_newsletter.py - simulates newsletter generation."""
import argparse
import sys
import json
from datetime import date

parser = argparse.ArgumentParser()
parser.add_argument("--type", required=True)
parser.add_argument("--topic", required=True)
parser.add_argument("--articles", type=int, default=10)
parser.add_argument("--affiliate-links", type=int, default=0)
parser.add_argument("--include-tutorials", action="store_true")
parser.add_argument("--include-products", action="store_true")
parser.add_argument("--tone", default="professional")
parser.add_argument("--output", required=True)
args = parser.parse_args()

today = date.today().strftime("%B %d, %Y")

lines = []

if args.type == "weekly":
    subject = f"Subject: {args.topic.replace('-',' ').title()} Weekly Roundup - Top {args.articles} Stories"
elif args.type == "daily":
    subject = f"Subject: {args.topic.replace('-',' ').title()} Daily Digest - {today}"
else:
    subject = f"Subject: {args.topic.replace('-',' ').title()} {args.type.title()} - {today}"

lines.append(subject)
lines.append("")
lines.append("---")
lines.append("")

if args.type == "weekly":
    lines.append("## This Week's Highlights")
else:
    lines.append("## Today's Top Stories")
lines.append("")

for i in range(1, args.articles + 1):
    lines.append(f"**Article {i}: {args.topic.replace('-',' ').title()} Insight #{i}**")
    lines.append(f"A curated insight about {args.topic} for our readers. Tone: {args.tone}.")
    lines.append(f"[Read more →](https://example.com/article-{i})")
    lines.append("")

if args.include_tutorials:
    lines.append("## Tutorial Corner")
    lines.append("")
    lines.append("**Getting Started with " + args.topic.replace("-"," ").title() + "**")
    lines.append("Step-by-step guide for beginners.")
    lines.append("")

if args.include_products:
    lines.append("## Recommended Resources")
    lines.append("")
    lines.append("**Top Tool for " + args.topic.replace("-"," ").title() + "**")
    lines.append("Boost your workflow with this recommended product.")
    lines.append("[Get it here →](https://example.com/product)")
    lines.append("")

if args.affiliate_links > 0:
    lines.append("## Featured Resource")
    lines.append("")
    for j in range(1, args.affiliate_links + 1):
        lines.append(f"**Affiliate Pick #{j}**")
        lines.append(f"Recommended product #{j} related to {args.topic}.")
        lines.append(f"[Get it here →](https://example.com/affiliate-{j})")
        lines.append("")

lines.append("---")
lines.append("")
lines.append("*Affiliate Disclosure: This newsletter may contain affiliate links.*")
lines.append("")

# Store metadata as JSON comment for eval
meta = {
    "type": args.type,
    "topic": args.topic,
    "articles": args.articles,
    "affiliate_links": args.affiliate_links,
    "include_tutorials": args.include_tutorials,
    "include_products": args.include_products,
    "tone": args.tone,
}
lines.append(f"<!-- META:{json.dumps(meta)} -->")

with open(args.output, "w") as f:
    f.write("\n".join(lines) + "\n")

print(f"[generate_newsletter] Generated {args.type} newsletter: {args.output}")
print(f"[generate_newsletter] Articles: {args.articles}, Affiliate links: {args.affiliate_links}, Tone: {args.tone}")
'''

# curate_content.py
curate_content = r'''#!/usr/bin/env python3
"""Mock curate_content.py - simulates content curation."""
import argparse
import json
import sys

parser = argparse.ArgumentParser()
parser.add_argument("--rss-feeds", default="")
parser.add_argument("--keywords", default="")
parser.add_argument("--max-articles", type=int, default=10)
parser.add_argument("--min-relevance", type=float, default=0.0)
parser.add_argument("--output", required=True)
args = parser.parse_args()

feeds = [f.strip() for f in args.rss_feeds.split(",") if f.strip()]
keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]

articles = []
for i in range(1, args.max_articles + 1):
    relevance = round(0.5 + (i % 5) * 0.1, 2)
    if relevance < args.min_relevance:
        continue
    articles.append({
        "id": i,
        "title": f"Article {i}: {', '.join(keywords[:2]) if keywords else 'General'} Insights",
        "url": f"https://example-feed.com/article-{i}",
        "source": feeds[i % len(feeds)] if feeds else "https://default-feed.com/rss",
        "summary": f"This article covers key insights about {', '.join(keywords)}.",
        "relevance_score": relevance,
        "keywords_matched": keywords,
    })

output = {
    "feeds": feeds,
    "keywords": keywords,
    "min_relevance": args.min_relevance,
    "max_articles": args.max_articles,
    "articles_found": len(articles),
    "articles": articles,
}

with open(args.output, "w") as f:
    json.dump(output, f, indent=2)

print(f"[curate_content] Curated {len(articles)} articles (min_relevance={args.min_relevance}) -> {args.output}")
'''

# add_affiliate_links.py
add_affiliate = r'''#!/usr/bin/env python3
"""Mock add_affiliate_links.py - adds affiliate links to newsletter."""
import argparse
import json
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--input", required=True)
parser.add_argument("--network", required=True, choices=["amazon","shareasale","cj","impact"])
parser.add_argument("--links", type=int, default=3)
parser.add_argument("--disclosure-position", required=True, choices=["top","bottom","inline"])
args = parser.parse_args()

content = Path(args.input).read_text()

disclosure = f"*FTC DISCLOSURE: This newsletter contains affiliate links from {args.network.upper()}. We may earn a commission at no extra cost to you.*"

new_links = []
for i in range(1, args.links + 1):
    new_links.append(f"\n**[{args.network.upper()} Affiliate #{i}]** - Recommended resource #{i}.\n[Shop now →](https://track.{args.network}.com/link/{i})\n")

affiliate_block = "\n## Affiliate Recommendations\n" + "".join(new_links)

# Insert disclosure
if args.disclosure_position == "top":
    content = disclosure + "\n\n" + content
elif args.disclosure_position == "bottom":
    content = content.rstrip() + "\n\n" + disclosure + "\n"
elif args.disclosure_position == "inline":
    content = content.replace("---\n", f"---\n{disclosure}\n", 1)

# Append affiliate block
content = content.rstrip() + "\n" + affiliate_block

# Append metadata for eval
affiliate_meta = {
    "network": args.network,
    "links_added": args.links,
    "disclosure_position": args.disclosure_position,
}
content += f"\n<!-- AFFILIATE_META:{json.dumps(affiliate_meta)} -->\n"

Path(args.input).write_text(content)
print(f"[add_affiliate_links] Added {args.links} {args.network} links (disclosure: {args.disclosure_position}) to {args.input}")
'''

# schedule_newsletter.py
schedule_nl = r'''#!/usr/bin/env python3
"""Mock schedule_newsletter.py - generates schedule JSON for ESP."""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import pytz

parser = argparse.ArgumentParser()
parser.add_argument("--newsletter", required=True)
parser.add_argument("--send-time", required=True)
parser.add_argument("--timezone", required=True)
parser.add_argument("--segments", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

try:
    tz = pytz.timezone(args.timezone)
    tz_valid = True
except pytz.UnknownTimeZoneError:
    tz_valid = False

now = datetime.now()
schedule_data = {
    "newsletter_file": args.newsletter,
    "send_time": args.send_time,
    "timezone": args.timezone,
    "timezone_valid": tz_valid,
    "segments": [s.strip() for s in args.segments.split(",")],
    "scheduled_at": now.strftime("%Y-%m-%dT%H:%M:%S"),
    "esp_ready": True,
}

with open(args.output, "w") as f:
    json.dump(schedule_data, f, indent=2)

print(f"[schedule_newsletter] Scheduled -> {args.output} | time={args.send_time} tz={args.timezone} segments={args.segments}")
'''

scripts = {
    "scripts/generate_newsletter.py": generate_newsletter,
    "scripts/curate_content.py": curate_content,
    "scripts/add_affiliate_links.py": add_affiliate,
    "scripts/schedule_newsletter.py": schedule_nl,
}

for rel, code in scripts.items():
    fpath = WORKSPACE / rel
    fpath.write_text(code)

print("Workspace generated successfully.")
print(f"Files created: {len(distractors) + len(scripts)}")