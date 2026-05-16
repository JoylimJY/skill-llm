#!/usr/bin/env python3
"""
Evaluation script for the compliance email audit task.
Checks:
  1. Agent used --confirm when fetching > 100 emails
  2. Agent polled fetch-status until completed (≥ 2 calls to fetch-status for same task_id)
  3. Agent ran summarize --task-id <task_id> immediately after fetch completed
  4. A Markdown summary report exists referencing the correct task_id
  5. Agent searched for compliance officer emails locally
  6. Agent read at least one compliance officer email (via read command)
  7. Agent exported the full mailbox to a CSV file with correct columns
"""
import sys
import json
import csv
import re
from pathlib import Path

def load_audit_log(workspace: Path):
    log_path = workspace / "logs" / "cli_audit.jsonl"
    if not log_path.exists():
        return []
    entries = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0
    weight_per_check = 1.0 / 7  # 7 checks

    audit = load_audit_log(workspace)

    # ── Helper: find all calls to a command ──────────────────────────────────
    def calls(cmd):
        return [e for e in audit if e.get("command") == cmd]

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 1: fetch was called with limit > 100 AND confirm=True
    # ────────────────────────────────────────────────────────────────────────
    fetch_calls = calls("fetch")
    confirmed_large_fetch = False
    task_id_used = None
    for fc in fetch_calls:
        a = fc.get("args", {})
        if a.get("limit", 0) > 100 and a.get("confirm", False):
            confirmed_large_fetch = True
            # Find the task_id from fetch-status calls that followed
            break

    checks.append({
        "name": "fetch_with_confirm_for_large_limit",
        "passed": confirmed_large_fetch,
        "detail": (
            "Agent called fetch with limit > 100 AND --confirm flag."
            if confirmed_large_fetch
            else f"No fetch call found with limit>100 and confirm=True. Fetch calls: {fetch_calls}"
        )
    })
    if confirmed_large_fetch:
        total_score += weight_per_check

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 2: fetch-status was polled at least twice for the same task_id
    # (proving async polling behavior)
    # ────────────────────────────────────────────────────────────────────────
    fetch_status_calls = calls("fetch-status")
    task_id_poll_counts = {}
    for fsc in fetch_status_calls:
        tid = fsc.get("args", {}).get("task_id", "")
        task_id_poll_counts[tid] = task_id_poll_counts.get(tid, 0) + 1

    polled_correctly = any(v >= 2 for v in task_id_poll_counts.values())
    if polled_correctly:
        task_id_used = max(task_id_poll_counts, key=task_id_poll_counts.get)

    checks.append({
        "name": "fetch_status_polled_until_completed",
        "passed": polled_correctly,
        "detail": (
            f"Agent polled fetch-status at least 2 times for task_id={task_id_used}."
            if polled_correctly
            else f"fetch-status not polled enough times. Counts: {task_id_poll_counts}"
        )
    })
    if polled_correctly:
        total_score += weight_per_check

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 3: summarize was called with the correct task_id after fetch
    # ────────────────────────────────────────────────────────────────────────
    summarize_calls = calls("summarize")
    summarize_with_task_id = False
    summary_task_id = None
    for sc in summarize_calls:
        a = sc.get("args", {})
        if a.get("task_id") and (task_id_used is None or a["task_id"] == task_id_used):
            summarize_with_task_id = True
            summary_task_id = a["task_id"]
            break

    checks.append({
        "name": "summarize_called_with_task_id_after_fetch",
        "passed": summarize_with_task_id,
        "detail": (
            f"Agent called summarize --task-id {summary_task_id} after fetch completed."
            if summarize_with_task_id
            else f"summarize not called with a task_id. Summarize calls: {summarize_calls}"
        )
    })
    if summarize_with_task_id:
        total_score += weight_per_check

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 4: A Markdown summary report file exists and contains required sections
    # ────────────────────────────────────────────────────────────────────────
    summary_md_files = list(workspace.rglob("summary_*.md"))
    report_ok = False
    report_detail = "No summary_*.md file found."

    for md_file in summary_md_files:
        try:
            content = md_file.read_text()
            has_stats = "Overall Statistics" in content or "Total Emails" in content
            has_action = "Action Required" in content
            has_compliance = "Compliance" in content or "Regulatory" in content
            if has_stats and has_action and has_compliance:
                report_ok = True
                report_detail = f"Valid Markdown report found at {md_file.name} with all required sections."
                break
            else:
                report_detail = f"File {md_file.name} missing sections: stats={has_stats}, action={has_action}, compliance={has_compliance}"
        except Exception as ex:
            report_detail = f"Error reading {md_file}: {ex}"

    checks.append({
        "name": "markdown_summary_report_with_sections",
        "passed": report_ok,
        "detail": report_detail
    })
    if report_ok:
        total_score += weight_per_check

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 5: Agent searched locally for compliance officer emails
    # ────────────────────────────────────────────────────────────────────────
    search_calls = calls("search")
    compliance_search = False
    COMPLIANCE_OFFICER = "margaret.thornton@finregulator.gov"
    for sc in search_calls:
        a = sc.get("args", {})
        sender = (a.get("sender") or "").lower()
        query = (a.get("query") or "").lower()
        if COMPLIANCE_OFFICER in sender or "margaret" in sender or "thornton" in sender \
           or "compliance" in query or "regulatory" in query or "finregulator" in sender:
            compliance_search = True
            break

    checks.append({
        "name": "local_search_for_compliance_emails",
        "passed": compliance_search,
        "detail": (
            "Agent searched locally for compliance officer emails."
            if compliance_search
            else f"No search call found targeting compliance officer. Search calls: {search_calls}"
        )
    })
    if compliance_search:
        total_score += weight_per_check

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 6: Agent read at least one compliance email via the read command
    # ────────────────────────────────────────────────────────────────────────
    read_calls = calls("read")
    read_compliance = False
    try:
        import sqlite3
        db_path = workspace / "data/emails/mail_index.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT message_id FROM emails WHERE sender = ?", (COMPLIANCE_OFFICER,))
        compliance_ids = {row["message_id"] for row in cur.fetchall()}
        conn.close()

        for rc in read_calls:
            if rc.get("args", {}).get("message_id", "") in compliance_ids:
                read_compliance = True
                break
    except Exception as ex:
        read_detail_extra = f" (DB error: {ex})"
    else:
        read_detail_extra = ""

    checks.append({
        "name": "read_compliance_officer_email",
        "passed": read_compliance,
        "detail": (
            f"Agent read at least one email from {COMPLIANCE_OFFICER}."
            if read_compliance
            else f"No read call found for compliance officer emails.{read_detail_extra} Read calls: {[rc.get('args',{}).get('message_id','') for rc in read_calls]}"
        )
    })
    if read_compliance:
        total_score += weight_per_check

    # ────────────────────────────────────────────────────────────────────────
    # CHECK 7: CSV export exists with correct columns and non-trivial row count
    # ────────────────────────────────────────────────────────────────────────
    REQUIRED_CSV_COLUMNS = {"message_id", "subject", "sender", "date", "folder", "is_read"}
    csv_files = list(workspace.rglob("*.csv"))
    # Filter out the distractor old_export_2023.csv by content validation
    export_ok = False
    export_detail = "No valid CSV export found."

    for csv_file in csv_files:
        try:
            if csv_file.name == "old_export_2023.csv":
                continue
            with open(csv_file, newline="") as f:
                reader = csv.DictReader(f)
                headers = set(reader.fieldnames or [])
                if not REQUIRED_CSV_COLUMNS.issubset(headers):
                    export_detail = f"{csv_file.name}: missing columns. Has: {headers}"
                    continue
                rows = list(reader)
                if len(rows) >= 100:  # Should have all ~150+ emails
                    export_ok = True
                    export_detail = f"Valid CSV export at {csv_file.name} with {len(rows)} rows and correct columns."
                    break
                else:
                    export_detail = f"{csv_file.name}: only {len(rows)} rows, expected ≥ 100."
        except Exception as ex:
            export_detail = f"Error reading {csv_file}: {ex}"

    checks.append({
        "name": "csv_export_with_correct_columns_and_rows",
        "passed": export_ok,
        "detail": export_detail
    })
    if export_ok:
        total_score += weight_per_check

    # ── Final output ─────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = passed_count >= 5  # Must pass at least 5/7

    result = {
        "passed": overall_passed,
        "score": round(total_score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    run_eval(sys.argv[1])