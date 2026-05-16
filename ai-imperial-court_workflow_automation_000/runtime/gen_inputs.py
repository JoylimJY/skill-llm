import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create distractor directory structure
dirs = [
    "bin",
    "references",
    "records",
    "logs",
    "config",
    "templates",
    "archive/2025",
    "archive/2024",
    "tmp",
    "docs/internal",
    "docs/external",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# SKILL.md - main skill documentation
skill_md = r"""---
name: ai-imperial-court
description: |
  AI朝廷三省六部协作系统。将中国唐代三省六部制映射到多Agent协作框架，实现"起草-审核-执行"的分权制衡流程。
  
  触发场景：
  - 用户要求多Agent协作完成任务
  - 需要评审、质检、审核流程
  - 复杂任务需要分解与协调
  - 提及"朝廷"、"三省"、"六部"、"封驳"、"协作"等关键词
  - 需要角色扮演式任务处理
---

# AI朝廷三省六部

将唐代三省六部制转化为多Agent协作框架，实现分权制衡与专业化分工。

## 核心理念

```
┌─────────────────────────────────────────────────────────────┐
│                         用  户 (皇帝)                        │
└─────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────┐              ┌─────────────────┐
│    中书省       │              │    门下省       │
│  (规划起草)     │───────────▶  │  (审核封驳)     │
│  规划Agent      │   草案       │  评审Agent      │
└─────────────────┘              └─────────────────┘
          │                              │
          │         通过                 │
          └──────────────────────────────┘
                         │
                         ▼
              ┌─────────────────┐
              │    尚书省       │
              │  (执行调度)     │
              │  执行调度器     │
              └─────────────────┘
                         │
          ┌──────┬──────┼──────┬──────┬──────┐
          ▼      ▼      ▼      ▼      ▼      ▼
        吏部   户部   礼部   兵部   刑部   工部
       人事   财务   文档   策略   合规   工程
```

## 三省职责

### 中书省 — 规划起草

**触发时机：** 接收用户任务后第一步

**核心职责：**
1. 分析任务需求
2. 制定执行计划
3. 起草方案草案
4. 分配六部职责

**输出格式：**
```markdown
## 诏令草案 [任务ID]

### 任务分析
- 背景：
- 目标：
- 约束：

### 执行计划
1. [步骤1] - 负责部门：工部
2. [步骤2] - 负责部门：吏部
3. ...

### 资源分配
- 吏部：[人力需求]
- 户部：[预算需求]
- 工部：[技术需求]

### 预期产出
- [产出物1]
- [产出物2]

---
起草：中书省
时间：[ISO时间]
```

---

### 门下省 — 审核封驳

**触发时机：** 收到中书省草案后

**核心职责：**
1. 审核方案可行性
2. 检查遗漏与风险
3. 提出修改建议
4. 决定通过/封驳

**审核清单：**
```markdown
## 门下省审核表

### 可行性检查
- [ ] 技术可行性
- [ ] 资源充足性
- [ ] 时间合理性
- [ ] 依赖完整性

### 风险检查
- [ ] 安全风险
- [ ] 合规风险
- [ ] 依赖风险

### 遗漏检查
- [ ] 边界情况
- [ ] 异常处理
- [ ] 回滚方案

### 决定
- [ ] 通过 - 可交付尚书省执行
- [ ] 封驳 - 需中书省重拟，原因：[具体原因]

---
审核：门下省
时间：[ISO时间]
```

**封驳权：** 门下省有权直接驳回不合规方案，中书省必须修改后重新提交

---

### 尚书省 — 执行调度

**触发时机：** 门下省审核通过后

**核心职责：**
1. 接收通过诏令
2. 调度六部执行
3. 监控执行进度
4. 汇报执行结果

**执行报告格式：**
```markdown
## 执行报告 [任务ID]

### 执行状态
| 部门 | 任务 | 状态 | 产出 |
|------|------|------|------|
| 工部 | [任务] | ✅ 完成 | [链接/文件] |
| 吏部 | [任务] | 🔄 进行中 | - |

### 问题与决策
- [问题1] → 决策：[处理方式]
- [问题2] → 决策：[处理方式]

### 最终产出
- [产出物1]：[链接/内容]
- [产出物2]：[链接/内容]

---
执行：尚书省
时间：[ISO时间]
```

---

## 六部专长

| 部门 | 职责 | 适用场景 |
|------|------|----------|
| **吏部** | 人事管理、Agent调度、角色分配 | 团队组建、角色定义、权限管理 |
| **户部** | 预算管理、资源规划、成本估算 | 预算评估、资源分配、ROI分析 |
| **礼部** | 文档撰写、沟通协调、对外交互 | 文档生成、报告撰写、用户沟通 |
| **兵部** | 策略制定、竞争分析、方案对比 | 技术选型、方案PK、竞争策略 |
| **刑部** | 合规检查、安全审计、风险识别 | 代码审计、安全检查、合规验证 |
| **工部** | 工程实施、代码构建、技术实现 | 编码、部署、测试、运维 |

**详细说明：** 见 [references/six-ministries.md](references/six-ministries.md)

---

## 工作流程

### 标准流程

```
用户请求 → 中书省起草 → 门下省审核 → [通过?]
                                          ↓
                     ┌─────── 否 ────────┤
                     ↓                    ↓
              中书省重拟              尚书省执行
                                          ↓
                                    六部协作
                                          ↓
                                    执行报告 → 用户
```

### 快速流程（简单任务）

对于简单任务（单步骤、无依赖），可跳过门下省审核：

```
用户请求 → 中书省起草（简化版）→ 尚书省执行 → 结果返回
```

**简单任务判定标准：**
- 单一步骤
- 无外部依赖
- 无安全风险
- 无合规要求

---

## 使用示例

### 示例1：代码项目开发

```
用户：帮我开发一个命令行TODO工具

中书省起草：
├── 分析：CLI工具，需文件存储，Python实现
├── 计划：工部负责开发，刑部负责安全检查，礼部负责文档
└── 预期：可执行CLI + README

门下省审核：
├── 检查：技术可行 ✅，资源充足 ✅，时间合理 ✅
├── 风险：无安全风险 ✅
└── 决定：通过

尚书省执行：
├── 工部：开发 todo.py
├── 刑部：检查文件操作安全性
├── 礼部：编写 README.md
└── 交付：可执行工具 + 文档
```

### 示例2：复杂决策（封驳场景）

```
用户：帮我设计一个支付系统

中书省起草：
├── 分析：支付网关，对接支付宝/微信
├── 计划：工部开发，户部预算...
└── [遗漏：安全审计、合规检查]

门下省审核：
├── 检查：技术可行 ✅
├── 风险：支付安全风险 ❌（未提及）
├── 合规：PCI-DSS ❌（未考虑）
└── 决定：封驳
    └── 原因：缺少安全审计方案，需补充刑部安全检查、合规评估

中书省重拟：
├── 补充：刑部安全审计，合规检查
├── 新增：沙箱测试阶段
└── 重新提交 → 门下省 → 通过
```

---

## 历史典故参考

三省制起源于隋唐，核心是**分权制衡**：

- **唐太宗贞观之治**：魏征（门下省给事中）多次封驳诏令，太宗虚心接受
- **斜封官事件**：唐中宗绕过三省直接任命，被朝野耻笑
- **王安石变法**：门下省封驳青苗法，朝堂博弈

**核心价值：** 即使是"皇帝"（用户）的命令，也要经过审核才能执行。这不是效率问题，是质量与安全的问题。

---

## 🚀 快速启动

### 一键生成工作流文档

```bash
node bin/court-start.js "任务名称"
```

将生成三个文档：
- `records/{id}-draft.md` — 诏令草案
- `records/{id}-review.md` — 审核表格
- `records/{id}-exec.md` — 执行报告

### 常用命令

| 命令 | 说明 |
|------|------|
| `启动朝廷 [任务]` | 启动完整工作流 |
| `中书省起草 [任务]` | 仅起草阶段 |
| `门下省审核` | 审核当前方案 |
| `尚书省执行` | 执行通过方案 |
| `六部汇报` | 各部门状态汇报 |

---

## 📚 参考文档

- [六部详解](references/six-ministries.md) — 六部职责与输出格式
- [执行示例](references/examples.md) — 常见场景示例

---

## 注意事项

1. **封驳不是拒绝**：是要求改进，最终目标是把事情做好
2. **三省协作而非对抗**：共同为用户负责，而非互相刁难
3. **灵活运用**：简单任务简化流程，复杂任务严格流程
4. **保留记录**：所有诏令、审核、执行报告应记录存档

---

## 更新日志

### v1.1.0 (2026-03-21)
- ✨ 新增快速启动脚本 `bin/court-start.js`
- 📚 新增执行示例文档 `references/examples.md`
- 📝 完善命令参考表

### v1.0.0 (2026-03-18)
- 🎉 初始发布
- ✨ 三省六部协作框架
- ✨ 分权制衡工作流

---

*此技能借鉴唐代三省六部制的智慧，应用于AI Agent协作。让每项任务都经过规划、审核、执行的完整流程，确保质量与安全。*
"""

with open(workspace / "SKILL.md", "w", encoding="utf-8") as f:
    f.write(skill_md)

# references/six-ministries.md
six_ministries_md = r"""# 六部详解

尚书省统领六部，每部负责特定领域的执行工作。

## 吏部 — 人事管理

### 对应职能
- Agent/角色创建与配置
- 权限管理
- 任务分配
- 角色定义

### 输出格式
```markdown
## 吏部报告

### 团队配置
| 角色 | 职责 | 权限 |
|------|------|------|
| [角色名] | [职责] | [权限级别] |

### 任务分配
- [任务] → [角色] (截止时间: [时间])

### 执行状态
- [角色1]: ✅ 已完成
- [角色2]: 🔄 执行中 (进度: 60%)
```

### 使用场景
- 需要多个Agent协作
- 定义新角色/职能
- 权限分配
- 团队规模调整

---

## 户部 — 资源管理

### 对应职能
- 预算估算
- 资源需求评估
- 成本效益分析
- 优先级排序

### 输出格式
```markdown
## 户部报告

### 资源预算
- 计算资源：[估算]
- API调用：[估算]
- 存储空间：[估算]
- 人力时间：[估算]

### 成本效益分析
| 方案 | 成本 | 收益 | ROI |
|------|------|------|-----|
| 方案A | [成本] | [收益] | [ROI] |

### 优先级建议
1. [高优先级任务] - 收益/成本比最高
2. [中优先级任务] - 战略需要
3. [低优先级任务] - 可选
```

### 使用场景
- 多方案对比
- 预算限制
- 资源规划
- 投资回报评估

---

## 礼部 — 文档与沟通

### 对应职能
- 文档撰写
- 用户沟通
- 报告生成
- 对外展示

### 输出格式
```markdown
## 礼部报告

### 文档清单
- [文档1]：已完成 [链接]
- [文档2]：草稿 [链接]

### 沟通记录
- 用户反馈：[摘要]
- 修改建议：[摘要]

### 对外材料
- README.md：[链接]
- 使用指南：[链接]
- 演示文稿：[链接]
```

### 使用场景
- 需要用户文档
- 对外沟通
- 报告撰写
- 材料整理

---

## 兵部 — 策略与竞争

### 对应职能
- 技术选型
- 方案对比
- 竞争分析
- 策略制定

### 输出格式
```markdown
## 兵部报告

### 技术方案对比
| 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| A | ... | ... | ... |
| B | ... | ... | ... |

### 推荐方案
**推荐：[方案X]**
- 理由1：...
- 理由2：...

### 风险对策
- [风险] → [对策]
```

### 使用场景
- 技术选型
- 架构决策
- 方案PK
- 风险评估

---

## 刑部 — 合规与安全

### 对应职能
- 安全审计
- 合规检查
- 风险评估
- 代码审查

### 输出格式
```markdown
## 刑部报告

### 安全检查
| 检查项 | 状态 | 说明 |
|--------|------|------|
| 输入验证 | ✅ | 已验证 |
| SQL注入 | ❌ | 发现漏洞 |
| XSS防护 | ✅ | 已防护 |

### 合规检查
- [合规项1]: ✅ 符合
- [合规项2]: ❌ 不合规 [原因]

### 风险清单
1. [高危] [风险描述] → [整改建议]
2. [中危] [风险描述] → [整改建议]

### 整改要求
- [ ] 修复SQL注入漏洞
- [ ] 增加日志审计
```

### 使用场景
- 安全审计
- 代码审查
- 合规验证
- 风险识别

---

## 工部 — 工程实施

### 对应职能
- 代码编写
- 系统部署
- 测试验证
- 运维支持

### 输出格式
```markdown
## 工部报告

### 开发成果
- [文件1]: [链接] [行数] [状态]
- [文件2]: [链接] [行数] [状态]

### 测试结果
- 单元测试: [X]/[Y] 通过
- 集成测试: [状态]
- 性能测试: [指标]

### 部署信息
- 环境: [开发/测试/生产]
- 版本: [版本号]
- 访问: [URL/命令]

### 技术债务
- [ ] [待优化项1]
- [ ] [待优化项2]
```

### 使用场景
- 编码实现
- 系统部署
- 测试验证
- 性能优化

---

## 六部协作示例

### 场景：开发一个API服务

```
尚书省调度：

1. 吏部：
   - 定义角色：API开发者、测试工程师、文档工程师
   - 分配任务

2. 户部：
   - 评估：需要多少API调用额度
   - 预算：服务器成本、数据库成本

3. 礼部：
   - 编写API文档
   - 编写使用示例
   - 撰写CHANGELOG

4. 兵部：
   - 技术选型：FastAPI vs Flask vs Django
   - 推荐：FastAPI（异步、自动文档）
   - 数据库选型：PostgreSQL vs MySQL

5. 刑部：
   - 安全检查：认证机制、权限控制
   - 合规检查：数据加密、日志审计
   - 发现：缺少Rate Limiting

6. 工部：
   - 实现API端点
   - 编写单元测试
   - 部署到服务器
   - 配置CI/CD
```

---

## 历史典故

### 吏部
- 唐代的"铨选"制度，由吏部负责选拔官员
- 著名吏部尚书：长孙无忌

### 户部
- 掌管全国土地、户籍、赋税
- 唐代财政中枢

### 礼部
- 负责科举、外交、祭祀
- 科举考试的最高主管

### 兵部
- 名义上掌管军事，但唐代实际军权在节度使
- 兵部更多是军事行政

### 刑部
- 与大理寺、御史台合称"三法司"
- 重大案件需三司会审

### 工部
- 掌管工程、屯田、水利、交通
- 负责宫殿修建、水利设施

---

## 现代映射

| 六部 | 现代企业 | 软件开发 | AI Agent |
|------|----------|----------|----------|
| 吏部 | HR | Team Lead | Agent调度 |
| 户部 | CFO | PM | 资源规划 |
| 礼部 | PR/文档 | Tech Writer | 文档生成 |
| 兵部 | Strategy | Architect | 技术选型 |
| 刑部 | Compliance | Security | 安全审计 |
| 工部 | Engineering | Dev/SRE | 代码实现 |
"""

with open(workspace / "references/six-ministries.md", "w", encoding="utf-8") as f:
    f.write(six_ministries_md)

# references/examples.md
examples_md = r"""# 执行示例库

本文档包含常见场景的执行示例，可直接复制使用。

## 场景1：代码项目开发

### 诏令草案

```markdown
## 诏令草案 [proj-001]

### 任务分析
- **背景**: 开发一个CLI工具
- **目标**: 实现核心功能，编写文档
- **约束**: Python实现，无外部依赖

### 执行计划
1. 设计API接口 - 负责部门：兵部
2. 编写核心代码 - 负责部门：工部
3. 安全审计 - 负责部门：刑部
4. 编写文档 - 负责部门：礼部

### 预期产出
- 可执行CLI工具
- README.md
- 测试用例
```

### 门下省审核

```markdown
## 门下省审核表 [proj-001]

### 可行性检查
- [x] 技术可行性 - Python标准库足够
- [x] 资源充足性 - 无额外资源需求
- [x] 时间合理性 - 预计2小时
- [x] 依赖完整性 - 无外部依赖

### 风险检查
- [x] 安全风险 - 低风险
- [x] 合规风险 - 无合规要求
- [x] 依赖风险 - 无依赖

### 决定
✅ 通过 - 可交付尚书省执行
```

### 尚书省执行

```markdown
## 执行报告 [proj-001]

### 执行状态
| 部门 | 任务 | 状态 | 产出 |
|------|------|------|------|
| 兵部 | API设计 | ✅ 完成 | api.md |
| 工部 | 核心代码 | ✅ 完成 | main.py |
| 刑部 | 安全审计 | ✅ 完成 | audit.md |
| 礼部 | 文档编写 | ✅ 完成 | README.md |

### 最终产出
- CLI工具: ./cli.py
- 文档: README.md
- 测试: test_cli.py
```
"""

with open(workspace / "references/examples.md", "w", encoding="utf-8") as f:
    f.write(examples_md)

# bin/court-start.js stub (the skill mentions this exists)
court_start_js = """#!/usr/bin/env node
// court-start.js - Quick start script for AI Imperial Court workflow
// Usage: node bin/court-start.js "task name"

const task = process.argv[2];
if (!task) {
    console.error('Usage: node bin/court-start.js "task name"');
    process.exit(1);
}

const id = 'task-' + Date.now();
console.log('Workflow ID:', id);
console.log('Create these files:');
console.log('  records/' + id + '-draft.md');
console.log('  records/' + id + '-review.md');
console.log('  records/' + id + '-exec.md');
"""

with open(workspace / "bin/court-start.js", "w", encoding="utf-8") as f:
    f.write(court_start_js)

# Distractor files to simulate a real project
distractors = {
    "config/db-migration.yaml": """# Database Migration Config
source:
  host: legacy-db.internal
  port: 5432
  database: finance_legacy
  schema: public
target:
  host: new-db.internal
  port: 5432
  database: finance_v2
  schema: main
migration:
  batch_size: 1000
  parallel_workers: 4
  tables:
    - accounts
    - transactions
    - audit_log
    - user_profiles
""",
    "config/security-policy.json": json.dumps({
        "encryption": "AES-256",
        "tls_version": "1.3",
        "data_classification": "PCI-DSS",
        "audit_logging": True,
        "rate_limiting": False,
        "backup_required": True
    }, indent=2, ensure_ascii=False),
    "logs/migration-attempt-2024-11.log": """[2024-11-01 09:00:00] INFO Migration started
[2024-11-01 09:05:00] ERROR Connection timeout to legacy-db
[2024-11-01 09:05:01] INFO Retrying connection...
[2024-11-01 09:10:00] ERROR Max retries exceeded. Migration aborted.
[2024-11-01 09:10:01] INFO Rollback initiated
[2024-11-01 09:10:30] INFO Rollback complete
""",
    "logs/security-scan-2024.log": """Security Scan Report - 2024-12-01
Findings:
  HIGH: Unencrypted data transfer on port 3306
  MEDIUM: Missing audit log rotation
  LOW: Outdated TLS 1.0 configuration on legacy endpoints
Recommendation: Address HIGH findings before migration.
""",
    "archive/2024/old-schema.sql": """-- Legacy schema (archived)
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    balance DECIMAL(15,2),
    created_at TIMESTAMP
);
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id),
    amount DECIMAL(15,2),
    type VARCHAR(20),
    ts TIMESTAMP
);
""",
    "archive/2025/migration-notes.txt": """Migration Notes - Q1 2025
- Legacy DB has 2.3M transaction records
- Need zero-downtime migration window
- Compliance team requires PCI-DSS audit before go-live
- DBA team: 2 engineers available
- Budget: $15,000 estimated infrastructure cost
- Timeline: 6 weeks
- RISK: No rollback plan documented yet
""",
    "tmp/scratch.txt": """TODO:
- Ask about compliance requirements
- Get sign-off from security team
- Schedule maintenance window
""",
    "docs/internal/team-roster.md": """# Migration Team

| Name | Role | Availability |
|------|------|-------------|
| Alice Chen | DBA Lead | Full-time |
| Bob Kumar | Backend Engineer | Part-time |
| Carol Wu | Security Analyst | Consultant |
| David Lee | Project Manager | Full-time |
""",
    "docs/external/vendor-contract.txt": """Database Migration Services Agreement
Vendor: CloudMigrate Inc.
Contract ID: CM-2025-0042
Services: Schema migration, data validation, performance tuning
SLA: 99.9% uptime during migration window
Compliance: Vendor certified for PCI-DSS Level 1
""",
    "templates/report-template.txt": """# Project Status Report
Date: [DATE]
Project: [PROJECT_NAME]
Status: [ON_TRACK/AT_RISK/BLOCKED]
Progress: [X]%
Next Steps:
- [STEP_1]
- [STEP_2]
""",
}

for rel_path, content in distractors.items():
    full_path = workspace / rel_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")