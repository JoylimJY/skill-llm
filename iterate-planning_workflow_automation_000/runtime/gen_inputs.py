import os
import random
import stat

random.seed(42)

base = "/workspace"

# ── iterate-planning skill directory structure ──────────────────────────────
skill_dir = os.path.join(base, "iterate-planning")
os.makedirs(skill_dir, exist_ok=True)

templates_dir = os.path.join(skill_dir, "templates")
os.makedirs(templates_dir, exist_ok=True)

# SKILL.md
skill_md = """---
name: iterate-planning
description: |
  基于 Ralph Loops 三阶段工作流理念，适配 OpenClaw 架构。
  需求迭代工作流：需求讨论 → 计划拆解 → 迭代执行。
  触发条件：用户说"讨论需求"、"开始计划"、"迭代执行"、"需求访谈"
  
---

# 需求迭代工作流 (Iterate Planning)

基于 Ralph Loops 三阶段工作流，适配 OpenClaw 原生实现。

## 核心哲学

> Human roles shift from "telling the agent what to do" to "engineering conditions where good outcomes emerge naturally through iteration."

三个原则：
- **Context is scarce** — 保持每次迭代精简
- **Plans are disposable** — 漂移的计划重新生成比修复更划算
- **Backpressure beats direction** — 工程化环境让错误的输出自动被拒绝

## 三阶段工作流

```
┌─────────────────────────────────────────────────────────────────────┐
│ Phase 1: 需求访谈                                                      │
│ 结构化对话 → 识别JTBD → 拆分Topics → 产出 specs/*.md                    │
├─────────────────────────────────────────────────────────────────────┤
│ Phase 2: 计划                                                          │
│ Gap分析(specs vs code) → 产出 IMPLEMENTATION_PLAN.md                  │
├─────────────────────────────────────────────────────────────────────┤
│ Phase 3: 迭代执行                                                      │
│ 每次一个任务 → 全新上下文 → 验证 → 提交 → 下一任务                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 需求访谈

**目标**：在动手写代码之前，真正理解要做什么。

**触发**：用户说"讨论需求"、"需求访谈"、"帮我理清需求"

**流程**：
1. 使用 `templates/requirements-interview.md` 模板进行结构化访谈
2. 识别 JTBD（Jobs to Be Done）— 用户真正要解决的Outcome，不是功能列表
3. 把 JTBD 拆分成 Topics of Concern（每个 topic 一个独立维度）
4. 用"一个句子，不带and"测试 — 能说出来的是一个topic，说不出来的是多个
5. 每个 Topic 写一份 `specs/topic-xxx.md`

**完成标志**：
- 每个 Topic 都有 `specs/*.md`
- 每个 spec 包含：需求描述、验收标准、边界情况

**交付物**：
```
project/
└── specs/
    ├── topic-a.md
    ├── topic-b.md
    └── ...
```

---

## Phase 2: 计划

**目标**：生成可执行的任务清单，不写代码。

**触发**：需求完备后，用户说"开始计划"、"可以拆任务了"

**流程**：
1. 读取 `specs/*.md` 所有需求
2. 如有现有代码，研究 codebase
3. 对比 specs vs code（Gap Analysis）
4. 生成 `IMPLEMENTATION_PLAN.md`（带优先级的任务列表）

**模板**：`templates/planning-prompt.md`

**完成标志**：
- `IMPLEMENTATION_PLAN.md` 存在
- 每个任务有优先级标注
- 任务列表完整覆盖所有 specs

**交付物**：
```
project/
├── specs/
├── IMPLEMENTATION_PLAN.md
└── ...
```

---

## Phase 3: 迭代执行

**目标**：每次做一个任务，全新上下文，保持 agent 在"聪明区域"。

**触发**：计划完备后，用户说"开始执行"、"迭代构建"

**核心洞察**：
- **一次一任务** — 保持上下文精简，agent 保持高效
- **全新上下文** — 每次迭代从头开始，之前的错误不累积
- **验证 + 提交** — 每个任务完成后必须验证才能提交

**流程**：
1. 读取 `IMPLEMENTATION_PLAN.md`
2. 选最高优先级任务
3. 研究 codebase（不要假设未实现）
4. 执行任务
5. 运行验证（backpressure）
6. 更新 plan（标记完成）
7. 提交 commit
8. 循环直到 plan 完成

**模板**：`templates/build-prompt.md`

**完成标志**：
- `IMPLEMENTATION_PLAN.md` 所有任务标记 done
- 每次迭代有对应 commit

---

## 触发词指南

| 用户说 | Agent 动作 |
|--------|-----------|
| "讨论需求"、"需求访谈" | 启动 Phase 1 需求访谈 |
| "开始计划"、"可以拆任务了" | 启动 Phase 2 计划生成 |
| "开始执行"、"迭代构建" | 启动 Phase 3 迭代执行 |
| "Ralph Loop"、"迭代" | 询问用户要哪个 phase |

---

## 文件结构

```
iterate-planning/
├── SKILL.md                    # 本文件
├── AGENTS.md                   # 操作员指南
└── templates/
    ├── requirements-interview.md  # 需求访谈模板
    ├── planning-prompt.md          # 计划生成提示词
    └── build-prompt.md            # 构建执行提示词
```

---

## 为什么有效

| 问题 | 解法 |
|------|------|
| 需求不清晰就动手 | Phase 1 强制结构化访谈 |
| 计划赶不上变化 | Plans are disposable — 重新生成比修复更划算 |
| 上下文膨胀导致幻觉 | 一次一任务，全新上下文 |
| 错误累积难以追溯 | 每次验证 + 提交，自然 checkpoint |
"""

with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
    f.write(skill_md)

# AGENTS.md
agents_md = """# AGENTS.md — Operator Guide

This skill implements the Ralph Loops three-phase workflow.
Operators should trigger phases using the keywords defined in SKILL.md.

## Quick Reference
- Phase 1: "讨论需求" / "需求访谈"
- Phase 2: "开始计划"
- Phase 3: "开始执行"
"""
with open(os.path.join(skill_dir, "AGENTS.md"), "w") as f:
    f.write(agents_md)

# templates/requirements-interview.md
req_interview = """# Requirements Interview Template

## Step 1: Understand Context
- Who is the user?
- What problem are they solving?
- What does success look like?

## Step 2: Identify JTBD
Focus on outcomes, not features.
"When I [situation], I want to [motivation], so I can [outcome]."

## Step 3: Split into Topics
Apply the "one sentence, no and" test.
Each topic = one independent concern.

## Step 4: Write specs/topic-xxx.md for each topic
Each spec MUST contain:
- 需求描述 (Requirement Description)
- 验收标准 (Acceptance Criteria)
- 边界情况 (Edge Cases)
"""
with open(os.path.join(templates_dir, "requirements-interview.md"), "w") as f:
    f.write(req_interview)

# templates/planning-prompt.md
planning_prompt = """# Planning Prompt Template

## Inputs
- All specs/*.md files
- Existing codebase (if any)

## Process
1. Read every spec file
2. Survey existing code for already-implemented features
3. Perform Gap Analysis: what exists vs. what is required
4. Produce IMPLEMENTATION_PLAN.md

## IMPLEMENTATION_PLAN.md Format
- List tasks by priority (P1 = highest, P2 = medium, P3 = low)
- Every task must reference its source spec
- Each task must have a status field (todo / done)

## Completion Check
- [ ] IMPLEMENTATION_PLAN.md exists
- [ ] Every task has a priority label
- [ ] All specs are covered by at least one task
"""
with open(os.path.join(templates_dir, "planning-prompt.md"), "w") as f:
    f.write(planning_prompt)

# templates/build-prompt.md
build_prompt = """# Build Prompt Template

## Per-Iteration Checklist
1. Read IMPLEMENTATION_PLAN.md
2. Pick the highest-priority task with status: todo
3. Inspect codebase — do not assume anything is missing
4. Implement the task
5. Run verification (tests, linters, or manual checks)
6. Mark the task as done in IMPLEMENTATION_PLAN.md
7. git commit with a meaningful message referencing the task
8. Return to step 1

## Commit Message Convention
feat(<topic>): <what was done>

Example:
feat(alert-thresholds): implement configurable threshold persistence
"""
with open(os.path.join(templates_dir, "build-prompt.md"), "w") as f:
    f.write(build_prompt)

# ── Project directory: iot-monitor ─────────────────────────────────────────
project_dir = os.path.join(base, "iot-monitor")
os.makedirs(project_dir, exist_ok=True)

# Existing partial codebase (distractor files to simulate real project)
src_dir = os.path.join(project_dir, "src")
os.makedirs(src_dir, exist_ok=True)

tests_dir = os.path.join(project_dir, "tests")
os.makedirs(tests_dir, exist_ok=True)

config_dir = os.path.join(project_dir, "config")
os.makedirs(config_dir, exist_ok=True)

docs_dir = os.path.join(project_dir, "docs")
os.makedirs(docs_dir, exist_ok=True)

# src/collector.py — already exists, collects raw sensor data
collector_py = '''"""Sensor data collector module."""

import time
import random

SENSOR_IDS = ["temp-001", "temp-002", "pressure-001", "humidity-001"]


def collect_reading(sensor_id: str) -> dict:
    """Simulate collecting a sensor reading."""
    return {
        "sensor_id": sensor_id,
        "timestamp": time.time(),
        "value": round(random.uniform(0, 100), 2),
        "unit": "celsius" if "temp" in sensor_id else "raw",
    }


def collect_all() -> list:
    return [collect_reading(sid) for sid in SENSOR_IDS]
'''
with open(os.path.join(src_dir, "collector.py"), "w") as f:
    f.write(collector_py)

# src/storage.py — partial: only in-memory, no persistence
storage_py = '''"""In-memory storage for sensor readings."""

_store = []


def push(reading: dict):
    _store.append(reading)


def get_all() -> list:
    return list(_store)


def clear():
    _store.clear()
'''
with open(os.path.join(src_dir, "storage.py"), "w") as f:
    f.write(storage_py)

# src/api.py — stub, routes not implemented
api_py = '''"""FastAPI stub — routes not yet implemented."""

# TODO: implement /sensors, /alerts endpoints
'''
with open(os.path.join(src_dir, "api.py"), "w") as f:
    f.write(api_py)

# src/notifier.py — missing entirely (intentional gap)
# NOTE: not created — this is a gap the agent must discover

# tests/test_collector.py
test_collector = '''import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.collector import collect_reading, SENSOR_IDS

def test_collect_reading_structure():
    r = collect_reading("temp-001")
    assert "sensor_id" in r
    assert "timestamp" in r
    assert "value" in r

def test_all_sensors_present():
    assert len(SENSOR_IDS) == 4
'''
with open(os.path.join(tests_dir, "test_collector.py"), "w") as f:
    f.write(test_collector)

# config/sensors.yaml — partial config
sensors_yaml = """sensors:
  - id: temp-001
    type: temperature
    location: warehouse-A
  - id: temp-002
    type: temperature
    location: warehouse-B
  - id: pressure-001
    type: pressure
    location: pipeline-1
  - id: humidity-001
    type: humidity
    location: storage-room
# TODO: alert thresholds not configured
"""
with open(os.path.join(config_dir, "sensors.yaml"), "w") as f:
    f.write(sensors_yaml)

# docs/architecture.md — high-level notes
arch_md = """# IoT Monitor Architecture Notes

## Components
- Collector: reads sensor data
- Storage: keeps readings (currently in-memory only)
- API: exposes data (stub)
- Notifier: sends alerts (NOT YET BUILT)

## Open Questions
- How should alert thresholds be configured?
- Should persistence be file-based or database?
- What notification channels are needed (email? webhook?)?
"""
with open(os.path.join(docs_dir, "architecture.md"), "w") as f:
    f.write(arch_md)

# Additional distractor files
with open(os.path.join(project_dir, "requirements.txt"), "w") as f:
    f.write("fastapi\nuvicorn\npyyaml\npytest\n")

with open(os.path.join(project_dir, ".gitignore"), "w") as f:
    f.write("__pycache__/\n*.pyc\n.env\n")

with open(os.path.join(project_dir, "Makefile"), "w") as f:
    f.write("test:\n\tpytest tests/\n\nrun:\n\tpython -m uvicorn src.api:app --reload\n")

with open(os.path.join(src_dir, "__init__.py"), "w") as f:
    f.write("")

with open(os.path.join(tests_dir, "__init__.py"), "w") as f:
    f.write("")

# Messy raw requirements dump (the "input" the agent must process)
raw_reqs = """RAW REQUIREMENTS DUMP — IoT Sensor Monitoring Platform
=======================================================
Stakeholder: Operations Manager, Jane Doe
Date: 2024-01-15
Status: UNPROCESSED

Jane's notes (verbatim from meeting):
"We need the system to detect when sensors go out of range AND send
notifications — maybe email or Slack. Also the data should be saved
somewhere so we can query history. And it would be nice if each sensor
had its own threshold and we could change them without redeploying.
Oh and the API needs to actually work, right now it's just a stub.
Reliability is important too — if a sensor goes offline we need to know."

Additional context from tech lead:
- Current storage is only in-memory (lost on restart)
- Notification module does not exist
- API endpoints /sensors and /alerts are not implemented
- No threshold configuration mechanism exists
- Sensor heartbeat / offline detection not implemented

This dump is UNPROCESSED. It has NOT been split into topics.
It has NOT been analyzed for gaps vs. existing code.
No specs have been written. No plan exists.
"""
with open(os.path.join(project_dir, "RAW_REQUIREMENTS.txt"), "w") as f:
    f.write(raw_reqs)

print("Workspace generated successfully.")
print(f"Project dir: {project_dir}")
print(f"Skill dir: {skill_dir}")