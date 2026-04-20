# SkillLLM

从技能定义自动合成评测任务，在 Docker 沙箱中运行 Agent，并评测其完成质量。

## 架构总览

```
SKILL.md ──→ Claude API ──→ Instance Dir ──→ Docker Build ──→ Filter ──→ Agent Loop ──→ Eval
 (技能定义)    (synthesize)    (任务产物)       (沙箱环境)    (质量过滤)    (多轮交互)    (自动评分)
```

## 环境配置

### 前置依赖

- Python >= 3.12
- Docker
- [uv](https://docs.astral.sh/uv/) (Python 包管理器)
- vLLM 或任何 OpenAI-compatible API (模型服务)

### 安装 uv

```bash
# Linux / macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或通过 pip
pip install uv
```

### 初始化项目

```bash
# 克隆项目后，在项目根目录执行：
uv sync
```

`uv sync` 会根据 `pyproject.toml` 和 `uv.lock` 自动创建虚拟环境并安装所有依赖（`anthropic`、`openai` 等）。

> **注意：** 后续所有 Python 命令均通过 `uv run python` 执行，无需手动激活虚拟环境。

### 环境变量

合成阶段需要 Anthropic API Key：

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 目录结构

```
anthropic-skills/           # 技能定义 (18 个)
  └── pdf/
      ├── SKILL.md          # 技能入口，定义能力范围和用法
      ├── reference.md      # 详细参考
      └── forms.md          # 子能力说明
src/
  ├── synthesizer.py        # 读取 SKILL.md → 调 Claude API → 生成 InstanceSpec → 写磁盘
  ├── sandbox.py            # Docker CLI 封装 (build / run / exec / cp / destroy / cleanup)
  ├── evaluator.py          # 在容器内运行 eval.py，解析 JSON 评分结果
  ├── filter.py             # 任务质量过滤：多次运行 Agent，全对/全错的任务被丢弃
  ├── agent_runner_lib.py   # Agent 交互核心逻辑（供 filter.py 调用的库版本）
  ├── schema.py             # InstanceSpec + EvalResult + FilterResult + RunSummary 数据类
  ├── prompts.py            # Prompt 模板加载器
  └── run.py                # CLI: synthesize / build / filter / evaluate / destroy / cleanup / all
scripts/
  ├── 01_synthesize.sh      # 批量合成：遍历所有 skill，每个生成 6 个 instance
  ├── 02_build.sh           # 批量构建：遍历所有 instance，构建 Docker 镜像
  ├── 02.5_filter.sh        # 批量过滤：对已构建的 instance 运行 16 次 Agent，过滤质量不合格的任务
  └── 03_evaluate.sh        # 批量评测：用 Agent 完成任务并评分
prompts/
  ├── synthesis.txt         # 合成 prompt 模板
  ├── fix_dockerfile.txt    # Dockerfile 修复 prompt
  └── agent_system.txt      # Agent system prompt
agent_runner.py             # Agent 多轮交互驱动 (接 OpenAI-compatible API)
instances/                  # 任务定义 (不可变，不含评测结果)
results/                    # 评测结果 (按轮次组织)
pyproject.toml              # 项目配置 & 依赖声明
uv.lock                    # 依赖锁定文件
```

### 任务与结果分离

`instances/` 只包含不可变的任务定义，评测结果和交互记录保存在 `results/` 下，按轮次（run）组织：

```
instances/{instance_id}/          # 任务定义 (不可变)
├── task.json                     # 元信息: instance_id, skill_name, prompt, difficulty, category
│                                 #   build_status: success / failed
│                                 #   filter_status: kept / too_easy / unsolvable (过滤后)
│                                 #   filter_details: {num_trials, num_passed, pass_rate, trial_scores, model}
├── runtime/
│   ├── Dockerfile
│   ├── gen_inputs.py
│   ├── setup.sh
│   └── workspace/
└── eval/
    ├── eval.py
    └── expected.json

results/{run_name}/               # 一次评测轮次的所有结果
├── summary.json                  # 当轮统计: total, passed, avg_score, 各实例得分
├── {instance_id}/
│   ├── result.json               # 评测结果 (passed, score, checks)
│   └── conversation.json         # Agent 多轮交互记录
└── ...
```

`run_name` 默认为 `{model}_{timestamp}`，可通过 `--run-dir` 指定。

## 使用流程

### 1. 合成任务 (Synthesize)

读取 `SKILL.md` + 引用的子文件，调用 Claude API (`claude-sonnet-4-20250514`)，一次性生成：

| 产物 | 路径 | 作用 |
|------|------|------|
| 任务描述 | `task.json` | 自然语言 prompt + 元信息 (难度/分类) |
| 运行环境 | `runtime/Dockerfile` | 基于 `python:3.11-slim`，含所有依赖 |
| 输入生成 | `runtime/gen_inputs.py` | 确定性生成输入文件，内嵌 marker 用于验证 |
| 初始化 | `runtime/setup.sh` | 容器启动后的额外设置 |
| 评测脚本 | `eval/eval.py` | 检查产出文件，输出 `{passed, score, checks}` JSON |
| 预期输出 | `eval/expected.json` | 期望的文件名/属性/内容 |

难度分布：easy / medium / hard 均匀分配。

```bash
uv run python -m src.run synthesize --skill-dir anthropic-skills/pdf --num 6
```

### 2. 构建环境 (Build)

构建 Docker 镜像 + 创建容器 + 运行 gen_inputs.py + setup.sh。构建失败时自动调用 Claude 修复 Dockerfile（最多重试 3 次）。

```bash
uv run python -m src.run build --instance instances_awesome-claude-skills-master/artifacts-builder_create_hard_005
```

### 3. 任务质量过滤 (Filter)

在构建成功后、正式评测前，用一个小模型（如 Qwen3.5-27B）对每个 instance 运行多次 Agent。根据通过情况过滤掉质量不合格的任务：

- **16 次全部通过** → 标记为 `too_easy`（太简单，丢弃）
- **16 次全部失败** → 标记为 `unsolvable`（不可解，丢弃）
- **其他** → 标记为 `kept`（保留）

每次 trial 复用已构建的 Docker 镜像，但创建独立的新容器，确保环境互不干扰。支持可配置的并行数。

```bash
# 过滤所有已构建的 instance（默认 16 次 trial，4 并行）
uv run python -m src.run filter \
    --api-base http://localhost:8200/v1 \
    --model Qwen3.5-27B \
    --output-dir instances_anthropic-skills

# 过滤单个 instance
uv run python -m src.run filter \
    --instance instances/pdf_merge_easy_000 \
    --api-base http://localhost:8200/v1 \
    --model Qwen3.5-27B

# 自定义参数
uv run python -m src.run filter \
    --api-base http://localhost:8200/v1 \
    --model Qwen3.5-27B \
    --num-trials 16 \
    --concurrency 8 \
    --force  # 重新过滤已过滤的 instance
```

过滤结果写入 `task.json` 的 `filter_status` 字段，后续 `evaluate` 和 `agent_runner.py` 自动跳过被过滤的 instance。

### 4. Agent 交互 + 评测 (Run + Evaluate)

```bash
# Agent 多轮交互完成任务 (结果保存到 results/{run_name}/)
uv run python agent_runner.py --instance instances_stage1-final/algorithmic-art_create_easy_000 \
    --api-base http://localhost:8300/v1 \
    --model Qwen3.5-27B \
    --run-dir results/test

# 或仅运行评测（需要容器已存在）
uv run python -m src.run evaluate --instance instances/pdf_merge_easy_000 \
    --run-dir results/Qwen3-8B_round1
```

Agent 交互流程：

```
System Prompt (角色 + 规则)
    │
    ├─→ Model: 生成 ```bash 或 ```python 代码块
    │     ↓
    ├─→ Harness: 提取代码 → docker exec 执行 → 返回 stdout/stderr
    │     ↓
    ├─→ Model: 根据输出决定下一步
    │     ↓
    └─→ 重复直到 Model 输出 "TASK_COMPLETE" 或达到 max_turns
```

`eval.py` 在容器内执行，针对 `/workspace` 检查产出。输出格式：

```json
{
  "passed": true,
  "score": 0.85,
  "checks": [
    {"name": "merged_file_exists", "passed": true, "detail": "merged_report.pdf found"},
    {"name": "correct_page_count", "passed": true, "detail": "3 pages as expected"},
    {"name": "all_content_present", "passed": true, "detail": "All markers found"},
    {"name": "correct_merge_order", "passed": false, "detail": "DOC2 appears before DOC1"}
  ]
}
```

### 5. 清理容器 (Cleanup)

```bash
# 清理所有 skillbench 容器 + 残留的 container.json
uv run python -m src.run cleanup

# 清理单个实例的容器
uv run python -m src.run destroy --instance instances/pdf_merge_easy_000
```

`agent_runner.py` 也支持 `--cleanup` 参数，在评测结束后自动清理容器。

## 一键执行

`all` 子命令串联 合成 → 构建 → 过滤 → 评测 全流程：

```bash
# 不含过滤（向后兼容）
uv run python -m src.run all --skill-dir anthropic-skills/pdf --num 6 \
    --run-dir results/my_run

# 含过滤步骤
uv run python -m src.run all --skill-dir anthropic-skills/pdf --num 6 \
    --run-dir results/my_run \
    --filter-api-base http://localhost:8200/v1 \
    --filter-model Qwen3.5-27B
```

## 批量脚本 (scripts/)

`scripts/` 目录下提供了端到端的批量执行脚本，按编号顺序依次运行：

### `01_synthesize.sh` — 批量合成

遍历 `anthropic-skills/` 下所有 skill 目录，每个生成 6 个 instance。已有足够实例的 skill 会自动跳过。

```bash
bash scripts/01_synthesize.sh
```

### `02_build.sh` — 批量构建

遍历 `instances/` 下所有 instance，构建 Docker 镜像（含 LLM 自动修复失败的 Dockerfile）。已构建成功的 instance 会自动跳过。

```bash
bash scripts/02_build.sh
```


### `02.5_filter.sh` — 批量过滤

对所有已构建成功的 instance 运行质量过滤。通过环境变量配置参数：

```bash
# 使用默认配置
bash scripts/02.5_filter.sh

# 自定义配置
FILTER_INSTANCES_DIR="instances_openclaw_skills_Clawdbot Tools" \
FILTER_API_BASE=http://localhost:8300/v1 \
FILTER_MODEL=Qwen3.5-27B \
FILTER_NUM_TRIALS=4 \
FILTER_CONCURRENCY=4 \
bash scripts/02.5_filter.sh 
```

脚本结束后会打印每个 instance 的过滤状态汇总表。

### `03_evaluate.sh` — 批量评测

使用 `agent_runner.py` 对所有已构建（且未被过滤）的 instance 运行 Agent 交互 + 评测。评测后自动清理容器。脚本结束后输出按 skill 和难度分组的统计报告。

```bash
bash scripts/03_evaluate.sh
```

> **注意：** `03_evaluate.sh` 中的 `API_BASE`、`MODEL`、`RUN_DIR` 变量需根据实际环境修改。

### 推荐执行顺序

```bash
bash scripts/01_synthesize.sh          # 1. 合成所有 skill 的任务
bash scripts/02_build.sh               # 2. 构建所有 Docker 环境
bash scripts/02.5_filter.sh            # 3. 过滤质量不合格的任务
bash scripts/03_evaluate.sh            # 4. 批量 Agent 交互 + 评测
```

## CLI 参考

| 命令 | 说明 |
|------|------|
| `python -m src.run synthesize --skill-dir <dir> --num <n>` | 合成 n 个任务实例 |
| `python -m src.run build --instance <dir>` | 构建 Docker 镜像 + 创建容器 |
| `python -m src.run filter --api-base <url> --model <name>` | 批量过滤：丢弃全对/全错的任务 |
| `python -m src.run filter --instance <dir> --api-base <url> --model <name>` | 过滤单个实例 |
| `python -m src.run evaluate --instance <dir> --run-dir <dir>` | 运行评测 |
| `python -m src.run destroy --instance <dir>` | 销毁单个实例容器 |
| `python -m src.run cleanup` | 清理所有 skillbench 容器 |
| `python -m src.run all --skill-dir <dir> --num <n> --run-dir <dir>` | 全流程一键执行 |
| `python agent_runner.py --instance <dir> --api-base <url> --model <name>` | Agent 交互评测 |

> 所有命令均通过 `uv run python` 执行。

## 快速开始

```bash
# 0. 安装依赖
uv sync

# 1. 启动模型服务
CUDA_VISIBLE_DEVICES=4 vllm serve Qwen/Qwen3-8B --port 8100 --max-model-len 8192

# 2. 构建 + Agent 交互 + 评测（--cleanup 自动清理容器）
uv run python -m src.run build --instance instances/pdf_merge_easy_000
uv run python agent_runner.py --instance "instances_too_easy_for_9b/canvas-design_create_easy_000 copy" \
    --api-base http://localhost:8300/v1 --model Qwen3.5-9B \
    --run-dir results/Qwen3-8B_exp1 --cleanup --force

# 3. 查看当轮统计
cat results/Qwen3-8B_exp1/summary.json

# 4. 或批量清理所有残留容器
uv run python -m src.run cleanup
```

## 依赖

项目依赖在 `pyproject.toml` 中声明，由 `uv` 管理：

- `anthropic >= 0.85.0` — Claude API (合成阶段)
- `openai >= 2.29.0` — OpenAI-compatible API (Agent 调用)
- Docker — 沙箱环境
- vLLM 或任何 OpenAI-compatible API — 模型服务

uv run python -m src.run filter \
  --api-base http://localhost:8300/v1 \
  --model Qwen3.5-27B \
  --output-dir instances_stage1-final \
  --num-trials 4 \
  --concurrency 4

uv run python -m src.run synthesize \
    --skill-dir awesome-claude-skills-master/artifacts-builder \
    --num 1 \
    --output-dir temp_instances

docker run --gpus all \
    --ipc=host \
    -p 8300:8000 \
    -v /home/test/test12/models:/models \
    vllm/vllm-openai:latest \
    /models/Qwen3.5-27B \
    --served-model-name "Qwen3.5-27B" \
    --tensor-parallel-size 8 \
    --max-model-len 16384 \
    --gpu-memory-utilization 0.9 \
    --trust-remote-code \
    --reasoning-parser qwen3 \

TERMINUS_FILTER_INSTANCES_DIR="instances_openclaw_skills_Cli Utilities&Coding Agents And Ides" \
TERMINUS_FILTER_PROVIDER=openai \
TERMINUS_FILTER_MODEL=gpt-oss-120b \
TERMINUS_FILTER_API_BASE="***REMOVED***/v1" \
TERMINUS_FILTER_API_KEY="***REMOVED***" \
TERMINUS_FILTER_NUM_TRIALS=4 \
TERMINUS_FILTER_CONCURRENCY=4 \
bash scripts/02.5_filter_terminus.sh

python agent_runner_terminus.py \
    --instance "instances_openclaw_skills_Ai And Llms1/xiwan-agent-linguo_transform_hard_004" \
    --provider openai \
    --api-base http://localhost:8300/v1 \
    --model Qwen3.5-27B

python agent_runner_terminus.py \
    --instance "instances_openclaw_skills_Ai And Llms1/zoroposkai-anti-regression_create_hard_005" \
    --provider claude \
    --model claude-sonnet-4-20250514"

python agent_runner_terminus.py \
    --instance "instances_openclaw_skills_Browser And Automation/gekacross-personal-sleep_create_hard_004" \
    --provider openai \
    --model gpt-oss-120b \
    --api-base "***REMOVED***/v1" \
    --api-key "***REMOVED***"

export ANTHROPIC_BASE_URL="***REMOVED***"
export ANTHROPIC_AUTH_TOKEN="***REMOVED***"
