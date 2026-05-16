import os
import json
import random
import string
from pathlib import Path

random.seed(42)

WORKSPACE = os.environ.get("WORKSPACE", "/workspace")

# ── Deep directory structure with distractor files ──────────────────────────
dirs = [
    "services/payment-processor/src",
    "services/payment-processor/tests",
    "services/payment-processor/config",
    "services/fraud-detector/src",
    "services/fraud-detector/config",
    "infra/terraform/modules",
    "infra/k8s/manifests",
    "infra/k8s/secrets",
    "ops/monitoring/dashboards",
    "ops/monitoring/alerts",
    "ops/runbooks",
    "data/raw/2024-06",
    "data/processed",
    "ci/scripts",
    "ci/configs",
    "logs/archive",
    "logs/incidents",
]
for d in dirs:
    Path(os.path.join(WORKSPACE, d)).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = [
    ("services/payment-processor/src/processor.py",
     "# Payment processor core logic\ndef process(tx): pass\n"),
    ("services/payment-processor/tests/test_processor.py",
     "import pytest\ndef test_noop(): assert True\n"),
    ("services/fraud-detector/src/detector.py",
     "# Fraud detection ML stub\ndef detect(features): return 0.0\n"),
    ("infra/terraform/modules/main.tf",
     'resource "aws_lambda_function" "payment" { function_name = "payment-proc" }\n'),
    ("infra/k8s/manifests/deployment.yaml",
     "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: payment-processor\n"),
    ("infra/k8s/secrets/vault-config.yaml",
     "# Vault secrets config - DO NOT COMMIT\nvault_addr: https://vault.internal\n"),
    ("ops/monitoring/dashboards/latency.json",
     json.dumps({"title": "P99 Latency", "panels": [], "version": 7})),
    ("ops/monitoring/alerts/slo_breach.yaml",
     "alert: SLOBreach\nexpr: rate(errors[5m]) > 0.01\nfor: 5m\n"),
    ("ops/runbooks/incident_response.md",
     "# Incident Response\n## Steps\n1. Page on-call\n2. Check dashboards\n3. Rollback if needed\n"),
    ("data/raw/2024-06/metrics_export.csv",
     "timestamp,service,latency_ms,status\n2024-06-01T00:00:00Z,payment,42,ok\n"),
    ("data/processed/aggregated_june.parquet.stub",
     "PLACEHOLDER - real parquet file goes here\n"),
    ("ci/scripts/build.sh",
     "#!/bin/bash\nset -euo pipefail\ndocker build -t payment-processor:latest .\n"),
    ("logs/archive/2024-05-31.log.gz.stub",
     "PLACEHOLDER - compressed log\n"),
    ("logs/incidents/INC-2024-0087.txt",
     "Incident: Payment timeout spike\nSeverity: P1\nDuration: 47 min\nRCA: DB connection pool exhausted\n"),
    ("services/payment-processor/config/feature_flags.json",
     json.dumps({"enable_3ds": True, "max_retry": 3, "fraud_threshold": 0.85})),
    ("services/fraud-detector/config/model_params.yaml",
     "model: gradient_boost\nthreshold: 0.72\nfeature_version: v3.1\n"),
]
for rel_path, content in distractors:
    fpath = os.path.join(WORKSPACE, rel_path)
    with open(fpath, "w") as f:
        f.write(content)

# ── PROBLEM FILE 1: Messy JSONL traces from the weekend incident ─────────────
# Realistic distributed trace data — some malformed lines, mixed fields
trace_lines = []
services = ["payment-processor", "fraud-detector", "auth-service", "db-proxy", "api-gateway"]
statuses = ["ok", "error", "timeout", "ok", "ok", "ok"]
operations = ["POST /charge", "GET /validate", "POST /auth", "SELECT tx", "CALL fraud-check"]

random.seed(42)
for i in range(120):
    svc = random.choice(services)
    ts = f"2024-06-15T{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}Z"
    trace = {
        "trace_id": f"tr-{random.randint(100000,999999)}",
        "span_id": f"sp-{i:04d}",
        "service": svc,
        "operation": random.choice(operations),
        "duration_ms": random.randint(5, 4800),
        "status": random.choice(statuses),
        "timestamp": ts,
        "tags": {
            "env": "production",
            "version": f"v{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,9)}",
            "region": random.choice(["eu-west-1", "us-east-1"]),
        }
    }
    # Inject some malformed lines (no span_id, extra null fields, etc.)
    if i % 17 == 0:
        trace.pop("span_id")
        trace["malformed_extra"] = None
    if i % 31 == 0:
        trace["duration_ms"] = "NaN"   # bad type
    trace_lines.append(json.dumps(trace))

# Add a completely broken line
trace_lines.insert(55, "NOT_JSON{{broken}}")
# Add an empty line
trace_lines.insert(80, "")

traces_path = os.path.join(WORKSPACE, "data", "raw", "2024-06", "incident_traces.jsonl")
with open(traces_path, "w") as f:
    f.write("\n".join(trace_lines) + "\n")

# ── PROBLEM FILE 2: CI pipeline config with security/test gate issues ────────
# Deliberately missing required security steps and test gates
ci_config = {
    "pipeline_name": "payment-processor-release",
    "version": "2.4.1",
    "stages": [
        {
            "name": "build",
            "steps": [
                {"name": "checkout", "type": "git_checkout", "branch": "main"},
                {"name": "compile", "type": "docker_build", "image": "payment-processor"},
            ]
        },
        {
            "name": "test",
            "steps": [
                {"name": "unit_tests", "type": "test_runner", "framework": "pytest", "coverage_threshold": 75},
                # MISSING: integration tests, security scan
            ]
        },
        {
            "name": "deploy",
            "steps": [
                # MISSING: security gate (SAST/DAST), approval gate
                {"name": "push_image", "type": "registry_push", "registry": "ecr.internal"},
                {"name": "deploy_k8s", "type": "kubectl_apply", "namespace": "production"},
            ]
        }
    ],
    "notifications": {
        "slack_channel": "#payments-releases",
        "on_failure": True,
        "on_success": False
    },
    "metadata": {
        "owner": "payments-team",
        "compliance": "PCI-DSS",
        "last_updated": "2024-06-14"
    }
}

ci_config_path = os.path.join(WORKSPACE, "ci", "configs", "release_pipeline.json")
with open(ci_config_path, "w") as f:
    json.dump(ci_config, f, indent=2)

print(f"[gen_inputs] Workspace prepared at {WORKSPACE}")
print(f"[gen_inputs]   Traces JSONL: {traces_path}")
print(f"[gen_inputs]   CI config:    {ci_config_path}")
print(f"[gen_inputs]   {len(distractors)} distractor files created across {len(dirs)} directories")