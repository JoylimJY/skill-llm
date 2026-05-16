import os
import random

random.seed(42)

base = "/workspace"

# --- Deep distractor directory structure ---
dirs = [
    "logs/archive/2024/jan",
    "logs/archive/2024/feb",
    "logs/archive/2024/mar",
    "logs/current",
    "reports/monthly",
    "reports/weekly",
    "config/nginx",
    "config/firewall",
    "scripts/cron",
    "tmp/staging",
    "tmp/cache",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "logs/archive/2024/jan/access.log.gz.bak": "binary-like garbage\x00\x01\x02",
    "logs/archive/2024/feb/error.log": "Feb error logs - nothing relevant\n",
    "logs/archive/2024/mar/access.log": "Mar access - archived\n",
    "logs/current/debug.log": "DEBUG 2024-06-01 kernel: segfault at 0x00\n",
    "reports/monthly/june_summary.txt": "Placeholder - not generated yet\n",
    "reports/weekly/week22.csv": "date,hits\n2024-06-01,100\n",
    "config/nginx/nginx.conf": "worker_processes auto;\nevents { worker_connections 1024; }\n",
    "config/firewall/rules.txt": "ALLOW 80\nALLOW 443\nDENY ALL\n",
    "scripts/cron/cleanup.sh": "#!/bin/bash\nfind /tmp -mtime +7 -delete\n",
    "tmp/staging/pending.txt": "staging area - empty\n",
    "tmp/cache/hits.tmp": "cache miss\ncache hit\ncache hit\n",
}
for rel_path, content in distractor_files.items():
    full_path = os.path.join(base, rel_path)
    with open(full_path, "w", errors="replace") as f:
        f.write(content)

# --- THE PROBLEM INPUT: a messy server access log ---
# This file contains mixed-format lines. The agent must:
# 1. Load this file into the clipboard
# 2. Read it back from clipboard, filter only lines with HTTP 200 status
# 3. Count unique IPs from those 200 lines
# 4. Write a result: "OK_REQUESTS: <count_of_200_lines>\nUNIQUE_IPS: <count_of_unique_ips>\n"
#    into /workspace/reports/monthly/clipboard_relay_report.txt
#    BUT the relay MUST go through clipboard: the filtered content must be written to clipboard first,
#    then read back from clipboard to produce the final report.

log_lines = []
ips = [
    "192.168.1.10", "10.0.0.5", "172.16.0.3", "192.168.1.10",
    "10.0.0.7", "192.168.1.15", "10.0.0.5", "172.16.0.9",
    "192.168.1.10", "10.0.0.12", "172.16.0.3", "192.168.1.20",
    "10.0.0.5", "172.16.0.3", "192.168.1.25",
]
statuses = [200, 200, 404, 200, 500, 200, 200, 301, 200, 404, 200, 200, 500, 200, 200]
paths = [
    "/index.html", "/api/v1/health", "/missing", "/api/v1/data",
    "/crash", "/static/style.css", "/api/v1/users", "/old-page",
    "/favicon.ico", "/not-here", "/api/v1/metrics", "/dashboard",
    "/error", "/api/v1/config", "/home",
]
random.seed(42)
for i in range(len(ips)):
    ts = f"2024-06-15 12:{i:02d}:00"
    line = f'{ips[i]} - - [{ts}] "GET {paths[i]} HTTP/1.1" {statuses[i]} {random.randint(200,5000)}'
    log_lines.append(line)

# Add some malformed/garbage lines as noise
log_lines.insert(3, "MALFORMED LINE - no ip or status")
log_lines.insert(7, "::1 - - [2024-06-15 12:07:00] INVALID REQUEST")
log_lines.insert(11, "")

log_content = "\n".join(log_lines) + "\n"

log_path = os.path.join(base, "logs/current/access.log")
with open(log_path, "w") as f:
    f.write(log_content)

print("Workspace generated.")
print(f"Log file written to: {log_path}")
print("Log contents:")
print(log_content)

# Pre-compute expected answers for reference (not written to workspace)
ok_lines = [l for l in log_lines if " 200 " in l]
unique_ips = set()
for l in ok_lines:
    parts = l.split()
    if parts:
        unique_ips.add(parts[0])

print(f"\nExpected OK_REQUESTS: {len(ok_lines)}")
print(f"Expected UNIQUE_IPS: {len(unique_ips)}")