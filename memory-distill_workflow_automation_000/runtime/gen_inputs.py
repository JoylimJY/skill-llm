import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# === Create realistic distractor directory structure ===
dirs = [
    "docs/architecture",
    "docs/api",
    "src/core",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "memory",
    "logs",
    "configs",
    "reports/weekly",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "docs/architecture/system-design.md": "# System Design\n\nMicroservices architecture with event-driven messaging.\n",
    "docs/api/endpoints.md": "# API Endpoints\n\nGET /health\nPOST /distill\nGET /memory\n",
    "src/core/engine.py": "# Core engine placeholder\nclass Engine:\n    pass\n",
    "src/utils/parser.py": "# Parser utility\ndef parse(text): return text.split()\n",
    "tests/unit/test_engine.py": "import pytest\ndef test_placeholder(): assert True\n",
    "tests/integration/test_flow.py": "import pytest\ndef test_integration(): pass\n",
    "logs/app.log": "[2024-01-15 10:23:11] INFO: Service started\n[2024-01-15 10:23:12] INFO: Ready\n",
    "configs/app.yaml": "env: production\ndebug: false\nport: 8080\n",
    "reports/weekly/week-01.md": "# Week 1 Report\nCompleted onboarding tasks.\n",
    "reports/weekly/week-02.md": "# Week 2 Report\nStarted feature development.\n",
    ".gitignore": "*.pyc\n__pycache__/\n.env\n",
    "requirements.txt": "fastapi==0.104.0\npydantic==2.0.0\n",
}

for rel_path, content in distractor_files.items():
    p = workspace / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# === Create OLD memory files that should be flagged as expired ===
today = datetime.now()
old_dates = [
    today - timedelta(days=45),
    today - timedelta(days=60),
    today - timedelta(days=35),
]
recent_dates = [
    today - timedelta(days=5),
    today - timedelta(days=10),
]

for d in old_dates:
    fname = workspace / "memory" / f"{d.strftime('%Y-%m-%d')}.md"
    fname.write_text(
        f"# {d.strftime('%Y-%m-%d')} 记忆蒸馏摘要\n\n"
        f"### 决策\n- 使用 Redis 作为缓存层 - 上下文：性能优化会议\n\n"
        f"### 任务\n- [ ] 配置 Redis 集群 - 截止：{(d + timedelta(days=7)).strftime('%Y-%m-%d')}\n",
        encoding="utf-8"
    )

for d in recent_dates:
    fname = workspace / "memory" / f"{d.strftime('%Y-%m-%d')}.md"
    fname.write_text(
        f"# {d.strftime('%Y-%m-%d')} 记忆蒸馏摘要\n\n"
        f"### 知识点\n- CI/CD Pipeline：配置了 GitHub Actions 自动部署流程\n",
        encoding="utf-8"
    )

# === THE MAIN INPUT: A messy raw conversation transcript ===
# This contains items from ALL categories that need to be classified
today_str = today.strftime("%Y-%m-%d")

conversation_transcript = f"""=== 产品团队对话记录 ===
日期：{today_str}
参与者：张明（产品经理）、李华（技术负责人）、王芳（设计师）

[09:15] 张明：好，大家注意一下，我们已经决定把新版本的发布日期定在下个月15号，这个是最终决定了。

[09:17] 李华：确认收到。那我需要记得在本周五之前完成数据库迁移脚本，这个很关键，记得提醒我。

[09:20] 王芳：我喜欢用 Figma 做原型，以后设计文件都放在 Figma 里好了，我偏好这种协作方式。

[09:22] 张明：好的，另外我们定下来了，项目名称就叫"凤凰计划"，项目成员包括我们三个加上测试的陈强，当前状态是开发中。

[09:25] 李华：我发现了一个新概念——零知识证明，这个技术可以用在我们的用户认证模块，值得研究一下。

[09:28] 王芳：临时提醒一下，测试环境的临时访问码是 TMP-8847-XKQZ，今天下午要用，用完作废的。

[09:31] 李华：还有一个待办事项，要做用户权限管理模块的设计文档，目标是下周三前完成。

[09:35] 张明：我们确认一下，技术栈选 FastAPI + PostgreSQL，这是最终技术架构决定，不再改了。

[09:40] 李华：新发现，PostgreSQL 的 JSONB 类型性能比普通 JSON 列快很多，我们的数据模型要利用这个特性。

[09:45] 王芳：我偏好每周一早上开站会，时间控制在15分钟内。
"""

(workspace / "raw_conversation.txt").write_text(conversation_transcript, encoding="utf-8")

# === A partially broken existing MEMORY.md with some old content ===
existing_memory = """# 项目记忆库

## 历史决策
- 2024-01-10: 选择使用微服务架构 - 上下文：系统扩展性需求

## 历史知识点
- Docker 多阶段构建：减少镜像体积的有效方式

"""
(workspace / "MEMORY.md").write_text(existing_memory, encoding="utf-8")

# Note: USER.md does NOT exist yet - agent must create it
# Note: distill-config.json does NOT exist yet - agent must create it
# Note: memory/TODAY.md does NOT exist yet - agent must create it

print("Workspace initialized successfully.")
print(f"Today's date: {today_str}")
print(f"Old memory files created: {[d.strftime('%Y-%m-%d') for d in old_dates]}")
print(f"Recent memory files created: {[d.strftime('%Y-%m-%d') for d in recent_dates]}")