import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Deep distractor directory structure ──────────────────────────────────────
dirs = [
    "tasks/archive",
    "tasks/pending",
    "tasks/completed",
    "config/alerts",
    "config/schedules",
    "logs/2026-03",
    "logs/2026-04",
    "scripts/utils",
    "scripts/cron",
    "data/flights/raw",
    "data/flights/processed",
    "references",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files (messy, incomplete, misleading)
distractors = {
    "tasks/archive/task_old_001.json": json.dumps({
        "taskId": "old_001",
        "status": "expired",
        "from": "上海",
        "to": "广州",
        "date": "2026-01-10",
        "basePrice": 620,
        "selectedFlights": [],
        "thresholdPercent": 10,
        "thresholdAmount": 200,
    }, ensure_ascii=False, indent=2),

    "tasks/completed/task_002.json": json.dumps({
        "taskId": "002",
        "status": "completed",
        "from": "北京",
        "to": "深圳",
        "date": "2026-03-20",
        "basePrice": 900,
        "selectedFlights": [
            {"flightNo": "CA1803", "price": 900, "airline": "国航",
             "isBaseFlight": True, "jumpUrl": "https://a.feizhu.com/ca1803"}
        ],
        "thresholdPercent": 15,
        "thresholdAmount": 300,
    }, ensure_ascii=False, indent=2),

    "config/alerts/dingtalk_config.json": json.dumps({
        "webhook": "https://oapi.dingtalk.com/robot/send?access_token=PLACEHOLDER",
        "secret": "PLACEHOLDER",
        "enabled": False,
    }, ensure_ascii=False, indent=2),

    "config/schedules/cron_template.txt": (
        "# Cron schedule template\n"
        "# Default: every day at 09:00\n"
        "0 9 * * * /usr/bin/node /workspace/scripts/check_prices.js\n"
    ),

    "logs/2026-04/monitor_20260401.log": (
        "[2026-04-01 09:00:01] Checking task 002 - price stable\n"
        "[2026-04-01 09:00:03] Task 002 expired, skipping\n"
    ),

    "logs/2026-04/monitor_20260402.log": (
        "[2026-04-02 09:00:01] No active tasks\n"
    ),

    "scripts/utils/price_formatter.js": (
        "// Utility: format price changes\n"
        "function formatDiff(current, base) {\n"
        "  const diff = current - base;\n"
        "  const pct = ((diff / base) * 100).toFixed(1);\n"
        "  return `${diff > 0 ? '+' : ''}${diff}(${pct}%)`;\n"
        "}\n"
        "module.exports = { formatDiff };\n"
    ),

    "scripts/cron/heartbeat.sh": (
        "#!/bin/bash\n"
        "# Heartbeat script for OpenClaw\n"
        "echo 'heartbeat: ok'\n"
    ),

    "data/flights/raw/sample_response_old.json": json.dumps({
        "flights": [
            {"flightNo": "MU1001", "airline": "东航", "price": 750,
             "departure": "07:00", "arrival": "09:30", "type": "direct"},
        ]
    }, ensure_ascii=False, indent=2),

    "data/flights/processed/bj_sh_20260310.json": json.dumps({
        "route": "北京-上海",
        "date": "2026-03-10",
        "lowestPrice": 450,
        "flights": 5,
    }, ensure_ascii=False, indent=2),

    "scripts/utils/validate_task.py": (
        "# Task validation stub\n"
        "def validate(task):\n"
        "    required = ['taskId','from','to','date','selectedFlights']\n"
        "    return all(k in task for k in required)\n"
    ),
}

for relpath, content in distractors.items():
    p = workspace / relpath
    p.write_text(content, encoding="utf-8")

# ── Core Input: raw flight search result (as if returned by the CLI) ──────────
# This simulates the raw output from: flyai flight search --from 北京 --to 成都 --date 2026-05-01 --type direct --json
# The agent must use this data to build a monitoring task
raw_flight_data = {
    "flights": [
        {
            "flightNo": "CA4101",
            "airline": "中国国航",
            "departure": "08:30",
            "arrival": "11:15",
            "duration": "2h45m",
            "price": 680,
            "type": "direct",
            "available": True,
            "depStation": "首都",
            "arrStation": "双流",
            "jumpUrl": "https://a.feizhu.com/ca4101abc"
        },
        {
            "flightNo": "3U8501",
            "airline": "四川航空",
            "departure": "10:00",
            "arrival": "12:50",
            "duration": "2h50m",
            "price": 650,
            "type": "direct",
            "available": True,
            "depStation": "首都",
            "arrStation": "双流",
            "jumpUrl": "https://a.feizhu.com/3u8501def"
        },
        {
            "flightNo": "MU2301",
            "airline": "中国东航",
            "departure": "13:20",
            "arrival": "16:05",
            "duration": "2h45m",
            "price": 720,
            "type": "direct",
            "available": True,
            "depStation": "首都",
            "arrStation": "双流",
            "jumpUrl": "https://a.feizhu.com/mu2301ghi"
        },
        {
            "flightNo": "ZH9201",
            "airline": "深圳航空",
            "departure": "18:00",
            "arrival": "20:55",
            "duration": "2h55m",
            "price": 590,
            "type": "direct",
            "available": True,
            "depStation": "大兴",
            "arrStation": "双流",
            "jumpUrl": "https://a.feizhu.com/zh9201jkl"
        },
        {
            "flightNo": "HU7601",
            "airline": "海南航空",
            "departure": "20:40",
            "arrival": "23:30",
            "duration": "2h50m",
            "price": 610,
            "type": "direct",
            "available": True,
            "depStation": "首都",
            "arrStation": "双流",
            "jumpUrl": "https://a.feizhu.com/hu7601mno"
        }
    ]
}

(workspace / "data/flights/raw/bj_cd_20260501_raw.json").write_text(
    json.dumps(raw_flight_data, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

# ── Core Input 2: Price history snapshots to evaluate ────────────────────────
# These represent three subsequent daily price checks across the monitored flights
# The agent must determine which checks should have triggered alerts
price_snapshots = [
    {
        "checkDate": "2026-04-10T09:00:00+08:00",
        "day": 1,
        "prices": {
            "3U8501": 615,   # slight drop from 650: -35 (5.4%) - below both thresholds, no alert
            "CA4101": 680,   # unchanged
            "MU2301": 720,   # unchanged
        }
    },
    {
        "checkDate": "2026-04-11T09:00:00+08:00",
        "day": 2,
        "prices": {
            "3U8501": 440,   # drop from 650: -210 (32.3%) - exceeds BOTH thresholds -> ALERT
            "CA4101": 660,   # slight drop from 680: -20 (2.9%) - no alert
            "MU2301": 750,   # slight rise from 720: +30 (4.2%) - no alert
        }
    },
    {
        "checkDate": "2026-04-12T09:00:00+08:00",
        "day": 3,
        "prices": {
            "3U8501": 430,   # further drop - but 24h rule: lastAlertAt was day 2 -> no new alert
            "CA4101": 450,   # drop from 680: -230 (33.8%) - NEW alert candidate, different flight
            "MU2301": 900,   # rise from 720: +180 (25%) - exceeds BOTH rise thresholds -> ALERT
        }
    }
]

(workspace / "data/flights/processed/price_snapshots_bj_cd.json").write_text(
    json.dumps(price_snapshots, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

# ── Task briefing (business context, not hints) ──────────────────────────────
briefing = {
    "project": "BeijingChengdu Price Watch",
    "context": "Launch monitoring for Beijing to Chengdu on 2026-05-01",
    "createdAt": "2026-04-09T11:00:00+08:00",
    "requester": "ops-team",
    "taskId_to_assign": "003",
    "notes": "Use default monitoring settings. Standard 7-day watch period."
}

(workspace / "tasks/pending/briefing_003.json").write_text(
    json.dumps(briefing, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")