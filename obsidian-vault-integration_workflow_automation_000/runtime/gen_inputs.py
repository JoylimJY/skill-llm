#!/usr/bin/env python3
"""
Generate the sandbox workspace for the Obsidian vault integration task.
"""
import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Create vault directory structure ─────────────────────────────────────
vault = WORKSPACE / "company-vault"
dirs = [
    vault / "meetings",
    vault / "meetings" / "2024",
    vault / "meetings" / "2023",
    vault / "roadmap",
    vault / "roadmap" / "q1",
    vault / "roadmap" / "q2",
    vault / "team",
    vault / "archive" / "tasks",       # <-- the "moved" file lives here
    vault / "finance",
    vault / "finance" / "reports",
    vault / "engineering",
    vault / "engineering" / "specs",
    vault / ".obsidian",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ── 2. Distractor files ──────────────────────────────────────────────────────

# 2a. A file named open-questions.md but with WRONG type (trap for filename fallback)
wrong_oq = vault / "engineering" / "open-questions.md"
wrong_oq.write_text("""\
---
type: brainstorm-notes
status: draft
---
# Brainstorm Questions
These are speculative ideas, not tracked tasks.
- Maybe adopt Rust?
- Evaluate new cloud providers?
""")

# 2b. Meeting notes with checkboxes (distractor — not type: open-questions)
meeting1 = vault / "meetings" / "2024" / "sprint-42-retro.md"
meeting1.write_text("""\
---
type: meeting-notes
date: 2024-03-15
attendees: [Alice, Bob, Carlos]
---
# Sprint 42 Retrospective
## Action Items
- [x] Alice: Update CI pipeline config
- [ ] Bob: Review PR backlog
- [ ] Carlos: Schedule 1-on-1s
""")

meeting2 = vault / "meetings" / "2023" / "kickoff.md"
meeting2.write_text("""\
---
type: meeting-notes
date: 2023-01-10
---
# Project Kickoff
- [ ] Define MVP scope
- [x] Assign team leads
""")

# 2c. Roadmap files
roadmap_q1 = vault / "roadmap" / "q1" / "milestones.md"
roadmap_q1.write_text("""\
---
type: milestones
quarter: Q1-2024
---
# Q1 2024 Milestones
- [ ] Launch beta to 50 users
- [x] Complete SOC2 prep
- [ ] Integrate Stripe v2
""")

roadmap_q2 = vault / "roadmap" / "q2" / "milestones.md"
roadmap_q2.write_text("""\
---
type: milestones
quarter: Q2-2024
---
# Q2 2024 Milestones
- [ ] Scale to 500 users
- [ ] Launch mobile app
""")

# 2d. Team info
team_file = vault / "team" / "roster.md"
team_file.write_text("""\
---
type: team-roster
---
# Team Roster
| Name   | Role              | Slack       |
|--------|-------------------|-------------|
| Alice  | Backend Lead      | @alice      |
| Bob    | Frontend Lead     | @bob        |
| Carlos | DevOps            | @carlos     |
| Dave   | Product Manager   | @dave       |
| Elena  | Security Engineer | @elena      |
""")

# 2e. Finance distractors
finance1 = vault / "finance" / "reports" / "q1-2024.md"
finance1.write_text("""\
---
type: financial-report
quarter: Q1-2024
---
# Q1 Financial Report
Revenue: $120,000
Burn rate: $45,000/month
""")

# 2f. Engineering specs
spec1 = vault / "engineering" / "specs" / "payment-api.md"
spec1.write_text("""\
---
type: technical-spec
service: payment-api
---
# Payment API Spec
## Endpoints
- POST /v2/charge
- GET /v2/transactions
""")

spec2 = vault / "engineering" / "specs" / "auth-service.md"
spec2.write_text("""\
---
type: technical-spec
service: auth-service
---
# Auth Service Spec
JWT-based authentication with refresh tokens.
""")

# 2g. Obsidian config (realistic noise)
obsidian_cfg = vault / ".obsidian" / "app.json"
obsidian_cfg.write_text(json.dumps({
    "legacyEditor": False,
    "livePreview": True,
    "defaultViewMode": "source"
}, indent=2))

# 2h. A fake "tasks.md" in root with WRONG type (another trap)
fake_tasks = vault / "tasks.md"
fake_tasks.write_text("""\
---
type: archived-tasks
status: deprecated
---
# Old Tasks (Archived)
Do not update this file. See archive folder.
- [x] Old task 1
- [x] Old task 2
""")

# ── 3. THE REAL FILE: moved to archive/tasks/ with misleading name ──────────
# type: open-questions  ← only discoverable via frontmatter
real_oq = vault / "archive" / "tasks" / "legacy-items.md"
real_oq.write_text("""\
---
type: open-questions
status: active
last-updated: 2024-05-01
---
# Open Questions & Action Items

## Critical
- [ ] **[critical]** @Alice: Resolve payment gateway timeout issues
- [ ] **[critical]** @Bob: Database migration script review
- [x] **[critical]** @Carlos: Set up staging environment

## Important
- [ ] **[important]** @Dave: Define Q3 OKRs with leadership
- [ ] **[important]** @Alice: Audit third-party API rate limits
- [x] **[important]** @Bob: Complete API versioning RFC

## Nice to Have
- [ ] **[nice]** @Carlos: Document deployment runbook
- [ ] **[nice]** @Dave: Explore GraphQL adoption feasibility
""")

# ── 4. Create the scripts directory and vault-read.py / vault-write.py ──────
scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(exist_ok=True)

# vault-read.py
vault_read = scripts_dir / "vault-read.py"
vault_read.write_text(r'''#!/usr/bin/env python3
"""
vault-read.py — Read and parse vault files into structured JSON.

Usage:
    python vault-read.py <vault-path> --file <filename> --format json
    python vault-read.py <vault-path> --file <filename> --format text

Returns JSON array of tasks with fields: id, title, priority, status, owner
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    import frontmatter
except ImportError:
    print("ERR_DEPENDENCY: python-frontmatter not installed", file=sys.stderr)
    sys.exit(1)


PRIORITY_MAP = {
    "critical": "critical",
    "important": "important",
    "nice": "nice",
}


def discover_file(vault_path: Path, filename: str) -> Path | None:
    """
    Discovery chain:
    1. Frontmatter type: field
    2. Filename pattern matching
    3. Full-text search (not implemented, returns None)
    """
    # Derive target type from filename
    stem = Path(filename).stem  # e.g. "open-questions"
    target_type = stem  # type field should match stem

    # Phase 1: frontmatter type search
    for md_file in vault_path.rglob("*.md"):
        try:
            post = frontmatter.load(str(md_file))
            if post.metadata.get("type") == target_type:
                return md_file
        except Exception:
            continue

    # Phase 2: filename pattern matching
    pattern = f"*{stem}*"
    matches = list(vault_path.rglob(pattern))
    if matches:
        return matches[0]

    return None


def parse_tasks(content: str) -> list[dict]:
    """Parse checkbox tasks from markdown content."""
    tasks = []
    task_id = 0

    lines = content.split("\n")
    current_priority = "nice"

    for line in lines:
        # Detect section headers for priority
        header_lower = line.lower()
        if "## critical" in header_lower:
            current_priority = "critical"
        elif "## important" in header_lower:
            current_priority = "important"
        elif "## nice" in header_lower:
            current_priority = "nice"

        # Match checkbox items: - [ ] or - [x]
        m = re.match(
            r"^\s*-\s+\[([ xX])\]\s+(?:\*\*\[(\w+)\]\*\*\s+)?(?:@(\w+):\s+)?(.+)$",
            line,
        )
        if not m:
            continue

        checked, inline_priority, owner, title = m.groups()
        status = "done" if checked.lower() == "x" else "todo"
        priority = PRIORITY_MAP.get(inline_priority, current_priority) if inline_priority else current_priority
        # Clean up title
        title = title.strip().rstrip("*").strip()
        task_id += 1

        tasks.append({
            "id": task_id,
            "title": title,
            "priority": priority,
            "status": status,
            "owner": owner or "unassigned",
        })

    return tasks


def main():
    parser = argparse.ArgumentParser(description="Read vault files")
    parser.add_argument("vault_path", help="Path to vault directory")
    parser.add_argument("--file", required=True, help="Filename to read (e.g. open-questions.md)")
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()

    vault = Path(args.vault_path)
    if not vault.exists():
        print(json.dumps({"error": "ERR_VAULT_NOT_FOUND", "message": f"Vault not found: {vault}"}))
        sys.exit(1)

    target = discover_file(vault, args.file)
    if target is None:
        print(json.dumps({"error": "ERR_FILE_NOT_FOUND", "message": f"File not found: {args.file}"}))
        sys.exit(1)

    try:
        post = frontmatter.load(str(target))
        content = post.content
    except Exception as e:
        print(json.dumps({"error": "ERR_PARSE_FAILED", "message": str(e), "partial": []}))
        sys.exit(1)

    tasks = parse_tasks(content)

    if args.format == "json":
        print(json.dumps(tasks, indent=2))
    else:
        for t in tasks:
            status_icon = "[x]" if t["status"] == "done" else "[ ]"
            print(f"{t['id']:>3}. {status_icon} [{t['priority']:<9}] @{t['owner']:<12} {t['title']}")


if __name__ == "__main__":
    main()
''')

# vault-write.py
vault_write = scripts_dir / "vault-write.py"
vault_write.write_text(r'''#!/usr/bin/env python3
"""
vault-write.py — Write updates back to vault files with safety checks.

Usage:
    Add task:
        python vault-write.py <vault-path> --file open-questions.md \
            --action add-task --title "New task" --priority important --owner Dave

    Mark task done:
        python vault-write.py <vault-path> --file open-questions.md \
            --action mark-done --task-id 3

All writes are logged to <vault>/.vault-audit.log
"""
import argparse
import json
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    import frontmatter
except ImportError:
    print("ERR_DEPENDENCY: python-frontmatter not installed", file=sys.stderr)
    sys.exit(1)


PRIORITY_SECTIONS = {
    "critical": "## Critical",
    "important": "## Important",
    "nice": "## Nice to Have",
}

PRIORITY_TAGS = {
    "critical": "critical",
    "important": "important",
    "nice": "nice",
}


def discover_file(vault_path: Path, filename: str) -> Path | None:
    stem = Path(filename).stem
    target_type = stem

    for md_file in vault_path.rglob("*.md"):
        try:
            import frontmatter as fm
            post = fm.load(str(md_file))
            if post.metadata.get("type") == target_type:
                return md_file
        except Exception:
            continue

    pattern = f"*{stem}*"
    matches = list(vault_path.rglob(pattern))
    if matches:
        return matches[0]

    return None


def write_audit_log(vault_path: Path, agent: str, file_path: Path, action: str, detail: str):
    log_path = vault_path / ".vault-audit.log"
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"{ts} | agent={agent} | file={file_path.name} | action={action} | detail={detail}\n"
    with open(log_path, "a") as f:
        f.write(entry)


def count_tasks(content: str) -> int:
    count = 0
    for line in content.split("\n"):
        m = re.match(r"^\s*-\s+\[([ xX])\]", line)
        if m:
            count += 1
    return count


def add_task(vault_path: Path, target: Path, title: str, priority: str, owner: str):
    import frontmatter as fm
    post = fm.load(str(target))
    content = post.content

    section_header = PRIORITY_SECTIONS.get(priority)
    if section_header is None:
        print(json.dumps({"error": "ERR_INVALID_PRIORITY", "message": f"Unknown priority: {priority}"}))
        sys.exit(1)

    tag = PRIORITY_TAGS[priority]
    new_line = f"- [ ] **[{tag}]** @{owner}: {title}"

    # Insert after the section header
    lines = content.split("\n")
    insert_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower() == section_header.lower():
            insert_idx = i + 1
            break

    if insert_idx is None:
        # Section not found, append at end
        lines.append("")
        lines.append(section_header)
        lines.append(new_line)
    else:
        lines.insert(insert_idx, new_line)

    post.content = "\n".join(lines)

    # Update last-updated
    post.metadata["last-updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with open(target, "wb") as f:
        fm.dump(post, f)

    write_audit_log(vault_path, "agent", target, "add-task", f"title={title} priority={priority} owner={owner}")
    print(json.dumps({"status": "ok", "action": "add-task", "title": title, "file": str(target)}))


def mark_done(vault_path: Path, target: Path, task_id: int):
    import frontmatter as fm
    post = fm.load(str(target))
    content = post.content

    lines = content.split("\n")
    count = 0
    found = False
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*-\s+\[)([ xX])(\].+)$", line)
        if m:
            count += 1
            if count == task_id:
                lines[i] = m.group(1) + "x" + m.group(3)
                found = True
                break

    if not found:
        print(json.dumps({"error": "ERR_TASK_NOT_FOUND", "message": f"Task ID {task_id} not found"}))
        sys.exit(1)

    post.content = "\n".join(lines)
    post.metadata["last-updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    with open(target, "wb") as f:
        fm.dump(post, f)

    write_audit_log(vault_path, "agent", target, "mark-done", f"task_id={task_id}")
    print(json.dumps({"status": "ok", "action": "mark-done", "task_id": task_id, "file": str(target)}))


def main():
    parser = argparse.ArgumentParser(description="Write to vault files")
    parser.add_argument("vault_path", help="Path to vault directory")
    parser.add_argument("--file", required=True)
    parser.add_argument("--action", required=True, choices=["add-task", "mark-done"])
    parser.add_argument("--title", help="Task title (for add-task)")
    parser.add_argument("--priority", help="Priority: critical/important/nice (for add-task)")
    parser.add_argument("--owner", help="Owner name (for add-task)")
    parser.add_argument("--task-id", type=int, dest="task_id", help="Task ID to mark done")
    args = parser.parse_args()

    vault = Path(args.vault_path)
    if not vault.exists():
        print(json.dumps({"error": "ERR_VAULT_NOT_FOUND", "message": str(vault)}))
        sys.exit(1)

    target = discover_file(vault, args.file)
    if target is None:
        print(json.dumps({"error": "ERR_FILE_NOT_FOUND", "message": args.file}))
        sys.exit(1)

    if args.action == "add-task":
        if not args.title or not args.priority or not args.owner:
            print(json.dumps({"error": "ERR_MISSING_ARGS", "message": "--title, --priority, --owner required for add-task"}))
            sys.exit(1)
        add_task(vault, target, args.title, args.priority, args.owner)

    elif args.action == "mark-done":
        if args.task_id is None:
            print(json.dumps({"error": "ERR_MISSING_ARGS", "message": "--task-id required for mark-done"}))
            sys.exit(1)
        mark_done(vault, target, args.task_id)


if __name__ == "__main__":
    main()
''')

print("Workspace generated successfully.")
print(f"Vault path: {vault}")
print(f"Real open-questions file: {real_oq}")