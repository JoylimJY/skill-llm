import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

# --- Define workspace root ---
workspace = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))
workspace.mkdir(parents=True, exist_ok=True)

# --- Create realistic distractor directory structure for a mobile gaming studio ---
dirs = [
    workspace / "projects" / "retention_v2" / "analytics",
    workspace / "projects" / "retention_v2" / "experiments",
    workspace / "projects" / "liveops" / "events" / "summer_2025",
    workspace / "projects" / "liveops" / "events" / "fall_2025",
    workspace / "reports" / "weekly" / "2025-Q3",
    workspace / "reports" / "monthly",
    workspace / "docs" / "design",
    workspace / "docs" / "postmortems",
    workspace / "team" / "hiring",
    workspace / "team" / "1on1_notes",
    workspace / ".openclaw" / "workspace" / "memory",
    workspace / ".openclaw" / "config",
    workspace / ".openclaw" / "logs",
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    workspace / "projects" / "retention_v2" / "analytics" / "dau_trend_q3.csv": (
        "date,dau,retention_d1,retention_d7\n"
        "2025-07-01,142000,0.41,0.18\n"
        "2025-08-01,155000,0.43,0.20\n"
        "2025-09-01,161000,0.44,0.21\n"
    ),
    workspace / "projects" / "retention_v2" / "experiments" / "ab_test_onboarding.json": json.dumps({
        "experiment_id": "EXP-2025-0032",
        "name": "Revised Onboarding Flow v2",
        "status": "completed",
        "control_d1_retention": 0.38,
        "treatment_d1_retention": 0.44,
        "p_value": 0.021,
        "conclusion": "Treatment wins. Ship to 100%."
    }, indent=2),
    workspace / "projects" / "liveops" / "events" / "summer_2025" / "summer_blast_config.yaml": (
        "event_name: Summer Blast 2025\n"
        "start: 2025-07-15\n"
        "end: 2025-08-15\n"
        "rewards:\n"
        "  - type: coins\n"
        "    amount: 5000\n"
        "  - type: chest\n"
        "    rarity: epic\n"
        "participation_rate_target: 0.35\n"
    ),
    workspace / "projects" / "liveops" / "events" / "fall_2025" / "harvest_festival_plan.md": (
        "# Harvest Festival 2025\n\n"
        "## Goals\n"
        "- Increase 7-day retention by 3pp during event window\n"
        "- Drive IAP conversion to 8%\n\n"
        "## Timeline\n"
        "- Planning: Sep 15 - Sep 30\n"
        "- QA: Oct 1 - Oct 10\n"
        "- Launch: Oct 11\n"
    ),
    workspace / "reports" / "weekly" / "2025-Q3" / "week30_summary.txt": (
        "Week 30 Summary\n"
        "DAU: 158,200 (+2.1% WoW)\n"
        "D1 Retention: 43.1%\n"
        "D7 Retention: 19.8%\n"
        "Revenue: $312,400\n"
        "Top Issue: Push notification opt-out rate high at 34%\n"
    ),
    workspace / "reports" / "monthly" / "august_kpi_deck_notes.txt": (
        "August KPI Review Notes\n"
        "- D1 Retention hit 43%, up from 38% in June. Onboarding experiment key driver.\n"
        "- D30 Retention still lagging at 8.2%, target was 12%.\n"
        "- Push CTR improved to 11.4% after copy refresh.\n"
        "- IAP conversion: 6.9%, below 8% target.\n"
    ),
    workspace / "docs" / "design" / "retention_mechanics_spec.md": (
        "# Retention Mechanics Specification\n\n"
        "## Daily Login Reward Redesign\n"
        "Proposed changes to streak system to improve D7 retention.\n\n"
        "## Social Features\n"
        "Guild system to launch in Q4 to support long-term retention.\n"
    ),
    workspace / "docs" / "postmortems" / "push_notification_outage_aug2025.md": (
        "# Postmortem: Push Notification Outage - Aug 12, 2025\n\n"
        "**Duration:** 4 hours\n"
        "**Impact:** ~60,000 users missed daily reminder push\n"
        "**Root Cause:** Certificate expiry not monitored\n"
        "**Action Items:**\n"
        "- Add cert expiry monitoring to alerting dashboard\n"
        "- Rotate certs 30 days before expiry going forward\n"
    ),
    workspace / "team" / "hiring" / "senior_analyst_jd.txt": (
        "Senior Data Analyst - Mobile Gaming\n"
        "Requirements:\n"
        "- 3+ years in mobile analytics\n"
        "- SQL, Python, Tableau\n"
        "- Experience with retention cohort analysis\n"
    ),
    workspace / "team" / "1on1_notes" / "chen_wei_q3_notes.txt": (
        "1:1 Notes - Chen Wei (Lead Data Analyst)\n"
        "Q3 Highlights:\n"
        "- Delivered retention dashboard on time\n"
        "- Identified onboarding drop-off via funnel analysis\n"
        "Career goal: Move into product analytics lead role\n"
    ),
    workspace / ".openclaw" / "config" / "settings.json": json.dumps({
        "user": "li_na",
        "workspace": "~/.openclaw/workspace",
        "skills_enabled": ["okr", "notes", "tasks"],
        "default_cycle": "2025-Q3"
    }, indent=2),
    workspace / ".openclaw" / "logs" / "activity.log": (
        "2025-07-01 09:00:00 [INFO] Skill 'okr' loaded\n"
        "2025-07-01 09:05:00 [INFO] Session started: user=li_na\n"
        "2025-09-15 14:22:00 [INFO] Skill 'notes' invoked\n"
        "2025-09-28 11:00:00 [INFO] Skill 'okr' invoked\n"
    ),
}

for fpath, content in distractor_files.items():
    fpath.write_text(content, encoding="utf-8")

# --- The memory/okr.md does NOT exist yet; agent must create it from scratch ---
okr_path = workspace / ".openclaw" / "workspace" / "memory" / "okr.md"
# Intentionally leave it absent — agent must create it
assert not okr_path.exists(), "okr.md should not pre-exist"

# --- Write a brief context file the agent will see as their task briefing ---
brief_path = workspace / "q3_retention_initiative_brief.txt"
brief_path.write_text(
    "Q3 2025 Retention Initiative - Closure Brief\n"
    "============================================\n\n"
    "Owner: Li Na (Head of Product, Mobile Gaming Studio)\n"
    "Cycle: 2025-Q3 (Jul 1 – Sep 30, 2025)\n\n"
    "This quarter, the team set out to improve user retention across three fronts.\n"
    "Below are the three Key Results we committed to, and the final actuals:\n\n"
    "KR1: Increase Day-1 retention rate from 38% to 45%\n"
    "  → Achieved: 44%  (started at 38%)\n\n"
    "KR2: Increase Day-7 retention rate from 16% to 22%\n"
    "  → Achieved: 19.8%  (started at 16%)\n\n"
    "KR3: Reduce push notification opt-out rate from 40% to 28%\n"
    "  → Achieved: 34%  (started at 40%)\n\n"
    "The quarter is now closed. Please set up the tracking record for this initiative,\n"
    "mark it completed, log all final KR actuals, and produce a full end-of-quarter\n"
    "review with a rating for the overall objective.\n",
    encoding="utf-8"
)

print("Workspace initialized successfully.")
print(f"Brief file: {brief_path}")
print(f"OKR memory path (must be created by agent): {okr_path}")