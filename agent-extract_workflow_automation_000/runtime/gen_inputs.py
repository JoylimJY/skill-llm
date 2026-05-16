#!/usr/bin/env python3
import json
import os
import random

random.seed(42)

HOME = os.path.expanduser("~")
OPENCLAW_DIR = os.path.join(HOME, ".openclaw")

# Core directory structure
dirs = [
    f"{OPENCLAW_DIR}/agents/main/sessions",
    f"{OPENCLAW_DIR}/agents/main/transcripts",
    f"{OPENCLAW_DIR}/workspace/skills/social-monitor",
    f"{OPENCLAW_DIR}/workspace/skills/calendar",
    f"{OPENCLAW_DIR}/workspace/skills/email-digest",
    f"{OPENCLAW_DIR}/workspace/memory",
    f"{OPENCLAW_DIR}/workspace/logs",
    f"{OPENCLAW_DIR}/cron",
    f"{OPENCLAW_DIR}/channels",
    f"{OPENCLAW_DIR}/tmp",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- openclaw.json ---
config = {
    "version": "2.1.0",
    "agents": {
        "default": "main",
        "list": [
            {
                "id": "main",
                "name": "Main Assistant",
                "workspace": f"{HOME}/.openclaw/workspace"
            }
        ]
    },
    "channels": {
        "slack": {
            "enabled": True,
            "webhook": "https://hooks.slack.com/services/FAKE/FAKE/FAKE",
            "default_channel": "#ai-assistant"
        },
        "telegram": {
            "enabled": False,
            "token": "fake-token-12345"
        }
    },
    "settings": {
        "logLevel": "info",
        "maxRetries": 3,
        "timeoutMs": 30000
    }
}

with open(f"{OPENCLAW_DIR}/openclaw.json", "w") as f:
    json.dump(config, f, indent=2)

# --- sessions.json ---
sessions = {
    "main:default": {
        "created": "2024-01-15T08:00:00Z",
        "lastActive": "2024-06-01T12:00:00Z",
        "messageCount": 1842
    },
    "main:calendar": {
        "created": "2024-02-20T09:00:00Z",
        "lastActive": "2024-05-30T18:00:00Z",
        "messageCount": 234
    }
}
with open(f"{OPENCLAW_DIR}/agents/main/sessions/sessions.json", "w") as f:
    json.dump(sessions, f, indent=2)

# --- cron jobs store ---
cron_store = {
    "jobs": [
        {
            "id": "job-001",
            "name": "Main Heartbeat",
            "schedule": {"kind": "every", "everyMs": 3600000},
            "agentId": "main",
            "sessionKey": "main:default",
            "sessionTarget": "resume",
            "payload": {
                "kind": "agentTurn",
                "message": "Read HEARTBEAT.md if it exists. Follow it strictly."
            },
            "delivery": {"mode": "announce"}
        }
    ]
}
with open(f"{OPENCLAW_DIR}/cron/jobs.json", "w") as f:
    json.dump(cron_store, f, indent=2)

# --- SOUL.md ---
soul_content = """# Soul

## Core Values
- Helpfulness above all
- Honesty and transparency
- Respect for privacy
- Continuous improvement

## Personality Traits
- Curious and analytical
- Warm but professional
- Direct and concise
- Adaptable to context
"""
with open(f"{OPENCLAW_DIR}/workspace/SOUL.md", "w") as f:
    f.write(soul_content)

# --- IDENTITY.md ---
identity_content = """# Identity

## Name
Assistant Prime

## Role
General-purpose AI assistant for Acme Corp

## Primary Responsibilities
- Daily task management
- Email summarization
- Calendar management
- Social media monitoring (via social-monitor skill)
- General Q&A
"""
with open(f"{OPENCLAW_DIR}/workspace/IDENTITY.md", "w") as f:
    f.write(identity_content)

# --- AGENTS.md ---
agents_content = """# Agents Configuration

## Main Agent
Handles all incoming requests. Routes to specialized skills as needed.

## Shared Knowledge
- Company: Acme Corp
- Timezone: UTC+8
- Business hours: 09:00-18:00

## Coordination
- Main agent coordinates with skills via function calls
- Skills report back via session messages
"""
with open(f"{OPENCLAW_DIR}/workspace/AGENTS.md", "w") as f:
    f.write(agents_content)

# --- USER.md ---
user_content = """# User Profile

## Name
Alex Chen

## Preferences
- Brief, bullet-point responses preferred
- Technical detail when asked
- No excessive pleasantries
- Prefer metric units

## Communication Style
- Direct
- Data-driven
"""
with open(f"{OPENCLAW_DIR}/workspace/USER.md", "w") as f:
    f.write(user_content)

# --- HEARTBEAT.md (main workspace - contains BOTH general and social-monitor tasks) ---
heartbeat_content = """# 心跳任务

## 任务描述

### 通用任务
- 检查今日日历事件，如有即将到来的会议则发送提醒
- 检查邮件摘要队列，如有未处理项目则执行摘要

### Social Monitor 任务
- 检查 Weibo、Twitter、LinkedIn 上 Acme Corp 的最新提及
- 如有负面情绪内容，立即提醒 Alex
- 发布每日品牌健康报告到 #social-monitoring Slack 频道
- 跟踪竞争对手 BetaCorp 的最新动态

## 频率控制
- 通用检查：每 60 分钟
- Social Monitor：每 30 分钟

## 静默条件
- 夜间 23:00-08:00 除非紧急
- 无新通知时回复 HEARTBEAT_OK
"""
with open(f"{OPENCLAW_DIR}/workspace/HEARTBEAT.md", "w") as f:
    f.write(heartbeat_content)

# --- MEMORY.md ---
memory_content = """# Long-term Memory

## Key Facts
- Alex's birthday: March 15
- Preferred meeting time: 10:00-12:00
- Current project: Project Phoenix (deadline Q3 2024)
- Social media handles: @acmecorp on all platforms

## Important Decisions
- 2024-01-10: Switched from weekly to daily email digests
- 2024-03-05: Added social monitoring after PR crisis
"""
with open(f"{OPENCLAW_DIR}/workspace/MEMORY.md", "w") as f:
    f.write(memory_content)

# --- memory/*.md files ---
memory_files = {
    "project-phoenix.md": "# Project Phoenix\n\nDeadline: Q3 2024\nStatus: On track\nTeam: 5 engineers\n",
    "vendor-contacts.md": "# Vendor Contacts\n\nOpenAI: contact@openai.com\nAWS: aws-support@amazon.com\n",
    "meeting-notes-2024-05.md": "# Meeting Notes May 2024\n\n## 2024-05-15\n- Discussed Q2 roadmap\n- Social monitoring KPIs reviewed\n",
}
for fname, content in memory_files.items():
    with open(f"{OPENCLAW_DIR}/workspace/memory/{fname}", "w") as f:
        f.write(content)

# --- skills/social-monitor/ ---
social_monitor_skill = {
    "skill.json": json.dumps({
        "id": "social-monitor",
        "name": "Social Media Monitor",
        "version": "1.2.0",
        "description": "Monitors social media platforms for brand mentions",
        "platforms": ["weibo", "twitter", "linkedin"],
        "triggers": ["brand_mention", "negative_sentiment", "competitor_activity"]
    }, indent=2),
    "SKILL.md": "# Social Monitor Skill\n\nMonitors social platforms for Acme Corp mentions.\n\n## Commands\n- `monitor check` - Run immediate check\n- `monitor report` - Generate daily report\n",
    "monitor.py": "#!/usr/bin/env python3\n# Social monitoring script\nprint('Monitoring social platforms...')\n",
    "config.yaml": "platforms:\n  - weibo\n  - twitter\n  - linkedin\nkeywords:\n  - 'Acme Corp'\n  - 'AcmeCorp'\n  - '@acmecorp'\n",
}
for fname, content in social_monitor_skill.items():
    with open(f"{OPENCLAW_DIR}/workspace/skills/social-monitor/{fname}", "w") as f:
        f.write(content)

# --- skills/calendar/ ---
with open(f"{OPENCLAW_DIR}/workspace/skills/calendar/skill.json", "w") as f:
    json.dump({"id": "calendar", "name": "Calendar Manager", "version": "0.9.1"}, f, indent=2)
with open(f"{OPENCLAW_DIR}/workspace/skills/calendar/SKILL.md", "w") as f:
    f.write("# Calendar Skill\n\nManages calendar events and reminders.\n")

# --- skills/email-digest/ ---
with open(f"{OPENCLAW_DIR}/workspace/skills/email-digest/skill.json", "w") as f:
    json.dump({"id": "email-digest", "name": "Email Digest", "version": "1.0.3"}, f, indent=2)
with open(f"{OPENCLAW_DIR}/workspace/skills/email-digest/SKILL.md", "w") as f:
    f.write("# Email Digest Skill\n\nSummarizes and prioritizes emails.\n")

# --- Distractor files ---
with open(f"{OPENCLAW_DIR}/tmp/debug.log", "w") as f:
    f.write("[2024-05-30 10:00:01] INFO: Heartbeat triggered\n[2024-05-30 10:30:01] INFO: Social check complete\n")

with open(f"{OPENCLAW_DIR}/channels/slack-config.json", "w") as f:
    json.dump({"channel": "#ai-assistant", "format": "markdown"}, f, indent=2)

with open(f"{OPENCLAW_DIR}/agents/main/transcripts/2024-05-30.jsonl", "w") as f:
    f.write('{"role":"user","content":"Check today schedule","ts":"2024-05-30T09:00:00Z"}\n')
    f.write('{"role":"assistant","content":"You have 2 meetings today.","ts":"2024-05-30T09:00:01Z"}\n')

with open(f"{OPENCLAW_DIR}/workspace/logs/activity.log", "w") as f:
    f.write("2024-05-30: 42 tasks completed\n2024-05-31: 38 tasks completed\n")

print("Sandbox workspace generated successfully.")
print(f"OpenClaw home: {OPENCLAW_DIR}")