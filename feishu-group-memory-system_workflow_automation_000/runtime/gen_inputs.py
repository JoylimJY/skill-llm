import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Create directory structure ---
dirs = [
    "memory/FeishuGroupMemory",
    "memory/archive",
    "references",
    "logs",
    "config",
    "sessions",
    "notes/personal",
    "notes/projects",
    "scripts",
    "tmp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Fixed date for determinism ---
TODAY = "2026-04-15"
YESTERDAY = "2026-04-14"
TARGET_CHAT_ID = "oc_1736efe0d350b597267e3ed59bcc8f42"

# --- DISTRACTOR FILES ---

# 1. Old daily memory files
old_memory_content = """# 2026-04-13

## 早晨回顾
- 昨天完成了数据库迁移的第一阶段
- 确认了后端 API 的接口规范

## 工作记录
- 完成 PR #234 的代码审查
- 更新了 K8s 的部署配置

## 明天计划
- 开始性能测试
"""
(workspace / "memory/2026-04-13.md").write_text(old_memory_content, encoding="utf-8")

# 2. Yesterday's daily memory (distractor - no group chat section yet)
yesterday_memory_content = """# 2026-04-14

## 早晨回顾
- 回顾了昨天的 API 设计决策
- 确认 Redis 缓存策略

## 工作记录
- 与产品团队对齐了 Q2 路线图
- 完成了单元测试覆盖率提升到 82%

## 其他备注
- 需要跟进 infra 团队的 cost 优化方案
"""
(workspace / f"memory/{YESTERDAY}.md").write_text(yesterday_memory_content, encoding="utf-8")

# 3. Today's daily memory - already has SOME content but NO group chat section
today_memory_content = """# 2026-04-15

## 早晨回顾
- 今天需要完成群聊记忆存档
- 跟进昨天遗留的 3 个技术问题

## 工作记录
- 参加了早会，确认了 sprint 目标
- 修复了登录模块的 bug #501

"""
(workspace / f"memory/{TODAY}.md").write_text(today_memory_content, encoding="utf-8")

# 4. EXISTING group memory file for target chat (CRITICAL: agent must NOT overwrite this)
existing_group_memory = """# 工程核心群 - 对话记忆

## 最后更新时间
2026-04-14 22:30

## 关键决策
- 决定采用 gRPC 替代 REST 用于内部微服务通信（2026-04-10）
- 确认 PostgreSQL 为主数据库，Redis 为缓存层（2026-04-12）
- 代码审查必须至少 2 人 approve（2026-04-14）

## 待办事项
- [ ] 完成 gRPC proto 文件定义（负责人：张伟）
- [ ] 搭建 staging 环境（负责人：李明）
- [ ] 编写数据库迁移脚本（负责人：王芳）

## 重要上下文
- 团队目前 6 人，分前后端各 3 人
- 项目代号 "ProjectNova"，目标 2026-06 上线
- 主要技术栈：Go + React + PostgreSQL + Redis + K8s

## 对话摘要
### 2026-04-14
团队确定了代码审查规范，要求至少 2 人 approve 才能合并。讨论了 CI/CD 流水线的优化方案，决定引入 GitHub Actions 替代现有的 Jenkins。
"""
(workspace / f"memory/FeishuGroupMemory/{TARGET_CHAT_ID}.md").write_text(
    existing_group_memory, encoding="utf-8"
)

# 5. Another group memory file (distractor)
other_chat_id = "oc_f1098998d86e69b7a5043a61bcc9d123"
(workspace / f"memory/FeishuGroupMemory/{other_chat_id}.md").write_text(
    """# 产品讨论群 - 对话记忆

## 最后更新时间
2026-04-10 18:00

## 关键决策
- 新功能优先级：用户通知 > 数据导出 > 报表

## 待办事项
- [ ] 完成用户通知模块原型

## 重要上下文
- 讨论了 Q2 的产品路线图

## 对话摘要
### 2026-04-10
产品和技术团队对齐了 Q2 优先级，确认用户通知模块为第一优先级。
""",
    encoding="utf-8",
)

# 6. References file
(workspace / "references/group-ids.md").write_text(
    f"""# 已知飞书群聊 ID 列表

| Chat ID | 用途 | 备注 |
|---------|------|------|
| `{TARGET_CHAT_ID}` | 工程核心群 | 核心研发团队 |
| `{other_chat_id}` | 产品讨论群 | 产品+技术跨团队 |
""",
    encoding="utf-8",
)

# 7. Raw session/conversation data that the agent needs to summarize and archive
raw_session_log = f"""# 群聊会话记录 - 待存档

**Chat ID**: {TARGET_CHAT_ID}
**群聊名称**: 工程核心群
**日期**: 2026-04-15
**时间**: 09:30 - 14:45

---

[09:32] 张伟: gRPC proto 文件已经定义完成，提了 PR #241，大家有空看一下
[09:35] 李明: 好的，待会看。staging 环境今天下午应该能搭好，用的是之前说的 helm chart 方案
[09:40] 王芳: 数据库迁移脚本我跑了一遍，本地没问题。有个问题想确认一下——users 表的 email 字段要不要加唯一索引？
[09:42] 张伟: 必须加，之前讨论过的，email 是登录唯一标识
[09:43] 王芳: 明白，那我更新脚本，加上 UNIQUE INDEX
[10:15] 李明: staging 环境遇到问题了，K8s namespace 配置有冲突，跟 ops 团队沟通一下
[10:20] 赵磊（ops）: 我看了，是 resource quota 设置太低了，我来调整
[10:35] 赵磊（ops）: 好了，你重试一下
[10:38] 李明: 可以了！staging 环境搭好了，地址：staging.projectnova.internal
[11:00] 张伟: PR #241 已经有 2 个 approve 了，合并进 main
[11:05] 王芳: 数据库迁移脚本更新完成，加了 email 字段的唯一索引，PR #242
[14:30] 全体: 下午站会确认——gRPC 接口联调安排在明天上午 10 点，需要前后端都在线
[14:45] 张伟: 保存上下文

---

## 本次对话关键信息

**完成的事项**:
1. gRPC proto 文件定义完成并合并（PR #241）
2. staging 环境搭建完成（staging.projectnova.internal）
3. 数据库迁移脚本更新，users 表 email 字段加了唯一索引（PR #242）

**新决策**:
- email 字段必须有唯一索引（确认）
- gRPC 接口联调时间：2026-04-16 上午 10 点，前后端全员参与

**更新的待办**:
- [x] 完成 gRPC proto 文件定义（张伟 - 已完成）
- [x] 搭建 staging 环境（李明 - 已完成）
- [ ] 完成数据库迁移脚本（王芳 - 已更新，待 review）
- [ ] gRPC 接口联调（2026-04-16 10:00）
"""
(workspace / "sessions/session_2026-04-15_engineering.md").write_text(
    raw_session_log, encoding="utf-8"
)

# 8. Distractor config files
(workspace / "config/openclaw.yaml").write_text(
    """version: 1.0
agent: openclaw
heartbeat_interval: 300
memory_dir: ~/.openclaw/workspace/memory
""",
    encoding="utf-8",
)

(workspace / "config/feishu_webhooks.yaml").write_text(
    """# Feishu webhook configurations
# DO NOT commit real tokens
webhooks:
  engineering: "https://open.feishu.cn/open-apis/bot/v2/hook/PLACEHOLDER"
""",
    encoding="utf-8",
)

# 9. AGENTS.md (distractor - needs group memory section added per skill)
(workspace / "AGENTS.md").write_text(
    """# OpenClaw Agent Configuration

## Every Session

1. 读取 `SOUL.md`
2. 读取 `USER.md`
3. 读取 `memory/YYYY-MM-DD.md`（今天 + 昨天）

## Capabilities

- 文件读写
- 网络请求（公开 API）
- 代码执行
""",
    encoding="utf-8",
)

# 10. SOUL.md (distractor)
(workspace / "SOUL.md").write_text(
    """# Soul Configuration

## 基本原则
- 帮助用户提高工作效率
- 保持简洁清晰的沟通

## 工作风格
- 主动确认模糊需求
- 优先考虑用户的长期利益
""",
    encoding="utf-8",
)

# 11. Some log files as distractors
(workspace / "logs/2026-04-14.log").write_text(
    "INFO: Session started\nINFO: Heartbeat check passed\nINFO: Session ended\n",
    encoding="utf-8",
)
(workspace / "logs/2026-04-15.log").write_text(
    "INFO: Session started at 09:00\nINFO: Processing group chat oc_1736efe0d350b597267e3ed59bcc8f42\n",
    encoding="utf-8",
)

# 12. Notes distractors
(workspace / "notes/personal/todo.md").write_text(
    "- 买菜\n- 健身\n- 读书30分钟\n", encoding="utf-8"
)
(workspace / "notes/projects/nova_spec.md").write_text(
    "# ProjectNova Spec\n\n## Architecture\nMicroservices with gRPC\n",
    encoding="utf-8",
)

# 13. A fake script file
(workspace / "scripts/cleanup.sh").write_text(
    "#!/bin/bash\n# Clean up old session files\nfind /tmp -name '*.session' -mtime +7 -delete\n",
    encoding="utf-8",
)

# 14. Archive distractor
(workspace / "memory/archive/2026-03.md").write_text(
    "# March 2026 Archive\n\nMonthly summary placeholder\n", encoding="utf-8"
)

print("Workspace initialized successfully.")
print(f"Target chat_id: {TARGET_CHAT_ID}")
print(f"Today's date for test: {TODAY}")
print("Key files created:")
print(f"  - memory/FeishuGroupMemory/{TARGET_CHAT_ID}.md  (EXISTING - must be merged, not overwritten)")
print(f"  - memory/{TODAY}.md  (EXISTING - must have group chat section APPENDED)")
print(f"  - sessions/session_2026-04-15_engineering.md  (raw session data to archive)")