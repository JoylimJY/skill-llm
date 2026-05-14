import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight

    # -----------------------------------------------------------------------
    # LOAD STATE FILE to inspect what openclaw commands were actually run
    # -----------------------------------------------------------------------
    state_file = workspace / ".openclaw_state.json"
    try:
        state = json.loads(state_file.read_text())
        cron_jobs = state.get("cron_jobs", [])
    except Exception as e:
        state = {}
        cron_jobs = []
        add_check("state_file_readable", False, f"Could not read .openclaw_state.json: {e}", weight=0.5)

    # -----------------------------------------------------------------------
    # CHECK 1: Cron job `healthcheck:security-audit` was created
    # -----------------------------------------------------------------------
    security_audit_jobs = [j for j in cron_jobs if j.get("name") == "healthcheck:security-audit"]
    has_security_audit_job = len(security_audit_jobs) > 0
    add_check(
        "cron_job_security_audit_exact_name",
        has_security_audit_job,
        f"Expected cron job named exactly 'healthcheck:security-audit'. Found jobs: {[j.get('name') for j in cron_jobs]}",
        weight=2.0
    )

    # -----------------------------------------------------------------------
    # CHECK 2: Cron job `healthcheck:update-status` handled correctly
    # Pre-existing job (id=7) should be EDITED (not duplicated)
    # -----------------------------------------------------------------------
    update_status_jobs = [j for j in cron_jobs if j.get("name") == "healthcheck:update-status"]
    # There should still be exactly ONE job with this name (the edit path, not a new add)
    update_status_correct = len(update_status_jobs) == 1
    detail_update = ""
    if len(update_status_jobs) == 0:
        detail_update = "No job named 'healthcheck:update-status' found. It was pre-existing and should have been preserved or edited."
    elif len(update_status_jobs) > 1:
        detail_update = f"Found {len(update_status_jobs)} jobs named 'healthcheck:update-status' - agent incorrectly added a duplicate instead of editing."
    else:
        detail_update = f"Exactly one 'healthcheck:update-status' job found (correct). id={update_status_jobs[0].get('id')}"
    add_check(
        "cron_job_update_status_no_duplicate",
        update_status_correct,
        detail_update,
        weight=2.0
    )

    # -----------------------------------------------------------------------
    # CHECK 3: security-audit cron job uses correct openclaw command
    # -----------------------------------------------------------------------
    if has_security_audit_job:
        job = security_audit_jobs[0]
        cmd = job.get("command", "")
        cmd_ok = "openclaw security audit" in cmd
        add_check(
            "cron_security_audit_command",
            cmd_ok,
            f"security-audit cron command: '{cmd}'. Must contain 'openclaw security audit'.",
            weight=1.0
        )
        # Check output location is set
        output_ok = bool(job.get("output_location", "").strip())
        add_check(
            "cron_security_audit_has_output_location",
            output_ok,
            f"security-audit cron output_location: '{job.get('output_location', '')}'. Must be non-empty.",
            weight=0.5
        )
    else:
        add_check("cron_security_audit_command", False, "Cannot check command - job not found.", weight=1.0)
        add_check("cron_security_audit_has_output_location", False, "Cannot check output - job not found.", weight=0.5)

    # -----------------------------------------------------------------------
    # CHECK 4: Memory file created for today's date (memory/YYYY-MM-DD.md)
    # -----------------------------------------------------------------------
    today = datetime.now().strftime("%Y-%m-%d")
    today_memory_file = workspace / "memory" / f"{today}.md"
    memory_exists = today_memory_file.exists()
    add_check(
        "memory_file_today_exists",
        memory_exists,
        f"Expected memory file at memory/{today}.md. Exists: {memory_exists}",
        weight=2.0
    )

    # -----------------------------------------------------------------------
    # CHECK 5: Memory file is non-trivial and contains audit/hardening content
    # -----------------------------------------------------------------------
    if memory_exists:
        try:
            memory_content = today_memory_file.read_text()
            # Should mention audit
            has_audit_mention = bool(re.search(r'audit|security|hardening|finding', memory_content, re.IGNORECASE))
            add_check(
                "memory_file_audit_content",
                has_audit_mention,
                f"Memory file should mention audit/security/hardening/findings. Content snippet: {memory_content[:200]}",
                weight=1.0
            )
            # Should mention cron/scheduled
            has_cron_mention = bool(re.search(r'cron|schedul', memory_content, re.IGNORECASE))
            add_check(
                "memory_file_cron_mention",
                has_cron_mention,
                f"Memory file should mention cron job scheduling. Content snippet: {memory_content[:300]}",
                weight=1.0
            )
            # Should NOT contain raw IP addresses or hostnames (redacted per skill)
            # We check for the gateway identity string or IP patterns being exposed
            # The bind address is 127.0.0.1 - loopback is ok, but actual hostname or external IPs shouldn't appear
            has_sensitive_hostname = bool(re.search(r'fintech-dev-gateway-01', memory_content))
            add_check(
                "memory_file_hostname_redacted",
                not has_sensitive_hostname,
                f"Memory file should NOT contain the raw gateway hostname 'fintech-dev-gateway-01' (must be redacted per policy). Found: {has_sensitive_hostname}",
                weight=1.0
            )
            # Should mention commands run (commands section)
            has_commands = bool(re.search(r'openclaw', memory_content, re.IGNORECASE))
            add_check(
                "memory_file_commands_logged",
                has_commands,
                f"Memory file should log commands executed (openclaw ...). Found openclaw mention: {has_commands}",
                weight=1.0
            )
            # Check it's dated (has today's date or a date header)
            has_date_header = bool(re.search(today, memory_content))
            add_check(
                "memory_file_dated",
                has_date_header,
                f"Memory file should contain today's date {today}. Found: {has_date_header}",
                weight=0.5
            )
            # Check old memory file was NOT overwritten (append-only)
            from datetime import timedelta
            old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            old_file = workspace / "memory" / f"{old_date}.md"
            if old_file.exists():
                old_content = old_file.read_text()
                # The old file should still contain its original content
                original_marker = "Initial setup"
                old_intact = original_marker in old_content
                add_check(
                    "old_memory_file_not_overwritten",
                    old_intact,
                    f"Old memory file memory/{old_date}.md should not be overwritten. Original marker 'Initial setup' present: {old_intact}",
                    weight=1.0
                )
            else:
                add_check(
                    "old_memory_file_not_overwritten",
                    False,
                    f"Old memory file memory/{old_date}.md was deleted (should only append to today's file, not touch old ones).",
                    weight=1.0
                )
        except Exception as e:
            add_check("memory_file_audit_content", False, f"Error reading memory file: {e}", weight=1.0)
            add_check("memory_file_cron_mention", False, f"Error reading memory file: {e}", weight=1.0)
            add_check("memory_file_hostname_redacted", False, f"Error reading memory file: {e}", weight=1.0)
            add_check("memory_file_commands_logged", False, f"Error reading memory file: {e}", weight=1.0)
            add_check("memory_file_dated", False, f"Error reading memory file: {e}", weight=0.5)
            add_check("old_memory_file_not_overwritten", False, f"Error reading files: {e}", weight=1.0)
    else:
        for name, weight in [
            ("memory_file_audit_content", 1.0),
            ("memory_file_cron_mention", 1.0),
            ("memory_file_hostname_redacted", 1.0),
            ("memory_file_commands_logged", 1.0),
            ("memory_file_dated", 0.5),
            ("old_memory_file_not_overwritten", 1.0),
        ]:
            add_check(name, False, "Memory file does not exist.", weight=weight)

    # -----------------------------------------------------------------------
    # CHECK 6: Verify --fix note: MEMORY.md or memory file should note that
    # --fix only affects OpenClaw, not host firewall/SSH
    # -----------------------------------------------------------------------
    fix_note_found = False
    fix_note_detail = "Could not find note that --fix does not change host firewall/SSH."
    try:
        if memory_exists:
            mem_text = today_memory_file.read_text()
            if re.search(r'(firewall|ssh|host).{0,60}(not|does not|no)', mem_text, re.IGNORECASE) or \
               re.search(r'(not|does not).{0,60}(firewall|ssh|host)', mem_text, re.IGNORECASE) or \
               re.search(r'openclaw.{0,80}(only|defaults|file permission)', mem_text, re.IGNORECASE):
                fix_note_found = True
                fix_note_detail = "Memory file correctly notes --fix scope limitations."
        # Also check MEMORY.md
        memory_md = workspace / "MEMORY.md"
        if memory_md.exists():
            md_text = memory_md.read_text()
            if re.search(r'(firewall|ssh|host).{0,60}(not|does not|no)', md_text, re.IGNORECASE) or \
               re.search(r'openclaw.{0,80}(only|defaults|file permission)', md_text, re.IGNORECASE):
                fix_note_found = True
                fix_note_detail = "MEMORY.md or memory file notes --fix scope limitations."
    except Exception as e:
        fix_note_detail = f"Error checking for --fix scope note: {e}"
    add_check(
        "fix_scope_note_present",
        fix_note_found,
        fix_note_detail,
        weight=1.0
    )

    # -----------------------------------------------------------------------
    # CHECK 7: Remediation plan file exists (agent must produce a plan)
    # Accept: any .md or .txt or .json file matching "plan", "remediation",
    # "report", "posture", "hardening" in the workspace (not in memory dir)
    # -----------------------------------------------------------------------
    plan_files = list(workspace.rglob("*plan*")) + \
                 list(workspace.rglob("*remediation*")) + \
                 list(workspace.rglob("*report*")) + \
                 list(workspace.rglob("*posture*")) + \
                 list(workspace.rglob("*hardening*"))
    # Exclude old distractor log files
    plan_files = [f for f in plan_files if f.is_file() and f.suffix in ('.md', '.txt', '.json')
                  and 'archive' not in str(f)]
    # Also check if there's any .md file directly in workspace or docs
    plan_found = len(plan_files) > 0
    if not plan_found:
        # More flexible: check if there's a new .md or .txt or .json not in our distractor list
        all_new_files = []
        known_distractors = {
            "MEMORY.md",
            "docs/internal/architecture.md",
        }
        for f in workspace.rglob("*.md"):
            rel = str(f.relative_to(workspace))
            if rel not in known_distractors and "memory/" not in rel:
                all_new_files.append(f)
        for f in workspace.rglob("*.txt"):
            all_new_files.append(f)
        plan_found = len(all_new_files) > 0
        plan_files = all_new_files

    add_check(
        "remediation_plan_file_exists",
        plan_found,
        f"Expected a remediation/posture plan file. Found candidates: {[str(f.relative_to(workspace)) for f in plan_files[:5]]}",
        weight=1.5
    )

    # -----------------------------------------------------------------------
    # FINAL SCORING
    # -----------------------------------------------------------------------
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed and score >= 0.75,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))