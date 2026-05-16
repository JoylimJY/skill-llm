import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory skeleton (distractors) ──────────────────────────────────────────
dirs = [
    "projects/alpha/docs",
    "projects/alpha/meetings",
    "projects/beta/reports",
    "projects/beta/design",
    "projects/gamma/retrospectives",
    "admin/hr/onboarding",
    "admin/finance/q2",
    "tools/scripts",
    "tools/templates",
    "archive/2023/q4",
    "archive/2022/q3",
    "inbox",
    "src",          # will hold the memory module
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractor_files = {
    "projects/alpha/docs/scope.txt": "Project Alpha scope: ERP modernisation for client XYZ.\nBudget: $4.2M. Timeline: 18 months.",
    "projects/alpha/meetings/kickoff_notes.txt": "Attendees: Priya, Marcus, Lena.\nAction items: finalise data migration plan by Friday.",
    "projects/beta/reports/status_wk22.txt": "Beta on track. Risk: vendor delay on API delivery.",
    "projects/beta/design/architecture.md": "# Architecture\n\nMicroservices on K8s. Event-driven with Kafka.",
    "projects/gamma/retrospectives/retro_jun.txt": "What went well: daily standups. What didn't: unclear requirements upfront.",
    "admin/hr/onboarding/checklist.txt": "1. Badge access\n2. Laptop setup\n3. Introduce to team lead",
    "admin/finance/q2/budget_notes.txt": "Q2 variance: +8% due to travel expenses.",
    "tools/templates/report_template.docx.stub": "TEMPLATE STUB - replace with real DOCX",
    "tools/scripts/deploy.sh": "#!/bin/bash\necho 'Deploy not implemented'",
    "archive/2023/q4/lessons_raw.txt": "Don't underestimate integration complexity.\nAlways negotiate SLAs upfront.",
    "archive/2022/q3/client_summary.txt": "Client: MegaBank. Outcome: Successful. NPS: 72.",
    "inbox/misc_notes.txt": "Call back Sandra re: subcontractor rates.\nReview NDA for Omega deal.",
}
for rel, content in distractor_files.items():
    (WORKSPACE / rel).write_text(content)

# ── THE REAL PROBLEM FILES ─────────────────────────────────────────────────────

# 1. Raw team roster — messy, inconsistent formatting
team_roster_raw = """\
TEAM ROSTER — PROJECT CONSTELLATION
=====================================
Name: Dr. Amara Osei-Bonsu | Role: Lead Data Scientist | Dept: Analytics | Clearance: L3
Name:Marcus Delgado|Role:Senior Consultant|Dept: Strategy|Clearance:L2
Name : Priya Nair | Role : Project Manager | Dept : PMO | Clearance : L2
Name:LENA KRAWCZYK|Role:Solutions Architect|Dept:Technology|Clearance:L3
Name: Tom Ridgeway | Role: Junior Analyst | Dept: Analytics | Clearance: L1
Name:Fatima Al-Hassan | Role: Risk Officer | Dept : Compliance | Clearance: L3

CLIENT ENTITIES
=====================================
Name: NovaTech Industries | Type: client | Sector: Manufacturing | Contract: NOVA-2024-07 | Value: $7.8M
Name: Meridian Financial Group | Type: client | Sector: Banking | Contract: MFG-2024-03 | Value: $3.1M

PARTNER / VENDOR ENTITIES
=====================================
Name: CloudBridge Solutions | Type: vendor | Speciality: Cloud Migration | SLA: 99.5%
Name: DataSense Analytics | Type: vendor | Speciality: BI Tooling | SLA: 99.0%
"""
(WORKSPACE / "inbox" / "team_roster_raw.txt").write_text(team_roster_raw)

# 2. Incident / failure log — messy JSON-ish, some fields use wrong outcome words
incident_log_raw = """\
[INCIDENT LOG — CONSTELLATION PROJECT]
Exported: 2024-06-15

---INCIDENT 001---
action: Deployed ETL pipeline to production without staging validation
context: data_pipeline
outcome: FAILED
insight: Always run full regression in staging before production push; a 2-hour outage resulted.

---INCIDENT 002---
action: Negotiated extended timeline with NovaTech after scope creep identified
context: client_management
outcome: SUCCESS
insight: Early scope flagging and client transparency prevented contract dispute.

---INCIDENT 003---
action: Used automated schema migration script on live database
context: data_pipeline
outcome: FAILED
insight: Schema migrations must be dry-run first; rollback capability is non-negotiable.

---INCIDENT 004---
action: Introduced weekly risk review cadence mid-project
context: project_management
outcome: SUCCESS
insight: Proactive risk reviews surfaced vendor delay 3 weeks early, allowing mitigation.

---INCIDENT 005---
action: Skipped stakeholder sign-off on revised architecture diagram
context: client_management
outcome: FAILED
insight: All architecture changes require written stakeholder approval regardless of urgency.

---INCIDENT 006---
action: Ran parallel processing across 8 nodes for batch analytics job
context: data_pipeline
outcome: SUCCESS
insight: Parallelisation reduced overnight batch from 6h to 45min; document configs for reuse.
"""
(WORKSPACE / "inbox" / "incident_log_raw.txt").write_text(incident_log_raw)

# 3. The src/memory.py module — the actual AgentMemory implementation
# This simulates the "clawdhub install agent-memory" result
memory_module = '''\
"""
AgentMemory — Persistent memory system for AI agents.
Installed via: clawdhub install agent-memory
"""

import sqlite3
import json
import time
from pathlib import Path
from typing import Optional


class AgentMemory:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            default_dir = Path.home() / ".agent-memory"
            default_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(default_dir / "memory.db")
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    tags TEXT,
                    ts REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    context TEXT NOT NULL,
                    outcome TEXT NOT NULL CHECK(outcome IN (\'positive\', \'negative\')),
                    insight TEXT NOT NULL,
                    ts REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    attributes TEXT,
                    ts REAL
                )
            """)
            conn.commit()

    def remember(self, content: str, tags: list = None):
        tags_str = json.dumps(tags or [])
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO facts (content, tags, ts) VALUES (?, ?, ?)",
                (content, tags_str, time.time())
            )
            conn.commit()

    def learn(self, action: str, context: str, outcome: str, insight: str):
        if outcome not in ("positive", "negative"):
            raise ValueError(f"outcome must be \'positive\' or \'negative\', got: {outcome!r}")
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO lessons (action, context, outcome, insight, ts) VALUES (?, ?, ?, ?, ?)",
                (action, context, outcome, insight, time.time())
            )
            conn.commit()

    def recall(self, query: str, limit: int = 10) -> list:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT content, tags FROM facts WHERE content LIKE ? ORDER BY ts DESC LIMIT ?",
                (f"%{query}%", limit)
            ).fetchall()
        return [{"content": r[0], "tags": json.loads(r[1])} for r in rows]

    def get_lessons(self, context: Optional[str] = None, limit: int = 20) -> list:
        with self._conn() as conn:
            if context:
                rows = conn.execute(
                    "SELECT action, context, outcome, insight FROM lessons WHERE context = ? ORDER BY ts DESC LIMIT ?",
                    (context, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT action, context, outcome, insight FROM lessons ORDER BY ts DESC LIMIT ?",
                    (limit,)
                ).fetchall()
        return [{"action": r[0], "context": r[1], "outcome": r[2], "insight": r[3]} for r in rows]

    def track_entity(self, name: str, entity_type: str, attributes: dict = None):
        attrs_str = json.dumps(attributes or {})
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO entities (name, entity_type, attributes, ts) VALUES (?, ?, ?, ?)",
                (name, entity_type, attrs_str, time.time())
            )
            conn.commit()

    def get_entities(self, entity_type: Optional[str] = None) -> list:
        with self._conn() as conn:
            if entity_type:
                rows = conn.execute(
                    "SELECT name, entity_type, attributes FROM entities WHERE entity_type = ? ORDER BY ts DESC",
                    (entity_type,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT name, entity_type, attributes FROM entities ORDER BY ts DESC"
                ).fetchall()
        return [{"name": r[0], "type": r[1], "attributes": json.loads(r[2])} for r in rows]
'''
(WORKSPACE / "src" / "memory.py").write_text(memory_module)

# ── AGENTS.md (hints at integration protocol, not the solution) ───────────────
agents_md = """\
# AGENTS.md — Project Constellation Intelligence System

## Purpose
Provide incoming project leads with an instantly accessible knowledge base
capturing team composition, client context, and lessons from past incidents.

## Knowledge Retention Tooling
The memory tooling is installed under `src/`. Consult the skill documentation
to understand how to use it correctly.

## Required Deliverable
Run a population script that:
1. Ingests `inbox/team_roster_raw.txt` and registers all persons and organisations.
2. Ingests `inbox/incident_log_raw.txt` and records every incident as a lesson.
3. Writes the populated database to `projects/constellation/memory.db`.
4. Produces `projects/constellation/onboarding_report.json` summarising what was stored.

## Report Schema (onboarding_report.json)
{
  "entities_loaded": <int>,
  "lessons_loaded": <int>,
  "pipeline_lessons": [ ... get_lessons for context data_pipeline ... ],
  "client_mgmt_lessons": [ ... get_lessons for context client_management ... ]
}
"""
(WORKSPACE / "AGENTS.md").write_text(agents_md)

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")