#!/usr/bin/env python3
"""
Generate the sandbox workspace for the memory-hub skill evaluation task.
Creates a realistic ~/.openclaw environment with a local bare git repo acting
as the "shared" remote, an existing clone, config, and distractor files.
"""
import os
import json
import subprocess
import random
import textwrap
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

HOME = Path(os.path.expanduser("~"))
OPENCLAW = HOME / ".openclaw"
SKILLS_DIR = OPENCLAW / "skills" / "shared-memory" / "scripts"
SHARED_MEM_DIR = OPENCLAW / "shared-memory"
WORKSPACE_DIR = OPENCLAW / "workspace"
BARE_REPO = HOME / ".openclaw" / "_bare_remote"  # acts as the "remote"

# ── Create directory structure ──────────────────────────────────────────────
for d in [SKILLS_DIR, SHARED_MEM_DIR, WORKSPACE_DIR, BARE_REPO]:
    d.mkdir(parents=True, exist_ok=True)

# ── Distractor files (≥10) ───────────────────────────────────────────────────
distractors = {
    OPENCLAW / "MEMORY.md": textwrap.dedent("""\
        # Local Agent Memory
        - Prefer Python 3.11
        - Use black formatter
        - Workspace: /workspace
    """),
    OPENCLAW / "AGENTS.md": textwrap.dedent("""\
        # Agent Config
        ## Every Session
        - Load local memory
        ## Rules
        - Be concise
    """),
    OPENCLAW / "skills" / "shared-memory" / "README.md": textwrap.dedent("""\
        # shared-memory skill
        See SKILL.md for usage.
    """),
    OPENCLAW / "workspace" / "task_log.txt": "Task log placeholder\n2026-06-01: initialized\n",
    OPENCLAW / "workspace" / "temp_notes.md": "## Scratch\nsome unrelated notes about kubernetes\n",
    OPENCLAW / "workspace" / "metrics.json": json.dumps({"cpu": 0.4, "mem": 1.2}, indent=2),
    OPENCLAW / "workspace" / "deploy_notes.txt": "Deploy v2.3 on 2026-05-30\nRollback plan: revert tag v2.2\n",
    HOME / ".openclaw" / "plugins" / "autocomplete.py": "# autocomplete stub\ndef complete(x): return []\n",
    HOME / ".openclaw" / "plugins" / "formatter.py": "# formatter stub\ndef fmt(s): return s.strip()\n",
    HOME / ".openclaw" / "logs" / "agent.log": "2026-06-01 INFO Agent started\n2026-06-01 INFO Session OK\n",
    HOME / ".openclaw" / "logs" / "sync.log": "2026-05-30 sync OK\n2026-05-29 sync OK\n",
    HOME / ".openclaw" / "cache" / "index.json": json.dumps({"version": 1, "entries": 0}),
}

for path, content in distractors.items():
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)

# ── Install script stub (exists but won't be called in this task) ────────────
install_sh = SKILLS_DIR / "install.sh"
install_sh.write_text("#!/bin/bash\necho 'install stub'\n")
install_sh.chmod(0o755)

# ── Initialize bare repo (the "remote") ─────────────────────────────────────
subprocess.run(["git", "init", "--bare", str(BARE_REPO)], check=True,
               capture_output=True)

# ── Initialize working repo and push initial content ────────────────────────
INIT_WORK = HOME / ".openclaw" / "_init_work"
INIT_WORK.mkdir(exist_ok=True)
subprocess.run(["git", "init", str(INIT_WORK)], check=True, capture_output=True)
subprocess.run(["git", "-C", str(INIT_WORK), "remote", "add", "origin", str(BARE_REPO)],
               check=True, capture_output=True)

# Populate the four canonical shared memory files
user_md = textwrap.dedent("""\
    ## [偏好] 代码审查风格

    主人喜欢简洁的 PR 描述，不超过5行，附带测试截图。

    _更新：2026-05-10 by agent-home_

    ## [偏好] 会议时间

    主人偏好上午10点前不排会议，保留深度工作时间。

    _更新：2026-05-15 by agent-office_
""")

knowledge_md = textwrap.dedent("""\
    ## [工具] Docker 多阶段构建缓存

    使用 `--mount=type=cache` 加速 pip/npm 安装，CI 速度提升40%。
    注意：缓存目录需要与 Dockerfile 路径一致。

    _更新：2026-04-20 by agent-home_

    ## [踩坑] Kubernetes HPA 冷启动

    HPA scaleUp 默认需要3分钟稳定期，压测时不要误判为 bug。
    调整 stabilizationWindowSeconds 可缩短至30s。

    _更新：2026-05-01 by agent-ci_
""")

rules_md = textwrap.dedent("""\
    ## [规范] 禁止硬编码密钥

    任何配置中不得出现明文密钥、token 或密码。
    使用环境变量或 secrets manager。

    _更新：2026-04-01 by agent-home_

    ## [规范] 变更必须有回滚方案

    所有生产变更必须在 PR 中描述回滚步骤。

    _更新：2026-04-15 by agent-office_
""")

tools_md = textwrap.dedent("""\
    ## [脚本] 快速清理 Docker 资源

    ```bash
    docker system prune -af --volumes
    ```
    谨慎使用，会删除所有未使用镜像和 volume。

    _更新：2026-05-05 by agent-home_

    ## [命令] 查看 Pod 日志最近100行

    ```bash
    kubectl logs <pod> --tail=100 -f
    ```

    _更新：2026-05-20 by agent-ci_
""")

(INIT_WORK / "USER.md").write_text(user_md)
(INIT_WORK / "KNOWLEDGE.md").write_text(knowledge_md)
(INIT_WORK / "RULES.md").write_text(rules_md)
(INIT_WORK / "TOOLS.md").write_text(tools_md)

subprocess.run(["git", "-C", str(INIT_WORK), "add", "-A"], check=True, capture_output=True)
subprocess.run(["git", "-C", str(INIT_WORK), "commit", "-m", "🧠 initial shared memory"],
               check=True, capture_output=True)
subprocess.run(["git", "-C", str(INIT_WORK), "push", "origin", "master"],
               check=True, capture_output=True)

# ── Clone from bare repo into the actual shared-memory working dir ───────────
subprocess.run(["git", "clone", str(BARE_REPO), str(SHARED_MEM_DIR)],
               check=True, capture_output=True)

# ── Write config.json ────────────────────────────────────────────────────────
last_sync = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S")
config = {
    "repo_url": str(BARE_REPO),
    "local_path": str(SHARED_MEM_DIR),
    "agent_id": "agent-devops",
    "last_sync": last_sync
}
(SHARED_MEM_DIR / "config.json").write_text(json.dumps(config, indent=2, ensure_ascii=False))

# ── Write a stale SHARED_MEMORY_CACHE.md (needs to be refreshed) ─────────────
stale_cache = textwrap.dedent("""\
    # 共享记忆摘要缓存
    _生成时间：2026-05-28T10:00:00_

    ## USER.md 摘要
    - 主人喜欢简洁 PR 描述

    ## KNOWLEDGE.md 摘要
    - Docker 多阶段构建缓存可加速 CI

    ## RULES.md 摘要
    - 禁止硬编码密钥

    ## TOOLS.md 摘要
    - docker system prune 清理资源
""")
(WORKSPACE_DIR / "SHARED_MEMORY_CACHE.md").write_text(stale_cache)

# ── Cleanup init work dir ────────────────────────────────────────────────────
import shutil
shutil.rmtree(INIT_WORK)

print("✅ Sandbox workspace generated successfully.")
print(f"   Bare remote : {BARE_REPO}")
print(f"   Working repo: {SHARED_MEM_DIR}")
print(f"   Config      : {SHARED_MEM_DIR}/config.json")
print(f"   Stale cache : {WORKSPACE_DIR}/SHARED_MEMORY_CACHE.md")