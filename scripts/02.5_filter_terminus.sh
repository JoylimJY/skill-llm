#!/bin/bash
# ============================================================================
# Filter tasks using Terminus-2 style agent
# ============================================================================
# Run terminus_2 agent multiple times on each built instance.
# Discard tasks where ALL pass (too easy) or NONE pass (unsolvable).
#
# Configuration via environment variables:
#   TERMINUS_FILTER_INSTANCES_DIR - Target instances directory (default: instances)
#   TERMINUS_FILTER_PROVIDER      - LLM provider: openai or claude (default: openai)
#   TERMINUS_FILTER_MODEL         - Model name (default: Qwen3-8B)
#   TERMINUS_FILTER_API_BASE      - API base URL (default: http://localhost:8100/v1)
#   TERMINUS_FILTER_API_KEY       - API key (optional)
#   TERMINUS_FILTER_NUM_TRIALS    - Number of trials per instance (default: 16)
#   TERMINUS_FILTER_CONCURRENCY   - Concurrent workers (default: 4)
#   TERMINUS_FILTER_MAX_ITER      - Max iterations per trial (default: 30)
# ============================================================================

INSTANCES_DIR="${TERMINUS_FILTER_INSTANCES_DIR:-instances}"
PROVIDER="${TERMINUS_FILTER_PROVIDER:-openai}"
MODEL="${TERMINUS_FILTER_MODEL:-Qwen3-8B}"
API_BASE="${TERMINUS_FILTER_API_BASE:-http://localhost:8100/v1}"
API_KEY="${TERMINUS_FILTER_API_KEY:-}"
NUM_TRIALS="${TERMINUS_FILTER_NUM_TRIALS:-16}"
CONCURRENCY="${TERMINUS_FILTER_CONCURRENCY:-4}"
MAX_ITER="${TERMINUS_FILTER_MAX_ITER:-30}"

echo "=============================================="
echo "Task Filtering (Terminus-2 Agent)"
echo "=============================================="
echo "  Instances:    $INSTANCES_DIR"
echo "  Provider:     $PROVIDER"
echo "  Model:        $MODEL"
echo "  API Base:     $API_BASE"
echo "  Trials:       $NUM_TRIALS"
echo "  Concurrency:  $CONCURRENCY"
echo "  Max Iter:     $MAX_ITER"
echo "  Rule:         discard if ALL pass (too easy) or NONE pass (unsolvable)"
echo "=============================================="
echo ""

# Build command
CMD="uv run python -m src.run filter_terminus \
    --output-dir \"$INSTANCES_DIR\" \
    --provider \"$PROVIDER\" \
    --model \"$MODEL\" \
    --api-base \"$API_BASE\" \
    --num-trials \"$NUM_TRIALS\" \
    --concurrency \"$CONCURRENCY\" \
    --max-iterations \"$MAX_ITER\""

# Add API key if provided
if [ -n "$API_KEY" ]; then
    CMD="$CMD --api-key \"$API_KEY\""
fi

eval $CMD

# Print summary of all filter results
echo ""
echo "=============================================="
echo "Filter Status Summary"
echo "=============================================="
uv run python -c "
import json
from pathlib import Path
from collections import Counter

instances_dir = Path('$INSTANCES_DIR')
statuses = Counter()
for d in sorted(instances_dir.iterdir()):
    task_json = d / 'task.json'
    if not task_json.exists():
        continue
    data = json.loads(task_json.read_text())
    build = data.get('build_status', 'unknown')
    filt = data.get('filter_status', 'not_filtered')
    statuses[filt] += 1
    if filt != 'not_filtered':
        details = data.get('filter_details', {})
        n_passed = details.get('num_passed', '?')
        n_trials = details.get('num_trials', '?')
        print(f'  {d.name:<50} {filt:<12} {n_passed}/{n_trials} passed')

print()
print('Counts:')
for key in sorted(statuses):
    print(f'  {key}: {statuses[key]}')
"
