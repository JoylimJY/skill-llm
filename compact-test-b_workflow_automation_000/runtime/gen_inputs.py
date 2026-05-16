#!/usr/bin/env python3
"""
Generate the sandbox workspace for the smart-compact evaluation task.
Creates a realistic DevOps project workspace with:
- A simulated conversation log containing tool outputs of varying sizes
- A pre-existing memory file (to test append-only behavior)
- Distractor files throughout the project
"""

import os
import random
from datetime import datetime, date
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

def create_dirs():
    dirs = [
        "memory",
        "k8s/manifests/prod",
        "k8s/manifests/staging",
        "k8s/helm/charts",
        "terraform/modules/vpc",
        "terraform/modules/eks",
        "scripts/migration",
        "scripts/monitoring",
        "logs/deploy",
        "logs/audit",
        "docs/runbooks",
        "src/api",
        "src/worker",
        ".github/workflows",
    ]
    for d in dirs:
        Path(WORKSPACE, d).mkdir(parents=True, exist_ok=True)

def write_file(path, content):
    full_path = Path(WORKSPACE, path)
    full_path.write_text(content, encoding="utf-8")

def generate_workspace():
    create_dirs()

    # --- Distractor files ---
    write_file("k8s/manifests/prod/namespace.yaml", """apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    env: prod
""")

    write_file("k8s/manifests/staging/namespace.yaml", """apiVersion: v1
kind: Namespace
metadata:
  name: staging
  labels:
    env: staging
""")

    write_file("k8s/helm/charts/values-prod.yaml", """replicaCount: 3
image:
  repository: registry.internal.corp/api
  tag: "1.4.2"
service:
  type: ClusterIP
  port: 8080
resources:
  limits:
    cpu: 500m
    memory: 512Mi
""")

    write_file("terraform/modules/vpc/main.tf", """resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  enable_dns_hostnames = true
  tags = {
    Name = "prod-vpc"
  }
}
""")

    write_file("terraform/modules/eks/variables.tf", """variable "cluster_name" {
  type    = string
  default = "prod-cluster"
}
variable "node_count" {
  type    = number
  default = 5
}
""")

    write_file("scripts/migration/rollback.sh", """#!/bin/bash
set -e
echo "Rolling back deployment..."
kubectl rollout undo deployment/api -n production
""")

    write_file("scripts/monitoring/alert_rules.yaml", """groups:
- name: k8s-alerts
  rules:
  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes > 400000000
    for: 5m
""")

    write_file("logs/deploy/deploy-2024-01-10.log", """[INFO] Starting deployment pipeline
[INFO] Image built: registry.internal.corp/api:1.4.2
[INFO] Helm upgrade completed
[INFO] Health check passed
""")

    write_file("logs/audit/access-2024-01-10.log", """2024-01-10 08:00:01 user=admin action=kubectl-get resource=pods
2024-01-10 08:05:33 user=ci-bot action=helm-upgrade chart=api
2024-01-10 09:12:44 user=admin action=kubectl-logs pod=api-7d9f8b-xk2pl
""")

    write_file("docs/runbooks/eks-migration.md", """# EKS Migration Runbook

## Overview
This runbook covers migration from EKS 1.24 to 1.29.

## Steps
1. Update node groups
2. Drain old nodes
3. Verify workloads
""")

    write_file(".github/workflows/ci.yml", """name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: make test
""")

    write_file("src/api/server.py", """from flask import Flask
app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'ok'}
""")

    write_file("src/worker/processor.py", """import time

def process_job(job_id):
    print(f'Processing job {job_id}')
    time.sleep(0.1)
    return True
""")

    # --- Pre-existing memory file (agent must APPEND, not overwrite) ---
    today = date.today().strftime("%Y-%m-%d")
    existing_memory = f"""# Memory — {today}

## 事实记录

- 集群版本目标：EKS 1.29（从 1.24 升级）
- Terraform 状态存储：s3://corp-terraform-state/prod

## 用户偏好

- 用户偏好使用 Helm 而不是原始 kubectl apply
"""
    write_file(f"memory/{today}.md", existing_memory)

    # --- Main conversation log ---
    # This is the key artifact the agent must analyze
    # It contains:
    # 1. A LARGE kubectl get pods output (>50 lines) with critical pod IPs and statuses
    # 2. A LARGE helm diff output (>2000 chars) showing config changes
    # 3. A small/redundant git status output (should be classified as discardable)
    # 4. An error message + resolution (must save)
    # 5. A decision record (must save)
    # 6. A repeated ls output (discardable)

    # Generate large kubectl output (55 lines of pod data - triggers >50 line threshold)
    kubectl_pods_lines = ["NAME                                      READY   STATUS    RESTARTS   AGE   IP              NODE"]
    node_names = ["ip-10-0-1-101.eu-west-1.compute.internal", "ip-10-0-1-102.eu-west-1.compute.internal", "ip-10-0-2-201.eu-west-1.compute.internal"]
    for i in range(54):
        pod_name = f"api-7d9f8b-{''.join(random.choices('abcdefghijklmnop', k=5))}"
        ip = f"10.0.{random.randint(1,3)}.{random.randint(10,250)}"
        node = random.choice(node_names)
        restarts = random.randint(0, 3)
        kubectl_pods_lines.append(f"{pod_name}   1/1     Running   {restarts}          2h    {ip}   {node}")
    kubectl_pods_output = "\n".join(kubectl_pods_lines)
    # Verify it's >50 lines
    assert len(kubectl_pods_lines) > 50, f"Got {len(kubectl_pods_lines)} lines"

    # Generate large helm diff output (>2000 chars)
    helm_diff_output = """Release "api" has been upgraded. Happy Helming!

MANIFEST:
---
# Source: api/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: production
  labels:
    app: api
    version: 1.4.2
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
        version: 1.4.2
    spec:
      containers:
      - name: api
        image: registry.internal.corp/api:1.4.2
        ports:
        - containerPort: 8080
        env:
        - name: DATABASE_URL
          value: "postgresql://dbuser:REDACTED@db-prod.internal.corp:5432/appdb"
        - name: REDIS_ENDPOINT
          value: "redis://redis-prod.internal.corp:6379/0"
        - name: METRICS_ENDPOINT
          value: "http://prometheus.monitoring.svc.cluster.local:9090"
        - name: LOG_LEVEL
          value: "INFO"
        - name: WORKER_CONCURRENCY
          value: "8"
        resources:
          requests:
            cpu: 250m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
# Source: api/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
---
# Source: api/templates/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70

COMPUTED VALUES:
replicaCount: 3
image:
  repository: registry.internal.corp/api
  tag: 1.4.2
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
"""
    # Verify it's >2000 chars
    assert len(helm_diff_output) > 2000, f"Got {len(helm_diff_output)} chars"

    # Small repeated git status (discardable - just routine output)
    git_status_output = """On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean"""

    # Small error + resolution (critical - must save)
    error_block = """Error from server (Forbidden): pods is forbidden: User "ci-bot" cannot list resource "pods" in API group "" in the namespace "production": requires cluster role binding"""

    resolution_note = """After investigating, the CI bot service account was missing the 'view' ClusterRoleBinding in the production namespace. Fixed by applying:
kubectl create clusterrolebinding ci-bot-view --clusterrole=view --serviceaccount=ci:ci-bot
This resolved the deployment pipeline failure."""

    # Decision record
    decision_note = """Decision: We chose to keep the API Gateway at nginx-ingress rather than migrating to AWS ALB Ingress Controller because the team is more familiar with nginx config and we have custom rate-limiting rules that are hard to replicate in ALB annotations. ALB migration is deferred to Q3."""

    # Second repeated ls output (discardable)
    ls_output_1 = """total 48
drwxr-xr-x  8 user user 4096 Jan 10 09:00 .
drwxr-xr-x 15 user user 4096 Jan 10 08:55 ..
drwxr-xr-x  2 user user 4096 Jan 10 08:00 k8s
drwxr-xr-x  2 user user 4096 Jan 10 08:00 terraform
drwxr-xr-x  2 user user 4096 Jan 10 08:00 scripts
drwxr-xr-x  2 user user 4096 Jan 10 08:00 docs
drwxr-xr-x  2 user user 4096 Jan 10 08:00 src
drwxr-xr-x  2 user user 4096 Jan 10 09:00 memory"""

    ls_output_2 = """total 48
drwxr-xr-x  8 user user 4096 Jan 10 09:15 .
drwxr-xr-x 15 user user 4096 Jan 10 08:55 ..
drwxr-xr-x  2 user user 4096 Jan 10 08:00 k8s
drwxr-xr-x  2 user user 4096 Jan 10 08:00 terraform
drwxr-xr-x  2 user user 4096 Jan 10 08:00 scripts
drwxr-xr-x  2 user user 4096 Jan 10 08:00 docs
drwxr-xr-x  2 user user 4096 Jan 10 08:00 src
drwxr-xr-x  2 user user 4096 Jan 10 09:00 memory"""

    conversation_log = f"""# DevOps Session Log — EKS Migration Debug Session
# Date: {today}
# Participants: Senior DevOps Engineer (SDE), CI/CD Pipeline Bot

---

[09:00:12] SDE: Let's check the current state of pods in production before we proceed with the migration.

[TOOL: kubectl] get pods -n production -o wide
---OUTPUT---
{kubectl_pods_output}
---END---

[09:02:45] SDE: Good, pods look healthy. Now let's see what changed in the last helm deploy.

[TOOL: ls] /workspace
---OUTPUT---
{ls_output_1}
---END---

[09:03:10] SDE: Now the helm diff:

[TOOL: helm] diff upgrade api ./k8s/helm/charts --values k8s/helm/charts/values-prod.yaml
---OUTPUT---
{helm_diff_output}
---END---

[09:08:22] SDE: The helm diff confirms the new image tag and updated HPA config. 
The REDIS_ENDPOINT is now redis://redis-prod.internal.corp:6379/0 and 
DATABASE_URL points to db-prod.internal.corp:5432/appdb — these are the new prod endpoints.

[09:10:01] SDE: Wait, the pipeline failed earlier. Let me check the error.

[TOOL: kubectl] auth can-i list pods --as=system:serviceaccount:ci:ci-bot -n production
---OUTPUT---
{error_block}
---END---

[09:11:30] SDE: Found it. Applying fix now...

[09:14:55] SDE: {resolution_note}

[09:16:00] SDE: Now let me check the directory again.

[TOOL: ls] /workspace
---OUTPUT---
{ls_output_2}
---END---

[09:17:00] SDE: {decision_note}

[09:18:30] SDE: Let me verify cluster version quickly.

[TOOL: kubectl] version --short
---OUTPUT---
Client Version: v1.29.0
Server Version: v1.24.17
---END---

[09:19:00] SDE: The server is still on 1.24.17 — we haven't completed the control plane upgrade yet. Target is 1.29.

[09:20:00] SDE: Also confirmed: the metrics endpoint is http://prometheus.monitoring.svc.cluster.local:9090

[09:21:00] SDE: Context is getting large. Time to run smart-compact before we continue with the upgrade steps.

---END OF SESSION LOG---
"""
    write_file("session_log.txt", conversation_log)

    # Create a checklist output file location hint (just a placeholder dir)
    Path(WORKSPACE, "output").mkdir(exist_ok=True)
    write_file("output/.gitkeep", "")

    print(f"Workspace generated at: {WORKSPACE}")
    print(f"Today's date: {today}")
    print(f"Memory file pre-created: memory/{today}.md")
    print(f"Session log created: session_log.txt")
    print(f"  kubectl pods output: {len(kubectl_pods_lines)} lines (threshold: 50)")
    print(f"  helm diff output: {len(helm_diff_output)} chars (threshold: 2000)")
    print(f"  git status: small (discardable)")
    print(f"  ls outputs: 2x repeated (discardable)")

generate_workspace()