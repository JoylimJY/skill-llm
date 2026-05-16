import os
import json
import random
from pathlib import Path
from datetime import datetime, timezone, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── Distractor directory structure ──────────────────────────────────────────
distractor_dirs = [
    workspace / "logs" / "gateway" / "2024-11",
    workspace / "logs" / "gateway" / "2024-12",
    workspace / "config" / "channels",
    workspace / "config" / "network",
    workspace / "data" / "sessions",
    workspace / "data" / "exports",
    workspace / "scripts" / "maintenance",
    workspace / "scripts" / "backup",
    workspace / "tmp" / "cache",
    workspace / "tmp" / "queue",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "logs" / "gateway" / "2024-11" / "gateway.log":
        "2024-11-01 12:00:00 INFO  Gateway started\n2024-11-01 12:01:00 INFO  Listening on :8080\n",
    workspace / "logs" / "gateway" / "2024-12" / "gateway.log":
        "2024-12-01 09:00:00 INFO  Gateway restarted\n2024-12-01 09:00:05 WARN  Pairing queue near capacity\n",
    workspace / "config" / "channels" / "telegram.conf":
        "[telegram]\ntoken=REDACTED\nwebhook=https://example.com/wh\n",
    workspace / "config" / "channels" / "slack.conf":
        "[slack]\napp_id=A0XXXXXXX\nsigning_secret=REDACTED\n",
    workspace / "config" / "network" / "proxy.conf":
        "http_proxy=socks5://127.0.0.1:1080\n",
    workspace / "data" / "sessions" / "session_index.json":
        json.dumps({"version": 2, "sessions": []}),
    workspace / "data" / "exports" / "users_export_2024.csv":
        "id,name,channel\n1001,Alice,telegram\n1002,Bob,slack\n",
    workspace / "scripts" / "maintenance" / "cleanup.sh":
        "#!/bin/bash\nfind /tmp -mtime +7 -delete\n",
    workspace / "scripts" / "backup" / "backup_creds.sh":
        "#!/bin/bash\ntar czf /tmp/creds_backup.tar.gz ~/.openclaw/credentials/\n",
    workspace / "tmp" / "cache" / "channel_meta.json":
        json.dumps({"telegram": {"status": "active"}, "slack": {"status": "active"}}),
    workspace / "tmp" / "queue" / "pending_jobs.json":
        json.dumps({"jobs": []}),
}
for path, content in distractor_files.items():
    path.write_text(content)

# ── skill scripts location (the skill expects this path) ─────────────────────
skill_scripts_dir = workspace / "skills" / "approve-pairing" / "scripts"
skill_scripts_dir.mkdir(parents=True, exist_ok=True)

approve_script = skill_scripts_dir / "approve_pairing.py"
approve_script.write_text(
    r'''#!/usr/bin/env python3
"""approve_pairing.py - approve a pending pairing request by channel + code."""
import sys, json, os
from pathlib import Path

def main():
    if len(sys.argv) < 3:
        print("Usage: approve_pairing.py <channel> <code>", file=sys.stderr)
        sys.exit(1)

    channel = sys.argv[1]
    code    = sys.argv[2]

    creds_dir   = Path.home() / ".openclaw" / "credentials"
    pairing_file = creds_dir / f"{channel}-pairing.json"

    if not pairing_file.exists():
        print(f"ERROR: {pairing_file} not found", file=sys.stderr)
        sys.exit(1)

    data = json.loads(pairing_file.read_text())
    requests = data.get("requests", [])

    matched = next((r for r in requests if r.get("code") == code), None)
    if not matched:
        print(f"ERROR: No pending request with code {code}", file=sys.stderr)
        sys.exit(1)

    sender_id  = matched["id"]
    account_id = matched.get("meta", {}).get("accountId", "") or "default"
    if not account_id or account_id.strip() == "":
        account_id = "default"

    allow_file = creds_dir / f"{channel}-{account_id}-allowFrom.json"

    if allow_file.exists():
        af = json.loads(allow_file.read_text())
        if sender_id not in af.get("allowFrom", []):
            af["allowFrom"].append(sender_id)
    else:
        af = {"version": 1, "allowFrom": [sender_id]}

    allow_file.write_text(json.dumps(af, indent=2))

    data["requests"] = [r for r in requests if r.get("code") != code]
    pairing_file.write_text(json.dumps(data, indent=2))

    print(f"OK: Approved {sender_id} for {channel} (account={account_id})")

if __name__ == "__main__":
    main()
'''
)
approve_script.chmod(0o755)

# ── ~/.openclaw/credentials/ ─────────────────────────────────────────────────
creds_dir = Path.home() / ".openclaw" / "credentials"
creds_dir.mkdir(parents=True, exist_ok=True)

now_iso = datetime.now(timezone.utc).isoformat()

# --- telegram: normal accountId "acc-7821" ---
telegram_pairing = {
    "version": 1,
    "requests": [
        {
            "id": "tg_user_553912",
            "code": "ALPHA77X",
            "createdAt": now_iso,
            "meta": {
                "accountId": "acc-7821",
                "displayName": "Priya Sharma"
            }
        },
        # distractor expired entry
        {
            "id": "tg_user_000001",
            "code": "EXPD0001",
            "createdAt": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
            "meta": {
                "accountId": "acc-7821",
                "displayName": "OldUser"
            }
        }
    ]
}
(creds_dir / "telegram-pairing.json").write_text(json.dumps(telegram_pairing, indent=2))

# --- slack: accountId is empty string (edge case → must map to "default") ---
slack_pairing = {
    "version": 1,
    "requests": [
        {
            "id": "slack_uid_U04NZPQ88",
            "code": "BETA99Z",
            "createdAt": now_iso,
            "meta": {
                "accountId": "",
                "displayName": "Marcus Webb"
            }
        }
    ]
}
(creds_dir / "slack-pairing.json").write_text(json.dumps(slack_pairing, indent=2))

# distractor: a pre-existing allowFrom for a different channel to confuse naive glob
whatsapp_allow = {
    "version": 1,
    "allowFrom": ["wa_user_99887766"]
}
(creds_dir / "whatsapp-default-allowFrom.json").write_text(json.dumps(whatsapp_allow, indent=2))

print("gen_inputs_script: workspace created successfully.")
print(f"  telegram pairing code : ALPHA77X  (accountId=acc-7821)")
print(f"  slack    pairing code : BETA99Z   (accountId='' → default)")