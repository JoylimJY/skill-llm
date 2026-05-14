#!/bin/bash
set -e

echo "[setup] Installing mock session_status command..."
cp /workspace/tmp/session_status_mock.sh /usr/local/bin/session_status
chmod +x /usr/local/bin/session_status

echo "[setup] Ensuring agent/logs directory exists..."
mkdir -p /workspace/agent/logs
mkdir -p /workspace/agent/sessions

echo "[setup] Verifying PowerShell is available..."
pwsh --version || { echo "ERROR: pwsh not found!"; exit 1; }

echo "[setup] Verifying check_context.ps1 exists..."
ls -la /workspace/skills/context-sentinel/scripts/check_context.ps1

echo "[setup] Adding 'powershell' symlink for SKILL.md compatibility..."
# SKILL.md uses `powershell -File ...`; on Linux with pwsh, we alias it
if ! command -v powershell &>/dev/null; then
    ln -s /usr/bin/pwsh /usr/local/bin/powershell
fi

echo "[setup] Setup complete."