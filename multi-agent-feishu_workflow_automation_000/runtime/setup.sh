#!/usr/bin/env bash
set -euo pipefail

# ── Create the mock `openclaw` CLI ──────────────────────────────────────
# This mock records every invocation to an audit log AND performs
# lightweight validation so the eval script can verify correct usage.

MOCK_BIN="/usr/local/bin/openclaw"
AUDIT_LOG="$HOME/.openclaw/audit.log"
AGENTS_DB="$HOME/.openclaw/agents_db.json"
GATEWAY_STATE="$HOME/.openclaw/gateway_state.json"

# Ensure directory exists
mkdir -p "$HOME/.openclaw"

# Initialise state files
echo "[]"  > "$AGENTS_DB"
echo '{"status":"stopped","restarts":0}' > "$GATEWAY_STATE"
touch "$AUDIT_LOG"

cat > "$MOCK_BIN" << 'OPENCLAW_SCRIPT'
#!/usr/bin/env python3
"""Mock openclaw CLI — records commands and validates structure."""
import sys, json, os, datetime, pathlib, re

HOME        = pathlib.Path.home()
OC_DIR      = HOME / ".openclaw"
AUDIT_LOG   = OC_DIR / "audit.log"
AGENTS_DB   = OC_DIR / "agents_db.json"
GATEWAY_ST  = OC_DIR / "gateway_state.json"
CONFIG_FILE = OC_DIR / "openclaw.json"

def log(entry: dict):
    with AUDIT_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")

def load_json(p):
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

def save_json(p, data):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False))

args = sys.argv[1:]

# ── openclaw agents add <id> --workspace <path> --bind feishu:<acct> --non-interactive
if args[:2] == ["agents", "add"]:
    if len(args) < 3:
        print("ERROR: missing agent_id", file=sys.stderr); sys.exit(1)

    agent_id = args[2]
    rest     = args[3:]

    # Parse flags
    workspace_val = None
    bind_val      = None
    non_interactive = False

    i = 0
    while i < len(rest):
        if rest[i] == "--workspace" and i+1 < len(rest):
            workspace_val = rest[i+1]; i += 2
        elif rest[i] == "--bind" and i+1 < len(rest):
            bind_val = rest[i+1]; i += 2
        elif rest[i] == "--non-interactive":
            non_interactive = True; i += 1
        else:
            i += 1

    errors = []
    if workspace_val is None:
        errors.append("missing --workspace")
    if bind_val is None:
        errors.append("missing --bind")
    elif not re.match(r'^feishu:.+', bind_val):
        errors.append(f"--bind must be 'feishu:<account_id>', got: {bind_val!r}")
    if not non_interactive:
        errors.append("missing --non-interactive flag")

    entry = {
        "ts": datetime.datetime.utcnow().isoformat(),
        "cmd": "agents add",
        "agent_id": agent_id,
        "workspace": workspace_val,
        "bind": bind_val,
        "non_interactive": non_interactive,
        "errors": errors
    }
    log(entry)

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    # Also validate that the account exists in openclaw.json
    cfg = load_json(CONFIG_FILE)
    account_id = bind_val.split(":", 1)[1]
    accounts = cfg.get("channels", {}).get("feishu", {}).get("accounts", {})
    if account_id not in accounts:
        msg = f"WARNING: account '{account_id}' not found in openclaw.json channels.feishu.accounts"
        print(msg)
        entry["config_warning"] = msg
    else:
        acct_data = accounts[account_id]
        if "appId" not in acct_data or "appSecret" not in acct_data:
            msg = f"WARNING: account '{account_id}' is missing appId or appSecret"
            print(msg)

    # Record agent in DB
    db = load_json(AGENTS_DB)
    if not isinstance(db, list):
        db = []
    db.append({"id": agent_id, "workspace": workspace_val, "bind": bind_val})
    save_json(AGENTS_DB, db)

    print(f"Agent '{agent_id}' added successfully.")
    sys.exit(0)

# ── openclaw gateway restart
elif args[:2] == ["gateway", "restart"]:
    st = load_json(GATEWAY_ST)
    st["status"]   = "running"
    st["restarts"] = st.get("restarts", 0) + 1
    st["last_restart"] = datetime.datetime.utcnow().isoformat()
    save_json(GATEWAY_ST, st)
    log({"ts": datetime.datetime.utcnow().isoformat(), "cmd": "gateway restart"})
    print("Gateway restarted successfully.")
    sys.exit(0)

# ── openclaw agents list --bindings
elif args[:2] == ["agents", "list"]:
    db = load_json(AGENTS_DB)
    log({"ts": datetime.datetime.utcnow().isoformat(), "cmd": "agents list", "flags": args[2:]})
    if "--bindings" in args:
        print(f"{'ID':<20} {'WORKSPACE':<35} {'BINDING'}")
        print("-" * 75)
        for a in (db if isinstance(db, list) else []):
            print(f"{a.get('id','?'):<20} {a.get('workspace','?'):<35} {a.get('bind','?')}")
    else:
        for a in (db if isinstance(db, list) else []):
            print(a.get("id", "?"))
    sys.exit(0)

# ── openclaw pairing approve feishu <code>
elif args[:3] == ["pairing", "approve", "feishu"]:
    code = args[3] if len(args) > 3 else "(none)"
    log({"ts": datetime.datetime.utcnow().isoformat(), "cmd": "pairing approve", "code": code})
    print(f"Pairing approved for code: {code}")
    sys.exit(0)

else:
    print(f"Unknown command: {' '.join(args)}", file=sys.stderr)
    log({"ts": datetime.datetime.utcnow().isoformat(), "cmd": "UNKNOWN", "args": args})
    sys.exit(1)
OPENCLAW_SCRIPT

chmod +x "$MOCK_BIN"

echo "Mock openclaw CLI installed at $MOCK_BIN"
echo "Audit log will be written to $AUDIT_LOG"