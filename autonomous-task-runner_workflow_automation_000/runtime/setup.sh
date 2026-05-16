#!/bin/bash
set -e

# Make scripts executable
find /workspace/scripts -name "*.sh" -exec chmod +x {} \;

# Verify pre-seeded queue file is in place
QUEUE_FILE="$HOME/.openclaw/tasks/task-queue.json"
if [ -f "$QUEUE_FILE" ]; then
    echo "✓ Pre-seeded queue file found at $QUEUE_FILE"
    echo "  Current lastId: $(jq -r '.lastId' $QUEUE_FILE)"
    echo "  Tasks in queue: $(jq '.tasks | length' $QUEUE_FILE)"
else
    echo "✗ ERROR: Pre-seeded queue file missing!"
    exit 1
fi

# Verify HEARTBEAT.md exists (without Task Runner entry)
HEARTBEAT="/workspace/HEARTBEAT.md"
if [ -f "$HEARTBEAT" ]; then
    echo "✓ HEARTBEAT.md exists (without Task Runner entry)"
    if grep -q "Task Runner Dispatcher" "$HEARTBEAT"; then
        echo "  WARNING: Task Runner Dispatcher already in HEARTBEAT.md (should not be)"
    else
        echo "  ✓ Task Runner Dispatcher NOT yet in HEARTBEAT.md (correct)"
    fi
fi

echo "Setup complete."