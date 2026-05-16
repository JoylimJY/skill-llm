import os
import random

random.seed(42)

base = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "infra/deploy/k8s",
    "infra/deploy/helm",
    "infra/monitoring",
    "infra/ci",
    "services/api-gateway",
    "services/auth",
    "services/data-pipeline",
    "docs/runbooks",
    "docs/architecture",
    "scripts/maintenance",
    "scripts/bootstrap",
    "tests/integration",
    "tests/unit",
    "config/environments",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────

# 1. Kubernetes deployment YAML (distractor)
with open(os.path.join(base, "infra/deploy/k8s/deployment.yaml"), "w") as f:
    f.write("""\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: company/api-gateway:v2.1.0
        ports:
        - containerPort: 8080
        env:
        - name: LOG_LEVEL
          value: "info"
""")

# 2. Helm values (distractor)
with open(os.path.join(base, "infra/deploy/helm/values.yaml"), "w") as f:
    f.write("""\
replicaCount: 2
image:
  repository: company/auth-service
  tag: "1.4.2"
service:
  type: ClusterIP
  port: 80
ingress:
  enabled: true
  hosts:
    - host: auth.company.internal
      paths: ["/"]
resources:
  limits:
    cpu: 500m
    memory: 512Mi
""")

# 3. Prometheus config (distractor)
with open(os.path.join(base, "infra/monitoring/prometheus.yml"), "w") as f:
    f.write("""\
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
""")

# 4. CI pipeline (distractor)
with open(os.path.join(base, "infra/ci/pipeline.yml"), "w") as f:
    f.write("""\
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

test:
  stage: test
  script:
    - pytest tests/ --cov=src --cov-report=xml

deploy:
  stage: deploy
  only:
    - main
  script:
    - helm upgrade --install app ./chart --set image.tag=$CI_COMMIT_SHA
""")

# 5. Auth service config (distractor .conf with non-standard extension)
with open(os.path.join(base, "services/auth/service.conf"), "w") as f:
    f.write("""\
# Auth Service Configuration
service_name: auth-service
version: 1.4.2

database:
  host: postgres.internal
  port: 5432
  name: auth_db
  pool_size: 10
  max_overflow: 20

jwt:
  secret_key: ${JWT_SECRET}
  algorithm: HS256
  expiry_seconds: 3600

redis:
  host: redis.internal
  port: 6379
  db: 0
  ttl: 86400

logging:
  level: info
  format: json
  output: stdout
""")

# 6. Data pipeline script (distractor)
with open(os.path.join(base, "services/data-pipeline/transform.py"), "w") as f:
    f.write("""\
#!/usr/bin/env python3
\"\"\"Data transformation pipeline.\"\"\"
import json
import sys
from pathlib import Path


def load_records(path: str) -> list:
    with open(path) as fh:
        return json.load(fh)


def validate_record(record: dict) -> bool:
    required = {"id", "timestamp", "payload"}
    return required.issubset(record.keys())


def transform(record: dict) -> dict:
    return {
        "record_id": record["id"],
        "ts": record["timestamp"],
        "data": record["payload"],
        "processed": True,
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: transform.py <input.json>")
        sys.exit(1)
    records = load_records(sys.argv[1])
    valid = [r for r in records if validate_record(r)]
    output = [transform(r) for r in valid]
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
""")

# 7. Maintenance script (distractor)
with open(os.path.join(base, "scripts/maintenance/cleanup.sh"), "w") as f:
    f.write("""\
#!/usr/bin/env bash
set -euo pipefail

RETENTION_DAYS=${1:-30}
LOG_DIR="/var/log/app"
BACKUP_DIR="/backup/logs"

echo "Cleaning logs older than ${RETENTION_DAYS} days..."
find "$LOG_DIR" -name "*.log" -mtime +"$RETENTION_DAYS" -exec mv {} "$BACKUP_DIR/" \\;
echo "Compressing backup logs..."
find "$BACKUP_DIR" -name "*.log" -exec gzip {} \\;
echo "Done."
""")

# 8. Bootstrap script (distractor)
with open(os.path.join(base, "scripts/bootstrap/init.sh"), "w") as f:
    f.write("""\
#!/usr/bin/env bash
set -euo pipefail

apt-get update
apt-get install -y curl wget git jq

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
mv kubectl /usr/local/bin/

echo "Bootstrap complete."
""")

# 9. Architecture doc (distractor)
with open(os.path.join(base, "docs/architecture/overview.md"), "w") as f:
    f.write("""\
# System Architecture Overview

## Components

### API Gateway
Routes incoming requests to backend microservices. Handles rate limiting and auth token validation.

### Auth Service
Issues JWT tokens after validating credentials against the user database.

### Data Pipeline
Processes and transforms event streams from Kafka into structured records stored in PostgreSQL.

## Communication
All internal services communicate via gRPC. External-facing endpoints use REST over HTTPS.
""")

# 10. Integration test (distractor)
with open(os.path.join(base, "tests/integration/test_gateway.py"), "w") as f:
    f.write("""\
import pytest
import httpx


BASE_URL = "http://localhost:8080"


@pytest.fixture(scope="session")
def client():
    return httpx.Client(base_url=BASE_URL, timeout=10.0)


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_unauthorized_request(client):
    resp = client.get("/api/v1/users")
    assert resp.status_code == 401


def test_rate_limiting(client):
    for _ in range(100):
        client.get("/api/v1/ping")
    resp = client.get("/api/v1/ping")
    assert resp.status_code == 429
""")

# ── TARGET FILE 1: deploy.sh ─────────────────────────────────────────────────
# The agent must extract lines 14-28 and 41-55 with style=numbers,changes,header
# and --paging=never --color=never
with open(os.path.join(base, "infra/deploy/deploy.sh"), "w") as f:
    f.write("""\
#!/usr/bin/env bash
# deploy.sh - Production deployment orchestrator
# Managed by Platform Engineering Team
# Last reviewed: 2024-01-15
#
# Usage: ./deploy.sh <environment> <version>
# Environments: staging, production, canary
#
# Dependencies: kubectl, helm, docker
# Required env vars: KUBECONFIG, REGISTRY_URL, SLACK_WEBHOOK
#
# Exit codes: 0=success, 1=validation_error, 2=deploy_error, 3=rollback_error

set -euo pipefail

# ── Validation Phase ──────────────────────────────────────────────────────────
validate_inputs() {
    local env="$1"
    local version="$2"

    if [[ ! "$env" =~ ^(staging|production|canary)$ ]]; then
        echo "ERROR: Invalid environment '$env'" >&2
        exit 1
    fi

    if [[ ! "$version" =~ ^v[0-9]+\\.[0-9]+\\.[0-9]+$ ]]; then
        echo "ERROR: Invalid version format '$version' (expected vX.Y.Z)" >&2
        exit 1
    fi

    echo "Inputs validated: env=$env version=$version"
}

# ── Pre-flight Checks ─────────────────────────────────────────────────────────
preflight_checks() {
    local env="$1"
    echo "Running pre-flight checks for $env..."

    # Check cluster connectivity
    kubectl cluster-info --context="$env" > /dev/null 2>&1 || {
        echo "ERROR: Cannot connect to cluster '$env'" >&2
        exit 2
    }

    # Verify image exists in registry
    docker manifest inspect "${REGISTRY_URL}/app:${VERSION}" > /dev/null 2>&1 || {
        echo "ERROR: Image not found in registry" >&2
        exit 2
    }

    # Check namespace exists
    kubectl get namespace "$env" > /dev/null 2>&1 || {
        echo "ERROR: Namespace '$env' not found" >&2
        exit 2
    }

    echo "Pre-flight checks passed."
}

# ── Deploy Phase ──────────────────────────────────────────────────────────────
deploy_application() {
    local env="$1"
    local version="$2"

    echo "Deploying version $version to $env..."

    helm upgrade --install app ./chart \\
        --namespace "$env" \\
        --set image.tag="$version" \\
        --set environment="$env" \\
        --wait \\
        --timeout 5m

    echo "Deploy complete."
}

# ── Rollback Handler ──────────────────────────────────────────────────────────
rollback() {
    local env="$1"
    echo "ROLLING BACK deployment in $env..." >&2
    helm rollback app --namespace "$env" || {
        echo "CRITICAL: Rollback failed in $env!" >&2
        exit 3
    }
    echo "Rollback complete."
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
    local env="${1:?Environment required}"
    local version="${2:?Version required}"

    trap 'rollback "$env"' ERR

    validate_inputs "$env" "$version"
    preflight_checks "$env"
    deploy_application "$env" "$version"

    echo "SUCCESS: $version deployed to $env"
}

main "$@"
""")

# ── TARGET FILE 2: app.conf ──────────────────────────────────────────────────
# The agent must extract lines 5-19 forced as YAML language
# with style=numbers,changes,header and --paging=never --color=never
with open(os.path.join(base, "config/environments/production.app.conf"), "w") as f:
    f.write("""\
# Production Application Configuration
# Environment: production
# Owner: Platform Engineering
# Config version: 3.2.1
server:
  host: 0.0.0.0
  port: 8443
  workers: 16
  timeout: 30
  keepalive: 75
  max_connections: 10000
  ssl:
    enabled: true
    cert_file: /etc/ssl/certs/app.crt
    key_file: /etc/ssl/private/app.key
    protocols: [TLSv1.2, TLSv1.3]
    ciphers: ECDHE+AESGCM:ECDHE+AES256

database:
  primary:
    host: postgres-primary.internal
    port: 5432
    name: appdb_prod
    user: app_user
    password: ${DB_PASSWORD}
    pool:
      min: 5
      max: 50
      overflow: 10
  replica:
    host: postgres-replica.internal
    port: 5432
    name: appdb_prod
    read_only: true

cache:
  backend: redis
  host: redis-cluster.internal
  port: 6379
  password: ${REDIS_PASSWORD}
  db: 0
  ttl: 3600
  max_memory: 4gb
  eviction_policy: allkeys-lru

feature_flags:
  new_checkout_flow: true
  experimental_search: false
  dark_mode: true
  analytics_v2: true
""")

# 11. Config for other env (distractor)
with open(os.path.join(base, "config/environments/staging.app.conf"), "w") as f:
    f.write("""\
# Staging Application Configuration
server:
  host: 0.0.0.0
  port: 8080
  workers: 4
  timeout: 30
database:
  primary:
    host: postgres-staging.internal
    port: 5432
    name: appdb_staging
""")

# 12. Runbook (distractor)
with open(os.path.join(base, "docs/runbooks/incident_response.md"), "w") as f:
    f.write("""\
# Incident Response Runbook

## Severity Levels
- P0: Total outage — page on-call immediately
- P1: Degraded performance — alert team channel
- P2: Minor issue — create ticket

## Steps
1. Acknowledge the alert
2. Check dashboards
3. Identify root cause
4. Apply fix or rollback
5. Write post-mortem
""")

print("Workspace generated successfully.")