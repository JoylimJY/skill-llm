import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Realistic DevOps project structure (distractor files) ──────────────────────
dirs = [
    "infra/k8s/namespaces",
    "infra/k8s/deployments",
    "infra/k8s/services",
    "infra/terraform/modules/networking",
    "infra/terraform/modules/compute",
    "infra/scripts",
    "infra/monitoring/dashboards",
    "infra/monitoring/alerts",
    "docs/runbooks",
    "docs/adr",
    "ci/.github/workflows",
    "src/api",
    "src/frontend",
    "tests/integration",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files ──────────────────────────────────────────────────────────────
distractor_files = {
    "infra/k8s/namespaces/production.yaml": """\
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    env: prod
""",
    "infra/k8s/deployments/api-server.yaml": """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-server
""",
    "infra/k8s/services/api-service.yaml": """\
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: production
spec:
  type: ClusterIP
  ports:
    - port: 8080
""",
    "infra/terraform/modules/networking/vpc.tf": """\
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "k8s-migration-vpc"
  }
}
""",
    "infra/terraform/modules/compute/eks.tf": """\
resource "aws_eks_cluster" "main" {
  name     = "prod-cluster-v2"
  role_arn = var.cluster_role_arn
}
""",
    "infra/scripts/migrate_namespaces.sh": """\
#!/bin/bash
# Phase 2: Namespace migration script
set -euo pipefail
CONTEXTS=(old-cluster new-cluster)
for ctx in "${CONTEXTS[@]}"; do
    kubectl --context=$ctx get namespaces
done
""",
    "infra/scripts/validate_dns.sh": """\
#!/bin/bash
# DNS cutover validation
nslookup api.internal.company.com || echo "DNS not yet propagated"
""",
    "infra/monitoring/dashboards/cluster_health.json": json.dumps({
        "title": "Cluster Health Overview",
        "panels": ["CPU Usage", "Memory Pressure", "Pod Restart Rate"],
        "refresh": "30s"
    }, indent=2),
    "infra/monitoring/alerts/pagerduty_rules.yaml": """\
groups:
  - name: k8s-migration-alerts
    rules:
      - alert: PodCrashLoopBackOff
        expr: kube_pod_container_status_waiting_reason{reason="CrashLoopBackOff"} > 0
        for: 5m
""",
    "docs/runbooks/cluster_migration.md": """\
# Kubernetes Cluster Migration Runbook

## Overview
This runbook covers the 4-phase migration from EKS 1.24 to EKS 1.30.

## Phases
1. Pre-migration validation
2. Namespace + workload migration
3. DNS cutover
4. Decommission old cluster

## Current Status
PHASE 2 IN PROGRESS — workload migration 60% complete.
DNS cutover blocked pending security team sign-off.

## Known Issues
- StatefulSet `postgres-primary` has not been migrated (data volume incompatibility).
- Ingress controller version mismatch between old and new cluster.
""",
    "docs/adr/001-eks-version-target.md": """\
# ADR-001: Target EKS Version

## Status: Accepted
## Decision: Migrate to EKS 1.30 (LTS)
## Rationale: Security patches, Karpenter support, cost savings via Graviton nodes.
""",
    "docs/adr/002-migration-strategy.md": """\
# ADR-002: Blue-Green Migration Strategy

## Status: Accepted
## Decision: Run old and new clusters in parallel for 30 days.
## Consequence: Double infrastructure cost during transition window.
""",
    "ci/.github/workflows/terraform_plan.yaml": """\
name: Terraform Plan
on: [pull_request]
jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: terraform init && terraform plan
""",
    "tests/integration/test_api_health.py": """\
import requests
def test_api_health():
    resp = requests.get("http://api.internal.company.com/health")
    assert resp.status_code == 200
""",
    "src/api/main.py": """\
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
""",
}

for relpath, content in distractor_files.items():
    fpath = workspace / relpath
    fpath.write_text(content)

# ── The task briefing given to the agent (the "business ask") ──────────────────
# This file simulates a manager's note dropped into the workspace
task_brief = """\
# Infrastructure Migration — Agent Context Brief

The team is in the middle of a multi-phase Kubernetes cluster migration (EKS 1.24 → EKS 1.30).

## Current Situation
- Phase 2 (workload migration) is 60% complete.
- Last decision made: Defer `postgres-primary` StatefulSet migration until the storage team provides a compatible CSI driver. Ticket: INFRA-4421.
- Blocker identified: Security team has not signed off on DNS cutover (waiting since 2024-11-12). Owner: @sarah.chen.
- Next logical move: Validate all non-stateful workloads in the new cluster pass health checks before the security sign-off arrives.

## Boundary Rules the Agent Must Respect
- Agent MUST NOT initiate DNS cutover or decommission old cluster without written approval.
- Agent MUST NOT modify any Terraform state or run `terraform apply` without a peer review.
- Agent CAN run read-only kubectl commands and validation scripts autonomously.
- Agent CAN propose changes to runbooks as drafts.

## Long Task Recovery Notes
- We were last working on the ingress controller version mismatch (old: nginx 1.9, new: nginx 1.11).
- Attempted fix: bumped `ingress-nginx` helm chart to 4.9.1. Outcome: partial — TLS termination works but gRPC routing still broken.
- Next micro-step: Check if annotation `nginx.ingress.kubernetes.io/backend-protocol: GRPC` is missing from gRPC service definitions.

## Reusable Patterns From Past Work
- Pattern: "validate-before-cut" — Always run a full smoke test suite against the new cluster endpoint before flipping any DNS record. Has saved 3 rollbacks.
- Pattern: "draft-then-approve" — For runbook edits, create a draft section and flag it with [DRAFT] prefix for team review.

## Recent Actions Log
- [2024-11-14 09:12] Migrated `auth-service` deployment to new cluster. Outcome: Success.
- [2024-11-14 11:45] Attempted `postgres-primary` migration. Outcome: Blocked (CSI incompatibility). Deferred to INFRA-4421.
- [2024-11-14 14:30] Ran smoke tests on new cluster for `api-server`, `worker`, `scheduler`. Outcome: All passed.
- [2024-11-14 16:00] Identified gRPC routing issue in ingress controller. Outcome: Partial fix applied, TLS OK, gRPC still broken.
"""

(workspace / "AGENT_BRIEF.md").write_text(task_brief)

# ── Skeleton AGENTS.md at workspace root (integration trigger) ─────────────────
agents_md = """\
# AGENTS.md — Workspace Agent Configuration

This file is read by any agent operating in this repository.

## Active Skills
- proactivity (pending initialization)

## Team
- @sarah.chen — Security lead, DNS cutover authority
- @devops-team — Day-to-day migration execution

## Communication Channels
- Slack: #k8s-migration (read-only for agents without approval)
"""
(workspace / "AGENTS.md").write_text(agents_md)

# ── Partial / corrupted proactivity state (simulating a crashed session) ──────
# ~/proactivity exists but is incomplete — the agent must detect and fix this
proactivity_home = Path.home() / "proactivity"
proactivity_home.mkdir(exist_ok=True)

# Only memory.md exists but is WRONG / incomplete
(proactivity_home / "memory.md").write_text("""\
# Memory

TODO: fill this in
""")

# session-state.md is missing entirely
# heartbeat.md is missing
# patterns.md is missing  
# log.md is missing
# domains/ directory is missing
# memory/working-buffer.md is missing (memory/ subdir doesn't exist)

print("Workspace generated successfully.")
print(f"Workspace root: {workspace}")
print(f"Proactivity home: {proactivity_home}")
print("Files created:", sum(1 for _ in workspace.rglob("*") if _.is_file()) + 1)