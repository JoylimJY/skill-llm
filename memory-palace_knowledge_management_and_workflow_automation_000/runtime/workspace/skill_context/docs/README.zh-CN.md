# Memory Palace

> OpenClaw 智能体的认知增强层

## 简介

Memory Palace（记忆宫殿）是一个 OpenClaw Skill，为智能体提供持久化记忆管理能力，支持语义搜索、知识图谱和认知增强功能。

## 特性

- 📝 **持久化存储** - 记忆以 Markdown 文件形式存储
- 🔍 **语义检索** - 向量搜索优先，文本搜索兜底
- ⏰ **时间推理** - 解析时间表达式（明天、下周、本月等）
- 🧠 **概念扩展** - 扩展查询相关概念
- 🏷️ **标签系统** - 灵活的分类机制
- 📍 **位置管理** - 按位置组织记忆
- ⭐ **重要性评分** - 为重要记忆设置优先级
- 🗑️ **回收站机制** - 软删除，支持恢复
- 🔄 **后台任务** - 冲突检测、记忆压缩

### v1.2.0 新功能

- 🧠 **LLM 集成** - AI 驱动的摘要、经验提取、时间解析
- 📚 **经验积累** - 记录、验证和检索经验
- 💡 **记忆类型** - 将记忆分类为事实/经验/教训/偏好/决策

## 安装

### 方式一：通过 ClawHub 安装（推荐）

```bash
# 从 ClawHub 安装 Memory Palace skill
clawhub install memory-palace
```

### 方式二：从源码安装

```bash
git clone https://github.com/Lanzhou3/memory-palace.git
cd memory-palace
npm install
npm run build
```

### 启用向量检索（推荐）

要使用语义检索功能，需要安装向量检索依赖：

```bash
# 安装 Python 依赖
pip install sentence-transformers numpy

# 设置 HuggingFace 镜像（国内用户）
export HF_ENDPOINT=https://hf-mirror.com

# 启动向量服务
python scripts/vector-service.py &

# BGE-small-zh-v1.5 模型（~100MB）会在首次运行时自动下载
```

**向量检索要求：**
- Python 3.8+
- ~200MB 内存（用于模型）
- BGE-small-zh-v1.5 模型（自动下载）

**不启用向量检索**：Memory Palace 会使用文本搜索（关键词匹配），准确率较低但无需额外依赖。

## 快速开始

```typescript
import { MemoryPalaceManager } from '@openclaw/memory-palace';

const manager = new MemoryPalaceManager({
  workspaceDir: '/path/to/workspace'
});

// 存储记忆
const memory = await manager.store({
  content: '用户偏好深色模式',
  tags: ['preferences', 'ui'],
  importance: 0.8,
  location: 'user-settings'
});

// 检索记忆
const results = await manager.recall('用户偏好');

// 列出记忆
const memories = await manager.list({
  tags: ['preferences'],
  limit: 10
});

// 获取统计信息
const stats = await manager.stats();
```

## 存储结构

记忆存储在 `{workspaceDir}/memory/palace/` 目录下，以 Markdown 文件形式保存：

```
workspace/
└── memory/
    └── palace/
        ├── uuid-1.md
        ├── uuid-2.md
        └── .trash/
            └── deleted-uuid.md
```

### 文件格式

```markdown
---
id: "uuid"
tags: ["tag1", "tag2"]
importance: 0.8
status: "active"
createdAt: "2026-03-18T10:00:00Z"
updatedAt: "2026-03-18T10:00:00Z"
source: "conversation"
location: "projects"
---

记忆内容...

## Summary
可选摘要
```

## API 文档

### MemoryPalaceManager

#### 构造函数

```typescript
new MemoryPalaceManager(options: {
  workspaceDir: string;
  vectorSearch?: VectorSearchProvider;  // 可选
})
```

#### 方法

| 方法 | 说明 |
|------|------|
| `store(params)` | 存储新记忆 |
| `get(id)` | 根据ID获取记忆 |
| `update(params)` | 更新记忆 |
| `delete(id, permanent?)` | 删除记忆（默认软删除） |
| `recall(query, options?)` | 搜索记忆 |
| `list(options?)` | 带筛选条件的列表 |
| `stats()` | 获取统计信息 |
| `restore(id)` | 从回收站恢复 |
| `listTrash()` | 列出已删除记忆 |
| `emptyTrash()` | 清空回收站 |
| `storeBatch(items)` | 批量存储 |
| `getBatch(ids)` | 批量获取 |

### 经验管理（v1.2.0）

| 方法 | 说明 |
|------|------|
| `recordExperience(params)` | 记录可复用的经验 |
| `getExperiences(options?)` | 按条件查询经验 |
| `verifyExperience(id, effective)` | 标记经验是否有效 |
| `getRelevantExperiences(context)` | 获取与当前上下文相关的经验 |

### LLM 增强方法（v1.1.0）

| 方法 | 说明 |
|------|------|
| `summarize(id)` | AI 驱动的记忆摘要 |
| `extractExperience(memoryIds)` | 从记忆中提取经验教训 |
| `parseTimeLLM(expression)` | 复杂时间表达式解析 |
| `expandConceptsLLM(query)` | 动态概念扩展 |
| `compress(memoryIds)` | 智能记忆压缩 |

### 认知模块

```typescript
import {
  TopicCluster,
  EntityTracker,
  KnowledgeGraphBuilder
} from '@openclaw/memory-palace';

// 主题聚类
const cluster = new TopicCluster();
const clusters = await cluster.cluster(memories);

// 实体追踪
const tracker = new EntityTracker();
const { entities, coOccurrences } = await tracker.track(memories);

// 知识图谱
const graphBuilder = new KnowledgeGraphBuilder();
const graph = await graphBuilder.build(memories);
```

### 后台任务

```typescript
import {
  ConflictDetector,
  MemoryCompressor
} from '@openclaw/memory-palace';

// 冲突检测
const detector = new ConflictDetector();
const conflicts = await detector.detect(memories);

// 记忆压缩
const compressor = new MemoryCompressor();
const results = await compressor.compress(memories);
```

## 与 OpenClaw 集成

Memory Palace 设计为封装 OpenClaw 的 `MemoryIndexManager`，提供向量搜索能力。

### 启用向量搜索

```typescript
import { MemoryPalaceManager } from '@openclaw/memory-palace';
import { MemoryIndexManager } from '@openclaw/memory';

const vectorSearch = new MemoryIndexManager({
  // OpenClaw 配置
});

const manager = new MemoryPalaceManager({
  workspaceDir: '/workspace',
  vectorSearch: {
    search: (query, topK, filter) => vectorSearch.search(query, topK, filter),
    index: (id, content, metadata) => vectorSearch.index(id, content, metadata),
    remove: (id) => vectorSearch.remove(id)
  }
});
```

### 无向量搜索模式

即使不配置向量搜索，Memory Palace 也能正常工作，会自动降级为文本匹配。

## 测试

```bash
npm test
```

## 架构原则

1. **无 MCP 协议** - 直接函数调用，无外部协议
2. **接口隔离** - 向量搜索为可选接口
3. **文件存储** - 简单、可移植、人类可读
4. **优雅降级** - 无高级功能时仍可工作

## 许可证

MIT

---

🔥 由混沌团队构建