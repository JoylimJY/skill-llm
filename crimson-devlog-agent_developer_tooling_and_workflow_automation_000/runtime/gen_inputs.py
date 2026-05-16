import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create a deeply nested distractor directory structure
dirs = [
    "infra/terraform/modules/networking",
    "infra/terraform/modules/compute",
    "infra/terraform/environments/staging",
    "infra/terraform/environments/prod",
    "services/auth-service/src",
    "services/auth-service/tests",
    "services/pipeline-service/src",
    "services/pipeline-service/configs",
    "monitoring/dashboards",
    "monitoring/alerts",
    "docs/architecture",
    "docs/runbooks",
    "scripts/deploy",
    "scripts/migrate",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "infra/terraform/modules/networking/main.tf": 'resource "aws_vpc" "main" { cidr_block = "10.0.0.0/16" }',
    "infra/terraform/modules/compute/variables.tf": 'variable "instance_type" { default = "t3.medium" }',
    "infra/terraform/environments/staging/terraform.tfvars": 'environment = "staging"\nregion = "us-east-1"',
    "infra/terraform/environments/prod/terraform.tfvars": 'environment = "prod"\nregion = "us-west-2"',
    "services/auth-service/src/main.py": "# Auth service entrypoint\ndef main():\n    pass",
    "services/auth-service/tests/test_auth.py": "def test_login():\n    assert True",
    "services/pipeline-service/src/pipeline.py": "# Pipeline orchestrator\nclass Pipeline:\n    def run(self): pass",
    "services/pipeline-service/configs/config.yaml": "timeout: 300\nretries: 3\nlog_level: INFO",
    "monitoring/dashboards/overview.json": json.dumps({"title": "Ops Overview", "panels": []}),
    "monitoring/alerts/cpu_alert.yaml": "alert: HighCPU\nexpr: cpu_usage > 90\nfor: 5m",
    "docs/architecture/system_design.md": "# System Design\n## Overview\nMicroservices architecture with event-driven messaging.",
    "docs/runbooks/incident_response.md": "# Incident Response\n1. Page on-call\n2. Assess impact\n3. Mitigate",
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying...'",
    "scripts/migrate/run_migration.sh": "#!/bin/bash\necho 'Running DB migration...'",
}

for rel_path, content in distractor_files.items():
    (workspace / rel_path).write_text(content)

# The sprint_retrospective_brief.txt - the raw, messy business input the agent needs to process
brief_content = """
SPRINT 42 RETROSPECTIVE BRIEF
==============================
Team: Platform Engineering
Duration: 2 weeks

--- PROJECT: Infra Modernization ---

[DONE] Completed full migration of legacy VPC peering to Transit Gateway.
Involved: networking, terraform, aws
Outcome: Reduced cross-region latency by 40%

[DONE] Finished automated DR failover script for RDS clusters.
Involved: rds, disaster-recovery, automation
Outcome: RTO reduced from 4h to 15min

[BLOCKED] Pipeline service deployment to prod is stuck.
Reason: TLS certificate renewal failed, cert-manager pod crashlooping.
Involved: kubernetes, tls, cert-manager
Next steps: escalate to security team

[IN PROGRESS] Refactoring Terraform state backend from S3+DynamoDB to Terraform Cloud.
Involved: terraform, state-management, refactor
Progress: 60% complete, staging done, prod pending

--- PROJECT: Auth Service Hardening ---

[DONE] Implemented OAuth2 PKCE flow for all mobile clients.
Involved: oauth2, pkce, mobile, security
Outcome: Eliminated auth token interception risk

[DONE] Added rate limiting middleware to all public auth endpoints.
Involved: rate-limiting, middleware, security
Outcome: Mitigated 3 potential brute-force vectors

[BLOCKED] MFA enforcement rollout paused.
Reason: Downstream service (notifications-svc) not ready for webhook integration.
Involved: mfa, webhooks, notifications
Next steps: coordinate with notifications team, target next sprint

[IN PROGRESS] Security audit of JWT signing key rotation process.
Involved: jwt, key-rotation, security-audit
Progress: Audit complete, remediation plan drafted

==============================
NOTE: All entries must be logged into our centralized dev tracking system before EOD Friday.
A summary JSON file named sprint42_summary.json must be created at the end.
"""

(workspace / "sprint_retrospective_brief.txt").write_text(brief_content)

print("Workspace initialized successfully.")
print(f"Files created: {len(distractor_files)} distractor files + sprint_retrospective_brief.txt")