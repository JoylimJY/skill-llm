#!/bin/bash
set -e

# Make mock ACP tools executable
chmod +x /workspace/.acp_mock/sessions_spawn.py
chmod +x /workspace/.acp_mock/sessions_list.py
chmod +x /workspace/.acp_mock/sessions_yield.py
chmod +x /workspace/.acp_mock/sessions_history.py

# Create symlinks so tools are available as commands in PATH
ln -sf /workspace/.acp_mock/sessions_spawn.py /usr/local/bin/sessions_spawn
ln -sf /workspace/.acp_mock/sessions_list.py /usr/local/bin/sessions_list
ln -sf /workspace/.acp_mock/sessions_yield.py /usr/local/bin/sessions_yield
ln -sf /workspace/.acp_mock/sessions_history.py /usr/local/bin/sessions_history

# Ensure call_log exists and is writable
touch /workspace/call_log.jsonl
chmod 666 /workspace/call_log.jsonl
chmod 666 /workspace/.acp_mock/state.json

# Ensure tmp dir for acp logs
mkdir -p /tmp/acp

echo "ACP mock tools installed."
echo "Available commands: sessions_spawn, sessions_list, sessions_yield, sessions_history"
echo "All calls will be logged to /workspace/call_log.jsonl"