#!/usr/bin/env bash
set -e

# Ensure workspace permissions are correct
chmod -R 755 /workspace

echo "Sandbox initialized. Workspace is ready at /workspace."
echo "Task file: /workspace/task.txt"
echo "Input file: /workspace/stakeholder/emails/pending/david_export_request.txt"