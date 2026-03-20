#!/bin/bash
API_BASE="http://11.11.24.2:8200/v1"
MODEL="Qwen3.5-9B"
RUN_DIR="results/Qwen3.5-9B_full"
total=0; evaluated=0; skipped=0

for inst in instances/*/; do
    inst=${inst%/}
    total=$((total+1))
    # Only evaluate successfully built instances
    status=$(python3 -c "import json; d=json.load(open('$inst/task.json')); print(d.get('build_status',''))" 2>/dev/null || echo "")
    if [ "$status" != "success" ]; then
        echo "SKIP (not built): $(basename $inst)"
        skipped=$((skipped+1))
        continue
    fi
    # Skip already evaluated instances
    result_file="$RUN_DIR/$(basename $inst)/result.json"
    if [ -f "$result_file" ]; then
        echo "SKIP (already evaluated): $(basename $inst)"
        evaluated=$((evaluated+1))
        continue
    fi
    echo "=== Evaluating: $(basename $inst) ==="
    uv run python agent_runner.py --instance "$inst" \
        --api-base "$API_BASE" --model "$MODEL" \
        --run-dir "$RUN_DIR" --cleanup || true
    evaluated=$((evaluated+1))
done
echo "=== Evaluate complete: $evaluated evaluated, $skipped skipped (of $total total) ==="

# Summary report
uv run python -c "
import json, os
from pathlib import Path
from collections import defaultdict

run_dir = Path('$RUN_DIR')
if not run_dir.exists():
    print('No results directory found.')
    exit()

# Collect results
results = []
for d in sorted(run_dir.iterdir()):
    rf = d / 'result.json'
    if not rf.exists():
        continue
    r = json.loads(rf.read_text())
    # Parse skill and difficulty from instance_id
    iid = r.get('instance_id', d.name)
    parts = iid.rsplit('_', 2)
    if len(parts) >= 3:
        skill = '_'.join(parts[:-2])
        difficulty = parts[-2]
    else:
        skill = iid
        difficulty = 'unknown'
    results.append({
        'instance_id': iid,
        'skill': skill,
        'difficulty': difficulty,
        'passed': r.get('passed', False),
        'score': r.get('score', 0.0),
    })

if not results:
    print('No results found.')
    exit()

# Overall
total = len(results)
passed = sum(1 for r in results if r['passed'])
avg_score = sum(r['score'] for r in results) / total
print(f'\n===== OVERALL: {passed}/{total} passed, avg score: {avg_score:.3f} =====\n')

# By skill
by_skill = defaultdict(list)
for r in results:
    by_skill[r['skill']].append(r)
print(f'{\"Skill\":<35} {\"Pass\":>6} {\"Total\":>6} {\"Rate\":>7} {\"AvgScore\":>9}')
print('-' * 65)
for skill in sorted(by_skill):
    rs = by_skill[skill]
    p = sum(1 for r in rs if r['passed'])
    t = len(rs)
    rate = p / t if t else 0
    avg = sum(r['score'] for r in rs) / t
    print(f'{skill:<35} {p:>6} {t:>6} {rate:>7.1%} {avg:>9.3f}')

# By difficulty
print()
by_diff = defaultdict(list)
for r in results:
    by_diff[r['difficulty']].append(r)
print(f'{\"Difficulty\":<15} {\"Pass\":>6} {\"Total\":>6} {\"Rate\":>7} {\"AvgScore\":>9}')
print('-' * 45)
for diff in ['easy', 'medium', 'hard']:
    if diff not in by_diff:
        continue
    rs = by_diff[diff]
    p = sum(1 for r in rs if r['passed'])
    t = len(rs)
    rate = p / t if t else 0
    avg = sum(r['score'] for r in rs) / t
    print(f'{diff:<15} {p:>6} {t:>6} {rate:>7.1%} {avg:>9.3f}')
print()
"
