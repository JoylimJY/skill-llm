#!/usr/bin/env python3
import os
import random
import stat

random.seed(42)

workspace = "/workspace"

# --- Directory Structure ---
dirs = [
    "skills/morning-email-rollup",
    "skills/weather-report",
    "skills/task-reminder",
    "skills/news-digest",
    "clawd/logs",
    "clawd/config",
    "config/cron",
    "config/accounts",
    "bin",
    "docs",
    "archive/old-scripts",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Main rollup.sh (the real script the agent must modify) ---
rollup_sh = r"""#!/usr/bin/env bash
# Morning Email Rollup Script
# Part of the clawd skill ecosystem

set -euo pipefail

# Configuration
MAX_EMAILS="${MAX_EMAILS:-10}"
GOG_ACCOUNT="${GOG_ACCOUNT:-}"
LOG_FILE="$HOME/clawd/morning-email-rollup-log.md"

log() {
    echo "- [$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

summarize_email() {
    local body="$1"
    local summary
    if command -v gemini &>/dev/null; then
        summary=$(gemini --model gemini-2.0-flash "Summarize this email in exactly 1 sentence of natural language. Make it medium to long length. Don't use quotes: $body" 2>/dev/null || echo "$body")
    else
        summary="$body"
    fi
    # Strip leading/trailing quotes
    summary="${summary#\"}"
    summary="${summary%\"}"
    echo "$summary"
}

main() {
    mkdir -p "$(dirname "$LOG_FILE")"
    log "🔄 Starting morning email rollup"

    # Calendar check
    if command -v gog &>/dev/null; then
        EVENTS=$(gog calendar list --today --account "$GOG_ACCOUNT" 2>/dev/null || true)
        if [[ -n "$EVENTS" ]]; then
            echo "📅 **Today's Calendar Events**"
            echo "$EVENTS"
        fi
    fi

    # Search important/starred emails
    IMPORTANT_EMAILS=$(gog gmail search 'is:important OR is:starred newer_than:1d' --max 20 --account "$GOG_ACCOUNT" --json 2>/dev/null || echo "[]")

    COUNT=$(echo "$IMPORTANT_EMAILS" | jq 'length' 2>/dev/null || echo 0)
    DISPLAY_COUNT=$((COUNT < MAX_EMAILS ? COUNT : MAX_EMAILS))

    echo "📧 **Morning Email Rollup** ($DISPLAY_COUNT emails)"

    for i in $(seq 0 $((DISPLAY_COUNT - 1))); do
        EMAIL=$(echo "$IMPORTANT_EMAILS" | jq ".[$i]")
        SUBJECT=$(echo "$EMAIL" | jq -r '.subject // "No Subject"' | tr -d '"')
        SENDER=$(echo "$EMAIL" | jq -r '.from // "Unknown"')
        UNREAD=$(echo "$EMAIL" | jq -r '.unread // false')
        BODY=$(echo "$EMAIL" | jq -r '.body // ""' | sed 's/<[^>]*>//g')

        if [[ "$UNREAD" == "true" ]]; then
            INDICATOR="🔴"
        else
            INDICATOR="🟢"
        fi

        SUMMARY=$(summarize_email "$BODY")

        echo "$INDICATOR **$SENDER: $SUBJECT**"
        echo "   $SUMMARY"
    done

    log "✅ Rollup complete: $DISPLAY_COUNT emails"
}

main "$@"
"""

with open(os.path.join(workspace, "skills/morning-email-rollup/rollup.sh"), "w") as f:
    f.write(rollup_sh)

# Make rollup.sh executable
os.chmod(os.path.join(workspace, "skills/morning-email-rollup/rollup.sh"),
         stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# --- SKILL.md (reference documentation) ---
skill_md = """---
name: morning-email-rollup
description: Daily morning rollup of important emails and calendar events at 8am with AI-generated summaries
metadata: {"clawdbot":{"emoji":"📧","requires":{"bins":["gog","gemini","jq","date"]}}}
---

# Morning Email Rollup

Automatically generates a daily summary of important emails and delivers it to Telegram at 8am Denver time.
"""
with open(os.path.join(workspace, "skills/morning-email-rollup/SKILL.md"), "w") as f:
    f.write(skill_md)

# --- Distractor files ---

# Weather skill (distractor)
weather_sh = """#!/usr/bin/env bash
# Weather report skill - NOT the email rollup
MAX_LOCATIONS="${MAX_LOCATIONS:-3}"
echo "Weather report placeholder"
"""
with open(os.path.join(workspace, "skills/weather-report/weather.sh"), "w") as f:
    f.write(weather_sh)

# Old rollup config (distractor - wrong format)
old_config = """{
  "schedule": "0 8 * * *",
  "timezone": "UTC",
  "max_emails": 10,
  "account": "old-account@gmail.com",
  "session": "default"
}
"""
with open(os.path.join(workspace, "archive/old-scripts/rollup-config.json"), "w") as f:
    f.write(old_config)

# Fake cron examples (distractor - wrong syntax)
cron_examples = """# Old cron examples (DO NOT USE - outdated format)
# cron add --name "Email Rollup" --schedule "0 8 * * *" --timezone "UTC"
# cron add --name "Weather" --schedule "0 7 * * *" --timezone "America/New_York"
# These examples use wrong flags and timezone formats
"""
with open(os.path.join(workspace, "config/cron/examples.txt"), "w") as f:
    f.write(cron_examples)

# Account config (distractor)
account_cfg = """# Account Configuration
# Gmail accounts registered in the system
primary: placeholder@example.com
backup: backup@example.com
"""
with open(os.path.join(workspace, "config/accounts/accounts.yaml"), "w") as f:
    f.write(account_cfg)

# Task reminder skill (distractor)
task_sh = """#!/usr/bin/env bash
# Task reminder skill
echo "Sending reminders..."
"""
with open(os.path.join(workspace, "skills/task-reminder/reminder.sh"), "w") as f:
    f.write(task_sh)

# News digest skill (distractor)
news_sh = """#!/usr/bin/env bash
# News digest - different from email rollup
MAX_ARTICLES="${MAX_ARTICLES:-5}"
echo "News digest placeholder"
"""
with open(os.path.join(workspace, "skills/news-digest/digest.sh"), "w") as f:
    f.write(news_sh)

# Fake log (distractor - wrong path)
fake_log = """- [2026-01-10 08:00:00] 🔄 Starting morning email rollup
- [2026-01-10 08:00:05] ✅ Rollup complete: 8 emails
"""
with open(os.path.join(workspace, "clawd/logs/old-rollup.log"), "w") as f:
    f.write(fake_log)

# Wrong rollup script in wrong location (distractor)
wrong_rollup = """#!/usr/bin/env bash
# This is NOT the correct rollup script location
MAX_EMAILS=10
echo "Wrong script"
"""
with open(os.path.join(workspace, "bin/rollup.sh"), "w") as f:
    f.write(wrong_rollup)

# Docs distractor
readme = """# Clawd Skills System
Various automation skills for daily workflows.
See individual skill directories for documentation.
"""
with open(os.path.join(workspace, "docs/overview.md"), "w") as f:
    f.write(readme)

# Test files (distractor)
with open(os.path.join(workspace, "tests/unit/test_rollup.py"), "w") as f:
    f.write("# Unit tests placeholder\nimport unittest\n")

with open(os.path.join(workspace, "tests/integration/test_cron.py"), "w") as f:
    f.write("# Integration tests placeholder\nimport unittest\n")

# Clawd config (distractor)
clawd_cfg = """# Clawd system configuration
version: 2
log_dir: ~/clawd/
telegram_enabled: true
"""
with open(os.path.join(workspace, "clawd/config/system.yaml"), "w") as f:
    f.write(clawd_cfg)

# Another distractor - partial cron setup file
partial_cron = """# Partial cron setup - incomplete
# name: Morning Email Rollup
# schedule: 0 8 * * *
# NOTE: This file is incomplete and should not be used
"""
with open(os.path.join(workspace, "config/cron/morning-rollup.partial"), "w") as f:
    f.write(partial_cron)

print("Workspace generated successfully.")
print(f"Key file: {workspace}/skills/morning-email-rollup/rollup.sh")