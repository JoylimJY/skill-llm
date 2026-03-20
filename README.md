# SkillLLM

从技能定义自动合成评测任务，在 Docker 沙箱中运行 Agent，并评测其完成质量。

## 架构总览

```
SKILL.md ──→ Claude API ──→ Instance Dir ──→ Docker Build ──→ Agent Loop ──→ Eval
 (技能定义)    (synthesize)    (任务产物)       (沙箱环境)     (多轮交互)    (自动评分)
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
  ├── schema.py             # InstanceSpec + EvalResult + RunSummary 数据类
  └── run.py                # CLI: synthesize / build / evaluate / destroy / cleanup / all
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
├── task.json
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

### 2. 构建环境 + Agent 交互 (Build + Run)

```bash
# 构建 Docker 镜像 + 创建容器 + 运行 gen_inputs.py + setup.sh
uv run python -m src.run build --instance instances/pdf_merge_easy_000

# Agent 多轮交互完成任务 (结果保存到 results/{run_name}/)
uv run python agent_runner.py --instance instances/pdf_merge_easy_000 \
    --api-base http://localhost:8100/v1 \
    --model Qwen/Qwen3-8B \
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

### 3. 评测 (Evaluate)

```bash
uv run python -m src.run evaluate --instance instances/pdf_merge_easy_000 \
    --run-dir results/Qwen3-8B_round1
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

### 4. 清理容器 (Cleanup)

评测完成后，清理所有 skillbench 容器：

```bash
# 清理所有 skillbench 容器 + 残留的 container.json
uv run python -m src.run cleanup

# 清理单个实例的容器
uv run python -m src.run destroy --instance instances/pdf_merge_easy_000
```

`agent_runner.py` 也支持 `--cleanup` 参数，在评测结束后自动清理容器：

```bash
uv run python agent_runner.py --instance instances/pdf_merge_easy_000 \
    --api-base http://localhost:8100/v1 \
    --model Qwen/Qwen3-8B \
    --run-dir results/Qwen3-8B_round1 \
    --cleanup
```

## 一键执行

`all` 子命令串联合成 → 构建 → 评测 → 清理全流程（每个实例评测后自动销毁容器）：

```bash
uv run python -m src.run all --skill-dir anthropic-skills/pdf --num 6 \
    --run-dir results/my_run
```

## CLI 参考

| 命令 | 说明 |
|------|------|
| `uv run python -m src.run synthesize --skill-dir <dir> --num <n>` | 合成 n 个任务实例 |
| `uv run python -m src.run build --instance <dir>` | 构建 Docker 镜像 + 创建容器 |
| `uv run python -m src.run evaluate --instance <dir> --run-dir <dir>` | 运行评测 |
| `uv run python -m src.run destroy --instance <dir>` | 销毁单个实例容器 |
| `uv run python -m src.run cleanup` | 清理所有 skillbench 容器 |
| `uv run python -m src.run all --skill-dir <dir> --num <n> --run-dir <dir>` | 全流程一键执行 |
| `uv run python agent_runner.py --instance <dir> --api-base <url> --model <name>` | Agent 交互评测 |

## 快速开始

```bash
# 0. 安装依赖
uv sync

# 1. 启动模型服务
CUDA_VISIBLE_DEVICES=4 vllm serve Qwen/Qwen3-8B --port 8100 --max-model-len 8192

# 2. 构建 + Agent 交互 + 评测（--cleanup 自动清理容器）
uv run python -m src.run build --instance instances/pdf_merge_easy_000
uv run python agent_runner.py --instance instances/pdf_merge_easy_000 \
    --api-base http://localhost:8100/v1 --model Qwen/Qwen3-8B \
    --run-dir results/Qwen3-8B_exp1 --cleanup

# 3. 查看当轮统计
cat results/Qwen3-8B_exp1/summary.json

# 4. 或批量清理所有残留容器
uv run python -m src.run cleanup
```

## 依赖

项目依赖在 `pyproject.toml` 中声明，由 `uv` 管理：

- `anthropic >= 0.85.0` — Claude API (合成阶段)
- `openai >= 0.29.0` — OpenAI-compatible API (Agent 调用)
- Docker — 沙箱环境
- vLLM 或任何 OpenAI-compatible API — 模型服务
