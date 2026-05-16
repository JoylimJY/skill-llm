import os
import random
import json
import sqlite3
from pathlib import Path

random.seed(42)

# ── Base workspace layout ──────────────────────────────────────────────────────
WORKSPACE = Path("/workspace")

# Replicate the GTM system directory structure described in SKILL.md
gtm_root = WORKSPACE / "gtm-system"
(gtm_root / "scripts").mkdir(parents=True, exist_ok=True)
(gtm_root / "data").mkdir(parents=True, exist_ok=True)
(gtm_root / "config").mkdir(parents=True, exist_ok=True)
(gtm_root / "logs").mkdir(parents=True, exist_ok=True)
(gtm_root / "reports" / "weekly").mkdir(parents=True, exist_ok=True)
(gtm_root / "reports" / "monthly").mkdir(parents=True, exist_ok=True)
(gtm_root / "crawlers" / "cache").mkdir(parents=True, exist_ok=True)

# ── Distractor files (≥10) ─────────────────────────────────────────────────────
distractors = [
    (gtm_root / "config" / "crawler_settings.json", json.dumps({
        "hn_min_score": 10,
        "reddit_subreddits": ["dataengineering", "devops"],
        "github_topics": ["bacalhau", "distributed-compute"],
        "crawl_interval_hours": 6
    }, indent=2)),
    (gtm_root / "config" / "keywords_seed.txt",
     "bacalhau\nexpanso\ndistributed-jobs\nwasm-compute\ndata-gravity\n"),
    (gtm_root / "logs" / "crawler_2024_01_10.log",
     "[INFO] HN crawl complete: 3 signals\n[INFO] Reddit crawl complete: 1 signal\n"),
    (gtm_root / "logs" / "crawler_2024_01_11.log",
     "[INFO] GitHub crawl complete: 2 signals\n[WARN] Rate limit approaching\n"),
    (gtm_root / "reports" / "weekly" / "week_02_2024.md",
     "# Weekly GTM Report\n## Pipeline Summary\n- 2 opps in evaluation\n- 1 opp in negotiation\n"),
    (gtm_root / "reports" / "monthly" / "jan_2024.json", json.dumps({
        "total_opps": 5, "closed_won": 1, "closed_lost": 0, "avg_cycle_days": 23
    }, indent=2)),
    (gtm_root / "crawlers" / "cache" / "hn_last_run.json", json.dumps({
        "last_fetch": "2024-01-11T08:00:00Z", "items_fetched": 42
    }, indent=2)),
    (gtm_root / "crawlers" / "cache" / "reddit_last_run.json", json.dumps({
        "last_fetch": "2024-01-11T09:30:00Z", "posts_fetched": 15
    }, indent=2)),
    (gtm_root / "config" / "stage_definitions.txt",
     "Stages: awareness, interest, evaluation, negotiation, closed_won, closed_lost\n"),
    (gtm_root / "reports" / "weekly" / "template.md",
     "# Weekly GTM Report - {{WEEK}}\n## New Contacts: {{NEW_CONTACTS}}\n## Pipeline Moves: {{MOVES}}\n"),
    (gtm_root / "data" / "archive_2023.sql",
     "-- Archived GTM data for 2023\n-- 47 contacts, 12 opportunities\n"),
    (gtm_root / "scripts" / "utils.py",
     "# Utility helpers for GTM scripts\ndef fmt_date(d): return d.strftime('%Y-%m-%d')\n"),
]

for path, content in distractors:
    path.write_text(content)

# ── SQLite database initialization ────────────────────────────────────────────
# Create the database with the schema that gtm.py expects so the CLI works
db_path = gtm_root / "data" / "gtm.db"
conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT,
    company TEXT,
    role TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS opportunities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    contact_id INTEGER,
    description TEXT,
    stage TEXT DEFAULT 'awareness',
    priority INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id)
);

CREATE TABLE IF NOT EXISTS interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    opportunity_id INTEGER,
    description TEXT,
    due_date TEXT,
    completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (opportunity_id) REFERENCES opportunities(id)
);

CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT,
    title TEXT,
    url TEXT,
    content TEXT,
    score REAL DEFAULT 0,
    processed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL UNIQUE,
    category TEXT DEFAULT 'general',
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")

# Seed some existing data so the agent is operating in a non-empty system
cur.execute("INSERT INTO contacts (name, email, company, role) VALUES (?, ?, ?, ?)",
            ("Alice Chen", "alice@oldcorp.io", "OldCorp", "VP Engineering"))
cur.execute("INSERT INTO opportunities (company, contact_id, description, stage, priority) VALUES (?, ?, ?, ?, ?)",
            ("OldCorp", 1, "Legacy evaluation from Q4", "interest", 2))
cur.execute("INSERT INTO keywords (keyword, category, weight) VALUES (?, ?, ?)",
            ("bacalhau", "domain", 2.0))
cur.execute("INSERT INTO signals (source, title, url, content, score, processed) VALUES (?, ?, ?, ?, ?, ?)",
            ("hn", "Ask HN: Best tools for distributed batch jobs?", "https://news.ycombinator.com/item?id=99991",
             "We've been evaluating Bacalhau and Ray for our pipeline...", 45.0, 0))
cur.execute("INSERT INTO signals (source, title, url, content, score, processed) VALUES (?, ?, ?, ?, ?, ?)",
            ("github", "expanso/bacalhau: New star from enterprise user", "https://github.com/expanso/bacalhau",
             "Enterprise repo activity detected", 30.0, 0))

conn.commit()
conn.close()

# ── Task brief for the agent (the only "documentation" it gets) ───────────────
brief = (WORKSPACE / "task_brief.txt")
brief.write_text(
    "TASK BRIEF\n"
    "==========\n"
    "Please handle the following sales operations tasks using the GTM system.\n"
    "The GTM system CLI is located at: /workspace/gtm-system/scripts/gtm.py\n\n"
    "See task details in task_instructions.md\n"
)

print("Workspace generation complete.")
print(f"GTM database: {db_path}")
print(f"Distractor files: {len(distractors)}")