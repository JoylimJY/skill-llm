import os
import json
import random
import pathlib

random.seed(42)

workspace = pathlib.Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "cluster/nodes/primary",
    "cluster/nodes/replica",
    "cluster/config/tls",
    "cluster/logs/archived",
    "inference/models/llm",
    "inference/models/embed",
    "inference/routing",
    "ops/monitoring",
    "ops/alerts",
    "ops/scripts",
    "deploy/k8s",
    "deploy/compose",
    "auth/tokens",
    "auth/policies",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "cluster/nodes/primary/node.conf": "[node]\nid=primary-01\nreplicas=3\ntimeout=30\n",
    "cluster/nodes/replica/node.conf": "[node]\nid=replica-01\nparent=primary-01\n",
    "cluster/config/tls/cert.pem": "-----BEGIN CERTIFICATE-----\nMIIFake...\n-----END CERTIFICATE-----\n",
    "cluster/logs/archived/2024-01-10.log": "INFO: cluster started\nINFO: all nodes online\n",
    "inference/models/llm/model_config.json": json.dumps({"model": "llm-7b", "layers": 32, "heads": 16}),
    "inference/models/embed/model_config.json": json.dumps({"model": "embed-v2", "dim": 768}),
    "inference/routing/routes.yaml": "routes:\n  - path: /v1/chat\n    backend: llm\n  - path: /v1/embed\n    backend: embed\n",
    "ops/monitoring/prometheus.yml": "global:\n  scrape_interval: 15s\nscrape_configs:\n  - job_name: gateway\n",
    "ops/alerts/alert_rules.json": json.dumps({"rules": [{"name": "HighLatency", "threshold": 500}]}),
    "ops/scripts/rotate_keys.sh": "#!/bin/bash\necho 'Rotating keys...'\n",
    "deploy/k8s/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: inference-gateway\n",
    "deploy/compose/docker-compose.yml": "version: '3.8'\nservices:\n  gateway:\n    image: openclaw:latest\n    ports:\n      - '7878:7878'\n",
    "auth/tokens/old_token.txt": "tok_DEPRECATED_aabbccdd1122\n",
    "auth/policies/rbac.json": json.dumps({"roles": ["admin", "reader", "agent"]}),
    "cluster/config/tls/ca.pem": "-----BEGIN CERTIFICATE-----\nMIIFakeCA...\n-----END CERTIFICATE-----\n",
}

for rel_path, content in distractor_files.items():
    f = workspace / rel_path
    f.write_text(content)

# --- The PROBLEM: openclaw.json with MISSING gateway.auth ---
# gateway.port is present but gateway.auth is completely absent
openclaw_home = pathlib.Path("/root/.openclaw")
openclaw_home.mkdir(parents=True, exist_ok=True)
(openclaw_home / "logs").mkdir(parents=True, exist_ok=True)

openclaw_config = {
    "version": "1.4.2",
    "gateway": {
        "port": 17878,
        "host": "127.0.0.1",
        "timeout": 60
        # NOTE: gateway.auth is intentionally MISSING
    },
    "agent": {
        "default_model": "llm-7b",
        "max_tokens": 4096
    },
    "telemetry": {
        "enabled": False
    }
}

config_path = openclaw_home / "openclaw.json"
config_path.write_text(json.dumps(openclaw_config, indent=2))

# --- Plant a gateway.log with the EXACT trigger string ---
gateway_log = openclaw_home / "logs" / "gateway.log"
gateway_log.write_text(
    "2024-01-15T10:00:00Z INFO  Gateway started on port 17878\n"
    "2024-01-15T10:01:05Z INFO  Agent session abc123 connected\n"
    "2024-01-15T10:02:11Z WARN  Slow response from model backend (1200ms)\n"
    "2024-01-15T10:03:44Z ERROR Unhandled stop reason: error\n"
    "2024-01-15T10:03:44Z INFO  Session abc123 terminated\n"
    "2024-01-15T10:04:00Z INFO  Waiting for reconnect...\n"
)

# --- Additional distractor config files in workspace ---
(workspace / "ops" / "monitoring" / "gateway_metrics.json").write_text(
    json.dumps({"uptime_hours": 142, "requests_total": 88421, "errors_total": 3})
)
(workspace / "auth" / "tokens" / "service_accounts.json").write_text(
    json.dumps({"accounts": [{"name": "inference-agent-1", "role": "agent"}, {"name": "router", "role": "admin"}]})
)
(workspace / "inference" / "routing" / "gateway_endpoints.json").write_text(
    json.dumps({"endpoints": [{"url": "http://127.0.0.1:17878", "healthy": False, "last_check": "2024-01-15T10:05:00Z"}]})
)

print("Gen inputs complete.")
print(f"openclaw.json written to: {config_path}")
print(f"gateway.log written to: {gateway_log}")
print("gateway.auth is intentionally MISSING from openclaw.json")