import os
import json
import random

random.seed(42)

BASE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "references",
    "scripts",
    "logs/2024/jan",
    "logs/2024/feb",
    "configs/channels",
    "configs/alerts",
    "reports/weekly",
    "reports/monthly",
    "incidents/INC-2041",
    "incidents/INC-2042",
    "team/oncall",
    "team/escalation",
    "monitoring/thresholds",
    "monitoring/exporters",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# ── SKILL.md and references/channels.md ─────────────────────────────────────
skill_md = """---
name: cross-platform-messenger-claw
description: "跨渠道消息推送与联络协调。"
---

# 跨平台消息联络虾

## 核心能力

通过 OpenClaw CLI `openclaw message` 命令，向 20+ 通讯渠道发送文本消息和媒体附件。

### 单条推送

```bash
openclaw message send --channel <渠道> --target <目标> --message "<消息>"
```

带附件：
```bash
openclaw message send --channel <渠道> --target <目标> --message "<消息>" --media <路径或URL>
```

### 广播/群发

```bash
openclaw message broadcast --channel <渠道> --targets <目标1> <目标2> ... --message "<消息>"
```

或使用 `scripts/notify.sh` 从文件批量推送：
```bash
./scripts/notify.sh --channel <渠道> --message "<消息>" < targets.txt
```

## 渠道参考

各渠道的 `--channel` 值和 `--target` 格式见 [references/channels.md](references/channels.md)。

**最常用渠道速查：**

| 场景 | 命令 |
|------|------|
| 飞书用户 | `--channel feishu --target ou_xxx` |
| 飞书群 | `--channel feishu --target oc_xxx` |
| WhatsApp | `--channel whatsapp --target +86138xxxx` |
| Telegram | `--channel telegram --target @username` |
| Discord 频道 | `--channel discord --target channel:<id>` |
| Slack 频道 | `--channel slack --target #channel_name` |

## 注意事项

- 各渠道有频率限制，群发时注意间隔
- 媒体文件建议 < 30MB
- `--dry-run` 可用于测试而不实际发送
- 发送失败时检查目标格式和渠道配置
"""

channels_md = """# 跨平台渠道参考

## OpenClaw 支持的渠道

| 渠道 | `--channel` 值 | 目标格式 |
|------|---------------|----------|
| 飞书 | `feishu` | 用户 open_id 或群 chat_id |
| WhatsApp | `whatsapp` | E.164 号码（如 `+8613800138000`） |
| Telegram | `telegram` | chat id 或 @username |
| Discord | `discord` | 频道/user ID |
| Slack | `slack` | 频道/user ID |
| Signal | `signal` | E.164 号码 |
| iMessage | `imessage` | Apple ID / 手机号 |
| Line | `line` | 用户/群 ID |
| Google Chat | `googlechat` | 空间/线程 ID |
| MS Teams | `msteams` | 频道/用户 ID |
| Matrix | `matrix` | 房间/user ID |
| Mattermost | `mattermost` | 频道 ID |
| IRC | `irc` | 频道/用户 |
| Nostr | `nostr` | npub hex |
| Nextcloud Talk | `nextcloud-talk` | 会话 token |
| Synology Chat | `synology-chat` | 频道 ID |
| Tlon | `tlon` | 船/终端 ID |
| Zalo | `zalo` | 用户 ID |
| BlueBubbles | `bluebubbles` | chat GUID / 手机号 |

## 消息类型支持

- **纯文本**：所有渠道均支持
- **媒体附件**：`--media` 参数支持图片、音频、视频、文档
- **静默发送**：`--silent`（Telegram + Discord）
- **引用回复**：`--reply-to <message-id>`
- **按钮/卡片**：`--buttons`（Telegram）、`--card`（Adaptive Card）、`--components`（Discord）

## 跨渠道注意事项

1. **飞书**：target 使用 `ou_` 开头的 open_id 或 `oc_` 开头的 chat_id
2. **WhatsApp**：target 必须是 E.164 格式，带国际区号
3. **Telegram**：群组使用负数 chat_id
4. **Discord**：频道目标格式 `channel:<snowflake_id>`
5. **Slack**：频道目标使用 `#channel_name` 或 channel ID
6. **Markdown 支持**：各渠道对 Markdown 的支持程度不同；飞书/Discord/Slack 较完善，WhatsApp 不支持
7. **媒体大小**：各渠道有不同限制，建议附件 < 30MB
8. **速率限制**：群发时注意各渠道的频率限制，建议间隔 1-2 秒
"""

with open(os.path.join(BASE, "SKILL.md"), "w") as f:
    f.write(skill_md)

with open(os.path.join(BASE, "references", "channels.md"), "w") as f:
    f.write(channels_md)

# ── INCIDENT BRIEF (the task input) ─────────────────────────────────────────
# This is intentionally messy: raw/un-prefixed IDs, phone without country code
incident_brief = """\
INCIDENT INC-2042 — Production Database Cluster Failure
==========================================================
Severity: P0
Detected: 2024-06-15 03:17 UTC
Affected: payments-db-primary, payments-db-replica-1

Alert message to send (exact text):
  [P0 ALERT] INC-2042: payments-db cluster DOWN. Immediate action required. Failover initiated. ETA 15 min.

Notification targets
--------------------
Channel: Feishu (group chat)
  Raw group ID: c_9f3a2b1d7e04  ← this is the raw ID portion, needs correct prefix

Channel: Discord (engineering alerts channel)
  Raw snowflake ID: 987654321098765432
  Note: send silently (do not notify members with a ping sound)

Channel: Telegram (SRE on-call group)
  Raw group ID: 1001234567890
  Note: this is a GROUP, not a private chat; send silently

Channel: WhatsApp (escalation contact)
  Phone: 13912345678  ← missing country code (China +86)

Channel: Slack (incidents channel)
  Channel name: incidents
"""

with open(os.path.join(BASE, "incidents", "INC-2042", "brief.txt"), "w") as f:
    f.write(incident_brief)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "configs/channels/feishu_legacy.json": json.dumps({
        "channel": "feishu", "webhook": "https://open.feishu.cn/old_hook",
        "token": "EXPIRED_TOKEN_XYZ", "note": "deprecated, do not use"
    }, indent=2),

    "configs/alerts/pagerduty_rules.yaml": """\
rules:
  - severity: P0
    route: pagerduty
  - severity: P1
    route: email
""",

    "configs/alerts/thresholds.json": json.dumps({
        "cpu_alert": 90, "mem_alert": 85, "disk_alert": 95
    }, indent=2),

    "logs/2024/jan/system.log": "\n".join([
        f"2024-01-{d:02d} INFO: Health check passed" for d in range(1, 32)
    ]),

    "logs/2024/feb/system.log": "\n".join([
        f"2024-02-{d:02d} WARN: Latency spike detected p99=450ms" for d in range(1, 29)
    ]),

    "team/oncall/rotation.csv": """\
week,primary,secondary,phone
2024-W24,alice,bob,alice_phone_internal
2024-W25,charlie,diana,charlie_phone_internal
2024-W26,eve,frank,eve_phone_internal
""",

    "team/escalation/contacts.txt": """\
L1: SRE Team (Slack #incidents, Feishu group)
L2: Platform Lead - alice@company.com
L3: CTO - escalation only after 30min unresolved
""",

    "reports/weekly/week24_summary.md": """\
# Week 24 Summary
- Total incidents: 3
- P0: 0, P1: 1, P2: 2
- MTTR: 42 min average
""",

    "reports/monthly/may_report.json": json.dumps({
        "month": "2024-05",
        "uptime_pct": 99.87,
        "incidents": 7,
        "top_cause": "network partition"
    }, indent=2),

    "monitoring/thresholds/db_thresholds.yaml": """\
connection_pool_max: 500
query_timeout_ms: 3000
replication_lag_alert_s: 30
""",

    "monitoring/exporters/prometheus_config.yaml": """\
scrape_configs:
  - job_name: payments-db
    static_configs:
      - targets: ['payments-db-primary:9187', 'payments-db-replica-1:9187']
""",

    "incidents/INC-2041/brief.txt": """\
INCIDENT INC-2041 — API Gateway Timeout Storm
Severity: P1
Resolved: 2024-06-12 11:45 UTC
Root cause: misconfigured circuit breaker timeout (50ms too low)
""",

    "scripts/check_db.sh": """\
#!/bin/bash
# Checks DB replication lag
psql -h payments-db-primary -c "SELECT now() - pg_last_xact_replay_timestamp() AS lag;"
""",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ── notify.sh stub ───────────────────────────────────────────────────────────
notify_sh = """\
#!/bin/bash
# Reads targets line by line from stdin, sends message to each via openclaw
CHANNEL=""
MESSAGE=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --channel) CHANNEL="$2"; shift ;;
        --message) MESSAGE="$2"; shift ;;
    esac
    shift
done
while IFS= read -r target; do
    openclaw message send --channel "$CHANNEL" --target "$target" --message "$MESSAGE"
done
"""
with open(os.path.join(BASE, "scripts", "notify.sh"), "w") as f:
    f.write(notify_sh)

print("Workspace generated successfully.")