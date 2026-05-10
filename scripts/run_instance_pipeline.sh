#!/usr/bin/env bash
set -uo pipefail 

# ── 参数解析 ─────────────────────────────────────────────────────────────
INSTANCE_DIR="${1:?Usage: $0 <INSTANCE_DIR> [--keep] [--skip-solution]}"
shift
KEEP_CONTAINER=false
SKIP_SOLUTION=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --keep)           KEEP_CONTAINER=true ;;
        --skip-solution)  SKIP_SOLUTION=true ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# ── 路径与变量 ───────────────────────────────────────────────────────────
INSTANCE_NAME=$(basename "$INSTANCE_DIR")
_sanitize() { echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9_.-]/-/g' | tr -s '.-' '-' | sed 's/^[-.]*//; s/[-.]*$//'; }
IMAGE_TAG="sb-$(_sanitize "$INSTANCE_NAME")"
CONTAINER_NAME="sb-pipe-$(_sanitize "$INSTANCE_NAME")"

RUNTIME_DIR="$INSTANCE_DIR/runtime"
EVAL_DIR="$INSTANCE_DIR/eval"
TASK_JSON="$INSTANCE_DIR/task.json"

# ── 辅助函数 (保持简洁输出并捕获错误) ───────────────────────────────────────────
info() { echo -ne "\033[1;34m[..]\033[0m $1\r"; }
ok()   { echo -e "\033[1;32m[OK]\033[0m $1"; }
fail() { 
    echo -e "\033[1;31m[FAIL]\033[0m $1"
    [[ -f "${2:-}" ]] && echo -e "\n--- ERROR LOG (Last 30 lines) ---\n" && tail -n 30 "$2" && echo -e "\n--------------------------------\n"
    exit 1
}

# 模拟旧代码的命令执行与日志捕获
run_command() {
    local msg="$1"
    local cmd="$2"
    local log_file=$(mktemp)
    info "$msg"
    if eval "$cmd" > "$log_file" 2>&1; then
        ok "$msg"
        rm -f "$log_file"
    else
        fail "$msg" "$log_file"
    fi
}

cleanup() {
    if [[ "$KEEP_CONTAINER" == false ]] && docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
        docker rm -f "$CONTAINER_NAME" > /dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

# ── 核心流程 (严格遵循旧版逻辑顺序) ───────────────────────────────────────────
echo -e "\n\033[1;36m>>> Pipeline started:\033[0m $INSTANCE_NAME\n"

# 1. Docker Build
run_command "Docker Build" "docker build -t '$IMAGE_TAG' -f '$RUNTIME_DIR/Dockerfile' '$RUNTIME_DIR'"

# 2. Create & Start
run_command "Container Start" "docker run -d --name '$CONTAINER_NAME' -w /workspace '$IMAGE_TAG' tail -f /dev/null"

# 3. Seeding Workspace (这里是你的原始逻辑：逐个检查并 cp)

# 3a. Copy workspace scaffold
if [[ -d "$RUNTIME_DIR/workspace" ]] && [[ -n "$(ls -A "$RUNTIME_DIR/workspace" 2>/dev/null)" ]]; then
    docker cp "$RUNTIME_DIR/workspace/." "$CONTAINER_NAME:/workspace/" > /dev/null
    ok "Copy: workspace folder"
fi

# 3b. Copy skill_context (optional)
if [[ -d "$RUNTIME_DIR/skill_context" ]] && [[ -n "$(ls -A "$RUNTIME_DIR/skill_context" 2>/dev/null)" ]]; then
    docker cp "$RUNTIME_DIR/skill_context/." "$CONTAINER_NAME:/workspace/skill_context/" > /dev/null
    ok "Copy: skill_context"
fi

# 3c. gen_inputs.py (这是之前报错的关键：旧逻辑会检查并 cp 单个文件)
if [[ -f "$RUNTIME_DIR/gen_inputs.py" ]]; then
    docker cp "$RUNTIME_DIR/gen_inputs.py" "$CONTAINER_NAME:/workspace/gen_inputs.py" > /dev/null
    run_command "Exec: gen_inputs.py" "docker exec '$CONTAINER_NAME' python3 /workspace/gen_inputs.py"
fi

# 3d. setup.sh
if [[ -f "$RUNTIME_DIR/setup.sh" ]]; then
    docker cp "$RUNTIME_DIR/setup.sh" "$CONTAINER_NAME:/workspace/setup.sh" > /dev/null
    run_command "Exec: setup.sh" "docker exec '$CONTAINER_NAME' bash -c 'chmod +x /workspace/setup.sh && /workspace/setup.sh'"
fi

# 4. Solution (带保护的执行)
if [[ "$SKIP_SOLUTION" == true ]]; then
    ok "Solution (Skipped)"
else
    if [[ ! -f "$RUNTIME_DIR/solution.sh" ]]; then
        fail "Solution (solution.sh missing in $RUNTIME_DIR)"
    fi
    docker cp "$RUNTIME_DIR/solution.sh" "$CONTAINER_NAME:/workspace/solution.sh" > /dev/null
    run_command "Solution Execution" "docker exec '$CONTAINER_NAME' timeout 300s bash /workspace/solution.sh"
fi

# 5. Eval & Update task.json
info "Evaluation"
if [[ ! -f "$EVAL_DIR/eval.py" ]]; then
    fail "Evaluation (eval.py missing in $EVAL_DIR)"
fi
docker cp "$EVAL_DIR/eval.py" "$CONTAINER_NAME:/eval.py" > /dev/null

EVAL_LOG=$(mktemp)
if docker exec "$CONTAINER_NAME" python3 /eval.py /workspace > "$EVAL_LOG" 2>&1; then
    # 使用 Python 更新宿主机上的 task.json
    UPDATE_STATUS=$(python3 -c "
import json, sys
try:
    with open('$EVAL_LOG', 'r') as f:
        eval_data = json.load(f)
    with open('$TASK_JSON', 'r') as f:
        task_data = json.load(f)
    
    task_data['evaluation'] = {
        'score': eval_data.get('score', 0),
        'passed': eval_data.get('passed', False),
        'details': eval_data.get('checks', [])
    }
    
    with open('$TASK_JSON', 'w') as f:
        json.dump(task_data, f, indent=4)
    
    p = 'PASS' if eval_data.get('passed') else 'FAIL'
    print(f'SUCCESS|{p}|{eval_data.get(\"score\", 0)*100:.1f}%')
except Exception as e:
    print(f'ERROR|{str(e)}')
")

    if [[ "$UPDATE_STATUS" == ERROR* ]]; then
        fail "Evaluation (Update task.json failed: ${UPDATE_STATUS#ERROR|})" "$EVAL_LOG"
    else
        RES_INFO=${UPDATE_STATUS#SUCCESS|}
        ok "Evaluation: Result: ${RES_INFO%|*} | Score: ${RES_INFO#*|}"
        ok "Saved: task.json updated"
    fi
else
    fail "Evaluation (Script crashed)" "$EVAL_LOG"
fi
rm -f "$EVAL_LOG"

echo -e "\n\033[1;32m>>> Pipeline Finished Successfully.\033[0m\n"