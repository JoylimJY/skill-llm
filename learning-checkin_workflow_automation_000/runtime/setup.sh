#!/bin/bash
set -e

echo "=== Setting up learning-checkin skill ==="

SKILL_DIR="/workspace/skills/learning-checkin"

# If clone failed during gen_inputs_script, retry here
if [ -f "${SKILL_DIR}/.clone_failed" ]; then
    echo "Retrying git clone..."
    rm -rf "${SKILL_DIR}"
    mkdir -p "${SKILL_DIR}"
    git clone https://github.com/daizongyu/learning-checkin.git "${SKILL_DIR}" || {
        echo "ERROR: Cannot clone learning-checkin repository"
        exit 1
    }
fi

# Ensure the script is executable
if [ -f "${SKILL_DIR}/learning_checkin.py" ]; then
    chmod +x "${SKILL_DIR}/learning_checkin.py"
    echo "Script is executable: ${SKILL_DIR}/learning_checkin.py"
else
    echo "ERROR: learning_checkin.py not found at ${SKILL_DIR}"
    ls -la "${SKILL_DIR}/" || true
    exit 1
fi

# Verify python can run it
python "${SKILL_DIR}/learning_checkin.py" --help 2>/dev/null || true
echo "Skill setup complete."
echo "Skill path: ${SKILL_DIR}"