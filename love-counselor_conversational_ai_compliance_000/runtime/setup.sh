#!/bin/bash
set -e

chmod -R 755 /workspace

echo "Workspace ready. Incoming sessions:"
ls /workspace/sessions/incoming/

echo ""
echo "Task environment initialized."