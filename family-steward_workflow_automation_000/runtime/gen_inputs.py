import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# Create distractor directory structure
distractor_dirs = [
    "old_records/2022",
    "old_records/2023/Q1",
    "old_records/2023/Q3",
    "archive/legal",
    "archive/financial",
    "temp/uploads",
    "temp/exports",
    "admin/config",
    "admin/backup",
    "reports/annual",
    "reports/quarterly",
]

for d in distractor_dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - various formats, none of which should be the answer
distractor_files = {
    "old_records/2022/contacts_export.csv": "Name,Email,Phone\nJohn Smith,john@example.com,555-0100\nJane Doe,jane@example.com,555-0101",
    "old_records/2022/members.txt": "Family Members List (OUTDATED)\n- Robert Chen (Patriarch)\n- Linda Chen (Matriarch)\n- David Chen (Son)",
    "old_records/2023/Q1/tasks_old.json": json.dumps({"tasks": [{"id": "t001", "title": "Old meeting", "status": "done"}]}),
    "old_records/2023/Q3/notes.md": "# Q3 Notes\n- Review trust documents\n- Schedule advisor meetings\n- Update wills",
    "archive/legal/document_index.txt": "INDEX (DEPRECATED)\n1. Family Trust - expires 2025-01-01\n2. NDA - expires 2024-06-01",
    "archive/financial/portfolio_2023.csv": "Asset,Value,Manager\nTech Fund,$2M,BlackRock\nBonds,$1.5M,Vanguard",
    "temp/uploads/scan_001.txt": "SCANNED DOCUMENT - NOT INDEXED\nDate: 2023-09-15\nContent: Property deed for Malibu estate",
    "temp/exports/export_broken.json": '{"error": "export failed", "timestamp": "2023-11-01"}',
    "admin/config/old_settings.json": json.dumps({"version": "0.9.0", "database": "sqlite", "deprecated": True}),
    "admin/backup/backup_manifest.txt": "Backup created: 2023-12-31\nFiles: 342\nSize: 45MB",
    "reports/annual/2023_summary.txt": "ANNUAL REPORT 2023\nFamily Members: 7\nDocuments: 23\nTasks Completed: 156",
    "reports/quarterly/Q4_2023.txt": "Q4 2023 Review\nKey Actions Pending:\n- Estate review\n- Tax filings",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content)

# THE CORE INPUT: A data specification file the agent MUST read and import
# This has specific dates calculated relative to "today" to make expiry/birthday checks deterministic
today = datetime.now()

# Birthday: in 20 days (within 30-day window)
birthday_soon = today + timedelta(days=20)
# Birthday: in 45 days (outside 30-day window)
birthday_far = today + timedelta(days=45)
# Document expiry: in 60 days (within 90-day window)
doc_expiry_soon = today + timedelta(days=60)
# Document expiry: in 120 days (outside 90-day window)
doc_expiry_far = today + timedelta(days=120)
# Task due: yesterday (overdue)
task_overdue = today - timedelta(days=1)
# Task due: in 5 days
task_upcoming = today + timedelta(days=5)
# Contact follow-up: in 3 days (within 7-day window)
followup_soon = today + timedelta(days=3)

family_data_spec = {
    "import_instructions": "Use the Family Steward system to import all data below. Each section must be added via the system's management tools.",
    "family_members": [
        {
            "name": "Wellington Hartford III",
            "relationship": "Patriarch",
            "generation": 1,
            "dateOfBirth": birthday_far.strftime("%Y-%m-%d"),
            "tags": ["patriarch", "founder"],
            "notes": "Founded Hartford Capital in 1985"
        },
        {
            "name": "Eleanor Hartford",
            "relationship": "Matriarch",
            "generation": 1,
            "dateOfBirth": birthday_soon.strftime("%Y-%m-%d"),
            "tags": ["matriarch", "philanthropist"],
            "notes": "Chairs the Hartford Foundation"
        },
        {
            "name": "Sebastian Hartford",
            "relationship": "Son",
            "generation": 2,
            "dateOfBirth": "1985-03-22",
            "tags": ["heir", "executive"],
            "notes": "CEO of Hartford Capital"
        },
        {
            "name": "Victoria Hartford-Chen",
            "relationship": "Daughter",
            "generation": 2,
            "dateOfBirth": "1988-07-14",
            "tags": ["daughter", "attorney"],
            "notes": "Family legal counsel"
        }
    ],
    "contacts": [
        {
            "name": "Marcus Blackwell",
            "category": "legal",
            "role": "Estate Attorney",
            "organization": "Blackwell & Partners LLP",
            "email": "m.blackwell@blackwellpartners.com",
            "phone": "+1-212-555-0190",
            "nextFollowUp": followup_soon.strftime("%Y-%m-%d"),
            "notes": "Handles all trust and estate matters"
        },
        {
            "name": "Priya Menon",
            "category": "financial",
            "role": "Chief Investment Officer",
            "organization": "Meridian Wealth Management",
            "email": "p.menon@meridianwm.com",
            "phone": "+1-415-555-0234",
            "nextFollowUp": (today + timedelta(days=30)).strftime("%Y-%m-%d"),
            "notes": "Manages $450M portfolio"
        },
        {
            "name": "Dr. Thomas Vance",
            "category": "medical",
            "role": "Family Physician",
            "organization": "Vance Private Medical Group",
            "email": "t.vance@vancemedical.com",
            "phone": "+1-310-555-0088",
            "nextFollowUp": (today + timedelta(days=90)).strftime("%Y-%m-%d"),
            "notes": "Concierge medical service"
        }
    ],
    "initial_interaction": {
        "contact_name": "Marcus Blackwell",
        "interaction": {
            "date": today.strftime("%Y-%m-%d"),
            "type": "meeting",
            "subject": "Annual trust review",
            "notes": "Reviewed Hartford Family Trust terms. Discussed updating successor trustee provisions. Next steps: draft amendment by end of month."
        }
    },
    "documents": [
        {
            "title": "Hartford Family Revocable Trust",
            "category": "trust",
            "description": "Primary family trust instrument covering all major assets",
            "expiryDate": doc_expiry_soon.strftime("%Y-%m-%d"),
            "nextReviewDate": (today + timedelta(days=15)).strftime("%Y-%m-%d"),
            "relatedContacts": ["Marcus Blackwell"],
            "tags": ["trust", "primary", "estate"]
        },
        {
            "title": "Malibu Estate Purchase Agreement",
            "category": "property",
            "description": "Property deed and purchase agreement for 24 Ocean View Drive",
            "expiryDate": doc_expiry_far.strftime("%Y-%m-%d"),
            "nextReviewDate": (today + timedelta(days=60)).strftime("%Y-%m-%d"),
            "relatedContacts": ["Marcus Blackwell"],
            "tags": ["property", "real-estate"]
        },
        {
            "title": "Investment Management Agreement - Meridian",
            "category": "financial",
            "description": "IMA governing the $450M managed portfolio",
            "expiryDate": (today + timedelta(days=45)).strftime("%Y-%m-%d"),
            "nextReviewDate": (today + timedelta(days=20)).strftime("%Y-%m-%d"),
            "relatedContacts": ["Priya Menon"],
            "tags": ["investment", "ima", "portfolio"]
        }
    ],
    "tasks": [
        {
            "title": "File Q3 estimated tax payments",
            "description": "Submit quarterly estimated income tax payments for Hartford Capital LLC",
            "priority": "critical",
            "dueDate": task_overdue.strftime("%Y-%m-%d"),
            "status": "pending",
            "assignedTo": "Sebastian Hartford",
            "tags": ["tax", "quarterly", "urgent"]
        },
        {
            "title": "Schedule family governance board meeting",
            "description": "Arrange the semi-annual family board meeting with all generation-1 and generation-2 members",
            "priority": "high",
            "dueDate": task_upcoming.strftime("%Y-%m-%d"),
            "status": "pending",
            "assignedTo": "Victoria Hartford-Chen",
            "tags": ["governance", "meeting", "family"]
        },
        {
            "title": "Review Meridian quarterly performance report",
            "description": "Analyze Q3 investment performance metrics and benchmark comparisons",
            "priority": "medium",
            "dueDate": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "status": "pending",
            "assignedTo": "Wellington Hartford III",
            "tags": ["investment", "review", "financial"]
        }
    ],
    "task_to_complete": "File Q3 estimated tax payments",
    "report_output_file": "family_office_report.json",
    "report_requirements": {
        "description": "After importing all data, query the system dashboard and produce a JSON report",
        "required_fields": [
            "total_family_members",
            "upcoming_birthdays_30_days",
            "total_contacts",
            "contacts_needing_followup_7_days",
            "total_documents",
            "expiring_documents_90_days",
            "documents_needing_review_30_days",
            "total_tasks",
            "overdue_tasks",
            "completed_tasks_count",
            "dashboard_alerts_count"
        ]
    }
}

(workspace / "family_data_spec.json").write_text(json.dumps(family_data_spec, indent=2))

# Additional distractor: a fake report template
fake_report = {
    "report_type": "TEMPLATE - DO NOT USE",
    "total_family_members": 0,
    "total_contacts": 0,
    "total_documents": 0,
    "total_tasks": 0,
    "note": "This is an empty template. Real data must come from the Family Steward system."
}
(workspace / "reports/annual/report_template.json").write_text(json.dumps(fake_report, indent=2))

# A misleading script that does the wrong thing
wrong_script = """#!/usr/bin/env python3
# DO NOT USE THIS SCRIPT - it is deprecated and generates incorrect output
import json
data = {"total_family_members": 99, "error": "deprecated script"}
print(json.dumps(data))
"""
(workspace / "admin/backup/old_report_gen.py").write_text(wrong_script)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")
print(f"Key input file: {workspace / 'family_data_spec.json'}")
print(f"\nKey dates used:")
print(f"  Birthday soon (Eleanor): {birthday_soon.strftime('%Y-%m-%d')} (in 20 days)")
print(f"  Birthday far (Wellington): {birthday_far.strftime('%Y-%m-%d')} (in 45 days)")
print(f"  Doc expiry soon (Trust): {doc_expiry_soon.strftime('%Y-%m-%d')} (in 60 days)")
print(f"  Doc expiry far (Estate): {doc_expiry_far.strftime('%Y-%m-%d')} (in 120 days)")
print(f"  Task overdue: {task_overdue.strftime('%Y-%m-%d')} (1 day ago)")
print(f"  Followup soon (Marcus): {followup_soon.strftime('%Y-%m-%d')} (in 3 days)")