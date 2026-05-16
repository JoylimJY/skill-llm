#!/usr/bin/env python3
"""
Generate the sandbox workspace for the memory-archiver skill evaluation task.
This creates:
1. The ~/.openclaw/workspace/ directory structure (skills, existing partial memories)
2. A raw_session_notes.txt with messy, unstructured sprint notes the agent must process
3. Distractor files to simulate a real project environment
"""

import os
import random
from pathlib import Path
from datetime import date, timedelta

random.seed(42)

HOME = Path(os.environ.get("HOME", "/root"))
WORKSPACE = HOME / ".openclaw" / "workspace"

# ── Core memory-archiver directories ──────────────────────────────────────────
skill_dir = WORKSPACE / "skills" / "memory-archiver"
scripts_dir = skill_dir / "scripts"
hooks_dir = skill_dir / "hooks"
memory_daily = WORKSPACE / "memory" / "daily"
memory_weekly = WORKSPACE / "memory" / "weekly"
hooks_installed = WORKSPACE / "hooks" / "auto-memory-search"

for d in [scripts_dir, hooks_dir, memory_daily, memory_weekly, hooks_installed]:
    d.mkdir(parents=True, exist_ok=True)

# ── Dates ──────────────────────────────────────────────────────────────────────
today = date(2026, 3, 23)
yesterday = today - timedelta(days=1)
two_days_ago = today - timedelta(days=2)
three_days_ago = today - timedelta(days=3)
today_str = today.isoformat()
yesterday_str = yesterday.isoformat()
two_days_ago_str = two_days_ago.isoformat()

# ── Existing daily memory files (partial, to test dedup) ──────────────────────
existing_daily_yesterday = memory_daily / f"{yesterday_str}.md"
existing_daily_yesterday.write_text(
    f"""# Daily Memory - {yesterday_str}

[semantic] 项目使用 Next.js 14 + TypeScript 作为前端框架
[episodic] 用户完成了登录页面的响应式布局重构
[procedural] 代码审查流程：1. 提交 PR 2. 两人审查 3. CI 通过后合并
""",
    encoding="utf-8",
)

existing_daily_two_days = memory_daily / f"{two_days_ago_str}.md"
existing_daily_two_days.write_text(
    f"""# Daily Memory - {two_days_ago_str}

[semantic] 团队使用 Tailwind CSS v3 进行样式管理
[episodic] 发现了一个 hydration 错误，原因是 SSR 与客户端状态不同步
[procedural] 修复 hydration 错误步骤：1. 检查 useEffect 依赖 2. 确保 initialState 一致 3. 添加 suppressHydrationWarning 作临时方案
""",
    encoding="utf-8",
)

existing_daily_three_days = memory_daily / f"{three_days_ago.isoformat()}.md"
existing_daily_three_days.write_text(
    f"""# Daily Memory - {three_days_ago.isoformat()}

[semantic] API 使用 tRPC + Zod 进行类型安全的端到端通信
[episodic] 完成了用户认证模块的单元测试覆盖（覆盖率提升到 87%）
""",
    encoding="utf-8",
)

# ── Existing MEMORY.md (long-term, sparse) ────────────────────────────────────
memory_md = WORKSPACE / "MEMORY.md"
memory_md.write_text(
    """# Long-Term Memory - Permanent Knowledge Base

_Last updated: 2026-03-20_

## 技术栈偏好

[semantic] 用户倾向于使用函数式编程风格，避免 class 组件
[semantic] 数据库选型：PostgreSQL (主) + Redis (缓存层)

## 工作习惯

[procedural] 每次开发新功能前必须先写接口文档再写代码
[episodic] 2026-03-15: 项目从 Webpack 迁移到 Turbopack，构建速度提升 60%
""",
    encoding="utf-8",
)

# ── skill.json ─────────────────────────────────────────────────────────────────
(skill_dir / "skill.json").write_text(
    """{
  "name": "memory-archiver",
  "version": "7.0.0",
  "description": "三层时间架构记忆管理",
  "postinstall": "scripts/install.sh"
}
""",
    encoding="utf-8",
)

# ── Stub scripts (exist but agent should not depend on running them) ───────────
stub_scripts = [
    "install.sh",
    "auto-memory-search.sh",
    "memory-loader.sh",
    "memory-search.sh",
    "memory-refresh.sh",
    "memory-dedup.sh",
]
for s in stub_scripts:
    script_path = scripts_dir / s
    script_path.write_text(
        f"""#!/bin/bash
# {s} - memory-archiver script
echo "Script {s} called with args: $@"
""",
        encoding="utf-8",
    )
    script_path.chmod(0o755)

# ── Hook files ─────────────────────────────────────────────────────────────────
(hooks_dir / "HOOK.md").write_text(
    """# Auto Memory Search Hook
event: message:received
description: Intercepts incoming messages, extracts keywords, searches memory, injects context.
""",
    encoding="utf-8",
)
(hooks_dir / "handler.js").write_text(
    """// handler.js - Hook handler for auto-memory-search
module.exports = async function handler(event, context) {
  // Auto-search memory based on message type
};
""",
    encoding="utf-8",
)

# ── THE MAIN TASK INPUT: raw sprint session notes ─────────────────────────────
# This is the messy, unprocessed data the agent must classify and archive
raw_notes_path = Path("/workspace") / "raw_session_notes.txt"
raw_notes_path.write_text(
    """=== SPRINT SESSION NOTES - Week of 2026-03-23 ===
Recorded by: Dev Assistant Bot
Date: 2026-03-23

--- Conversation Log Excerpt ---

09:15 - 用户说他今天早上喝了咖啡才开始工作 [SKIP - trivial]

09:22 - 决定：将 authentication 模块从 NextAuth.js v4 迁移到 v5 (Auth.js)。
原因：v5 提供更好的 Edge Runtime 支持，与 Next.js 14 App Router 完全兼容。
这是一个重要的架构决策。

09:45 - 用户提问："如何配置 Auth.js 的 JWT 回调？"
解决方案记录：在 auth.config.ts 中配置 callbacks.jwt，
注意：session 对象需手动扩展类型定义 (augment next-auth types)。
具体步骤：
  1. 安装 next-auth@beta
  2. 创建 auth.config.ts，配置 providers + callbacks
  3. 在 middleware.ts 中导入并使用 auth
  4. 扩展 Session/User 类型 (types/next-auth.d.ts)

10:30 - 发现问题：Redis 缓存键命名混乱，user:session:${"{userId}"} 和 session:user:${"{userId}"} 两种格式混用导致缓存未命中率升高。
修复决策：统一使用 user:session:${"{userId}"} 格式，并编写迁移脚本清理旧键。

11:00 - 用户今天心情不错，说周末要去爬山 [SKIP - private/trivial]

11:15 - 临时想法：也许可以试试 Bun 作为运行时替代 Node.js？[SKIP - volatile idea]

11:30 - 确认了新的 API 错误处理规范：
  所有 tRPC procedure 必须使用 TRPCError 抛出错误，不能直接 throw new Error()
  错误码规范：NOT_FOUND(404), UNAUTHORIZED(401), BAD_REQUEST(400), INTERNAL_SERVER_ERROR(500)

12:00 - 完成了 Redis 缓存键统一迁移。共处理 3 个服务文件，修复 12 处命名不一致。
这是今天的一个重要完成事项。

14:00 - 数据库连接池配置最佳实践（从今天的调优中总结）：
  - max connections: 20 (生产环境)
  - min connections: 5  
  - idle timeout: 30000ms
  - connection timeout: 5000ms
  对应代码：在 db/index.ts 中配置 pool 参数

15:00 - 用户已经记录过：项目使用 Next.js 14 + TypeScript [DUPLICATE - already in yesterday memory]

15:30 - 团队规范更新：所有新功能分支命名改为 feat/JIRA-ID-short-description 格式
例如：feat/AUTH-123-jwt-refresh-token

16:00 - 今天又开了一个会讨论是否要加功能，没有结论 [SKIP - no value]

16:30 - 周报时间！本周技术亮点：成功将 CI/CD 流水线从 GitHub Actions 迁移到 内部 Jenkins，
构建时间从平均 8 分钟降低到 3 分钟。这是本周最重要的基础设施改进，值得长期记录。

=== END OF SESSION NOTES ===
""",
    encoding="utf-8",
)

# ── Distractor project files (simulate real dev environment) ──────────────────
project_dir = Path("/workspace") / "project"
(project_dir / "src" / "components").mkdir(parents=True, exist_ok=True)
(project_dir / "src" / "pages").mkdir(parents=True, exist_ok=True)
(project_dir / "src" / "utils").mkdir(parents=True, exist_ok=True)
(project_dir / "tests").mkdir(parents=True, exist_ok=True)
(project_dir / "docs").mkdir(parents=True, exist_ok=True)
(project_dir / ".github" / "workflows").mkdir(parents=True, exist_ok=True)

(project_dir / "package.json").write_text(
    '{"name": "my-app", "version": "1.0.0", "dependencies": {"next": "14.1.0"}}',
    encoding="utf-8",
)
(project_dir / "tsconfig.json").write_text(
    '{"compilerOptions": {"strict": true, "target": "ES2022"}}', encoding="utf-8"
)
(project_dir / "src" / "components" / "LoginForm.tsx").write_text(
    "// LoginForm component\nexport default function LoginForm() { return <form/>; }",
    encoding="utf-8",
)
(project_dir / "src" / "pages" / "index.tsx").write_text(
    "// Home page\nexport default function Home() { return <div>Home</div>; }",
    encoding="utf-8",
)
(project_dir / "src" / "utils" / "redis.ts").write_text(
    "// Redis utility\nexport const cacheKey = (userId: string) => `user:session:${userId}`;",
    encoding="utf-8",
)
(project_dir / "tests" / "auth.test.ts").write_text(
    "// Auth tests\ndescribe('auth', () => { it('should work', () => {}); });",
    encoding="utf-8",
)
(project_dir / "docs" / "architecture.md").write_text(
    "# Architecture\nNext.js 14 + tRPC + PostgreSQL + Redis",
    encoding="utf-8",
)
(project_dir / ".github" / "workflows" / "ci.yml").write_text(
    "name: CI\non: push\njobs:\n  test:\n    runs-on: ubuntu-latest",
    encoding="utf-8",
)
(project_dir / "README.md").write_text(
    "# My App\nA Next.js application.", encoding="utf-8"
)
(project_dir / ".env.example").write_text(
    "DATABASE_URL=postgresql://...\nREDIS_URL=redis://...", encoding="utf-8"
)
(project_dir / "src" / "utils" / "db.ts").write_text(
    "// DB config\nimport { Pool } from 'pg';\nexport const pool = new Pool({ max: 20 });",
    encoding="utf-8",
)

# ── Session state cache file (distractor) ─────────────────────────────────────
session_state = WORKSPACE / "SESSION-STATE.md"
session_state.write_text(
    """# Session State Cache
_Auto-generated by memory-loader.sh_

Last loaded: 2026-03-22T23:55:00

## Cached Entries
[semantic] 项目使用 Next.js 14 + TypeScript
[semantic] 团队使用 Tailwind CSS v3
""",
    encoding="utf-8",
)

print("✅ Workspace generated successfully.")
print(f"   WORKSPACE: {WORKSPACE}")
print(f"   Task input: {raw_notes_path}")
print(f"   Today's date for task: {today_str}")