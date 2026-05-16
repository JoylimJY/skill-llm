import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Create realistic distractor directory structure ---
dirs = [
    "memory",
    "logs/sessions",
    "logs/errors",
    "projects/saas-platform/backend",
    "projects/saas-platform/frontend",
    "projects/saas-platform/infra",
    "projects/analytics-pipeline",
    "reviews/weekly",
    "reviews/monthly",
    "notes/research",
    "notes/meetings",
    "templates",
    "archive/2024",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- The TARGET date for the review ---
TARGET_DATE = date(2025, 6, 12)
TARGET_DATE_STR = TARGET_DATE.strftime("%Y-%m-%d")

# --- Create the target memory file with realistic messy product decisions ---
memory_content = f"""# Daily Log — {TARGET_DATE_STR}

## Morning

- Reviewed Q3 roadmap with engineering lead. Decided to delay the multi-tenant SSO feature by 6 weeks to focus on improving dashboard load times.
- Customer success flagged 3 enterprise clients asking for bulk CSV export. Quick to build, decided to prioritize it above the planned API rate-limiting improvements.
- Approved budget for a third-party monitoring tool (Datadog) — it's what all the competitors use so it seems like the obvious choice.

## Afternoon

- Spent 3 hours debugging a race condition in the webhook delivery system. Fixed it with a retry mechanism with exponential backoff.
- Decided NOT to write a postmortem for the webhook outage because the fix was "obvious in hindsight" and "we don't have time right now."
- The analytics pipeline refactor from two months ago is still 40% done — kept pushing it because the new work keeps feeling more urgent. Team has sunk significant effort already, need to finish it.

## Evening

- Agreed to add a dark mode toggle to the mobile app after a single power user requested it on Twitter and it got 12 likes.
- Declined a partnership with a niche data vendor because we've never worked with that type of data before and it felt too uncertain.
- Set up a new Slack channel for async decision logging, but nobody used it today.

## Decisions Summary
1. Delayed SSO in favor of performance work
2. Prioritized CSV export over API rate-limiting
3. Chose Datadog based on competitor usage
4. Skipped postmortem for webhook outage
5. Continuing analytics refactor despite delays
6. Added dark mode based on one viral tweet
7. Declined data vendor partnership due to unfamiliarity
"""

(workspace / "memory" / f"{TARGET_DATE_STR}.md").write_text(memory_content)

# --- Create distractor memory files (other dates) ---
for delta in [-3, -2, -1, 1, 2]:
    d = TARGET_DATE + timedelta(days=delta)
    ds = d.strftime("%Y-%m-%d")
    content = f"""# Daily Log — {ds}

## Morning
- Routine standup. No major decisions.
- Reviewed PR backlog.

## Afternoon  
- Pair programming session on auth module.
- Updated confluence docs.

## Decisions Summary
- Minor refactoring approved.
"""
    (workspace / "memory" / f"{ds}.md").write_text(content)

# --- Create distractor session logs ---
session_log_content = """[09:02] Session started
[09:15] User query: "what's the status of the SSO feature?"
[09:18] Response delivered
[11:30] User query: "show me dashboard metrics for last week"
[14:45] User query: "webhook is failing intermittently"
[17:22] Session ended
"""
(workspace / "logs" / "sessions" / f"session_{TARGET_DATE_STR}.log").write_text(session_log_content)

old_session = """[08:55] Session started
[10:00] Reviewed analytics pipeline status
[15:30] Session ended
"""
(workspace / "logs" / "sessions" / f"session_2025-06-11.log").write_text(old_session)

error_log = """[2025-06-12 14:33:01] ERROR webhook_service: Delivery attempt 1 failed for event_id=evt_9921
[2025-06-12 14:33:04] WARN  retry_scheduler: Backoff applied, next attempt in 4s
[2025-06-12 14:33:08] INFO  webhook_service: Delivery succeeded on attempt 2 for event_id=evt_9921
"""
(workspace / "logs" / "errors" / f"errors_{TARGET_DATE_STR}.log").write_text(error_log)

# --- Distractor project files ---
(workspace / "projects" / "saas-platform" / "backend" / "config.py").write_text(
    "# Backend configuration\nDB_POOL_SIZE = 10\nWEBHOOK_RETRY_LIMIT = 3\nRATELIMIT_MAX = 1000\n"
)
(workspace / "projects" / "saas-platform" / "frontend" / "feature_flags.json").write_text(
    '{"dark_mode": false, "csv_export": true, "sso_enabled": false}\n'
)
(workspace / "projects" / "saas-platform" / "infra" / "monitoring.yaml").write_text(
    "provider: datadog\nretention_days: 30\nalerts:\n  - name: webhook_failure_rate\n    threshold: 0.05\n"
)
(workspace / "projects" / "analytics-pipeline" / "pipeline.py").write_text(
    "# Analytics pipeline - 40% complete\n# TODO: Finish schema migration, dedup logic, output connectors\n"
)

# --- Distractor review files ---
(workspace / "reviews" / "weekly" / "2025-W23.md").write_text(
    "# Week 23 Review\n\n- Velocity: 34 story points\n- Bugs closed: 7\n- Customer tickets resolved: 23\n"
)
(workspace / "reviews" / "monthly" / "2025-05.md").write_text(
    "# May 2025 Review\n\n- MRR growth: +8%\n- Churn: 1.2%\n- NPS: 47\n"
)

# --- Distractor notes ---
(workspace / "notes" / "research" / "competitor_analysis.md").write_text(
    "# Competitor Analysis\n\nDatadog: market leader in APM.\nNew Relic: strong in full-stack observability.\n"
)
(workspace / "notes" / "meetings" / "2025-06-10-board-prep.md").write_text(
    "# Board Meeting Prep\n\n- Prepare Q3 forecasts\n- Review hiring plan\n- SSO feature timeline update\n"
)
(workspace / "notes" / "meetings" / "2025-06-12-engineering-sync.md").write_text(
    "# Engineering Sync — 2025-06-12\n\nAttendees: CTO, 4 engineers\nTopics: SSO delay rationale, webhook postmortem (cancelled), Datadog onboarding.\n"
)

# --- Templates ---
(workspace / "templates" / "daily_log_template.md").write_text(
    "# Daily Log — YYYY-MM-DD\n\n## Morning\n\n## Afternoon\n\n## Evening\n\n## Decisions Summary\n"
)
(workspace / "templates" / "review_template.md").write_text(
    "# Review Template\n\n## Wins\n\n## Blockers\n\n## Next Steps\n"
)

# --- Archive distractors ---
(workspace / "archive" / "2024" / "annual_retrospective.md").write_text(
    "# 2024 Annual Retrospective\n\nKey learnings: ship faster, instrument earlier, hire senior engineers sooner.\n"
)

print(f"Workspace scaffold complete. Target memory file: memory/{TARGET_DATE_STR}.md")
print(f"Total files created: {len(list(workspace.rglob('*.*')))}")