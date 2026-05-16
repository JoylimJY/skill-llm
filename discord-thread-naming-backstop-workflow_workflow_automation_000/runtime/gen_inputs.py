import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "ops/discord/hooks",
    "ops/discord/logs",
    "ops/discord/archive",
    "ops/notifications/templates",
    "ops/notifications/sent",
    "ops/cron/jobs",
    "ops/cron/history",
    "config/guild",
    "config/channels",
    "scripts/utils",
    "scripts/validators",
    "docs/runbooks",
    "docs/sop",
    "monitoring/alerts",
    "monitoring/dashboards",
    "references",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files

# 1. Old backstop run log (historical, should not be overwritten)
old_log = {
    "run_date": "2026-03-13",
    "threads_processed": 2,
    "threads": [
        {"id": "1482100000000000001", "action": "renamed", "new_name": "【任务】数据迁移测试 - 20260313"},
        {"id": "1482100000000000002", "action": "renamed", "new_name": "【文档】API接口规范更新 - 20260313"},
    ]
}
with open(os.path.join(workspace, "ops/discord/logs/backstop_run_2026-03-13.json"), "w") as f:
    json.dump(old_log, f, ensure_ascii=False, indent=2)

# 2. Naming convention doc (distractor)
with open(os.path.join(workspace, "docs/sop/thread-naming-convention.md"), "w") as f:
    f.write("# Thread Naming Convention\n\nUse format: 【Type】Target - YYYYMMDD\n\nDo not use raw message content as thread name.\n")

# 3. Channel config (distractor)
channel_cfg = {
    "guild_id": "1478785964896817267",
    "channels": [
        {"id": "1478785965580357754", "name": "🎛️丨dispatch", "type": "text"},
        {"id": "1478996389727043584", "name": "🔔丨alerts", "type": "text"},
    ]
}
with open(os.path.join(workspace, "config/channels/channel_map.json"), "w") as f:
    json.dump(channel_cfg, f, ensure_ascii=False, indent=2)

# 4. Old cron history (distractor)
cron_history = [
    {"job": "discord-backstop", "last_run": "2026-03-13T10:30:00+08:00", "status": "ok", "threads_renamed": 2},
    {"job": "discord-backstop", "last_run": "2026-03-13T10:10:00+08:00", "status": "ok", "threads_renamed": 0},
]
with open(os.path.join(workspace, "ops/cron/history/backstop_cron_history.json"), "w") as f:
    json.dump(cron_history, f, ensure_ascii=False, indent=2)

# 5. Notification templates (distractor reference)
with open(os.path.join(workspace, "references/dispatch-thread-rename-notification-templates.md"), "w") as f:
    f.write("# Notification Templates\n\nSee SKILL.md for P2 and RESOLVED templates.\n\nTarget channel: 1478996389727043584\n")

# 6. Script utils (distractor)
with open(os.path.join(workspace, "scripts/utils/timezone_helper.py"), "w") as f:
    f.write("import pytz\nfrom datetime import datetime\n\ndef now_shanghai():\n    tz = pytz.timezone('Asia/Shanghai')\n    return datetime.now(tz)\n")

# 7. Validator (distractor)
with open(os.path.join(workspace, "scripts/validators/name_validator.py"), "w") as f:
    f.write("import re\nPATTERN = r'^【[^】]+】.+ - \\d{8}$'\n\ndef is_valid(name):\n    return bool(re.match(PATTERN, name))\n")

# 8. Guild config
guild_cfg = {"guild_id": "1478785964896817267", "name": "OpenClaw Ops", "region": "singapore"}
with open(os.path.join(workspace, "config/guild/guild_config.json"), "w") as f:
    json.dump(guild_cfg, f, ensure_ascii=False, indent=2)

# 9. Monitoring alert rules (distractor)
with open(os.path.join(workspace, "monitoring/alerts/discord_bot_alerts.yaml"), "w") as f:
    f.write("alerts:\n  - name: bot_offline\n    threshold: 5m\n    severity: P1\n  - name: rename_failure\n    threshold: 3\n    severity: P2\n")

# 10. Dashboard config (distractor)
with open(os.path.join(workspace, "monitoring/dashboards/ops_dashboard.json"), "w") as f:
    json.dump({"title": "Discord Ops Dashboard", "panels": ["thread_rename_rate", "p2_alerts", "cron_success"]}, f)

# 11. Archive of old thread names (distractor)
with open(os.path.join(workspace, "ops/discord/archive/renamed_threads_march.csv"), "w") as f:
    f.write("threadId,old_name,new_name,date\n")
    f.write("1482100000000000001,数据迁移，帮我搞一下,【任务】数据迁移测试,2026-03-13\n")
    f.write("1482100000000000002,关于API文档的内容.md,【文档】API接口规范更新,2026-03-13\n")

# 12. Hook config (distractor)
hook_cfg = {
    "prehook": "discord-thread-naming-prehook",
    "backstop": "discord-thread-naming-backstop",
    "schedule": "every 20 minutes",
    "max_threads_per_run": 3,
}
with open(os.path.join(workspace, "ops/discord/hooks/hook_config.json"), "w") as f:
    json.dump(hook_cfg, f, ensure_ascii=False, indent=2)

# 13. Failed notifications log (distractor)
with open(os.path.join(workspace, "ops/notifications/sent/failed_p2_log.json"), "w") as f:
    json.dump([], f)

# 14. Write the mock server script
mock_server_code = '''#!/usr/bin/env python3
"""
Mock Discord API server for backstop task evaluation.
Reference time: 2026-03-14 10:40 Asia/Shanghai (UTC 02:40)
"""

import json
import os
import threading
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

LOG_FILE = "/workspace/mock_server_requests.jsonl"
log_lock = threading.Lock()

# Reference time: 2026-03-14 10:40:00 Asia/Shanghai = 2026-03-14 02:40:00 UTC
REF_TIME_UTC = datetime(2026, 3, 14, 2, 40, 0, tzinfo=timezone.utc)

# Track channel-edit call counts per thread id
edit_call_counts = {}
edit_lock = threading.Lock()

THREADS = [
    {
        "id": "1482300000000000001",
        "name": '{"action":"deploy","service":"nginx","env":"prod","version":"1.2.3"}',
        "parent_id": "1478785965580357754",
        "thread_metadata": {
            "create_timestamp": "2026-03-14T02:28:00+00:00"
        }
    },
    {
        "id": "1482300000000000002",
        "name": "帮我写一个关于系统监控告警规则配置的完整文档说明，包括所有参数和使用场景",
        "parent_id": "1478785965580357754",
        "thread_metadata": {
            "create_timestamp": "2026-03-14T02:35:00+00:00"
        }
    },
    {
        "id": "1482300000000000003",
        "name": "【修复】OAuth登录异常 - 20260314",
        "parent_id": "1478785965580357754",
        "thread_metadata": {
            "create_timestamp": "2026-03-14T01:15:00+00:00"
        }
    },
    {
        "id": "1482300000000000004",
        "name": "fix bug in auth module",
        "parent_id": "1478785965580357754",
        "thread_metadata": {
            "create_timestamp": "2026-03-13T14:00:00+00:00"
        }
    },
    {
        "id": "1482300000000000005",
        "name": "【任务】用户权限审查 - 20260314",
        "parent_id": "1478785965580357754",
        "thread_metadata": {
            "create_timestamp": "2026-03-14T02:22:00+00:00"
        }
    },
    {
        "id": "1482300000000000006",
        "name": "请你帮我分析一下当前报错异常的根本原因，另外关于修复方案也请一并给出详细建议",
        "parent_id": "1478785965580357754",
        "thread_metadata": {
            "create_timestamp": "2026-03-14T01:50:00+00:00"
        }
    },
]

thread_current_names = {t["id"]: t["name"] for t in THREADS}

def log_request(entry):
    with log_lock:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\\n")

@app.route("/discord-action", methods=["POST"])
def discord_action():
    data = request.get_json(force=True)
    action = data.get("action", "")
    
    log_request(data)
    
    if action == "thread-list":
        guild_id = data.get("guildId", "")
        channel_id = data.get("channelId", "")
        include_archived = data.get("includeArchived", True)
        limit = data.get("limit", 100)
        
        threads_out = []
        for t in THREADS:
            if t["parent_id"] == channel_id:
                threads_out.append(t)
        
        return jsonify({"ok": True, "threads": threads_out[:limit]})
    
    elif action == "channel-edit":
        thread_id = data.get("target", "")
        new_name = data.get("name", "")
        
        with edit_lock:
            count = edit_call_counts.get(thread_id, 0)
            edit_call_counts[thread_id] = count + 1
            current_count = count + 1
        
        # Thread 1482300000000000001: fail on first attempt, succeed on second
        if thread_id == "1482300000000000001":
            if current_count == 1:
                log_request({"_mock_note": f"channel-edit FAIL attempt {current_count} for {thread_id}"})
                return jsonify({"ok": False, "error": "Internal Server Error", "code": 500}), 500
            else:
                thread_current_names[thread_id] = new_name
                log_request({"_mock_note": f"channel-edit SUCCESS attempt {current_count} for {thread_id}"})
                return jsonify({"ok": True, "id": thread_id, "name": new_name})
        else:
            thread_current_names[thread_id] = new_name
            return jsonify({"ok": True, "id": thread_id, "name": new_name})
    
    elif action == "channel-info":
        thread_id = data.get("target", "")
        name = thread_current_names.get(thread_id, "unknown")
        return jsonify({"ok": True, "id": thread_id, "name": name})
    
    elif action == "send-message":
        channel_id = data.get("channelId", "")
        content = data.get("content", "")
        return jsonify({"ok": True, "channel": channel_id, "content": content})
    
    else:
        return jsonify({"ok": False, "error": f"Unknown action: {action}"}), 400

if __name__ == "__main__":
    open(LOG_FILE, "w").close()
    app.run(host="0.0.0.0", port=7788, debug=False)
'''

with open(os.path.join(workspace, "mock_discord_server.py"), "w") as f:
    f.write(mock_server_code)

# 15. Write a task description file that the agent reads
task_spec = {
    "task": "discord-thread-naming-backstop",
    "description": "Run the backstop naming inspection for the dispatch channel. Fix any non-compliant thread names. Log results to backstop_run_log.json.",
    "discord_api_endpoint": "http://localhost:7788/discord-action",
    "reference_time_shanghai": "2026-03-14 10:40",
    "output_file": "backstop_run_log.json",
    "skill": "discord-thread-naming-backstop-workflow"
}
with open(os.path.join(workspace, "task_spec.json"), "w") as f:
    json.dump(task_spec, f, ensure_ascii=False, indent=2)

print("Workspace generated successfully.")