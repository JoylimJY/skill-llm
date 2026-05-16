#!/usr/bin/env python3
"""
Build the initial sandbox workspace for the algernon-review FSRS task.
"""
import os
import json
import sqlite3
import random
from datetime import datetime, date, timedelta
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
ALGERNON_HOME = WORKSPACE / "algernon_home"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    ALGERNON_HOME / "data",
    ALGERNON_HOME / "memory" / "conversations",
    ALGERNON_HOME / "memory" / "context",
    ALGERNON_HOME / "config",
    ALGERNON_HOME / "logs",
    ALGERNON_HOME / "exports",
    ALGERNON_HOME / "templates",
    WORKSPACE / "scripts",
    WORKSPACE / "docs" / "scheduling",
    WORKSPACE / "docs" / "schema",
    WORKSPACE / "backups",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    ALGERNON_HOME / "config" / "settings.yaml": """\
theme: dark
language: en
notifications: true
sync_interval: 300
""",
    ALGERNON_HOME / "config" / "prompts.yaml": """\
review_greeting: "Time to review!"
summary_template: "You reviewed {n} cards today."
""",
    ALGERNON_HOME / "logs" / "app.log": """\
2025-01-10 09:00:01 INFO  Application started
2025-01-10 09:00:02 INFO  Database connection established
2025-01-10 09:15:33 INFO  Review session initiated by user
2025-01-10 09:22:11 INFO  Session completed: 12 cards
""",
    ALGERNON_HOME / "exports" / "export_2025-01-10.csv": """\
card_id,front,back,stability,reps
1,Q: Mechanism of beta-blockers?,A: Block beta-1 receptors,4.0,3
2,Q: Loop diuretics?,A: Block Na/K/2Cl transporter,0.3,2
""",
    ALGERNON_HOME / "templates" / "card_template.md": """\
# Card Template

## Flashcard
front: <question>
back: <answer>

## Dissertative
front: <open-ended question>
back: <reference answer>
""",
    ALGERNON_HOME / "memory" / "context" / "study_goals.md": """\
# Study Goals
- Master pharmacology for Step 1
- Complete cardiology deck by end of month
""",
    WORKSPACE / "docs" / "scheduling" / "sm2_notes.md": """\
# SM-2 Algorithm Notes (DEPRECATED)
These notes describe the old SM-2 algorithm.
Do NOT use these formulas for the current system.
EF' = EF + (0.1 - (5-q)*(0.08 + (5-q)*0.02))
""",
    WORKSPACE / "docs" / "scheduling" / "overview.md": """\
# Scheduling Overview
The system uses a modern spaced repetition algorithm.
Refer to the skill documentation for exact parameters.
""",
    WORKSPACE / "docs" / "schema" / "tables.md": """\
# Database Schema Reference
See study.db for live schema.
""",
    WORKSPACE / "scripts" / "migrate.sh": """\
#!/bin/bash
# Migration script - do not run manually
echo "Migration complete"
""",
    WORKSPACE / "backups" / "study_backup_2025-01-09.db.bak": b"\x53\x51\x4c\x69\x74\x65\x20\x66\x6f\x72\x6d\x61\x74\x20\x33",
}

for path, content in distractor_files.items():
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content)

# ── Build study.db ────────────────────────────────────────────────────────────
DB_PATH = ALGERNON_HOME / "data" / "study.db"
conn = sqlite3.connect(str(DB_PATH))
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS materials (
    id INTEGER PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS decks (
    id INTEGER PRIMARY KEY,
    material_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (material_id) REFERENCES materials(id)
);

CREATE TABLE IF NOT EXISTS cards (
    id INTEGER PRIMARY KEY,
    deck_id INTEGER NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('flashcard','dissertative','argumentative')),
    front TEXT NOT NULL,
    back TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    source_title TEXT,
    created_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (deck_id) REFERENCES decks(id)
);

CREATE TABLE IF NOT EXISTS card_state (
    id INTEGER PRIMARY KEY,
    card_id INTEGER UNIQUE NOT NULL,
    stability REAL NOT NULL DEFAULT 0.0,
    difficulty REAL NOT NULL DEFAULT 0.0,
    reps INTEGER NOT NULL DEFAULT 0,
    lapses INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL DEFAULT 'new' CHECK(state IN ('new','learning','review','relearning')),
    due_date TEXT NOT NULL,
    last_review DATETIME,
    FOREIGN KEY (card_id) REFERENCES cards(id)
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY,
    card_id INTEGER NOT NULL,
    grade INTEGER NOT NULL,
    scheduled_days INTEGER,
    elapsed_days REAL,
    reviewed_at DATETIME DEFAULT (datetime('now')),
    FOREIGN KEY (card_id) REFERENCES cards(id)
);
""")

# Materials & Decks
cur.execute("INSERT INTO materials (id, slug, title) VALUES (1, 'cardiology-step1', 'Cardiology USMLE Step 1')")
cur.execute("INSERT INTO materials (id, slug, title) VALUES (2, 'pharmacology-step1', 'Pharmacology USMLE Step 1')")
cur.execute("INSERT INTO decks (id, material_id, name) VALUES (1, 1, 'Heart Failure')")
cur.execute("INSERT INTO decks (id, material_id, name) VALUES (2, 2, 'Antihypertensives')")

today = date.today().isoformat()
nine_days_ago = (date.today() - timedelta(days=9)).isoformat()
five_days_ago = (date.today() - timedelta(days=5)).isoformat()
one_day_ago = (date.today() - timedelta(days=1)).isoformat()

# ── Cards ─────────────────────────────────────────────────────────────────────
# Card 1: flashcard, state=review, stability=4.0, difficulty=0.35, reps=3, lapses=0
#   last_review = 5 days ago, due today
#   Grade=3 (Good) → review+Good FSRS path
cur.execute("""INSERT INTO cards (id, deck_id, type, front, back, tags, source_title)
               VALUES (1, 1, 'flashcard',
                       'What is the Frank-Starling mechanism?',
                       'The Frank-Starling mechanism states that increased ventricular end-diastolic volume leads to increased stroke volume due to greater sarcomere stretch and actin-myosin overlap.',
                       '["[N1]"]',
                       'Cardiology Essentials Ch.3')""")
cur.execute("""INSERT INTO card_state (card_id, stability, difficulty, reps, lapses, state, due_date, last_review)
               VALUES (1, 4.0, 0.35, 3, 0, 'review', ?, ?)""", (today, five_days_ago))

# Card 2: dissertative, state=new, stability=0.0, difficulty=0.0, reps=0, lapses=0
#   due today, Grade=1 (Again), MISCONCEPTION detected
cur.execute("""INSERT INTO cards (id, deck_id, type, front, back, tags, source_title)
               VALUES (2, 2, 'dissertative',
                       'Explain the mechanism of action of beta-blockers in the treatment of heart failure. Include the physiological rationale.',
                       'Beta-blockers antagonize beta-1 adrenergic receptors in the heart, reducing catecholamine-driven cardiac remodeling, heart rate, and myocardial oxygen demand. Paradoxically, though they acutely reduce contractility, chronic use improves EF by reversing maladaptive remodeling. Key drugs: carvedilol, metoprolol succinate, bisoprolol.',
                       '["[N1]"]',
                       'Pharmacology Review 2024')""")
cur.execute("""INSERT INTO card_state (card_id, stability, difficulty, reps, lapses, state, due_date, last_review)
               VALUES (2, 0.0, 0.0, 0, 0, 'new', ?, NULL)""", (today,))

# Card 3: flashcard, state=learning, stability=0.3, difficulty=0.35, reps=2, lapses=0
#   last_review=1 day ago, due today
#   Grade=3 (Good) → learning+Good FSRS path
cur.execute("""INSERT INTO cards (id, deck_id, type, front, back, tags, source_title)
               VALUES (3, 1, 'flashcard',
                       'Name the four cardinal signs of loop diuretic toxicity.',
                       'Ototoxicity, hypokalemia, metabolic alkalosis, hypovolemia.',
                       '["[N1]"]',
                       'Pharmacology Review 2024')""")
cur.execute("""INSERT INTO card_state (card_id, stability, difficulty, reps, lapses, state, due_date, last_review)
               VALUES (3, 0.3, 0.35, 2, 0, 'learning', ?, ?)""", (today, one_day_ago))

# Card 4: flashcard, state=review, stability=10.0, difficulty=0.20, reps=5, lapses=1
#   last_review=9 days ago, due today, tag=[N1] → promotion candidate
#   Grade=3 (Good) → review+Good FSRS path + promotion to N2
cur.execute("""INSERT INTO cards (id, deck_id, type, front, back, tags, source_title)
               VALUES (4, 2, 'flashcard',
                       'What is the first-line treatment for hypertensive emergency with acute pulmonary edema?',
                       'IV nitroprusside or nitroglycerin combined with a loop diuretic (furosemide). Nitroprusside reduces both preload and afterload via NO-mediated vasodilation.',
                       '["[N1]"]',
                       'Cardiology Essentials Ch.7')""")
cur.execute("""INSERT INTO card_state (card_id, stability, difficulty, reps, lapses, state, due_date, last_review)
               VALUES (4, 10.0, 0.20, 5, 1, 'review', ?, ?)""", (today, nine_days_ago))

# ── Pre-seed review history for Card 4's deck (deck_id=2) over last 7 days ────
# 6 Good reviews → retention = 1.0 >= 0.9 → promotion triggers
# These are for OTHER cards in the same deck, or for card 4 itself (historical).
# We need: SELECT ... WHERE c.deck_id = 2 AND r.reviewed_at >= datetime('now', '-7 days')
# Insert dummy reviews associated with cards in deck 2 (card 2 and card 4).
# Add a dummy card 5 in deck 2 for extra history
cur.execute("""INSERT INTO cards (id, deck_id, type, front, back, tags)
               VALUES (5, 2, 'flashcard',
                       'What is the mechanism of hydralazine?',
                       'Direct arterial vasodilator; mechanism unclear but involves opening K+ channels and increased NO synthesis.',
                       '["[N1]"]')""")
cur.execute("""INSERT INTO card_state (card_id, stability, difficulty, reps, lapses, state, due_date, last_review)
               VALUES (5, 6.0, 0.25, 4, 0, 'review', ?, ?)""",
               ((date.today() + timedelta(days=5)).isoformat(),
                (date.today() - timedelta(days=3)).isoformat()))

# Insert 6 Good reviews for deck 2 cards in last 7 days
for i in range(6):
    days_ago = random.randint(1, 6)
    reviewed_at = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
    card_in_deck2 = random.choice([2, 4, 5])
    cur.execute("""INSERT INTO reviews (card_id, grade, scheduled_days, elapsed_days, reviewed_at)
                   VALUES (?, 3, ?, ?, ?)""",
                   (card_in_deck2, random.randint(3,10), float(random.randint(3,10)), reviewed_at))

conn.commit()
conn.close()

# ── review_results.json ───────────────────────────────────────────────────────
review_results = {
    "session_date": today,
    "results": [
        {
            "card_id": 1,
            "grade": 3,
            "user_answer": None
        },
        {
            "card_id": 2,
            "grade": 1,
            "user_answer": "Beta-blockers work by blocking beta receptors. They slow the heart rate. They are used in heart failure to reduce workload. I think they work mainly by reducing blood pressure which relieves the heart.",
            "misconception": True,
            "misconception_question": "Do beta-blockers primarily treat heart failure by reducing blood pressure?",
            "correct_explanation": "No. Beta-blockers treat heart failure primarily by blocking catecholamine-driven maladaptive cardiac remodeling via beta-1 receptor antagonism, not through blood pressure reduction. Chronic use reverses ventricular remodeling and improves ejection fraction."
        },
        {
            "card_id": 3,
            "grade": 3,
            "user_answer": None
        },
        {
            "card_id": 4,
            "grade": 3,
            "user_answer": None
        }
    ]
}

review_results_path = WORKSPACE / "review_results.json"
review_results_path.write_text(json.dumps(review_results, indent=2))

# ── Write an env file the agent can source ────────────────────────────────────
env_file = WORKSPACE / "algernon_env.sh"
env_file.write_text(f"""\
export ALGERNON_HOME="{ALGERNON_HOME}"
export DB="{ALGERNON_HOME}/data/study.db"
""")

print("Workspace initialized successfully.")
print(f"  DB: {DB_PATH}")
print(f"  Review results: {review_results_path}")
print(f"  ALGERNON_HOME: {ALGERNON_HOME}")