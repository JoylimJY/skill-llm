#!/usr/bin/env bash
set -e

WORKSPACE="${WORKSPACE:-/workspace}"

# Ensure follow_ups directory exists and is writable
mkdir -p "$WORKSPACE/follow_ups"
chmod -R 755 "$WORKSPACE"

# Write a clear reference date file so the agent knows what "today" is
echo "2026-03-10" > "$WORKSPACE/data/today.txt"

echo "Setup complete. Reference date: $(cat $WORKSPACE/data/today.txt)"