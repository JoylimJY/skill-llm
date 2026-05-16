#!/bin/bash
set -e

chmod +x /workspace/scripts/fetch_evals.sh 2>/dev/null || true

echo "Workspace ready. Key files:"
echo "  - /workspace/data/raw_evals/daily_eval_dump_2025-07-08.json  (main input)"
echo "  - /workspace/config/openclaw_config.json  (platform config)"
echo "  - /workspace/notes/team_notes.txt"