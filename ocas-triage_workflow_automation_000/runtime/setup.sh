#!/usr/bin/env bash
set -e

# Ensure .triage directory permissions are correct
chmod -R 755 /workspace/.triage
chmod 644 /workspace/.triage/queue.jsonl
chmod 644 /workspace/.triage/signals.jsonl
chmod 644 /workspace/.triage/decisions.jsonl
chmod 644 /workspace/.triage/history.jsonl
chmod 644 /workspace/.triage/config.json
chmod 644 /workspace/.triage/incoming_request.json

# Make journals directory writable
chmod 777 /workspace/.triage/journals
chmod 777 /workspace/.triage/reports

echo "[setup] Workspace ready. Triage queue is in post-crash inconsistent state."
echo "[setup] Incoming urgent request is at /workspace/.triage/incoming_request.json"
echo "[setup] Agent must reconcile queue and process the incoming request."