#!/usr/bin/env python3
"""
Generate the sandbox workspace for the outreach sequencer task.
"""
import os
import json
import random
import duckdb
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── Directory structure with distractor files ──────────────────────────────
dirs = [
    "crm/exports",
    "crm/archive",
    "crm/templates_old",
    "analytics/q1",
    "analytics/q2",
    "configs/deprecated",
    "configs/active",
    "scripts/util",
    "scripts/archive",
    "notes",
    "data/raw",
    "data/processed",
]
for d in dirs:
    Path(f"{WORKSPACE}/{d}").mkdir(parents=True, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────
distractors = {
    "crm/exports/leads_export_2023_q4.csv": "Name,Email,Company,Title\nOld Lead,old@example.com,OldCo,Manager\n",
    "crm/archive/sequence_v1.json": json.dumps({"version": 1, "steps": ["connect", "message", "followup"]}),
    "crm/templates_old/email_template.txt": "Hi {first_name},\n\nI hope this finds you well.\n\nBest,\nPatrick",
    "analytics/q1/reply_rates.csv": "month,sent,replied\nJan,120,18\nFeb,95,14\nMar,140,22\n",
    "analytics/q2/conversion_funnel.json": json.dumps({"step1": 200, "step2": 80, "step3": 40, "converted": 12}),
    "configs/deprecated/cron_v1.json": json.dumps({"schedule": "0 * * * *", "action": "send_batch"}),
    "configs/active/send_limits.yaml": "linkedin_connections_per_day: 50\nlinkedin_messages_per_day: 100\nemail_per_day: 100\n",
    "scripts/util/dedupe_leads.py": "# Deduplication utility\ndef dedupe(df):\n    return df.drop_duplicates(subset='Email')\n",
    "scripts/archive/old_mailer.py": "# Legacy mailer - DO NOT USE\nimport smtplib\n",
    "notes/campaign_ideas.txt": "- Try video outreach\n- Personalize by funding stage\n- A/B test subject lines\n",
    "data/raw/linkedin_scrape_2024.jsonl": json.dumps({"profile": "https://linkedin.com/in/jdoe", "connections": 500}) + "\n",
    "data/processed/enriched_leads_sample.csv": "Name,Email,Company,Title,LinkedIn\nJane Doe,jane@techco.com,TechCo,CTO,https://linkedin.com/in/janedoe\n",
}
for path, content in distractors.items():
    Path(f"{WORKSPACE}/{path}").write_text(content)

# ── DuckDB setup ───────────────────────────────────────────────────────────
db_path = f"{WORKSPACE}/crm/leads.db"
today = date.today()

con = duckdb.connect(db_path)

con.execute("""
CREATE TABLE leads (
    id INTEGER PRIMARY KEY,
    "Name" VARCHAR,
    "Email" VARCHAR,
    "Company" VARCHAR,
    "Title" VARCHAR,
    "LinkedIn" VARCHAR,
    "Outreach Status" VARCHAR DEFAULT 'Queued',
    "Sequence Step" INTEGER DEFAULT 0,
    "Last Outreach" DATE,
    "Next Outreach" DATE,
    "Outreach Channel" VARCHAR,
    "Reply Received" BOOLEAN DEFAULT false,
    "Thread ID" VARCHAR,
    "mutual" VARCHAR,
    "trigger" VARCHAR,
    "value_prop" VARCHAR,
    "pain_point" VARCHAR,
    "generated_message" VARCHAR,
    "message_channel" VARCHAR
)
""")

# ── Lead data ──────────────────────────────────────────────────────────────
# Seniority: C-suite (CTO, CEO, VP), IC (Senior Engineer, Staff Engineer, SWE)
leads = [
    # New leads (Queued, Step 0) — need initial outreach (Step 1)
    {
        "id": 1,
        "Name": "Marcus Webb",
        "Email": "marcus.webb@novalytics.io",
        "Company": "Novalytics",
        "Title": "CTO",
        "LinkedIn": "https://linkedin.com/in/marcuswebb",
        "Outreach Status": "Queued",
        "Sequence Step": 0,
        "Last Outreach": None,
        "Next Outreach": str(today),
        "Outreach Channel": "LinkedIn",
        "Reply Received": False,
        "Thread ID": None,
        "mutual": "YC S22 alumni network",
        "trigger": "announced $8M Series A last week",
        "value_prop": "engineering velocity tooling that cuts deploy time by 60%",
        "pain_point": "scaling engineering org post-funding",
    },
    {
        "id": 2,
        "Name": "Priya Sharma",
        "Email": "priya@novalytics.io",
        "Company": "Novalytics",  # SAME company as Marcus — messages must differ
        "Title": "Staff Engineer",
        "LinkedIn": "https://linkedin.com/in/priyasharma",
        "Outreach Status": "Queued",
        "Sequence Step": 0,
        "Last Outreach": None,
        "Next Outreach": str(today),
        "Outreach Channel": "LinkedIn",
        "Reply Received": False,
        "Thread ID": None,
        "mutual": "both attended PyCon 2023",
        "trigger": "published a blog post on distributed tracing",
        "value_prop": "observability tooling that integrates with your existing stack",
        "pain_point": "debugging latency spikes in microservices",
    },
    {
        "id": 3,
        "Name": "Derek Fontaine",
        "Email": "derek@stackpilot.com",
        "Company": "StackPilot",
        "Title": "VP Engineering",
        "LinkedIn": "https://linkedin.com/in/derekfontaine",
        "Outreach Status": "Queued",
        "Sequence Step": 0,
        "Last Outreach": None,
        "Next Outreach": str(today),
        "Outreach Channel": "Email",
        "Reply Received": False,
        "Thread ID": None,
        "mutual": "ex-Stripe colleagues",
        "trigger": "hiring 12 engineers this quarter per LinkedIn",
        "value_prop": "onboarding automation that cuts ramp time from 3 weeks to 5 days",
        "pain_point": "onboarding velocity at scale",
    },
    # Mid-sequence leads (Sent, overdue for follow-up)
    {
        "id": 4,
        "Name": "Sofia Reyes",
        "Email": "sofia.reyes@clarabit.com",
        "Company": "ClaraBit",
        "Title": "Senior Software Engineer",
        "LinkedIn": "https://linkedin.com/in/sofiareyes",
        "Outreach Status": "Sent",
        "Sequence Step": 1,
        "Last Outreach": str(today - timedelta(days=3)),
        "Next Outreach": str(today),  # Day 3 follow-up due today
        "Outreach Channel": "Email",
        "Reply Received": False,
        "Thread ID": "thread_abc123",
        "mutual": "Berkeley CS alumni",
        "trigger": "open-sourced a Rust caching library 2 weeks ago",
        "value_prop": "performance profiling that integrates with Rust toolchains",
        "pain_point": "production performance bottlenecks",
    },
    {
        "id": 5,
        "Name": "Nathaniel Cross",
        "Email": "ncross@meridianai.com",
        "Company": "MeridianAI",
        "Title": "CEO",
        "LinkedIn": "https://linkedin.com/in/nathanielcross",
        "Outreach Status": "Sent",
        "Sequence Step": 2,
        "Last Outreach": str(today - timedelta(days=7)),
        "Next Outreach": str(today),  # Day 7 value-add due today
        "Outreach Channel": "Email",
        "Reply Received": False,
        "Thread ID": "thread_def456",
        "mutual": "both spoke at SaaStr 2023",
        "trigger": "MeridianAI just hit 500 enterprise customers",
        "value_prop": "AI-powered churn prediction that saved similar companies 2M ARR",
        "pain_point": "retaining enterprise customers at scale",
    },
    {
        "id": 6,
        "Name": "Chen Liu",
        "Email": "chen.liu@cloudnine.dev",
        "Company": "CloudNine",
        "Title": "Senior DevOps Engineer",
        "LinkedIn": "https://linkedin.com/in/chenliu",
        "Outreach Status": "Sent",
        "Sequence Step": 3,
        "Last Outreach": str(today - timedelta(days=14)),
        "Next Outreach": str(today),  # Day 14 break-up due today
        "Outreach Channel": "Email",
        "Reply Received": False,
        "Thread ID": "thread_ghi789",
        "mutual": "AWS re:Invent 2023 attendee",
        "trigger": "CloudNine migrating from monolith to Kubernetes",
        "value_prop": "K8s cost optimization tooling, avg 35% infra savings",
        "pain_point": "Kubernetes cost management during migration",
    },
    # Lead NOT due (future Next Outreach) — should be EXCLUDED from today's batch
    {
        "id": 7,
        "Name": "Amara Osei",
        "Email": "amara@futuretech.io",
        "Company": "FutureTech",
        "Title": "CTO",
        "LinkedIn": "https://linkedin.com/in/amaraosei",
        "Outreach Status": "Sent",
        "Sequence Step": 1,
        "Last Outreach": str(today),
        "Next Outreach": str(today + timedelta(days=3)),  # Not due yet
        "Outreach Channel": "LinkedIn",
        "Reply Received": False,
        "Thread ID": None,
        "mutual": "MIT Media Lab alumni",
        "trigger": "recently promoted to CTO",
        "value_prop": "engineering metrics dashboard for new CTOs",
        "pain_point": "establishing engineering culture and metrics",
    },
    # Opted Out lead — must never be contacted
    {
        "id": 8,
        "Name": "Jake Thornton",
        "Email": "jake@thorntontech.com",
        "Company": "ThorntonTech",
        "Title": "VP Engineering",
        "LinkedIn": "https://linkedin.com/in/jakethornton",
        "Outreach Status": "Opted Out",
        "Sequence Step": 1,
        "Last Outreach": str(today - timedelta(days=5)),
        "Next Outreach": str(today),  # Would be due, but Opted Out
        "Outreach Channel": "Email",
        "Reply Received": True,
        "Thread ID": "thread_optout",
        "mutual": None,
        "trigger": None,
        "value_prop": None,
        "pain_point": None,
    },
]

for lead in leads:
    con.execute("""
        INSERT INTO leads VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
    """, [
        lead["id"],
        lead["Name"],
        lead["Email"],
        lead["Company"],
        lead["Title"],
        lead["LinkedIn"],
        lead["Outreach Status"],
        lead["Sequence Step"],
        lead["Last Outreach"],
        lead["Next Outreach"],
        lead["Outreach Channel"],
        lead["Reply Received"],
        lead["Thread ID"],
        lead["mutual"],
        lead["trigger"],
        lead["value_prop"],
        lead["pain_point"],
        None,  # generated_message
        None,  # message_channel
    ])

# Create view matching SKILL.md query pattern
con.execute("""
    CREATE VIEW v_leads AS SELECT * FROM leads
""")

con.close()

# ── Minimal campaign config ────────────────────────────────────────────────
campaign_config = {
    "campaign_name": "Q3 Engineering Leaders Outreach",
    "owner_email": "patrick@candlefish.ai",
    "template": "Template 2: Cold Email Sequence",
    "linkedin_template": "Template 1: LinkedIn Connection + Message",
    "run_date": str(today),
}
Path(f"{WORKSPACE}/configs/active/campaign_config.json").write_text(
    json.dumps(campaign_config, indent=2)
)

print(f"Workspace initialized at {WORKSPACE}")
print(f"DuckDB created at {db_path}")
print(f"Today: {today}")
print("Leads inserted:", len(leads))