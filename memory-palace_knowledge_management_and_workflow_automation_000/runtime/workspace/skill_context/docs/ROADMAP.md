# Memory Palace 项目规划

**项目名称**: Memory Palace - 智能体记忆宫殿  
**当前版本**: v1.0.0  
**仓库地址**: https://github.com/Lanzhou3/memory-palace  
**更新日期**: 2026-03-18

---

## 项目概述

Memory Palace 是为 OpenClaw Agent 提供的认知增强层，实现持久化记忆管理、语义搜索、知识图谱等高级功能。

### 核心价值

- 🧠 **持久记忆** - 让 AI Agent 拥有跨会话的记忆能力
- 🔍 **智能检索** - 向量搜索 + 文本搜索双重保障
- ⏰ **时间推理** - 理解"下周三"、"三个月后"等时间表达
- 🏷️ **知识组织** - 标签、位置、重要性多维度管理
- 🔄 **自动维护** - 冲突检测、智能压缩后台任务

---

## 版本规划

### v1.0.0 (已完成 ✅)

**发布日期**: 2026-03-18

**核心功能**:
- ✅ MemoryPalaceManager 核心（CRUD + 检索）
- ✅ 文件存储（Markdown + YAML frontmatter）
- ✅ 向量检索集成（BGE-small-zh-v1.5）
- ✅ 时间推理引擎（规则引擎）
- ✅ 概念扩展器（预定义映射 + 向量相似度）
- ✅ 认知模块（聚类、实体、图谱）
- ✅ 后台任务（冲突检测、压缩）
- ✅ SKILL.md 工具定义（12 个工具）
- ✅ 31 个测试全部通过
- ✅ A/B 测试验证（100% 命中率）
- ✅ 开源到 GitHub（MIT 协议）

**安装方式**:
```bash
# ClawHub 安装（推荐）
clawhub install memory-palace

# 源码安装
git clone https://github.com/Lanzhou3/memory-palace
cd memory-palace && npm install && npm run build
```

**依赖要求**:
- Node.js 18+
- Python 3.8+（向量搜索可选）
- ~200MB RAM（向量模型）

---

### v1.1.0 (规划中 📋)

**目标**: LLM 智能增强

**核心改进**:
将所有需要 LLM 能力的功能统一使用 **OpenClaw Subagent** 方式实现。

**新增功能**:

| 功能 | 说明 | 超时 |
|------|------|------|
| 智能总结记忆 | LLM 提取关键信息、评估重要性 | 30s |
| 经验提取器 | 从对话中提取可复用经验 | 60s |
| 时间推理增强 | LLM 解析复杂时间表达 | 10s |
| 概念扩展增强 | LLM 动态发现相关概念 | 10s |
| 智能压缩 | LLM 提炼旧记忆精华 | 60s |

**技术方案**: `/data/agent-memory-palace/docs/v1.1-llm-integration.md`

**技术验证** (2026-03-18):

| 功能 | 实测耗时 | 目标 | 状态 |
|------|----------|------|------|
| 时间解析 | 7s | 10s | ✅ 达标 |
| 概念扩展 | 12s | 15s | ✅ 达标 |

**结论**: Subagent 方案技术可行，已验证通过。

**实现计划**:

| 阶段 | 内容 | 时间 |
|------|------|------|
| Phase 1 | Subagent 调用框架 + 降级机制 | 3 天 |
| Phase 2 | 5 个核心功能实现 | 3 天 |
| Phase 3 | 用户体验 + 工具暴露 | 2 天 |
| Phase 4 | 测试 + 文档 + 性能优化 | 2 天 |

**总计**: 10 天（含 buffer）

**预计发布**: 2026-03-28

---

### v1.2.0 (远期规划 🔮)

**目标**: 企业级增强

**计划功能**:
- 多工作空间支持
- 记忆导入导出
- 记忆同步（云端备份）
- 权限控制
- 审计日志
- 性能监控面板

---

## 技术架构

### 当前架构 (v1.0)

```
OpenClaw Agent
      │
      ▼ 调用 SKILL.md 工具
┌─────────────────┐
│ MemoryPalace    │
│ Manager         │
└─────────────────┘
      │
      ├─▶ FileStorage (Markdown)
      │
      └─▶ VectorSearch (BGE-small-zh-v1.5)
```

### 目标架构 (v1.1)

```
OpenClaw Agent
      │
      ▼ 调用 SKILL.md 工具
┌─────────────────┐
│ MemoryPalace    │
│ Manager         │
└─────────────────┘
      │
      ├─▶ FileStorage (Markdown)
      │
      ├─▶ VectorSearch (BGE-small-zh-v1.5)
      │
      └─▶ LLMService (Subagent)
            │
            ├─▶ summarizeMemory (30s)
            ├─▶ extractExperiences (60s)
            ├─▶ parseTime (10s)
            ├─▶ expandConcepts (10s)
            └─▶ compressMemories (60s)
```

---

## 发布渠道

### ClawHub (主要)

```bash
# 安装
clawhub install memory-palace

# 更新
clawhub update memory-palace
```

### GitHub (备选)

```bash
git clone https://github.com/Lanzhou3/memory-palace
```

---

## 文档结构

```
/data/agent-memory-palace/
├── README.md                    # 项目介绍
├── SKILL.md                     # OpenClaw Skill 定义
├── CHANGELOG.md                 # 变更日志
├── docs/
│   ├── README.zh-CN.md          # 中文文档
│   ├── installation.md          # 安装指南
│   ├── openclaw-integration.md  # OpenClaw 集成
│   ├── v1.1-llm-integration.md  # v1.1 技术方案
│   └── ROADMAP.md               # 本文档
├── examples/
│   ├── user-preferences.md      # 示例记忆
│   └── project-memory.md
└── src/
    ├── manager.ts               # 核心管理器
    ├── storage.ts               # 存储层
    ├── background/              # 后台任务
    ├── cognitive/               # 认知模块
    └── llm/                     # v1.1 新增
```

---

## 质量保障

### 测试覆盖

- ✅ 单元测试：31 个测试用例
- ✅ 集成测试：OpenClaw 集成验证
- ✅ A/B 测试：真实数据验证命中率 100%

### 性能基准

| 操作 | 性能 |
|------|------|
| 写入单条记忆 | < 10ms |
| 文本搜索 | < 50ms (1000 条) |
| 向量搜索 | < 100ms (1000 条) |
| 列表查询 | < 20ms |

---

## 团队分工

| 成员 | 职责 |
|------|------|
| 朱雀 🔥 | 研发实现 |
| 炎晖 📋 | 产品验收 |
| 煊璃 🧪 | 测试验收 |
| 祝融 🔥 | 统筹协调 |

---

## 风险与对策

| 风险 | 对策 |
|------|------|
| 向量模型占用内存 | 提供禁用选项，降级到文本搜索 |
| LLM 调用延迟 | 10s 快速任务优化，异步处理 |
| Subagent 并发限制 | 控制并发数，排队处理 |
| 记忆数据丢失 | 软删除 + 回收站机制 |
| 数据隐私 | 本地存储，不上传云端 |

---

## 成功指标

### v1.0 指标

- ✅ 31 个测试全部通过
- ✅ A/B 测试命中率 100%
- ✅ GitHub 开源
- ⏳ ClawHub 发布（待完成）

### v1.1 指标

- [ ] 5 个 LLM 功能全部实现
- [ ] 测试覆盖率 > 90%
- [ ] 10s 任务平均响应 < 8s
- [ ] 用户满意度 > 4.5/5

---

## 里程碑

| 版本 | 日期 | 状态 |
|------|------|------|
| v1.0.0 | 2026-03-18 | ✅ 完成 |
| v1.1.0 | 2026-03-22 | 📋 规划中 |
| ClawHub 发布 | TBD | ⏳ 待发布 |

---

🔥 混沌团队 - Memory Palace 项目组