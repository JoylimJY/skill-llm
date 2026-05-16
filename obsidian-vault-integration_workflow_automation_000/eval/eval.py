#!/usr/bin/env python3
"""
Evaluation script for the Obsidian vault integration task.

Checks:
1. The 'Database migration script review' task (owned by Bob, critical) is marked done
2. A new critical-priority task 'Security audit for payment module' assigned to Elena was added
3. The audit log exists and contains at least 2 write entries referencing open-questions/legacy-items
"""
import sys
import json
import re
from pathlib import Path
from datetime import datetime

try:
    import frontmatter
except ImportError:
    print(json.dumps({
        "passed": False,
        "score": 0.0,
        "checks": [{"name": "dependency_check", "passed": False, "detail": "python-frontmatter not installed in eval env"}]
    }))
    sys.exit(0)


def find_real_oq_file(vault: Path) -> Path | None:
    """Find the file with type: open-questions via frontmatter."""
    for md_file in vault.rglob("*.md"):
        try:
            post = frontmatter.load(str(md_file))
            if post.metadata.get("type") == "open-questions":
                return md_file
        except Exception:
            continue
    return None


def parse_tasks(content: str) -> list[dict]:
    tasks = []
    task_id = 0
    current_priority = "nice"
    for line in content.split("\n"):
        header_lower = line.lower()
        if "## critical" in header_lower:
            current_priority = "critical"
        elif "## important" in header_lower:
            current_priority = "important"
        elif "## nice" in header_lower:
            current_priority = "nice"

        m = re.match(
            r"^\s*-\s+\[([ xX])\]\s+(?:\*\*\[(\w+)\]\*\*\s+)?(?:@(\w+):\s+)?(.+)$",
            line,
        )
        if not m:
            continue
        checked, inline_priority, owner, title = m.groups()
        status = "done" if checked.lower() == "x" else "todo"
        priority_map = {"critical": "critical", "important": "important", "nice": "nice"}
        priority = priority_map.get(inline_priority, current_priority) if inline_priority else current_priority
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


def main(workspace: str):
    checks = []
    workspace_path = Path(workspace)
    vault = workspace_path / "company-vault"

    # ── Check 0: Vault exists ────────────────────────────────────────────────
    if not vault.exists():
        checks.append({
            "name": "vault_exists",
            "passed": False,
            "detail": f"Vault directory not found at {vault}"
        })
        score = 0.0
        result = {"passed": False, "score": score, "checks": checks}
        print(json.dumps(result, indent=2))
        return

    checks.append({"name": "vault_exists", "passed": True, "detail": str(vault)})

    # ── Check 1: Real open-questions file found via frontmatter ─────────────
    real_oq = find_real_oq_file(vault)
    if real_oq is None:
        checks.append({
            "name": "open_questions_file_found",
            "passed": False,
            "detail": "No file with frontmatter 'type: open-questions' found in vault"
        })
        score = 0.1
        result = {"passed": False, "score": score, "checks": checks}
        print(json.dumps(result, indent=2))
        return

    # Ensure it's NOT the wrong file (e.g. engineering/open-questions.md which has type: brainstorm-notes)
    checks.append({
        "name": "open_questions_file_found",
        "passed": True,
        "detail": f"Found at: {real_oq}"
    })

    # ── Check 2: 'Database migration script review' task is marked done ──────
    try:
        post = frontmatter.load(str(real_oq))
        tasks = parse_tasks(post.content)

        migration_tasks = [
            t for t in tasks
            if "database migration script review" in t["title"].lower()
        ]

        if not migration_tasks:
            checks.append({
                "name": "migration_task_marked_done",
                "passed": False,
                "detail": "Task 'Database migration script review' not found in file"
            })
        elif all(t["status"] != "done" for t in migration_tasks):
            checks.append({
                "name": "migration_task_marked_done",
                "passed": False,
                "detail": f"Task found but status is '{migration_tasks[0]['status']}', expected 'done'"
            })
        else:
            checks.append({
                "name": "migration_task_marked_done",
                "passed": True,
                "detail": f"Task correctly marked done (task_id={migration_tasks[0]['id']})"
            })
    except Exception as e:
        checks.append({
            "name": "migration_task_marked_done",
            "passed": False,
            "detail": f"Exception reading file: {e}"
        })

    # ── Check 3: New task 'Security audit for payment module' added ──────────
    try:
        post = frontmatter.load(str(real_oq))
        tasks = parse_tasks(post.content)

        security_tasks = [
            t for t in tasks
            if "security audit for payment module" in t["title"].lower()
        ]

        if not security_tasks:
            checks.append({
                "name": "security_task_added",
                "passed": False,
                "detail": "Task 'Security audit for payment module' not found in file"
            })
        else:
            st = security_tasks[0]
            detail_parts = []
            sub_passed = True

            if st["priority"] != "critical":
                detail_parts.append(f"priority is '{st['priority']}', expected 'critical'")
                sub_passed = False

            if st["owner"].lower() != "elena":
                detail_parts.append(f"owner is '{st['owner']}', expected 'Elena'")
                sub_passed = False

            if st["status"] != "todo":
                detail_parts.append(f"status is '{st['status']}', expected 'todo'")
                sub_passed = False

            if sub_passed:
                checks.append({
                    "name": "security_task_added",
                    "passed": True,
                    "detail": f"Task correctly added: priority=critical, owner=Elena, status=todo"
                })
            else:
                checks.append({
                    "name": "security_task_added",
                    "passed": False,
                    "detail": "; ".join(detail_parts)
                })
    except Exception as e:
        checks.append({
            "name": "security_task_added",
            "passed": False,
            "detail": f"Exception reading file: {e}"
        })

    # ── Check 4: Audit log exists and has write entries ─────────────────────
    audit_log = vault / ".vault-audit.log"
    if not audit_log.exists():
        checks.append({
            "name": "audit_log_exists",
            "passed": False,
            "detail": f"Audit log not found at {audit_log}"
        })
    else:
        try:
            log_content = audit_log.read_text()
            # Count write entries that mention our file types
            relevant_lines = [
                l for l in log_content.strip().split("\n")
                if l.strip() and ("add-task" in l or "mark-done" in l)
            ]
            if len(relevant_lines) >= 2:
                checks.append({
                    "name": "audit_log_exists",
                    "passed": True,
                    "detail": f"Audit log contains {len(relevant_lines)} write entries"
                })
            elif len(relevant_lines) == 1:
                checks.append({
                    "name": "audit_log_exists",
                    "passed": False,
                    "detail": f"Audit log only has {len(relevant_lines)} write entry; expected at least 2 (add-task + mark-done)"
                })
            else:
                checks.append({
                    "name": "audit_log_exists",
                    "passed": False,
                    "detail": f"Audit log exists but contains no write entries. Content: {log_content[:200]}"
                })
        except Exception as e:
            checks.append({
                "name": "audit_log_exists",
                "passed": False,
                "detail": f"Exception reading audit log: {e}"
            })

    # ── Check 5: Wrong distractor files were NOT modified ────────────────────
    try:
        # The brainstorm-notes file should NOT have been modified with tasks
        wrong_oq = vault / "engineering" / "open-questions.md"
        if wrong_oq.exists():
            wrong_post = frontmatter.load(str(wrong_oq))
            wrong_tasks = parse_tasks(wrong_post.content)
            security_in_wrong = [t for t in wrong_tasks if "security audit" in t["title"].lower()]
            migration_done_in_wrong = [t for t in wrong_tasks if "database migration" in t["title"].lower() and t["status"] == "done"]
            if security_in_wrong or migration_done_in_wrong:
                checks.append({
                    "name": "correct_file_targeted",
                    "passed": False,
                    "detail": "Agent incorrectly modified the brainstorm-notes file instead of the real open-questions file"
                })
            else:
                checks.append({
                    "name": "correct_file_targeted",
                    "passed": True,
                    "detail": "Distractor file was not incorrectly modified"
                })
        else:
            checks.append({
                "name": "correct_file_targeted",
                "passed": True,
                "detail": "Distractor file check: file not present or not modified"
            })
    except Exception as e:
        checks.append({
            "name": "correct_file_targeted",
            "passed": True,
            "detail": f"Could not verify distractor file (treating as pass): {e}"
        })

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weights: file_found=0.1, migration_done=0.3, security_added=0.35, audit_log=0.15, correct_file=0.1
    weights = {
        "vault_exists": 0.0,
        "open_questions_file_found": 0.1,
        "migration_task_marked_done": 0.30,
        "security_task_added": 0.35,
        "audit_log_exists": 0.15,
        "correct_file_targeted": 0.10,
    }
    score = 0.0
    for c in checks:
        if c["passed"]:
            score += weights.get(c["name"], 0.0)

    all_critical = (
        any(c["name"] == "migration_task_marked_done" and c["passed"] for c in checks) and
        any(c["name"] == "security_task_added" and c["passed"] for c in checks)
    )

    result = {
        "passed": all_critical,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    main(sys.argv[1])