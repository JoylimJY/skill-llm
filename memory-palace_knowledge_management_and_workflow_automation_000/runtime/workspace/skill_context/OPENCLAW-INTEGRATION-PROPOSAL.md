# Memory Palace 与 OpenClaw 集成技术方案

**版本**: 3.0 (最终版)  
**日期**: 2026-03-18  
**作者**: 祝融 🔥  
**状态**: ✅ 已实现

---

## 一、项目定位

**Memory Palace 是 OpenClaw Memory 的认知增强层，不是独立记忆系统。**

### 1.1 核心价值

| 功能 | OpenClaw Memory | Memory Palace |
|------|-----------------|---------------|
| 结构化记忆对象 | ❌ 无 | ✅ Memory 类（id, content, importance, tags） |
| 回收站机制 | ❌ 无 | ✅ 软删除 + 恢复 |
| 主题聚类 | ❌ 无 | ✅ 向量聚类 + 主题摘要 |
| 实体追踪 | ❌ 无 | ✅ 人物、项目、概念追踪 |
| 知识图谱 | ❌ 无 | ✅ 实体关系抽取 + 图存储 |
| 冲突检测 | ❌ 无 | ✅ 语义矛盾识别 |
| 记忆压缩 | ❌ 无 | ✅ LLM 摘要生成 |

### 1.2 不重复造轮子

Memory Palace **不实现**以下功能（直接用 OpenClaw）：
- ❌ 向量索引 → 用 OpenClaw MemoryIndexManager
- ❌ Embedding 生成 → 用 OpenClaw Embeddings
- ❌ 全文检索 → 用 OpenClaw Hybrid Search
- ❌ 后台任务调度 → 用 OpenClaw sessions_spawn

---

## 二、架构设计

### 2.1 分层架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    认知层 (Memory Palace)                        │
│                    ← 本项目实现                                   │
│  主题聚类 │ 实体追踪 │ 知识图谱 │ 冲突检测 │ 记忆压缩 │ 回收站    │
└─────────────────────────────────────────────────────────────────┘
                              │ 调用
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    检索层 (OpenClaw Memory)                      │
│                    ← OpenClaw 已有                                │
│  向量检索 │ 全文检索 │ 混合检索 │ 时间衰减 │ MMR                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    存储层 (OpenClaw Memory)                      │
│                    ← OpenClaw 已有                                │
│  SQLite │ sqlite-vec │ Embedding 缓存                           │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 调用流程

```
OpenClaw Agent
      │
      ▼ 调用 Skill 工具
┌─────────────────┐
│   SKILL.md      │  ← 定义 10 个工具
│   Tools 部分     │
└─────────────────┘
      │
      ▼ 直接调用（无 MCP 协议）
┌─────────────────┐
│ MemoryPalace    │  ← TypeScript 库
│ Manager         │
└─────────────────┘
      │
      ├──────────────────┐
      ▼                  ▼
┌─────────────┐   ┌─────────────┐
│ FileStorage │   │ VectorSearch│
│ (Markdown)  │   │ Provider    │
└─────────────┘   │ (可选)       │
                  └─────────────┘
```

---

## 三、存储设计

### 3.1 文件格式

Memory 对象存储为 Markdown 文件：

```markdown
---
id: "abc-123"
tags: ["project", "important"]
importance: 0.8
status: "active"
createdAt: "2026-03-18T10:00:00Z"
updatedAt: "2026-03-18T10:00:00Z"
source: "conversation"
location: "projects"
---

用户正在开发 Memory Palace 项目...

## Summary
（可选）LLM 生成的摘要
```

### 3.2 目录结构

```
workspace/
├── MEMORY.md                    # OpenClaw 原生长期记忆
├── memory/
│   ├── 2026-03-18.md           # OpenClaw 原生日志
│   └── palace/                  # Memory Palace 存储
│       ├── {uuid}.md           # 活跃记忆
│       ├── projects/           # 按位置分类（可选）
│       │   └── {uuid}.md
│       └── .trash/              # 回收站
│           └── {uuid}.md
```

---

## 四、API 设计

### 4.1 MemoryPalaceManager

```typescript
class MemoryPalaceManager {
  constructor(options: {
    workspaceDir: string;
    vectorSearch?: VectorSearchProvider;  // 可选
  });
  
  // === 核心操作 ===
  store(params: StoreParams): Promise<Memory>;
  get(id: string): Promise<Memory | null>;
  update(params: UpdateParams): Promise<Memory | null>;
  delete(id: string, permanent?: boolean): Promise<void>;
  
  // === 检索 ===
  recall(query: string, options?: RecallOptions): Promise<SearchResult[]>;
  list(options?: ListOptions): Promise<Memory[]>;
  
  // === 统计 ===
  stats(): Promise<Stats>;
  
  // === 回收站 ===
  restore(id: string): Promise<Memory | null>;
  listTrash(): Promise<Memory[]>;
  emptyTrash(): Promise<void>;
}
```

### 4.2 VectorSearchProvider 接口

```typescript
interface VectorSearchProvider {
  search(query: string, topK: number, filter?: object): Promise<SearchResult[]>;
  index(id: string, content: string, metadata?: object): Promise<void>;
  remove(id: string): Promise<void>;
}
```

### 4.3 降级策略

- 有 `vectorSearch` → 使用向量检索
- 无 `vectorSearch` → 降级到文本匹配（关键词 + 重要性加权）

---

## 五、SKILL.md 工具列表

| 工具 | 功能 | 参数 |
|------|------|------|
| `memory_palace_write` | 写入记忆 | content, location?, tags?, importance? |
| `memory_palace_search` | 语义检索 | query, location?, tags?, top_k? |
| `memory_palace_get` | 获取单条 | id |
| `memory_palace_update` | 更新记忆 | id, content?, tags?, importance? |
| `memory_palace_delete` | 删除记忆 | id, permanent? |
| `memory_palace_list` | 列出记忆 | location?, tags?, status?, limit? |
| `memory_palace_stats` | 统计信息 | - |
| `memory_palace_restore` | 恢复记忆 | id |
| `memory_palace_trash_list` | 列出回收站 | - |
| `memory_palace_trash_empty` | 清空回收站 | - |

---

## 六、与 OpenClaw 集成

### 6.1 作为 Skill 使用

```typescript
import { MemoryPalaceManager } from "@openclaw/memory-palace";

// 创建 Manager
const palace = new MemoryPalaceManager({
  workspaceDir: "/path/to/workspace",
  // 可选：注入向量检索
  vectorSearch: openClawContext.memoryManager,
});

// 使用
await palace.store({
  content: "用户喜欢绿茶",
  tags: ["preference"],
  importance: 0.7,
});

const results = await palace.recall("用户喜欢什么");
```

### 6.2 包装 OpenClaw MemoryIndexManager

```typescript
import { MemoryIndexManager } from "openclaw/memory/manager.js";
import { MemoryPalaceManager } from "@openclaw/memory-palace";

// 获取 OpenClaw Memory Manager
const memoryManager = await MemoryIndexManager.get({
  cfg: openClawConfig,
  agentId: "my-agent",
});

// 包装为 VectorSearchProvider
const vectorSearchProvider = {
  async search(query, topK, filter) {
    return memoryManager.search(query, { maxResults: topK });
  },
  async index(id, content, metadata) {
    // OpenClaw 自动索引 memory/ 目录下的文件
  },
  async remove(id) {
    // 删除文件即可
  },
};

// 创建 Memory Palace
const palace = new MemoryPalaceManager({
  workspaceDir,
  vectorSearch: vectorSearchProvider,
});
```

---

## 七、认知增强模块

### 7.1 主题聚类 (TopicCluster)

```typescript
const cluster = new TopicCluster(palace);
const clusters = await cluster.clusterByTags();
// 或
const clusters = await cluster.clusterBySimilarity(threshold: 0.8);
```

### 7.2 实体追踪 (EntityTracker)

```typescript
const tracker = new EntityTracker(palace);
const entities = await tracker.extractEntities();
// 返回: { people: [...], projects: [...], concepts: [...] }
```

### 7.3 知识图谱 (KnowledgeGraphBuilder)

```typescript
const builder = new KnowledgeGraphBuilder(palace);
const graph = await builder.build();
// 返回: { nodes: [...], edges: [...] }
```

---

## 八、安全特性

### 8.1 正则注入防护

```typescript
// manager.ts
function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
```

### 8.2 并发安全

```typescript
// storage.ts - 文件锁机制
class FileLock {
  async withLock<T>(key: string, fn: () => Promise<T>): Promise<T> {
    // 防止同一文件并发写入冲突
  }
}
```

---

## 九、项目状态

| 阶段 | 状态 | 完成日期 |
|------|------|----------|
| 技术方案 | ✅ 完成 | 2026-03-18 |
| TypeScript 开发 | ✅ 完成 | 2026-03-18 |
| 单元测试 | ✅ 24 个通过 | 2026-03-18 |
| 安全修复 | ✅ 完成 | 2026-03-18 |
| 产品验收 | ✅ 通过 | 2026-03-18 |
| OpenClaw 联调 | 🔄 进行中 | - |

---

## 十、后续规划

1. **Phase 3**：认知增强模块完善
   - 实体提取 NER 增强
   - 知识图谱可视化
   
2. **Phase 4**：生产优化
   - 多进程文件锁（proper-lockfile）
   - 性能监控
   - 批量导入/导出

---

🔥 混沌团队 - Memory Palace 项目组