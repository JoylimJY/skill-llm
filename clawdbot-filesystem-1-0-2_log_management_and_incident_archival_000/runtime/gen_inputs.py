#!/usr/bin/env python3
import os
import random

random.seed(42)

# Create deep directory structure under /workspace/app_logs
base = "/workspace/app_logs"
dirs = [
    base,
    f"{base}/web",
    f"{base}/web/nginx",
    f"{base}/web/apache",
    f"{base}/db",
    f"{base}/db/postgres",
    f"{base}/db/mysql",
    f"{base}/services",
    f"{base}/services/auth",
    f"{base}/services/payment",
    f"{base}/archive_old",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# Archive destination (empty, agent must create and populate)
os.makedirs("/workspace/archive", exist_ok=True)

# Files: (path, content, size_approx)
# We need some .log files with CRITICAL, some without, and distractor files
# CRITICAL-containing .log files (these should be archived):
critical_logs = [
    (f"{base}/web/nginx/access.log", 
     "INFO 2024-01-15 req /api/v1 200\n" * 300 + 
     "CRITICAL 2024-01-15 nginx worker process died\n" +
     "ERROR connection refused\n" * 50),
    (f"{base}/db/postgres/pg_main.log",
     "DEBUG query executed in 12ms\n" * 400 +
     "CRITICAL 2024-01-16 out of disk space on /var/lib/postgresql\n" +
     "ERROR checkpoint failed\n" * 30),
    (f"{base}/services/auth/auth_service.log",
     "INFO token validated\n" * 200 +
     "WARNING rate limit approaching\n" * 100 +
     "CRITICAL 2024-01-17 authentication service crashed: segfault\n" +
     "INFO service restarted\n" * 20),
    (f"{base}/services/payment/payment.log",
     "INFO transaction processed\n" * 500 +
     "CRITICAL 2024-01-18 payment gateway unreachable: timeout after 30s\n" +
     "ERROR failed to process 47 pending transactions\n" * 10),
]

# Non-CRITICAL .log files (should NOT be archived):
non_critical_logs = [
    (f"{base}/web/apache/access.log",
     "INFO 2024-01-15 GET /index.html 200\n" * 150 +
     "WARNING slow response 3200ms\n" * 20),
    (f"{base}/db/mysql/query.log",
     "DEBUG SELECT * FROM users WHERE id=1\n" * 80 +
     "INFO slow query logged: 2100ms\n" * 10),
    (f"{base}/services/auth/debug.log",
     "DEBUG entering jwt decode\n" * 60 +
     "DEBUG exiting jwt decode\n" * 60),
]

# Distractor files (non-.log — should never be archived):
distractor_files = [
    (f"{base}/web/nginx/nginx.conf.bak",
     "worker_processes auto;\nevents { worker_connections 1024; }\n" * 5),
    (f"{base}/db/postgres/pg_stats.json",
     '{"queries": 10234, "connections": 47, "cache_hits": 0.97}\n'),
    (f"{base}/services/payment/CRITICAL_notes.txt",
     "CRITICAL: remember to rotate API keys monthly\nThis is a note file, not a log.\n" * 10),
    (f"{base}/archive_old/old_system.log.gz",
     "this is old gzip-named content CRITICAL fake\n" * 20),
    (f"{base}/db/mysql/schema.sql",
     "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(255));\n" * 5),
    (f"{base}/services/auth/config.json",
     '{"jwt_secret": "REDACTED", "token_ttl": 3600}\n'),
    (f"{base}/web/nginx/error.tmp",
     "CRITICAL tmp error placeholder\n" * 5),
    (f"{base}/services/payment/README",
     "Payment service documentation.\nCRITICAL issues should be escalated.\n"),
]

all_files = critical_logs + non_critical_logs + distractor_files

for fpath, content in all_files:
    with open(fpath, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
for fpath, content in all_files:
    size = os.path.getsize(fpath)
    print(f"  {fpath}: {size} bytes")