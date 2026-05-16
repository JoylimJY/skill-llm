import os
import random
import csv

random.seed(42)

# -------------------------------------------------------------------
# Directory scaffold
# -------------------------------------------------------------------
base = "/workspace"
dirs = [
    "analytics/exports/sessions",
    "analytics/exports/events",
    "analytics/channel_config",
    "analytics/reports/monthly",
    "analytics/reports/weekly",
    "seo/gsc_exports",
    "seo/keyword_lists",
    "marketing/campaigns/q1",
    "marketing/campaigns/q2",
    "ops/logs",
    "ops/cron",
    "docs/internal",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# -------------------------------------------------------------------
# Distractor files
# -------------------------------------------------------------------
distractors = {
    "analytics/exports/events/page_view_events_march.csv": (
        "event_name,page_location,user_pseudo_id\n"
        "page_view,https://bookstore.example.com/books/fiction,abc123\n"
        "scroll,https://bookstore.example.com/books/fiction,abc123\n"
    ),
    "analytics/reports/monthly/march_summary.txt": (
        "March 2024 Summary\n"
        "Total Sessions: 120,000\n"
        "Bounce Rate: 42%\n"
        "Top Page: /books/bestsellers\n"
    ),
    "analytics/reports/weekly/week12.txt": (
        "Week 12 Traffic Notes\n"
        "- Organic up 8%\n"
        "- Direct down 3%\n"
        "- Referral stable\n"
    ),
    "analytics/channel_config/old_channel_group_v1.json": (
        '{\n  "name": "Default Channel Group (Legacy)",\n'
        '  "channels": [\n'
        '    {"name": "Organic Search", "filter": "medium == organic"},\n'
        '    {"name": "Paid Search", "filter": "medium == cpc"},\n'
        '    {"name": "Referral", "filter": "medium == referral"},\n'
        '    {"name": "Direct", "filter": "source == direct"}\n'
        '  ]\n}\n'
    ),
    "seo/gsc_exports/impressions_q1.csv": (
        "query,impressions,clicks,ctr,position\n"
        "buy books online,5200,310,0.06,4.2\n"
        "best fiction 2024,3100,180,0.058,6.1\n"
        "cheap textbooks,2800,95,0.034,9.3\n"
    ),
    "seo/keyword_lists/ai_related_queries.txt": (
        "# Queries that seem to come via AI assistants\n"
        "what are the best books recommended by chatgpt\n"
        "perplexity book recommendations\n"
        "ai suggested reading list\n"
    ),
    "marketing/campaigns/q1/utm_plan.txt": (
        "Q1 UTM Plan\n"
        "campaign=spring_sale&source=newsletter&medium=email\n"
        "campaign=spring_sale&source=instagram&medium=social\n"
    ),
    "marketing/campaigns/q2/budget_notes.txt": (
        "Q2 Budget: $45,000 total\n"
        "AI-related content investment: $8,000\n"
        "Paid Search: $20,000\n"
    ),
    "ops/logs/server_access_march.log": (
        "2024-03-01 00:01:22 GET /books/fiction 200\n"
        "2024-03-01 00:01:45 GET /cart 200\n"
        "2024-03-01 00:02:11 POST /checkout 302\n"
    ),
    "ops/cron/daily_export.sh": (
        "#!/bin/bash\n"
        "# Export GA4 data to GCS bucket\n"
        "bq export --project=bookstore-analytics --table=sessions_raw\n"
    ),
    "docs/internal/analytics_glossary.txt": (
        "Glossary\n"
        "Session Source: The domain or platform that referred a user.\n"
        "Medium: Categorization (organic, cpc, referral, etc.)\n"
        "Channel: Grouping of sessions by source/medium rules.\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(base, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# -------------------------------------------------------------------
# THE CORE PROBLEM FILE: messy raw session export
# -------------------------------------------------------------------
# These are the actual AI sources from the SKILL.md (exact domains)
# plus some imposter sources and organic/direct/paid that must NOT be classified as AI
ai_sources = [
    "chatgpt.com",
    "openai.com",
    "openai",                        # bare token — must be caught
    "perplexity.ai",
    "perplexity",                    # bare token — must be caught
    "doubao.com",
    "chat.qwen.ai",
    "copilot.microsoft.com",
    "copilot.com",
    "business.gemini.google",
    "gemini.google",                 # partial match of (business\.)?gemini\.google
    "chat.deepseek.com",
    "deepseek.com",
    "poe.com",
    "anthropic.com",
    "claude.ai",
    "bard.google.com",
    "edgeservices.bing.com",
]

non_ai_sources = [
    "google",
    "bing",
    "(direct)",
    "facebook.com",
    "twitter.com",
    "reddit.com",
    "newsletter.bookstore.com",
    "amazon.com",
    "goodreads.com",
    "instagram.com",
    "tiktok.com",
    "youtube.com",
    "duckduckgo.com",
    "linkedin.com",
    "yahoo",
]

rows = []
session_id = 1000

# Generate sessions: heavy non-AI majority, meaningful AI minority
for source in non_ai_sources:
    count = random.randint(40, 120)
    for _ in range(count):
        rows.append({
            "session_id": f"S{session_id}",
            "session_source": source,
            "sessions": 1,
            "engaged_sessions": random.randint(0, 1),
            "conversions": random.randint(0, 1) if random.random() < 0.05 else 0,
        })
        session_id += 1

for source in ai_sources:
    count = random.randint(8, 35)
    for _ in range(count):
        rows.append({
            "session_id": f"S{session_id}",
            "session_source": source,
            "sessions": 1,
            "engaged_sessions": random.randint(0, 1),
            "conversions": random.randint(0, 1) if random.random() < 0.12 else 0,
        })
        session_id += 1

# Shuffle to make it messy
random.shuffle(rows)

out_path = os.path.join(base, "analytics/exports/sessions/raw_sessions_april.csv")
with open(out_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["session_id", "session_source", "sessions", "engaged_sessions", "conversions"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} session rows.")
print("Workspace setup complete.")