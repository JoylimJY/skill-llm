#!/bin/bash
set -e

# ─────────────────────────────────────────────────────────────
# Mock `am` CLI binary
# ─────────────────────────────────────────────────────────────
cat > /usr/local/bin/am << 'PYEOF'
#!/usr/bin/env python3
"""
Mock `am` CLI — deterministic simulation for evaluation purposes.
State is stored in XDG_CONFIG_HOME/am/ and XDG_DATA_HOME/am/
"""
import sys
import os
import json
import time
import hashlib
import toml
from pathlib import Path

XDG_CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
XDG_DATA   = Path(os.environ.get("XDG_DATA_HOME",   Path.home() / ".local/share"))

CONFIG_DIR     = XDG_CONFIG / "am"
IDENTITIES_DIR = XDG_DATA   / "am" / "identities"
SEND_LOG       = XDG_DATA   / "am" / "send_log.jsonl"
CONFIG_FILE    = CONFIG_DIR  / "config.toml"

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
IDENTITIES_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    if CONFIG_FILE.exists():
        return toml.loads(CONFIG_FILE.read_text())
    return {"default_identity": "default", "format": "json", "relays": []}

def save_config(cfg):
    CONFIG_FILE.write_text(toml.dumps(cfg))

def deterministic_npub(name: str) -> str:
    h = hashlib.sha256(f"mock-identity-{name}".encode()).hexdigest()[:40]
    return f"npub1{h}"

def deterministic_event_id(payload: str) -> str:
    return hashlib.sha256(f"event-{payload}-{time.time_ns()}".encode()).hexdigest()

def err(msg, code=1):
    print(json.dumps({"error": msg}), file=sys.stderr)
    sys.exit(code)

args = sys.argv[1:]
if not args:
    print("Usage: am <command> [options]")
    sys.exit(2)

# ── version ──────────────────────────────────────────────────
if args[0] == "--version":
    print("am 0.1.0-mock")
    sys.exit(0)

# ── identity ─────────────────────────────────────────────────
if args[0] == "identity":
    if len(args) < 2:
        err("subcommand required", 2)

    sub = args[1]

    if sub == "generate":
        # --name <name>
        if "--name" not in args:
            err("--name required", 2)
        name = args[args.index("--name") + 1]
        nsec_file = IDENTITIES_DIR / f"{name}.nsec"
        npub = deterministic_npub(name)
        nsec_file.write_text(json.dumps({"name": name, "npub": npub, "nsec": f"nsec1mock{name}"}))
        nsec_file.chmod(0o600)
        cfg = load_config()
        if "identities" not in cfg:
            cfg["identities"] = []
        if name not in cfg["identities"]:
            cfg["identities"].append(name)
        if "default_identity" not in cfg:
            cfg["default_identity"] = name
        save_config(cfg)
        print(json.dumps({"name": name, "npub": npub}))
        sys.exit(0)

    if sub == "show":
        cfg = load_config()
        default_id = cfg.get("default_identity", "default")
        nsec_file = IDENTITIES_DIR / f"{default_id}.nsec"
        if not nsec_file.exists():
            err(f"identity '{default_id}' not found", 4)
        data = json.loads(nsec_file.read_text())
        print(json.dumps({"name": data["name"], "npub": data["npub"]}))
        sys.exit(0)

    if sub == "list":
        cfg = load_config()
        identities = cfg.get("identities", [])
        result = []
        for iname in identities:
            f = IDENTITIES_DIR / f"{iname}.nsec"
            if f.exists():
                d = json.loads(f.read_text())
                result.append({"name": d["name"], "npub": d["npub"]})
        print(json.dumps(result))
        sys.exit(0)

    err(f"unknown identity subcommand: {sub}", 2)

# ── relay ─────────────────────────────────────────────────────
if args[0] == "relay":
    if len(args) < 2:
        err("subcommand required", 2)
    sub = args[1]

    if sub == "add":
        if len(args) < 3:
            err("relay URL required", 2)
        url = args[2]
        cfg = load_config()
        if "relays" not in cfg:
            cfg["relays"] = []
        if url not in cfg["relays"]:
            cfg["relays"].append(url)
        save_config(cfg)
        print(json.dumps({"added": url}))
        sys.exit(0)

    if sub == "list":
        cfg = load_config()
        relays = cfg.get("relays", [])
        print(json.dumps(relays))
        sys.exit(0)

    err(f"unknown relay subcommand: {sub}", 2)

# ── config ────────────────────────────────────────────────────
if args[0] == "config":
    if len(args) < 2:
        err("subcommand required", 2)
    sub = args[1]

    if sub == "show":
        cfg = load_config()
        print(json.dumps(cfg))
        sys.exit(0)

    if sub == "set":
        if len(args) < 4:
            err("usage: am config set <key> <value>", 2)
        key, value = args[2], args[3]
        cfg = load_config()
        cfg[key] = value
        save_config(cfg)
        print(json.dumps({"set": {key: value}}))
        sys.exit(0)

    err(f"unknown config subcommand: {sub}", 2)

# ── send ──────────────────────────────────────────────────────
if args[0] == "send":
    to_npub = None
    identity_name = None
    msg_content = None

    i = 1
    while i < len(args):
        if args[i] == "--to" and i + 1 < len(args):
            to_npub = args[i+1]; i += 2
        elif args[i] == "--identity" and i + 1 < len(args):
            identity_name = args[i+1]; i += 2
        elif args[i] == "--format" and i + 1 < len(args):
            i += 2  # consume but ignore for mock
        else:
            msg_content = args[i]; i += 1

    if not to_npub:
        err("--to required", 2)

    # Read from stdin if no inline message
    if msg_content is None:
        if not sys.stdin.isatty():
            msg_content = sys.stdin.read().strip()
        else:
            err("message content required (inline or stdin)", 2)

    cfg = load_config()
    if identity_name is None:
        identity_name = cfg.get("default_identity", "default")

    nsec_file = IDENTITIES_DIR / f"{identity_name}.nsec"
    if not nsec_file.exists():
        err(f"identity '{identity_name}' not found", 4)

    id_data = json.loads(nsec_file.read_text())
    event_id = deterministic_event_id(msg_content)

    record = {
        "from_identity": identity_name,
        "from_npub": id_data["npub"],
        "to": to_npub,
        "content": msg_content,
        "event_id": event_id,
        "sent_at": int(time.time())
    }

    SEND_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(SEND_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")

    print(json.dumps({"to": to_npub, "event_id": event_id}))
    sys.exit(0)

# ── listen ────────────────────────────────────────────────────
if args[0] == "listen":
    once   = "--once"  in args
    limit  = None
    since  = None

    if "--limit" in args:
        limit = int(args[args.index("--limit") + 1])
    if "--since" in args:
        since = int(args[args.index("--since") + 1])

    # Pre-seeded deterministic inbox (10 messages)
    INBOX = [
        {"from": "npub1sender_aaa000000000000000000000000000000000000000000000000001",
         "content": json.dumps({"task_id": f"t-{8990+k}", "status": "completed", "result": f"pattern_{k}_found"}),
         "created_at": 1700000000 + k * 60,
         "event_id": hashlib.sha256(f"inbox-event-{k}".encode()).hexdigest()}
        for k in range(10)
    ]

    # Apply --since filter
    if since is not None:
        INBOX = [m for m in INBOX if m["created_at"] >= since]

    # Apply --limit (take LAST N messages, simulating newest-first then reversed)
    if limit is not None:
        INBOX = INBOX[-limit:]

    if once:
        for msg in INBOX:
            print(json.dumps(msg))
        sys.exit(0)
    else:
        # Streaming mode: print all then block (for mock purposes, just print and exit)
        for msg in INBOX:
            print(json.dumps(msg))
        sys.exit(0)

err(f"unknown command: {args[0]}", 2)
PYEOF

chmod +x /usr/local/bin/am

# Verify mock works
am --version

echo "Mock am CLI installed successfully."