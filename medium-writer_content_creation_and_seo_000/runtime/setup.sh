#!/bin/bash
set -e

# Make workspace files readable
chmod -R 644 /workspace/content_brief.txt
chmod -R 644 /workspace/research_notes.txt
chmod -R 644 /workspace/drafts/broken_draft.md

echo "Setup complete. Workspace ready."