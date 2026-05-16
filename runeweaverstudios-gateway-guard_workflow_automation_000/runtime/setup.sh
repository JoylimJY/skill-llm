#!/bin/bash
set -e

OPENCLAW_HOME="${OPENCLAW_HOME:-/root/.openclaw}"
mkdir -p "$OPENCLAW_HOME/logs"
mkdir -p /workspace/scripts

# -------------------------------------------------------------------------
# 1. Create the mock `openclaw` CLI
#    Logs all invocations and simulates the real CLI's side effects
# -------------------------------------------------------------------------
cat > /usr/local/bin/openclaw << 'OPENCLAW_CLI'
#!/bin/bash
set -e

OPENCLAW_HOME="${OPENCLAW_HOME:-/root/.openclaw}"
LOG_FILE="$OPENCLAW_HOME/logs/mock_openclaw_calls.log"
mkdir -p "$OPENCLAW_HOME/logs"

# Log every invocation
echo "$(date -Iseconds) CALL: openclaw $*" >> "$LOG_FILE"

case "$1" in
  "gateway")
    shift
    if [ "$1" = "stop" ]; then
      echo "$(date -Iseconds) EFFECT: gateway stopped" >> "$LOG_FILE"
      # Remove any running-state sentinel
      rm -f "$OPENCLAW_HOME/logs/gateway.running"
      echo "Gateway stopped."
      exit 0
    fi
    # gateway --port N --auth token --token SECRET
    # Parse args
    PORT=""
    AUTH_MODE=""
    SECRET=""
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --port) PORT="$2"; shift 2;;
        --auth) AUTH_MODE="$2"; shift 2;;
        --token) SECRET="$2"; shift 2;;
        --password) SECRET="$2"; shift 2;;
        *) shift;;
      esac
    done
    echo "$(date -Iseconds) EFFECT: gateway started port=$PORT auth=$AUTH_MODE secret=$SECRET" >> "$LOG_FILE"
    # Write a running-state file so lsof mock can report the port as open
    echo "$PORT $AUTH_MODE $SECRET" > "$OPENCLAW_HOME/logs/gateway.running"
    # Start a tiny background TCP listener on the specified port (nc)
    # so --wait actually sees the port open
    if [ -n "$PORT" ]; then
      # Kill any previous listener on this port
      pkill -f "nc -l.*$PORT" 2>/dev/null || true
      sleep 0.2
      # Background nc listener; will accept one connection then exit, but that's enough for --wait
      (while true; do nc -l -p "$PORT" 2>/dev/null; done) &
      NC_PID=$!
      echo "$NC_PID" > "$OPENCLAW_HOME/logs/gateway_nc.pid"
      echo "$(date -Iseconds) EFFECT: nc listener started on $PORT pid=$NC_PID" >> "$LOG_FILE"
    fi
    echo "Gateway started on port $PORT with $AUTH_MODE auth."
    exit 0
    ;;

  "agent")
    shift
    # agent --message continue --deliver
    MSG=""
    DELIVER=false
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --message) MSG="$2"; shift 2;;
        --deliver) DELIVER=true; shift;;
        *) shift;;
      esac
    done
    echo "$(date -Iseconds) EFFECT: agent message='$MSG' deliver=$DELIVER" >> "$LOG_FILE"
    if [ "$DELIVER" = "true" ] && [ "$MSG" = "continue" ]; then
      echo "$(date -Iseconds) DELIVERED: continue message sent to agent" >> "$LOG_FILE"
      echo "continue" > "$OPENCLAW_HOME/logs/continue_delivered.flag"
    fi
    echo "Message delivered: $MSG"
    exit 0
    ;;

  *)
    echo "Unknown openclaw command: $1" >&2
    exit 1
    ;;
esac
OPENCLAW_CLI

chmod +x /usr/local/bin/openclaw

# -------------------------------------------------------------------------
# 2. Create gateway_guard.py — the real, complete implementation
#    following the SKILL.md spec exactly
# -------------------------------------------------------------------------
cat > /workspace/scripts/gateway_guard.py << 'GATEWAY_GUARD_PY'
#!/usr/bin/env python3
"""
Gateway Guard — Ensures OpenClaw gateway auth consistency.
Follows the SKILL.md specification exactly.
"""

import argparse
import json
import os
import pathlib
import secrets
import socket
import subprocess
import sys
import time

OPENCLAW_HOME = pathlib.Path(os.environ.get("OPENCLAW_HOME", pathlib.Path.home() / ".openclaw"))
OPENCLAW_BIN  = os.environ.get("OPENCLAW_BIN", "openclaw")
CONFIG_PATH   = OPENCLAW_HOME / "openclaw.json"
GATEWAY_LOG   = OPENCLAW_HOME / "logs" / "gateway.log"
CONTINUE_STATE= OPENCLAW_HOME / "logs" / "gateway-guard.continue-state.json"
TRIGGER_STR   = "Unhandled stop reason: error"
COOLDOWN_SECS = 90


# ── helpers ──────────────────────────────────────────────────────────────────

def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"openclaw.json not found at {CONFIG_PATH}")
    with CONFIG_PATH.open() as f:
        return json.load(f)


def save_config(cfg):
    with CONFIG_PATH.open("w") as f:
        json.dump(cfg, f, indent=2)


def get_gateway_port(cfg):
    return cfg.get("gateway", {}).get("port")


def get_gateway_auth(cfg):
    """Return (mode, secret) or (None, None) if missing."""
    auth = cfg.get("gateway", {}).get("auth")
    if not auth:
        return None, None
    mode = auth.get("mode")
    secret = auth.get("token") if mode == "token" else auth.get("password")
    return mode, secret


def is_port_open(host, port, timeout=1.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def wait_for_port(host, port, timeout_secs=30):
    deadline = time.time() + timeout_secs
    while time.time() < deadline:
        if is_port_open(host, port):
            return True
        time.sleep(0.5)
    return False


def gateway_running_state():
    """
    Check if gateway is running on configured port.
    Returns (running: bool, pid: int|None).
    We check the running sentinel written by the mock CLI.
    """
    running_file = OPENCLAW_HOME / "logs" / "gateway.running"
    if running_file.exists():
        return True, None  # pid not tracked in mock
    return False, None


def secret_matches_config(cfg):
    """
    Compare the config's auth secret against what is running.
    In the real implementation this would compare against the live process;
    in our mock we compare against the running sentinel file.
    Returns (matches: bool, reason: str)
    """
    mode, secret = get_gateway_auth(cfg)
    if mode is None or secret is None:
        return False, "gateway.auth missing in config"

    running_file = OPENCLAW_HOME / "logs" / "gateway.running"
    if not running_file.exists():
        return False, "gateway not running"

    content = running_file.read_text().strip().split()
    if len(content) < 3:
        return False, "cannot read running gateway state"

    running_port, running_mode, running_secret = content[0], content[1], content[2]
    port = get_gateway_port(cfg)

    if str(running_port) != str(port):
        return False, f"port mismatch: config={port} running={running_port}"
    if running_mode != mode:
        return False, f"auth mode mismatch: config={mode} running={running_mode}"
    if running_secret != secret:
        return False, "secret does not match config (device_token_mismatch)"
    return True, "ok"


def ensure_auth_in_config(cfg):
    """
    If gateway.auth is missing or mode/secret is absent, generate and write.
    Only writes when missing/wrong; never overwrites correct config.
    Returns (cfg, was_written: bool, token: str)
    """
    auth = cfg.get("gateway", {})
    existing_auth = auth.get("auth")
    if existing_auth and existing_auth.get("mode") and (
        existing_auth.get("token") or existing_auth.get("password")
    ):
        return cfg, False, existing_auth.get("token") or existing_auth.get("password")
    # Generate token (token mode default)
    new_token = "tok_" + secrets.token_hex(16)
    if "gateway" not in cfg:
        cfg["gateway"] = {}
    cfg["gateway"]["auth"] = {"mode": "token", "token": new_token}
    save_config(cfg)
    return cfg, True, new_token


def restart_gateway(cfg):
    port = get_gateway_port(cfg)
    mode, secret = get_gateway_auth(cfg)
    host = cfg.get("gateway", {}).get("host", "127.0.0.1")
    # Stop
    subprocess.run([OPENCLAW_BIN, "gateway", "stop"], check=False,
                   capture_output=True)
    time.sleep(0.3)
    # Start
    flag = "--token" if mode == "token" else "--password"
    subprocess.run(
        [OPENCLAW_BIN, "gateway", f"--port", str(port),
         "--auth", mode, flag, secret],
        check=True, capture_output=True
    )
    return host, port


# ── subcommands ──────────────────────────────────────────────────────────────

def cmd_status(args):
    result = {
        "ok": False,
        "secretMatchesConfig": False,
        "running": False,
        "pid": None,
        "reason": "",
        "recommendedAction": "",
        "configPath": str(CONFIG_PATH),
        "authMode": None,
        "gatewayPort": None,
    }
    try:
        cfg = load_config()
        port = get_gateway_port(cfg)
        mode, secret = get_gateway_auth(cfg)
        result["authMode"] = mode
        result["gatewayPort"] = port

        running, pid = gateway_running_state()
        result["running"] = running
        result["pid"] = pid

        if not running:
            result["reason"] = "gateway not running"
            result["recommendedAction"] = "run gateway_guard.py ensure --apply and restart client session"
        elif mode is None:
            result["reason"] = "gateway.auth missing in config"
            result["recommendedAction"] = "run gateway_guard.py ensure --apply and restart client session"
        else:
            matches, reason = secret_matches_config(cfg)
            result["secretMatchesConfig"] = matches
            if matches:
                result["ok"] = True
                result["reason"] = "ok"
                result["recommendedAction"] = ""
            else:
                result["reason"] = reason
                result["recommendedAction"] = "run gateway_guard.py ensure --apply and restart client session"
    except Exception as e:
        result["reason"] = str(e)
        result["recommendedAction"] = "run gateway_guard.py ensure --apply and restart client session"

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status_str = "OK" if result["ok"] else "MISMATCH"
        print(f"Gateway status: {status_str}")
        print(f"  running={result['running']}  authMode={result['authMode']}  port={result['gatewayPort']}")
        if not result["ok"]:
            print(f"  reason: {result['reason']}")
            print(f"  action: {result['recommendedAction']}")

    sys.exit(0 if result["ok"] else 1)


def cmd_ensure(args):
    result = {
        "ok": False,
        "secretMatchesConfig": False,
        "running": False,
        "pid": None,
        "reason": "",
        "recommendedAction": "",
        "configPath": str(CONFIG_PATH),
        "authMode": None,
        "gatewayPort": None,
        "applied": False,
        "configWritten": False,
    }
    try:
        cfg = load_config()
        port = get_gateway_port(cfg)
        mode, secret = get_gateway_auth(cfg)
        result["authMode"] = mode
        result["gatewayPort"] = port

        running, pid = gateway_running_state()
        result["running"] = running
        result["pid"] = pid

        # Check current state
        needs_apply = False
        if mode is None or secret is None:
            result["reason"] = "gateway.auth missing in config"
            needs_apply = True
        else:
            matches, reason = secret_matches_config(cfg)
            result["secretMatchesConfig"] = matches
            if not matches:
                result["reason"] = reason
                needs_apply = True
            else:
                result["ok"] = True
                result["reason"] = "ok"

        if needs_apply and args.apply:
            # Step 1: ensure auth exists in config (generate if missing)
            cfg, was_written, _ = ensure_auth_in_config(cfg)
            result["configWritten"] = was_written
            # Re-read mode/secret after possible write
            mode, secret = get_gateway_auth(cfg)
            result["authMode"] = mode
            # Step 2: restart gateway
            host, port = restart_gateway(cfg)
            result["applied"] = True
            # Step 3: optionally wait for port
            if args.wait:
                opened = wait_for_port(host, port, timeout_secs=30)
                result["portOpen"] = opened
            # Step 4: recheck
            matches, reason = secret_matches_config(cfg)
            result["secretMatchesConfig"] = matches
            result["ok"] = matches
            result["reason"] = reason if not matches else "ok"
            result["recommendedAction"] = "" if matches else "run gateway_guard.py ensure --apply and restart client session"
        elif needs_apply and not args.apply:
            result["recommendedAction"] = "run gateway_guard.py ensure --apply and restart client session"
        else:
            result["recommendedAction"] = ""

    except Exception as e:
        result["reason"] = str(e)
        result["recommendedAction"] = "run gateway_guard.py ensure --apply and restart client session"

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Ensure: ok={result['ok']} applied={result['applied']} configWritten={result['configWritten']}")
        if not result["ok"]:
            print(f"  reason: {result['reason']}")
            print(f"  action: {result['recommendedAction']}")

    sys.exit(0 if result["ok"] else 1)


def cmd_continue_on_error(args):
    result = {
        "triggered": False,
        "found": False,
        "inCooldown": False,
        "reason": "",
    }

    def _check_once():
        # Load state
        state = {}
        if CONTINUE_STATE.exists():
            try:
                state = json.loads(CONTINUE_STATE.read_text())
            except Exception:
                state = {}

        last_trigger = state.get("last_trigger", 0)
        now = time.time()
        in_cooldown = (now - last_trigger) < COOLDOWN_SECS

        # Check log
        found = False
        if GATEWAY_LOG.exists():
            content = GATEWAY_LOG.read_text()
            if TRIGGER_STR in content:
                found = True

        result["found"] = found
        result["inCooldown"] = in_cooldown

        if found and not in_cooldown:
            # Deliver continue
            try:
                subprocess.run(
                    [OPENCLAW_BIN, "agent", "--message", "continue", "--deliver"],
                    check=True, capture_output=True
                )
                result["triggered"] = True
                result["reason"] = "run error detected; continue delivered"
                # Update state
                CONTINUE_STATE.parent.mkdir(parents=True, exist_ok=True)
                state["last_trigger"] = now
                CONTINUE_STATE.write_text(json.dumps(state, indent=2))
            except Exception as e:
                result["reason"] = f"failed to deliver continue: {e}"
        elif found and in_cooldown:
            result["reason"] = f"run error found but in cooldown ({COOLDOWN_SECS}s)"
        else:
            result["reason"] = "no run error detected in gateway.log"

    if args.loop:
        interval = args.interval
        while True:
            _check_once()
            if args.json:
                print(json.dumps(result, indent=2))
            time.sleep(interval)
    else:
        _check_once()
        if args.json:
            print(json.dumps(result, indent=2))

    sys.exit(0 if result["triggered"] else (0 if not result["found"] else 1))


def cmd_watch(args):
    """Combined daemon: token sync + continue-on-error check."""
    cfg = load_config()
    # (0) token sync
    ensure_args = argparse.Namespace(apply=True, wait=True, json=args.json)
    cmd_ensure(ensure_args)
    # (1) continue-on-error check
    cont_args = argparse.Namespace(once=True, loop=False, interval=30, json=args.json)
    cmd_continue_on_error(cont_args)


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gateway Guard")
    sub = parser.add_subparsers(dest="cmd")

    p_status = sub.add_parser("status")
    p_status.add_argument("--json", action="store_true")

    p_ensure = sub.add_parser("ensure")
    p_ensure.add_argument("--apply", action="store_true")
    p_ensure.add_argument("--wait",  action="store_true")
    p_ensure.add_argument("--json",  action="store_true")

    p_coe = sub.add_parser("continue-on-error")
    p_coe.add_argument("--once",     action="store_true")
    p_coe.add_argument("--loop",     action="store_true")
    p_coe.add_argument("--interval", type=int, default=30)
    p_coe.add_argument("--json",     action="store_true")

    p_watch = sub.add_parser("watch")
    p_watch.add_argument("--json", action="store_true")

    args = parser.parse_args()
    if args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "ensure":
        cmd_ensure(args)
    elif args.cmd == "continue-on-error":
        cmd_continue_on_error(args)
    elif args.cmd == "watch":
        cmd_watch(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
GATEWAY_GUARD_PY

chmod +x /workspace/scripts/gateway_guard.py

# -------------------------------------------------------------------------
# 3. Create ensure_gateway_then.sh
# -------------------------------------------------------------------------
cat > /workspace/scripts/ensure_gateway_then.sh << 'ENSURE_SH'
#!/bin/bash
set -e
python3 /workspace/scripts/gateway_guard.py ensure --apply --wait
if [ $# -gt 0 ]; then
    exec "$@"
fi
ENSURE_SH
chmod +x /workspace/scripts/ensure_gateway_then.sh

# -------------------------------------------------------------------------
# 4. Create LaunchAgent plist stubs (non-functional in Linux/Docker,
#    but present per file manifest)
# -------------------------------------------------------------------------
cat > /workspace/scripts/com.openclaw.gateway-guard.watcher.plist << 'PLIST1'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.openclaw.gateway-guard.watcher</string>
  <key>ProgramArguments</key>
  <array>
    <string>python3</string>
    <string>OPENCLAW_SKILL_DIR/scripts/gateway_guard.py</string>
    <string>watch</string>
  </array>
  <key>StartInterval</key><integer>30</integer>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
PLIST1

cat > /workspace/scripts/com.openclaw.gateway-guard.continue-on-error.plist << 'PLIST2'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.openclaw.gateway-guard.continue-on-error</string>
  <key>ProgramArguments</key>
  <array>
    <string>python3</string>
    <string>OPENCLAW_SKILL_DIR/scripts/gateway_guard.py</string>
    <string>continue-on-error</string>
    <string>--once</string>
  </array>
  <key>StartInterval</key><integer>30</integer>
</dict>
</plist>
PLIST2

cat > /workspace/scripts/install_watcher.sh << 'INSTALL_SH'
#!/bin/bash
echo "LaunchAgent install not applicable in this environment (Linux/Docker)."
echo "The watcher plist is at: /workspace/scripts/com.openclaw.gateway-guard.watcher.plist"
INSTALL_SH
chmod +x /workspace/scripts/install_watcher.sh

cat > /workspace/scripts/install_continue_on_error.sh << 'INSTALL2_SH'
#!/bin/bash
echo "Redirecting to install_watcher.sh..."
bash /workspace/scripts/install_watcher.sh
INSTALL2_SH
chmod +x /workspace/scripts/install_continue_on_error.sh

# -------------------------------------------------------------------------
# 5. Ensure OPENCLAW_HOME log dir exists
# -------------------------------------------------------------------------
mkdir -p /root/.openclaw/logs

echo "Setup complete. Gateway guard scripts are in /workspace/scripts/"
echo "openclaw.json is at /root/.openclaw/openclaw.json"
echo "gateway.log is at /root/.openclaw/logs/gateway.log"