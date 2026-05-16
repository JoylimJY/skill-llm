---
name: hive-builder
description: "🚀 在空白 OpenClaw 上从零构建 Hive 一人公司 · Build a complete Hive one-person company on a fresh OpenClaw. Orchestrator pattern: 1 CEO (main session) + HRM (hiring + workflow) + OPS (external matching) + N business specialists (subagents). All triggered via sessions_spawn."
---

# Hive Builder · Skill

## 目的 · Purpose

🚀 **在空白 OpenClaw 上从零构建 Hive 一人公司**

**Build a complete Hive one-person company from scratch** on a fresh OpenClaw.

Hive is built on the **Orchestrator pattern**: the CEO is the main session (main agent), and all specialists are subagents dispatched via `sessions_spawn`. As a one-person company, Hive gives one person the output of a full team — without hiring more humans.

扩员是 HRM 的内置职责，无需单独触发。
Expanding is **HRM's built-in job** — HRM is always active and handles new specialist hiring automatically. No separate scenario needed.

## Core Concept

```
Hive = 一家公司，基于 Orchestrator 模式构建
#0 CEO（指挥官） = 主会话（main session），编排中枢，最终审批权
#1 HRM（组织官） = 招聘官，负责扩员（内置职责）
#2 OPS（运维官） = 运维官，CEO发起才执行
新员工从 #3 开始
```

## Architecture · 运作机制

```
用户请求
    ↓
CEO（主会话）
    ├── 判断任务类型
    ├── 决策是否走链路
    └── 调度 subagent
         sessions_spawn
              ↓
         子 Agent（HRM / OPS / 业务专员）
              ↓
         产物写入 /workspace/hive/artifacts/
              ↓
         状态写入 /workspace/hive/state/tasks/
              ↓
         CEO 汇总 → 用户
```

### 关键机制
- **CEO = 主会话**：接收用户所有请求，不直接执行任务，只调度
- **子 Agent = subagent**：通过 `sessions_spawn` 启动，独立 workspace
- **产物传递**：共享文件系统（`{WORKSPACE}/hive/artifacts/`）
- **状态外置**：JSON 文件（`{WORKSPACE}/hive/state/tasks/`）
- **统一回复**：子 Agent 不直接回复用户，统一经 CEO 汇总

## When to Use

Triggered when user says:
- "我想构建一个 Hive"
- "我想从零搭建 Hive"

> Note: User saying "Hive 支持 XXX" does NOT trigger this skill.  
> That triggers **HRM directly** (built-in, always active).

## Build Order (Fresh Start)

1. Create Hive directory structure at `{WORKSPACE}/hive/`
2. Initialize **#1 HRM（组织官）** (ROLE.md)
3. Initialize **#2 OPS（运维官）** (ROLE.md)
4. Create business specialists (#3-#8): Collector, Analyst, Writer, QA, PM, Doc
5. Create document management system at `{USER_DOCUMENTS}/Hive/`
6. Update proactivity memory (see below)
7. Generate SETUP.md
8. Run a test task to validate

## Three Core Staff · Definitions

### #0 CEO（指挥官）
- **Model**: {DEFAULT_MODEL}
- **Role**: Orchestration hub, final approval authority
- **Requirements**:
  - All major decisions go through CEO
  - Does not execute specific tasks, only schedules and approves
  - Responsible for overall Hive operations
  - **In practice**: CEO = the main OpenClaw session; receives all user requests

### #1 HRM（组织官）
- **Model**: {STRONG_MODEL}
- **Role**: Hiring + workflow design — brings new specialists into Hive and designs their work chains
- **Requirements**:
  - When user says "Hive 支持 XXX", HRM auto-activates
  - Must design: specialist config AND work chain (when to activate, 上下游, data flow)
  - Must submit to CEO for approval before deploying
  - Cannot deploy without CEO approval
  - Hiring + workflow design is HRM's built-in job, always active

### #2 OPS（运维官）
- **Model**: {STRONG_MODEL}
- **Role**: External environment matching
- **Requirements**:
  - Does NOT autonomously initiate tasks
  - Only acts when CEO initiates "运维检查"
  - Execute version check → evaluate compatibility → report to CEO
  - Only updates after CEO approval

## OPS Workflow

```
CEO initiates: "运维检查"
    ↓
OPS checks version + evaluates compatibility
    ↓
Reports to CEO:
    - Match → "版本匹配，无需更新"
    - Mismatch → proposal + wait for approval
    ↓
[CEO approves] → OPS updates
[CEO refuses] → OPS logs reason, done
```

## Standard Specialists (#3-#8)

| # | Specialist | Model | Duties |
|---|-----------|-------|--------|
| 3 | Collector | {FAST_MODEL} | 资料收集 |
| 4 | Analyst | {STRONG_MODEL} | 数据分析 |
| 5 | Writer | {STRONG_MODEL} | 报告撰写 |
| 6 | QA | {STRONG_MODEL} | 质量审核 |
| 7 | PM | {FAST_MODEL} | 任务追踪 |
| 8 | Doc | {FAST_MODEL} | 归档管理 |

## Business Specialist ROLE.md Template

Each specialist (#3-#8) needs a ROLE.md containing:

```markdown
## 身份
- 名称、编号
- 核心职责

## 工作链路位置
- 何时被激活（触发条件）
- 上下游是谁
- 数据流向（产出给谁消费）

## 核心职责
- 具体任务列表

## 产物
- 产出什么
- 产出路径

## 边界
- 不做什么
- 不与谁直接交互
```

## OPS ≠ System Admin

OPS does:
- Version check
- Compatibility evaluation
- Report to CEO
- Execute after approval

OPS does NOT:
- Autonomously initiate tasks
- System-level exec
- Modify configs without approval

## Directory Structure

```
{WORKSPACE}/hive/
├── agents/
│   ├── hrm/              # HRM（组织官）(#1)
│   ├── ops/               # OPS（运维官）(#2)
│   ├── commander/         # CEO（指挥官）(#0)
│   ├── collector/          #3
│   ├── analyst/           #4
│   ├── writer/            #5
│   ├── qa/               #6
│   ├── pm/               #7
│   └── doc/                #8
├── state/
│   ├── tasks/            # 任务状态文件
│   ├── checkpoints/        # 检查点
│   ├── artifacts/         # 产物索引
│   └── audit/ops/         # OPS 审计日志
├── artifacts/
│   ├── raw/              # 原始资料
│   ├── analysis/         # 分析结果
│   ├── reports/          # 报告草稿
│   ├── review/            # 审核记录
│   └── final/             # 最终交付物

{USER_DOCUMENTS}/Hive/     # Default. User can change.
    ├── 01_工作归档/
    ├── 02_进行中/
    ├── 03_模板库/
    ├── 04_知识库/
    └── manifest.json
```

## Proactivity Memory · What to Update

When initializing Hive, update these memory files:

### `{WORKSPACE}/proactivity/session-state.md`
```
## Current Active Decisions
- 系统名称：Hive
- 三位初始化员工：CEO(#0) / HRM(#1) / OPS(#2)
- 业务专员：Collector(#3) / Analyst(#4) / Writer(#5) / QA(#6) / PM(#7) / Doc(#8)

## 两大链路（均需CEO发起）
- HRM扩员链路：用户"Hive支持XXX" → HRM分析+设计链路 → CEO审批 → [批准]部署
- OPS运维链路：CEO发起"运维检查" → OPS版本检查+评估 → CEO报告 → [批准]执行
```

## SETUP.md · What to Generate

Generate at `{USER_DOCUMENTS}/Hive/SETUP.md`:
- Hive 系统概述
- 三位初始化员工职责
- 业务专员列表及触发条件
- 两大链路说明
- 目录结构
- 下一步行动

## Model Placeholders

| Placeholder | 说明 |
|------------|------|
| `{DEFAULT_MODEL}` | CEO（指挥官）默认模型（快速，成本低）|
| `{FAST_MODEL}` | 简单任务用模型（快速，成本低）|
| `{STRONG_MODEL}` | 复杂任务用模型（强、准确，成本高）|

## Placeholders Reference

| Placeholder | 说明 | 示例 |
|-------------|------|------|
| `{WORKSPACE}` | OpenClaw workspace 路径 | `~/.openclaw/workspace/` |
| `{USER_DOCUMENTS}` | 用户文档目录 | `~/Documents/` |
| `{DEFAULT_MODEL}` | CEO 默认模型 | `minimax-m2.7` |
| `{FAST_MODEL}` | 简单任务模型 | `minimax-m2.7` |
| `{STRONG_MODEL}` | 复杂任务模型 | `openai-codex/gpt-5.4` |

## Quality Checklist

- [ ] HRM (#1) and OPS (#2) initialized with clear ROLE.md
- [ ] #3-#8 created with complete ROLE.md (含工作链路位置)
- [ ] Document directory created at `{USER_DOCUMENTS}/Hive/`
- [ ] proactivity memory updated (session-state.md)
- [ ] SETUP.md generated
- [ ] OPS audit directory created at `{WORKSPACE}/hive/state/audit/ops/`
- [ ] User can run a test task and receive a coordinated response
