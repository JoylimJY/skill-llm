import os
import random
import stat

random.seed(42)

workspace = os.environ.get("WORKSPACE", "/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "config/app",
    "config/db",
    "config/cache",
    "logs/app",
    "logs/infra",
    "deploy/staging",
    "deploy/prod",
    "monitoring/alerts",
    "monitoring/dashboards",
    "docs/runbooks",
    "docs/architecture",
    "tests/integration",
    "tests/smoke",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "config/app/settings.yaml": """\
app:
  name: finpay-gateway
  env: staging
  debug: false
  log_level: INFO
""",
    "config/db/postgres.conf": """\
host=localhost
port=5432
dbname=finpay
user=svc_account
password=REDACTED
pool_size=10
""",
    "config/cache/redis.conf": """\
bind 127.0.0.1
port=6379
maxmemory 512mb
maxmemory-policy allkeys-lru
""",
    "config/app/feature_flags.json": """\
{
  "new_payment_flow": true,
  "legacy_auth": false,
  "rate_limiting": true
}
""",
    "logs/app/app.log": """\
2024-06-01 10:00:01 INFO  [startup] finpay-gateway starting
2024-06-01 10:00:02 INFO  [db] connected to postgres
2024-06-01 10:00:03 ERROR [cache] redis connection refused
2024-06-01 10:00:04 WARN  [api] upstream slow response 4200ms
""",
    "logs/infra/deploy.log": """\
[deploy] 2024-06-01 09:55:00 - starting staging rollout
[deploy] 2024-06-01 09:55:45 - pods healthy: 3/3
[deploy] 2024-06-01 09:56:10 - smoke tests passed
""",
    "deploy/staging/manifest.yaml": """\
services:
  - name: finpay-api
    port: 8080
  - name: postgres
    port: 5432
  - name: redis
    port: 6379
  - name: metrics
    port: 9090
  - name: admin-ui
    port: 3000
""",
    "deploy/prod/checklist.md": """\
# Production Deployment Checklist
- [ ] All services health-checked
- [ ] Database migrations applied
- [ ] Cache warmed
- [ ] Load balancer rules confirmed
- [ ] Rollback plan documented
""",
    "monitoring/alerts/rules.yaml": """\
alerts:
  - name: HighErrorRate
    expr: rate(http_requests_total{status=~\"5..\"}[5m]) > 0.05
    severity: critical
  - name: ServiceDown
    expr: up == 0
    severity: critical
""",
    "monitoring/dashboards/overview.json": """\
{
  "title": "FinPay Overview",
  "panels": ["Request Rate", "Error Rate", "Latency p99", "DB Connections"]
}
""",
    "docs/runbooks/incident_response.md": """\
# Incident Response Runbook
1. Identify affected service
2. Check service health endpoints
3. Review recent deployments
4. Escalate if unresolved within 15 minutes
""",
    "docs/architecture/service_map.txt": """\
[client] --> [finpay-api:8080] --> [postgres:5432]
                               --> [redis:6379]
                               --> [payment-svc:8081]
[finpay-api:8080] --> [metrics:9090]
""",
    "tests/integration/db_test.py": """\
import psycopg2
def test_db_connection():
    conn = psycopg2.connect(host='localhost', port=5432, dbname='finpay')
    assert conn is not None
""",
    "tests/smoke/api_smoke.sh": """\
#!/bin/bash
curl -sf http://localhost:8080/health || exit 1
curl -sf http://localhost:8080/ready || exit 1
echo 'Smoke tests passed'
""",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── The actual port-check script (the skill script) ──────────────────────────
# This is what the SKILL.md says already exists in scripts/
port_check_script = r"""#!/bin/bash
# port-check.sh — Check if services are responding on given host:port pairs.
# Supports TCP and HTTP checks with configurable timeout.

set -euo pipefail

TIMEOUT=3
HTTP_MODE=false
TARGETS=()
EXIT_CODE=0

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --http)
            HTTP_MODE=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        *)
            TARGETS+=("$1")
            shift
            ;;
    esac
done

for target in "${TARGETS[@]}"; do
    HOST="${target%%:*}"
    PORT="${target##*:}"

    # TCP check
    if nc -z -w "$TIMEOUT" "$HOST" "$PORT" 2>/dev/null; then
        if [ "$HTTP_MODE" = true ]; then
            HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                --max-time "$TIMEOUT" "http://${HOST}:${PORT}/" 2>/dev/null || echo "000")
            if [ "$HTTP_STATUS" = "200" ]; then
                echo "✅ ${target} — open (HTTP 200)"
            else
                echo "⚠️ ${target} — open but HTTP ${HTTP_STATUS}"
                EXIT_CODE=1
            fi
        else
            echo "✅ ${target} — open"
        fi
    else
        echo "❌ ${target} — closed/timeout"
        EXIT_CODE=1
    fi
done

exit $EXIT_CODE
"""

script_path = os.path.join(workspace, "scripts", "port-check.sh")
with open(script_path, "w") as f:
    f.write(port_check_script)

os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# ── Task brief for the agent ─────────────────────────────────────────────────
# (This is not a README/hint — it is the business context document)
brief = """\
## Pre-Deployment Service Health Gate — FinPay Staging Stack

Engineering has requested a connectivity snapshot before the next production push.
The following endpoints must be verified:

TCP-only targets:
  - localhost:5432   (PostgreSQL — expected UP)
  - localhost:6379   (Redis — expected DOWN in staging)
  - localhost:9999   (legacy-svc — expected DOWN, decommissioned)

HTTP targets (need HTTP response code verification):
  - localhost:8080   (finpay-api — expected UP, returns 200)
  - localhost:8081   (payment-svc — expected UP, returns 500 — known issue)

All checks should use a timeout of 2 seconds.

Save the combined output of all checks to: health_report.txt
"""

brief_path = os.path.join(workspace, "deploy", "staging", "health_gate_brief.txt")
with open(brief_path, "w") as f:
    f.write(brief)

print(f"Workspace prepared at: {workspace}")
print("Created scripts/port-check.sh and distractor files.")