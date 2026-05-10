#!/bin/bash

# ============================================================================
# Terminus-2 Style Agent Evaluation Script
# ============================================================================
# This script runs the terminus_2 style agent on benchmark instances.
# 
# Configuration via environment variables:
#   TERMINUS_MODEL      - Model name (default: Qwen3-8B)
#   TERMINUS_API_BASE   - API base URL (default: http://localhost:8100/v1)
#   TERMINUS_RUN_DIR    - Results output directory (default: results/terminus_{MODEL})
#   TERMINUS_MAX_ITER   - Max iterations per task (default: 50)
#
# Usage:
#   ./03_evaluate_terminus.sh [TARGET_PATH]
# 
# Examples:
#   1. Evaluate a single instance:
#      ./03_evaluate_terminus.sh instances/bitwarden_list_easy_001
#   2. Evaluate a whole directory of instances:
#      ./03_evaluate_terminus.sh instances/
#   3. With specific model:
#      TERMINUS_MODEL=Qwen3.5-9B ./03_evaluate_terminus.sh instances/my_task
# ============================================================================

# 获取命令行传入的第一个参数作为目标路径，如果不传，默认使用 instances 目录
TARGET_PATH="${1:-instances}"

# Configuration from environment variables
MODEL="${TERMINUS_MODEL:-Qwen3-8B}"
PROVIDER="${TERMINUS_PROVIDER:-openai}"
API_BASE="${TERMINUS_API_BASE:-http://localhost:8100/v1}"
API_KEY="${TERMINUS_API_KEY:-}"
RUN_DIR="${TERMINUS_RUN_DIR:-results/terminus_${MODEL}}"
MAX_ITER="${TERMINUS_MAX_ITER:-32}"

echo "=============================================="
echo "Terminus-2 Style Agent Evaluation"
echo "=============================================="
echo "Provider:   $PROVIDER"
echo "Model:      $MODEL"
echo "API Base:   $API_BASE"
echo "Target:     $TARGET_PATH"
echo "Run Dir:    $RUN_DIR"
echo "Max Iter:   $MAX_ITER"
echo "=============================================="
echo ""

total=0
evaluated=0
skipped=0
failed=0

# Check if target path exists
if [ ! -d "$TARGET_PATH" ]; then
    echo "Error: Target directory '$TARGET_PATH' not found"
    exit 1
fi

# 智能判断：如果目录下有 task.json，说明传的是单个实例；否则说明是包含多个实例的父目录
if [ -f "$TARGET_PATH/task.json" ]; then
    echo "Mode: Single Instance Evaluation"
    INSTANCES=("$TARGET_PATH")
else
    echo "Mode: Batch Directory Evaluation"
    INSTANCES=("$TARGET_PATH"/*/)
fi

for inst in "${INSTANCES[@]}"; do
    if [ ! -d "$inst" ]; then
        echo "No valid instances found in $TARGET_PATH"
        continue
    fi
    
    inst=${inst%/}
    INSTANCE_NAME=$(basename "$inst")
    total=$((total+1))
    
    # Only evaluate successfully built instances
    status=$(python3 -c "import json; d=json.load(open('$inst/task.json')); print(d.get('build_status',''))" 2>/dev/null || echo "")
    if [ "$status" != "success" ]; then
        echo "SKIP (not built): $INSTANCE_NAME"
        skipped=$((skipped+1))
        continue
    fi
    
    # Skip filtered instances
    filter_status=$(python3 -c "import json; d=json.load(open('$inst/task.json')); print(d.get('filter_status',''))" 2>/dev/null || echo "")
    if [ "$filter_status" = "too_easy" ] || [ "$filter_status" = "unsolvable" ]; then
        echo "SKIP (filtered: $filter_status): $INSTANCE_NAME"
        skipped=$((skipped+1))
        continue
    fi
    
    # Skip already evaluated instances
    result_file="$RUN_DIR/$INSTANCE_NAME/result.json"
    if [ -f "$result_file" ]; then
        echo "SKIP (already evaluated): $INSTANCE_NAME"
        evaluated=$((evaluated+1))
        continue
    fi
    
    echo "=== Evaluating: $INSTANCE_NAME ==="
    
    # Build command with optional arguments
    CMD="uv run python agent_runner_terminus.py \
        --instance \"$inst\" \
        --provider \"$PROVIDER\" \
        --model \"$MODEL\" \
        --run-dir \"$RUN_DIR\" \
        --max-iterations \"$MAX_ITER\" \
        --cleanup"
    
    # Add API base if provided
    if [ -n "$API_BASE" ]; then
        CMD="$CMD --api-base \"$API_BASE\""
    fi
    
    # Add API key if provided
    if [ -n "$API_KEY" ]; then
        CMD="$CMD --api-key \"$API_KEY\""
    fi
    
    # --- 核心修改：将日志保存到指定的 results 目录下 ---
    INSTANCE_RUN_DIR="$RUN_DIR/$INSTANCE_NAME"
    # 必须提前创建目录，否则 tee 写入文件时会报错找不到路径
    mkdir -p "$INSTANCE_RUN_DIR"
    
    LOG_FILE="$INSTANCE_RUN_DIR/agent_eval.log"
    echo "  -> Logging to: $LOG_FILE"
    
    eval $CMD 2>&1 | tee "$LOG_FILE"
    
    EXIT_CODE=${PIPESTATUS[0]}
    
    if [ $EXIT_CODE -eq 0 ]; then
        evaluated=$((evaluated+1))
    else
        echo "FAILED: $INSTANCE_NAME"
        failed=$((failed+1))
    fi
done

echo ""
echo "=============================================="
echo "Evaluation Complete"
echo "=============================================="
echo "Total:     $total"
echo "Evaluated: $evaluated"    
echo "Skipped:   $skipped"
echo "Failed:    $failed"
echo "=============================================="

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