import os
import random
import json
import sqlite3
import time
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create deeply nested distractor directory structure
dirs = [
    "scripts",
    "logs/archive/2024",
    "logs/archive/2025",
    "logs/current",
    "config/email",
    "config/reminders",
    "data/raw",
    "data/processed",
    "reports/monthly",
    "reports/weekly",
    "backup/scripts",
    "backup/data",
    "tests/unit",
    "tests/integration",
    "docs/internal",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files with realistic content
distractor_files = {
    "logs/archive/2024/fetch_emails.log": "2024-03-01 09:00:00 INFO: fetch_emails.sh started\n2024-03-01 09:00:01 INFO: Found 5 emails\n",
    "logs/archive/2024/reminders.log": "2024-03-01 09:00:02 INFO: Created 2 reminders\n",
    "logs/archive/2025/migration_notes.txt": "Migration from V9 to V10 mail database completed.\nTimestamp offset removed in V10.\n",
    "logs/current/run_20250601.log": "Script execution log\nStatus: completed\nEmails fetched: 12\nReminders created: 3\n",
    "config/email/settings.json": json.dumps({"account": "user@company.com", "sync_interval": 300, "range_default": "today"}),
    "config/reminders/preferences.json": json.dumps({"lead_time_hours": 2, "list_name": "默认提醒事项", "notify": True}),
    "config/email/legacy_query.sql": "-- OLD METHOD (broken for V10)\nSELECT datetime(date_received + 978307200, 'unixepoch') FROM messages;\n-- This adds CFAbsoluteTime offset - DO NOT USE\n",
    "data/raw/sample_email_dump.json": json.dumps([
        {"id": 1, "subject": "团队周会 - 3月31日 14:30", "sender": "boss@company.com", "body": "请准时参加团队周会，时间：2026年3月31日 14:30，地点：3号会议室"},
        {"id": 2, "subject": "客户拜访提醒", "sender": "sales@company.com", "body": "明天上午10点客户拜访，请做好准备"},
    ], indent=2, ensure_ascii=False),
    "data/processed/reminders_created.json": json.dumps([
        {"title": "团队周会", "time": "2026-03-31 14:30", "reminder_at": "2026-03-31 12:30"},
    ], indent=2, ensure_ascii=False),
    "reports/monthly/march_2025_summary.txt": "March 2025 Email Schedule Summary\nTotal emails processed: 45\nReminders created: 18\n",
    "reports/weekly/week_13_report.txt": "Week 13 Report\nEmails: 23, Reminders: 7\n",
    "backup/scripts/fetch_emails_v1.sh": "#!/bin/bash\n# DEPRECATED - uses old CFAbsoluteTime offset\necho 'This script is outdated'\n",
    "backup/data/old_reminder_format.txt": "Old format reminders - pre-migration backup\n",
    "tests/unit/test_time_parsing.py": "# Unit tests for time parsing\nimport unittest\n\nclass TestTimeParsing(unittest.TestCase):\n    def test_unix_epoch(self):\n        # V10 uses direct unix timestamps\n        pass\n",
    "tests/integration/test_pipeline.sh": "#!/bin/bash\n# Integration test placeholder\necho 'Run: ./scripts/fetch_emails.sh unread | ./scripts/create_reminders.py'\n",
    "docs/internal/email_db_schema.md": "# Mail Database Schema\n\n## messages table\n- date_received: Unix timestamp (seconds since 1970-01-01)\n- date_sent: Unix timestamp\n- sender: ROWID ref to addresses\n- subject: ROWID ref to subjects\n\n## NOTE: V10 no longer uses CFAbsoluteTime\n",
}

for path, content in distractor_files.items():
    filepath = workspace / path
    filepath.write_text(content, encoding="utf-8")

# Create a mock SQLite database mimicking macOS Mail V10 structure
db_dir = workspace / "mock_mail_db"
db_dir.mkdir(exist_ok=True)
db_path = db_dir / "Envelope Index"

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

# Create tables matching macOS Mail V10 schema
cur.executescript("""
CREATE TABLE IF NOT EXISTS subjects (
    ROWID INTEGER PRIMARY KEY,
    subject TEXT
);

CREATE TABLE IF NOT EXISTS addresses (
    ROWID INTEGER PRIMARY KEY,
    address TEXT,
    comment TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    ROWID INTEGER PRIMARY KEY,
    date_received INTEGER,
    date_sent INTEGER,
    sender INTEGER,
    subject INTEGER,
    read INTEGER DEFAULT 0,
    flagged INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS message_data (
    ROWID INTEGER PRIMARY KEY,
    message_id INTEGER,
    body TEXT
);
""")

# Insert realistic test data
# Use current time as base for "unread" emails
import time
now = int(time.time())
one_day = 86400

addresses_data = [
    (1, "ceo@mckinsey-consulting.cn", "张总"),
    (2, "hr@mckinsey-consulting.cn", "人事部"),
    (3, "it@mckinsey-consulting.cn", "IT部门"),
    (4, "client@fortune500.com", "客户联系人"),
    (5, "noreply@newsletter.com", "Newsletter"),
]
cur.executemany("INSERT INTO addresses VALUES (?,?,?)", addresses_data)

subjects_data = [
    (1, "高管战略会议 - 2026年8月15日 09:00"),
    (2, "季度业绩评审会议通知 - 8月20日 下午3点"),
    (3, "新员工入职培训安排 - 8/22 10:30"),
    (4, "客户项目启动会 - 明天上午9点"),
    (5, "IT系统维护通知 - 下周一 14:00"),
    (6, "每周团队例会提醒"),
    (7, "财务报告审批请求"),
    (8, "年度战略规划会议 - 2026年9月1日 08:30"),
]
cur.executemany("INSERT INTO subjects VALUES (?,?)", subjects_data)

messages_data = [
    # Unread emails (read=0) - these are what we want
    (1, now - 3600,    now - 3700,    1, 1, 0, 0),  # unread, 1h ago
    (2, now - 7200,    now - 7300,    2, 2, 0, 0),  # unread, 2h ago
    (3, now - 10800,   now - 10900,   3, 3, 0, 0),  # unread, 3h ago
    (4, now - 14400,   now - 14500,   4, 4, 0, 0),  # unread, 4h ago
    (5, now - 18000,   now - 18100,   3, 5, 0, 0),  # unread, 5h ago
    # Read emails (read=1)
    (6, now - 86400,   now - 86500,   1, 6, 1, 0),  # read, yesterday
    (7, now - 172800,  now - 172900,  2, 7, 1, 0),  # read, 2 days ago
    (8, now - 259200,  now - 259300,  4, 8, 1, 0),  # read, 3 days ago
]
cur.executemany("INSERT INTO messages VALUES (?,?,?,?,?,?,?)", messages_data)

message_bodies = [
    (1, 1, "尊敬的各位，\n\n敬请参加本月高管战略会议。\n\n会议时间：2026年8月15日 09:00\n会议地点：总部大楼18层董事会议室\n\n请准时出席，谢谢。\n\n张总"),
    (2, 2, "各位同事，\n\n季度业绩评审会议将于8月20日 下午3点在线上召开，\n请提前准备好各自部门的业绩数据。\n\nZoom链接将另行发送。\n\n人事部"),
    (3, 3, "亲爱的新同事们，\n\n新员工入职培训将于8/22 10:30在多功能厅举行。\n请携带身份证原件及一寸照片两张。\n\nIT部门"),
    (4, 4, "您好，\n\n客户项目启动会定于明天上午9点，地点：客户办公室A栋3楼。\n请携带项目提案文件。\n\n期待与您合作！"),
    (5, 5, "IT系统维护通知：\n\n本次维护时间为下周一 14:00，预计持续2小时。\n维护期间邮件服务可能中断，请提前做好准备。\n\nIT部门"),
    (6, 6, "本周团队例会照常进行，时间：每周五下午4点。"),
    (7, 7, "财务报告已上传至共享盘，请审批。"),
    (8, 8, "年度战略规划会议将于2026年9月1日 08:30举行，为期两天。"),
]
cur.executemany("INSERT INTO message_data VALUES (?,?,?)", message_bodies)

conn.commit()
conn.close()

print(f"Mock database created at: {db_path}")
print(f"Database has {len(messages_data)} messages, {len([m for m in messages_data if m[5]==0])} unread")
print("Workspace structure created successfully.")