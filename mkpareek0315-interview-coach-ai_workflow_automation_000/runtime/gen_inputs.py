import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Distractor directory structure ---
dirs = [
    workspace / "notes" / "general",
    workspace / "notes" / "companies",
    workspace / "resources" / "templates",
    workspace / "resources" / "checklists",
    workspace / "drafts" / "emails",
    workspace / "drafts" / "answers",
    workspace / "logs" / "sessions",
    workspace / "logs" / "errors",
    workspace / "config",
    workspace / "exports",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files (realistic but irrelevant)
distractor_files = [
    (workspace / "notes" / "general" / "interview_goals.txt",
     "Goal: Land a data engineering role at a top tech company by Q3.\nFocus: SQL, Spark, Python pipelines."),

    (workspace / "notes" / "companies" / "target_companies.txt",
     "1. Stripe\n2. Databricks\n3. Snowflake\n4. Airbnb\n5. LinkedIn"),

    (workspace / "resources" / "templates" / "cover_letter_template.txt",
     "Dear Hiring Manager,\n\nI am writing to express my interest in the [ROLE] position at [COMPANY]...\n\nBest,\n[NAME]"),

    (workspace / "resources" / "templates" / "resume_outline.txt",
     "Summary\nExperience\nSkills\nEducation\nProjects"),

    (workspace / "resources" / "checklists" / "pre_interview.txt",
     "- Research company\n- Review JD\n- Prepare STAR stories\n- Set alarm"),

    (workspace / "drafts" / "emails" / "followup_draft.txt",
     "Hi Sarah,\nThank you for the interview yesterday. I really enjoyed learning about the data platform team...\n\n[INCOMPLETE DRAFT]"),

    (workspace / "drafts" / "answers" / "tell_me_about_yourself_v1.txt",
     "I'm a software engineer with 5 years of experience building data pipelines. I've worked primarily in fintech and am now looking to specialize in data engineering..."),

    (workspace / "drafts" / "answers" / "weakness_answer_draft.txt",
     "I sometimes take on too much work at once. I've been working on better delegation by..."),

    (workspace / "logs" / "sessions" / "session_notes.txt",
     "Session 1: Felt nervous. Answers were too vague.\nSession 2: Better STAR structure. Need to quantify results more."),

    (workspace / "logs" / "errors" / "app_errors.txt",
     "[2024-01-15 09:22:11] Profile load error: file not found, creating new.\n[2024-01-16 14:05:33] History parse warning: empty array."),

    (workspace / "config" / "app_settings.txt",
     "theme=dark\nlanguage=en\nnotifications=off"),

    (workspace / "exports" / "score_export_old.txt",
     "DEPRECATED FORMAT - DO NOT USE\n2024-01-10: Score 5.8/10\n2024-01-11: Score 6.1/10"),
]

for path, content in distractor_files:
    path.write_text(content)

# --- The "messy" seed data the agent must work with ---
# This is a rough notes file describing what happened in 2 sessions
# The agent must translate this into the proper skill data format

briefing_content = """COACHING SESSION SUMMARY — For Data File Setup
================================================

CANDIDATE: Jordan Rivera
TARGET ROLE: Data Engineer
TARGET COMPANY: Databricks
EXPERIENCE: 5 years
INDUSTRY: Fintech
SKILLS: Python, SQL, Spark, Kafka, Airflow
PAST ROLES: Software Engineer at PayPal, Junior Dev at a startup

SESSION 1 — Mock Interview (Behavioral + Technical + HR)
---------------------------------------------------------
Date: 2024-03-01
Behavioral Round: 70/100
Technical Round: 62/100
HR/Culture Round: 68/100
Overall: 67/100
Questions answered this session: 13

STAR breakdown for one answer in Session 1 (Process improvement question):
  Situation: 7/10
  Task: 5/10
  Action: 8/10
  Result: 4/10   <-- WEAK (below 6)
  Overall STAR score: 6/10

SESSION 2 — Mock Interview (Behavioral + Technical + HR)
---------------------------------------------------------
Date: 2024-03-05
Behavioral Round: 78/100
Technical Round: 74/100
HR/Culture Round: 76/100
Overall: 76/100
Questions answered this session: 13

STAR breakdown for one answer in Session 2 (Leadership question):
  Situation: 8/10
  Task: 7/10
  Action: 9/10
  Result: 5/10   <-- WEAK (below 6)
  Overall STAR score: 7/10

SAVED ANSWER (to be bookmarked):
---------------------------------
Question category: "Tell me about yourself"
Score: 9/10
Answer text: "I'm a data engineer with 5 years of experience building large-scale data pipelines in fintech. At PayPal, I led a migration from a monolithic ETL system to Apache Spark, cutting processing time by 65% for 50M+ daily transactions. I'm drawn to Databricks because of its focus on the Lakehouse architecture, which aligns directly with the distributed systems work I've been doing. I'm excited to bring my pipeline optimization experience to help the platform team scale further."

WEAK AREAS IDENTIFIED:
-----------------------
- Quantifying results in STAR answers (Result scores of 4 and 5, both below 6)
"""

(workspace / "session_briefing.txt").write_text(briefing_content)

print("Workspace initialized with distractor files and session briefing.")
print(f"Files created: {len(distractor_files) + 1}")