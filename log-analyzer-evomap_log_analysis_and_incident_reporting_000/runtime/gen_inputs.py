import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Deeply nested distractor directory structure ──────────────────────────────
dirs = [
    "services/auth/logs",
    "services/auth/config",
    "services/payment/logs",
    "services/payment/config",
    "services/notification/logs",
    "infra/k8s/manifests",
    "infra/terraform/modules",
    "monitoring/grafana/dashboards",
    "monitoring/alertmanager",
    "ci/pipelines",
    "docs/runbooks",
    "scripts/maintenance",
    "archive/2023/Q4",
    "archive/2024/Q1",
    "tmp/uploads",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files (irrelevant content)
distractors = {
    "services/auth/config/app.yaml": "port: 8080\ndb_host: localhost\ndb_port: 5432\n",
    "services/payment/config/stripe.json": '{"webhook_secret": "whsec_test_xxx", "mode": "sandbox"}',
    "infra/k8s/manifests/deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: api-server\n",
    "infra/terraform/modules/vpc.tf": 'resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"\n}\n',
    "monitoring/grafana/dashboards/overview.json": '{"title": "Overview", "panels": []}',
    "monitoring/alertmanager/config.yml": "global:\n  resolve_timeout: 5m\nroute:\n  receiver: slack\n",
    "ci/pipelines/build.yml": "stages:\n  - build\n  - test\n  - deploy\n",
    "docs/runbooks/incident-response.md": "# Incident Response\n1. Page on-call\n2. Assess impact\n3. Mitigate\n",
    "scripts/maintenance/cleanup.sh": "#!/bin/bash\nfind /tmp -mtime +7 -delete\n",
    "archive/2023/Q4/metrics_summary.csv": "date,error_rate,p99_latency\n2023-10-01,0.02,240\n2023-11-01,0.05,310\n",
    "archive/2024/Q1/capacity_plan.txt": "Projected growth: 30% QoQ\nRequired nodes: 12\n",
    "tmp/uploads/.gitkeep": "",
}
for path, content in distractors.items():
    (workspace / path).write_text(content)

# ── Realistic distractor log files (normal operational logs, NOT crash logs) ─
normal_log = """2024-05-10T08:00:01Z INFO  [api-server] Server started on port 3000
2024-05-10T08:00:05Z INFO  [api-server] Connected to database pool (size=10)
2024-05-10T08:01:22Z INFO  [api-server] GET /health 200 4ms
2024-05-10T08:01:45Z INFO  [api-server] POST /api/v1/users 201 32ms
2024-05-10T08:02:10Z INFO  [api-server] GET /api/v1/products 200 18ms
2024-05-10T08:15:00Z INFO  [worker] Job queue flushed successfully
"""
(workspace / "services/auth/logs/access.log").write_text(normal_log)
(workspace / "services/payment/logs/access.log").write_text(normal_log.replace("api-server", "payment-svc"))
(workspace / "services/notification/logs/worker.log").write_text(
    "2024-05-10T09:00:00Z INFO  [notifier] Email sent to user@example.com\n" * 20
)

# ── The primary crash log the agent must analyze ──────────────────────────────
# A realistic messy multi-error log mixing JS, Python, and go-style errors
crash_log = """\
=== CRASH REPORT: api-gateway v2.3.1 ===
Generated: 2024-06-15T03:47:22.391Z
Environment: production | region: us-east-1
Hostname: prod-api-gw-07

--- INCIDENT #1 ---
2024-06-15T03:45:01.112Z ERROR [upstream-proxy] Failed to reach payment service
Error: connect ECONNREFUSED 10.0.0.45:8080
    at TCPConnectWrap.afterConnect [as oncomplete] (node:net:1494:16)
    at Object.createConnection (node:net:1559:15)
    at PaymentClient.connect (/app/src/clients/payment.js:87:22)
    at processTicksAndRejections (node:internal/process/task_queues:95:5)

--- INCIDENT #2 ---
2024-06-15T03:45:18.774Z ERROR [file-service] Cannot open upload temp file
Error: ENOENT: no such file or directory, open '/var/uploads/tmp/req-a8f3b.bin'
    at Object.openSync (node:fs:585:3)
    at FileService.createTempFile (/app/src/services/file.js:34:18)
    at MultipartParser.onField (/app/src/middleware/upload.js:112:9)

--- INCIDENT #3 ---
2024-06-15T03:46:05.220Z CRITICAL [session-store] Redis write rejected
Error: EACCES: permission denied, open '/var/run/redis/redis.sock'
    at Object.openSync (node:fs:585:3)
    at RedisUnixClient.connect (/app/src/cache/redis-unix.js:29:14)
    at SessionStore.init (/app/src/session/store.js:55:22)

--- INCIDENT #4 ---
2024-06-15T03:46:44.881Z FATAL [worker-pool] Node.js worker thread crashed
FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory
 1: 0xb7c860 node::Abort() [node]
 2: 0xa91a20 node::FatalError(char const*, char const*) [node]
 3: 0xd9ca7e v8::Utils::ReportOOMFailure(v8::internal::Isolate*, char const*, bool) [node]
 4: 0xd9cdf7 v8::internal::V8::FatalProcessOutOfMemory(v8::internal::Isolate*, char const*, bool) [node]
Aborted (core dumped)

--- INCIDENT #5 ---
2024-06-15T03:47:10.055Z ERROR [external-api] Third-party KYC check stalled
Error: ETIMEDOUT - Request to https://api.kyc-provider.io/verify timed out after 30000ms
    at ClientRequest.emit (node:events:526:35)
    at TLSSocket.socketErrorListener (node:_http_client:495:9)
    at KYCClient.verify (/app/src/integrations/kyc.js:203:17)

--- INCIDENT #6 ---
Traceback (most recent call last):
  File "/app/scripts/report_gen.py", line 88, in generate_daily_report
    conn = psycopg2.connect(dsn=DATABASE_URL, connect_timeout=5)
  File "/usr/local/lib/python3.10/dist-packages/psycopg2/__init__.py", line 122, in connect
    conn = _connect(dsn, connection_factory=connection_factory, **kwasync)
psycopg2.OperationalError: could not connect to server: Connection refused
        Is the server running on host "10.0.0.12" and accepting
        TCP/IP connections on port 5432?

=== END OF CRASH REPORT ===
"""
(workspace / "tmp/uploads/crash_report_2024-06-15.log").write_text(crash_log)

# ── evolver-memory logs (for analyzeEvolverLogs test) ─────────────────────────
evolver_dir = Path.home() / "evolver-memory"
evolver_dir.mkdir(parents=True, exist_ok=True)

evolver_log_1 = """\
[2024-06-01T12:00:00Z] ERROR capsule:data-fetcher - FetchError: fetch failed
    at Object.fetch (/home/user/.evomap/capsules/data-fetcher/index.js:45:11)
    network connection dropped during large dataset pull
[2024-06-01T12:01:30Z] ERROR capsule:data-fetcher - FetchError: fetch failed
[2024-06-02T09:15:00Z] ERROR capsule:data-fetcher - ECONNREFUSED 127.0.0.1:9200
"""
(evolver_dir / "capsule-errors.log").write_text(evolver_log_1)

evolver_log_2 = """\
[2024-06-10T08:00:00Z] WARN  capsule:code-indexer - ENOENT: no such file or directory '/tmp/index_cache.db'
[2024-06-10T08:00:01Z] INFO  capsule:code-indexer - Rebuilding index from scratch
[2024-06-11T14:22:00Z] ERROR capsule:code-indexer - heap out of memory during full repo scan
    process killed by OOM killer (rss: 4.1GB)
"""
(evolver_dir / "indexer-errors.log").write_text(evolver_log_2)

evolver_log_3 = """\
[2024-06-12T17:00:00Z] ERROR capsule:summarizer - timeout: deadline exceeded (15000ms)
    at SummarizerClient.call (/home/user/.evomap/capsules/summarizer/index.js:88:9)
[2024-06-12T17:00:30Z] ERROR capsule:summarizer - timeout: deadline exceeded (15000ms)
"""
(evolver_dir / "summarizer-errors.log").write_text(evolver_log_3)

print("Workspace generation complete.")
print(f"Primary crash log: {workspace}/tmp/uploads/crash_report_2024-06-15.log")
print(f"Evolver memory logs: {evolver_dir}/")