#!/bin/bash
set -e

# ── Create the mock openclaw binary ───────────────────────────────────────────
cat > /usr/local/bin/openclaw << 'MOCK_SCRIPT'
#!/usr/bin/env python3
import sys
import json
import os
import re
from datetime import datetime

LOG_FILE = "/root/.openclaw/command_log.txt"
CONFIG_FILE = "/root/.openclaw/openclaw.json"

def log_command(args):
    with open(LOG_FILE, "a") as f:
        f.write(" ".join(args) + "\n")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def main():
    args = sys.argv[1:]
    log_command(["openclaw"] + args)

    if not args:
        print("Usage: openclaw <command> [options]")
        sys.exit(1)

    cmd = args[0]

    # ── openclaw agents add ──────────────────────────────────────────────────
    if cmd == "agents" and len(args) > 1 and args[1] == "add":
        agent_id = args[2] if len(args) > 2 else None
        workspace = None
        model = None
        non_interactive = False
        i = 3
        while i < len(args):
            if args[i] == "--workspace" and i+1 < len(args):
                workspace = args[i+1]; i += 2
            elif args[i] == "--model" and i+1 < len(args):
                model = args[i+1]; i += 2
            elif args[i] == "--non-interactive":
                non_interactive = True; i += 1
            else:
                i += 1
        config = load_config()
        if "agents" not in config:
            config["agents"] = {}
        config["agents"][agent_id] = {
            "workspace": workspace,
            "model": model,
            "createdAt": datetime.utcnow().isoformat() + "Z"
        }
        save_config(config)
        print(f"✅ Agent '{agent_id}' created successfully")
        print(f"   Workspace: {workspace}")
        print(f"   Model: {model}")

    # ── openclaw agents list ─────────────────────────────────────────────────
    elif cmd == "agents" and len(args) > 1 and args[1] == "list":
        config = load_config()
        agents = config.get("agents", {})
        print("Registered Agents:")
        for aid, info in agents.items():
            print(f"  - {aid} | model: {info.get('model','?')} | workspace: {info.get('workspace','?')}")

    # ── openclaw agents bind ─────────────────────────────────────────────────
    elif cmd == "agents" and len(args) > 1 and args[1] == "bind":
        agent = None
        bind = None
        i = 2
        while i < len(args):
            if args[i] == "--agent" and i+1 < len(args):
                agent = args[i+1]; i += 2
            elif args[i] == "--bind" and i+1 < len(args):
                bind = args[i+1]; i += 2
            else:
                i += 1
        config = load_config()
        if "bindings" not in config:
            config["bindings"] = []
        binding_str = f"{bind} -> {agent}"
        if binding_str not in config["bindings"]:
            config["bindings"].append(binding_str)
        save_config(config)
        print(f"✅ Route bound: {bind} → {agent}")

    # ── openclaw channels add ────────────────────────────────────────────────
    elif cmd == "channels" and len(args) > 1 and args[1] == "add":
        channel = None
        account = None
        name = None
        i = 2
        while i < len(args):
            if args[i] == "--channel" and i+1 < len(args):
                channel = args[i+1]; i += 2
            elif args[i] == "--account" and i+1 < len(args):
                account = args[i+1]; i += 2
            elif args[i] == "--name" and i+1 < len(args):
                name = args[i+1]; i += 2
            else:
                i += 1
        config = load_config()
        if "channels" not in config:
            config["channels"] = {}
        if channel not in config["channels"]:
            config["channels"][channel] = {"accounts": {}}
        if "accounts" not in config["channels"][channel]:
            config["channels"][channel]["accounts"] = {}
        if account not in config["channels"][channel]["accounts"]:
            config["channels"][channel]["accounts"][account] = {}
        config["channels"][channel]["accounts"][account]["displayName"] = name
        save_config(config)
        print(f"✅ Channel account added: {channel}/{account} ('{name}')")

    # ── openclaw config set ──────────────────────────────────────────────────
    elif cmd == "config" and len(args) > 1 and args[1] == "set":
        key_path = args[2] if len(args) > 2 else None
        value = args[3] if len(args) > 3 else None
        config = load_config()
        # Navigate dot-path and set value
        parts = key_path.split(".")
        ref = config
        for p in parts[:-1]:
            if p not in ref:
                ref[p] = {}
            ref = ref[p]
        ref[parts[-1]] = value
        save_config(config)
        print(f"✅ Config set: {key_path} = {value}")

    # ── openclaw config get ──────────────────────────────────────────────────
    elif cmd == "config" and len(args) > 1 and args[1] == "get":
        key_path = args[2] if len(args) > 2 else None
        config = load_config()
        if key_path:
            parts = key_path.split(".")
            ref = config
            for p in parts:
                if isinstance(ref, dict) and p in ref:
                    ref = ref[p]
                else:
                    ref = None
                    break
            print(json.dumps(ref, indent=2, ensure_ascii=False))
        else:
            print(json.dumps(config, indent=2, ensure_ascii=False))

    # ── openclaw gateway restart ─────────────────────────────────────────────
    elif cmd == "gateway" and len(args) > 1 and args[1] == "restart":
        print("🔄 Gateway restarting...")
        print("✅ Gateway restarted successfully on port 8080")

    # ── openclaw gateway status ──────────────────────────────────────────────
    elif cmd == "gateway" and len(args) > 1 and args[1] == "status":
        print("✅ Gateway running on port 8080")

    # ── openclaw gateway logs ────────────────────────────────────────────────
    elif cmd == "gateway" and len(args) > 1 and args[1] == "logs":
        print("[INFO] No errors in gateway logs.")

    else:
        print(f"Unknown command: {' '.join(args)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
MOCK_SCRIPT

chmod +x /usr/local/bin/openclaw

# Verify mock is accessible
openclaw gateway status

# Ensure log file exists
touch /root/.openclaw/command_log.txt

echo "Mock openclaw CLI installed and verified."
echo "Config directory contents:"
ls -la /root/.openclaw/