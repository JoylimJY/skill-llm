import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Directory structure ---
dirs = [
    "data",
    "config",
    "logs",
    "cache",
    "archive/2025-01",
    "archive/2025-02",
    "scripts",
    "templates",
    "exports",
    "raw_feeds",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- sources.json (the key config file) ---
sources_config = {
    "niche": "indie game development",
    "keywords": ["indie game", "game dev", "pixel art game", "solo developer", "game jam"],
    "reddit": {
        "subreddits": ["gamedev", "indiegaming"],
        "feed_url": "http://localhost:7331/reddit_feed"
    },
    "rss": {
        "feeds": [
            "http://localhost:7331/rss_gamedeveloper",
            "http://localhost:7331/rss_indiegames"
        ]
    },
    "youtube": {
        "search_url": "http://localhost:7331/youtube_feed"
    },
    "twitter": {
        "search_url": "http://localhost:7331/twitter_feed"
    },
    "output_dir": "data",
    "timezone": "America/New_York"
}
(workspace / "sources.json").write_text(json.dumps(sources_config, indent=2))

# --- Mock Reddit feed data (served by local server) ---
# Mix of qualifying and non-qualifying posts
reddit_data = {
    "subreddit": "gamedev",
    "posts": [
        {
            "title": "I built a full game in 30 days using only free assets — here's what I learned",
            "url": "https://reddit.com/r/gamedev/comments/abc123",
            "score": 3420,
            "num_comments": 187,
            "flair": "Discussion",
            "period": "7d"
        },
        {
            "title": "Why pixel art is having a massive comeback in 2025",
            "url": "https://reddit.com/r/gamedev/comments/def456",
            "score": 2100,
            "num_comments": 95,
            "flair": "Article",
            "period": "24h"
        },
        {
            "title": "My first game flopped — AMA about what went wrong",
            "url": "https://reddit.com/r/indiegaming/comments/ghi789",
            "score": 890,
            "num_comments": 312,
            "flair": "Discussion",
            "period": "24h"
        },
        {
            "title": "Anyone else using AI tools for game sound effects?",
            "url": "https://reddit.com/r/gamedev/comments/jkl012",
            "score": 12,
            "num_comments": 4,
            "flair": "Question",
            "period": "24h"
        },
        {
            "title": "Steam visibility algorithm changed — devs are noticing a drop",
            "url": "https://reddit.com/r/indiegaming/comments/mno345",
            "score": 4750,
            "num_comments": 421,
            "flair": "News",
            "period": "7d"
        }
    ]
}
(workspace / "raw_feeds" / "reddit_raw.json").write_text(json.dumps(reddit_data, indent=2))

# --- Mock Twitter/X feed data ---
twitter_data = {
    "keyword": "indie game",
    "tweets": [
        {
            "id": "1001",
            "text": "THREAD: 10 mistakes I made releasing my first indie game (and how to avoid them) 🧵",
            "likes": 2340,
            "retweets": 876,
            "url": "https://twitter.com/gamedevjane/status/1001",
            "format": "thread"
        },
        {
            "id": "1002",
            "text": "Hot take: Steam Next Fest has become useless for small devs. Change my mind.",
            "likes": 450,
            "retweets": 89,
            "url": "https://twitter.com/indiedevmike/status/1002",
            "format": "hot_take"
        },
        {
            "id": "1003",
            "text": "My game made $12 in its first week. Here's the breakdown.",
            "likes": 67,
            "retweets": 8,
            "url": "https://twitter.com/solodev_art/status/1003",
            "format": "list"
        },
        {
            "id": "1004",
            "text": "List: 7 free tools every solo game dev needs in 2025. Saved me 100+ hours.",
            "likes": 1870,
            "retweets": 534,
            "url": "https://twitter.com/gamedevtools/status/1004",
            "format": "list"
        },
        {
            "id": "1005",
            "text": "Pixel art shader tutorial — no Unity required",
            "likes": 88,
            "retweets": 12,
            "url": "https://twitter.com/shadergeek/status/1005",
            "format": "tutorial"
        }
    ]
}
(workspace / "raw_feeds" / "twitter_raw.json").write_text(json.dumps(twitter_data, indent=2))

# --- Mock YouTube feed data ---
youtube_data = {
    "query": "indie game development 2025",
    "videos": [
        {
            "title": "I Quit My Job to Make Games — 1 Year Later (Honest Results)",
            "channel": "IndieGameDev",
            "url": "https://youtube.com/watch?v=vid001",
            "views": 234000,
            "published_days_ago": 3,
            "description": "Honest breakdown of income, lessons, and the reality of going full-time indie"
        },
        {
            "title": "How I Got 10,000 Wishlist Signups Before Launch",
            "channel": "SteamDevPro",
            "url": "https://youtube.com/watch?v=vid002",
            "views": 87000,
            "published_days_ago": 5,
            "description": "Marketing strategy for indie games on Steam"
        },
        {
            "title": "Godot 4 vs Unity 2025 — Which Should You Use?",
            "channel": "GameEngineReview",
            "url": "https://youtube.com/watch?v=vid003",
            "views": 412000,
            "published_days_ago": 1,
            "description": "Comparing game engines for solo developers in 2025"
        },
        {
            "title": "Old game dev vlog from 2019",
            "channel": "RetroDevs",
            "url": "https://youtube.com/watch?v=vid004",
            "views": 1200,
            "published_days_ago": 2190,
            "description": "Making a game in the old days"
        }
    ]
}
(workspace / "raw_feeds" / "youtube_raw.json").write_text(json.dumps(youtube_data, indent=2))

# --- Mock RSS feed XML (stored locally, served by server) ---
rss_gamedeveloper_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Game Developer</title>
    <link>https://www.gamedeveloper.com</link>
    <description>Game development news and resources</description>
    <item>
      <title>The Rise of Solo Developers: How One-Person Studios Are Changing the Industry</title>
      <link>https://www.gamedeveloper.com/article/solo-devs-2025</link>
      <description>Analysis of how solo developers are capturing market share with focused, niche games. Key takeaway: smaller scope, stronger identity.</description>
      <pubDate>Mon, 20 Jan 2025 08:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Monetization Fatigue: Why Gamers Are Choosing Premium Indie Titles</title>
      <link>https://www.gamedeveloper.com/article/monetization-fatigue-2025</link>
      <description>Players are spending more on premium indie games as a backlash against mobile monetization tactics. Opportunity for indie devs.</description>
      <pubDate>Tue, 21 Jan 2025 10:00:00 +0000</pubDate>
    </item>
    <item>
      <title>New Porting Tools for Nintendo Switch in 2025</title>
      <link>https://www.gamedeveloper.com/article/switch-porting-2025</link>
      <description>Updated SDK and third-party tools make porting indie games to Switch easier than ever.</description>
      <pubDate>Wed, 22 Jan 2025 09:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>"""
(workspace / "raw_feeds" / "rss_gamedeveloper.xml").write_text(rss_gamedeveloper_xml)

rss_indiegames_xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Indie Games Daily</title>
    <link>https://indiegamesdaily.com</link>
    <description>Curated indie game news</description>
    <item>
      <title>Game Jam Culture: How 48-Hour Events Are Creating Full-Time Developers</title>
      <link>https://indiegamesdaily.com/game-jam-culture-2025</link>
      <description>Game jams as career launchpads. Many full-time indie devs trace their start to a 48-hour jam. Tips on leveraging jams for visibility.</description>
      <pubDate>Thu, 23 Jan 2025 07:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Discord Communities as Marketing Channels for Indie Devs</title>
      <link>https://indiegamesdaily.com/discord-marketing-2025</link>
      <description>Building pre-launch communities on Discord has become a key strategy for indie success in 2025.</description>
      <pubDate>Fri, 24 Jan 2025 11:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>"""
(workspace / "raw_feeds" / "rss_indiegames.xml").write_text(rss_indiegames_xml)

# --- Distractor files ---
# Old archive reports (different schema, wrong format)
old_report = {"date": "2024-11-01", "topics": ["unity", "godot"], "raw_notes": "informal notes"}
(workspace / "archive" / "2025-01" / "old-report-2025-01-15.json").write_text(json.dumps(old_report, indent=2))

# A half-finished template with wrong field names (trap)
bad_template = {
    "date": "YYYY-MM-DD",
    "topics": [],
    "ideas": [],
    "formats": []
}
(workspace / "templates" / "report-template-DRAFT.json").write_text(json.dumps(bad_template, indent=2))

# Config files that look important but aren't
(workspace / "config" / "scheduler.yaml").write_text("""schedule: "0 6 * * *"\ntimezone: "America/New_York"\nenabled: true\n""")
(workspace / "config" / "notifications.yaml").write_text("""channel: slack\nwebhook: ""\nenabled: false\n""")

# Log files
(workspace / "logs" / "scraper-2025-01-20.log").write_text("[INFO] Run started\n[INFO] Reddit: 5 posts fetched\n[ERROR] Twitter API rate limited\n[INFO] Run complete\n")
(workspace / "logs" / "scraper-2025-01-21.log").write_text("[INFO] Run started\n[INFO] All sources checked\n[INFO] Report saved\n")

# Cache files
(workspace / "cache" / "reddit_cache_2025-01.json").write_text(json.dumps({"cached": True, "posts": []}, indent=2))
(workspace / "cache" / "youtube_cache_2025-01.json").write_text(json.dumps({"cached": True, "videos": []}, indent=2))

# Scripts directory
(workspace / "scripts" / "clean_cache.sh").write_text("#!/bin/bash\nrm -rf ../cache/*\necho 'Cache cleared'\n")
(workspace / "scripts" / "archive_reports.sh").write_text("#!/bin/bash\nmv ../data/*.json ../archive/\necho 'Archived'\n")

# Exports
(workspace / "exports" / "content-calendar-2025-01.csv").write_text("date,title,format,status\n2025-01-15,Indie Game Mistakes,thread,published\n2025-01-22,Pixel Art Guide,article,draft\n")

# A confusing near-miss file with wrong structure
near_miss = {
    "report_date": "2025-01-24",
    "trending": [{"name": "pixel art", "platform": "twitter"}],
    "post_ideas": [{"headline": "some idea"}]
}
(workspace / "data" / "partial-report-2025-01-24.json").write_text(json.dumps(near_miss, indent=2))

print("Workspace initialized successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")