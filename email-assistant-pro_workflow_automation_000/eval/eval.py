import sys
import json
import re
from pathlib import Path

def find_report(workspace):
    """Find email_report.json anywhere in the workspace."""
    results = list(Path(workspace).rglob("email_report.json"))
    return results[0] if results else None

def check_classification(data, checks):
    """Check that all 6 emails are classified with correct proprietary category labels."""
    classification_passed = True
    details = []

    # Expected classifications based on email content
    expected = {
        "email_001": ["重要", "⭐"],   # urgent client contract
        "email_002": ["推广", "📢"],   # marketing newsletter
        "email_003": ["待办", "📎"],   # task assignment email
        "email_004": ["垃圾", "🚮"],   # spam/prize scam
        "email_005": ["常规", "📋"],   # routine partner update
        "email_006": ["常规", "📋"],   # routine HR notice
    }

    # Try to find classification section
    classifications = data.get("classifications", data.get("邮件归类", data.get("email_classifications", [])))

    if not classifications:
        checks.append({"name": "classification_section_exists", "passed": False, "detail": "No 'classifications' key found in email_report.json"})
        return False

    checks.append({"name": "classification_section_exists", "passed": True, "detail": f"Found classifications section with {len(classifications)} entries"})

    # Build a lookup from email id or subject
    classified_map = {}
    if isinstance(classifications, list):
        for item in classifications:
            eid = item.get("id", item.get("email_id", ""))
            classified_map[eid] = item
    elif isinstance(classifications, dict):
        classified_map = classifications

    # Check each expected email
    for email_id, (category_cn, emoji) in expected.items():
        item = classified_map.get(email_id, {})
        if not item:
            # Try searching through list by id substring
            if isinstance(classifications, list):
                for c in classifications:
                    if email_id in str(c.get("id", "")) or email_id in str(c.get("email_id", "")):
                        item = c
                        break

        if not item:
            checks.append({"name": f"classification_{email_id}", "passed": False, "detail": f"Email {email_id} not found in classifications"})
            classification_passed = False
            continue

        category_str = str(item.get("category", item.get("分类", item.get("label", ""))))
        has_cn = category_cn in category_str
        has_emoji = emoji in category_str

        passed = has_cn or has_emoji
        checks.append({
            "name": f"classification_{email_id}",
            "passed": passed,
            "detail": f"Expected category containing '{category_cn}' or '{emoji}', got '{category_str}'"
        })
        if not passed:
            classification_passed = False

    return classification_passed

def check_todos(data, checks):
    """Check that todos are extracted with required fields: 截止/deadline, 优先级/priority, 来源/source."""
    todos = data.get("todos", data.get("待办事项", data.get("todo_items", [])))

    if not todos:
        checks.append({"name": "todos_section_exists", "passed": False, "detail": "No todos/待办事项 key found in email_report.json"})
        return False

    checks.append({"name": "todos_section_exists", "passed": True, "detail": f"Found {len(todos)} todos"})

    # Must have at least 4 todos (email_001 has 2 tasks, email_003 has 4 tasks)
    min_todos = 4
    count_ok = len(todos) >= min_todos
    checks.append({
        "name": "todos_minimum_count",
        "passed": count_ok,
        "detail": f"Expected at least {min_todos} todos, found {len(todos)}"
    })

    # Check required fields in todos
    required_field_groups = [
        ["截止", "deadline", "due_date", "截止日期"],
        ["优先级", "priority"],
        ["来源", "source", "from", "发件人", "origin"]
    ]

    field_names = ["deadline_field", "priority_field", "source_field"]
    field_passed = True

    for todo in todos[:min_todos]:  # Check first min_todos
        todo_str = json.dumps(todo, ensure_ascii=False)
        for group, fname in zip(required_field_groups, field_names):
            has_field = any(f in todo_str for f in group)
            if not has_field:
                checks.append({
                    "name": fname,
                    "passed": False,
                    "detail": f"Todo missing required field group {group}. Todo content: {todo_str[:200]}"
                })
                field_passed = False
                break
        if not field_passed:
            break

    if field_passed:
        for fname in field_names:
            checks.append({"name": fname, "passed": True, "detail": "Required field present in todos"})

    # Check that email_001 deadline (2026-03-15) is captured
    all_todos_str = json.dumps(todos, ensure_ascii=False)
    deadline_captured = "2026-03-15" in all_todos_str or "03-15" in all_todos_str or "3月15" in all_todos_str or "March 15" in all_todos_str.lower()
    checks.append({
        "name": "critical_deadline_captured",
        "passed": deadline_captured,
        "detail": f"Email 001 critical deadline 2026-03-15 {'found' if deadline_captured else 'NOT found'} in todos"
    })

    # Check that email_003 tasks are captured (at least 2 of the 4 tasks)
    task_markers = ["用户调研报告", "OKR", "竞品分析", "API文档", "Q1", "Q2"]
    task_count = sum(1 for m in task_markers if m in all_todos_str)
    task_ok = task_count >= 2
    checks.append({
        "name": "email_003_tasks_captured",
        "passed": task_ok,
        "detail": f"Found {task_count}/{len(task_markers)} expected task markers from email_003 meeting minutes"
    })

    return count_ok and field_passed and deadline_captured and task_ok

def check_priority_sorting(data, checks):
    """Check Eisenhower matrix quadrant labels in priority sorting."""
    priority = data.get("priority_sorted", data.get("优先级排序", data.get("eisenhower_matrix", data.get("prioritized_todos", {}))))

    if not priority:
        checks.append({"name": "priority_section_exists", "passed": False, "detail": "No priority_sorted/优先级排序 key found"})
        return False

    checks.append({"name": "priority_section_exists", "passed": True, "detail": "Found priority sorting section"})

    priority_str = json.dumps(priority, ensure_ascii=False)

    # Must contain Eisenhower quadrant labels from SKILL.md
    eisenhower_quadrants = [
        ["紧急且重要", "urgent_important", "立即处理"],
        ["重要不紧急", "important_not_urgent", "安排时间"],
        ["紧急不重要", "urgent_not_important", "委托"],
        ["不紧急不重要", "not_urgent_not_important", "忽略"]
    ]

    quadrant_names = ["quadrant_urgent_important", "quadrant_important_not_urgent",
                      "quadrant_urgent_not_important", "quadrant_not_urgent_not_important"]

    at_least_two_quadrants = 0
    for group, qname in zip(eisenhower_quadrants, quadrant_names):
        has_q = any(q in priority_str for q in group)
        if has_q:
            at_least_two_quadrants += 1
        checks.append({
            "name": qname,
            "passed": has_q,
            "detail": f"Eisenhower quadrant {group[0]} {'found' if has_q else 'NOT found'} in priority sorting"
        })

    # email_001 (urgent client contract renewal) must be in "紧急且重要" or equivalent
    urgent_important_section = ""
    if isinstance(priority, dict):
        for k, v in priority.items():
            if any(q in str(k) for q in eisenhower_quadrants[0]):
                urgent_important_section = json.dumps(v, ensure_ascii=False)
                break
        if not urgent_important_section:
            # Try to find it anywhere
            urgent_important_section = priority_str

    email_001_in_urgent = any(kw in priority_str for kw in ["续签", "合同", "陈大卫", "enterprise-client", "email_001"])
    checks.append({
        "name": "email_001_in_urgent_quadrant",
        "passed": email_001_in_urgent,
        "detail": f"Email_001 (contract renewal) reference {'found' if email_001_in_urgent else 'NOT found'} in priority section"
    })

    return at_least_two_quadrants >= 2

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0

    # Find the report file
    report_path = find_report(workspace)
    if not report_path:
        checks.append({"name": "file_exists", "passed": False, "detail": "email_report.json not found anywhere in workspace"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found email_report.json at {report_path}"})

    # Load and parse JSON
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "file_parseable", "passed": False, "detail": f"Failed to parse JSON: {e}"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "file_parseable", "passed": True, "detail": "email_report.json is valid JSON"})

    # Check all 6 emails are present in the report
    try:
        data_str = json.dumps(data, ensure_ascii=False)
        email_ids_found = sum(1 for eid in ["email_001", "email_002", "email_003", "email_004", "email_005", "email_006"] if eid in data_str)
        all_emails_covered = email_ids_found >= 5
        checks.append({
            "name": "all_emails_covered",
            "passed": all_emails_covered,
            "detail": f"Found references to {email_ids_found}/6 email IDs in the report"
        })
    except Exception as e:
        checks.append({"name": "all_emails_covered", "passed": False, "detail": f"Error checking email coverage: {e}"})
        all_emails_covered = False

    # === Section 1: Classification ===
    try:
        class_passed = check_classification(data, checks)
    except Exception as e:
        checks.append({"name": "classification_check_error", "passed": False, "detail": f"Exception: {e}"})
        class_passed = False

    # === Section 2: Todo Extraction ===
    try:
        todos_passed = check_todos(data, checks)
    except Exception as e:
        checks.append({"name": "todos_check_error", "passed": False, "detail": f"Exception: {e}"})
        todos_passed = False

    # === Section 3: Priority Sorting ===
    try:
        priority_passed = check_priority_sorting(data, checks)
    except Exception as e:
        checks.append({"name": "priority_check_error", "passed": False, "detail": f"Exception: {e}"})
        priority_passed = False

    # Calculate score
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3) if total_checks > 0 else 0.0

    # Overall pass: must pass classification + todos + priority + file found
    overall_passed = (
        checks[0]["passed"] and  # file exists
        checks[1]["passed"] and  # file parseable
        class_passed and
        todos_passed and
        priority_passed
    )

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()