#!/bin/bash
set -e

# Ensure check_model.py is executable everywhere
chmod +x /workspace/check_model.py
chmod +x ~/.openclaw/skills/model-switch-notify/scripts/check_model.py

# Create a symlink so both paths work
ln -sf ~/.openclaw/skills/model-switch-notify/scripts/check_model.py /usr/local/bin/check_model.py 2>/dev/null || true

# Verify DB exists
if [ -f ~/.openclaw/data/model-switch.db ]; then
    echo "[setup] SQLite DB found at ~/.openclaw/data/model-switch.db"
    sqlite3 ~/.openclaw/data/model-switch.db "SELECT agent_id, last_model, pending_notify FROM model_states;"
else
    echo "[setup] WARNING: DB not found, will be created on first use"
fi

echo "[setup] Environment ready."