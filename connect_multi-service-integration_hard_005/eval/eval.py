import sys
import os
import json
import re
from pathlib import Path

workspace = sys.argv[1]
checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# Load reference data
try:
    with open(os.path.join(workspace, 'issues.json')) as f:
        issues = json.load(f)
    with open(os.path.join(workspace, 'config.json')) as f:
        config = json.load(f)
except Exception as e:
    print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "load_inputs", "passed": False, "detail": str(e)}]}))
    sys.exit(0)

bug_issues = [i for i in issues if 'bug' in [l.lower() for l in i.get('labels', [])]]
total_count = len(issues)
bug_count = len(bug_issues)
non_bug_count = total_count - bug_count
slack_channel = config.get('slack_channel', '')
email_recipient = config.get('email_recipient', '')
summary_prefix = config.get('summary_prefix', '')

# --- Check report.md ---
report_path = None
for fname in os.listdir(workspace):
    if 'report' in fname.lower() and fname.endswith('.md'):
        report_path = os.path.join(workspace, fname)
        break

if report_path is None:
    check("report_md_exists", False, "No report.md file found")
    report_content = ''
else:
    check("report_md_exists", True, f"Found {report_path}")
    with open(report_path) as f:
        report_content = f.read()

rc = report_content.lower()

check("report_heading", 'bug report summary' in rc, "report.md should contain heading 'Bug Report Summary'")
check("report_bug_issues_section", 'bug issues' in rc, "report.md should contain section '## Bug Issues'")
check("report_stats_section", 'stats' in rc, "report.md should contain section '## Stats'")
check("report_actions_taken_section", 'actions taken' in rc, "report.md should contain section '## Actions Taken'")

# Check all bug entries present in report
bug_entries_found = 0
for issue in bug_issues:
    entry_id = f'bug-{issue["id"]}'
    if entry_id in rc:
        bug_entries_found += 1
check("report_bug_entries", bug_entries_found == bug_count, f"Expected {bug_count} bug entries in report, found {bug_entries_found}")

# Check stats
check("report_total_count", f'total issues: {total_count}' in rc or f'total issues:{total_count}' in rc, f"report.md should contain 'Total issues: {total_count}'")
check("report_bug_count", f'bug issues: {bug_count}' in rc or f'bug issues:{bug_count}' in rc, f"report.md should contain 'Bug issues: {bug_count}'")
check("report_non_bug_count", f'non-bug issues: {non_bug_count}' in rc or f'non-bug issues:{non_bug_count}' in rc, f"report.md should contain 'Non-bug issues: {non_bug_count}'")

# Check actions taken section
check("report_slack_channel", slack_channel.lower() in rc or slack_channel.lstrip('#').lower() in rc, f"report.md should mention slack channel {slack_channel}")
check("report_email_recipient", email_recipient.lower() in rc, f"report.md should mention email {email_recipient}")
check("report_summary_prefix", summary_prefix.lower() in rc, f"report.md should mention summary prefix {summary_prefix}")

# --- Check actions_log.json ---
log_path = None
for fname in os.listdir(workspace):
    if 'actions' in fname.lower() and fname.endswith('.json') and fname != 'issues.json' and fname != 'config.json':
        log_path = os.path.join(workspace, fname)
        break

if log_path is None:
    check("actions_log_exists", False, "No actions_log.json file found")
    actions = []
else:
    check("actions_log_exists", True, f"Found {log_path}")
    try:
        with open(log_path) as f:
            actions = json.load(f)
        check("actions_log_is_array", isinstance(actions, list), f"actions_log.json should be a JSON array, got {type(actions)}")
    except Exception as e:
        check("actions_log_is_array", False, f"Failed to parse actions_log.json: {e}")
        actions = []

# Check slack action exists
slack_actions = [a for a in actions if isinstance(a, dict) and a.get('action_type', '').lower() == 'slack_message']
check("actions_slack_present", len(slack_actions) >= 1, f"Expected at least one slack_message action, found {len(slack_actions)}")

if slack_actions:
    sa = slack_actions[0]
    check("actions_slack_target", slack_channel.lstrip('#') in sa.get('target', '') or slack_channel in sa.get('target', ''), f"Slack action target should reference channel {slack_channel}")
    payload_str = str(sa.get('payload', '')).lower()
    check("actions_slack_payload", summary_prefix.lower() in payload_str or str(bug_count) in payload_str, f"Slack action payload should reference summary_prefix or bug count")
else:
    check("actions_slack_target", False, "No slack action found")
    check("actions_slack_payload", False, "No slack action found")

# Check email action exists
email_actions = [a for a in actions if isinstance(a, dict) and a.get('action_type', '').lower() == 'email']
check("actions_email_present", len(email_actions) >= 1, f"Expected at least one email action, found {len(email_actions)}")

if email_actions:
    ea = email_actions[0]
    check("actions_email_target", email_recipient.lower() in ea.get('target', '').lower(), f"Email action target should be {email_recipient}")
    payload_str = str(ea.get('payload', '')).lower()
    check("actions_email_payload", summary_prefix.lower() in payload_str or str(bug_count) in payload_str, f"Email action payload should reference summary_prefix or bug count")
else:
    check("actions_email_target", False, "No email action found")
    check("actions_email_payload", False, "No email action found")

# Check github_comment actions for each bug issue
github_actions = [a for a in actions if isinstance(a, dict) and a.get('action_type', '').lower() == 'github_comment']
check("actions_github_count", len(github_actions) >= bug_count, f"Expected at least {bug_count} github_comment actions, found {len(github_actions)}")

github_targets = [str(a.get('target', '')).lower() for a in github_actions]
bug_actions_matched = 0
for issue in bug_issues:
    target_key = f'issue-{issue["id"]}'
    if any(target_key in t for t in github_targets):
        bug_actions_matched += 1
check("actions_github_targets", bug_actions_matched == bug_count, f"Expected github_comment targets for all {bug_count} bug issues, matched {bug_actions_matched}")

# Check timestamp field exists in all actions
has_timestamp = all('timestamp' in a for a in actions) if actions else False
check("actions_have_timestamp", has_timestamp and len(actions) > 0, "All action objects should have a 'timestamp' field")

# --- Check stdout output (integration_hub.py exists and is runnable) ---
script_path = os.path.join(workspace, 'integration_hub.py')
check("script_exists", os.path.isfile(script_path), f"integration_hub.py should exist at {script_path}")

# Check script runs and prints expected output
import subprocess
try:
    result = subprocess.run(
        ['python', 'integration_hub.py'],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=30
    )
    stdout = result.stdout.strip().lower()
    expected_line = f'workflow complete. {bug_count} bug issues processed.'
    check("script_stdout", expected_line in stdout, f"stdout should contain '{expected_line}', got: {result.stdout.strip()[:200]}")
    check("script_exit_code", result.returncode == 0, f"Script exited with code {result.returncode}, stderr: {result.stderr[:200]}")
except subprocess.TimeoutExpired:
    check("script_stdout", False, "Script timed out")
    check("script_exit_code", False, "Script timed out")
except Exception as e:
    check("script_stdout", False, f"Error running script: {e}")
    check("script_exit_code", False, f"Error running script: {e}")

total = len(checks)
passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / total if total > 0 else 0.0
result = {"passed": score >= 0.8, "score": score, "checks": checks}
print(json.dumps(result, indent=2))
