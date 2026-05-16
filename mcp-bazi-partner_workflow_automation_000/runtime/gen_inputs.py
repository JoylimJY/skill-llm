import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create a realistic deeply nested directory structure with distractor files
dirs = [
    "profiles/users/pending",
    "profiles/users/active",
    "profiles/templates",
    "config/system",
    "config/locales",
    "logs/2024",
    "logs/2025",
    "data/raw",
    "data/processed",
    "reports/monthly",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant
distractor_files = {
    "profiles/users/pending/user_0042.json": json.dumps({
        "user_id": "0042",
        "name": "张伟",
        "birth_date": "1990-07-15",
        "status": "pending_analysis",
        "notes": "Awaiting destiny profile"
    }, ensure_ascii=False, indent=2),

    "profiles/users/pending/user_0099.json": json.dumps({
        "user_id": "0099",
        "name": "李梅",
        "birth_date": "1993-11-03",
        "status": "incomplete",
        "notes": "Missing birth hour"
    }, ensure_ascii=False, indent=2),

    "profiles/users/active/user_0001.json": json.dumps({
        "user_id": "0001",
        "name": "王芳",
        "birth_date": "1988-02-28",
        "partner_type": "木系 · 某搭档",
        "status": "active"
    }, ensure_ascii=False, indent=2),

    "profiles/templates/default_profile.json": json.dumps({
        "version": "2.1",
        "template_type": "bazi_profile",
        "fields": ["year", "month", "day", "hour", "pattern", "partner"],
        "description": "Standard template for destiny analysis profiles"
    }, ensure_ascii=False, indent=2),

    "config/system/settings.yaml": """# System Configuration
version: "3.0"
locale: zh-CN
timezone: Asia/Shanghai
analysis_engine: zipping_method
default_status: 成格
soul_file: SOUL.md
""",

    "config/system/partners_registry.txt": """# Partner Type Registry (partial)
水系 · 铁壁回声
金系 · 铁壁回声
木系 · 顺流使者
火系 · 破局者
土系 · 稳锚者
# Full registry loaded from bazi engine
""",

    "config/locales/zh_CN.json": json.dumps({
        "patterns": {
            "七杀格": "Seven Killings Pattern",
            "伤官格": "Hurting Officer Pattern",
            "印格": "Seal Pattern",
            "食神格": "Eating God Pattern",
            "财格": "Wealth Pattern",
            "正官格": "Direct Officer Pattern"
        },
        "sub_patterns": {
            "煞印相生": "Kill-Seal Mutual Generation",
            "煞邀食制": "Kill restrained by Eating God",
            "财旺生官": "Wealth Generates Officer"
        }
    }, ensure_ascii=False, indent=2),

    "logs/2025/analysis_log.txt": """2025-01-10 09:23:11 INFO  bazi_analyze called for user_0001
2025-01-10 09:23:12 INFO  Pattern determined: 印格
2025-01-10 09:23:13 INFO  Sub-pattern: 印绶用官
2025-01-10 09:23:14 INFO  bazi_partner matched: 木系 · 顺流使者
2025-01-10 09:23:15 INFO  bazi_apply_prompt executed successfully
""",

    "logs/2024/errors.txt": """2024-12-01 ERROR bazi_partner: unknown sub_type '食神格'
2024-12-02 ERROR SOUL.md write failed: permission denied
2024-12-03 WARN  hour=-1 used, accuracy may be reduced
""",

    "data/raw/birth_records_batch_7.csv": """user_id,name,year,month,day,hour
0043,陈刚,1985,3,22,11
0044,孙丽,1992,8,14,7
0045,赵强,1978,12,31,23
0046,周敏,2000,6,6,0
""",

    "data/processed/analysis_results.jsonl": '{"user_id":"0043","status":"queued","pattern":null}\n{"user_id":"0044","status":"queued","pattern":null}\n',

    "reports/monthly/2025_01_summary.txt": """Monthly Destiny Analysis Summary - January 2025
Total analyses requested: 47
Completed: 31
Pending: 16
Most common L1 pattern: 印格
Partner type distribution:
  木系: 8
  水系: 7
  金系: 6
  火系: 5
  土系: 5
""",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# The target user record - this is the one the agent needs to process
target_user = {
    "user_id": "0043",
    "name": "陈刚",
    "year": 1985,
    "month": 3,
    "day": 22,
    "hour": 11,
    "request": "请为本用户完成八字命理排盘分析并激活专属搭档人格",
    "status": "awaiting_processing"
}

(workspace / "data/raw/target_user_0043.json").write_text(
    json.dumps(target_user, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

# An incomplete/wrong SOUL.md to make the task about REPLACING/OVERWRITING it
wrong_soul = """# SOUL.md
## AI Identity

This is a placeholder. No partner personality has been configured yet.

system_prompt: ""
partner_type: ""
"""
(workspace / "SOUL.md").write_text(wrong_soul, encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Files created: {len(distractor_files) + 2}")
print("Target: data/raw/target_user_0043.json (陈刚, 1985-03-22 11:00)")
print("SOUL.md: placeholder (needs to be overwritten with real partner profile)")