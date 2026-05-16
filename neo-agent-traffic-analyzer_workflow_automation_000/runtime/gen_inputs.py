import json
import os
import random
from datetime import datetime, timedelta, timezone

random.seed(42)

# Create a deeply nested workspace mimicking a real MLOps project
dirs = [
    "workspace/ops/monitoring/alerts",
    "workspace/ops/monitoring/dashboards",
    "workspace/ops/logs/archive",
    "workspace/ops/logs/raw",
    "workspace/infra/terraform/modules",
    "workspace/infra/k8s/manifests",
    "workspace/agents/configs",
    "workspace/agents/specs",
    "workspace/reports/previous",
    "workspace/scripts/utils",
    "workspace/data/samples",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/ops/monitoring/alerts/cpu_alert.yaml": "threshold: 90\nmetric: cpu_usage\nseverity: critical\n",
    "workspace/ops/monitoring/dashboards/overview.json": json.dumps({"dashboard": "overview", "panels": 12}),
    "workspace/ops/logs/archive/2025-12-01.log": "INFO: system start\nWARN: high memory usage\nERROR: connection timeout\n",
    "workspace/infra/terraform/modules/main.tf": 'resource "aws_instance" "agent_host" {\n  ami = "ami-12345"\n  instance_type = "t3.medium"\n}\n',
    "workspace/infra/k8s/manifests/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: agent-orchestrator\n",
    "workspace/agents/configs/alpha.yaml": "name: agent-alpha\nmodel: gpt-4\nmax_tokens: 2048\ntemperature: 0.7\n",
    "workspace/agents/configs/beta.yaml": "name: agent-beta\nmodel: gpt-4\nmax_tokens: 1024\ntemperature: 0.3\n",
    "workspace/agents/specs/agent_contract.md": "# Agent Contract\nAll agents must respond within 500ms.\nPayloads must not exceed 10KB.\n",
    "workspace/scripts/utils/cleanup.sh": "#!/bin/bash\nrm -rf /tmp/agent_cache/*\necho 'Cache cleared'\n",
    "workspace/data/samples/sample_payload.txt": "SAMPLE_PAYLOAD: {\"task\": \"classify\", \"input\": \"some text data\"}\n",
    "workspace/reports/previous/q4_2025_summary.txt": "Q4 2025 Performance Summary\nTotal messages: 45320\nAvg latency: 67ms\nBottlenecks detected: 3\n",
    "workspace/infra/k8s/manifests/service.yaml": "apiVersion: v1\nkind: Service\nmetadata:\n  name: agent-svc\nspec:\n  port: 8080\n",
    "workspace/ops/logs/archive/2025-12-15.log": "INFO: agent-alpha -> agent-gamma: request sent\nERROR: agent-gamma timeout\nINFO: retry 1/3\n",
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# Generate the main communication log file (messy, realistic, large enough)
agents = [
    "agent-alpha", "agent-beta", "agent-gamma",
    "agent-delta", "agent-epsilon", "agent-zeta"
]

# Deliberately make agent-gamma a bottleneck: high latency, many errors
msg_types = ["request", "response", "broadcast", "heartbeat"]
statuses = ["delivered", "delivered", "delivered", "failed", "timeout"]

messages = []
base_time = datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

msg_id = 1

# Normal traffic between alpha->beta, alpha->delta, beta->epsilon
normal_pairs = [
    ("agent-alpha", "agent-beta"),
    ("agent-alpha", "agent-delta"),
    ("agent-beta", "agent-epsilon"),
    ("agent-delta", "agent-zeta"),
    ("agent-epsilon", "agent-zeta"),
    ("agent-zeta", "agent-alpha"),
]

for i in range(80):
    pair = random.choice(normal_pairs)
    t = base_time + timedelta(seconds=random.randint(0, 3600))
    messages.append({
        "id": f"msg-{msg_id:04d}",
        "from": pair[0],
        "to": pair[1],
        "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": random.choice(msg_types),
        "payload_size": random.randint(256, 4096),
        "latency_ms": random.randint(10, 80),
        "status": random.choice(["delivered", "delivered", "delivered", "failed"])
    })
    msg_id += 1

# Bottleneck traffic: agent-gamma receives tons of messages with high latency
bottleneck_sources = ["agent-alpha", "agent-beta", "agent-delta", "agent-epsilon"]
for i in range(60):
    src = random.choice(bottleneck_sources)
    t = base_time + timedelta(seconds=random.randint(0, 3600))
    # High latency and many failures for gamma
    messages.append({
        "id": f"msg-{msg_id:04d}",
        "from": src,
        "to": "agent-gamma",
        "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": "request",
        "payload_size": random.randint(2048, 8192),
        "latency_ms": random.randint(350, 950),
        "status": random.choice(["timeout", "failed", "failed", "delivered"])
    })
    msg_id += 1

# agent-gamma trying to respond (mostly failing)
for i in range(20):
    dst = random.choice(bottleneck_sources)
    t = base_time + timedelta(seconds=random.randint(0, 3600))
    messages.append({
        "id": f"msg-{msg_id:04d}",
        "from": "agent-gamma",
        "to": dst,
        "timestamp": t.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "type": "response",
        "payload_size": random.randint(512, 2048),
        "latency_ms": random.randint(400, 1200),
        "status": random.choice(["timeout", "failed", "delivered"])
    })
    msg_id += 1

# Shuffle messages to make them non-ordered
random.shuffle(messages)

log_path = "workspace/ops/logs/raw/agent_comms_jan2026.json"
with open(log_path, "w") as f:
    json.dump(messages, f, indent=2)

print(f"Generated {len(messages)} messages in {log_path}")
print("Workspace structure created successfully.")