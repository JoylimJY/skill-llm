import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "memory",
    "releases/v1.0",
    "releases/v1.1",
    "releases/drafts",
    "ops/cron",
    "ops/logs/archive",
    "content/articles",
    "content/assets",
    "reports/weekly",
    "reports/monthly",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
today = date.today()
yesterday = today - timedelta(days=1)

# Old memory files (different dates — distractors)
for delta in [2, 5, 10, 30]:
    old_date = today - timedelta(days=delta)
    old_mem = workspace / "memory" / f"{old_date.isoformat()}.md"
    old_mem.write_text(
        f"# Ops Log {old_date.isoformat()}\n\n"
        "- executed: old newsletter blast\n"
        "- result: 200 emails sent\n"
        "- next: A/B test subject line\n"
    )

# Distractor release notes
(workspace / "releases/v1.0/CHANGELOG.md").write_text(
    "## v1.0\n- Initial launch\n- 10 articles published\n"
)
(workspace / "releases/v1.1/CHANGELOG.md").write_text(
    "## v1.1\n- Fixed paywall bug\n- Added Discord webhook\n"
)
(workspace / "releases/drafts/draft_post.md").write_text(
    "# Draft: How to monetize your newsletter\n\nComing soon...\n"
)

# Distractor cron config
(workspace / "ops/cron/schedule.txt").write_text(
    "0 9 * * * /opt/publish.sh --env prod\n"
    "0 18 * * * /opt/report.sh\n"
)

# Distractor log archive
(workspace / "ops/logs/archive/run_2024-11-01.log").write_text(
    "[INFO] publish.sh started\n[INFO] 5 items queued\n[INFO] Done.\n"
)

# Distractor weekly/monthly reports
(workspace / "reports/weekly/week_48.md").write_text(
    "Weekly summary: 3 posts, 120 new subscribers.\n"
)
(workspace / "reports/monthly/november.md").write_text(
    "Monthly: revenue $2,400 | churn 2%\n"
)

# Content articles
for i in range(1, 5):
    (workspace / f"content/articles/article_{i:02d}.md").write_text(
        f"# Article {i}\n\nContent body for article {i}.\n"
    )

# Tmp scratch
(workspace / "tmp/scratch.txt").write_text(
    "ad-hoc notes: check discord webhook, re-run if failed\n"
)

# ── THE PROBLEM: a raw, unstructured incident report the agent must process ──
# This describes a distribution job that had a delay (the postmortem trigger)
# and partially shipped. The agent must produce the properly-formatted artifacts.
incident_report = workspace / "ops/logs/distribution_incident_raw.txt"
incident_report.write_text(
    f"DATE: {yesterday.isoformat()}\n"
    "JOB: paid-content-distribution-batch\n"
    "TASK: Publish 8 premium articles to ClawHub platform and send Discord notification.\n"
    "\n"
    "TIMELINE:\n"
    "  T+0:00  - Job triggered by cron\n"
    "  T+2:15  - First 4 articles successfully published\n"
    "    URLs: https://clawhub.io/posts/1021, https://clawhub.io/posts/1022,\n"
    "          https://clawhub.io/posts/1023, https://clawhub.io/posts/1024\n"
    "  T+4:30  - Progress: 4/8 articles done\n"
    "  T+6:10  - Network timeout hit on article batch 2 (articles 5-8)\n"
    "  T+8:45  - Retry attempted, only article 5 recovered\n"
    "    URL: https://clawhub.io/posts/1025\n"
    "  T+9:00  - Job ended WITHOUT final completion signal (kickoff-only failure)\n"
    "  T+12:00 - Delay acknowledged by ops team\n"
    "\n"
    "OUTCOME:\n"
    "  Published: 5/8 articles\n"
    "  Failed: articles 6, 7, 8 (network timeout — batch 2 partially unrecoverable)\n"
    "  Discord notification: NOT sent (job exited before reporting step)\n"
    "\n"
    "ROOT CAUSE: batch-2 timeout threshold too low (10s); needs increase to 30s.\n"
    "PROPOSED FIX: Update cron job config to set BATCH_TIMEOUT=30\n"
    "\n"
    "NOTE FOR OPS: This run ended without a finish signal. Must be logged as\n"
    "kickoff-only failure per execution discipline. A postmortem and permanent\n"
    "rule update are required.\n"
)

print("Workspace scaffold complete.")
print(f"Today:     {today.isoformat()}")
print(f"Yesterday: {yesterday.isoformat()}")
print(f"Incident report: {incident_report}")