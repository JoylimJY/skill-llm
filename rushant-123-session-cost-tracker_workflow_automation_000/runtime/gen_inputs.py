import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create deeply nested distractor directory structure ---
dirs = [
    "projects/saas-platform/backend/api",
    "projects/saas-platform/frontend/components",
    "projects/saas-platform/infra/terraform",
    "reports/q3/finance",
    "reports/q3/engineering",
    "logs/agent-runs/2024-10",
    "logs/agent-runs/2024-11",
    "notes/standup",
    "notes/retrospectives",
    "scripts/deprecated",
    "scripts/active",
    "data/raw",
    "data/processed",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "projects/saas-platform/backend/api/routes.py": "# FastAPI routes\nfrom fastapi import APIRouter\nrouter = APIRouter()\n",
    "projects/saas-platform/backend/api/config.json": json.dumps({"env": "production", "debug": False, "version": "2.1.0"}),
    "projects/saas-platform/frontend/components/Dashboard.tsx": "// React dashboard component\nexport default function Dashboard() { return <div>Dashboard</div>; }\n",
    "projects/saas-platform/infra/terraform/main.tf": 'resource "aws_instance" "app" { ami = "ami-0c55b159cbfafe1f0" }\n',
    "reports/q3/finance/burn_rate.csv": "month,burn,revenue\nJuly,45000,12000\nAugust,47000,15000\nSeptember,44000,18000\n",
    "reports/q3/engineering/velocity.md": "# Q3 Velocity\n- Sprint 1: 34 points\n- Sprint 2: 41 points\n- Sprint 3: 38 points\n",
    "logs/agent-runs/2024-10/summary.txt": "Agent run log - October 2024\nTotal runs: 47\nSuccessful: 39\nFailed: 8\n",
    "logs/agent-runs/2024-11/summary.txt": "Agent run log - November 2024\nTotal runs: 52\nSuccessful: 44\nFailed: 8\n",
    "notes/standup/2024-11-18.md": "# Standup\n- Worked on CI fixes\n- Reviewing PR backlog\n- Planning next sprint\n",
    "notes/retrospectives/sprint-22.md": "# Sprint 22 Retro\nWhat went well: deployment pipeline\nWhat to improve: code review turnaround\n",
    "scripts/deprecated/old_deploy.sh": "#!/bin/bash\n# DEPRECATED - do not use\necho 'old deploy'\n",
    "scripts/active/health_check.sh": "#!/bin/bash\ncurl -sf http://localhost:8080/health && echo OK\n",
    "data/raw/user_events.jsonl": '{"event":"login","user":"u1","ts":1699900000}\n{"event":"purchase","user":"u2","ts":1699900100}\n',
    "data/processed/aggregated_metrics.json": json.dumps({"dau": 1240, "wau": 5800, "mau": 18200}),
}

for path, content in distractor_files.items():
    fpath = workspace / path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# --- THE CORE PROBLEM: Session records that the agent must log ---
# These are intentionally described in business language, requiring the agent
# to map them to the correct proprietary value categories from SKILL.md,
# including both core AND extended categories.

session_records_content = """\
# AI Agent Session Records - Week of Nov 18, 2024
# These sessions need to be formally logged into the cost tracking system.
# Each line: SESSION_ID | Task Description | Outcome | Value Classification | Tokens Used | Model
#
# Value Classifications used by our team:
#   SHIPPED  -> We created a new artifact that wouldn't exist otherwise
#   FIXED    -> Saved significant time, would cost $50+ to outsource
#   USEFUL   -> Moved things forward but not critical
#   CLEANUP  -> Cleaning up previous rushed/messy work
#   FASTSHIP -> Shipped fast but created future cleanup debt
#   MONITOR  -> Heartbeat / memory review / monitoring check
#   EXPLORE  -> Uncertain value, exploratory work
#   WASTED   -> No output, failed attempt, rabbit hole

S001 | refactored auth module | cleaned up JWT mess from sprint 19 | CLEANUP | 9200 | claude-opus-4.5
S002 | wrote onboarding email sequence | 5-email drip campaign ready for review | SHIPPED | 15400 | claude-opus-4.5
S003 | investigated memory leak | found root cause in connection pool | FIXED | 7800 | claude-opus-4.5
S004 | daily infra health check | everything green, no issues found | MONITOR | 3100 | claude-opus-4.5
S005 | explored new vector DB options | notes only, no decision made | EXPLORE | 11200 | claude-opus-4.5
S006 | shipped v2 API without tests | works but needs test coverage later | FASTSHIP | 18900 | claude-opus-4.5
S007 | attempted competitor price scrape | blocked by rate limits, nothing retrieved | WASTED | 6600 | claude-opus-4.5
S008 | drafted investor update memo | 2-page memo sent to board | SHIPPED | 13300 | claude-opus-4.5
S009 | triaged 3 support tickets | resolved and documented fixes | USEFUL | 5500 | claude-opus-4.5
S010 | reviewed last month sessions | memory consolidation complete | MONITOR | 2800 | claude-opus-4.5
"""

(workspace / "data" / "raw" / "agent_sessions_nov18.txt").write_text(session_records_content)

# --- A secondary task descriptor file to drive the agent's workflow ---
task_brief = """\
TASK BRIEF - AI Productivity Audit (Board Prep)
================================================
Prepared by: CTO Office
Date: 2024-11-19

Background:
  We've been running AI agent sessions all week but haven't formally tracked
  their cost-to-value. Before the board meeting, we need all sessions from
  the file `agent_sessions_nov18.txt` logged into the official tracking system.

Requirements:
  1. Log ALL 10 sessions from agent_sessions_nov18.txt into the tracking system.
     Use the FULL logging format (not quick-log) for sessions S001, S002, and S003.
     Use the QUICK logging format for all remaining sessions (S004–S010).

  2. After logging, run the by-task grouped statistics report and save the
     complete output to a file named `by_task_stats_report.txt` in this workspace
     (at /workspace/by_task_stats_report.txt).

Notes:
  - The tracking system stores data in a well-known location automatically.
  - Map our internal value labels (SHIPPED, FIXED, CLEANUP, etc.) to whatever
    categories the tracking system actually uses — read the system documentation.
  - For full-log entries, use a meaningful outcome description from the session record.
"""

(workspace / "TASK_BRIEF.txt").write_text(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")