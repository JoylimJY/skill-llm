import sys
import os
import json
import re

def load_summary_file(path):
    if not os.path.isdir(path):
        return None
    for filename in os.listdir(path):
        if filename.lower().endswith('.txt') or filename.lower().endswith('.md'):
            with open(os.path.join(path, filename), 'r', encoding='utf-8') as f:
                return f.read()
    return None

def check_summary(summary_text, issues):
    checks = []
    summary_lower = summary_text.lower() if summary_text else ""
    # Check presence of header
    header_present = "weekly bug summary:" in summary_lower
    checks.append({"name": "Header present", "passed": header_present, "detail": "Header line 'Weekly Bug Summary:' must appear (case-insensitive)."})

    # Check each issue summarized
    issues_passed = 0
    for issue in issues:
        title = issue.get('title', '').lower()
        body_first_sentence = re.split(r'[.?!]', issue.get('body', ''))[0].lower().strip()
        # Check if title in summary
        title_found = title and title in summary_lower
        # Check if first sentence of body in summary
        body_found = body_first_sentence and body_first_sentence in summary_lower

        passed = title_found and body_found
        detail = f"Title found: {title_found}; First sentence found: {body_found}"
        checks.append({"name": f"Summary inclusion for issue '{issue.get('title','')}'", "passed": passed, "detail": detail})
        if passed:
            issues_passed += 1

    # Check that each summary line starts with dash or bullet (allow some formatting tolerance)
    lines = [line.strip() for line in summary_text.splitlines() if line.strip()]
    list_lines = [line for line in lines if line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line)]
    list_check = len(list_lines) >= len(issues)
    checks.append({"name": "List format with dashes", "passed": list_check, "detail": f"Found {len(list_lines)} list lines for {len(issues)} issues."})

    return checks

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Arguments", "passed": False, "detail": "Missing workspace directory path argument."}]}))
        return

    workspace = sys.argv[1]

    # Load generated summary (Slack message)
    summary = load_summary_file(workspace)
    if not summary:
        result = {"passed": False, "score": 0.0, "checks": [{"name": "Output summary file", "passed": False, "detail": "No summary file found with .txt or .md extension."}]}
        print(json.dumps(result))
        return

    # Load input issues
    input_issues_path = os.path.join(workspace, "github_issues.json")
    if not os.path.exists(input_issues_path):
        result = {"passed": False, "score": 0.0, "checks": [{"name": "Input issues file", "passed": False, "detail": "Input file github_issues.json not found."}]}
        print(json.dumps(result))
        return

    with open(input_issues_path, 'r', encoding='utf-8') as f:
        issues = json.load(f)

    # Filter issues: label 'bug', open state, created last 7 days
    from datetime import datetime, timedelta
    cutoff_date = datetime(2024, 6, 10, 12, 0, 0) - timedelta(days=7)
    filtered_issues = []
    for issue in issues:
        labels = [lbl.lower() for lbl in issue.get('labels', [])]
        state = issue.get('state', '').lower()
        created_str = issue.get('created_at', '')
        try:
            created_dt = datetime.fromisoformat(created_str.replace('Z',''))
        except Exception:
            continue
        if 'bug' in labels and state == 'open' and created_dt >= cutoff_date:
            filtered_issues.append(issue)

    if not filtered_issues:
        # No issues found to summarize, so passing if summary states no bugs
        no_bugs_phrases = ["no bugs", "no issues", "nothing to report"]
        summary_lc = summary.lower()
        no_bugs_found = any(phrase in summary_lc for phrase in no_bugs_phrases)
        passed = no_bugs_found
        checks = [{"name": "No bugs message included", "passed": passed, "detail": "No recent bug issues; summary should indicate no bugs."}]
        print(json.dumps({"passed": passed, "score": float(passed), "checks": checks}))
        return

    # Run checks on summary
    checks = check_summary(summary, filtered_issues)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / len(checks) if checks else 0.0
    passed = score == 1.0

    print(json.dumps({"passed": passed, "score": score, "checks": checks}))

if __name__ == "__main__":
    main()
