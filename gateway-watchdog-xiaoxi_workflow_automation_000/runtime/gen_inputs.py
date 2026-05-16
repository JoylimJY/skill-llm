import os
import random
import stat

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "logs/gateway",
    "logs/system",
    "config/network",
    "config/auth",
    "services/trading",
    "services/risk",
    "infra/monitoring",
    "infra/backup",
    "scripts/legacy",
    "docs/internal",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "logs/gateway/access.log": "2024-01-15 09:00:01 GET /api/v2/orders 200\n2024-01-15 09:00:02 POST /api/v2/trade 201\n",
    "logs/gateway/error.log": "2024-01-15 08:55:00 ERROR connection_timeout host=db-primary\n",
    "logs/system/syslog.txt": "Jan 15 09:00:00 kernel: [12345.678] net: connection established\n",
    "config/network/firewall.conf": "[rules]\nallow_inbound=8080,443\ndeny_all=true\n",
    "config/auth/tokens.cfg": "# DO NOT COMMIT\ntoken_expiry=3600\nrefresh_enabled=true\n",
    "config/gateway.conf": "[gateway]\nhost=0.0.0.0\nport=8080\nmax_connections=1000\ntimeout=30\n",
    "services/trading/order_service.py": "# Order processing service\nclass OrderService:\n    pass\n",
    "services/risk/risk_engine.py": "# Risk calculation engine\nclass RiskEngine:\n    pass\n",
    "infra/monitoring/alerts.yml": "alerts:\n  - name: high_latency\n    threshold: 500ms\n  - name: error_rate\n    threshold: 0.01\n",
    "infra/backup/backup_schedule.txt": "Daily backup: 02:00 UTC\nWeekly snapshot: Sunday 03:00 UTC\n",
    "scripts/legacy/old_monitor.sh": "#!/bin/bash\n# DEPRECATED - do not use\n# This cron-based monitor is broken when gateway is down\n*/5 * * * * check_gateway.sh\n",
    "docs/internal/architecture.md": "# System Architecture\n## Components\n- API Gateway (OpenClaw)\n- Trading Engine\n- Risk Manager\n## Note\nGateway must remain online 24/7 for trading operations.\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── The real skill scripts the agent needs to discover and use ───────────────
# gateway_watchdog.py — a realistic mock that actually tracks PIDs and state
watchdog_script = '''\
#!/usr/bin/env python3
"""
OpenClaw Gateway Watchdog
External process watchdog for OpenClaw Gateway.
Usage: python gateway_watchdog.py [start|stop|status|restart]
"""

import sys
import os
import json
import time
import signal

STATE_FILE = "/tmp/gateway_watchdog_state.json"
LOG_FILE = "/tmp/gateway_watchdog.log"


def _load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"running": False, "pid": None, "started_at": None}


def _save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def _append_log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\\n")
    print(msg)


def _is_pid_alive(pid):
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def cmd_start():
    state = _load_state()
    if state["running"] and _is_pid_alive(state.get("pid")):
        _append_log(f"⚠️  Gateway Watchdog already running (PID: {state[\'pid\']})")
        return 1

    # Simulate watchdog process by recording current PID
    pid = os.getpid()
    state = {"running": True, "pid": pid, "started_at": time.time()}
    _save_state(state)
    _append_log(f"🚀 启动 Gateway Watchdog...")
    _append_log(f"✅ Gateway Watchdog 已启动 (PID: {pid})")
    _append_log("✅ 完成！Gateway 将 7/24 运行")
    return 0


def cmd_status():
    state = _load_state()
    if state["running"]:
        pid = state.get("pid")
        started = state.get("started_at")
        uptime = int(time.time() - started) if started else 0
        _append_log(f"✅ Gateway Watchdog 运行中 (PID: {pid}, 运行时间: {uptime}s)")
        _append_log(f"STATUS:running PID:{pid}")
    else:
        _append_log("❌ Gateway Watchdog 未运行")
        _append_log("STATUS:stopped")
    return 0


def cmd_stop():
    state = _load_state()
    if not state["running"]:
        _append_log("⚠️  Gateway Watchdog 未在运行")
        return 1
    state["running"] = False
    state["pid"] = None
    _save_state(state)
    _append_log("🛑 Gateway Watchdog 已停止")
    return 0


def cmd_restart():
    _append_log("🔄 重启 Gateway Watchdog...")
    cmd_stop()
    time.sleep(0.2)
    return cmd_start()


def main():
    if len(sys.argv) < 2:
        print("用法: python gateway_watchdog.py [start|stop|status|restart]")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "start":
        sys.exit(cmd_start())
    elif cmd == "stop":
        sys.exit(cmd_stop())
    elif cmd == "status":
        sys.exit(cmd_status())
    elif cmd == "restart":
        sys.exit(cmd_restart())
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "gateway_watchdog.py"), "w") as f:
    f.write(watchdog_script)
os.chmod(os.path.join(workspace, "gateway_watchdog.py"), 0o755)

# install.py — one-shot bootstrapper
install_script = '''\
#!/usr/bin/env python3
"""
OpenClaw Gateway Watchdog Installer
One-click install and start.
"""
import subprocess
import sys
import os

print("📦 OpenClaw Gateway Watchdog Installer")
print("=" * 40)

watchdog = "gateway_watchdog.py"
if not os.path.exists(watchdog):
    print(f"📥 正在下载 {watchdog}...")
    # In production this would download from GitHub
    print("❌ 未找到 gateway_watchdog.py，请先下载")
    sys.exit(1)
else:
    print(f"✅ {watchdog} 已就绪")

print("🚀 启动 Gateway Watchdog...")
result = subprocess.run([sys.executable, watchdog, "start"], capture_output=False)
if result.returncode == 0:
    print("✅ 安装完成！Gateway 将 7/24 运行")
else:
    print("⚠️  启动时出现问题，请检查日志")
sys.exit(result.returncode)
'''

with open(os.path.join(workspace, "install.py"), "w") as f:
    f.write(install_script)
os.chmod(os.path.join(workspace, "install.py"), 0o755)

# A dummy openclaw CLI shim
openclaw_shim = '''\
#!/usr/bin/env python3
import sys
args = sys.argv[1:]
if args and args[0] == "version":
    print("OpenClaw Gateway v2.4.1")
elif args and args[0] == "status":
    print("Gateway: operational")
else:
    print(f"openclaw {' '.join(args)}")
'''
with open("/usr/local/bin/openclaw", "w") as f:
    f.write(openclaw_shim)
os.chmod("/usr/local/bin/openclaw", 0o755)

print("Workspace generation complete.")
print(f"Files created in {workspace}:")
for root, dirs_list, files in os.walk(workspace):
    level = root.replace(workspace, "").count(os.sep)
    indent = "  " * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = "  " * (level + 1)
    for fname in files:
        print(f"{subindent}{fname}")