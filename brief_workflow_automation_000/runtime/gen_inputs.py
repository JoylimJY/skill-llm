import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ─── SKILL.md ─────────────────────────────────────────────────────────────────
skill_md = workspace / "SKILL.md"
skill_md.write_text("""\
---
name: Brief
slug: brief
version: 1.0.1
description: Condense information into actionable briefings. User specifies sources, skill structures the output.
changelog: Added explicit data sources and storage location
metadata: {"clawdbot":{"emoji":"📋","requires":{"bins":[]},"os":["linux","darwin","win32"]}}
---

## Data Storage

```
~/brief/
├── preferences.md    # Learned format preferences
└── templates/        # Custom brief templates
```

Create on first use: `mkdir -p ~/brief/templates`

## Scope

This skill:
- ✅ Structures information user provides into briefs
- ✅ Learns format preferences from explicit feedback
- ✅ Stores preferences in ~/brief/preferences.md

**User-driven model:**
- User specifies WHAT information to include
- User grants access to any needed sources
- Skill handles STRUCTURE and FORMAT

This skill does NOT:
- ❌ Access files, email, or calendar without user request
- ❌ Pull data from sources user hasn't specified
- ❌ Store content (only format preferences)

## Quick Reference

| Topic | File |
|-------|------|
| Format dimensions | `dimensions.md` |
| Brief templates | `templates.md` |

## Core Rules

### 1. User Specifies Sources
When user requests a brief:
1. User provides the information OR specifies where to get it
2. If source requires access, user grants it explicitly
3. Skill structures and formats the output

Example:
```
User: "Brief me on project X status"
Agent: "I'll need access to the project docs. Can you share 
        the status doc or grant access to the project folder?"
User: [shares doc or grants access]
→ Brief generated from user-provided source
```

### 2. Brief Structure
```
📋 [BRIEF TYPE] — [SUBJECT]

⚡ BOTTOM LINE
[1-2 sentences: key takeaway]

📊 KEY POINTS
• [Point 1]
• [Point 2]
• [Point 3]

🎯 ACTION NEEDED
[Decision or action required]
```

### 3. Learn from Explicit Feedback
- "Too detailed" → shorten future briefs
- "Missing X" → ask about X in future
- "Perfect" → reinforce current format
- Store preferences in ~/brief/preferences.md

### 4. Preference Storage Format
One line per preference:
```
- Prefers bullet points over paragraphs
- Executive summary first
- Include metrics when available
- Max 1 page for status briefs
```

### 5. Brief Types
| Type | When | Key elements |
|------|------|-------------|
| Executive | Decision needed | BLUF, recommendation, risks |
| Project | Status update | Progress, blockers, next steps |
| Meeting | Before meeting | Purpose, context, decisions |
| Handoff | Transition | Current state, gotchas, priorities |
""")

# ─── RAW HANDOFF NOTES (the messy source material) ────────────────────────────
handoff_notes_dir = workspace / "ops" / "payments-service" / "handoff"
handoff_notes_dir.mkdir(parents=True, exist_ok=True)

(handoff_notes_dir / "raw_notes.txt").write_text("""\
PAYMENTS SERVICE HANDOFF NOTES  — Jordan (outgoing lead) to Taylor (incoming)
Last updated: 2024-11-14

=== CURRENT STATE ===
- Service is live in prod, handling ~12k transactions/day
- Running on k8s cluster: namespace = payments-prod
- Main repo: github.com/internal/payments-core  (private)
- DB: PostgreSQL 14.6, hosted on db-primary-03, credentials in Vault at secret/payments/db
- Redis 7 cache layer for session tokens, TTL = 900s
- Deployment pipeline: ArgoCD watches the main branch, auto-deploys on merge

=== GOTCHAS / THINGS THAT WILL BITE YOU ===
- The retry logic in charge_handler.go has an off-by-one bug. If a payment fails on attempt #3, it silently drops instead of escalating. Do NOT increase MAX_RETRIES above 3 until this is patched (ticket PAY-441).
- Vault token renewal is manual — set a calendar reminder every 30 days or the DB connection will silently fail at 3am.
- The "staging" environment is actually running prod DB credentials for the card tokenization service (yes, really). This is known, ticket PAY-388, no ETA on fix.
- Prometheus alerting for the payments namespace is misconfigured — latency alerts fire at 200ms but the SLA is actually 500ms. Lots of false pages. Adjust threshold in alerts/payments-latency.yaml.

=== PRIORITIES FOR NEXT 30 DAYS ===
1. Fix PAY-441 (retry bug) — P0, blocking quarterly audit
2. Rotate the Vault token before Dec 15 or we go down
3. Separate staging/prod credentials for tokenization (PAY-388) — P1 compliance risk
4. Review and recalibrate Prometheus alert thresholds — P2

=== CONTACTS ===
- Platform team (k8s issues): #platform-eng Slack
- DB admin: dbteam@company.internal
- Security/Vault: secops@company.internal
""")

# ─── DISTRACTOR FILES ─────────────────────────────────────────────────────────

# Distractor 1: old brief (wrong format, not a handoff)
old_briefs_dir = workspace / "archive" / "old_briefs"
old_briefs_dir.mkdir(parents=True, exist_ok=True)
(old_briefs_dir / "q3_status.txt").write_text("""\
STATUS UPDATE Q3
----------------
Things are going well. Deployment was successful. No blockers.
Action: Continue monitoring.
""")

# Distractor 2: a preferences file with WRONG format (paragraphs, not bullet lines)
wrong_prefs_dir = workspace / "archive" / "old_prefs"
wrong_prefs_dir.mkdir(parents=True, exist_ok=True)
(wrong_prefs_dir / "old_preferences.txt").write_text("""\
The user generally prefers a concise format. They like bullet points. Metrics are useful. 
Keep it short. One page max.
""")

# Distractor 3: templates folder with a partial template
templates_dir = workspace / "ops" / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
(templates_dir / "exec_template.txt").write_text("""\
EXECUTIVE BRIEF TEMPLATE (DRAFT)
Subject: 
Decision:
Risks:
Recommendation:
""")

# Distractor 4: random ops files
(workspace / "ops" / "payments-service" / "README_OLD.md").write_text("""\
# Payments Service (archived)
This README is out of date. See Confluence for current docs.
""")

(workspace / "ops" / "payments-service" / "deploy" / "argo.yaml").mkdir(parents=True, exist_ok=True) if False else None
deploy_dir = workspace / "ops" / "payments-service" / "deploy"
deploy_dir.mkdir(parents=True, exist_ok=True)
(deploy_dir / "argo.yaml").write_text("""\
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payments-core
spec:
  source:
    repoURL: github.com/internal/payments-core
    targetRevision: main
  destination:
    namespace: payments-prod
""")

# Distractor 5: unrelated project notes
unrelated_dir = workspace / "projects" / "data-pipeline" / "notes"
unrelated_dir.mkdir(parents=True, exist_ok=True)
(unrelated_dir / "sprint_notes.txt").write_text("""\
Sprint 22 notes:
- ETL pipeline refactor complete
- Spark job now runs in 4 hours instead of 9
- Blocked: waiting for S3 bucket permissions
- Next: add unit tests for transformation logic
""")

# Distractor 6: another unrelated brief request
(unrelated_dir / "meeting_prep.txt").write_text("""\
Meeting with vendor on Monday.
Topics: pricing, SLA, integration timeline.
Need a brief before the call.
""")

# Distractor 7: config file
config_dir = workspace / "ops" / "payments-service" / "config"
config_dir.mkdir(parents=True, exist_ok=True)
(config_dir / "app.env").write_text("""\
ENV=production
MAX_RETRIES=3
REDIS_TTL=900
DB_HOST=db-primary-03
VAULT_PATH=secret/payments/db
PROMETHEUS_LATENCY_ALERT_MS=200
""")

# Distractor 8: alerts file
alerts_dir = workspace / "ops" / "payments-service" / "alerts"
alerts_dir.mkdir(parents=True, exist_ok=True)
(alerts_dir / "payments-latency.yaml").write_text("""\
groups:
  - name: payments-latency
    rules:
      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(payment_request_duration_seconds_bucket[5m])) > 0.2
        for: 5m
        labels:
          severity: page
        annotations:
          summary: "Payment latency above 200ms"
""")

# Distractor 9: vault notes
vault_dir = workspace / "ops" / "vault"
vault_dir.mkdir(parents=True, exist_ok=True)
(vault_dir / "vault_renewal_notes.txt").write_text("""\
Vault tokens expire every 30 days.
Last renewed: 2024-11-15
Next due: 2024-12-15
Manual renewal required — no auto-renew configured.
""")

# Distractor 10: ticket tracker stub
tickets_dir = workspace / "ops" / "tickets"
tickets_dir.mkdir(parents=True, exist_ok=True)
(tickets_dir / "open_tickets.csv").write_text("""\
ticket_id,priority,title,status
PAY-441,P0,Retry logic off-by-one in charge_handler.go,open
PAY-388,P1,Staging env uses prod DB creds for tokenization,open
PAY-301,P3,Add request tracing to payments API,open
PAY-312,P2,Upgrade Redis from 7.0 to 7.2,backlog
""")

# ─── TASK INSTRUCTION FILE ─────────────────────────────────────────────────────
# This is the user's prompt/task context — messy, business-style
(workspace / "task.md").write_text("""\
# Handoff Brief Request

Hi — I'm Taylor, the new lead taking over the payments service from Jordan.

Jordan left raw handoff notes in: ops/payments-service/handoff/raw_notes.txt

Please create a proper transition summary document from those notes. 
Save it as `payments_handoff_brief.md` somewhere I can find it.

Also — for future briefs, please make note of my preferences:
1. I want metrics included whenever available
2. Keep it to the point — no long paragraphs
3. Always surface the most critical risk or action first

Thanks
""")

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")