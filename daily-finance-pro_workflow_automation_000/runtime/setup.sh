#!/bin/bash
set -e

# Create the mock openclaw CLI that records all commands and simulates behavior
cat > /usr/local/bin/openclaw << 'OPENCLAW_EOF'
#!/usr/bin/env python3
import sys
import json
import os
from datetime import datetime

LOG_FILE = "/workspace/openclaw_command_log.json"

def load_log():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"commands": [], "cron_jobs": {}}

def save_log(data):
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    args = sys.argv[1:]
    log = load_log()
    
    # Record the full command
    cmd_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "args": args,
        "raw_command": "openclaw " + " ".join(args)
    }
    
    if len(args) >= 2 and args[0] == "cron" and args[1] == "add":
        # Parse cron add arguments
        parsed = {}
        i = 2
        while i < len(args):
            if args[i].startswith("--") and i+1 < len(args):
                key = args[i][2:]
                val = args[i+1]
                parsed[key] = val
                i += 2
            else:
                i += 1
        
        cmd_record["subcommand"] = "cron_add"
        cmd_record["parsed_params"] = parsed
        
        job_name = parsed.get("name", "unknown")
        log["cron_jobs"][job_name] = {
            "params": parsed,
            "created_at": datetime.utcnow().isoformat()
        }
        
        print(f"✅ 定时任务已创建: {job_name}")
        print(f"   计划: {parsed.get('schedule', 'N/A')}")
        print(f"   频道: {parsed.get('channel', 'N/A')}")
        print(f"   消息: {parsed.get('message', 'N/A')}")
    
    elif len(args) >= 2 and args[0] == "cron" and args[1] == "run":
        # cron run with --preview
        job_name = args[2] if len(args) > 2 else "unknown"
        is_preview = "--preview" in args
        
        cmd_record["subcommand"] = "cron_run"
        cmd_record["job_name"] = job_name
        cmd_record["preview"] = is_preview
        
        if job_name in log["cron_jobs"]:
            job = log["cron_jobs"][job_name]
            print(f"🔍 预览模式: {job_name}")
            print(f"   下次运行时间 (UTC): {job['params'].get('schedule', 'N/A')}")
            print(f"   推送频道: {job['params'].get('channel', 'N/A')}")
            print(f"   [PREVIEW] 推送内容模拟发送成功")
        else:
            print(f"⚠️  任务不存在: {job_name}")
            print(f"   可用任务: {list(log['cron_jobs'].keys())}")
    
    elif len(args) >= 2 and args[0] == "cron" and args[1] == "rm":
        job_name = args[2] if len(args) > 2 else "unknown"
        cmd_record["subcommand"] = "cron_rm"
        cmd_record["job_name"] = job_name
        
        if job_name in log["cron_jobs"]:
            del log["cron_jobs"][job_name]
            print(f"🗑️  任务已删除: {job_name}")
        else:
            print(f"⚠️  任务不存在: {job_name}")
    
    elif len(args) >= 2 and args[0] == "cron" and args[1] == "ls":
        cmd_record["subcommand"] = "cron_ls"
        print("📋 当前定时任务列表:")
        for name, job in log["cron_jobs"].items():
            print(f"  - {name}: {job['params'].get('schedule','N/A')} -> {job['params'].get('channel','N/A')}")
    
    else:
        cmd_record["subcommand"] = "unknown"
        print(f"openclaw: unknown command '{' '.join(args)}'")
    
    log["commands"].append(cmd_record)
    save_log(log)

if __name__ == "__main__":
    main()
OPENCLAW_EOF

chmod +x /usr/local/bin/openclaw

# Initialize the command log
python3 -c "
import json
with open('/workspace/openclaw_command_log.json', 'w', encoding='utf-8') as f:
    json.dump({'commands': [], 'cron_jobs': {}}, f, ensure_ascii=False, indent=2)
"

echo "Mock openclaw CLI installed and ready."
echo "Command log initialized at /workspace/openclaw_command_log.json"