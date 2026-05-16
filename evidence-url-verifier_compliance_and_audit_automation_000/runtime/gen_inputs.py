import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Create distractor directory structure ---
dirs = [
    "compliance/soc2/controls",
    "compliance/soc2/policies",
    "compliance/soc2/evidence",
    "compliance/internal/audits/2023",
    "compliance/internal/audits/2024",
    "projects/alpha/docs",
    "projects/alpha/src",
    "projects/beta/reports",
    "infrastructure/configs",
    "infrastructure/logs",
    "hr/policies",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "compliance/soc2/policies/access_control_policy.md": "# Access Control Policy\nAll access must be logged and reviewed quarterly.",
    "compliance/soc2/policies/incident_response.md": "# Incident Response\nAll incidents must be reported within 24 hours.",
    "compliance/internal/audits/2023/audit_summary.txt": "Audit completed 2023-11-15. No critical findings.",
    "compliance/internal/audits/2024/draft_notes.txt": "Still in progress. Do not distribute.",
    "projects/alpha/docs/architecture.md": "# Architecture\nMicroservices running on Kubernetes.",
    "projects/alpha/src/main.py": "print('hello world')",
    "projects/beta/reports/q3_report.csv": "date,value\n2024-07-01,1200\n2024-08-01,1350",
    "infrastructure/configs/nginx.conf": "server { listen 80; }",
    "infrastructure/logs/access.log": "127.0.0.1 - - [01/Jan/2024] GET /index.html 200",
    "hr/policies/remote_work.md": "# Remote Work Policy\nEmployees may work remotely up to 3 days per week.",
    "compliance/soc2/controls/cc6_logical_access.txt": "Control CC6.1: Logical access security measures restrict access.",
    "compliance/soc2/controls/cc7_system_operations.txt": "Control CC7.2: System operational failures are detected.",
}
for path, content in distractor_files.items():
    full = os.path.join(WORKSPACE, path)
    with open(full, "w") as f:
        f.write(content)

# --- Local artifact files for evidence validation ---
# These are referenced in the manifest as local paths

# VALID: exists and non-empty
valid_artifact_path = os.path.join(WORKSPACE, "compliance/soc2/evidence/pentest_report_2024.pdf")
with open(valid_artifact_path, "w") as f:
    f.write("PENTEST REPORT 2024\nFinding: No critical vulnerabilities found.\nDate: 2024-03-15\nAuthor: SecAudit Inc.")

# EMPTY: exists but zero bytes
empty_artifact_path = os.path.join(WORKSPACE, "compliance/soc2/evidence/vuln_scan_output.txt")
with open(empty_artifact_path, "w") as f:
    f.write("")  # empty file

# MISSING: does not exist (referenced in manifest but file won't be created)
missing_artifact_path = os.path.join(WORKSPACE, "compliance/soc2/evidence/employee_training_certs.zip")
# intentionally NOT created

# VALID local: another existing non-empty file
valid_artifact_2_path = os.path.join(WORKSPACE, "compliance/soc2/evidence/access_log_export.csv")
with open(valid_artifact_2_path, "w") as f:
    f.write("timestamp,user,action\n2024-01-10 09:00,alice,LOGIN\n2024-01-10 09:05,bob,READ_FILE")

# --- The evidence manifest ---
# Port 18923 will be used by the mock server
BASE_URL = "http://localhost:18923"

manifest = {
    "submission_id": "SOC2-2024-ACME-007",
    "submitted_by": "compliance-team@acme.example",
    "evidence_items": [
        {
            "id": "EV-001",
            "description": "Annual penetration test report hosted on internal portal",
            "claimed_type": "text",
            "url": f"{BASE_URL}/real-report",
            "local_path": None
        },
        {
            "id": "EV-002",
            "description": "Vulnerability scanning results summary",
            "claimed_type": "text",
            "url": f"{BASE_URL}/placeholder-page",
            "local_path": None
        },
        {
            "id": "EV-003",
            "description": "Employee security training completion certificates",
            "claimed_type": "text",
            "url": f"{BASE_URL}/missing-resource",
            "local_path": None
        },
        {
            "id": "EV-004",
            "description": "Firewall configuration export (PDF claimed as text)",
            "claimed_type": "text",
            "url": f"{BASE_URL}/pdf-as-text",
            "local_path": None
        },
        {
            "id": "EV-005",
            "description": "Access review log exported from IAM system",
            "claimed_type": "text",
            "url": f"{BASE_URL}/valid-json-report",
            "local_path": None
        },
        {
            "id": "EV-006",
            "description": "Lorem-filled draft doc mistakenly submitted",
            "claimed_type": "text",
            "url": f"{BASE_URL}/lorem-ipsum-page",
            "local_path": None
        },
        {
            "id": "EV-007",
            "description": "Local copy of penetration test report",
            "claimed_type": "text",
            "url": None,
            "local_path": valid_artifact_path
        },
        {
            "id": "EV-008",
            "description": "Local vulnerability scan output file",
            "claimed_type": "text",
            "url": None,
            "local_path": empty_artifact_path
        },
        {
            "id": "EV-009",
            "description": "Local employee training certificate archive",
            "claimed_type": "text",
            "url": None,
            "local_path": missing_artifact_path
        },
        {
            "id": "EV-010",
            "description": "Local access log export",
            "claimed_type": "text",
            "url": None,
            "local_path": valid_artifact_2_path
        },
    ]
}

manifest_path = os.path.join(WORKSPACE, "evidence_manifest.json")
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Workspace setup complete. Manifest written to {manifest_path}")
print(f"Local artifacts created:")
print(f"  VALID (non-empty): {valid_artifact_path}")
print(f"  EMPTY: {empty_artifact_path}")
print(f"  MISSING (not created): {missing_artifact_path}")
print(f"  VALID (non-empty): {valid_artifact_2_path}")