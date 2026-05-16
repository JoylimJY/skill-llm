#!/usr/bin/env bash
set -e

chmod +x /workspace/email-marketing/scripts/check_replies.py
chmod +x /workspace/email-marketing/scripts/auto_reply_manager.py
chmod +x /workspace/email-marketing/scripts/final_sender.py
chmod +x /workspace/email-marketing/scripts/check_setup.py

echo "=== Workspace ready ==="
echo "Key files:"
ls /workspace/Desktop/
echo ""
echo "Email marketing scripts:"
ls /workspace/email-marketing/scripts/
echo ""
echo "Assets:"
ls /workspace/email-marketing/assets/