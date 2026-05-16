#!/bin/bash
set -e

WORKSPACE=/workspace

# ---------------------------------------------------------
# Create the extract_minutes.py script
# ---------------------------------------------------------
cat > "$WORKSPACE/scripts/extract_minutes.py" << 'PYEOF'
#!/usr/bin/env python3
"""
extract_minutes.py — Converts raw meeting notes into structured meeting minutes.
"""
import argparse
import re
import sys
from pathlib import Path
from datetime import datetime

def parse_attendees(text):
    patterns = [
        r'参与人员[：:]\s*(.+)',
        r'参会人[：:]\s*(.+)',
        r'与会人员[：:]\s*(.+)',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            return m.group(1).strip()
    return "未记录"

def parse_date(text):
    m = re.search(r'(\d{4}年\d{1,2}月\d{1,2}日)', text)
    if m:
        return m.group(1)
    return datetime.today().strftime("%Y年%m月%d日")

def parse_recorder(text):
    m = re.search(r'[（(]记录[）)]\s*([^、，,\s（(）)]+)', text)
    if m:
        return m.group(1).strip()
    # try another pattern
    m2 = re.search(r'(\w+)[（(]记录[）)]', text)
    if m2:
        return m2.group(1).strip()
    return "未记录"

def parse_topic(text):
    # Extract the first line that looks like a title
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line and '会议' in line and len(line) < 60:
            # remove date part
            title = re.sub(r'\s*[-—]\s*\d{4}年.*', '', line).strip()
            return title if title else line
    return "会议纪要"

def parse_agenda_and_discussion(text):
    """Extract agenda items and discussion points from the raw text."""
    agenda = []
    discussions = []
    decisions = []
    todos = []

    # Find topic sections
    topic_pattern = re.compile(r'话题\d+[：:]\s*(.+)')
    topics = topic_pattern.findall(text)
    agenda = topics if topics else ["综合讨论"]

    # Extract decisions
    decision_pattern = re.compile(r'决定[：:]\s*(.+)')
    decisions = decision_pattern.findall(text)

    # Extract action items / todos
    todo_pattern = re.compile(r'行动项[：:]\s*(.+)')
    raw_todos = todo_pattern.findall(text)

    for todo_text in raw_todos:
        # Try to extract person and date
        # Pattern: person + verb + date
        person_match = re.match(r'^(\w+)[需要在要]?\s*', todo_text)
        date_match = re.search(r'(\d{1,2}月\d{1,2}日)', todo_text)
        
        # Extract the task description
        task = todo_text.strip()
        person = "待定"
        deadline = "待定"
        
        if date_match:
            deadline = date_match.group(1)
        
        # Common Chinese names at start
        name_match = re.match(r'^([^\s，,。需负责提出]{2,4})\s*[需负在]', todo_text)
        if name_match:
            person = name_match.group(1)
        
        todos.append({
            "task": task,
            "person": person,
            "deadline": deadline,
            "status": "待领取"
        })

    # Build discussion points from topic blocks
    lines = text.split('\n')
    current_topic = None
    for line in lines:
        line = line.strip()
        if re.match(r'话题\d+', line):
            current_topic = line
        elif current_topic and line and not line.startswith('决定') and not line.startswith('行动项') and not line.startswith('话题'):
            if len(line) > 5:
                discussions.append(line)

    return agenda, discussions[:8], decisions, todos

def generate_markdown(title, date, attendees, recorder, agenda, discussions, decisions, todos):
    lines = []
    lines.append(f"# 会议纪要 — {title}")
    lines.append("")
    lines.append("## 基本信息")
    lines.append(f"- 时间：{date}")
    lines.append(f"- 参会人：{attendees}")
    lines.append(f"- 记录人：{recorder}")
    lines.append("")
    lines.append("## 议程")
    for i, item in enumerate(agenda, 1):
        lines.append(f"{i}. {item}")
    lines.append("")
    lines.append("## 讨论要点")
    for d in discussions:
        lines.append(f"- {d}")
    lines.append("")
    lines.append("## 决议")
    for dec in decisions:
        lines.append(f"- {dec}")
    lines.append("")
    lines.append("## 待办事项")
    lines.append("| 事项 | 负责人 | 截止时间 | 状态 |")
    lines.append("|------|--------|----------|------|")
    for todo in todos:
        lines.append(f"| {todo['task']} | {todo['person']} | {todo['deadline']} | {todo['status']} |")
    lines.append("")
    lines.append("---")
    lines.append("*由 meeting-minutes-assistant 生成*")
    return "\n".join(lines)

def generate_html(title, date, attendees, recorder, agenda, discussions, decisions, todos):
    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{title}</title></head>
<body>
<h1>会议纪要 — {title}</h1>
<h2>基本信息</h2>
<ul>
<li>时间：{date}</li>
<li>参会人：{attendees}</li>
<li>记录人：{recorder}</li>
</ul>
<h2>议程</h2>
<ol>
{''.join(f'<li>{item}</li>' for item in agenda)}
</ol>
<h2>讨论要点</h2>
<ul>
{''.join(f'<li>{d}</li>' for d in discussions)}
</ul>
<h2>决议</h2>
<ul>
{''.join(f'<li>{dec}</li>' for dec in decisions)}
</ul>
<h2>待办事项</h2>
<table border="1">
<tr><th>事项</th><th>负责人</th><th>截止时间</th><th>状态</th></tr>
{''.join(f"<tr><td>{t['task']}</td><td>{t['person']}</td><td>{t['deadline']}</td><td>{t['status']}</td></tr>" for t in todos)}
</table>
<hr/>
<p><em>由 meeting-minutes-assistant 生成</em></p>
</body>
</html>"""
    return html

def main():
    parser = argparse.ArgumentParser(description='Extract and structure meeting minutes')
    parser.add_argument('--input', required=True, help='Input raw meeting notes file')
    parser.add_argument('--output', required=True, help='Output structured minutes file')
    parser.add_argument('--format', choices=['md', 'html'], default='md', help='Output format')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding='utf-8')

    title = parse_topic(text)
    date = parse_date(text)
    attendees = parse_attendees(text)
    recorder = parse_recorder(text)
    agenda, discussions, decisions, todos = parse_agenda_and_discussion(text)

    if args.format == 'html':
        content = generate_html(title, date, attendees, recorder, agenda, discussions, decisions, todos)
    else:
        content = generate_markdown(title, date, attendees, recorder, agenda, discussions, decisions, todos)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding='utf-8')

    print(f"[extract_minutes] ✓ Structured minutes written to: {args.output}")
    print(f"  - Attendees: {attendees}")
    print(f"  - Agenda items: {len(agenda)}")
    print(f"  - Decisions: {len(decisions)}")
    print(f"  - TODOs extracted: {len(todos)}")

if __name__ == '__main__':
    main()
PYEOF

# ---------------------------------------------------------
# Create the extract_todos.py script
# ---------------------------------------------------------
cat > "$WORKSPACE/scripts/extract_todos.py" << 'PYEOF'
#!/usr/bin/env python3
"""
extract_todos.py — Extracts action items / TODOs from structured meeting minutes.
"""
import argparse
import re
import sys
import json
from pathlib import Path

def extract_todos_from_markdown(text):
    todos = []
    in_table = False
    header_passed = False

    for line in text.split('\n'):
        # Detect the start of the todo table
        if '待办事项' in line and line.startswith('#'):
            in_table = True
            header_passed = False
            continue
        
        if in_table:
            # Skip the header row and separator row
            if '|' not in line:
                if line.strip() == '' or line.startswith('#'):
                    in_table = False
                continue
            
            if '事项' in line and '负责人' in line:
                header_passed = True
                continue
            
            if '---' in line and '|' in line:
                continue
            
            if header_passed and '|' in line:
                parts = [p.strip() for p in line.strip('|').split('|')]
                if len(parts) >= 4:
                    task, person, deadline, status = parts[0], parts[1], parts[2], parts[3]
                    if task:
                        todos.append({
                            "task": task,
                            "assignee": person,
                            "deadline": deadline,
                            "status": status
                        })
    return todos

def format_as_markdown(todos):
    lines = ["# 待办事项清单", "", "| 事项 | 负责人 | 截止时间 | 状态 |", "|------|--------|----------|------|"]
    for t in todos:
        lines.append(f"| {t['task']} | {t['assignee']} | {t['deadline']} | {t['status']} |")
    lines.append("")
    lines.append(f"共 {len(todos)} 项待办事项")
    return "\n".join(lines)

def format_as_json(todos):
    output = {
        "total": len(todos),
        "todos": todos
    }
    return json.dumps(output, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Extract TODO items from meeting minutes')
    parser.add_argument('--input', required=True, help='Input structured minutes file (.md)')
    parser.add_argument('--format', choices=['md', 'json'], required=True, help='Output format: md or json')
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding='utf-8')
    todos = extract_todos_from_markdown(text)

    if not todos:
        print(f"Warning: No TODO items found in '{args.input}'", file=sys.stderr)

    if args.format == 'json':
        output = format_as_json(todos)
        # Determine output filename
        out_path = input_path.with_suffix('.todos.json')
    else:
        output = format_as_markdown(todos)
        out_path = input_path.with_suffix('.todos.md')

    out_path.write_text(output, ensure_ascii=False)
    print(f"[extract_todos] ✓ TODOs written to: {out_path}")
    print(f"  - Format: {args.format}")
    print(f"  - Items extracted: {len(todos)}")

if __name__ == '__main__':
    main()
PYEOF

# ---------------------------------------------------------
# Create the push_minutes.py script
# ---------------------------------------------------------
cat > "$WORKSPACE/scripts/push_minutes.py" << 'PYEOF'
#!/usr/bin/env python3
"""
push_minutes.py — Pushes meeting minutes to the specified channel.
Supported channels: wecom, feishu, ddingtalk
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

MOCK_PUSH_LOG = "/workspace/logs/push_results.jsonl"

SUPPORTED_CHANNELS = ["wecom", "feishu", "ddingtalk"]

def push_to_channel(channel, content, filename):
    """Simulate pushing to a channel and log the result."""
    timestamp = datetime.now().isoformat()
    
    record = {
        "timestamp": timestamp,
        "channel": channel,
        "filename": filename,
        "content_length": len(content),
        "status": "success",
        "message": f"Successfully pushed to {channel}"
    }
    
    # Simulate channel-specific behavior
    if channel == "feishu":
        record["feishu_card_id"] = f"feishu_card_{hash(content) % 100000:05d}"
    elif channel == "wecom":
        record["wecom_msg_id"] = f"wecom_{hash(content) % 100000:05d}"
    elif channel == "ddingtalk":
        record["ddingtalk_msg_id"] = f"ddingtalk_{hash(content) % 100000:05d}"
    
    # Write to log
    log_path = Path(MOCK_PUSH_LOG)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    return record

def main():
    parser = argparse.ArgumentParser(description='Push meeting minutes to a channel')
    parser.add_argument('--file', required=True, help='Minutes file to push')
    parser.add_argument('--channel', required=True, choices=SUPPORTED_CHANNELS,
                        help=f'Target channel: {"|".join(SUPPORTED_CHANNELS)}')
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: File '{args.file}' not found.", file=sys.stderr)
        sys.exit(1)

    content = file_path.read_text(encoding='utf-8')
    
    print(f"[push_minutes] Pushing '{args.file}' to channel: {args.channel}")
    
    result = push_to_channel(args.channel, content, str(file_path))
    
    print(f"[push_minutes] ✓ Push successful!")
    print(f"  - Channel: {args.channel}")
    print(f"  - Status: {result['status']}")
    print(f"  - Content length: {result['content_length']} chars")
    if args.channel == "feishu":
        print(f"  - Feishu Card ID: {result.get('feishu_card_id', 'N/A')}")
    
if __name__ == '__main__':
    main()
PYEOF

chmod +x "$WORKSPACE/scripts/extract_minutes.py"
chmod +x "$WORKSPACE/scripts/extract_todos.py"
chmod +x "$WORKSPACE/scripts/push_minutes.py"

echo "[setup] All scripts created and made executable."
echo "[setup] Workspace ready."
ls -la "$WORKSPACE/scripts/"