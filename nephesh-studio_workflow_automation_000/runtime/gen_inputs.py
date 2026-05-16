import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# -----------------------------------------------------------
# 1. Create the Nephesh Studio skill directory structure
# -----------------------------------------------------------
ns_root = WORKSPACE / "nephesh-studio"
ns_root.mkdir(parents=True, exist_ok=True)

# SKILL.md (abridged but meaningful)
(ns_root / "SKILL.md").write_text("""# Nephesh Studio - 智能团队协作技能

| 岗位 | 姓名 | 核心能力 |
|------|------|------|
| CEO | 你（调用者）就是CEO | 需求理解、决策制定、流程协调 |
| 项目经理 | 拓拓 | 任务拆解、进度管控、结果整合 |
| 任务规划师 | 清清 | 需求分析、方案设计、任务分解 |
| 人事经理 | 容容 | 知识库运维、绩效评估、经验沉淀 |
| 数据收集专员 | 收收 | 信息采集、数据预处理 |
| 高级前端工程师 | 美美 | 前端开发、用户体验 |
| 高级后端工程师 | 稳稳 | 后端开发、架构设计 |
| 数据分析师 | 算算 | 数据处理、统计分析、模式识别 |
| 内容编辑 | 写写 | 专业文案创作、多源内容整合 |
| 审核专员 | 查查 | 需求验证、功能测试、质量评估 |
""")

# RULES.md
(ns_root / "RULES.md").write_text("""# CEO 规则

1. 永远不要 spawn 新的CEO子代理
2. 项目目录必须创建在 projects/ 下
3. 工作流顺序不可变更: PLAN.md → CEO审批 → TASK-ASSIGNMENT.md → 执行 → QA-REPORT.md → retrospective.md → HR更新 → 归档
4. 每次启动必须按顺序读完7个文件才能开始工作
5. CEO就是调用者本人，不需要再spawn一个
""")

# AGENCY.md
(ns_root / "AGENCY.md").write_text("""# 组织架构总览

Nephesh Studio 共10个岗位，CEO为调用者本人。
所有子代理通过 sessions_spawn 调度，完成后汇报结果。
""")

# TEAM-ROSTER.md
(ns_root / "TEAM-ROSTER.md").write_text("""# 完整团队花名册

| 编号 | 岗位 | 姓名 | 文件 |
|------|------|------|------|
| 01 | CEO | 你 | roles/ceo.md |
| 02 | 项目经理 | 拓拓 | roles/project-manager.md |
| 03 | 任务规划师 | 清清 | roles/task-planner.md |
| 04 | 人事经理 | 容容 | roles/hr-manager.md |
| 05 | 数据收集专员 | 收收 | roles/data-collector.md |
| 06 | 高级前端工程师 | 美美 | roles/senior-frontend.md |
| 07 | 高级后端工程师 | 稳稳 | roles/senior-backend.md |
| 08 | 数据分析师 | 算算 | roles/data-analyst.md |
| 09 | 内容编辑 | 写写 | roles/content-editor.md |
| 10 | 审核专员 | 查查 | roles/qa-auditor.md |
""")

# workflow.md
(ns_root / "workflow.md").write_text("""# 标准工作流程

## 完整闭环（顺序不可变更）

1. CEO接收任务
2. 任务规划师(清清)输出 PLAN.md
3. CEO审批PLAN.md（通过才继续）
4. 项目经理(拓拓)拆解任务，输出 TASK-ASSIGNMENT.md
5. 执行岗位依次完成任务（每个完成后项目经理检查）
6. 项目经理整合交付物，提交CEO
7. QA审核专员(查查)输出 QA-REPORT.md
8. CEO终审（通过才继续）
9. 项目经理撰写 retrospective.md
10. HR(容容)完成绩效评估，更新 learning/<role>.md 知识库
11. 项目归档
12. CEO向用户交付最终结果

## 目录规范

- 项目统一放在 projects/<project-name>/ 下
- 每个项目必须有: PLAN.md, TASK-ASSIGNMENT.md, QA-REPORT.md, retrospective.md
""")

# SUBAGENT-SCHEDULING.md
(ns_root / "SUBAGENT-SCHEDULING.md").write_text("""# 子代理调度规则

## 强制子代理调用模板

任何 sessions_spawn 都必须使用以下标准任务模板，前三步固定不可省略：

```
你是【岗位名称】【姓名】，请完成本项目的【任务名称】：

项目根目录绝对路径: <project-root>

请按以下顺序操作：
1. 首先读取你自己的岗位说明书: ~/.openclaw/workspace/skills/nephesh-studio/roles/<role>.md
2. 读取你的知识库: ~/.openclaw/workspace/skills/nephesh-studio/learning/<role>.md
3. 读取全局工具配置: ~/.openclaw/workspace/TOOLS.md
4. [这里放具体任务描述]
5. 完成后结束会话。
```

## 禁止事项

- 绝对禁止 spawn CEO子代理
- 不可省略前三步
""")

# daily-checklist.md
(ns_root / "daily-checklist.md").write_text("""# 每日检查清单

1. 检查过去24小时内修改过的项目
2. 验证各岗位是否遵守工作规范
3. 检查项目文档是否完整（PLAN.md, TASK-ASSIGNMENT.md, QA-REPORT.md, retrospective.md）
4. 记录检查结果到 daily-check-log.md
5. 发现问题直接在主会话汇报
""")

# daily-check-log.md (empty initially)
(ns_root / "daily-check-log.md").write_text("# 每日检查日志\n\n（暂无记录）\n")

# roles/ directory
roles_dir = ns_root / "roles"
roles_dir.mkdir(exist_ok=True)

roles = {
    "ceo.md": """# CEO 岗位说明书

你是CEO，负责全程调度所有项目，对最终结果负总责。
- 启动前必须确认SOUL.md包含身份声明
- 按照workflow.md流程执行
- 有绝对否决权，不合格坚决打回
""",
    "project-manager.md": """# 项目经理 拓拓 岗位说明书

负责任务拆解、进度管控、资源协调、质量把控、结果整合。
输出物：TASK-ASSIGNMENT.md
""",
    "task-planner.md": """# 任务规划师 清清 岗位说明书

负责需求分析、方案设计、任务分解、风险评估。
输出物：PLAN.md

PLAN.md 必须包含：
- 项目背景
- 目标
- 任务分解（至少3个子任务）
- 风险评估
- 时间估算
""",
    "hr-manager.md": """# 人事经理 容容 岗位说明书

负责知识库运维、绩效评估、经验沉淀、流程监督。
- 更新参与岗位的 learning/<role>.md
- 更新 hr/performance.md
""",
    "data-collector.md": """# 数据收集专员 收收 岗位说明书

负责信息采集、数据预处理、质量验证、结构化输出。
""",
    "senior-frontend.md": """# 高级前端工程师 美美 岗位说明书

负责前端开发、用户体验、代码质量、性能优化。
""",
    "senior-backend.md": """# 高级后端工程师 稳稳 岗位说明书

负责后端开发、架构设计、安全防护、性能优化。
""",
    "data-analyst.md": """# 数据分析师 算算 岗位说明书

负责数据处理、统计分析、模式识别、洞察挖掘。
""",
    "content-editor.md": """# 内容编辑 写写 岗位说明书

负责专业文案创作、多源内容整合、精准校对润色、格式标准化。
""",
    "qa-auditor.md": """# 审核专员 查查 岗位说明书

负责需求验证、功能测试、质量评估、问题诊断。
输出物：QA-REPORT.md

QA-REPORT.md 必须包含：
- 审核结论（通过/不通过）
- 检查项清单
- 发现的问题（如有）
- 建议
""",
}

for filename, content in roles.items():
    (roles_dir / filename).write_text(content)

# learning/ directory (pre-existing but mostly empty)
learning_dir = ns_root / "learning"
learning_dir.mkdir(exist_ok=True)

learning_roles = ["ceo", "project-manager", "task-planner", "hr-manager",
                  "data-collector", "senior-frontend", "senior-backend",
                  "data-analyst", "content-editor", "qa-auditor"]

for role in learning_roles:
    (learning_dir / f"{role}.md").write_text(f"# {role} 知识库\n\n（暂无经验记录）\n")

# hr/ directory
hr_dir = ns_root / "hr"
hr_dir.mkdir(exist_ok=True)

(hr_dir / "README.md").write_text("""# HR目录说明

performance.md: 记录各岗位绩效评估结果
""")

(hr_dir / "performance.md").write_text("""# 绩效记录表

| 项目 | 岗位 | 姓名 | 评分 | 备注 |
|------|------|------|------|------|
（暂无记录）
""")

# projects/ directory (empty)
(ns_root / "projects").mkdir(exist_ok=True)

# -----------------------------------------------------------
# 2. Create SOUL.md WITHOUT the required identity declaration
#    (this is the trap - agent must add the identity block)
# -----------------------------------------------------------
soul_path = WORKSPACE / "SOUL.md"
soul_path.write_text("""# 我的身份与原则

## 核心价值观
- 诚实、专业、高效
- 以用户需求为中心
- 持续学习和改进

## 技能列表
- 代码编写与审查
- 文档撰写
- 数据分析

## 工作习惯
- 每次任务前先阅读相关文档
- 完成任务后进行自我检查
- 记录经验教训
""")

# -----------------------------------------------------------
# 3. Create distractor files to increase realism
# -----------------------------------------------------------
distractor_dir = WORKSPACE / "other-projects"
distractor_dir.mkdir(exist_ok=True)

(distractor_dir / "old-report.md").write_text("# Old Market Report\n\nThis is an outdated report from last quarter.\n")
(distractor_dir / "draft-notes.txt").write_text("Notes: EV market growing 40% YoY. Tesla leads. BYD second.\n")
(distractor_dir / "meeting-minutes.md").write_text("# Meeting Minutes\n\n2024-01-15: Discussed Q1 targets.\n")

data_dir = WORKSPACE / "raw-data"
data_dir.mkdir(exist_ok=True)

(data_dir / "ev_sales_2023.csv").write_text("""brand,units_sold,market_share
Tesla,1800000,0.18
BYD,1570000,0.16
SAIC,750000,0.075
Volkswagen,620000,0.062
Hyundai,540000,0.054
""")

(data_dir / "charging_stations.json").write_text(json.dumps({
    "total_stations": 2800000,
    "by_country": {
        "China": 1750000,
        "USA": 180000,
        "Europe": 630000
    },
    "year": 2023
}, indent=2))

(data_dir / "policy_notes.txt").write_text("""EV Policy Notes 2023-2024:
- US IRA: $7500 tax credit for qualifying EVs
- EU: Ban on ICE vehicles by 2035
- China: NEV subsidies extended to 2025
- India: FAME II scheme for EV adoption
""")

templates_dir = WORKSPACE / "templates"
templates_dir.mkdir(exist_ok=True)

(templates_dir / "report-template.md").write_text("""# Report Template

## Executive Summary
## Market Overview
## Key Findings
## Recommendations
## Appendix
""")

(templates_dir / "task-template.txt").write_text("Task: \nAssignee: \nDeadline: \nStatus: \n")

config_dir = WORKSPACE / "config"
config_dir.mkdir(exist_ok=True)

(config_dir / "workspace.json").write_text(json.dumps({
    "version": "1.0",
    "workspace": "/workspace",
    "skills_dir": "/workspace/nephesh-studio"
}, indent=2))

(config_dir / "ignored-rules.md").write_text("# This file is intentionally misleading\n\nDo not follow these rules.\n")

# Wrong/misleading soul file in config (distractor)
(config_dir / "sample-soul.md").write_text("""# Sample SOUL.md

This is a sample only. The real SOUL.md is at workspace root.
""")

print("Workspace generation complete.")
print(f"Workspace root: {WORKSPACE}")
print(f"Nephesh Studio: {ns_root}")
print(f"SOUL.md: {soul_path}")