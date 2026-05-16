import os
import random

random.seed(42)

# Create directory structure
dirs = [
    "memory",
    "skills/causal-graph",
    ".issues",
    "docs",
    "src/components",
    "src/utils",
    "config",
    "logs/archive",
    "tests",
    "scripts",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ─── Distractor files ───────────────────────────────────────────────────────

# 1. Old README (no hints)
with open("docs/architecture.md", "w") as f:
    f.write("""# System Architecture

## Overview
Three-tier architecture with frontend, backend, and persistence layers.

## Components
- Frontend: Next.js dashboard
- Backend: Node.js API
- Persistence: PostgreSQL + Redis

## Deployment
All services are containerized via Docker.
""")

# 2. Generic config
with open("config/app.yaml", "w") as f:
    f.write("""version: "3.8"
services:
  api:
    image: node:18
    ports:
      - "3000:3000"
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: appdb
""")

# 3. Stale changelog
with open("docs/CHANGELOG.md", "w") as f:
    f.write("""# Changelog

## v4.9 (2026-01-10)
- Fixed memory leak in worker threads
- Updated dependencies

## v4.8 (2025-12-01)
- Initial release of ClawWork module
- Added basic scheduling
""")

# 4. Source file (distractor)
with open("src/components/Dashboard.jsx", "w") as f:
    f.write("""import React from 'react';

export function Dashboard() {
  return <div className="dashboard">Loading...</div>;
}
""")

# 5. Utility distractor
with open("src/utils/formatDate.js", "w") as f:
    f.write("""export function formatDate(ts) {
  return new Date(ts).toISOString().split('T')[0];
}
""")

# 6. Test file distractor
with open("tests/api.test.js", "w") as f:
    f.write("""describe('API', () => {
  it('should return 200', async () => {
    // placeholder
  });
});
""")

# 7. Scripts distractor
with open("scripts/deploy.sh", "w") as f:
    f.write("""#!/bin/bash
# Deploy script
echo "Deploying to production..."
npm run build && vercel --prod
""")

# 8. Archive log (distractor - old, should not dominate)
with open("logs/archive/2025-11-15.log", "w") as f:
    f.write("""2025-11-15 09:00 - System boot
2025-11-15 09:05 - Database connection established
2025-11-15 14:00 - Backup completed
""")

# 9. Package.json distractor
with open("config/package-lock-summary.json", "w") as f:
    f.write("""{
  "lockfileVersion": 3,
  "requires": true,
  "packages": {
    "node_modules/react": {"version": "18.2.0"},
    "node_modules/next": {"version": "14.1.0"}
  }
}
""")

# 10. Environment sample distractor
with open("config/.env.example", "w") as f:
    f.write("""DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
NEXT_PUBLIC_API_URL=http://localhost:3000
""")

# ─── Core input files: messy memory logs ────────────────────────────────────

# memory/2026-02-22.md
with open("memory/2026-02-22.md", "w") as f:
    f.write("""# 2026-02-22 工作日志

今天实施了**永续记忆增强**功能，主要集中在 AgentAwaken 项目上。
因为系统记忆健康度持续下降，所以我们决定实施三层记忆架构。

工作内容：
- 瓜农完成了核心记忆模块的重构
- 基于 GitHub 进行代码版本管理
- 该功能需要 PostgreSQL 作为持久层

这次增强使得记忆健康度从 60% 提升到了 85%，任务完成率也随之上升。
永续记忆增强 → 记忆健康度提升 → 任务完成率提升

P0 标记: 本任务为最高优先级，Jason Zuo 确认优先执行。
""")

# memory/2026-02-26.md
with open("memory/2026-02-26.md", "w") as f:
    f.write("""# 2026-02-26 工作日志

**NeuroBoost v5.0** 正式发布！

由于 ClawHub 出现了超时问题，检查版本后发现新版已经发布。
ClawHub 超时 → 检查版本 → 发现已发布

发布工作由龙虾负责，部署到 Vercel 平台上。
NeuroBoost 依赖 ClawWork 进行任务调度。

今天 AgentAwaken 也更新了，因为 NeuroBoost v5.0 提供了新的 API 接口，
使得 AgentAwaken 能够调用更强大的推理能力。

Jason Zuo 批准了发布计划。
""")

# memory/2026-03-01.md
with open("memory/2026-03-01.md", "w") as f:
    f.write("""# 2026-03-01 工作日志

创建了 **agentawaken** repo，基于 GitHub 托管。

部署事件: 将 AgentAwaken 部署到 Vercel，需要 pnpm 作为包管理工具。
部署完成后，仪表盘功能允许团队查看实时指标。

瓜农今日开会讨论了三层架构设计。
- AgentAwaken 需要 Vercel 进行部署
- AgentAwaken 需要 GitHub 进行版本控制  
- AgentAwaken 需要 pnpm 管理依赖

因为三层架构实施完毕，所以系统稳定性大幅提升。
龙虾 完成了 ClawWork 与 AgentAwaken 的集成测试，让两个系统可以协同工作。
""")

# MEMORY.md - long-term memory (messy)
with open("MEMORY.md", "w") as f:
    f.write("""# 长期记忆 / Long-term Memory

## 项目概览

### AgentAwaken
- 核心 AI Agent 平台
- 使用三层架构
- 依赖: GitHub, Vercel, Next.js, pnpm
- 负责人: 瓜农, Jason Zuo

### NeuroBoost  
- AI 推理增强模块
- v5.0 于 2026-02-26 发布
- 依赖 ClawWork 进行调度
- 负责人: 龙虾

### ClawWork
- 任务调度系统
- 与 ClawHub 集成
- 工具类: 部署和编排

## 重要事件时间线

[2026-02-22] 永续记忆增强 实施完成
[2026-02-26] NeuroBoost v5.0 发布
[2026-03-01] AgentAwaken repo 创建 + 部署到 Vercel

## 关键概念
- 永续记忆: 跨会话保持记忆的能力
- 三层架构: Frontend / Backend / Persistence 三层设计
- P0 标记: 最高优先级标签

## 关系摘要
永续记忆增强 导致 记忆健康度提升
记忆健康度提升 导致 任务完成率提升
NeuroBoost 使得 AgentAwaken 获得更强推理
ClawHub 超时 导致 版本检查
""")

# .issues/open-001.md
with open(".issues/open-001.md", "w") as f:
    f.write("""# [P0] ClawHub 集成稳定性

## 问题描述
ClawHub 工具与 ClawWork 之间的连接偶发超时。

## 影响
- NeuroBoost 调度延迟
- AgentAwaken 任务队列堆积

## 负责人
龙虾

## 状态
Open - 待 NeuroBoost v5.0 发布后验证修复情况

## 依赖
此问题需要 ClawWork v2.3+ 才能解决。
ClawWork 需要 ClawHub API v4 接口。
""")

# .issues/open-002.md  
with open(".issues/open-002.md", "w") as f:
    f.write("""# [P1] AgentAwaken 仪表盘性能优化

## 问题描述
Dashboard 加载时间超过 3 秒，影响用户体验。

## 根因分析
因为数据查询未做缓存，所以每次刷新都触发全量查询。
数据查询未缓存 → 全量查询 → 仪表盘加载慢

## 负责人
瓜农

## 所需工具
- Vercel Edge Functions
- Redis 缓存层

## 依赖
AgentAwaken 需要 Redis 实现缓存功能。
""")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk("."):
    # skip hidden dirs except .issues
    dirs_list[:] = [d for d in dirs_list if not d.startswith('.') or d == '.issues']
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")