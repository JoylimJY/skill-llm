#!/usr/bin/env bash
set -euo pipefail

WORKSPACE=/workspace

# ── Mock `pm2` binary ─────────────────────────────────────────────────────────
cat > /usr/local/bin/pm2 << 'MOCK_PM2'
#!/usr/bin/env python3
import sys, json, time

args = sys.argv[1:]

if not args:
    print("Usage: pm2 <command> [options]")
    sys.exit(0)

cmd = args[0]

if cmd == "list":
    print("""
┌────┬──────────────────┬─────────┬─────────┬──────────┬────────┬──────┬──────────┐
│ id │ name             │ mode    │ ↺       │ status   │ cpu    │ mem  │ watching │
├────┼──────────────────┼─────────┼─────────┼──────────┼────────┼──────┼──────────┤
│ 0  │ api-gateway      │ cluster │ 7       │ errored  │ 0%     │ 0b   │ disabled │
│ 1  │ payment-worker   │ fork    │ 0       │ online   │ 1.2%   │ 48mb │ disabled │
│ 2  │ auth-service     │ fork    │ 0       │ online   │ 0.8%   │ 32mb │ disabled │
└────┴──────────────────┴─────────┴─────────┴──────────┴────────┴──────┴──────────┘
""")

elif cmd == "logs" and len(args) >= 2:
    svc = args[1]
    lines_arg = None
    for i, a in enumerate(args):
        if a == "--lines" and i+1 < len(args):
            lines_arg = args[i+1]
    print(f"[PM2][LOG] Streaming logs for {svc} (last 50 lines):")
    print(f"[2024-03-12 14:18:32.441] [api-gateway] ERROR: ECONNREFUSED connecting to postgres://prod-db.internal:5432")
    print(f"[2024-03-12 14:19:01.112] [api-gateway] ERROR: health check failed – shutting down worker pid 18842")
    print(f"[2024-03-12 14:19:01.115] [api-gateway] WARN:  max restarts (7) reached – process marked as errored")
    print(f"[2024-03-12 14:20:00.000] [api-gateway] INFO:  Waiting for manual intervention")

elif cmd == "restart" and len(args) >= 2:
    svc = args[1]
    print(f"[PM2] Restarting {svc}...")
    time.sleep(0.3)
    print(f"[PM2] ✓ {svc} restarted successfully (pid 19200)")

elif cmd == "delete" and len(args) >= 2:
    svc = args[1]
    print(f"[PM2] Deleted process {svc}")

else:
    print(f"[PM2] Unknown command: {cmd}")
    sys.exit(1)
MOCK_PM2
chmod +x /usr/local/bin/pm2

# ── Mock `docker` binary ──────────────────────────────────────────────────────
cat > /usr/local/bin/docker << 'MOCK_DOCKER'
#!/usr/bin/env python3
import sys

args = sys.argv[1:]
if not args:
    print("Usage: docker <command>")
    sys.exit(0)

cmd = args[0]

if cmd == "ps":
    print("CONTAINER ID   IMAGE                  COMMAND       CREATED        STATUS        PORTS     NAMES")
    print("a1b2c3d4e5f6   nginx:alpine           nginx -g …    2 hours ago    Up 2 hours    80/tcp    nginx-proxy")
    print("b2c3d4e5f6a1   redis:7                redis-serv…   5 hours ago    Up 5 hours    6379/tcp  redis-cache")

elif cmd == "logs" and len(args) >= 2:
    ctr = args[1]
    print(f"[docker][{ctr}] INFO: container running normally")

elif cmd == "restart" and len(args) >= 2:
    ctr = args[1]
    print(f"Container {ctr} restarted.")

else:
    print(f"[docker] command: {' '.join(args)}")
MOCK_DOCKER
chmod +x /usr/local/bin/docker

# ── Main `nexus-safe` binary ──────────────────────────────────────────────────
cat > /usr/local/bin/nexus-safe << 'NEXUS_SAFE_PY'
#!/usr/bin/env python3
"""
Nexus-Safe V1.3.0 — Autonomous local System Reliability Agent for OpenClaw.
All logic is 100% local. No outbound network calls.
"""
import sys, os, json, time, subprocess
from pathlib import Path
from datetime import datetime

# ── State directory ────────────────────────────────────────────────────────────
STATE_DIR = Path("/workspace/.nexus_safe_state")
STATE_DIR.mkdir(parents=True, exist_ok=True)

RESTART_LOG_FILE = STATE_DIR / "restart_log.json"
LOGS_REVIEWED_FILE = STATE_DIR / "logs_reviewed.json"

RATE_LIMIT_MAX = 3
RATE_LIMIT_WINDOW = 3600   # 1 hour in seconds
LOGS_FRESHNESS   = 300     # 5 minutes in seconds

def load_json(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:
        return default

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))

def get_allowed(env_var):
    raw = os.environ.get(env_var, "")
    return [s.strip() for s in raw.split(",") if s.strip()]

def cmd_status():
    try:
        import psutil
        cpu  = psutil.cpu_percent(interval=1)
        ram  = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        load = os.getloadavg()
        print(json.dumps({
            "cpu_percent":  cpu,
            "ram_used_pct": ram.percent,
            "disk_used_pct": disk.percent,
            "load_avg_1m":  load[0],
            "load_avg_5m":  load[1],
            "load_avg_15m": load[2],
        }, indent=2))
    except ImportError:
        print("ERROR: psutil not installed. Run: pip install psutil")
        sys.exit(1)

def cmd_logs(service):
    """Retrieve logs and record the review timestamp."""
    # Try PM2 first
    allowed_pm2 = get_allowed("NEXUS_SAFE_ALLOWED_PM2")
    allowed_docker = get_allowed("NEXUS_SAFE_ALLOWED_DOCKER")

    found = False
    if service in allowed_pm2 or not allowed_pm2:
        result = subprocess.run(["pm2", "logs", service, "--lines", "50", "--nostream"],
                                capture_output=True, text=True)
        if result.returncode == 0 or result.stdout:
            print(result.stdout or result.stderr)
            found = True

    if not found:
        result = subprocess.run(["docker", "logs", "--tail", "50", service],
                                capture_output=True, text=True)
        print(result.stdout or result.stderr)

    # Record review timestamp
    reviews = load_json(LOGS_REVIEWED_FILE, {})
    reviews[service] = time.time()
    save_json(LOGS_REVIEWED_FILE, reviews)
    print(f"[nexus-safe] Logs reviewed for '{service}' at {datetime.utcnow().isoformat()}Z")

def cmd_recover(service):
    """Recover (restart) a service after policy checks."""
    allowed_pm2    = get_allowed("NEXUS_SAFE_ALLOWED_PM2")
    allowed_docker = get_allowed("NEXUS_SAFE_ALLOWED_DOCKER")

    # ── 1. Allowlist check ─────────────────────────────────────────────────────
    in_pm2    = service in allowed_pm2
    in_docker = service in allowed_docker

    if not in_pm2 and not in_docker:
        print(f"[nexus-safe] POLICY VIOLATION: '{service}' is not in NEXUS_SAFE_ALLOWED_PM2 "
              f"or NEXUS_SAFE_ALLOWED_DOCKER. Add it to the allowlist and retry.")
        sys.exit(1)

    # ── 2. Logs-First policy ───────────────────────────────────────────────────
    reviews = load_json(LOGS_REVIEWED_FILE, {})
    last_review = reviews.get(service, 0)
    age = time.time() - last_review
    if age > LOGS_FRESHNESS:
        print(f"[nexus-safe] POLICY VIOLATION (Logs-First): Logs for '{service}' were last "
              f"reviewed {int(age)}s ago (limit: {LOGS_FRESHNESS}s). "
              f"Run `nexus-safe logs {service}` first, then retry within 5 minutes.")
        sys.exit(1)

    # ── 3. Rate limit check ────────────────────────────────────────────────────
    restart_log = load_json(RESTART_LOG_FILE, [])
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    recent = [t for t in restart_log if t > window_start]

    if len(recent) >= RATE_LIMIT_MAX:
        print(f"[nexus-safe] RATE LIMIT: Max {RATE_LIMIT_MAX} restarts per hour reached. "
              f"Try again later.")
        sys.exit(1)

    # ── 4. Execute restart ─────────────────────────────────────────────────────
    if in_pm2:
        result = subprocess.run(["pm2", "restart", service], capture_output=True, text=True)
        runtime = "pm2"
    else:
        result = subprocess.run(["docker", "restart", service], capture_output=True, text=True)
        runtime = "docker"

    if result.returncode != 0:
        print(f"[nexus-safe] ERROR: Restart command failed.\n{result.stderr}")
        sys.exit(1)

    # ── 5. Record restart & emit summary ──────────────────────────────────────
    recent.append(now)
    save_json(RESTART_LOG_FILE, recent)

    summary = {
        "service":   service,
        "action":    "restart",
        "runtime":   runtime,
        "status":    "success",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    print(json.dumps(summary, indent=2))

# ── Entry point ────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: nexus-safe <status|logs|recover> [service]")
        sys.exit(1)

    subcmd = sys.argv[1]

    if subcmd == "status":
        cmd_status()
    elif subcmd == "logs":
        if len(sys.argv) < 3:
            print("Usage: nexus-safe logs <service>")
            sys.exit(1)
        cmd_logs(sys.argv[2])
    elif subcmd == "recover":
        if len(sys.argv) < 3:
            print("Usage: nexus-safe recover <service>")
            sys.exit(1)
        cmd_recover(sys.argv[2])
    else:
        print(f"Unknown subcommand: {subcmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
NEXUS_SAFE_PY
chmod +x /usr/local/bin/nexus-safe

echo "Setup complete. nexus-safe, pm2, and docker mocks are installed."