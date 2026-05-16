import sys
import json
import csv
import re
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    # ── Helper ────────────────────────────────────────────────────────────────
    def add(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 1 – tasks CSV exists and has correct headers
    # ════════════════════════════════════════════════════════════════════════
    csv_files = list(ws.rglob("*.csv"))
    # Exclude the sample distractor
    task_csvs = [f for f in csv_files if "sample_tasks" not in f.name and "q3_feature" in f.name.lower() or
                 (f.name not in ["sample_tasks.csv"] and any(kw in f.name.lower() for kw in ["task", "action", "q3", "checkout", "scoping", "meeting"]))]
    # Broader: any new CSV not in exports/csv/sample_tasks.csv
    task_csvs = [f for f in csv_files if f != ws / "exports/csv/sample_tasks.csv"]

    csv_found = len(task_csvs) > 0
    csv_path = task_csvs[0] if csv_found else None
    total_score += add("tasks_csv_exists", csv_found,
                       f"Found task CSV at {csv_path}" if csv_found else "No task CSV found (expected output from task_extractor.py)")

    rows = []
    if csv_found:
        try:
            with open(csv_path, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                headers = reader.fieldnames or []
            required_headers = {"task", "owner", "status", "note"}
            has_headers = required_headers.issubset(set(h.lower() for h in headers))
            # No due_date column (free edition omits it)
            no_due_date = "due_date" not in [h.lower() for h in headers]
            total_score += add("csv_correct_headers", has_headers,
                               f"Headers: {headers}. Required: task,owner,status,note")
            total_score += add("csv_no_due_date_column", no_due_date,
                               "Free edition must NOT include due_date column in CSV" if not no_due_date
                               else "Correctly omits due_date column")
        except Exception as e:
            total_score += add("csv_correct_headers", False, f"Error reading CSV: {e}")
            total_score += add("csv_no_due_date_column", False, f"Error reading CSV: {e}")
    else:
        total_score += add("csv_correct_headers", False, "No CSV to check")
        total_score += add("csv_no_due_date_column", False, "No CSV to check")

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 2 – tasks CSV content: status=todo, unassigned owners
    # ════════════════════════════════════════════════════════════════════════
    if rows:
        statuses = [r.get("status", r.get("Status", "")).strip().lower() for r in rows]
        all_todo = all(s == "todo" for s in statuses) and len(statuses) > 0
        total_score += add("csv_all_status_todo", all_todo,
                           f"All statuses must be 'todo'. Found: {set(statuses)}")

        owners = [r.get("owner", r.get("Owner", "")).strip().lower() for r in rows]
        # At least one task must have 'unassigned' (the doc update task has no explicit owner)
        has_unassigned = any(o == "unassigned" for o in owners)
        total_score += add("csv_unassigned_owner_present", has_unassigned,
                           f"At least one task must have owner='unassigned'. Owners found: {owners}")

        # Named owners should NOT be 'tbd', 'n/a', or empty for tasks that DO have owners
        named_owners = [o for o in owners if o not in ("", "unassigned")]
        no_bad_placeholders = not any(o in ("tbd", "n/a", "none", "unknown") for o in named_owners)
        total_score += add("csv_no_bad_owner_placeholders", no_bad_placeholders,
                           f"Named owners should not be tbd/n/a/none/unknown. Found: {named_owners}")

        # At least 4 tasks extracted (5 action lines in raw notes)
        enough_tasks = len(rows) >= 4
        total_score += add("csv_sufficient_tasks", enough_tasks,
                           f"Expected >=4 tasks from 5 action lines, got {len(rows)}")
    else:
        for name in ["csv_all_status_todo", "csv_unassigned_owner_present",
                     "csv_no_bad_owner_placeholders", "csv_sufficient_tasks"]:
            total_score += add(name, False, "No rows to check")

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 3 – meeting recap / summary file exists
    # ════════════════════════════════════════════════════════════════════════
    md_candidates = [f for f in ws.rglob("*.md")
                     if f.name not in ("templates.md",)
                     and "archive" not in str(f)
                     and "exports" not in str(f)
                     and any(kw in f.name.lower() for kw in
                             ["recap", "summary", "meeting", "q3", "checkout", "scoping"])]
    # Also accept any new .md not in references/ archive/
    all_new_mds = [f for f in ws.rglob("*.md")
                   if f != ws / "references/templates.md"
                   and f != ws / "archive/processed/q1_summary.md"
                   and f != ws / "exports/reports/weekly_digest.md"]
    recap_candidates = md_candidates if md_candidates else all_new_mds
    recap_found = len(recap_candidates) > 0
    recap_path = recap_candidates[0] if recap_found else None
    total_score += add("recap_md_exists", recap_found,
                       f"Found recap at {recap_path}" if recap_found else "No recap .md file found")

    recap_text = ""
    if recap_found:
        try:
            recap_text = recap_path.read_text(errors="replace").lower()
        except Exception as e:
            total_score += add("recap_md_readable", False, f"Could not read recap: {e}")
            recap_text = ""
    
    # ════════════════════════════════════════════════════════════════════════
    # CHECK 4 – recap output ORDER (meeting context before summary before key points
    #           before task list before open questions)
    # ════════════════════════════════════════════════════════════════════════
    if recap_text:
        def find_pos(text, patterns):
            for p in patterns:
                m = re.search(p, text, re.IGNORECASE)
                if m:
                    return m.start()
            return -1

        pos_context  = find_pos(recap_text, [r'meeting context', r'## context'])
        pos_summary  = find_pos(recap_text, [r'concise summary', r'## summary', r'meeting summary'])
        pos_keypts   = find_pos(recap_text, [r'key points', r'## key'])
        pos_tasks    = find_pos(recap_text, [r'task list', r'## task'])
        pos_openq    = find_pos(recap_text, [r'open questions', r'unanswered questions'])

        sections_present = all(p >= 0 for p in [pos_context, pos_summary, pos_keypts, pos_tasks, pos_openq])
        total_score += add("recap_all_sections_present", sections_present,
                           f"Positions: context={pos_context}, summary={pos_summary}, "
                           f"keypoints={pos_keypts}, tasks={pos_tasks}, openq={pos_openq}")

        if sections_present:
            correct_order = (pos_context < pos_summary < pos_keypts < pos_tasks < pos_openq)
            total_score += add("recap_correct_section_order", correct_order,
                               "Sections must appear: Meeting Context → Summary → Key Points → Task List → Open Questions. "
                               f"Got order: context={pos_context}, summary={pos_summary}, "
                               f"keypoints={pos_keypts}, tasks={pos_tasks}, openq={pos_openq}")
        else:
            total_score += add("recap_correct_section_order", False,
                               "Cannot check order — not all sections present")
    else:
        total_score += add("recap_all_sections_present", False, "No recap text to check")
        total_score += add("recap_correct_section_order", False, "No recap text to check")

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 5 – recap content correctness
    # ════════════════════════════════════════════════════════════════════════
    if recap_text:
        # Key decisions must be mentioned
        has_payment_widget_decision = "payment widget" in recap_text and (
            "september" in recap_text or "decided" in recap_text or "decision" in recap_text)
        total_score += add("recap_includes_decisions", has_payment_widget_decision,
                           "Recap must mention the payment widget decision for September release")

        # Blockers mentioned
        has_blockers = any(kw in recap_text for kw in ["blocked", "blocker", "security audit", "staging config",
                                                        "compliance"])
        total_score += add("recap_includes_blockers", has_blockers,
                           "Recap must mention blockers (security audit / staging config)")

        # Open questions present
        has_open_questions_content = (
            "compliance" in recap_text or "design freeze" in recap_text or
            ("open questions" in recap_text and len(recap_text.split("open questions")[1].strip()) > 10)
        )
        total_score += add("recap_open_questions_have_content", has_open_questions_content,
                           "Open questions section must contain actual questions from the meeting")

        # Must NOT invent due dates (no hard deadlines not in source)
        invented_deadline = bool(re.search(
            r'\b(by\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+\d{1,2}|'
            r'due\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))',
            recap_text, re.IGNORECASE))
        total_score += add("recap_no_invented_deadlines", not invented_deadline,
                           "Must not invent specific due-date deadlines not present in the source notes"
                           if invented_deadline else "No invented deadlines found")

        # Participants section
        has_participants = any(name.lower() in recap_text for name in
                               ["grace lin", "alice chen", "eva novak", "bob ramirez", "hiro tanaka"])
        total_score += add("recap_includes_participants", has_participants,
                           "Recap must include participant names from the meeting notes")
    else:
        for name in ["recap_includes_decisions", "recap_includes_blockers",
                     "recap_open_questions_have_content", "recap_no_invented_deadlines",
                     "recap_includes_participants"]:
            total_score += add(name, False, "No recap text to check")

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 6 – normalized buckets appear in the structured output
    # ════════════════════════════════════════════════════════════════════════
    if recap_text:
        has_decisions_bucket   = bool(re.search(r'decision', recap_text, re.IGNORECASE))
        has_discussion_bucket  = bool(re.search(r'discussion', recap_text, re.IGNORECASE))
        has_blockers_bucket    = bool(re.search(r'blocker', recap_text, re.IGNORECASE))
        has_next_steps_bucket  = bool(re.search(r'next\s+step', recap_text, re.IGNORECASE))
        all_buckets = has_decisions_bucket and has_discussion_bucket and has_blockers_bucket and has_next_steps_bucket
        total_score += add("recap_normalized_buckets", all_buckets,
                           f"decisions={has_decisions_bucket}, discussion={has_discussion_bucket}, "
                           f"blockers={has_blockers_bucket}, next_steps={has_next_steps_bucket}")
    else:
        total_score += add("recap_normalized_buckets", False, "No recap text to check")

    # ════════════════════════════════════════════════════════════════════════
    # Final score
    # ════════════════════════════════════════════════════════════════════════
    n = len(checks)
    score = round(sum(1.0 for c in checks if c["passed"]) / n, 4) if n else 0.0
    passed = score >= 0.75  # require 75% of checks to pass

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))