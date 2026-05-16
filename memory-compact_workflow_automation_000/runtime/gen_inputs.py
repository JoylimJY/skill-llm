import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

workspace = Path("/root/.openclaw/workspace")

# Create directory structure
dirs = [
    workspace / "skills" / "memory-compact",
    workspace / "memory",
    workspace / "backup" / "memory",
    workspace / "scripts",
    workspace / "config",
    workspace / "logs",
    workspace / "drafts",
    workspace / "archive" / "old",
    workspace / "notes" / "weekly",
    workspace / "notes" / "monthly",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# ---------- The target daily memory file ----------
# Use a fixed "today" date for determinism
target_date = date(2026, 5, 14)
memory_filename = workspace / "memory" / f"{target_date}.md"

memory_content = """# 2026-05-14 对话记录

## 上午

用户询问了关于数据库优化的几个方案，讨论了索引策略和查询缓存。

经过反复比较，用户决定采用分布式缓存方案来提升系统响应速度。

讨论了几个开源框架，最终选定了 Redis 作为缓存层。

用户提到他很喜欢 Redis 的简单 API 设计，认为上手成本低。

## 下午

团队会议中，讨论了下季度的技术路线图。

用户记住了需要在月底前完成性能基线测试。

讨论了监控方案，决定引入 Prometheus + Grafana 作为可观测性基础设施。

用户提出了一个重要的安全审计需求，需要在正式上线前完成。

## 晚间

回顾了今天的工作进展，用户计划明天重点处理日志聚合模块的开发。

讨论了团队目标，确认 Q3 的主要方向是提升系统稳定性到 99.9% SLA。

用户讨厌过度复杂的配置文件，希望保持工具链的简洁性。
"""

memory_filename.write_text(memory_content, encoding="utf-8")

# ---------- Older memory files (already backed up / distractors) ----------
old_dates = [
    date(2026, 5, 10),
    date(2026, 5, 11),
    date(2026, 5, 12),
]
old_contents = [
    "# 2026-05-10 对话记录\n\n用户决定重构前端组件。\n",
    "# 2026-05-11 对话记录\n\n讨论了 CI/CD 流程改进。\n",
    "# 2026-05-12 对话记录\n\n用户记住了要更新文档。\n",
]
for d, c in zip(old_dates, old_contents):
    (workspace / "backup" / "memory" / f"{d}.md").write_text(c, encoding="utf-8")

# ---------- wrapper.py  (the entry-point script from SKILL.md) ----------
wrapper_script = workspace / "skills" / "memory-compact" / "wrapper.py"
wrapper_script.write_text(
    """#!/usr/bin/env python3
\"\"\"
Wrapper script for memory-compact skill.
Calls memory_backup.py with correct paths.
\"\"\"
import subprocess, sys, os

script_dir = os.path.dirname(os.path.abspath(__file__))
backup_script = os.path.join(script_dir, "memory_backup.py")

result = subprocess.run([sys.executable, backup_script], capture_output=False)
sys.exit(result.returncode)
""",
    encoding="utf-8",
)

# ---------- memory_backup.py (stub — the agent must write/complete it) ----------
# We intentionally DO NOT create memory_backup.py so the agent must create it.
# We only provide wrapper.py which calls memory_backup.py.

# ---------- Distractor files ----------
(workspace / "config" / "settings.json").write_text(
    '{"version": "1.0", "lang": "zh-CN", "theme": "dark"}', encoding="utf-8"
)
(workspace / "config" / "cron_jobs.json").write_text(
    '{"jobs": [{"name": "unused-job", "schedule": "0 0 * * *"}]}', encoding="utf-8"
)
(workspace / "scripts" / "cleanup.sh").write_text(
    "#!/bin/bash\necho 'Cleaning temp files...'\nfind /tmp -name '*.tmp' -delete\n",
    encoding="utf-8",
)
(workspace / "scripts" / "health_check.py").write_text(
    "import os\nprint('System healthy:', os.path.exists('/root/.openclaw'))\n",
    encoding="utf-8",
)
(workspace / "logs" / "system.log").write_text(
    "2026-05-13 23:00:01 INFO  cron started\n2026-05-13 23:00:02 INFO  all jobs ok\n",
    encoding="utf-8",
)
(workspace / "drafts" / "proposal_v1.md").write_text(
    "# Draft Proposal\n\n用户希望未来系统能支持多租户架构。\n",
    encoding="utf-8",
)
(workspace / "drafts" / "proposal_v2.md").write_text(
    "# Draft Proposal v2\n\n修订版：多租户支持将在 Q4 实现。\n",
    encoding="utf-8",
)
(workspace / "archive" / "old" / "2026-04-30.md").write_text(
    "# 四月总结\n\n完成了原型开发阶段。\n", encoding="utf-8"
)
(workspace / "notes" / "weekly" / "week18.md").write_text(
    "# 第18周\n\n本周重点：基础设施搭建。\n", encoding="utf-8"
)
(workspace / "notes" / "monthly" / "may.md").write_text(
    "# 五月计划\n\n- 完成缓存层\n- 性能测试\n- 安全审计\n", encoding="utf-8"
)
(workspace / "notes" / "monthly" / "april.md").write_text(
    "# 四月回顾\n\n原型已完成，进入测试阶段。\n", encoding="utf-8"
)

# Existing MEMORY.md from previous months (agent must append/update correctly)
(workspace / "MEMORY.md").write_text(
    """# MEMORY - 长期记忆

## 2026-05-10
1. 用户决定重构前端组件以提升可维护性
2. 团队讨论了代码审查规范

## 2026-05-11
1. CI/CD 流程改进方案已确定
2. 用户计划在下周完成自动化部署脚本
""",
    encoding="utf-8",
)

print("Workspace initialized successfully.")
print(f"Target memory file: {memory_filename}")