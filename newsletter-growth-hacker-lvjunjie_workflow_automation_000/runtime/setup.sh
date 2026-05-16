#!/bin/bash
set -e

SKILL_DIR="/workspace/skills/newsletter-growth-hacker/scripts"
chmod +x "$SKILL_DIR/main.py" 2>/dev/null || true

# Verify scripts exist
for f in subscriber_acquisition.py content_optimizer.py analytics_engine.py main.py; do
    if [ ! -f "$SKILL_DIR/$f" ]; then
        echo "ERROR: $SKILL_DIR/$f missing!"
        exit 1
    fi
done

echo "Setup complete. Skill scripts verified."