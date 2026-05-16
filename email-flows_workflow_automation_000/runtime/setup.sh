#!/usr/bin/env bash
set -e

# No mock servers needed. Ensure workspace permissions are correct.
chmod -R 755 /workspace

echo "Setup complete. Workspace is ready."
echo "Agent should read /workspace/context_brief.txt and produce email_sequences.md"