import os
import random
from pathlib import Path
from datetime import date

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ── Directory scaffold ────────────────────────────────────────────────────────
dirs = [
    "memory/experience-bank/entries",
    "memory/experience-bank/index",
    "playbooks/archived",
    "skills/active",
    "skills/drafts",
    "references",
    "projects/analytics-cluster/docs",
    "projects/analytics-cluster/scripts",
    "projects/analytics-cluster/logs",
    "projects/infra/terraform",
    "projects/infra/ansible",
    "scratch",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "projects/analytics-cluster/docs/architecture.md": "# Analytics Cluster Architecture\n\nPostgres 15 primary + 2 replicas. Analytics reads routed to replicas.\n",
    "projects/analytics-cluster/scripts/deploy.sh": "#!/bin/bash\necho 'Deploying analytics cluster...'\nkubectl apply -f k8s/\n",
    "projects/analytics-cluster/logs/deploy-2024-11-01.log": "[2024-11-01 09:12] Deployment started\n[2024-11-01 09:14] All pods healthy\n",
    "projects/infra/terraform/main.tf": 'provider "aws" {\n  region = "us-east-1"\n}\n',
    "projects/infra/ansible/inventory.ini": "[analytics]\ndb01 ansible_host=10.0.1.10\ndb02 ansible_host=10.0.1.11\n",
    "skills/active/postgres-tuning.md": "# Skill: postgres-tuning\nAdjust work_mem and checkpoint settings for OLAP workloads.\n",
    "skills/drafts/k8s-rolling-deploy.md": "# Draft: k8s-rolling-deploy\nNot yet validated.\n",
    "playbooks/archived/old-backup-v1.md": "# OLD Backup Playbook (v1 — deprecated)\nUsed pg_dump without compression. Do not use.\n",
    "scratch/notes.txt": "random scratch notes from earlier session\npg_dump worked, pg_basebackup did not for logical\n",
    "memory/experience-bank/index/README.md": "# Experience Bank Index\nEntries are stored in entries/ as markdown files.\n",
}
for path, content in distractors.items():
    (WORKSPACE / path).write_text(content)

# ── Core references the agent MUST read ──────────────────────────────────────

decision_rules = """\
# OpenClaw Knowledge Routing — Decision Rules
version: 2.1

## Layer Definitions

### daily-log  (`memory/YYYY-MM-DD.md`)
Store here when:
- The information is DATE-SPECIFIC (tied to a particular day's work, incident, or result)
- It is raw evidence, observations, or a timestamped outcome
- It would NOT be useful lifted out of its date context
- Rule: ANY artifact that is primarily an event record → daily-log FIRST, regardless of other layers

### experience  (`memory/experience-bank/entries/`)
Store here when:
- A concrete TRIGGER → ACTION pattern was discovered (i.e., "when X happens, do Y")
- The lesson is REUSABLE across future tasks but NOT a full workflow
- It captures a non-obvious failure mode or gotcha
- Naming convention: `<slug>.md` where slug is lowercase-hyphenated summary of the trigger
- Required fields in entry: `trigger:`, `action:`, `failure_mode:`, `tags:`

### playbook  (`playbooks/`)
Store here when:
- The task is a CANONICAL MULTI-STEP WORKFLOW that will be repeated verbatim
- It has a clear start-state, ordered steps, and a done-condition
- It is project-specific OR cross-project but NOT yet a reusable package
- Required fields: `# Playbook: <Name>`, `## Prerequisites`, `## Steps`, `## Done-condition`

### skill  (`skills/`)
Store here when:
- The capability is REUSABLE AS A PACKAGE across multiple unrelated projects
- It has its own configuration surface (flags, parameters)
- It would be invoked by name from other agents or automations
- DO NOT create a skill just because something worked; require cross-project reuse evidence

## Routing Priority
1. If the task produced a dated, one-time event record → daily-log (mandatory)
2. If the task revealed a reusable trigger-action lesson → experience
3. If the task produced a canonical repeatable workflow → playbook
4. If the capability is cross-project reusable with its own config surface → skill
5. If NONE of the above apply, or the information is too noisy/trivial → no-op

## Multi-layer rule
A single completed task MAY produce artifacts in multiple layers.
Order of writes: daily-log → experience → playbook → skill.

## Anti-patterns (NEVER do these)
- Do NOT write raw command output as long-term knowledge
- Do NOT create a skill entry unless cross-project reuse is justified
- Do NOT skip daily-log when a dated event occurred
- Do NOT put playbook content inside memory/
- Do NOT put experience entries inside playbooks/
"""

template = """\
# OpenClaw Lightweight Invocation Template

## Experience Entry Template
```markdown
---
trigger: <one-line description of when this applies>
action: <what to do>
failure_mode: <what goes wrong if you don't>
tags: [<tag1>, <tag2>]
---

## Context
<1-3 sentences of background>

## Lesson
<The core reusable insight>
```

## Playbook Template
```markdown
# Playbook: <Name>

## Prerequisites
- <item>

## Steps
1. <step>
2. <step>

## Done-condition
<How you know it succeeded>
```

## Daily Log Template
```markdown
# <YYYY-MM-DD>

## Summary
<What happened today>

## Evidence / Artifacts
- <item>

## Follow-ups
- <item>
```
"""

examples = """\
# OpenClaw Examples

## Example 1 — Database incident (multi-layer)
**Scenario:** Postgres replica fell behind by 8 hours due to vacuum misconfiguration.

daily-log → `memory/2024-10-15.md`
  - Record: replica lag detected at 14:30, root cause identified (autovacuum disabled on replica), fix applied

experience → `memory/experience-bank/entries/postgres-replica-lag-autovacuum.md`
  - trigger: replica lag spikes unexpectedly
  - action: check autovacuum enabled on replica first
  - failure_mode: hours of lag investigation if autovacuum check skipped

NO playbook (fix was one-off, not a canonical workflow)
NO skill (single-project concern)

---

## Example 2 — New deployment workflow (playbook)
**Scenario:** Team standardized a blue-green deploy for all services.

NO daily-log (not a dated one-time event, it's a canonical workflow)
NO experience (the full workflow needs all steps preserved together)

playbook → `playbooks/blue-green-deploy.md`
  - Prerequisites, ordered steps, done-condition

NO skill (still project-specific)

---

## Example 3 — One-time data migration
**Scenario:** Migrated 50GB of customer records from MySQL to Postgres today.

daily-log → `memory/2024-11-05.md`
  - Record: migration ran 09:00–11:30, 50GB transferred, 0 errors

experience → `memory/experience-bank/entries/mysql-to-postgres-charset-gotcha.md`
  - trigger: migrating MySQL tables with latin1 charset to Postgres
  - action: run iconv pre-conversion step before pg_restore
  - failure_mode: silent data corruption on special characters

NO playbook (one-time migration, not canonical)
NO skill (no cross-project config surface)
"""

(WORKSPACE / "references/decision-rules.md").write_text(decision_rules)
(WORKSPACE / "references/template.md").write_text(template)
(WORKSPACE / "references/examples.md").write_text(examples)

# ── The scenario briefing for the agent ──────────────────────────────────────
scenario = """\
# Completed Task Briefing: Nightly DB Backup Automation

## Date completed: 2024-12-03

## What we did
We set up a fully automated nightly backup system for the analytics Postgres cluster.
The work took place on 2024-12-03 and involved:

1. Wrote `/opt/backup/pg_backup.sh` using `pg_dump -Fc --compress=9 -h localhost -U backup_user analytics_db`
   and tested it successfully at 22:00.
2. Registered the script as a cron job: `0 22 * * * /opt/backup/pg_backup.sh >> /var/log/pg_backup.log 2>&1`
3. Discovered a critical gotcha: pg_dump with `-Fc` format requires `pg_restore` (NOT `psql`) for restore.
   We initially tried `psql < backup.dump` and it failed with a binary format error.
4. Implemented a 7-day retention rotation using `find /backups -mtime +7 -delete`.
5. Confirmed first backup ran at 22:00:03, size 2.1 GB, duration 4m 12s.
6. This backup workflow will be reused verbatim for 2 other clusters (reporting-db and warehouse-db)
   that are being set up next quarter.

## Non-obvious lessons learned
- `-Fc` format is NOT human-readable and cannot be restored with psql; always use pg_restore.
- compress level 9 reduced backup size from 8.1 GB to 2.1 GB (74% reduction).
- Cron needs full absolute paths for scripts and log files (relative paths silently fail).

## Outcome
Backup system is live. First run confirmed successful.
"""

(WORKSPACE / "scratch/task-briefing.md").write_text(scenario)

print("Workspace generated successfully.")
print(f"Workspace root: {WORKSPACE}")