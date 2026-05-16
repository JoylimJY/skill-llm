import os
import random
from pathlib import Path
from datetime import datetime

random.seed(42)

workspace = Path("/workspace")

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "src/notifier",
    "src/router",
    "src/escalation",
    "src/integrations/slack",
    "src/integrations/pagerduty",
    "tests/unit",
    "tests/integration",
    "docs/adr",
    "docs/plans",        # target dir must exist but be empty
    "scripts",
    "config",
    ".github/workflows",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor source files ─────────────────────────────────────────────────
(workspace / "src/notifier/__init__.py").write_text("# notifier package\n")
(workspace / "src/notifier/sender.py").write_text(
    """import smtplib

def send_email(to, subject, body):
    \"\"\"Legacy email sender - known latency issues above 500 msgs/s\"\"\"
    pass  # TODO: implement retry logic
""")

(workspace / "src/router/__init__.py").write_text("# router package\n")
(workspace / "src/router/rules.py").write_text(
    """# Rule engine - currently uses linear scan O(n) over all rules
RULES = []

def match(alert):
    for rule in RULES:
        if rule.matches(alert):
            return rule.destination
    return 'default'
""")

(workspace / "src/escalation/__init__.py").write_text("")
(workspace / "src/escalation/policy.py").write_text(
    """# Escalation policy - hard-coded 5-minute window
ESCALATION_MINUTES = 5

class EscalationPolicy:
    def __init__(self, levels):
        self.levels = levels  # list of on-call user IDs per level

    def next_level(self, current_level):
        if current_level + 1 < len(self.levels):
            return self.levels[current_level + 1]
        return None  # no more escalation levels → alert drops silently (BUG?)
""")

(workspace / "src/integrations/slack/__init__.py").write_text("")
(workspace / "src/integrations/slack/webhook.py").write_text(
    """import requests

SLACK_WEBHOOK_URL = None  # must be set via env

def post_message(channel, text):
    if not SLACK_WEBHOOK_URL:
        raise RuntimeError('SLACK_WEBHOOK_URL not configured')
    requests.post(SLACK_WEBHOOK_URL, json={'channel': channel, 'text': text})
""")

(workspace / "src/integrations/pagerduty/__init__.py").write_text("")
(workspace / "src/integrations/pagerduty/client.py").write_text(
    """# PagerDuty Events API v2 wrapper
# Rate limit: 120 req/min per service key

class PDClient:
    def trigger(self, summary, severity='critical', dedup_key=None):
        pass  # Not yet implemented
""")

(workspace / "tests/unit/test_router.py").write_text(
    """import pytest

def test_match_returns_default_when_no_rules():
    from src.router.rules import match
    class FakeAlert: pass
    assert match(FakeAlert()) == 'default'
""")

(workspace / "tests/integration/test_escalation.py").write_text(
    """# Integration test skeleton - not yet runnable
def test_full_escalation_chain():
    pass
""")

(workspace / "scripts/seed_rules.py").write_text(
    """#!/usr/bin/env python3
\"\"\"One-off script to seed initial routing rules into DB\"\"\"
# TODO: connect to DB
""")

(workspace / "config/routing.yaml").write_text(
    """# Routing configuration (DRAFT - not validated)
default_channel: '#alerts-general'
max_retries: 3
retry_backoff_seconds: 10
# missing: priority tiers, on-call schedule integration
""")

(workspace / ".github/workflows/ci.yml").write_text(
    """name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install pytest
      - run: pytest tests/
""")

(workspace / "docs/adr/001-use-webhook-for-slack.md").write_text(
    """# ADR 001: Use Slack Incoming Webhooks

## Status: Accepted

## Context
Need to post alert notifications to Slack channels.

## Decision
Use Incoming Webhooks (simpler than full Slack app).

## Consequences
- No interactive components possible via webhook alone.
- Webhook URL must be stored as secret.
""")

# ── The "messy brief" that the agent must read ──────────────────────────────
(workspace / "BRIEF.md").write_text(
    """# Feature Request: Smart Alert Routing v2

**Raised by:** Priya (Head of Engineering)
**Date:** 2024-03-15

## Problem (roughly)
Right now every alert from our monitoring stack hits the same Slack channel.
Engineers ignore most of them because of noise. On-call people miss the critical ones.
We need something smarter.

## Vague wishlist
- Route alerts by severity / service / team
- Escalate if nobody acknowledges within some window
- Integrate with both Slack and PagerDuty
- Maybe support on-call schedule rotation? 
- Some kind of suppression for known flapping services?
- Dashboard? (probably out of scope for now)
- Could we do ML-based noise filtering? (stretch goal, maybe never)

## Constraints we know about
- Can't break existing Slack webhooks (customers depend on them)
- PagerDuty rate limit is a concern at scale
- Team has 2 engineers available for 6 weeks

## Open questions
- Do we need real-time routing or is eventual-consistency OK?
- Should rules be code or UI-configurable?
- Who owns the on-call schedule data?

## Current pain points in the code
- rules.py is O(n) – fine for now, may bottleneck at >10k rules
- escalation/policy.py silently drops alerts at the last level (see comment in code)
- No dedup logic anywhere
""")

# ── Skill scaffold (the SKILL.md the agent will reference) ─────────────────
skill_dir = workspace / ".claude/skills/brainstorm"
skill_dir.mkdir(parents=True, exist_ok=True)
refs_dir = skill_dir / "references"
refs_dir.mkdir(exist_ok=True)

(skill_dir / "SKILL.md").write_text(
    open("/dev/stdin").read() if False else
    """---
name: brainstorm
description: 把模糊想法变成可执行方案。唤醒词: /brainstorm, /bs, 脑暴, 头脑风暴
version: 1.0.0
metadata:
  openclaw:
    emoji: "🧠"
  requires:
    bins:
      - python3
---

# 设计对话引导

将零散的想法，通过对话梳理成清晰的设计蓝图。

## 引导心法

与其一次抛出大量问题，不如：
- **逐步深入** - 先建立共识，再细化细节
- **提供选项** - 让选择比描述更容易
- **敢于删减** - 每个功能都要有存在的理由
- **多维对比** - 好方案是比较出来的
- **小步确认** - 每一步都确保方向正确

## 对话三步法

### 第一步：建立共识

搞清楚"做什么"和"为什么做"

**先看项目现状**
- 瞄一眼相关代码和文档
- 了解现有架构和技术选型
- 感受项目的风格和习惯

**再逐个确认**
- 每次只聊一个话题
- 关键问题用选择题形式
- 一次问多个问题时，问题带编号（①②③）

**多问题回复格式**
告诉用户用「编号+选项」回复，空格或逗号分隔：
```
① 资讯类型？A.AI B.财经 C.都要
② 来源偏好？A.公众号 B.Twitter C.RSS
③ 输出形式？A.推送 B.存档 C.都要

回复示例: 1A 2C 3B 或 1A, 2C, 3B
```

**要明确的重点**
- 为什么要做这个？（动机）
- 有什么限制？（约束）
- 怎样算成功？（验收标准）

→ **出口条件**：能用一句话说清楚要解决的问题

### 第二步：构思方案

提出多个可行路径，权衡后做出选择

**给出 2-3 条路**
- 每条路都能走通
- 各有不同的取舍
- 覆盖从保守到激进的选项

**说清楚利弊**
- 每个方案的优缺点
- 适用什么场景
- 实现难度如何

**先表明倾向**
```
我倾向于方案 B，因为：
1. 复用现有组件，成本低
2. 团队熟悉这个技术栈
3. 能满足当前需求

代价是：扩展性不如方案 C

你更倾向哪个？或者有其他想法？
```

→ **出口条件**：确定要走的路线

### 第三步：细化设计

把选定方案展开成可执行的细节

**分段呈现**（每段控制篇幅）
- 一次性给太多信息会消化不良
- 每个部分讲清楚再往下

**逐段确认**
```
这部分 OK 吗？需要调整哪里？
```

**覆盖的设计要素**
1. 整体架构 - 大图景
2. 核心组件 - 关键模块
3. 数据流转 - 信息怎么流动
4. 异常处理 - 出问题怎么办
5. 测试思路 - 怎么验证正确性
6. 边界情况 - 特殊场景

**随时可以回退**
- 某个点卡住了就停下来
- 回到前面重新对齐理解
- 不要硬着头皮往下推

→ **出口条件**：设计获得确认

## 设计定稿后

### 输出文档

写入 `docs/plans/YYYY-MM-DD-<主题>-design.md`

格式参考 [输出模板](references/output-templates.md)

别忘了提交到 git。

### 继续实现

```
设计完成了，接下来要开始实现吗？
```

如果确认，可以：
1. 生成实现计划
2. 在独立分支开始编码

## 典型场景应用

### 用户想法很模糊

```
"我想做一个好用的工具"
```

**引导方式**：
1. "主要解决什么问题？"
2. "给谁用的？"
3. "现在怎么解决的？有什么不满意？"

### 功能需求太多

```
"我要 A、B、C、D、E..."
```

**引导方式**：
1. 列出来全部功能
2. "第一版必须有哪几个？"
3. 解释分阶段的好处
4. 帮助砍掉暂时不需要的

### 需求反复变化

**引导方式**：
1. 暂停细化设计
2. "我注意到有变化，重新确认下核心目标..."
3. 回到第一步重新对齐
4. 明确范围边界

## 参考资源

按需查阅：

- [问题模板](references/question-templates.md) - 各类场景怎么提问
- [设计模式](references/design-patterns.md) - 常见架构参考
- [输出模板](references/output-templates.md) - 文档格式规范
""")

# ── Output template (referenced by SKILL.md) ───────────────────────────────
(refs_dir / "output-templates.md").write_text(
    """# 输出模板

## 设计文档模板

```markdown
# <主题> 设计文档

## 问题陈述
<!-- 一句话说清楚要解决的问题 -->

## 方案对比

### 方案 A：<名称>
**优点：**
**缺点：**
**适用场景：**

### 方案 B：<名称>
**优点：**
**缺点：**
**适用场景：**

### 方案 C：（可选）<名称>
**优点：**
**缺点：**
**适用场景：**

## 选定方案

我倾向于方案 X，因为：
1. ...
2. ...
3. ...

代价是：...

## 整体架构

<!-- 大图景，主要模块和它们的关系 -->

## 核心组件

<!-- 每个关键模块的职责 -->

## 数据流转

<!-- 信息如何在系统中流动 -->

## 异常处理

<!-- 出问题时怎么办 -->

## 测试思路

<!-- 怎么验证正确性 -->

## 边界情况

<!-- 特殊场景和极端输入 -->
```
""")

(refs_dir / "question-templates.md").write_text(
    """# 问题模板

## 澄清动机
- 为什么现在要做这个？
- 不做会有什么影响？

## 约束摸底
- 时间、人力、技术有什么限制？
- 有哪些不能动的现有系统？

## 验收标准
- 做完什么算成功？
- 怎么衡量效果？
""")

(refs_dir / "design-patterns.md").write_text(
    """# 设计模式参考

## 事件驱动架构
适合：解耦生产者和消费者，支持扩展

## 规则引擎
适合：业务规则复杂、经常变化

## 优先级队列
适合：需要按优先级处理任务
""")

print("Workspace generated successfully.")
print(f"Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")