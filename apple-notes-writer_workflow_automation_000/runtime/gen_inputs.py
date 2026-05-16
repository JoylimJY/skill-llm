import os
import random
random.seed(42)

workspace = "/workspace"

# Create realistic directory structure with distractor files
dirs = [
    "scripts",
    "incidents",
    "incidents/2024",
    "incidents/2024/Q1",
    "incidents/2024/Q2",
    "team_docs",
    "team_docs/runbooks",
    "team_docs/templates",
    "archive",
    "archive/old_notes",
    "configs",
    "exports",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ---- Create the mock apple_notes.py script in scripts/ ----
# This simulates the existing script (as per SKILL.md: "All scripts mentioned in the SKILL.md already exist")
apple_notes_script = '''#!/usr/bin/env python3
"""
Apple Notes Writer - Mock implementation for Linux testing.
Real implementation uses osascript on macOS.
"""
import subprocess
import re
import sys
import argparse


def markdown_to_html(markdown_text: str) -> str:
    """Convert Markdown to Apple Notes compatible HTML."""
    lines = markdown_text.split("\\n")
    html_lines = []
    in_ul = False
    in_ol = False

    for line in lines:
        # Headers
        if line.startswith("### "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append(f"<h3>{line[4:].strip()}</h3>")
        elif line.startswith("## "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append(f"<h2>{line[3:].strip()}</h2>")
        elif line.startswith("# "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append(f"<h1>{line[2:].strip()}</h1>")
        # Unordered list
        elif re.match(r"^- ", line):
            if in_ol: html_lines.append("</ol>"); in_ol = False
            if not in_ul: html_lines.append("<ul>"); in_ul = True
            item = line[2:].strip()
            item = re.sub(r"\\*\\*(.+?)\\*\\*", r"<b>\\1</b>", item)
            item = re.sub(r"\\*(.+?)\\*", r"<i>\\1</i>", item)
            html_lines.append(f"<li>{item}</li>")
        # Ordered list
        elif re.match(r"^\\d+\\. ", line):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if not in_ol: html_lines.append("<ol>"); in_ol = True
            item = re.sub(r"^\\d+\\. ", "", line).strip()
            item = re.sub(r"\\*\\*(.+?)\\*\\*", r"<b>\\1</b>", item)
            item = re.sub(r"\\*(.+?)\\*", r"<i>\\1</i>", item)
            html_lines.append(f"<li>{item}</li>")
        # Empty line -> <br>
        elif line.strip() == "":
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append("<br>")
        # Regular paragraph
        else:
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            text = line.strip()
            text = re.sub(r"\\*\\*(.+?)\\*\\*", r"<b>\\1</b>", text)
            text = re.sub(r"\\*(.+?)\\*", r"<i>\\1</i>", text)
            html_lines.append(f"<p>{text}</p>")

    if in_ul: html_lines.append("</ul>")
    if in_ol: html_lines.append("</ol>")

    return "<div>\\n" + "\\n".join(html_lines) + "\\n</div>"


def escape_for_applescript(content: str) -> str:
    """Escape content for AppleScript string embedding."""
    content = content.replace("\\\\", "\\\\\\\\")
    content = content.replace(\'"\', \'\\\\"\')
    return content


class AppleNotesWriter:
    def __init__(self, account: str = "iCloud"):
        self.account = account

    def write(self, title: str, content: str, folder: str = None,
              update_existing: bool = False) -> str:
        escaped = escape_for_applescript(content)
        # On real macOS this would call osascript
        # Here we just return a mock success
        location = f" in folder {folder}" if folder else ""
        action = "updated" if update_existing else "created"
        return f"SUCCESS: Note {action} - {title}{location}"

    def create_folder(self, title: str) -> str:
        return f"SUCCESS: Folder created - {title}"

    def list_notes(self, folder: str = None) -> list:
        return []

    def read(self, title: str) -> str:
        return ""


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    write_parser = subparsers.add_parser("write")
    write_parser.add_argument("--title", required=True)
    write_parser.add_argument("--content", default=None)
    write_parser.add_argument("--file", default=None)
    write_parser.add_argument("--markdown", action="store_true")
    write_parser.add_argument("--folder", default=None)
    write_parser.add_argument("--update", action="store_true")

    read_parser = subparsers.add_parser("read")
    read_parser.add_argument("--title", required=True)

    list_parser = subparsers.add_parser("list")
    list_parser.add_argument("--folder", default=None)

    folder_parser = subparsers.add_parser("create-folder")
    folder_parser.add_argument("--title", required=True)

    args = parser.parse_args()
    writer = AppleNotesWriter()

    if args.command == "write":
        content = args.content
        if args.file:
            with open(args.file, "r") as f:
                content = f.read()
        if args.markdown:
            content = markdown_to_html(content)
        result = writer.write(
            title=args.title,
            content=content,
            folder=args.folder,
            update_existing=args.update
        )
        print(result)
    elif args.command == "read":
        print(writer.read(args.title))
    elif args.command == "list":
        notes = writer.list_notes(folder=args.folder)
        for n in notes:
            print(n)
    elif args.command == "create-folder":
        print(writer.create_folder(args.title))


if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "scripts", "apple_notes.py"), "w") as f:
    f.write(apple_notes_script)

# Create __init__.py so scripts is importable
with open(os.path.join(workspace, "scripts", "__init__.py"), "w") as f:
    f.write("")

# ---- THE CORE INPUT: A messy incident postmortem Markdown file ----
# This is intentionally messy: has unsupported tags (code, img references in text),
# special characters (backslashes, quotes), todos with plain text checkboxes,
# and needs to be converted to properly formatted Apple Notes HTML.
incident_markdown = '''# Incident Postmortem: API Gateway Outage

**Incident ID:** INC-2024-0042
**Severity:** P1 - Critical
**Date:** 2024-06-15
**Duration:** 3h 47m

## Executive Summary

The API Gateway experienced a complete outage affecting 100% of production traffic.
Root cause was a misconfigured load balancer rule containing a "rogue backslash" (\\) in the path matcher.
The config value was: "path=/api\\v2\\" which caused the parser to fail silently.

## Timeline

1. 14:03 - Alert triggered: "5xx error rate > 50%"
2. 14:11 - On-call engineer acknowledged: Jane Smith
3. 14:45 - Root cause identified: bad config with \\n escape in YAML
4. 17:50 - Service fully restored

## Root Cause Analysis

The deployment script used an unescaped double-quote (") in the config template.
Specifically the value `timeout: "30s"` was written as timeout: "30s" without escaping.

```yaml
# This was the broken config (DO NOT USE):
path: /api\\v2\\"
timeout: "30s"
```

The `config-validator` tool should have caught this but was disabled.

## Action Items

- [ ] Fix config validator to detect escape issues
- [ ] Add integration test for path patterns containing backslashes
- [ ] Update runbook for API Gateway failures
- [x] Deploy hotfix to production
- [x] Send customer notification

## Lessons Learned

**What went well:**
- Alert fired within 3 minutes of outage start
- Team communication was effective

**What went poorly:**
- No pre-deployment validation gate existed
- Config review process did not catch the "bad escape" issue

### Follow-up

Next review scheduled for: 2024-06-22
Owner: Platform Team <platform@company.com>

---
*This document is confidential. Do not share externally.*
'''

with open(os.path.join(workspace, "incidents", "2024", "Q2", "INC-2024-0042-postmortem.md"), "w") as f:
    f.write(incident_markdown)

# ---- Distractor files ----
distractor_files = [
    ("configs/lb_config.yaml", "path: /api/v2\ntimeout: 30s\nretries: 3\n"),
    ("configs/alerts.json", '{"threshold": 0.5, "window": "5m", "team": "platform"}\n'),
    ("team_docs/runbooks/api_gateway_restart.md", "# API Gateway Restart Runbook\n\n1. SSH to bastion\n2. Run `kubectl rollout restart deployment/api-gateway`\n3. Verify pods are healthy\n"),
    ("team_docs/runbooks/database_failover.md", "# Database Failover\n\nThis runbook describes the database failover procedure.\n"),
    ("team_docs/templates/postmortem_template.md", "# Incident Postmortem: [TITLE]\n\n**Incident ID:**\n**Severity:**\n**Date:**\n\n## Summary\n\n## Timeline\n\n## Root Cause\n\n## Action Items\n"),
    ("archive/old_notes/meeting_2024_01.txt", "Meeting notes from January 2024 planning session.\nAttendees: Alice, Bob, Carol\nDecision: Migrate to new API gateway by Q2.\n"),
    ("archive/old_notes/incident_summary_2023.txt", "In 2023 we had 3 P1 incidents. Total downtime: 8h 23m.\n"),
    ("exports/weekly_report_2024_W24.txt", "Week 24 Report\nIncidents: 1 P1, 2 P2\nMTTR: 2h 15m\n"),
    ("incidents/2024/Q1/INC-2024-0011-postmortem.md", "# Incident Postmortem: Database Connection Pool Exhaustion\n\n**Severity:** P2\n**Date:** 2024-03-10\n\n## Summary\nConnection pool was exhausted due to a slow query.\n"),
    ("incidents/2024/Q2/INC-2024-0038-postmortem.md", "# Incident Postmortem: CDN Misconfiguration\n\n**Severity:** P2\n**Date:** 2024-06-01\n\n## Summary\nCDN cache rules were incorrectly set, causing stale responses.\n"),
]

for rel_path, content in distractor_files:
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# ---- Task specification file (business requirement, NOT a hint) ----
task_spec = """TASK BRIEF - Platform Engineering Team

We need to archive the INC-2024-0042 postmortem into our team's note management system.

Requirements:
1. The postmortem is located at: incidents/2024/Q2/INC-2024-0042-postmortem.md
2. It must be saved into the folder called "Incident Reports" in the note system.
3. If a note with this title already exists, it must be updated (not duplicated).
4. The note title should be: "INC-2024-0042 API Gateway Outage Postmortem"
5. The action items section should use proper checkbox symbols for pending items 
   and checkmark symbols for completed items (replace markdown [ ] and [x] notation).
6. Any code blocks in the source must be removed (the note system does not support them);
   replace each code block with an italic note saying "(see attached config file)".
7. Produce two output artifacts:
   a) A file named `note_content.html` containing the final formatted HTML content 
      that will be written to the note system.
   b) A Python script named `publish_note.py` that uses the note system's Python API 
      to write this note with all correct parameters.

The script and content file should be placed anywhere in the workspace.
"""

with open(os.path.join(workspace, "TASK_BRIEF.txt"), "w") as f:
    f.write(task_spec)

print("Workspace generated successfully.")
print("Key files:")
print("  - TASK_BRIEF.txt")
print("  - incidents/2024/Q2/INC-2024-0042-postmortem.md")
print("  - scripts/apple_notes.py")