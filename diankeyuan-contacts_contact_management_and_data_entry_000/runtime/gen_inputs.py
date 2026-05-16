import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create realistic distractor files ---
distractor_dirs = [
    workspace / "archive" / "2024",
    workspace / "archive" / "2025",
    workspace / "reports" / "q1",
    workspace / "reports" / "q2",
    workspace / "meetings" / "notes",
    workspace / "hr" / "old_rosters",
    workspace / "hr" / "templates",
    workspace / "config",
    workspace / "logs",
    workspace / "temp",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "archive" / "2024" / "contacts_backup.json": json.dumps({"note": "archived 2024 data, do not use"}),
    workspace / "archive" / "2025" / "old_staff.csv": "姓名,科室,职务\n张三,系统所,工程师\n李四,继电所,主任",
    workspace / "reports" / "q1" / "summary.txt": "Q1季度报告摘要，无人员变动",
    workspace / "reports" / "q2" / "summary.txt": "Q2季度报告摘要，人员有所调整",
    workspace / "meetings" / "notes" / "2025-01-15.txt": "会议记录：讨论了新人入职事项",
    workspace / "meetings" / "notes" / "2025-02-20.txt": "会议记录：科室调整方案审议",
    workspace / "hr" / "old_rosters" / "2023_roster.csv": "姓名,科室\n王五,系统所\n赵六,试验所",
    workspace / "hr" / "templates" / "staff_template.xlsx": "FAKE_EXCEL_BINARY",
    workspace / "config" / "app_config.ini": "[database]\npath=/tmp/db.sqlite\nhost=localhost",
    workspace / "logs" / "access.log": "2025-01-01 09:00:00 INFO system started\n2025-01-01 09:05:12 INFO user login",
    workspace / "temp" / "scratch.txt": "临时笔记，待整理",
    workspace / "config" / "settings.json": json.dumps({"theme": "dark", "language": "zh-CN"}),
}

for path, content in distractor_files.items():
    path.write_text(content, encoding="utf-8")

# --- Create the main task input: a messy roster memo ---
roster_memo = """
电科院新增人员通知单
发文日期：2026-03-10
经人力资源部审核，以下人员信息需录入联系人系统：

【系统所 - 二次评估室】 办公室：1512
1. 张磊，职务：高级工程师
2. 陈小燕，职务：市场专员
3. 刘强，职务：实习生  （注：此条为误录，请勿录入，若已录入请删除）

【继电所 - 保护研究室】 办公室：806
4. 吴海涛，职务：研究员
5. 周敏，职务：工程师

【试验所 - 电气试验室】 办公室：302
6. 赵宇，职务：技术员
7. 林建国，职务：副主任

补充说明：
- 张磊的办公室实际是1516（非1512），请以此为准录入。
- 周敏的职务应为"高级工程师"，非"工程师"。
"""

(workspace / "hr" / "new_staff_notice.txt").write_text(roster_memo, encoding="utf-8")

# --- Create a correction memo ---
correction_memo = """
更正通知（2026-03-11）
1. 系统所 - 二次评估室 张磊 的办公室号应为 1516，非 1512，请修正。
2. 继电所 - 保护研究室 周敏 的职务更正为 高级工程师。
"""
(workspace / "hr" / "correction_memo.txt").write_text(correction_memo, encoding="utf-8")

# --- Ensure the target directory does NOT pre-exist (agent must create it) ---
target_dir = Path("/Users/aibin/.openclaw/workspace")
target_dir.mkdir(parents=True, exist_ok=True)
# Do NOT create the JSON file; the agent must create it fresh
target_json = target_dir / "diankeyuan_contacts.json"
if target_json.exists():
    target_json.unlink()

print("Workspace and inputs generated successfully.")
print(f"Roster file: {workspace / 'hr' / 'new_staff_notice.txt'}")
print(f"Target JSON path: {target_json}")