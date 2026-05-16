import json
import sys
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── 1. Find the report file ──────────────────────────────────────────────
    report_path = None
    for candidate in workspace.rglob("family_office_report.json"):
        # Skip the template and backup files
        if "template" in str(candidate) or "backup" in str(candidate) or "old_records" in str(candidate):
            continue
        report_path = candidate
        break

    if report_path is None:
        add_check("report_file_exists", False, "family_office_report.json not found in workspace")
        return finalize(checks, 0.0)

    add_check("report_file_exists", True, f"Found at {report_path}")

    # ── 2. Parse the report ─────────────────────────────────────────────────
    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        add_check("report_valid_json", False, f"Failed to parse JSON: {e}")
        return finalize(checks, 0.0)

    add_check("report_valid_json", True, "Report is valid JSON")

    # ── 3. Family members count = 4 ─────────────────────────────────────────
    try:
        val = int(report.get("total_family_members", -1))
        ok = add_check("total_family_members_correct",
                       val == 4,
                       f"Expected 4, got {val}")
    except Exception as e:
        add_check("total_family_members_correct", False, f"Error reading field: {e}")

    # ── 4. Upcoming birthdays within 30 days = 1 (Eleanor, 20 days away) ───
    try:
        val = int(report.get("upcoming_birthdays_30_days", -1))
        ok = add_check("upcoming_birthdays_30_days_correct",
                       val == 1,
                       f"Expected 1 (Eleanor in 20 days), got {val}")
    except Exception as e:
        add_check("upcoming_birthdays_30_days_correct", False, f"Error: {e}")

    # ── 5. Total contacts = 3 ───────────────────────────────────────────────
    try:
        val = int(report.get("total_contacts", -1))
        ok = add_check("total_contacts_correct",
                       val == 3,
                       f"Expected 3, got {val}")
    except Exception as e:
        add_check("total_contacts_correct", False, f"Error: {e}")

    # ── 6. Contacts needing follow-up in 7 days = 1 (Marcus, 3 days away) ──
    try:
        val = int(report.get("contacts_needing_followup_7_days", -1))
        ok = add_check("contacts_followup_7_days_correct",
                       val == 1,
                       f"Expected 1 (Marcus Blackwell in 3 days), got {val}")
    except Exception as e:
        add_check("contacts_followup_7_days_correct", False, f"Error: {e}")

    # ── 7. Total documents = 3 ──────────────────────────────────────────────
    try:
        val = int(report.get("total_documents", -1))
        ok = add_check("total_documents_correct",
                       val == 3,
                       f"Expected 3, got {val}")
    except Exception as e:
        add_check("total_documents_correct", False, f"Error: {e}")

    # ── 8. Documents expiring within 90 days ────────────────────────────────
    # Trust (60 days) and IMA-Meridian (45 days) = 2 documents
    try:
        val = int(report.get("expiring_documents_90_days", -1))
        ok = add_check("expiring_documents_90_days_correct",
                       val == 2,
                       f"Expected 2 (Trust in 60d, IMA in 45d), got {val}")
    except Exception as e:
        add_check("expiring_documents_90_days_correct", False, f"Error: {e}")

    # ── 9. Documents needing review within 30 days ──────────────────────────
    # Trust (15 days) = 1 document  [IMA is 20d, Estate is 60d]
    # Actually IMA review is in 20 days too - both Trust (15d) and IMA (20d) qualify
    try:
        val = int(report.get("documents_needing_review_30_days", -1))
        ok = add_check("documents_needing_review_30_days_correct",
                       val == 2,
                       f"Expected 2 (Trust in 15d, IMA in 20d), got {val}")
    except Exception as e:
        add_check("documents_needing_review_30_days_correct", False, f"Error: {e}")

    # ── 10. Total tasks = 3 ─────────────────────────────────────────────────
    try:
        val = int(report.get("total_tasks", -1))
        ok = add_check("total_tasks_correct",
                       val == 3,
                       f"Expected 3, got {val}")
    except Exception as e:
        add_check("total_tasks_correct", False, f"Error: {e}")

    # ── 11. Overdue tasks = 1 (tax payment) ─────────────────────────────────
    try:
        val = int(report.get("overdue_tasks", -1))
        ok = add_check("overdue_tasks_correct",
                       val == 1,
                       f"Expected 1 (Q3 tax payment overdue), got {val}")
    except Exception as e:
        add_check("overdue_tasks_correct", False, f"Error: {e}")

    # ── 12. Completed tasks = 1 (tax task was marked complete) ──────────────
    try:
        val = int(report.get("completed_tasks_count", -1))
        ok = add_check("completed_tasks_count_correct",
                       val == 1,
                       f"Expected 1 completed task (Q3 tax), got {val}")
    except Exception as e:
        add_check("completed_tasks_count", False, f"Error: {e}")

    # ── 13. Dashboard alerts > 0 ────────────────────────────────────────────
    try:
        val = int(report.get("dashboard_alerts_count", -1))
        ok = add_check("dashboard_alerts_present",
                       val > 0,
                       f"Expected >0 alerts, got {val}")
    except Exception as e:
        add_check("dashboard_alerts_present", False, f"Error: {e}")

    # ── 14. Verify Family Steward data directory was actually used ───────────
    steward_data = workspace / "family-steward" / "data"
    data_files = list(steward_data.glob("*.json")) if steward_data.exists() else []
    used_steward = len(data_files) > 0
    add_check("family_steward_data_populated",
              used_steward,
              f"Found {len(data_files)} data files in family-steward/data/: {[f.name for f in data_files]}")

    # ── 15. Verify interaction was logged (Marcus Blackwell) ─────────────────
    try:
        contacts_file = steward_data / "contacts.json"
        if contacts_file.exists():
            contacts_data = json.loads(contacts_file.read_text())
            # Find Marcus Blackwell
            contacts_list = contacts_data if isinstance(contacts_data, list) else contacts_data.get("contacts", [])
            marcus = next((c for c in contacts_list if "Blackwell" in str(c.get("name", ""))), None)
            if marcus:
                interactions = marcus.get("interactionHistory", marcus.get("interactions", []))
                has_meeting = any(
                    "meeting" in str(i.get("type", "")).lower() or 
                    "trust" in str(i.get("subject", "")).lower() or
                    "trust" in str(i.get("notes", "")).lower()
                    for i in interactions
                ) if interactions else False
                add_check("marcus_interaction_logged",
                          has_meeting,
                          f"Marcus interactions: {interactions}")
            else:
                add_check("marcus_interaction_logged", False, "Marcus Blackwell not found in contacts data")
        else:
            add_check("marcus_interaction_logged", False, "contacts.json not found in data directory")
    except Exception as e:
        add_check("marcus_interaction_logged", False, f"Error checking interactions: {e}")

    return finalize(checks, None)


def finalize(checks, forced_score):
    if forced_score is not None:
        return {"passed": False, "score": forced_score, "checks": checks}
    
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Must pass the critical structural checks to pass overall
    critical = ["report_file_exists", "report_valid_json", 
                "total_family_members_correct", "total_contacts_correct",
                "total_documents_correct", "family_steward_data_populated"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    
    # Also require at least 70% score
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))