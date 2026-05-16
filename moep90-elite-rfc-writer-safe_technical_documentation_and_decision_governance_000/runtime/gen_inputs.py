import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Directory Structure: Realistic CI/CD platform engineering repo ---
dirs = [
    "references",
    "docs/architecture",
    "docs/runbooks",
    "pipeline/jenkins",
    "pipeline/tekton",
    "pipeline/shared-libs",
    "infra/terraform",
    "infra/helm-charts",
    "scripts",
    "meetings/2024-Q3",
    "meetings/2024-Q4",
    "rfc/archive",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "docs/architecture/current-state.md": """# Current Architecture

Jenkins runs on a dedicated EC2 instance (t3.xlarge). 
~80 pipelines active. Build times average 12 minutes.
No containerized build agents currently.
""",
    "docs/architecture/tekton-poc-notes.md": """# Tekton PoC Notes (Draft)

Ran a proof-of-concept in the dev cluster (Jan 2024).
Tekton pipelines executed successfully for 3 microservices.
Average build time: 9.2 minutes (container-native agents).
Known issue: secret management differs significantly from Jenkins credentials plugin.
""",
    "docs/runbooks/jenkins-backup.md": """# Jenkins Backup Runbook

1. Stop Jenkins service
2. Archive $JENKINS_HOME
3. Upload to S3 bucket: s3://platform-backups/jenkins/
4. Restart Jenkins
""",
    "pipeline/jenkins/Jenkinsfile.example": """pipeline {
  agent { label 'linux' }
  stages {
    stage('Build') { steps { sh 'make build' } }
    stage('Test')  { steps { sh 'make test' } }
    stage('Push')  { steps { sh 'make push' } }
  }
}
""",
    "pipeline/tekton/pipeline-run-example.yaml": """apiVersion: tekton.dev/v1
kind: PipelineRun
metadata:
  name: build-and-push
spec:
  pipelineRef:
    name: build-test-push
  params:
    - name: IMAGE
      value: registry.internal/myapp:latest
""",
    "pipeline/shared-libs/README_INTERNAL.txt": """Internal shared Groovy libraries for Jenkins.
Do not delete. ~23 pipelines depend on these.
Migration impact: HIGH.
""",
    "infra/terraform/main.tf": """resource "aws_instance" "jenkins_master" {
  ami           = "ami-0abcdef1234567890"
  instance_type = "t3.xlarge"
  tags = { Name = "jenkins-master-prod" }
}
""",
    "infra/helm-charts/tekton-values.yaml": """tekton-pipelines:
  controller:
    replicas: 2
  webhook:
    replicas: 2
""",
    "scripts/migrate_jobs.py": """#!/usr/bin/env python3
# Stub: converts Jenkinsfile to Tekton Pipeline YAML
# NOT production-ready
import sys

def convert(jenkinsfile_path):
    raise NotImplementedError("Conversion logic not implemented")

if __name__ == '__main__':
    convert(sys.argv[1])
""",
    "meetings/2024-Q3/platform-sync-notes.md": """# Platform Sync - 2024-09-10

Attendees: Alice (Platform Lead), Bob (SRE), Carol (Security), Dave (Finance)

Action items:
- Evaluate Tekton as Jenkins replacement (Alice)
- Cost analysis for Jenkins vs Tekton on EKS (Dave)
- Security review of Tekton RBAC model (Carol)
""",
    "meetings/2024-Q4/decision-needed.md": """# Q4 Architecture Decision Required

Leadership has requested a formal decision document for the CI/CD migration by 2025-01-31.
Decision owner: Alice Müller (Platform Lead)
Approval needed from: CTO, Security, Finance
""",
    "rfc/archive/rfc-observability-stack-2023.md": """# Zusammenfassung
Wir migrieren von einem selbst-gehosteten Prometheus zu einem verwalteten Grafana Cloud Stack.

# Motivation
...

# Ziele
...
""",
}

for fpath, content in distractor_files.items():
    full_path = workspace / fpath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

# --- References directory: rfc-intake-checklist.md ---
intake_checklist = """# RFC Intake Checklist

Before drafting an RFC, confirm the following five categories are present:

## 1. Problem to Solve
- Is the problem clearly stated?
- Is there measurable evidence the problem exists?

## 2. Stakeholders Affected
- Who is impacted by this decision?
- Who needs to approve?

## 3. Constraints
- Technical constraints (e.g., language, platform, infrastructure limits)
- Organizational constraints (e.g., team size, skill gaps)
- Regulatory constraints (e.g., compliance requirements)
- Financial constraints (e.g., budget caps)

## 4. Alternatives Considered
- At least two alternatives must be documented.
- For each alternative: why was it rejected?

## 5. Risks and Open Questions
- List all known risks.
- List open questions with a named owner and a due date.

If any category is missing: ASK before drafting.
"""
(workspace / "references/rfc-intake-checklist.md").write_text(intake_checklist, encoding="utf-8")

# --- References directory: decision-guardrails.md ---
decision_guardrails = """# Decision Guardrails (Project-Syn Inspired)

These guardrails apply inside each mandatory RFC section.

## Zusammenfassung
- Must state decision status: one of [speculative, draft, accepted, rejected, implemented, obsolete]
- Must state the decision owner (named person or role)
- Must state the decision date (or "pending")

## Motivation
- Must include measurable evidence that the problem exists (e.g., metrics, incident count, cost data)
- Must list all assumptions explicitly (label them as "Annahme:")

## Ziele
- Each goal must have a measurable success criterion
- Format: bullet points

## Nicht-Ziele
- Must explicitly mark what is out-of-scope
- Must identify no-go areas to avoid scope creep
- Format: bullet points

## Vorschlag
- Must include a migration path when operationally relevant
- Must include a rollback strategy when operationally relevant
- Must list key constraints (technical, organizational, regulatory, financial)

## Anhang
- Must include alternatives considered and the reason each was rejected
- Must include drawbacks/risks with mitigations
- Must include open questions, each with a named owner and a due date
- Must include references to tickets, PRs, or documents used as evidence

## Tone
- Neutral and analytical
- No marketing language
- Statements should be testable/falsifiable where possible
"""
(workspace / "references/decision-guardrails.md").write_text(decision_guardrails, encoding="utf-8")

# --- THE CORE INPUT: Raw, messy intake brief ---
intake_brief = """From: Dave Chen <d.chen@platform-internal.example>
To: Platform Team
Subject: CI/CD Migration - Please write up the decision doc

Hi team,

We really need to get this formalized. Here's everything I know. Sorry it's a bit scattered.

=== What's the problem? ===

Our Jenkins setup is becoming a serious liability. We have one Jenkins master (EC2 t3.xlarge),
no HA, and it went down twice in Q3 2024 causing ~6 hours of total CI downtime across 3 incidents.
Each incident costs us roughly €4,200 in delayed deployments and engineer time.
Maintenance overhead is ~10 engineer-hours/month just keeping Jenkins alive (plugins, updates, credential rotation).
We currently have 80 active pipelines and the instance is at ~78% CPU during peak build hours.
We need to decide whether to migrate to Tekton (running on our existing EKS cluster) or keep investing in Jenkins.

=== Who is affected? ===

All 6 engineering squads use CI/CD daily. Platform team (3 people) owns the infra.
Security team (Carol Brandt) needs to sign off - they care about RBAC and secret handling.
Finance (represented by Dave Chen) has approved up to €15,000 one-time migration budget.
CTO (Ingrid Hofer) has final approval authority.
Decision owner: Alice Müller, Platform Lead.

=== Constraints ===

Technical:
- We're already on EKS (Kubernetes 1.29). Tekton runs natively there.
- 23 Jenkins pipelines use shared Groovy libraries. There is no direct equivalent in Tekton. These need manual rewriting.
- Secret management: we use the Jenkins Credentials Plugin. Tekton requires a different approach (Kubernetes Secrets or external vault).

Organizational:
- Platform team has only 3 engineers. Migration cannot take more than 3 months elapsed time.
- All 6 squads need ~1 day of onboarding training for Tekton.

Regulatory:
- We must maintain full audit logs of all pipeline executions (SOC 2 Type II requirement).
- Tekton provides execution logs via Kubernetes-native mechanisms; we need to confirm archival meets 12-month retention requirement.

Financial:
- Migration budget: max €15,000 one-time.
- Ongoing: Tekton has no licensing fee. Jenkins has no license fee but EC2 costs ~€380/month. Tekton would run on existing EKS nodes (marginal cost).
- Target: eliminate the €380/month EC2 cost within 6 months of decision.

=== Alternatives we looked at ===

1. Keep Jenkins as-is, but add a standby master for HA.
   Rejected because: still a single point of architectural complexity, plugin ecosystem stagnation,
   does not resolve the CPU saturation issue long-term, adds ~€200/month for the standby instance.

2. Migrate to GitHub Actions (cloud-hosted runners).
   Rejected because: would require sending build artifacts and source code to GitHub's cloud infrastructure,
   violating our data residency policy (all builds must stay on-prem/EU-region EKS). Also: variable cost model
   is unpredictable at our pipeline volume (~3,200 builds/month).

3. Migrate to Tekton on EKS (PROPOSED).
   This is what we're proposing to formalize.

=== Risks and open questions ===

Risks:
- Groovy library migration is the highest risk item. No automated tool exists. Manual effort estimated 80–120 hours.
- If Tekton adoption fails mid-migration, we'd need to roll back to Jenkins (which will still be running in parallel during migration phase).
- SOC 2 log retention: unconfirmed whether Kubernetes-native log archival meets 12-month requirement.
- Team skill gap: platform team has Tekton PoC experience but no production experience.

Open questions:
1. Does our current log archival setup (Loki + S3) meet the 12-month SOC 2 retention requirement? Owner: Carol Brandt. Need answer by: 2025-02-15.
2. What is the exact mapping of Jenkins shared Groovy libraries to Tekton Tasks/Pipelines? Owner: Alice Müller. Need answer by: 2025-03-01.
3. Is the €15,000 budget sufficient, given the manual migration effort? Owner: Dave Chen. Need answer by: 2025-01-31.

Please write this up properly. The decision needs to be in draft status since CTO hasn't approved yet.
Target decision date for leadership review: 2025-01-31.

Thanks,
Dave
"""
(workspace / "intake_brief.txt").write_text(intake_brief, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")