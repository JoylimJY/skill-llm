#!/bin/bash
# Filter tasks: run agent 16 times on each built instance.
# Discard tasks where ALL 16 pass (too easy) or NONE pass (unsolvable).

API_BASE="${FILTER_API_BASE:-http://11.11.24.2:8200/v1}"
MODEL="${FILTER_MODEL:-Qwen3.5-27B}"
NUM_TRIALS="${FILTER_NUM_TRIALS:-16}"
CONCURRENCY="${FILTER_CONCURRENCY:-4}"

echo "=== Task Filtering ==="
echo "  Model:        $MODEL"
echo "  API Base:     $API_BASE"
echo "  Trials:       $NUM_TRIALS"
echo "  Concurrency:  $CONCURRENCY"
echo "  Rule:         discard if ALL pass (too easy) or NONE pass (unsolvable)"
echo ""

uv run python -m src.run filter \
    --output-dir instances \
    --api-base "$API_BASE" \
    --model "$MODEL" \
    --num-trials "$NUM_TRIALS" \
    --concurrency "$CONCURRENCY"

# Print summary of all filter results
echo ""
echo "=== Filter Status Summary ==="
uv run python -c "
import json
from pathlib import Path
from collections import Counter

instances_dir = Path('instances')
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
