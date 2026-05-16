import sys
import json
import os
import re
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
score_total = 0.0
max_score = 10.0

def find_review_file(workspace):
    """Find the code review report JSON file."""
    candidates = list(Path(workspace).rglob("code_review_report.json"))
    if candidates:
        return candidates[0]
    return None

def load_report(path):
    with open(path, "r") as f:
        return json.load(f)

review_path = find_review_file(workspace)

# CHECK 0: File exists
if review_path is None:
    checks.append({
        "name": "review_file_exists",
        "passed": False,
        "detail": "Could not find 'code_review_report.json' anywhere in the workspace."
    })
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)
else:
    checks.append({
        "name": "review_file_exists",
        "passed": True,
        "detail": f"Found review file at: {review_path}"
    })
    score_total += 0.5

try:
    report = load_report(review_path)
except Exception as e:
    checks.append({
        "name": "review_file_parseable",
        "passed": False,
        "detail": f"Failed to parse JSON: {e}"
    })
    result = {"passed": False, "score": score_total / max_score, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

checks.append({
    "name": "review_file_parseable",
    "passed": True,
    "detail": "JSON parsed successfully."
})
score_total += 0.5

# Normalize report to a string for flexible searching
report_str = json.dumps(report).lower()

# ============================================================
# ACTUAL BUGS — Agent MUST identify these
# ============================================================

# BUG 1: os.ReadFile in Update (dashboard.go, 'c' key handler)
bug1_keywords = [
    (r"os\.readfile", "os.ReadFile"),
    (r"blocks?.*ui|blocking.*update|blocks.*ui\s*thread", "blocking"),
    (r"dashboard\.go|dashboard", "dashboard.go"),
]
bug1_found = all(re.search(pat, report_str) for pat, _ in bug1_keywords)
checks.append({
    "name": "bug_os_readfile_in_update",
    "passed": bug1_found,
    "detail": (
        "PASS: os.ReadFile() in Update correctly identified as a blocking I/O bug in dashboard.go"
        if bug1_found else
        "FAIL: Agent did not flag os.ReadFile() called directly inside Update() in dashboard.go"
    )
})
if bug1_found:
    score_total += 2.0

# BUG 2: time.Sleep in Update (dashboard.go, 's' key handler)
bug2_keywords = [
    (r"time\.sleep", "time.Sleep"),
    (r"freeze|blocks?|blocking|freezes", "freezes UI"),
]
bug2_found = all(re.search(pat, report_str) for pat, _ in bug2_keywords)
checks.append({
    "name": "bug_time_sleep_in_update",
    "passed": bug2_found,
    "detail": (
        "PASS: time.Sleep() in Update correctly identified as blocking"
        if bug2_found else
        "FAIL: Agent did not flag time.Sleep() called directly inside Update() in dashboard.go"
    )
})
if bug2_found:
    score_total += 1.5

# BUG 3: Lipgloss style created inside View/View helper (dashboard.go errStyle + orderform.go detailStyle)
bug3_keywords = [
    (r"lipgloss\.newstyle", "lipgloss.NewStyle"),
    (r"view\b.*style|style.*\bview\b|in.*view|inside.*view|view.*creat|creat.*view", "created in view"),
]
bug3_found = all(re.search(pat, report_str) for pat, _ in bug3_keywords)
checks.append({
    "name": "bug_lipgloss_style_in_view",
    "passed": bug3_found,
    "detail": (
        "PASS: Lipgloss style creation inside View() correctly identified as a bug"
        if bug3_found else
        "FAIL: Agent did not flag lipgloss.NewStyle() being called inside View() functions"
    )
})
if bug3_found:
    score_total += 1.5

# BUG 4: huh.Form.Run() inside Update (orderform.go)
bug4_keywords = [
    (r"form\.run\(\)|huh.*run\(\)|\.run\(\)", "form.Run()"),
    (r"blocks?|blocking|orderform", "blocking/orderform"),
]
bug4_found = all(re.search(pat, report_str) for pat, _ in bug4_keywords)
checks.append({
    "name": "bug_huh_form_run_in_update",
    "passed": bug4_found,
    "detail": (
        "PASS: huh.Form.Run() inside Update correctly identified as blocking"
        if bug4_found else
        "FAIL: Agent did not flag huh.Form.Run() called inside Update() in orderform.go"
    )
})
if bug4_found:
    score_total += 1.5

# BUG 5: viewport.SetContent called inside View (watchlist.go)
bug5_keywords = [
    (r"viewport\.setcontent|setcontent", "viewport.SetContent"),
    (r"view\(\)|inside.*view|view.*side.effect|side.effect.*view|pure|impure|not.*pure", "side effect in View"),
    (r"watchlist", "watchlist.go"),
]
bug5_found = all(re.search(pat, report_str) for pat, _ in bug5_keywords)
checks.append({
    "name": "bug_viewport_setcontent_in_view",
    "passed": bug5_found,
    "detail": (
        "PASS: viewport.SetContent() inside View() correctly flagged as side effect"
        if bug5_found else
        "FAIL: Agent did not flag viewport.SetContent() called inside View() in watchlist.go"
    )
})
if bug5_found:
    score_total += 1.5

# ============================================================
# FALSE POSITIVES — Agent must NOT flag these as bugs
# ============================================================

# FALSE POSITIVE CHECK 1: return m, m.refreshFeed() must NOT be flagged as blocking
# We check that the agent explicitly acknowledges this is correct, OR
# that the report does not list refreshFeed as a bug
report_flags_refreshfeed_as_bug = bool(re.search(
    r"(bug|issue|problem|error|wrong|incorrect|blocking)[^\"]{0,80}refreshfeed|"
    r"refreshfeed[^\"]{0,80}(bug|issue|problem|error|wrong|incorrect|blocking)",
    report_str
))
fp1_passed = not report_flags_refreshfeed_as_bug
checks.append({
    "name": "no_false_positive_refreshFeed_cmd",
    "passed": fp1_passed,
    "detail": (
        "PASS: Agent correctly did NOT flag 'return m, m.refreshFeed()' as blocking (it's a tea.Cmd helper)"
        if fp1_passed else
        "FAIL: Agent incorrectly flagged m.refreshFeed() as a blocking call — this is a FALSE POSITIVE. "
        "refreshFeed() returns a tea.Cmd, which is executed asynchronously by the BubbleTea runtime."
    )
})
if fp1_passed:
    score_total += 0.5

# FALSE POSITIVE CHECK 2: m.table, cmd = m.table.Update(msg) must NOT be flagged as problematic
report_flags_table_update = bool(re.search(
    r"(bug|issue|problem|error|wrong|incorrect)[^\"]{0,80}(table\.update|m\.table.*update|update.*m\.table)|"
    r"(table\.update|m\.table.*update)[^\"]{0,80}(bug|issue|problem|error|wrong|incorrect)",
    report_str
))
fp2_passed = not report_flags_table_update
checks.append({
    "name": "no_false_positive_nested_component_update",
    "passed": fp2_passed,
    "detail": (
        "PASS: Agent correctly did NOT flag nested component update (m.table, cmd = m.table.Update(msg)) as a bug"
        if fp2_passed else
        "FAIL: Agent incorrectly flagged nested component update as a bug — this is the standard BubbleTea composition pattern."
    )
})
if fp2_passed:
    score_total += 0.5

# FALSE POSITIVE CHECK 3: Value receiver on Update must NOT be flagged
report_flags_value_receiver = bool(re.search(
    r"(bug|issue|problem|error|wrong|incorrect)[^\"]{0,80}(value.receiver|func.*m model.*update)|"
    r"(value.receiver)[^\"]{0,80}(bug|issue|problem|error|wrong|incorrect)",
    report_str
))
fp3_passed = not report_flags_value_receiver
checks.append({
    "name": "no_false_positive_value_receiver",
    "passed": fp3_passed,
    "detail": (
        "PASS: Agent correctly did NOT flag value receiver on Update() as a bug"
        if fp3_passed else
        "FAIL: Agent incorrectly flagged value receiver on Update() — this is the standard BubbleTea pattern."
    )
})
if fp3_passed:
    score_total += 0.5

# ============================================================
# STRUCTURE CHECK: Report must cover all 3 files
# ============================================================
covers_all_files = (
    "dashboard" in report_str and
    "orderform" in report_str and
    "watchlist" in report_str
)
checks.append({
    "name": "report_covers_all_three_files",
    "passed": covers_all_files,
    "detail": (
        "PASS: Report references all three reviewed files (dashboard, orderform, watchlist)"
        if covers_all_files else
        "FAIL: Report does not reference all three files (dashboard.go, orderform.go, watchlist.go)"
    )
})
if covers_all_files:
    score_total += 0.5

# ============================================================
# Final scoring
# ============================================================
final_score = min(score_total / max_score, 1.0)
total_passed = sum(1 for c in checks if c["passed"])
overall_passed = (
    total_passed >= 8 and
    bug1_found and bug2_found and bug3_found and bug4_found and bug5_found and
    fp1_passed and fp2_passed
)

result = {
    "passed": overall_passed,
    "score": round(final_score, 3),
    "checks": checks
}
print(json.dumps(result, indent=2))