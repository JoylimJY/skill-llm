#!/bin/bash
set -e

WORKSPACE="/workspace"

# ─── Write the mock tt binary ───────────────────────────────────────────────────
cat > /usr/local/bin/tt << 'TTEOF'
#!/usr/bin/env python3
"""
Mock 'tt' binary for tutti orchestration testing.
Records every invocation to /workspace/.tutti/tt_invocations.log
"""
import sys, json, os, time
from pathlib import Path

LOG = Path("/workspace/.tutti/tt_invocations.log")
LOG.parent.mkdir(parents=True, exist_ok=True)

args = sys.argv[1:]
with open(LOG, "a") as f:
    f.write(json.dumps({"ts": time.time(), "args": args}) + "\n")

# Produce minimal valid JSON output for any subcommand
result = {"ok": True, "subcommand": args[0] if args else "unknown", "agents": [], "workflows": []}

# Simulate doctor check success
if args and args[0] == "doctor":
    result["checks"] = {"tt": True, "tmux": True, "python3": True, "config": True}

print(json.dumps(result))
sys.exit(0)
TTEOF
chmod +x /usr/local/bin/tt

# ─── Write tutti_openclaw.py ────────────────────────────────────────────────────
cat > /workspace/tutti_openclaw.py << 'PYEOF'
#!/usr/bin/env python3
"""
Mock tutti_openclaw.py wrapper.
Logs every call with full argv to /workspace/.tutti/openclaw_invocations.log
Returns a valid JSON envelope for every action.
"""
import sys, json, os, time, shlex
from pathlib import Path

INVOC_LOG = Path("/workspace/.tutti/openclaw_invocations.log")
INVOC_LOG.parent.mkdir(parents=True, exist_ok=True)

args = sys.argv[1:]

# strip global flags like --tt-bin
clean_args = []
skip_next = False
for i, a in enumerate(args):
    if skip_next:
        skip_next = False
        continue
    if a == "--tt-bin":
        skip_next = True
        continue
    clean_args.append(a)

action = clean_args[0] if clean_args else "unknown"
rest   = clean_args[1:] if len(clean_args) > 1 else []

entry = {
    "ts":     time.time(),
    "action": action,
    "args":   rest,
    "raw":    sys.argv[1:]
}
with open(INVOC_LOG, "a") as f:
    f.write(json.dumps(entry) + "\n")

# ── per-action side-effects ──────────────────────────────────────────────────
state_dir = Path("/workspace/.tutti/state")
state_dir.mkdir(parents=True, exist_ok=True)

if action == "doctor_check":
    data = {"checks": {"tt": True, "tmux": True, "python3": True, "config": True}}

elif action == "launch_team":
    for name in ["variant-caller", "qc-reporter", "annotation-engine"]:
        (state_dir / f"{name}.json").write_text(
            json.dumps({"name": name, "status": "running", "pid": 12345})
        )
    data = {"launched": ["variant-caller", "qc-reporter", "annotation-engine"]}

elif action == "launch_agent":
    name = rest[0] if rest else "unknown"
    (state_dir / f"{name}.json").write_text(
        json.dumps({"name": name, "status": "running", "pid": 12345})
    )
    data = {"launched": name}

elif action == "team_status":
    agents = []
    for f in state_dir.glob("*.json"):
        agents.append(json.loads(f.read_text()))
    data = {"agents": agents}

elif action == "send_prompt":
    agent  = rest[0] if rest else "unknown"
    data   = {"agent": agent, "delivered": True, "output": "Analysis complete."}

elif action == "run_workflow":
    wf_name = rest[0] if rest else "unknown"
    data = {"workflow": wf_name, "steps_run": 3, "status": "ok"}

elif action == "verify_team":
    vpath = Path("/workspace/.tutti/last_verify.json")
    vpath.write_text(json.dumps({"status": "passed", "warnings": []}))
    data = {"status": "passed"}

elif action == "read_verify_status":
    vpath = Path("/workspace/.tutti/last_verify.json")
    if vpath.exists():
        data = json.loads(vpath.read_text())
    else:
        data = {"status": "unknown"}

elif action == "land_agent":
    agent = rest[0] if rest else "unknown"
    data  = {"agent": agent, "landed": True}

elif action == "generate_handoff":
    agent  = rest[0] if rest else "unknown"
    packet = f"/workspace/.tutti/handoffs/{agent}-{int(time.time())}.json"
    Path(packet).parent.mkdir(parents=True, exist_ok=True)
    Path(packet).write_text(json.dumps({"agent": agent, "context": "captured"}))
    data = {"agent": agent, "packet": packet}

elif action == "apply_handoff":
    data = {"applied": True}

elif action == "list_handoffs":
    data = {"handoffs": []}

elif action == "list_workflows":
    data = {"workflows": []}

elif action == "plan_workflow":
    data = {"plan": []}

elif action == "stop_agent":
    data = {"stopped": rest[0] if rest else "unknown"}

elif action == "stop_team":
    data = {"stopped": True}

elif action == "agent_output":
    data = {"output": "mock terminal output"}

elif action == "permissions_check":
    data = {"allowed": True}

else:
    data = {}

envelope = {
    "ok":        True,
    "action":    action,
    "command":   ["tt"] + clean_args,
    "exit_code": 0,
    "data":      data,
    "stdout":    json.dumps(data),
    "stderr":    ""
}
print(json.dumps(envelope, indent=2))
sys.exit(0)
PYEOF
chmod +x /workspace/tutti_openclaw.py

# ─── Ensure .tutti dirs exist ───────────────────────────────────────────────────
mkdir -p /workspace/.tutti/state
mkdir -p /workspace/.tutti/handoffs

# ─── Git init (needed for land_agent) ──────────────────────────────────────────
cd /workspace
git config --global user.email "ci@test.local"
git config --global user.name "CI"
git init -q
git add -A
git commit -q -m "initial"

echo "Setup complete."