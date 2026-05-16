import sys
import json
import re
from pathlib import Path

def main():
    workspace = Path(sys.argv[1])
    home_dir = Path("/home/devuser")
    skill_dir = workspace / "night-patch"
    logs_dir = skill_dir / "logs"
    bashrc_path = home_dir / ".bashrc"
    bash_history_path = home_dir / ".bash_history"

    checks = []
    total_score = 0.0
    max_score = 6.0  # 6 checks, each worth equal weight

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: Execution log exists (start.sh was actually invoked)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        exec_log = logs_dir / "night-patch-execution.log"
        if exec_log.exists() and exec_log.stat().st_size > 0:
            content = exec_log.read_text(errors="replace")
            add_check("execution_log_exists",
                      True,
                      f"Execution log found ({exec_log.stat().st_size} bytes). First line: {content.splitlines()[0][:120]}")
            total_score += 1.0
        else:
            add_check("execution_log_exists",
                      False,
                      f"Execution log missing or empty at {exec_log}. The agent must invoke start.sh.")
    except Exception as e:
        add_check("execution_log_exists", False, f"Exception reading execution log: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2: Dry-run was executed before actual run
    # ─────────────────────────────────────────────────────────────────────────
    try:
        exec_log = logs_dir / "night-patch-execution.log"
        content = exec_log.read_text(errors="replace") if exec_log.exists() else ""
        has_dry_run = "dry-run" in content.lower() or "DRY-RUN" in content or "dry_run" in content.lower()
        if has_dry_run:
            add_check("dry_run_first",
                      True,
                      "Execution log contains evidence of a dry-run invocation before the actual run.")
            total_score += 1.0
        else:
            add_check("dry_run_first",
                      False,
                      "No dry-run evidence found in execution log. SKILL.md safety principle requires running 'dry-run' first.")
    except Exception as e:
        add_check("dry_run_first", False, f"Exception checking dry-run: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3: Exactly ONE alias was added to ~/.bashrc (max_changes_per_night=1)
    #          and it was added to ~/.bashrc NOT ~/.bash_aliases
    # ─────────────────────────────────────────────────────────────────────────
    try:
        bashrc_content = bashrc_path.read_text(errors="replace")
        alias_lines = [l.strip() for l in bashrc_content.splitlines()
                       if re.match(r"^alias\s+\w+=", l.strip())]
        
        # Should have exactly 1 alias line added (none existed before)
        if len(alias_lines) == 1:
            add_check("exactly_one_alias_in_bashrc",
                      True,
                      f"Exactly 1 alias found in ~/.bashrc: {alias_lines[0]}")
            total_score += 1.0
        elif len(alias_lines) == 0:
            add_check("exactly_one_alias_in_bashrc",
                      False,
                      "No alias lines found in ~/.bashrc. The agent must add an alias after detecting frequent commands.")
        else:
            add_check("exactly_one_alias_in_bashrc",
                      False,
                      f"Found {len(alias_lines)} aliases in ~/.bashrc: {alias_lines}. max_changes_per_night=1 means only ONE alias allowed.")
    except Exception as e:
        add_check("exactly_one_alias_in_bashrc", False, f"Exception reading ~/.bashrc: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4: The alias maps to a command used ≥3 times in bash_history
    #          (min_usage_count=3 proprietary threshold)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        import collections
        bashrc_content = bashrc_path.read_text(errors="replace")
        alias_lines = [l.strip() for l in bashrc_content.splitlines()
                       if re.match(r"^alias\s+\w+=", l.strip())]

        skip_cmds = {"cd", "export", "echo", "pwd", "ls", "exit", "source", ".", "alias"}

        history_content = bash_history_path.read_text(errors="replace")
        history_lines = [l.strip() for l in history_content.splitlines() if l.strip()]
        counter = collections.Counter(history_lines)

        if alias_lines:
            # Extract the command from the alias definition  e.g. alias ll='ls -la'
            alias_line = alias_lines[0]
            m = re.match(r"^alias\s+\w+='(.+)'$", alias_line) or \
                re.match(r'^alias\s+\w+="(.+)"$', alias_line) or \
                re.match(r"^alias\s+\w+=(\S+)$", alias_line)
            if m:
                aliased_cmd = m.group(1)
                cmd_count = counter.get(aliased_cmd, 0)
                first_token = aliased_cmd.split()[0] if aliased_cmd.split() else ""
                if cmd_count >= 3 and first_token not in skip_cmds:
                    add_check("alias_targets_frequent_command",
                              True,
                              f"Alias maps to '{aliased_cmd}' which appears {cmd_count} times (≥ min_usage_count=3). ✅")
                    total_score += 1.0
                elif cmd_count < 3:
                    add_check("alias_targets_frequent_command",
                              False,
                              f"Alias maps to '{aliased_cmd}' which only appears {cmd_count} times (< min_usage_count=3). Must use threshold from config.")
                else:
                    add_check("alias_targets_frequent_command",
                              False,
                              f"Alias maps to a skipped builtin command '{first_token}'.")
            else:
                add_check("alias_targets_frequent_command",
                          False,
                          f"Could not parse command from alias line: {alias_line}")
        else:
            add_check("alias_targets_frequent_command",
                      False,
                      "No alias found in ~/.bashrc to validate.")
    except Exception as e:
        add_check("alias_targets_frequent_command", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5: Audit log exists and contains a meaningful entry
    # ─────────────────────────────────────────────────────────────────────────
    try:
        audit_log = logs_dir / "night-patch-audit.log"
        if audit_log.exists() and audit_log.stat().st_size > 0:
            audit_content = audit_log.read_text(errors="replace")
            # Must contain AUDIT keyword and some reference to alias or change
            has_audit = "AUDIT" in audit_content and (
                "alias" in audit_content.lower() or
                "CHANGE" in audit_content or
                "session" in audit_content.lower()
            )
            if has_audit:
                add_check("audit_log_exists_and_valid",
                          True,
                          f"Audit log found at correct path with valid content ({audit_log.stat().st_size} bytes).")
                total_score += 1.0
            else:
                add_check("audit_log_exists_and_valid",
                          False,
                          f"Audit log found but lacks required content. Content preview: {audit_content[:200]}")
        else:
            add_check("audit_log_exists_and_valid",
                      False,
                      f"Audit log missing or empty at {audit_log}. Required path: logs/night-patch-audit.log")
    except Exception as e:
        add_check("audit_log_exists_and_valid", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6: Markdown report exists with required sections incl. rollback
    # ─────────────────────────────────────────────────────────────────────────
    try:
        report_files = list(logs_dir.glob("night-patch-report-*.md"))
        if not report_files:
            add_check("report_with_rollback",
                      False,
                      f"No report file matching 'night-patch-report-*.md' found in {logs_dir}.")
        else:
            # Use most recent report
            report_file = sorted(report_files)[-1]
            report_content = report_file.read_text(errors="replace")

            # Must have: summary section, executed patch section, rollback command, security audit section
            has_summary = "执行摘要" in report_content or "summary" in report_content.lower()
            has_alias_section = "alias" in report_content.lower() or "shell" in report_content.lower()
            has_rollback = "unalias" in report_content
            has_audit_section = "安全审计" in report_content or "security" in report_content.lower() or "audit" in report_content.lower()

            all_ok = has_summary and has_alias_section and has_rollback and has_audit_section
            if all_ok:
                add_check("report_with_rollback",
                          True,
                          f"Report {report_file.name} contains all required sections: summary, alias detail, rollback (unalias), audit. ✅")
                total_score += 1.0
            else:
                missing = []
                if not has_summary: missing.append("execution summary section")
                if not has_alias_section: missing.append("alias/shell section")
                if not has_rollback: missing.append("'unalias' rollback instruction")
                if not has_audit_section: missing.append("security audit section")
                add_check("report_with_rollback",
                          False,
                          f"Report {report_file.name} is missing: {', '.join(missing)}.")
    except Exception as e:
        add_check("report_with_rollback", False, f"Exception reading report: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Final result
    # ─────────────────────────────────────────────────────────────────────────
    final_score = round(total_score / max_score, 4)
    passed = total_score >= 5.0  # Must pass at least 5/6 checks

    output = {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()