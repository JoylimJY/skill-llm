# SkillLLM

从技能定义自动合成评测任务，在 Docker 沙箱中运行 Agent，并评测其完成质量。

## 架构总览

```
SKILL.md ──→ Claude API ──→ Instance Dir ──→ Docker Build ──→ Agent Loop ──→ Eval
 (技能定义)    (synthesize)    (任务产物)       (沙箱环境)     (多轮交互)    (自动评分)
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
  ├── sandbox.py            # Docker CLI 封装 (build / run / exec / cp / destroy)
  ├── evaluator.py          # 在容器内运行 eval.py，解析 JSON 评分结果
  ├── schema.py             # InstanceSpec + EvalResult 数据类
  └── run.py                # CLI: synthesize / build / evaluate / destroy / all
agent_runner.py             # Agent 多轮交互驱动 (接 OpenAI-compatible API)
instances/                  # 生成的任务实例
```

## 流程分三步

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
python -m src.run synthesize --skill-dir anthropic-skills/pdf --num 6
```

### 2. 构建环境 + Agent 交互 (Build + Run)

```bash
# 构建 Docker 镜像 + 创建容器 + 运行 gen_inputs.py + setup.sh
python -m src.run build --instance instances/pdf_merge_easy_000

# Agent 多轮交互完成任务
python agent_runner.py --instance instances/pdf_merge_easy_000 \
    --api-base http://localhost:8100/v1 \
    --model Qwen/Qwen3-8B
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
python -m src.run evaluate --instance instances/pdf_merge_easy_000
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

## Case: `pdf_merge_easy_000`

**task.json prompt:**
> I have three PDF files (doc1.pdf, doc2.pdf, doc3.pdf) that I need to combine into a single document called 'merged_report.pdf'. Please merge them in order.

**gen_inputs.py** 生成 3 个 PDF，每个嵌入 marker (`DOC1_CONTENT_MARKER` 等)。

**Agent 交互示例 (理想流程):**

```
[Turn 1] Model → ls /workspace
         Output → doc1.pdf  doc2.pdf  doc3.pdf  gen_inputs.py  setup.sh

[Turn 2] Model → python3 -c "
           from pypdf import PdfReader, PdfWriter
           writer = PdfWriter()
           for f in ['doc1.pdf','doc2.pdf','doc3.pdf']:
               reader = PdfReader(f)
               for page in reader.pages:
                   writer.add_page(page)
           writer.write('merged_report.pdf')
           print('Done')
         "
         Output → Done

[Turn 3] Model → TASK_COMPLETE
```

**eval.py 评分:**

| Check | 权重 | 验证内容 |
|-------|------|----------|
| merged_file_exists | 30% | `merged_report.pdf` 存在 |
| correct_page_count | 30% | 页数 == 3 |
| all_content_present | 20% | 三个 marker 全部出现 |
| correct_merge_order | 20% | marker 按 DOC1→DOC2→DOC3 顺序 |

## 快速开始

```bash
# 1. 启动模型服务
CUDA_VISIBLE_DEVICES=4 vllm serve Qwen/Qwen3-8B --port 8100 --max-model-len 8192

# 2. 合成 + 构建 + Agent 交互 + 评测 (单个实例)
python -m src.run build --instance instances/pdf_merge_easy_000
python agent_runner.py --instance instances/pdf_merge_easy_000 \
    --api-base http://localhost:8100/v1 --model Qwen/Qwen3-8B
# agent_runner 会自动调用 evaluate 并输出评分

# 3. 清理
python -m src.run destroy --instance instances/pdf_merge_easy_000
```

## 依赖

- Python 3.11+, `anthropic` SDK (合成阶段), `openai` SDK (Agent 调用)
- Docker (沙箱)
- vLLM 或任何 OpenAI-compatible API (模型服务)
