#!/usr/bin/env python3
"""
Generate a realistic sandbox workspace simulating a broken OpenClaw deployment
at a fintech company. Multiple distractor files, messy configs, realistic logs.
"""
import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

BASE = Path("/workspace")
OPENCLAW_BASE = Path("/root")

# ─── OpenClaw skill structure (mocked as it would exist) ───────────────────────
SKILL_DIR = OPENCLAW_BASE / ".openclaw" / "workspace" / "skills" / "openclaw-diagnostics"
SCRIPTS_DIR = SKILL_DIR / "scripts"
ASSETS_DIR = SKILL_DIR / "assets"
REFS_DIR = SKILL_DIR / "references"

for d in [SCRIPTS_DIR, ASSETS_DIR, REFS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Mock diagnostic scripts ───────────────────────────────────────────────────
(SCRIPTS_DIR / "get-diagnostic-info.sh").write_text(textwrap.dedent("""\
    #!/bin/bash
    # OpenClaw Diagnostic Info Collector
    CONFIG_PATH="${HOME}/.openclaw/config.yaml"
    echo "=== OpenClaw Config ==="
    if [ -f "$CONFIG_PATH" ]; then
        cat "$CONFIG_PATH"
    else
        echo "Config not found at $CONFIG_PATH"
    fi
    echo ""
    echo "=== OpenClaw Status ==="
    echo "gateway: stopped"
    echo "channels: telegram=disconnected, whatsapp=unknown"
    echo ""
    echo "=== Recent Logs ==="
    LOG_PATH="${HOME}/.openclaw/logs/openclaw.log"
    if [ -f "$LOG_PATH" ]; then
        tail -50 "$LOG_PATH"
    else
        echo "No log file found at $LOG_PATH"
    fi
"""))

(SCRIPTS_DIR / "check-common-issues.sh").write_text(textwrap.dedent("""\
    #!/bin/bash
    # OpenClaw Common Issues Checker
    CONFIG_PATH="${HOME}/.openclaw/config.yaml"
    echo "=== Common Issues Check ==="

    if [ ! -f "$CONFIG_PATH" ]; then
        echo "[FAIL] Config file missing"
        exit 1
    fi

    echo "[INFO] Checking gateway status..."
    echo "[WARN] Gateway appears to be stopped"

    echo "[INFO] Checking cron jobs..."
    grep -q "cron" "$CONFIG_PATH" && echo "[INFO] Cron config found" || echo "[WARN] No cron config detected"

    echo "[INFO] Checking group policy..."
    GROUP_POLICY=$(grep "groupPolicy" "$CONFIG_PATH" | awk '{print $2}' | tr -d '"')
    if [ -n "$GROUP_POLICY" ]; then
        echo "[INFO] groupPolicy is set to: $GROUP_POLICY"
    else
        echo "[WARN] groupPolicy not set"
    fi

    echo "[INFO] Checking ackReactionScope..."
    ACK_SCOPE=$(grep "ackReactionScope" "$CONFIG_PATH" | awk '{print $2}' | tr -d '"')
    if [ -n "$ACK_SCOPE" ]; then
        echo "[INFO] ackReactionScope is set to: $ACK_SCOPE"
    else
        echo "[WARN] ackReactionScope not configured"
    fi
    echo "=== Check Complete ==="
"""))

# ─── Knowledge base snapshot (minimal but realistic) ──────────────────────────
SNAPSHOT = {
    "meta": {
        "pageCount": 335,
        "snapshotDate": "2024-11-01T08:00:00Z",
        "sizeBytes": 3240482
    },
    "index": [
        {"slug": "008888be", "title": "Group Messaging Configuration", "url": "https://docs.openclaw.io/group-messaging", "description": "How to configure group message handling, ackReactionScope, and group policies."},
        {"slug": "0bfb808e", "title": "Group Allowlist Setup", "url": "https://docs.openclaw.io/group-allowlist", "description": "Configuring groupPolicy allowlist mode and whitelisting specific groups."},
        {"slug": "919c126f", "title": "Device Pairing Guide", "url": "https://docs.openclaw.io/pairing", "description": "Steps to pair WhatsApp and other channels to OpenClaw gateway."},
        {"slug": "a99b0ed8", "title": "Message Routing", "url": "https://docs.openclaw.io/message-routing", "description": "How OpenClaw routes incoming messages to skills and handlers."},
        {"slug": "a632126a", "title": "Automation Troubleshooting", "url": "https://docs.openclaw.io/automation-troubleshooting", "description": "Troubleshoot failed automations, skill invocations, and event triggers."},
        {"slug": "87e3285b", "title": "Auth Monitoring", "url": "https://docs.openclaw.io/auth-monitoring", "description": "Monitor authentication state, session health, and auth failure alerts."},
        {"slug": "b239629c", "title": "Cron Job Scheduling", "url": "https://docs.openclaw.io/cron-jobs", "description": "Configure and troubleshoot scheduled cron tasks in OpenClaw."},
        {"slug": "6569d3b4", "title": "Channels Overview", "url": "https://docs.openclaw.io/channels", "description": "Overview of supported channels and connection configuration."},
        {"slug": "d09047a0", "title": "WhatsApp Integration", "url": "https://docs.openclaw.io/whatsapp", "description": "Connect and configure WhatsApp channel in OpenClaw."},
        {"slug": "d423ce29", "title": "Telegram Integration", "url": "https://docs.openclaw.io/telegram", "description": "Connect and configure Telegram channel in OpenClaw."},
        {"slug": "90a33c43", "title": "Feishu Integration", "url": "https://docs.openclaw.io/feishu", "description": "Connect and configure Feishu/Lark channel in OpenClaw."}
    ],
    "pages": {
        "008888be": textwrap.dedent("""\
            # Group Messaging Configuration

            ## ackReactionScope

            Controls which group messages the bot responds to.

            | Value | Behavior |
            |-------|----------|
            | `all` | Respond to all messages in the group |
            | `group-mentions` | Only respond when the bot is @mentioned |
            | `dm-only` | Never respond in groups |

            **Default:** `group-mentions`

            If users report that the bot does not respond to regular group messages,
            check if `ackReactionScope` is set to `group-mentions`. In this case the bot
            is working correctly — users must @ mention the bot.

            ## groupPolicy

            | Value | Behavior |
            |-------|----------|
            | `open` | Bot joins and responds in any group |
            | `allowlist` | Bot only responds in whitelisted groups |

            `groupPolicy: "open"` is a valid and common configuration. Do not treat it as missing or broken.
        """),
        "0bfb808e": textwrap.dedent("""\
            # Group Allowlist Setup

            When `groupPolicy` is set to `allowlist`, you must whitelist each group ID.

            ```yaml
            groupPolicy: allowlist
            allowedGroups:
              - "120363XXXXXXXXX@g.us"
              - "120363YYYYYYYYY@g.us"
            ```

            Groups not in the list will be silently ignored.
        """),
        "b239629c": textwrap.dedent("""\
            # Cron Job Scheduling

            ## Prerequisites

            The OpenClaw **Gateway must be running** for cron jobs to trigger.
            If the gateway is stopped, no scheduled tasks will execute.

            ## Configuration

            ```yaml
            cron:
              - id: daily-report
                expression: "0 9 * * 1-5"
                skill: compliance-reporter
                enabled: true
            ```

            ## Troubleshooting

            1. Verify gateway is running: `openclaw status`
            2. Validate cron expression (standard 5-field cron syntax)
            3. Check logs for `[CRON]` trigger lines
            4. Verify `muteHours` is not blocking the schedule window
            5. Ensure `enabled: true` is set on the cron entry

            Common mistake: setting `enabled: false` during testing and forgetting to re-enable.
        """),
        "87e3285b": textwrap.dedent("""\
            # Auth Monitoring

            ## Session Health

            OpenClaw maintains persistent sessions for each connected channel.
            Auth failures appear in logs as `[AUTH] session expired` or `[AUTH] QR required`.

            ## Reconnection

            If a channel disconnects, OpenClaw will attempt auto-reconnect up to 3 times.
            After 3 failures, manual re-pairing is required.

            ## Monitoring

            Set `authMonitoring: true` to receive alerts when sessions degrade.
        """),
        "6569d3b4": textwrap.dedent("""\
            # Channels Overview

            OpenClaw supports the following channels:
            - WhatsApp (via WA Web protocol)
            - Telegram (via Bot API)
            - Feishu / Lark
            - Slack (beta)

            Each channel requires its own config block under `channels:`.

            Channel status can be checked with `openclaw status`.
        """),
        "a632126a": textwrap.dedent("""\
            # Automation Troubleshooting

            ## Skill Not Triggering

            1. Confirm the Gateway is running
            2. Confirm the channel delivering the trigger message is connected
            3. Check the skill trigger pattern matches the incoming message
            4. Review logs for `[SKILL]` lines

            ## Event Not Firing

            Check `allowFrom` and ensure the sending entity is not blocked.
        """),
        "919c126f": "# Device Pairing\n\nRun `openclaw pair --channel whatsapp` and scan the QR code.\n",
        "a99b0ed8": "# Message Routing\n\nMessages are routed based on channel, sender, and trigger patterns.\n",
        "d09047a0": "# WhatsApp Integration\n\nRequires pairing via QR code. Session stored in `.openclaw/sessions/`.\n",
        "d423ce29": "# Telegram Integration\n\nRequires a Bot Token from BotFather. Set in `channels.telegram.token`.\n",
        "90a33c43": "# Feishu Integration\n\nRequires App ID and App Secret from Feishu Developer Console.\n"
    }
}

(ASSETS_DIR / "default-snapshot.json").write_text(json.dumps(SNAPSHOT, indent=2))

# ─── knowledge-base-index.md ──────────────────────────────────────────────────
(REFS_DIR / "knowledge-base-index.md").write_text(textwrap.dedent("""\
    # Knowledge Base Index

    ## Group Messages
    - `008888be` — Group Messaging Configuration (ackReactionScope, groupPolicy)
    - `0bfb808e` — Group Allowlist Setup

    ## Pairing
    - `919c126f` — Device Pairing Guide

    ## Message Routing
    - `a99b0ed8` — Message Routing

    ## Automation
    - `a632126a` — Automation Troubleshooting

    ## Authentication
    - `87e3285b` — Auth Monitoring

    ## Scheduling
    - `b239629c` — Cron Job Scheduling

    ## Channels
    - `6569d3b4` — Channels Overview
    - `d09047a0` — WhatsApp Integration
    - `d423ce29` — Telegram Integration
    - `90a33c43` — Feishu Integration
"""))

# ─── common-issues.md ─────────────────────────────────────────────────────────
(REFS_DIR / "common-issues.md").write_text(textwrap.dedent("""\
    # Common Issues Diagnostic Rules

    ## Rule 1: Group Messages Not Responding

    **Trigger:** Users report bot does not reply in group chats.

    **Check:**
    - `ackReactionScope: "group-mentions"` → Bot only responds to @mentions. This is NOT a bug.
      Diagnosis: Inform user to @mention the bot. Reference: `008888be`
    - `ackReactionScope: "all"` + bot in group + Gateway running → Check message routing (`a99b0ed8`)
    - `groupPolicy: "open"` is VALID — do NOT flag as an issue.
    - `groupPolicy: "allowlist"` + group not in allowedGroups → Group is blocked. Reference: `0bfb808e`

    ## Rule 2: Cron Jobs Not Executing

    **Trigger:** Scheduled tasks never fire.

    **Check order:**
    1. Is Gateway running? If NO → Root cause. Reference: `b239629c`
    2. Is `enabled: true` on the cron entry? If NO → Enable it.
    3. Is cron expression valid?
    4. Check muteHours overlap.

    ## Rule 3: Channel Connection Issues

    **Trigger:** Channel shows disconnected or unknown status.

    **Check:**
    - Run `openclaw status`
    - For WhatsApp: check pairing status (`919c126f`, `d09047a0`)
    - For Telegram: verify token (`d423ce29`)
    - Check auth monitoring (`87e3285b`)

    ## Diagnosis Output Format

    Each identified issue should be reported with:
    - `issue_id`: short kebab-case identifier
    - `category`: one of `group-messaging`, `cron-jobs`, `channel-connection`, `authentication`
    - `root_cause`: concise description
    - `is_misconfiguration`: true/false (false if config is valid but user behavior is wrong)
    - `reference_slugs`: list of relevant doc slugs
    - `recommended_action`: what to do next
"""))

# ─── The broken OpenClaw config ───────────────────────────────────────────────
OPENCLAW_HOME = Path.home() / ".openclaw"
(OPENCLAW_HOME / "logs").mkdir(parents=True, exist_ok=True)

(OPENCLAW_HOME / "config.yaml").write_text(textwrap.dedent("""\
    # OpenClaw Configuration - FinTrack Internal Bot
    version: "2.1"

    gateway:
      port: 3000
      logLevel: info

    channels:
      telegram:
        enabled: true
        token: "REDACTED"
      whatsapp:
        enabled: true
        sessionPath: ".openclaw/sessions/wa-main"

    messaging:
      ackReactionScope: "group-mentions"
      groupPolicy: "open"
      allowFrom:
        - "all"

    cron:
      - id: daily-compliance-report
        expression: "0 9 * * 1-5"
        skill: compliance-reporter
        enabled: false
      - id: weekly-summary
        expression: "0 17 * * 5"
        skill: weekly-summarizer
        enabled: true

    muteHours:
      start: 22
      end: 7

    authMonitoring: false
"""))

# Realistic log file
(OPENCLAW_HOME / "logs" / "openclaw.log").write_text(textwrap.dedent("""\
    2024-11-14T08:45:01Z [INFO] OpenClaw v2.1.4 starting...
    2024-11-14T08:45:02Z [INFO] Loading config from /root/.openclaw/config.yaml
    2024-11-14T08:45:03Z [INFO] Channel telegram: initialized
    2024-11-14T08:45:03Z [WARN] Channel whatsapp: session not found, pairing required
    2024-11-14T08:45:04Z [AUTH] whatsapp session expired, attempting reconnect (1/3)
    2024-11-14T08:45:07Z [AUTH] whatsapp reconnect failed (2/3)
    2024-11-14T08:45:12Z [AUTH] whatsapp reconnect failed (3/3) - manual re-pair required
    2024-11-14T08:45:12Z [WARN] Gateway stopping due to channel error
    2024-11-14T08:45:13Z [INFO] Gateway stopped.
    2024-11-14T09:00:00Z [CRON] Trigger check: daily-compliance-report - SKIPPED (enabled=false)
    2024-11-14T09:00:00Z [CRON] Trigger check: weekly-summary - SKIPPED (gateway not running)
    2024-11-14T10:23:15Z [INFO] Group message received in 120363ABC@g.us - no response (ackReactionScope=group-mentions, no @mention detected)
    2024-11-14T10:45:00Z [INFO] Group message received in 120363ABC@g.us - no response (ackReactionScope=group-mentions, no @mention detected)
    2024-11-14T11:00:00Z [CRON] Trigger check: daily-compliance-report - SKIPPED (enabled=false)
    2024-11-14T17:00:00Z [CRON] Trigger check: weekly-summary - SKIPPED (gateway not running)
"""))

# ─── Distractor files (fintech company context) ───────────────────────────────
distractor_base = BASE / "fintrack-ops"

(distractor_base / "runbooks").mkdir(parents=True, exist_ok=True)
(distractor_base / "runbooks" / "incident-template.md").write_text(
    "# Incident Report Template\n\n## Summary\n## Timeline\n## Root Cause\n## Action Items\n"
)
(distractor_base / "runbooks" / "escalation-matrix.csv").write_text(
    "severity,team,contact\nP1,infra,oncall@fintrack.io\nP2,platform,platform@fintrack.io\n"
)

(distractor_base / "deployments").mkdir(parents=True, exist_ok=True)
(distractor_base / "deployments" / "k8s-bot-deployment.yaml").write_text(textwrap.dedent("""\
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: fintrack-bot
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: fintrack-bot
"""))
(distractor_base / "deployments" / "docker-compose.yml").write_text(textwrap.dedent("""\
    version: '3'
    services:
      openclaw:
        image: openclaw:2.1
        volumes:
          - ~/.openclaw:/root/.openclaw
"""))

(distractor_base / "configs" / "legacy").mkdir(parents=True, exist_ok=True)
(distractor_base / "configs" / "legacy" / "old-config-v1.yaml").write_text(textwrap.dedent("""\
    # Legacy v1 config - DO NOT USE
    version: "1.0"
    bot_token: "OLD_TOKEN"
    group_mode: reply_all
"""))
(distractor_base / "configs" / "legacy" / "migration-notes.txt").write_text(
    "Migrated from v1 to v2.1 on 2024-10-01. Token redacted. Check new config format.\n"
)

(distractor_base / "alerts").mkdir(parents=True, exist_ok=True)
(distractor_base / "alerts" / "pagerduty-config.json").write_text(json.dumps({
    "service_key": "REDACTED",
    "alert_on": ["gateway_down", "auth_failure"]
}, indent=2))

(distractor_base / "scripts").mkdir(parents=True, exist_ok=True)
(distractor_base / "scripts" / "restart-bot.sh").write_text(
    "#!/bin/bash\n# Restart OpenClaw service\nsystemctl restart openclaw || docker restart openclaw\n"
)
(distractor_base / "scripts" / "check-health.sh").write_text(
    "#!/bin/bash\ncurl -sf http://localhost:3000/health && echo OK || echo FAIL\n"
)

(distractor_base / "tickets").mkdir(parents=True, exist_ok=True)
(distractor_base / "tickets" / "FINOPS-2891.txt").write_text(textwrap.dedent("""\
    Ticket: FINOPS-2891
    Reporter: compliance-team@fintrack.io
    Subject: Daily compliance report not sent today (2024-11-14)
    Priority: P1
    Description: The automated daily compliance report that should arrive at 9am via Telegram
    did not arrive. This is a compliance obligation. Please investigate urgently.
"""))
(distractor_base / "tickets" / "FINOPS-2892.txt").write_text(textwrap.dedent("""\
    Ticket: FINOPS-2892
    Reporter: trading-desk@fintrack.io
    Subject: Bot not responding in WhatsApp group
    Priority: P2
    Description: Our WhatsApp trading desk group messages are being sent but the bot
    never responds. We are NOT @mentioning the bot because we assumed it responds to all messages.
    Is the bot broken?
"""))
(distractor_base / "tickets" / "FINOPS-2893.txt").write_text(textwrap.dedent("""\
    Ticket: FINOPS-2893
    Reporter: ops-team@fintrack.io
    Subject: WhatsApp channel showing unknown status
    Priority: P1
    Description: OpenClaw status command shows WhatsApp as 'unknown'. Telegram seems to be
    initialized but we're not sure if it's working. Bot seems completely offline.
"""))

(distractor_base / "docs" / "onboarding").mkdir(parents=True, exist_ok=True)
(distractor_base / "docs" / "onboarding" / "bot-setup-guide.md").write_text(
    "# Bot Setup Guide\n\nSee internal wiki for setup instructions.\n"
)

# ─── Ensure output dir exists ─────────────────────────────────────────────────
(BASE / "reports").mkdir(parents=True, exist_ok=True)

print("Workspace generated successfully.")
print(f"Key files:")
print(f"  Config: {OPENCLAW_HOME / 'config.yaml'}")
print(f"  Logs:   {OPENCLAW_HOME / 'logs' / 'openclaw.log'}")
print(f"  Skill:  {SKILL_DIR}")
print(f"  Tickets: {distractor_base / 'tickets'}")