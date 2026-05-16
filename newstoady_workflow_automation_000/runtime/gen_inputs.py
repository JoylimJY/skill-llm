import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create realistic distractor directory structure ---
dirs = [
    "scripts",
    "data/users",
    "data/rss_cache",
    "data/topics",
    "data/alerts",
    "logs/morning",
    "logs/evening",
    "logs/breaking",
    "config",
    "config/channels",
    "config/sources",
    "tests",
    "tests/fixtures",
    "docs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_configs = {
    "config/sources/rss_feeds.json": {
        "feeds": [
            {"name": "Sina News", "url": "https://rss.sina.com.cn/news/china/focus15.xml", "lang": "zh"},
            {"name": "The Paper", "url": "https://www.thepaper.cn/rss", "lang": "zh"},
            {"name": "36Kr", "url": "https://36kr.com/feed", "lang": "zh"},
            {"name": "BBC Chinese", "url": "https://feeds.bbci.co.uk/zhongwen/simp/rss.xml", "lang": "zh"},
            {"name": "Reuters Chinese", "url": "https://cn.reuters.com/rssfeed/cn_topnews", "lang": "zh"},
        ]
    },
    "config/channels/telegram.json": {
        "type": "telegram",
        "webhook": "https://api.telegram.org/bot{token}/sendMessage",
        "parse_mode": "Markdown"
    },
    "config/channels/slack.json": {
        "type": "slack",
        "webhook_env": "SLACK_WEBHOOK_URL",
        "icon_emoji": ":newspaper:"
    },
    "config/channels/feishu.json": {
        "type": "feishu",
        "webhook_env": "FEISHU_WEBHOOK_URL"
    },
    "config/channels/discord.json": {
        "type": "discord",
        "webhook_env": "DISCORD_WEBHOOK_URL"
    },
}

for path, content in distractor_configs.items():
    with open(workspace / path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

# --- Distractor: existing user (not the one being created) ---
existing_user = {
    "userId": "user_demo",
    "language": "en",
    "topics": ["tech", "finance"],
    "channel": "telegram",
    "preferences": {
        "tech": 0.7,
        "finance": 0.6
    },
    "push": {
        "enabled": True,
        "morning": "08:00",
        "evening": "20:00",
        "channel": "telegram"
    },
    "registeredAt": "2024-01-15T10:00:00Z"
}
with open(workspace / "data/users/user_demo.json", "w", encoding="utf-8") as f:
    json.dump(existing_user, f, ensure_ascii=False, indent=2)

# --- Distractor: stale alert config ---
stale_alert = {
    "userId": "user_demo",
    "threshold": {
        "earthquake": 7,
        "market": "circuit_breaker",
        "policy": "major"
    },
    "lastCheck": "2024-06-01T08:00:00Z"
}
with open(workspace / "data/alerts/user_demo_alert.json", "w", encoding="utf-8") as f:
    json.dump(stale_alert, f, ensure_ascii=False, indent=2)

# --- Distractor: topic definitions ---
topic_defs = {
    "topics": ["科技", "财经", "娱乐", "体育", "社会", "国际"],
    "en_topics": ["tech", "finance", "entertainment", "sports", "society", "international"],
    "weight_range": [0, 1]
}
with open(workspace / "data/topics/topic_definitions.json", "w", encoding="utf-8") as f:
    json.dump(topic_defs, f, ensure_ascii=False, indent=2)

# --- Distractor: RSS cache entries ---
rss_cache_entries = [
    {"title": "美联储宣布维持利率不变", "source": "Reuters Chinese", "timestamp": "2024-06-10T06:00:00Z", "topic": "财经"},
    {"title": "AI大模型竞争加剧", "source": "36Kr", "timestamp": "2024-06-10T07:30:00Z", "topic": "科技"},
    {"title": "G7峰会发表联合声明", "source": "BBC Chinese", "timestamp": "2024-06-10T08:15:00Z", "topic": "国际"},
]
with open(workspace / "data/rss_cache/latest.json", "w", encoding="utf-8") as f:
    json.dump(rss_cache_entries, f, ensure_ascii=False, indent=2)

# --- Distractor logs ---
for date in ["2024-06-08", "2024-06-09"]:
    with open(workspace / f"logs/morning/{date}.log", "w") as f:
        f.write(f"[{date} 08:00] Morning push delivered to user_demo via telegram\n")
        f.write(f"[{date} 08:00] 10 stories aggregated, 3 duplicates removed\n")
    with open(workspace / f"logs/evening/{date}.log", "w") as f:
        f.write(f"[{date} 20:00] Evening push delivered to user_demo via telegram\n")

# --- Distractor test fixtures ---
with open(workspace / "tests/fixtures/sample_rss_response.xml", "w") as f:
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample News Feed</title>
    <item>
      <title>Test Story</title>
      <description>Test description</description>
      <pubDate>Mon, 10 Jun 2024 08:00:00 +0800</pubDate>
    </item>
  </channel>
</rss>""")

# --- Distractor: a misconfigured user file with WRONG weight format (trap) ---
# This shows weights as integers 1-10 (wrong format) to mislead the agent
bad_example = {
    "_comment": "DEPRECATED FORMAT - do not use",
    "userId": "old_user_format",
    "preferences": {
        "科技": 8,
        "财经": 10
    }
}
with open(workspace / "data/users/_old_format_example.json", "w", encoding="utf-8") as f:
    json.dump(bad_example, f, ensure_ascii=False, indent=2)

# --- Distractor: partial config for breaking alerts ---
breaking_config = {
    "schedule": "*/2 * * * *",
    "window": {"start": "08:00", "end": "22:00"},
    "thresholds": {
        "earthquake_magnitude": 7,
        "market_events": ["circuit_breaker", "halt"],
        "policy_events": ["major_announcement"]
    }
}
with open(workspace / "config/breaking_alert_config.json", "w", encoding="utf-8") as f:
    json.dump(breaking_config, f, ensure_ascii=False, indent=2)

print("Workspace initialized with distractor files.")
print("Directory structure created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")