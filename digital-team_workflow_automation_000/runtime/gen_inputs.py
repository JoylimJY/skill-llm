#!/usr/bin/env python3
"""
Generate a realistic messy sandbox workspace for the digital-team skill evaluation.
The workspace simulates a partially-initialized fintech project where some agents exist
but are incomplete, and the knowledge base is missing critical files.
"""

import os
import random

random.seed(42)

workspace = "/workspace"

# --- Create the overall project directory structure ---
dirs_to_create = [
    "workspace/agents",
    "workspace/knowledge",
    "workspace/src/backend/loan_engine",
    "workspace/src/frontend/components",
    "workspace/src/shared/utils",
    "workspace/docs/api",
    "workspace/docs/design",
    "workspace/tests/unit",
    "workspace/tests/integration",
    "workspace/scripts",
    "workspace/config",
    "workspace/logs",
]

for d in dirs_to_create:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files to simulate a real messy repo ---
distractor_files = {
    "workspace/src/backend/loan_engine/credit_score.py": """\
# Credit scoring engine v2.1
def calculate_score(applicant_data):
    base = applicant_data.get('income', 0) * 0.4
    debt_ratio = applicant_data.get('debt', 0) / max(applicant_data.get('income', 1), 1)
    return max(300, min(850, int(base - debt_ratio * 200)))
""",
    "workspace/src/backend/loan_engine/risk_model.py": """\
RISK_TIERS = {'A': (750, 850), 'B': (650, 749), 'C': (550, 649), 'D': (300, 549)}

def classify_risk(score):
    for tier, (lo, hi) in RISK_TIERS.items():
        if lo <= score <= hi:
            return tier
    return 'D'
""",
    "workspace/src/frontend/components/LoanForm.jsx": """\
import React, { useState } from 'react';
export default function LoanForm({ onSubmit }) {
  const [amount, setAmount] = useState('');
  return <form onSubmit={() => onSubmit(amount)}><input value={amount} onChange={e => setAmount(e.target.value)} /></form>;
}
""",
    "workspace/src/shared/utils/validators.js": """\
export const isValidSSN = (ssn) => /^\\d{3}-\\d{2}-\\d{4}$/.test(ssn);
export const isValidEmail = (email) => /^[^@]+@[^@]+\\.[^@]+$/.test(email);
""",
    "workspace/docs/api/loan_api_v1.md": """\
# Loan API v1
## POST /api/loans/apply
Request body: { applicant_id, amount, term_months }
Response: { loan_id, status, interest_rate }
""",
    "workspace/docs/design/ux_flows.md": """\
# UX Flows - Digital Lending Platform
## Flow 1: Loan Application
Step 1: Landing → Step 2: Eligibility Check → Step 3: Document Upload → Step 4: Decision
""",
    "workspace/tests/unit/test_credit.py": """\
from src.backend.loan_engine.credit_score import calculate_score
def test_basic_score():
    assert calculate_score({'income': 5000, 'debt': 1000}) == 1800  # TODO: fix
""",
    "workspace/tests/integration/test_loan_flow.py": """\
# Integration tests for full loan origination flow
# TODO: Write tests after API stabilizes
""",
    "workspace/scripts/seed_db.sh": """\
#!/bin/bash
echo 'Seeding development database...'
psql -U devuser -d lendingdb -f migrations/001_initial.sql
""",
    "workspace/config/app.yaml": """\
environment: development
database:
  host: localhost
  port: 5432
  name: lendingdb
feature_flags:
  auto_approval: false
  ml_scoring: true
""",
    "workspace/logs/deploy_2024_01_15.log": """\
[2024-01-15 09:00:01] INFO  Deployment started
[2024-01-15 09:00:45] INFO  Backend services healthy
[2024-01-15 09:01:12] WARN  Frontend build cache miss
[2024-01-15 09:01:58] INFO  Deployment complete - v0.8.3
""",
    "workspace/docs/api/error_codes.md": """\
# Error Codes
E001 - Invalid applicant ID
E002 - Amount exceeds limit
E003 - Term not supported
E004 - Credit check failed
""",
}

for fpath, content in distractor_files.items():
    full_path = os.path.join(workspace, fpath)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create PARTIALLY initialized agents directory ---
# Only 'pm' agent exists, but it's INCOMPLETE (missing current.md)
# This tests that the agent notices incomplete state and handles it

os.makedirs("workspace/agents/pm", exist_ok=True)

with open("workspace/agents/pm/profile.md", "w") as f:
    f.write("""\
# PM 角色设定
**角色名称:** pm (产品经理)
**核心职责:** 需求分析、路线图规划、跨团队协调、产品决策
**工作风格:** 数据驱动，以用户为中心
**主要输出:** PRD、用户故事、验收标准
""")

with open("workspace/agents/pm/memory.md", "w") as f:
    f.write("""\
# PM 长期记忆
## 项目背景
- 数字借贷平台，目标用户：中小企业主
- 核心功能：在线申请、自动审批、额度管理

## 已完成工作
- 完成竞品分析报告（Q4 2023）
- 制定 MVP 功能范围

## 关键决策
- 优先 Web 端，移动端 Phase 2
""")

# Intentionally missing: workspace/agents/pm/current.md
# This is the "messy real-world" state the agent must handle

# --- Create a bare ROLES.md that only has pm listed ---
with open("workspace/agents/ROLES.md", "w") as f:
    f.write("""\
# 角色别名映射

| 角色 | 别名 |
|------|------|
| pm | product, 产品, 产品经理 |
""")

# --- Create a TEMPLATE.md ---
with open("workspace/agents/TEMPLATE.md", "w") as f:
    f.write("""\
# 角色启动模板

## profile.md 模板
```
# {角色名} 角色设定
**角色名称:** {角色名}
**核心职责:** {职责描述}
**工作风格:** 专业、高效
**主要输出:** 相关交付物
```

## memory.md 模板
```
# {角色名} 长期记忆
## 项目背景
（从 knowledge/project.md 读取）

## 已完成工作
（初始化为空）

## 关键决策
（从 knowledge/decisions.md 读取）
```

## current.md 模板
```
# {角色名} 当前状态
**当前任务:** 待分配
**进度:** 0%
**阻塞项:** 无
```
""")

# --- Knowledge directory: project.md exists but others are MISSING ---
# knowledge/decisions.md and knowledge/team.md are missing (agent must create them)
with open("workspace/knowledge/project.md", "w") as f:
    f.write("""\
# 项目背景：数字借贷平台

## 项目名称
LendFlow - 中小企业数字借贷平台

## 核心目标
为中小企业提供 24 小时在线贷款申请、自动化审批和智能额度管理服务

## 技术栈
- 后端：Python/FastAPI + PostgreSQL
- 前端：React + TypeScript
- ML：信用评分模型 v2

## 当前阶段
Phase 1 - MVP 开发（预计 Q2 2024 上线）

## 关键 KPIs
- 申请到放款 < 4 小时
- 自动审批率 > 70%
- 坏账率 < 2%
""")

# NOTE: knowledge/decisions.md and knowledge/team.md are intentionally absent
# NOTE: agents/arch/, agents/qa/ etc. do NOT exist yet - agent must create them

print("Workspace generated successfully.")
print("\nCurrent structure:")
for root, dirs, files in os.walk("/workspace/workspace"):
    level = root.replace("/workspace/workspace", "").count(os.sep)
    indent = " " * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = " " * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")