#!/usr/bin/env python3
"""
Generate the sandbox workspace for the config-guardian evaluation task.
Creates the skill directory structure, distractor files, and the core
openclaw-config-guardian scripts that would normally be shipped with the package.
"""

import os
import sys
import stat
import json
import hashlib
import random
import string
from pathlib import Path

WORKSPACE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
random.seed(42)

# ── helpers ──────────────────────────────────────────────────────────────────

def write(path: Path, content: str, mode: int = 0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    os.chmod(path, mode)

def rnd_str(n=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))

# ── 1. Distractor files (realistic fintech project noise) ─────────────────────

distractor_tree = {
    "services/gateway/routes.py": "# Routing logic for OpenClaw gateway\nROUTES = ['/pay', '/refund', '/status']\n",
    "services/gateway/middleware.py": "# Auth middleware placeholder\nclass AuthMiddleware: pass\n",
    "services/gateway/Dockerfile": "FROM python:3.11-slim\nCOPY . /app\nCMD ['python', 'main.py']\n",
    "services/gateway/requirements.txt": "fastapi==0.111.0\nuvicorn==0.29.0\nhttpx==0.27.0\n",
    "services/db/migrations/0001_init.sql": "CREATE TABLE transactions (id SERIAL PRIMARY KEY, amount DECIMAL);\n",
    "services/db/migrations/0002_add_status.sql": "ALTER TABLE transactions ADD COLUMN status VARCHAR(32);\n",
    "services/db/schema.json": json.dumps({"version": 2, "tables": ["transactions", "audit_log"]}, indent=2) + "\n",
    "deploy/k8s/gateway-deployment.yaml": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: openclaw-gateway\n",
    "deploy/k8s/configmap.yaml": "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: openclaw-config\n",
    "deploy/terraform/main.tf": 'provider "aws" { region = "us-east-1" }\n',
    "deploy/terraform/variables.tf": 'variable "env" { default = "production" }\n',
    "monitoring/alerts/cpu_high.yaml": "alert: HighCPU\nexpr: cpu_usage > 90\n",
    "monitoring/alerts/config_drift.yaml": "alert: ConfigDrift\nexpr: config_changes_total > 0\n",
    "monitoring/dashboards/gateway.json": json.dumps({"title": "Gateway Dashboard", "panels": []}, indent=2) + "\n",
    "ci/.gitlab-ci.yml": "stages:\n  - test\n  - deploy\ntest:\n  script:\n    - pytest\n",
    "ci/scripts/run_tests.sh": "#!/bin/bash\nset -e\npytest services/\n",
    "docs/runbook.md": "# Runbook\n## Incident Response\nSee config-guardian for config rollback procedures.\n",
    "docs/architecture.md": "# Architecture\nOpenClaw Gateway + Config Guardian protect production config.\n",
    "config/logging.yaml": "level: INFO\nformat: json\noutput: /var/log/openclaw/gateway.log\n",
    "config/feature_flags.json": json.dumps({"new_payment_flow": False, "retry_logic": True}, indent=2) + "\n",
    "scripts/rotate_keys.sh": "#!/bin/bash\n# Placeholder: key rotation\necho 'Rotating keys...'\n",
}

for rel, content in distractor_tree.items():
    write(WORKSPACE / rel, content)

# ── 2. Skill directory: scripts/ (the actual shipped scripts) ─────────────────

# The real openclaw-config-guardian runtime script
# This is what install.sh copies to /usr/local/bin/
GUARDIAN_SCRIPT = r"""#!/bin/bash
# openclaw-config-guardian v3.2
# Protects /root/.openclaw/openclaw.json with auto-rollback, lock mode,
# multi-version baseline, audit log, and SIGUSR1 hot-reload.

set -euo pipefail

GUARDIAN_VERSION="3.2"
CONFIG_PATH="/root/.openclaw/openclaw.json"
BACKUP_DIR="/root/.openclaw/backups/config"
BASELINE_PATH="$BACKUP_DIR/baseline.json"
STATE_PATH="$BACKUP_DIR/.guardian_state.json"
AUDIT_LOG="$BACKUP_DIR/guardian_audit.log"
CHECKSUM_FILE="$BACKUP_DIR/.guardian_checksum"
HISTORY_DIR="$BACKUP_DIR/baseline_history"
SELF_PATH="/usr/local/bin/openclaw-config-guardian"
LOCK_THRESHOLD=3
MAX_HISTORY=7

# ── subcommand: unlock ────────────────────────────────────────────────────────
if [[ "${1:-}" == "unlock" ]]; then
    if ! jq -e . "$CONFIG_PATH" > /dev/null 2>&1; then
        echo "[guardian] ERROR: config JSON invalid, fix before unlocking" >&2
        exit 1
    fi
    # validate required fields
    if ! jq -e '.gateway_id and .port and .environment' "$CONFIG_PATH" > /dev/null 2>&1; then
        echo "[guardian] ERROR: config missing required fields (gateway_id, port, environment)" >&2
        exit 1
    fi
    # reset state
    jq '.locked = false | .attempts = 0 | .last_error = null' "$STATE_PATH" > /tmp/_gs_tmp.json
    mv /tmp/_gs_tmp.json "$STATE_PATH"
    _audit "UNLOCK" "manual unlock successful"
    echo "[guardian] ✅ unlocked successfully"
    exit 0
fi

# ── self-integrity check ──────────────────────────────────────────────────────
_self_check() {
    if [[ ! -f "$CHECKSUM_FILE" ]]; then
        echo "[guardian] WARN: no checksum file, skipping self-check"
        return 0
    fi
    local expected actual
    expected=$(awk '{print $1}' "$CHECKSUM_FILE")
    actual=$(sha256sum "$SELF_PATH" | awk '{print $1}')
    if [[ "$expected" != "$actual" ]]; then
        echo "[guardian] FATAL: self-integrity check failed! Script tampered. Refusing to start." >&2
        exit 127
    fi
}

# ── audit log ────────────────────────────────────────────────────────────────
_audit() {
    local event="$1" detail="${2:-}"
    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"ts\":\"$ts\",\"event\":\"$event\",\"detail\":\"$detail\",\"pid\":$$}" >> "$AUDIT_LOG"
}

# ── state helpers ─────────────────────────────────────────────────────────────
_state_get() { jq -r ".$1 // empty" "$STATE_PATH" 2>/dev/null || echo ""; }

_state_init() {
    if [[ ! -f "$STATE_PATH" ]]; then
        echo '{"locked":false,"attempts":0,"last_error":null}' > "$STATE_PATH"
    fi
}

# ── baseline archive ──────────────────────────────────────────────────────────
_archive_baseline() {
    if [[ ! -f "$BASELINE_PATH" ]]; then return; fi
    mkdir -p "$HISTORY_DIR"
    local ts
    ts=$(date -u +"%Y%m%dT%H%M%SZ")
    cp "$BASELINE_PATH" "$HISTORY_DIR/baseline_${ts}.json"
    # prune to MAX_HISTORY
    local count
    count=$(ls "$HISTORY_DIR"/baseline_*.json 2>/dev/null | wc -l)
    if (( count > MAX_HISTORY )); then
        ls -t "$HISTORY_DIR"/baseline_*.json | tail -n +$((MAX_HISTORY+1)) | xargs rm -f
    fi
}

# ── validate config ───────────────────────────────────────────────────────────
_validate() {
    local path="$1"
    if ! jq -e . "$path" > /dev/null 2>&1; then
        echo "invalid JSON"
        return 1
    fi
    if ! jq -e '.gateway_id and .port and .environment' "$path" > /dev/null 2>&1; then
        echo "missing required fields"
        return 1
    fi
    return 0
}

# ── rollback ──────────────────────────────────────────────────────────────────
_rollback() {
    local reason="$1"
    if [[ -f "$BASELINE_PATH" ]]; then
        cp "$BASELINE_PATH" "$CONFIG_PATH"
        _audit "ROLLBACK" "$reason"
        echo "[guardian] 🔄 rolled back: $reason"
    else
        _audit "ROLLBACK_FAILED" "no baseline available"
        echo "[guardian] ERROR: no baseline to rollback to" >&2
    fi
}

# ── signal SIGUSR1 to gateway ─────────────────────────────────────────────────
_notify_gateway() {
    local gw_pid
    gw_pid=$(pgrep -f "openclaw.*gateway" 2>/dev/null | head -1 || true)
    if [[ -n "$gw_pid" ]]; then
        kill -SIGUSR1 "$gw_pid" 2>/dev/null || true
        _audit "SIGUSR1" "notified gateway pid=$gw_pid"
    fi
}

# ── lock state ────────────────────────────────────────────────────────────────
_increment_attempts() {
    local err="$1"
    local attempts
    attempts=$(jq '.attempts' "$STATE_PATH")
    attempts=$((attempts + 1))
    jq --argjson a "$attempts" --arg e "$err" \
       '.attempts = $a | .last_error = $e' "$STATE_PATH" > /tmp/_gs_tmp.json
    mv /tmp/_gs_tmp.json "$STATE_PATH"
    if (( attempts >= LOCK_THRESHOLD )); then
        jq '.locked = true' "$STATE_PATH" > /tmp/_gs_tmp.json
        mv /tmp/_gs_tmp.json "$STATE_PATH"
        _audit "LOCKED" "threshold reached after $attempts failures"
        echo "[guardian] 🔒 LOCKED after $attempts consecutive failures"
        openclaw message send "🚨 config-guardian LOCKED: $err" 2>/dev/null || true
    fi
}

_reset_attempts() {
    jq '.attempts = 0 | .last_error = null' "$STATE_PATH" > /tmp/_gs_tmp.json
    mv /tmp/_gs_tmp.json "$STATE_PATH"
}

# ── main watch loop ───────────────────────────────────────────────────────────
_watch() {
    echo "[guardian] 🛡️ guardian v$GUARDIAN_VERSION started"
    _audit "START" "guardian v$GUARDIAN_VERSION"

    # ensure baseline exists
    if [[ ! -f "$BASELINE_PATH" ]]; then
        if _validate "$CONFIG_PATH" > /dev/null 2>&1; then
            cp "$CONFIG_PATH" "$BASELINE_PATH"
            _audit "BASELINE_INIT" "initial baseline created"
        fi
    fi

    inotifywait -m -e close_write,moved_to --format '%e %w%f' "$CONFIG_PATH" 2>/dev/null |
    while IFS= read -r event_line; do
        local locked
        locked=$(_state_get locked)

        local err
        if ! err=$(_validate "$CONFIG_PATH" 2>&1); then
            _increment_attempts "$err"
            _rollback "$err"
            continue
        fi

        if [[ "$locked" == "true" ]]; then
            # locked: force rollback even for valid configs
            _increment_attempts "locked mode"
            _rollback "locked mode active"
            continue
        fi

        # valid + not locked: promote to baseline
        _archive_baseline
        cp "$CONFIG_PATH" "$BASELINE_PATH"
        _reset_attempts
        _audit "BASELINE_UPDATE" "new valid baseline accepted"
        _notify_gateway
        echo "[guardian] ✅ baseline updated"
    done
}

# ── entry ─────────────────────────────────────────────────────────────────────
mkdir -p "$BACKUP_DIR" "$HISTORY_DIR"
_state_init
_self_check
_watch
"""

write(WORKSPACE / "scripts/openclaw-config-guardian", GUARDIAN_SCRIPT, mode=0o755)

# install.sh
INSTALL_SH = r"""#!/bin/bash
set -euo pipefail

INSTALL_BIN="/usr/local/bin/openclaw-config-guardian"
BACKUP_DIR="/root/.openclaw/backups/config"
CHECKSUM_FILE="$BACKUP_DIR/.guardian_checksum"
SYSTEMD_UNIT="/etc/systemd/system/openclaw-config-guardian.service"
SCRIPT_SRC="$(dirname "$0")/openclaw-config-guardian"

echo "[install] Installing openclaw-config-guardian..."

# 1. copy binary
install -m 0755 "$SCRIPT_SRC" "$INSTALL_BIN"

# 2. create directories
mkdir -p "$BACKUP_DIR" /root/.openclaw

# 3. write checksum
sha256sum "$INSTALL_BIN" > "$CHECKSUM_FILE"
echo "[install] Checksum written: $CHECKSUM_FILE"

# 4. write systemd unit
cat > "$SYSTEMD_UNIT" <<'UNIT'
[Unit]
Description=OpenClaw Config Guardian
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/openclaw-config-guardian
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

echo "[install] Systemd unit written: $SYSTEMD_UNIT"

# 5. enable + start (best-effort; may fail in containers without systemd)
if command -v systemctl &>/dev/null && systemctl --version &>/dev/null 2>&1; then
    systemctl daemon-reload
    systemctl enable openclaw-config-guardian 2>/dev/null || true
    systemctl start openclaw-config-guardian 2>/dev/null || true
    echo "[install] Service enabled and started"
else
    echo "[install] systemd not active; skipping service start"
fi

echo "[install] ✅ Installation complete"
"""

write(WORKSPACE / "scripts/install.sh", INSTALL_SH, mode=0o755)

# ── 3. Initial valid openclaw.json ────────────────────────────────────────────

OPENCLAW_CONFIG_DIR = Path("/root/.openclaw")
OPENCLAW_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

valid_config = {
    "gateway_id": "gw-prod-7a3f",
    "port": 8443,
    "environment": "production",
    "tls": True,
    "max_connections": 1000,
    "timeout_ms": 5000,
    "routes": [
        {"path": "/pay", "upstream": "payment-svc:9001"},
        {"path": "/refund", "upstream": "refund-svc:9002"}
    ]
}

config_path = OPENCLAW_CONFIG_DIR / "openclaw.json"
config_path.write_text(json.dumps(valid_config, indent=2))
os.chmod(config_path, 0o600)

# ── 4. SKILL.md (the agent's primary reference) ───────────────────────────────

SKILL_MD = """---
name: config-guardian
description: Protect openclaw.json with automatic rollback, lock mode, multi-version baseline snapshots, audit log, and SIGUSR1 gateway hot-reload.
license: MIT
metadata:
  version: 1.0.4
  author: 大黑 #F_SEC
---

# config-guardian（配置自愈）

自动监控 `openclaw.json`，写入失败自动回滚到上一个有效版本。支持磁盘持久化锁定模式、多版本快照、结构化审计日志、SIGUSR1 热重载。

## 功能一览

- **自动回滚**：任何写入触发验证，失败立即恢复到 baseline
- **锁定模式**：连续 3 次失败后进入锁定，所有写入强制回滚，监控不停止
- **持久化状态**：锁定状态落盘，守护重启后依然有效
- **多版本 baseline**：每次更新 baseline 前归档，保留最近 7 个有效版本
- **SIGUSR1 热重载**：回滚/验证通过后自动通知 gateway，无需手动重启
- **审计日志**：每次操作记录时间戳、事件类型、触发进程
- **自身完整性**：启动时 SHA256 自检，脚本被篡改则拒绝启动并告警

## 安装

```bash
bash scripts/install.sh
```

安装后验证：

```bash
systemctl status openclaw-config-guardian
# 应显示：active (running)，日志含 🛡️ guardian v3.2 started
```

## 核心命令速查

```bash
# 查看锁定状态
jq '.locked, .attempts, .last_error' /root/.openclaw/backups/config/.guardian_state.json

# 解锁
openclaw-config-guardian unlock

# 查看审计日志
tail -30 /root/.openclaw/backups/config/guardian_audit.log

# 查看 baseline 历史
ls -lth /root/.openclaw/backups/config/baseline_history/

# 重启守护
systemctl restart openclaw-config-guardian
```

## 解锁流程

1. 修复配置使其包含所有必需字段
2. 执行解锁（内置 validate，通过才解锁）：
   ```bash
   openclaw-config-guardian unlock
   ```
3. 确认：`jq '.locked' /root/.openclaw/backups/config/.guardian_state.json` → `false`

## 更新 guardian 脚本后必须刷新 checksum

```bash
sha256sum /usr/local/bin/openclaw-config-guardian > \\
  /root/.openclaw/backups/config/.guardian_checksum
systemctl restart openclaw-config-guardian
```
"""

write(WORKSPACE / "SKILL.md", SKILL_MD)

# ── 5. references/ directory (additional docs, realistic noise) ───────────────

DESIGN_MD = """# DESIGN.md — Config Guardian Architecture

## State Machine

```
INIT → WATCHING → VALID_WRITE (baseline promoted)
                → INVALID_WRITE (rollback, attempts++)
                → LOCKED (attempts >= 3, all writes rolled back)
                → UNLOCKED (manual unlock, attempts reset)
```

## Files

| Path | Purpose |
|------|---------|
| /root/.openclaw/backups/config/baseline.json | Current golden baseline |
| /root/.openclaw/backups/config/.guardian_state.json | Persistent lock state |
| /root/.openclaw/backups/config/guardian_audit.log | NDJSON audit trail |
| /root/.openclaw/backups/config/.guardian_checksum | SHA256 of guardian binary |
| /root/.openclaw/backups/config/baseline_history/ | Archived prior baselines |
"""

USAGE_MD = """# USAGE.md — Daily Operations

## Simulating a bad write (for testing)

```bash
echo '{"broken": true}' > /root/.openclaw/openclaw.json
```

This will trigger a rollback within seconds.

## Checking lock state

```bash
jq '.locked, .attempts' /root/.openclaw/backups/config/.guardian_state.json
```

## Recovery from lockout

Fix the config first, then:
```bash
openclaw-config-guardian unlock
```
"""

OPERATION_MD = """# OPERATION.md — Ops Guide

## Checksum Refresh (after binary update)

If you update the guardian script you MUST refresh the checksum or it will refuse to start:

```bash
sha256sum /usr/local/bin/openclaw-config-guardian > /root/.openclaw/backups/config/.guardian_checksum
systemctl restart openclaw-config-guardian
```

## Log Locations

- Audit log: /root/.openclaw/backups/config/guardian_audit.log
- Systemd journal: journalctl -u openclaw-config-guardian
"""

write(WORKSPACE / "references/DESIGN.md", DESIGN_MD)
write(WORKSPACE / "references/USAGE.md", USAGE_MD)
write(WORKSPACE / "references/OPERATION.md", OPERATION_MD)

# ── 6. Additional distractor configs (red herrings) ──────────────────────────

write(WORKSPACE / "config/guardian.conf.example",
      "# Example guardian config (not used directly)\nLOCK_THRESHOLD=3\nMAX_HISTORY=7\n")

write(WORKSPACE / "config/openclaw.json.template",
      json.dumps({"gateway_id": "REPLACE_ME", "port": 8443, "environment": "REPLACE_ME"}, indent=2))

write(WORKSPACE / "logs/.gitkeep", "")

write(WORKSPACE / "scripts/healthcheck.sh",
      "#!/bin/bash\ncurl -sf http://localhost:8443/health || exit 1\n", mode=0o755)

write(WORKSPACE / "scripts/backup_config.sh",
      "#!/bin/bash\ncp /root/.openclaw/openclaw.json /tmp/openclaw.json.bak\n", mode=0o755)

# ── done ──────────────────────────────────────────────────────────────────────
print("[gen_inputs] Workspace generated successfully.")
print(f"  Distractor files: {len(distractor_tree)}")
print(f"  Config at: {config_path}")
print(f"  Workspace root: {WORKSPACE}")