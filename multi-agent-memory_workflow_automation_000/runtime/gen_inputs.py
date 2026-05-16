#!/usr/bin/env python3
"""
Generate the initial sandbox workspace for the multi-agent-memory task.
Creates a realistic messy pre-existing state that the agent must extend correctly.
"""

import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

BASE = Path("/root/.openclaw")

# ── 1. Create the full skill directory (as if already installed) ──────────────
skill_dir = BASE / "skills" / "multi-agent-memory"
(skill_dir / "templates").mkdir(parents=True, exist_ok=True)
(skill_dir / "scripts").mkdir(parents=True, exist_ok=True)

# Write stub scripts (they exist but agent should NOT rely on them for this task)
(skill_dir / "scripts" / "init-project.sh").write_text(
    "#!/bin/bash\n# init-project stub - not fully implemented\necho \"Init stub for $1\"\n"
)
(skill_dir / "scripts" / "daily-check.sh").write_text(
    "#!/bin/bash\n# daily-check stub\necho \"Daily check for $1\"\n"
)
os.chmod(skill_dir / "scripts" / "init-project.sh", 0o755)
os.chmod(skill_dir / "scripts" / "daily-check.sh", 0o755)

# ── 2. Create workspace directories ───────────────────────────────────────────
for agent in ["commander", "maker", "vibe", "killjoy", "main"]:
    ws = BASE / f"workspace-{agent}"
    ws.mkdir(parents=True, exist_ok=True)

# maker's current project is phoenix-engine
(BASE / "workspace-maker" / "current-project.txt").write_text("phoenix-engine\n")
(BASE / "workspace-commander" / "current-project.txt").write_text("phoenix-engine\n")

# Distractor files in workspaces
(BASE / "workspace-maker" / "scratch.md").write_text(
    "# Scratch notes\n- TODO: check rendering pipeline\n- Ask vibe about shaders\n"
)
(BASE / "workspace-maker" / "temp-ideas.txt").write_text(
    "Idea: use Vulkan instead of OpenGL for cross-platform support\n"
)
(BASE / "workspace-commander" / "meeting-notes.md").write_text(
    "# Meeting 2026-03-10\n- Discussed Phase 1 completion timeline\n- maker to finish rendering pipeline by EOW\n"
)

# ── 3. Create the phoenix-engine project (partially initialized) ──────────────
proj = BASE / "projects" / "phoenix-engine"
(proj / "status").mkdir(parents=True, exist_ok=True)
(proj / "weekly").mkdir(parents=True, exist_ok=True)
(proj / "handoffs").mkdir(parents=True, exist_ok=True)
(proj / "docs" / "requirements").mkdir(parents=True, exist_ok=True)
(proj / "docs" / "specs").mkdir(parents=True, exist_ok=True)
(proj / "logs").mkdir(parents=True, exist_ok=True)
(proj / "milestones").mkdir(parents=True, exist_ok=True)

# context.md
(proj / "context.md").write_text(
    "# Phoenix Engine - Project Context\n\n"
    "**目标：** 构建高性能分布式游戏引擎，支持多平台渲染\n\n"
    "**阶段：**\n"
    "- Phase 1: 核心渲染管线（进行中）\n"
    "- Phase 2: 物理引擎集成（待开始）\n"
    "- Phase 3: 多平台构建系统（计划中）\n\n"
    "**团队：**\n"
    "- maker: 渲染管线开发\n"
    "- vibe: UI/UX 集成\n"
    "- killjoy: QA & 性能测试\n"
    "- commander: 项目管理\n"
)

# todos.md (current version - has content that should be preserved via versioning)
(proj / "todos.md").write_text(
    "# Phoenix Engine - Todos\n\n"
    "## 紧急\n"
    "- [ ] 完成渲染管线 Phase 1\n"
    "- [ ] 编写单元测试\n\n"
    "## 本周\n"
    "- [ ] 集成 Vulkan 后端\n"
    "- [ ] 性能基准测试\n\n"
    "## 下周\n"
    "- [ ] Phase 2 规划\n"
)

# Existing maker status file with TWO previous versions (to test 3-version rotation)
maker_status_v2_content = (
    "# Maker Status - 2026-03-08\n\n"
    "**当前任务：** 研究 Vulkan API\n"
    "**进度：** 20%\n"
    "**阻碍：** 文档理解困难\n"
)
maker_status_v1_content = (
    "# Maker Status - 2026-03-09\n\n"
    "**当前任务：** 实现 Vulkan 渲染管线\n"
    "**进度：** 65%\n"
    "**阻碍：** 无\n"
)
maker_status_current_content = (
    "# Maker Status - 2026-03-10\n\n"
    "**当前任务：** 渲染管线 Phase 1 最终调试\n"
    "**进度：** 90%\n"
    "**阻碍：** 需要 killjoy 确认测试通过\n"
)

(proj / "status" / "maker.md.2").write_text(maker_status_v2_content)
(proj / "status" / "maker.md.1").write_text(maker_status_v1_content)
(proj / "status" / "maker.md").write_text(maker_status_current_content)

# Other agent statuses (distractors)
(proj / "status" / "commander.md").write_text(
    "# Commander Status - 2026-03-10\n\n"
    "**当前任务：** 协调 Phase 1 交付\n"
    "**进度：** 持续进行\n"
)
(proj / "status" / "vibe.md").write_text(
    "# Vibe Status - 2026-03-10\n\n"
    "**当前任务：** 等待渲染管线 API 稳定\n"
    "**进度：** 阻塞中\n"
)
(proj / "status" / "killjoy.md").write_text(
    "# Killjoy Status - 2026-03-10\n\n"
    "**当前任务：** 准备性能测试用例\n"
    "**进度：** 40%\n"
)

# Existing weekly report (distractor)
(proj / "weekly" / "2026-W09.md").write_text(
    "# Weekly Report - 2026-W09\n\n"
    "## 本周完成\n- Vulkan 研究完成\n- 初始架构设计\n\n"
    "## 下周计划\n- 开始实现渲染管线\n"
)

# Milestones (distractor)
(proj / "milestones" / "milestones.md").write_text(
    "# Phoenix Engine Milestones\n\n"
    "## M1: 渲染管线 Phase 1\n"
    "- **目标：** 完成基础 Vulkan 渲染管线\n"
    "- **截止：** 2026-03-15\n"
    "- **状态：** 进行中\n"
    "- **负责人（Accountable）：** maker\n\n"
    "## M2: 物理引擎集成\n"
    "- **目标：** 集成 Bullet Physics\n"
    "- **截止：** 2026-04-15\n"
    "- **状态：** 未开始\n"
)

# Existing docs (distractors)
(proj / "docs" / "specs" / "2026-03-01-10-00-设计-渲染管线架构.md").write_text(
    "# 渲染管线架构设计\n\n"
    "## 技术选型\n- Vulkan 1.3\n- SPIRV 着色器\n"
)
(proj / "docs" / "requirements" / "2026-03-01-09-00-需求-渲染性能.md").write_text(
    "# 渲染性能需求\n\n"
    "- 60fps @ 1080p 最低要求\n"
    "- 支持 PBR 材质系统\n"
)

# ── 4. Create another project (to test cross-project knowledge isolation) ─────
proj2 = BASE / "projects" / "data-pipeline"
(proj2 / "status").mkdir(parents=True, exist_ok=True)
(proj2 / "logs").mkdir(parents=True, exist_ok=True)
(proj2 / "docs" / "specs").mkdir(parents=True, exist_ok=True)
(proj2 / "context.md").write_text(
    "# Data Pipeline Project\n\n**目标：** 构建实时数据处理管线\n"
)
(proj2 / "status" / "maker.md").write_text(
    "# Maker Status (data-pipeline) - 2026-03-10\n\n"
    "**当前任务：** N/A - 专注于 phoenix-engine\n"
)
(proj2 / "logs" / "2026-03-05-10-00-开发日志-数据摄取模块.md").write_text(
    "# 开发日志 - 数据摄取模块\n\n**负责人：** maker\n**项目：** data-pipeline\n"
)

# ── 5. Create the shared knowledge base (with existing content to append to) ──
knowledge = BASE / "knowledge"
(knowledge / "decisions").mkdir(parents=True, exist_ok=True)
(knowledge / "patterns").mkdir(parents=True, exist_ok=True)
(knowledge / "glossary").mkdir(parents=True, exist_ok=True)
(knowledge / "index").mkdir(parents=True, exist_ok=True)

(knowledge / "decisions" / "decisions.md").write_text(
    "# Global Decisions Log\n\n"
    "## D001 - 2026-03-01\n"
    "**决策：** 使用 Vulkan 作为主渲染后端\n"
    "**理由：** 跨平台支持更好，性能更高\n"
    "**项目：** phoenix-engine\n"
    "**负责人（Accountable）：** commander\n\n"
    "## D002 - 2026-03-05\n"
    "**决策：** 采用 Apache Kafka 作为消息队列\n"
    "**理由：** 高吞吐量，生态成熟\n"
    "**项目：** data-pipeline\n"
    "**负责人（Accountable）：** commander\n\n"
)

(knowledge / "patterns" / "patterns.md").write_text(
    "# Technical Patterns & Lessons Learned\n\n"
    "## P001 - Vulkan 初始化模式\n"
    "**来源项目：** phoenix-engine\n"
    "**模式：** 使用 RAII 封装 Vulkan 对象生命周期\n\n"
)

(knowledge / "glossary" / "glossary.md").write_text(
    "# Glossary\n\n"
    "- **PBR**: Physically Based Rendering\n"
    "- **SPIRV**: Standard Portable Intermediate Representation for Vulkan\n"
)

(knowledge / "index" / "keywords.txt").write_text(
    "Vulkan\nrendering\nPBR\nKafka\ndata-pipeline\nphoenix-engine\n"
)

# ── 6. Create archive directory (distractor) ──────────────────────────────────
archive = BASE / "archive" / "phoenix-engine" / "2026-W09"
archive.mkdir(parents=True, exist_ok=True)
(archive / "summary.md").write_text(
    "# Archive Summary - 2026-W09\n\nPhase 0 完成，进入 Phase 1 开发。\n"
)

print("Workspace generated successfully.")
print(f"Base directory: {BASE}")