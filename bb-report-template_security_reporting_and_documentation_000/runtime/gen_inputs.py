import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE", "/workspace"))

# --- Create distractor directory structure ---
dirs = [
    workspace / "research" / "target_recon" / "subdomains",
    workspace / "research" / "target_recon" / "screenshots",
    workspace / "research" / "payloads" / "xss",
    workspace / "research" / "payloads" / "sqli",
    workspace / "notes" / "drafts",
    workspace / "notes" / "archive",
    workspace / "submissions" / "pending",
    workspace / "submissions" / "accepted",
    workspace / "tools" / "burp_exports",
    workspace / "tools" / "nuclei_results",
    workspace / "reports",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
(workspace / "research" / "target_recon" / "subdomains" / "subs.txt").write_text(
    "\n".join([f"sub{i}.payments.fintech-corp.io" for i in range(1, 25)])
)

(workspace / "research" / "target_recon" / "screenshots" / "readme.txt").write_text(
    "Screenshots taken with gowitness on 2024-03-10. Not processed yet."
)

(workspace / "research" / "payloads" / "xss" / "reflected_payloads.txt").write_text(
    "<script>alert(1)</script>\n\"><img src=x onerror=alert(1)>\n'><svg/onload=alert(1)>"
)

(workspace / "research" / "payloads" / "sqli" / "error_based.txt").write_text(
    "' OR '1'='1\n' UNION SELECT NULL--\n1; DROP TABLE users--"
)

(workspace / "notes" / "drafts" / "vuln_notes.txt").write_text(
    """Vulnerability Notes - 2024-03-15
===============================
Target: payments.fintech-corp.io
Program: Bugcrowd

Finding 1: IDOR on /api/v2/transactions/{id}
- Severity: HIGH
- Any authenticated user can access other users' transaction records
- No ownership check on the 'id' parameter
- Tested with accounts: user_a (id=1042) and user_b (id=1043)
- user_a can fetch /api/v2/transactions/1043 successfully

Finding 2: SQL Injection on /api/v1/search
- Severity: CRITICAL  
- Unsanitized 'q' parameter passed directly to SQL query
- Confirmed blind SQLi, can enumerate DB
- Target: api.fintech-corp.io (HackerOne program)
"""
)

(workspace / "notes" / "archive" / "old_report_attempt.txt").write_text(
    """Title: IDOR bug
Severity: high
Platform: bugcrowd
Status: DRAFT - never submitted, needs proper formatting
"""
)

(workspace / "notes" / "drafts" / "cvss_scratch.txt").write_text(
    "IDOR CVSS rough: AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N => 6.5\n"
    "SQLi CVSS rough: AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H => 10.0\n"
)

(workspace / "submissions" / "pending" / "tracker.json").write_text(json.dumps({
    "pending": [
        {"id": "BUG-001", "title": "IDOR on transactions API", "platform": "bugcrowd", "status": "draft"},
        {"id": "BUG-002", "title": "SQL Injection on search endpoint", "platform": "hackerone", "status": "draft"},
    ]
}, indent=2))

(workspace / "tools" / "burp_exports" / "idor_request.txt").write_text(
    "GET /api/v2/transactions/1043 HTTP/1.1\nHost: payments.fintech-corp.io\nAuthorization: Bearer eyJhbGciOiJIUzI1NiJ9.user_a_token\n"
)

(workspace / "tools" / "burp_exports" / "sqli_request.txt").write_text(
    "GET /api/v1/search?q=test%27+OR+%271%27%3D%271 HTTP/1.1\nHost: api.fintech-corp.io\n"
)

(workspace / "tools" / "nuclei_results" / "scan_output.txt").write_text(
    "[2024-03-15] [sqli] [critical] api.fintech-corp.io/api/v1/search\n"
    "[2024-03-15] [idor] [high] payments.fintech-corp.io/api/v2/transactions\n"
)

(workspace / "reports" / ".gitkeep").write_text("")

print("Workspace initialized successfully.")
print(f"Structure created under: {workspace}")