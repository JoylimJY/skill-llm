#!/bin/bash
set -e

WORKSPACE="/workspace"

# ─────────────────────────────────────────────
# Create the mock fetch_emails.sh script
# This mimics the real macOS script but reads from our mock DB
# ─────────────────────────────────────────────
cat > "$WORKSPACE/scripts/fetch_emails.sh" << 'FETCH_EOF'
#!/bin/bash

RANGE="${1:-today}"
DB_PATH="/workspace/mock_mail_db/Envelope Index"

if [ ! -f "$DB_PATH" ]; then
    echo '[]'
    exit 1
fi

# Build WHERE clause based on range parameter - mimics real script logic
case "$RANGE" in
    today)
        # Correct V10 behavior: direct unixepoch (no CFAbsoluteTime offset)
        WHERE_CLAUSE="WHERE date(m.date_received, 'unixepoch', 'localtime') = date('now', 'localtime')"
        ;;
    yesterday)
        WHERE_CLAUSE="WHERE date(m.date_received, 'unixepoch', 'localtime') >= date('now', '-1 day', 'localtime')"
        ;;
    unread)
        WHERE_CLAUSE="WHERE m.read = 0"
        ;;
    all)
        WHERE_CLAUSE="ORDER BY m.date_received DESC LIMIT 50"
        ;;
    *)
        echo "Error: Unknown range '$RANGE'. Use: today | yesterday | unread | all" >&2
        exit 1
        ;;
esac

# Query DB and output JSON
python3 - "$DB_PATH" "$WHERE_CLAUSE" << 'PYEOF'
import sys
import sqlite3
import json

db_path = sys.argv[1]
where_clause = sys.argv[2]

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

if where_clause.startswith("ORDER"):
    query = f"""
        SELECT m.ROWID as id,
               datetime(m.date_received, 'unixepoch', 'localtime') as date_received,
               a.address as sender,
               a.comment as sender_name,
               s.subject as subject,
               md.body as body,
               m.read as is_read
        FROM messages m
        LEFT JOIN addresses a ON m.sender = a.ROWID
        LEFT JOIN subjects s ON m.subject = s.ROWID
        LEFT JOIN message_data md ON md.message_id = m.ROWID
        {where_clause}
    """
else:
    query = f"""
        SELECT m.ROWID as id,
               datetime(m.date_received, 'unixepoch', 'localtime') as date_received,
               a.address as sender,
               a.comment as sender_name,
               s.subject as subject,
               md.body as body,
               m.read as is_read
        FROM messages m
        LEFT JOIN addresses a ON m.sender = a.ROWID
        LEFT JOIN subjects s ON m.subject = s.ROWID
        LEFT JOIN message_data md ON md.message_id = m.ROWID
        {where_clause}
        ORDER BY m.date_received DESC
    """

cur.execute(query)
rows = cur.fetchall()
conn.close()

result = [dict(row) for row in rows]
print(json.dumps(result, ensure_ascii=False, indent=2))
PYEOF
FETCH_EOF

chmod +x "$WORKSPACE/scripts/fetch_emails.sh"

# ─────────────────────────────────────────────
# Create the mock create_reminders.py script
# This mimics real remindctl behavior in-process
# ─────────────────────────────────────────────
cat > "$WORKSPACE/scripts/create_reminders.py" << 'PYEOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock create_reminders.py
Reads JSON from stdin, extracts time info, creates reminders (mocked),
and outputs the standard format defined in SKILL.md
"""

import sys
import json
import re
from datetime import datetime, timedelta

def extract_event_time(subject, body):
    """Extract meeting/event datetime from subject and body text."""
    patterns = [
        # 2026年8月15日 09:00
        r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})',
        # 8月20日 下午3点
        r'(\d{1,2})月(\d{1,2})日\s*下午(\d{1,2})点',
        # 8月20日 上午10点
        r'(\d{1,2})月(\d{1,2})日\s*上午(\d{1,2})点',
        # 8/22 10:30
        r'(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})',
        # 下周一 14:00
        r'下周[一二三四五六日]\s*(\d{1,2}):(\d{2})',
        # 明天上午9点
        r'明天\s*上午\s*(\d{1,2})点',
        # 明天下午N点
        r'明天\s*下午\s*(\d{1,2})点',
    ]

    text = (subject or '') + '\n' + (body or '')
    now = datetime.now()

    # Pattern 1: Full date with year
    m = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2}):(\d{2})', text)
    if m:
        try:
            dt = datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                         int(m.group(4)), int(m.group(5)))
            return dt
        except:
            pass

    # Pattern 2: Month/day with afternoon time
    m = re.search(r'(\d{1,2})月(\d{1,2})日\s*下午(\d{1,2})点', text)
    if m:
        try:
            hour = int(m.group(3))
            if hour < 12:
                hour += 12
            dt = datetime(now.year, int(m.group(1)), int(m.group(2)), hour, 0)
            if dt < now:
                dt = dt.replace(year=now.year + 1)
            return dt
        except:
            pass

    # Pattern 3: Month/day with morning time
    m = re.search(r'(\d{1,2})月(\d{1,2})日\s*上午(\d{1,2})点', text)
    if m:
        try:
            dt = datetime(now.year, int(m.group(1)), int(m.group(2)),
                         int(m.group(3)), 0)
            if dt < now:
                dt = dt.replace(year=now.year + 1)
            return dt
        except:
            pass

    # Pattern 4: M/D HH:MM
    m = re.search(r'(\d{1,2})/(\d{1,2})\s+(\d{1,2}):(\d{2})', text)
    if m:
        try:
            dt = datetime(now.year, int(m.group(1)), int(m.group(2)),
                         int(m.group(3)), int(m.group(4)))
            if dt < now:
                dt = dt.replace(year=now.year + 1)
            return dt
        except:
            pass

    # Pattern 5: 下周一/二/三/四/五 + time
    day_map = {'一': 0, '二': 1, '三': 2, '四': 3, '五': 4, '六': 5, '日': 6}
    m = re.search(r'下周([一二三四五六日])\s*(\d{1,2}):(\d{2})', text)
    if m:
        try:
            target_weekday = day_map[m.group(1)]
            days_ahead = (target_weekday - now.weekday() + 7) % 7 + 7
            if days_ahead == 0:
                days_ahead = 7
            dt = now + timedelta(days=days_ahead)
            dt = dt.replace(hour=int(m.group(2)), minute=int(m.group(3)), second=0, microsecond=0)
            return dt
        except:
            pass

    # Pattern 6: 明天上午N点
    m = re.search(r'明天\s*上午\s*(\d{1,2})点', text)
    if m:
        tomorrow = now + timedelta(days=1)
        dt = tomorrow.replace(hour=int(m.group(1)), minute=0, second=0, microsecond=0)
        return dt

    # Pattern 7: 明天下午N点
    m = re.search(r'明天\s*下午\s*(\d{1,2})点', text)
    if m:
        hour = int(m.group(1))
        if hour < 12:
            hour += 12
        tomorrow = now + timedelta(days=1)
        dt = tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
        return dt

    return None


def main():
    try:
        raw = sys.stdin.read()
        emails = json.loads(raw)
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        sys.exit(1)

    reminders_created = []

    for email in emails:
        subject = email.get('subject', '')
        body = email.get('body', '')
        sender = email.get('sender', '')

        event_time = extract_event_time(subject, body)
        if event_time is None:
            continue

        # Only create reminders for future events
        now = datetime.now()
        if event_time <= now:
            continue

        # Reminder is set 2 hours before the event (SKILL.md rule)
        reminder_time = event_time - timedelta(hours=2)

        # Mock remindctl call (simulate creating reminder)
        # In real usage: remindctl add "Title" --date "2026-08-15 07:00"
        event_name = subject.split('-')[0].strip() if '-' in subject else subject
        if len(event_name) > 30:
            event_name = event_name[:30]

        reminder = {
            "title": event_name,
            "event_time": event_time.strftime("%Y年%m月%d日 %H:%M"),
            "reminder_time": reminder_time.strftime("%Y年%m月%d日 %H:%M"),
            "sender": sender,
        }
        reminders_created.append(reminder)

    # Output in SKILL.md standard format
    email_count = len(emails)
    reminder_count = len(reminders_created)

    print("📧 邮件检索完成")
    print()
    print(f"查看邮件数量: {email_count}")
    print(f"创建提醒数量: {reminder_count}")
    print()
    if reminders_created:
        print("提醒详情:")
        for r in reminders_created:
            print(f"• {r['title']} - {r['event_time']}")

    # Also save machine-readable output for eval
    result_data = {
        "email_count": email_count,
        "reminder_count": reminder_count,
        "reminders": reminders_created,
        "range_used": "unknown"  # will be overwritten if called correctly
    }
    with open("/workspace/data/processed/last_run_result.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
PYEOF

chmod +x "$WORKSPACE/scripts/create_reminders.py"

# Make test scripts executable
chmod +x "$WORKSPACE/tests/integration/test_pipeline.sh" 2>/dev/null || true

echo "Setup complete. Scripts ready:"
echo "  - /workspace/scripts/fetch_emails.sh"
echo "  - /workspace/scripts/create_reminders.py"
echo "  - Mock DB at /workspace/mock_mail_db/Envelope Index"