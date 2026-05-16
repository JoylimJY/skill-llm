---
name: memory-archiver
description: 记忆管理技能 - 三层时间架构 + 三类记忆标签 + 自动搜索 Hook
version: 6.0.0
author: 前端 ⚡
---

# Memory Archiver Skill - 记忆归档技能

**版本**: 7.0 (Hook 安装自动化)  
**创建日期**: 2026-03-11  
**更新日期**: 2026-03-23  
**作者**: 前端 ⚡

---

## 📋 技能描述

**二维记忆架构**：时间分层 × 类型标签

- **时间分层**: daily (每天) → weekly (每周) → long-term (长期/MEMORY.md)
- **类型标签**: [episodic] 事件 / [semantic] 知识 / [procedural] 流程
- **存储**: 每日记忆 + 每周记忆 + 长期精选记忆
- **WAL 协议**: Write-Ahead Log，写前日志防数据丢失
- **自动搜索 Hook**: 检测用户消息类型，自动搜索记忆并注入上下文

---

## 🎯 功能清单

### 时间分层任务

| 任务 | 频率 | 说明 |
|------|------|------|
| **记忆及时写入** | 10 分钟 | 检查并写入重要信息到 daily 文件 |
| **记忆归档 - Daily 层** | 每天 23:00 | 提炼当天内容到 daily 文件 |
| **记忆总结 - Weekly 层** | 每周日 22:00 | 提炼 weekly 到 MEMORY.md 长期记忆 |

### 自动搜索 Hook（多维度增强）

| 功能 | 说明 |
|------|------|
| **消息类型检测** | 疑问/修复/规范/特征/配置/命令/技术 |
| **关键词提取** | 自动提取中英文关键词 |
| **维度 1: 关键词搜索** | 在 SESSION-STATE.md 缓存中搜索 |
| **维度 2: 类型标签搜索** | 按 [episodic]/[semantic]/[procedural] 标签搜索 |
| **维度 3: 时间维度搜索** | 今日→昨日→长期记忆，优先最近 |
| **维度 4: 组合搜索** | 多关键词 OR 关系，扩大匹配范围 |
| **上下文注入** | 合并所有维度结果注入 prompt |

---

## 📂 文件结构

```
skills/memory-archiver/
├── SKILL.md                          # 本文件
├── skill.json                        # 技能元数据
├── _meta.json                        # ClawHub 元数据
├── scripts/
│   ├── install.sh                    # 安装脚本（含 hook 自动注册）
│   ├── auto-memory-search.sh         # 自动记忆搜索（被 hook 调用）
│   ├── memory-loader.sh              # 加载记忆到缓存
│   ├── memory-search.sh              # 搜索记忆
│   ├── memory-refresh.sh             # 智能刷新缓存
│   ├── memory-dedup.sh               # 自动去重
│   └── README.md                     # 脚本说明文档
├── hooks/                            # Hook 源文件（安装时复制到 workspace/hooks/）
│   ├── handler.js                    # Hook 处理器（事件：message:received）
│   └── HOOK.md                       # Hook 元数据
└── .clawhub/                         # ClawHub 同步目录
```

### 安装后的工作区文件

```
~/.openclaw/workspace/
├── MEMORY.md                         # 长期精选记忆
├── hooks/
│   └── auto-memory-search/           # Hook（由 install.sh 自动部署）
│       ├── handler.js
│       └── HOOK.md
└── memory/
    ├── daily/                        # 每日记忆
    └── weekly/                       # 每周记忆
```

---

## 🔧 安装

### 方法 1: 通过 ClawHub 安装（推荐 ⭐）

```bash
clawhub install memory-archiver
```

安装后**自动执行**：
1. 创建 `memory/daily/` 和 `memory/weekly/` 目录
2. 部署 hook 到 `workspace/hooks/auto-memory-search/`
3. 执行 `openclaw hooks install --link` 注册 hook
4. 自动添加 3 个 cron 任务
5. 提示重启 gateway

### 方法 2: 本地技能目录（开发调试）

如果技能已在 `~/.openclaw/workspace/skills/memory-archiver/`：

```bash
bash ~/.openclaw/workspace/skills/memory-archiver/scripts/install.sh
```

### 验证安装

```bash
# 检查 hook 是否注册
openclaw hooks list
# 应看到 🔍 auto-memory-search (✓ ready)

# 检查 cron 任务
openclaw cron list
# 应看到 3 个记忆相关任务
```

---

## 📝 记忆写入规范

### 三类记忆标签

| 标签 | 说明 | 例子 |
|------|------|------|
| `[episodic]` | 事件/经历 | "用户今天完成了模板重设计" |
| `[semantic]` | 知识/事实 | "用户喜欢 Tailwind CSS" |
| `[procedural]` | 流程/方法 | "部署步骤：1. 构建 2. 上传 3. 重启" |

### 记录原则

**✅ 应该记录**:
- 关键决策和教训
- 新发现的有价值内容
- 技术栈使用经验
- 工作习惯调整
- 用户偏好

**❌ 不应该记录**:
- ❌ **重复的上下文** — 已有记录的内容不再重复
- ❌ **毫无意义的日常** — 无事发生就不记
- ❌ **重复的任务进度提示** — 避免刷屏
- ❌ **私密细节** — 保护隐私
- ❌ **短期易变想法** — 临时念头不持久

**核心判断**: 这条信息在未来回顾时是否有价值？

---

## 🔍 记忆搜索

### 方法 1: 使用记忆加载脚本（推荐 ⭐）

**步骤 1: 加载记忆到内存**
```bash
bash ~/.openclaw/workspace/skills/memory-archiver/scripts/memory-loader.sh
```
加载内容：今日 + 昨日 + 最近 3 天 daily + MEMORY.md + 最近 weekly

**步骤 2: 搜索记忆**
```bash
bash ~/.openclaw/workspace/skills/memory-archiver/scripts/memory-search.sh "关键词"
```

**在对话中使用**：
- 说 `加载记忆` → 运行 memory-loader.sh
- 说 `搜索记忆：关键词` → 运行 memory-search.sh

### 方法 2: 使用 grep 手动搜索

```bash
# 搜索所有记忆文件
grep -ri "CSS" ~/.openclaw/workspace/memory/

# 带上下文显示
grep -riC 3 "CSS" ~/.openclaw/workspace/memory/daily/*.md
```

---

## 📊 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| **7.0** | 2026-03-23 | **Hook 安装自动化**: `skill.json` 添加 `postinstall` 脚本，`clawhub install` 自动部署 hook + cron |
| 6.0 | 2026-03-20 | 整合 Auto Memory Search Hook: 将独立 Hook 合并到技能内 |
| 5.0 | 2026-03-20 | **三层精简架构**: 移除 monthly/yearly 层，保留 daily/weekly/long-term |
| 4.0 | 2026-03-20 | **精简版**: 移除向量搜索依赖，简化架构 |
| 3.0 | 2026-03-19 | 向量增强版：整合 Qdrant + Transformers.js |
| 2.0 | 2026-03-19 | 五层时间架构 (hourly/daily/weekly/monthly/yearly) |
| 1.0 | 2026-03-11 | 初始版本 |

---

## 🛠️ 维护命令

```bash
# 检查记忆文件总量
du -sh ~/.openclaw/workspace/memory/

# 查看每日记忆文件
ls -lh ~/.openclaw/workspace/memory/daily/

# 搜索记忆内容
grep -ri "关键词" ~/.openclaw/workspace/memory/
```

---

*文档最后更新：2026-03-20*
