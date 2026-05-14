import os
import random

random.seed(42)

# Create deeply nested directory structure with distractor files
dirs = [
    "workspace/ops/missions",
    "workspace/ops/logs",
    "workspace/ops/agents/analyze",
    "workspace/ops/agents/execute",
    "workspace/ops/agents/review",
    "workspace/infra/deployments",
    "workspace/infra/configs",
    "workspace/security/audits",
    "workspace/security/reports",
    "workspace/git/branches",
    "workspace/git/commits",
    "workspace/notifications",
    "workspace/templates/draft",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files - realistic but irrelevant
files = {
    "workspace/ops/logs/agent_run_2024_01_15.log": """[2024-01-15 09:01:22] Agent 'analyze' started on issue #88
[2024-01-15 09:05:44] Agent 'execute' triggered
[2024-01-15 09:12:03] Agent 'review' pending
[2024-01-15 09:30:00] Mission completed
""",
    "workspace/ops/logs/errors_2024_01_14.log": """ERROR: Timeout on agent 'execute' after 300s
ERROR: State transition failed: RUNNING -> COMPLETE (missing PARTIAL)
WARNING: Footer checksum mismatch
""",
    "workspace/ops/agents/analyze/config.json": """{
  "agent": "analyze",
  "timeout": 300,
  "retries": 3,
  "model": "gpt-4",
  "scope": ["*.py", "*.js"]
}
""",
    "workspace/ops/agents/execute/config.json": """{
  "agent": "execute",
  "timeout": 600,
  "retries": 1,
  "model": "gpt-4",
  "scope": ["src/", "tests/"]
}
""",
    "workspace/ops/agents/review/config.json": """{
  "agent": "review",
  "timeout": 180,
  "retries": 2,
  "model": "gpt-4",
  "scope": ["*.md", "CHANGELOG"]
}
""",
    "workspace/infra/deployments/hotfix_99.yaml": """deployment:
  issue: 99
  branch: hotfix/vuln-patch-issue-99
  environment: production
  strategy: rolling
  agents:
    - name: analyze
      task: scan codebase for CVE-2024-9911
    - name: execute
      task: apply patch and run regression suite
    - name: review
      task: validate diff and approve PR
""",
    "workspace/infra/configs/mission_template_OLD.txt": """# DEPRECATED TEMPLATE - DO NOT USE
MISSION: {name}
STATUS: {status}
AGENTS: {agents}
NOTE: This format is no longer valid as of v2.1
""",
    "workspace/security/audits/cve_2024_9911.md": """# CVE-2024-9911
**Severity:** HIGH
**Component:** auth-service/token_validator.py
**Description:** JWT token validation bypass via algorithm confusion
**Affected files:**
- src/auth/token_validator.py
- src/auth/middleware.py
- tests/test_auth.py
**Fix:** Enforce explicit algorithm allowlist
""",
    "workspace/security/reports/scan_results.json": """{
  "scan_date": "2024-01-16",
  "issue": 99,
  "vulnerabilities": [
    {"id": "CVE-2024-9911", "severity": "HIGH", "file": "src/auth/token_validator.py"},
    {"id": "CVE-2024-8812", "severity": "LOW", "file": "src/utils/helpers.py"}
  ],
  "total": 2,
  "critical": 0,
  "high": 1,
  "low": 1
}
""",
    "workspace/git/branches/active.txt": """hotfix/vuln-patch-issue-99
feature/agent-telemetry
main
""",
    "workspace/git/commits/recent.log": """abc1234 fix: apply CVE-2024-9911 patch to token_validator.py
def5678 test: add regression tests for auth bypass
ghi9012 chore: update CHANGELOG for hotfix release
""",
    "workspace/notifications/pushcut_log.txt": """2024-01-16T10:00:00Z SENT hotfix-99-start -> pushcut/telegram
2024-01-16T11:30:00Z SENT hotfix-99-awaiting -> pushcut/telegram
2024-01-16T12:00:00Z SENT hotfix-99-complete -> pushcut/telegram
""",
    "workspace/templates/draft/status_attempt.txt": """--- BROKEN DRAFT - IGNORE ---
Mission: CVE Hotfix #99
State: PARTIAL
Agents: 3/3
analyze: done
execute: done  
review: pending
Next: review agent to validate patch
--- END ---
NOTE: This format was rejected by the ops team, wrong structure
""",
    "workspace/ops/missions/mission_index.json": """{
  "missions": [
    {"id": "M-001", "issue": 88, "status": "COMPLETE", "date": "2024-01-15"},
    {"id": "M-002", "issue": 99, "status": "IN_PROGRESS", "date": "2024-01-16"}
  ]
}
""",
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# The agent's task: produce three operational documents
# We write a brief mission brief that explains WHAT happened (business context only, no format hints)
brief_content = """MISSION BRIEF - Issue #99
==========================
Date: 2024-01-16
Mission: CVE-2024-9911 Hotfix Deployment

Context:
A critical JWT authentication bypass vulnerability (CVE-2024-9911) was discovered
in the production auth-service. A 3-agent parallel workflow was dispatched to 
analyze, patch, and review the affected components.

Agents Involved:
- analyze: Responsible for scanning and identifying the vulnerability scope
- execute: Responsible for applying the patch and running regression tests
- review: Responsible for validating the diff and approving the PR

Timeline:
- Mission started: 2024-01-16 10:00 UTC
- Elapsed at PARTIAL state: 1h 30m
- Elapsed at AWAITING APPROVAL state: 1h 45m
- Mission completed: 2024-01-16 12:00 UTC (elapsed: 2h 00m)

Agent Outcomes at PARTIAL state:
- analyze: completed - CVE-2024-9911 confirmed in token_validator.py and middleware.py
- execute: completed - patch applied, all 47 regression tests passed
- review: in progress - diff review underway

Agent Outcomes at AWAITING APPROVAL state:
- analyze: completed - CVE-2024-9911 confirmed in token_validator.py and middleware.py
- execute: completed - patch applied, all 47 regression tests passed
- review: completed - diff approved, PR ready for merge

Final Agent Outcomes (COMPLETE):
- analyze: completed - CVE-2024-9911 confirmed in token_validator.py and middleware.py
- execute: completed - patch applied, all 47 regression tests passed
- review: completed - diff approved, PR merged to main

Goal: Patch and deploy CVE-2024-9911 fix to production auth-service without downtime
Completion Criteria: All regression tests pass, PR merged, production deployment verified
Scope: src/auth/token_validator.py, src/auth/middleware.py, tests/test_auth.py
Risk: high

Implemented: JWT algorithm allowlist enforced in token_validator.py and middleware.py
Validation: 47 regression tests passed, zero new vulnerabilities detected
Changes: src/auth/token_validator.py, src/auth/middleware.py, tests/test_auth.py, CHANGELOG
Risks/next steps: Monitor production logs for auth anomalies; schedule follow-up audit in 30 days
"""

with open("workspace/ops/missions/mission_brief_99.txt", "w", encoding="utf-8") as f:
    f.write(brief_content)

print("Workspace generated successfully.")
print("Files created:")
for path in list(files.keys()) + ["workspace/ops/missions/mission_brief_99.txt"]:
    print(f"  {path}")