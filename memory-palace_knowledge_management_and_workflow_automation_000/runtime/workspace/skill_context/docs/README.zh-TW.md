# Memory Palace

> OpenClaw 智能代理的認知增強層

## 簡介

Memory Palace（記憶宮殿）是一個 OpenClaw Skill，為智能代理提供持久化記憶管理能力，支援語意搜尋、知識圖譜和認知增強功能。

## 特性

- 📝 **持久化儲存** - 記憶以 Markdown 檔案形式儲存
- 🔍 **語意檢索** - 向量搜尋優先，文字搜尋備援
- ⏰ **時間推理** - 解析時間表達式（明天、下週、本月等）
- 🧠 **概念擴展** - 擴展查詢相關概念
- 🏷️ **標籤系統** - 靈活的分類機制
- 📍 **位置管理** - 按位置組織記憶
- ⭐ **重要性評分** - 為重要記憶設定優先級
- 🗑️ **資源回收筒機制** - 軟刪除，支援復原
- 🔄 **背景任務** - 衝突檢測、記憶壓縮

### v1.2.0 新功能

- 🧠 **LLM 整合** - AI 驅動的摘要、經驗提取、時間解析
- 📚 **經驗累積** - 記錄、驗證和檢索經驗
- 💡 **記憶類型** - 將記憶分類為事實/經驗/教訓/偏好/決策

## 安裝

### 方式一：透過 ClawHub 安裝（推薦）

```bash
# 從 ClawHub 安裝 Memory Palace skill
clawhub install memory-palace
```

### 方式二：從原始碼安裝

```bash
git clone https://github.com/Lanzhou3/memory-palace.git
cd memory-palace
npm install
npm run build
```

## 快速開始

```typescript
import { MemoryPalaceManager } from '@openclaw/memory-palace';

const manager = new MemoryPalaceManager({
  workspaceDir: '/path/to/workspace'
});

// 儲存記憶
const memory = await manager.store({
  content: '使用者偏好深色模式',
  tags: ['preferences', 'ui'],
  importance: 0.8,
  location: 'user-settings'
});

// 檢索記憶
const results = await manager.recall('使用者偏好');

// 列出記憶
const memories = await manager.list({
  tags: ['preferences'],
  limit: 10
});

// 取得統計資訊
const stats = await manager.stats();
```

## 儲存結構

記憶儲存在 `{workspaceDir}/memory/palace/` 目錄下，以 Markdown 檔案形式儲存：

```
workspace/
└── memory/
    └── palace/
        ├── uuid-1.md
        ├── uuid-2.md
        └── .trash/
            └── deleted-uuid.md
```

### 檔案格式

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

記憶內容...

## Summary
選用摘要
```

## API 文件

### MemoryPalaceManager

#### 建構函式

```typescript
new MemoryPalaceManager(options: {
  workspaceDir: string;
  vectorSearch?: VectorSearchProvider;  // 選用
})
```

#### 方法

| 方法 | 說明 |
|------|------|
| `store(params)` | 儲存新記憶 |
| `get(id)` | 根據 ID 取得記憶 |
| `update(params)` | 更新記憶 |
| `delete(id, permanent?)` | 刪除記憶（預設軟刪除） |
| `recall(query, options?)` | 搜尋記憶 |
| `list(options?)` | 帶篩選條件的列表 |
| `stats()` | 取得統計資訊 |
| `restore(id)` | 從資源回收筒復原 |
| `listTrash()` | 列出已刪除記憶 |
| `emptyTrash()` | 清空資源回收筒 |
| `storeBatch(items)` | 批次儲存 |
| `getBatch(ids)` | 批次取得 |

### 經驗管理（v1.2.0）

| 方法 | 說明 |
|------|------|
| `recordExperience(params)` | 記錄可復用的經驗 |
| `getExperiences(options?)` | 按條件查詢經驗 |
| `verifyExperience(id, effective)` | 標記經驗是否有效 |
| `getRelevantExperiences(context)` | 獲取與當前上下文相關的經驗 |

### LLM 增強方法（v1.1.0）

| 方法 | 說明 |
|------|------|
| `summarize(id)` | AI 驅動的記憶摘要 |
| `extractExperience(memoryIds)` | 從記憶中提取經驗教訓 |
| `parseTimeLLM(expression)` | 複雜時間表達式解析 |
| `expandConceptsLLM(query)` | 動態概念擴展 |
| `compress(memoryIds)` | 智慧記憶壓縮 |

### 認知模組

```typescript
import {
  TopicCluster,
  EntityTracker,
  KnowledgeGraphBuilder
} from '@openclaw/memory-palace';

// 主題聚類
const cluster = new TopicCluster();
const clusters = await cluster.cluster(memories);

// 實體追蹤
const tracker = new EntityTracker();
const { entities, coOccurrences } = await tracker.track(memories);

// 知識圖譜
const graphBuilder = new KnowledgeGraphBuilder();
const graph = await graphBuilder.build(memories);
```

### 背景任務

```typescript
import {
  ConflictDetector,
  MemoryCompressor
} from '@openclaw/memory-palace';

// 衝突檢測
const detector = new ConflictDetector();
const conflicts = await detector.detect(memories);

// 記憶壓縮
const compressor = new MemoryCompressor();
const results = await compressor.compress(memories);
```

## 與 OpenClaw 整合

Memory Palace 設計為封裝 OpenClaw 的 `MemoryIndexManager`，提供向量搜尋能力。

### 啟用向量搜尋

```typescript
import { MemoryPalaceManager } from '@openclaw/memory-palace';
import { MemoryIndexManager } from '@openclaw/memory';

const vectorSearch = new MemoryIndexManager({
  // OpenClaw 設定
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

### 無向量搜尋模式

即使不設定向量搜尋，Memory Palace 也能正常運作，會自動降級為文字匹配。

## 測試

```bash
npm test
```

## 架構原則

1. **無 MCP 協定** - 直接函式呼叫，無外部協定
2. **介面隔離** - 向量搜尋為選用介面
3. **檔案儲存** - 簡單、可攜、人類可讀
4. **優雅降級** - 無進階功能時仍可運作

## 授權條款

MIT

---

🔥 由混沌團隊構建