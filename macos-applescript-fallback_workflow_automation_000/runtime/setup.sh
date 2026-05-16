#!/usr/bin/env bash
set -e

# Make all mock scripts executable
chmod +x /workspace/scripts/create_reminder.sh
chmod +x /workspace/scripts/create_note.sh
chmod +x /workspace/scripts/create_calendar_event.sh
chmod +x /workspace/scripts/send_imessage.sh
chmod +x /workspace/scripts/archive/old_create_note.sh
chmod +x /workspace/scripts/utils/check_perms.sh

# Ensure logs directory exists and is writable
mkdir -p /workspace/logs
chmod 777 /workspace/logs

echo "Setup complete. Mock scripts are executable."