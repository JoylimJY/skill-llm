#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=/workspace
HOME_DIR=/home/quant

echo "=== ClawGuard Setup Script ==="

# ── 1. Install claw-guard from the skill directory ────────────────────────────
SKILL_DIR="${SKILL_DIR:-/skill}"

if [ -f "$SKILL_DIR/scripts/install.sh" ]; then
    echo "[setup] Installing claw-guard from $SKILL_DIR..."
    cd "$SKILL_DIR"
    bash scripts/install.sh
    echo "[setup] claw-guard installed."
else
    echo "[setup] WARNING: skill install script not found at $SKILL_DIR/scripts/install.sh"
    echo "[setup] Installing claw-guard stub into ~/.local/bin..."
    mkdir -p "$HOME_DIR/.local/bin"
    cat > "$HOME_DIR/.local/bin/claw-guard" << 'EOF'
#!/usr/bin/env python3
"""claw-guard stub — minimal implementation for environment setup."""
import sys
import os
import json
import argparse

STATE_DIR = os.path.expanduser("~/.openclaw/workspace/tools/claw-guard")
REGISTRATIONS_FILE = os.path.join(STATE_DIR, "registrations.json")
DAEMON_PID_FILE = os.path.join(STATE_DIR, "daemon.pid")

def load_registrations():
    if os.path.exists(REGISTRATIONS_FILE):
        with open(REGISTRATIONS_FILE) as f:
            return json.load(f)
    return {}

def save_registrations(data):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(REGISTRATIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def cmd_daemon(args):
    if args.action == "--start" or (hasattr(args, 'start') and args.start):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(DAEMON_PID_FILE, "w") as f:
            f.write(str(os.getpid()) + "\n")
        print(f"[claw-guard] daemon started (pid {os.getpid()})")
    elif args.action == "--stop" or (hasattr(args, 'stop') and args.stop):
        print("[claw-guard] daemon stopped")
    else:
        print("[claw-guard] daemon running")

def cmd_register(args):
    regs = load_registrations()
    job_id = args.job_id
    regs[job_id] = {
        "job_id": job_id,
        "pid_file": getattr(args, 'pid_file', None),
        "watch_dir": getattr(args, 'watch_dir', None),
        "log_file": getattr(args, 'log_file', None),
        "max_silence": getattr(args, 'max_silence', None),
        "notify": getattr(args, 'notify', None),
        "description": getattr(args, 'description', None),
    }
    save_registrations(regs)
    print(f"[claw-guard] registered job: {job_id}")

def cmd_unregister(args):
    regs = load_registrations()
    job_id = args.job_id
    if job_id in regs:
        del regs[job_id]
        save_registrations(regs)
        print(f"[claw-guard] unregistered job: {job_id}")
    else:
        print(f"[claw-guard] job not found: {job_id}")

def cmd_list(args):
    regs = load_registrations()
    if not regs:
        print("[claw-guard] no registered jobs")
    else:
        for job_id, info in regs.items():
            print(f"  {job_id}: {info}")

def cmd_gateway(args):
    regs = load_registrations()
    sub = args.subcommand
    if sub == "register-restart":
        regs["__gateway_restart__"] = {
            "notify": getattr(args, 'notify', None),
            "active": True,
        }
        save_registrations(regs)
        print("[claw-guard] gateway restart watch registered")
    elif sub == "status":
        print("[claw-guard] gateway status: ok")
    else:
        print(f"[claw-guard] gateway subcommand: {sub}")

def main():
    parser = argparse.ArgumentParser(prog="claw-guard")
    sub = parser.add_subparsers(dest="command")

    # daemon
    p_daemon = sub.add_parser("daemon")
    p_daemon.add_argument("action", nargs="?", default="--start")

    # register
    p_reg = sub.add_parser("register")
    p_reg.add_argument("job_id")
    p_reg.add_argument("--pid-file")
    p_reg.add_argument("--watch-dir")
    p_reg.add_argument("--log-file")
    p_reg.add_argument("--max-silence", type=int)
    p_reg.add_argument("--notify")
    p_reg.add_argument("--description")

    # unregister
    p_unreg = sub.add_parser("unregister")
    p_unreg.add_argument("job_id")

    # list
    p_list = sub.add_parser("list")

    # gateway
    p_gw = sub.add_parser("gateway")
    p_gw.add_argument("subcommand")
    p_gw.add_argument("--notify")
    p_gw.add_argument("--target")

    args = parser.parse_args()

    if args.command == "daemon":
        cmd_daemon(args)
    elif args.command == "register":
        cmd_register(args)
    elif args.command == "unregister":
        cmd_unregister(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "gateway":
        cmd_gateway(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
EOF
    chmod +x "$HOME_DIR/.local/bin/claw-guard"
    echo "[setup] claw-guard stub installed."
fi

# Ensure ~/.local/bin is in PATH for this session
export PATH="$HOME_DIR/.local/bin:$PATH"

# ── 2. Verify claw-guard is available ────────────────────────────────────────
if ! command -v claw-guard &>/dev/null; then
    echo "[setup] ERROR: claw-guard not found in PATH after install"
    exit 1
fi
echo "[setup] claw-guard found: $(which claw-guard)"

# ── 3. Start the claw-guard daemon ───────────────────────────────────────────
if systemctl --user is-active --quiet claw-guard 2>/dev/null; then
    echo "[setup] claw-guard daemon already running via systemd"
elif command -v systemctl &>/dev/null && systemctl --user start claw-guard 2>/dev/null; then
    echo "[setup] claw-guard daemon started via systemd"
else
    echo "[setup] Starting claw-guard daemon directly (no systemd)..."
    claw-guard daemon --start &>/tmp/claw-guard-daemon.log &
    sleep 2
    echo "[setup] claw-guard daemon started (PID $!)"
fi

# ── 4. Spawn three realistic background "job" processes ──────────────────────
sleep 3600 &
GGUF_PID=$!
echo $GGUF_PID > "$WORKSPACE/tmp/pids/gguf_export.pid"
echo "[setup] gguf_export job PID: $GGUF_PID"

sleep 3600 &
PARQUET_PID=$!
echo $PARQUET_PID > "$WORKSPACE/tmp/pids/parquet_dump.pid"
echo "[setup] parquet_dump job PID: $PARQUET_PID"

sleep 3600 &
RISK_PID=$!
echo $RISK_PID > "$WORKSPACE/tmp/pids/risk_matrix.pid"
echo "[setup] risk_matrix job PID: $RISK_PID (will be cancelled/removed by agent)"

# ── 5. Touch log files to simulate recent activity ───────────────────────────
touch "$WORKSPACE/quant_pipeline/logs/parquet_dump.log"
touch "$WORKSPACE/quant_pipeline/logs/risk_matrix.log"

echo "=== Setup complete ==="
echo "PIDs written:"
echo "  gguf_export:   $GGUF_PID"
echo "  parquet_dump:  $PARQUET_PID"
echo "  risk_matrix:   $RISK_PID"
echo ""
echo "Agent workspace: $WORKSPACE"
echo "Runbook: $WORKSPACE/ops/runbooks/overnight_ops_runbook.txt"