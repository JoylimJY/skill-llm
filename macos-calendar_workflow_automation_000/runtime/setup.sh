#!/usr/bin/env bash
set -e

WORKSPACE=/workspace
SKILL_DIR="$WORKSPACE/skills/macos-calendar"

# Ensure calendar.sh is executable
chmod +x "$SKILL_DIR/scripts/calendar.sh"

# Ensure logs directory is writable and empty (clean state)
mkdir -p "$SKILL_DIR/logs"
rm -f "$SKILL_DIR/logs/capture.jsonl"
rm -f "$SKILL_DIR/logs/calendar.log"
touch "$SKILL_DIR/logs/capture.jsonl"
touch "$SKILL_DIR/logs/calendar.log"

# Export SKILL_DIR for any child processes (write to profile)
echo "export SKILL_DIR=\"$SKILL_DIR\"" >> /etc/profile
echo "export SKILL_DIR=\"$SKILL_DIR\"" >> /root/.bashrc

echo "Setup complete. SKILL_DIR=$SKILL_DIR"
echo "Calendar script ready at: $SKILL_DIR/scripts/calendar.sh"