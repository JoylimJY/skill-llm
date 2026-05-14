import os
import random
from pathlib import Path
from datetime import datetime

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create the skill documentation tree (as it would exist in the workspace)
skill_dir = workspace / ".openclaw" / "skills" / "cursor-council"
skill_dir.mkdir(parents=True, exist_ok=True)
refs_dir = skill_dir / "references"
refs_dir.mkdir(exist_ok=True)

# Write SKILL.md
skill_md = r"""---
name: cursor-council
description: Multi-Cursor orchestration for parallel task execution and AI council deliberation.
metadata:
  {
    "openclaw":
      {
        "emoji": "🎭",
        "author": "xiaoyaner",
        "version": "2.0.0",
        "requires": { 
          "bins": ["tmux", "agent"],
          "skills": ["cursor-agent"]
        }
      }
  }
---

# 🎭 Cursor Council

## 两种模式

### 模式二：前辈议会 🧙‍♂️

角色分配逻辑：

| 角色 | 模型选择 | 思维特点 |
|------|----------|----------|
| **架构师** | Opus（深度推理） | 看长远、找边界、想极端情况 |
| **工程师** | Sonnet（快速实用） | 讲效率、抓重点、先跑起来 |
| **批判者** | GPT（不同视角） | 挑毛病、给替代方案、打破惯性 |

操作流程：

```bash
tmux send-keys -t council-opus "agent --model claude-opus-4-6 -p \"$(cat /tmp/council-opus-prompt.txt)\" --force --output-format text 2>&1 | tee /tmp/council-opus-output.txt" Enter
tmux send-keys -t council-sonnet "agent --model claude-sonnet-4-5 -p \"$(cat /tmp/council-sonnet-prompt.txt)\" --force --output-format text 2>&1 | tee /tmp/council-sonnet-output.txt" Enter
tmux send-keys -t council-gpt "agent --model gpt-5.2 -p \"$(cat /tmp/council-gpt-prompt.txt)\" --force --output-format text 2>&1 | tee /tmp/council-gpt-output.txt" Enter
```

## 会议归档

```
~/.openclaw/workspace/pr-review/
└── council-YYYY-MM-DD[-topic]/
    ├── README.md
    ├── council-opus-prompt.txt
    ├── council-opus-output.txt
    ├── council-sonnet-prompt.txt
    ├── council-sonnet-output.txt
    ├── council-gpt-prompt.txt
    └── council-gpt-output.txt
```
"""

(skill_dir / "SKILL.md").write_text(skill_md)

# Write references
council_deliberation = """# Council Deliberation Guide

## Model Role Assignments

### The Architect (Opus)
- Model: claude-opus-4-6
- Strengths: Deep analysis, sees implications others miss

### The Pragmatist (Sonnet)
- Model: claude-sonnet-4-5
- Strengths: Time-to-market, pragmatic tradeoffs

### The Challenger (GPT-5 / External Model)
- Model: gpt-5.2
- Strengths: Different training data, breaks groupthink

## Deliberation Workflow

### Phase 2: Parallel Consultation

```bash
for role in opus sonnet gpt; do
  tmux new-session -d -s council-$role
done

tmux send-keys -t council-opus "agent --model claude-opus-4-6 -p '...' --force" Enter
tmux send-keys -t council-sonnet "agent --model claude-sonnet-4-5 -p '...' --force" Enter
tmux send-keys -t council-gpt "agent --model gpt-5.2 -p '...' --force" Enter
```
"""
(refs_dir / "council-deliberation.md").write_text(council_deliberation)

session_readme_template = """# Session README Template

```markdown
# AI Council Session - YYYY-MM-DD

## 审查目标
- [PR/Issue/决策 描述]

## Council 成员

| 角色 | 模型 | 人设 | 关注点 |
|------|------|------|--------|
| 架构师 | opus-4.6 | **[大牛名字]** | [专长领域] |
| 工程师 | sonnet-4.5 | **[大牛名字]** | [专长领域] |
| 批判者 | gpt-5.2 | **[大牛名字]** | [专长领域] |

## 文件清单

| 文件 | 内容 | 行数 |
|------|------|------|
| `council-opus-prompt.txt` | Opus 任务 prompt | XX |
| `council-opus-output.txt` | Opus 完整分析 | XX |
| `council-sonnet-prompt.txt` | Sonnet 任务 prompt | XX |
| `council-sonnet-output.txt` | Sonnet 完整分析 | XX |
| `council-gpt-prompt.txt` | GPT 任务 prompt | XX |
| `council-gpt-output.txt` | GPT 完整分析 | XX |

## 共识矩阵

| 维度 | Opus | Sonnet | GPT |
|------|------|--------|-----|
| [维度1] | [观点] | [观点] | [观点] |

## 结论

### 一致同意
- [共识点1]

### 存在分歧
- [分歧点及各方观点]

### 最终建议
[综合建议]

## 后续行动

- [ ] [Action 1]
```
"""
(refs_dir / "session-readme-template.md").write_text(session_readme_template)

persona_engineering = """# Persona Engineering for AI Council

## 人设库

### 系统架构 / 软件工程

| 大牛 | 代表作 | 哲学 | 适合模型 |
|------|--------|------|----------|
| **Martin Fowler** | 重构, 企业架构模式 | 渐进式改进, 模式语言 | Opus (深度) |
| **Uncle Bob** | Clean Code, SOLID | 整洁代码, 原则优先 | Sonnet |
| **Linus Torvalds** | Linux, Git | 直言不讳, 务实, 性能优先 | GPT (批判) |

### 并发 / 分布式系统

| 大牛 | 代表作 | 哲学 | 适合模型 |
|------|--------|------|----------|
| **Martin Kleppmann** | DDIA | 数据密集型应用, CRDT | Opus/Sonnet |
| **Leslie Lamport** | Paxos, TLA+ | 形式化验证 | Opus |
"""
(refs_dir / "persona-engineering.md").write_text(persona_engineering)

parallel_execution = """# Parallel Execution Guide

## Session Management

```bash
for i in 1 2 3; do
  tmux kill-session -t cursor-$i 2>/dev/null || true
  tmux new-session -d -s cursor-$i
  tmux send-keys -t cursor-$i "cd $PROJECT_DIR" Enter
done
```
"""
(refs_dir / "parallel-execution.md").write_text(parallel_execution)

# Create a realistic fintech project structure (distractor files)
project_dir = workspace / "fintech-ledger"
project_dir.mkdir(exist_ok=True)

dirs = [
    "src/api", "src/models", "src/services", "src/middleware",
    "src/config", "tests/unit", "tests/integration",
    "docs/architecture", "scripts", "deploy"
]
for d in dirs:
    (project_dir / d).mkdir(parents=True, exist_ok=True)

# Distractor source files
files = {
    "src/api/transactions.py": """from flask import Blueprint, jsonify, request
from src.services.ledger import LedgerService

bp = Blueprint('transactions', __name__)

@bp.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.json
    # TODO: implement proper storage
    result = LedgerService.record(data)
    return jsonify(result)
""",
    "src/api/accounts.py": """from flask import Blueprint, jsonify
bp = Blueprint('accounts', __name__)

@bp.route('/accounts/<account_id>', methods=['GET'])
def get_account(account_id):
    # Currently using in-memory store - needs DB
    return jsonify({"id": account_id, "balance": 0})
""",
    "src/models/transaction.py": """class Transaction:
    def __init__(self, id, amount, currency, from_account, to_account):
        self.id = id
        self.amount = amount
        self.currency = currency
        self.from_account = from_account
        self.to_account = to_account
""",
    "src/models/account.py": """class Account:
    def __init__(self, id, owner, balance=0):
        self.id = id
        self.owner = owner
        self.balance = balance
""",
    "src/services/ledger.py": """class LedgerService:
    _store = {}

    @classmethod
    def record(cls, transaction_data):
        tx_id = transaction_data.get('id', 'unknown')
        cls._store[tx_id] = transaction_data
        return {"status": "recorded", "id": tx_id}
""",
    "src/config/database.py": """# TODO: This file needs to be replaced with actual DB config
# Options under consideration:
# 1. PostgreSQL - relational, ACID, team knows it
# 2. MongoDB - document store, flexible schema
# 3. Cassandra - wide-column, high write throughput

DATABASE_URL = None  # Not configured yet
""",
    "src/middleware/auth.py": """def require_auth(f):
    def wrapper(*args, **kwargs):
        # TODO: implement JWT validation
        return f(*args, **kwargs)
    return wrapper
""",
    "tests/unit/test_transaction.py": """import pytest
from src.models.transaction import Transaction

def test_transaction_creation():
    tx = Transaction('tx1', 100.0, 'USD', 'acc1', 'acc2')
    assert tx.amount == 100.0
    assert tx.currency == 'USD'
""",
    "tests/integration/test_api.py": """# Integration tests pending database selection
# Cannot write integration tests until storage layer is decided
""",
    "docs/architecture/adr-001-storage-options.md": """# ADR-001: Transaction Storage Selection

## Status: OPEN

## Context
Our fintech ledger processes ~200k transactions/day with strict ACID requirements.
Team size: 4 engineers, limited ops capacity.

## Options
1. **PostgreSQL** - Team familiar, strong ACID, vertical scaling limits
2. **MongoDB** - Flexible schema, horizontal scaling, weaker consistency
3. **Cassandra** - Extreme write throughput, eventual consistency, high ops overhead

## Decision
PENDING - blocked on technical advisory input

## Consequences
TBD
""",
    "docs/architecture/system-overview.md": """# Fintech Ledger System Overview

## Components
- REST API (Flask)
- Transaction Processing Engine
- Account Management
- Reporting Module

## Scale Requirements
- 200k transactions/day (~2.3 TPS average, 50 TPS peak)
- 99.99% uptime SLA
- Sub-100ms p99 latency
- 7-year data retention (regulatory)
""",
    "scripts/migrate.sh": """#!/bin/bash
# Migration script - placeholder
echo "No DB configured yet"
exit 1
""",
    "deploy/docker-compose.yml": """version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
  # db service TBD - pending storage decision
""",
}

for filepath, content in files.items():
    full_path = project_dir / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content)

# Create the openclaw workspace dir (but NOT the council session dir - agent must create it)
openclaw_pr_review = workspace / ".openclaw" / "workspace" / "pr-review"
openclaw_pr_review.mkdir(parents=True, exist_ok=True)

# Write a context file the agent will need
context_file = workspace / "db-decision-context.md"
context_file.write_text("""# Database Selection Context for Fintech Ledger

## Background
Our startup is building a financial transaction ledger. We're at the architectural crossroads
of selecting a primary storage engine. This decision will affect us for the next 5+ years.

## The Three Options

### Option A: PostgreSQL
- Team has 3 years experience with it
- Strong ACID guarantees, mature ecosystem
- Concern: vertical scaling limits as we grow

### Option B: MongoDB  
- Flexible document model for evolving transaction schemas
- Good horizontal scaling story
- Concern: default eventual consistency, requires careful configuration for financial data

### Option C: Cassandra
- Designed for massive write throughput (our peak is 50 TPS, future could be 5000 TPS)
- True horizontal scaling
- Concern: steep learning curve, no native JOINs, eventual consistency by default, heavy ops burden for 4-person team

## Constraints
- Team: 4 engineers, 1 part-time DevOps
- Budget: minimal, prefer managed services
- Regulatory: ACID compliance preferred for ledger entries
- Timeline: need decision in 1 week

## Decision needed
Which storage engine best fits our fintech ledger use case?
""")

print("Workspace generated successfully.")
print(f"Project dir: {project_dir}")
print(f"Council archive target: {openclaw_pr_review}")
print(f"Context file: {context_file}")