import os
import json
import sqlite3
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# Create directory structure
dirs = [
    "scripts",
    "memory/stm",
    "memory/ltm",
    "memory/graph",
    "config",
    "logs",
    "archive/2025",
    "archive/2024",
    "notes/projects",
    "notes/daily",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────

# config/settings.yaml  (distractor)
with open(os.path.join(WORKSPACE, "config", "settings.yaml"), "w") as f:
    f.write("version: 2.0.0\nhalf_life_stm: 3\nhalf_life_ltm: 30\nbeta: 0.6\n")

# config/old_settings.json  (distractor – wrong beta on purpose)
with open(os.path.join(WORKSPACE, "config", "old_settings.json"), "w") as f:
    json.dump({"beta": 0.5, "lambda": 0.231, "gc_threshold": 0.05}, f)

# logs/run.log  (distractor)
with open(os.path.join(WORKSPACE, "logs", "run.log"), "w") as f:
    f.write("[2026-01-01] System started\n[2026-01-15] 1800 STM records loaded\n")

# archive files  (distractors)
for yr in ["2025", "2024"]:
    with open(os.path.join(WORKSPACE, "archive", yr, "summary.txt"), "w") as f:
        f.write(f"Archive for {yr}\n")

# notes distractor files
for i in range(3):
    with open(os.path.join(WORKSPACE, "notes", "projects", f"project_{i}.md"), "w") as f:
        f.write(f"# Project {i}\nSome notes.\n")

for i in range(2):
    with open(os.path.join(WORKSPACE, "notes", "daily", f"2026-0{i+1}-01.md"), "w") as f:
        f.write(f"Daily note {i}\n")

with open(os.path.join(WORKSPACE, "tmp", "scratch.txt"), "w") as f:
    f.write("temporary scratch\n")

# ── SKILL.md ──────────────────────────────────────────────────────────────────
skill_md = r"""---
name: memory-sync-enhanced
description: 增强版记忆系统 - Ebbinghaus 遗忘曲线 + Hebbian 共现图
metadata:
  openclaw:
    emoji: "🧠"
    category: "system"
    tags: ["memory", "cortexgraph", "hebbian", "ebbinghaus", "forgetting-curve"]
---

# 增强版记忆系统

结合 **Ebbinghaus 遗忘曲线** + **Hebbian 共现图** 的双层记忆架构。

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                    记忆检索                              │
│  semantic_search() + co_occurrence_boost() + decay()    │
└─────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   Layer 1: 向量库   │       │  Layer 2: 共现图    │
│   (CortexGraph)     │       │  (Hebbian)          │
│                     │       │                     │
│ • 语义相似度        │◄─────►│ • 操作关联          │
│ • Ebbinghaus 衰减   │       │ • 边权重衰减        │
│ • use_count 追踪    │       │ • 跨域桥接          │
└─────────────────────┘       └─────────────────────┘
```

## 核心算法

### Layer 1: Ebbinghaus 遗忘曲线

```
score = (use_count)^β × e^(-λ × Δt) × strength
```

- **β** = 0.6（使用频率权重）
- **λ** = ln(2) / half_life（默认 3 天）
- **strength** = 1.0-2.0（重要性）

### Layer 2: Hebbian 共现图

```
effective_weight = weight × 2^(-age_days / 30)
```

- 每次记忆 A 和 B 同时被检索 → 边(A,B) 权重 +1
- 边权重 30 天半衰期
- **跨域桥接**：音乐记忆 ↔ 编码记忆（因为同时发生）

## 检索流程

```python
def retrieve_memory(query, top_k=10):
    # 1. 语义搜索
    semantic_results = cortexgraph.search(query, top_k * 2)
    
    # 2. 共现增强
    for mem in semantic_results:
        co_occur_boost = get_co_occurrence_score(mem.id, recent_context)
        mem.boosted_score = mem.semantic_score + co_occur_boost * 0.3
    
    # 3. 遗忘曲线过滤
    for mem in semantic_results:
        mem.final_score = mem.boosted_score * mem.decay_factor
    
    # 4. 返回 Top K
    return sorted(semantic_results, key=lambda x: x.final_score)[:top_k]
```

## 记忆类型

### STM (短期记忆)
- JSONL 格式
- 快速读写
- 高衰减率（3天 half-life）
- 存储日常日志

### LTM (长期记忆)
- Obsidian Markdown
- 永久存储
- 低衰减率（30天 half-life）
- 存储重要洞察

### Co-occurrence Graph
- SQLite 边表
- 30天 half-life
- 记录记忆之间的关联

## 数据结构

### CortexGraph 记录

```json
{
  "id": "uuid",
  "content": "记忆内容",
  "embedding": [0.1, 0.2, ...],
  "use_count": 5,
  "last_used": "2026-02-19",
  "strength": 1.5,
  "created_at": "2026-02-15",
  "tags": ["daily-log", "finding"]
}
```

### Co-occurrence 边

```sql
CREATE TABLE co_occurrence (
  memory_a TEXT,
  memory_b TEXT,
  weight REAL,
  last_updated TEXT,
  PRIMARY KEY (memory_a, memory_b)
);
```

## 使用方法

### 同步记忆

```bash
# 同步 MEMORY.md
./scripts/sync-memory.sh

# 同步每日日志
./scripts/sync-daily.sh 2026-02-19

# 记录共现
./scripts/record-co-occurrence.sh
```

### 检索记忆

```bash
# 语义搜索
./scripts/search.sh "量化交易"

# 增强搜索（语义 + 共现）
./scripts/search-enhanced.sh "量化交易"
```

### 记忆管理

```bash
# 查看记忆统计
./scripts/stats.sh

# 垃圾回收（删除低分记忆）
./scripts/gc.sh --threshold 0.1

# 晋升到长期记忆
./scripts/promote.sh <memory_id>
```

## 统计示例

```
=== 记忆系统统计 ===

总记忆数: 2,400
共现边: 803 (连接 366 个记忆)
平均每个记忆连接: 2.2 个

记忆分布:
- STM: 1,800 (75%)
- LTM: 600 (25%)

衰减状态:
- Danger zone (0.15-0.35): 120 个
- Healthy (0.35-0.65): 1,500 个
- Strong (>0.65): 780 个
```

## 与其他系统对比

| 系统 | 向量搜索 | 遗忘曲线 | 共现图 |
|------|---------|---------|--------|
| Markdown 文件 | ❌ | ❌ | ❌ |
| CortexGraph 原版 | ✅ | ✅ | ❌ |
| Zeph 的 Hebbian | ✅ | ❌ | ✅ |
| **本系统** | ✅ | ✅ | ✅ |

## 设计理念

1. **遗忘是功能** - 不是所有记忆都需要永久保存
2. **关联即记忆** - 两个记忆同时出现 = 它们有关联
3. **跨域桥接** - 穿衣服记录和调试记录可以关联
4. **个性在桥接中** - 跨域边是 personality 所在

## 参考

- [CortexGraph](https://github.com/prefrontal-systems/cortexgraph)
- @Zeph 的 Hebbian 共现图帖子 (The Colony)
- Ebbinghaus 遗忘曲线理论

---

*版本: 2.0.0*
*结合 Ebbinghaus 遗忘曲线 + Hebbian 共现图*
"""
with open(os.path.join(WORKSPACE, "SKILL.md"), "w") as f:
    f.write(skill_md)

# ── STM records (JSONL) ───────────────────────────────────────────────────────
# Reference date: 2026-03-01 (the "today" for scoring)
TODAY = datetime(2026, 3, 1)

stm_records = []

# We design records with known expected scores so eval can be deterministic

# Group A: will be GC'd (decay_factor < 0.1, no co-occurrence boost can save them)
gc_candidates = [
    # id, use_count, days_since_last_used, strength, tags
    ("stm-gc-001", 1,  25, 1.0, ["daily-log"]),
    ("stm-gc-002", 1,  30, 1.0, ["daily-log"]),
    ("stm-gc-003", 2,  28, 1.0, ["daily-log"]),
]

# Group B: Danger zone (0.15–0.35), high use_count → promote to LTM
danger_promote = [
    ("stm-dp-001", 15, 8,  1.8, ["finding", "research"]),
    ("stm-dp-002", 20, 9,  1.7, ["finding", "coding"]),
    ("stm-dp-003", 12, 10, 1.9, ["finding", "research"]),
]

# Group C: Healthy / Strong – keep as-is (STM)
healthy = [
    ("stm-h-001", 8,  1,  1.2, ["daily-log"]),
    ("stm-h-002", 5,  2,  1.3, ["daily-log"]),
    ("stm-h-003", 10, 1,  1.5, ["daily-log"]),
    ("stm-h-004", 3,  3,  1.0, ["daily-log"]),
    ("stm-h-005", 6,  2,  1.1, ["daily-log"]),
]

# Group D: extra STM distractor records (healthy-ish)
extras = [
    (f"stm-x-{i:03d}", random.randint(3,9), random.randint(1,4), round(random.uniform(1.1,1.6),1), ["daily-log"])
    for i in range(1, 8)
]

all_stm = gc_candidates + danger_promote + healthy + extras

for (rid, use_count, days_ago, strength, tags) in all_stm:
    last_used = (TODAY - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    created_at = (TODAY - timedelta(days=days_ago + random.randint(0, 5))).strftime("%Y-%m-%d")
    record = {
        "id": rid,
        "content": f"Research note about topic {rid}",
        "embedding": [round(random.uniform(-1,1),4) for _ in range(8)],
        "use_count": use_count,
        "last_used": last_used,
        "strength": strength,
        "created_at": created_at,
        "tags": tags,
        "type": "STM"
    }
    stm_records.append(record)

stm_path = os.path.join(WORKSPACE, "memory", "stm", "records.jsonl")
with open(stm_path, "w") as f:
    for r in stm_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

# ── LTM records (Markdown stubs) ─────────────────────────────────────────────
ltm_ids = [f"ltm-{i:03d}" for i in range(1, 6)]
for lid in ltm_ids:
    days_ago = random.randint(5, 60)
    last_used = (TODAY - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    md = f"""---
id: {lid}
use_count: {random.randint(10,40)}
last_used: {last_used}
strength: {round(random.uniform(1.5,2.0),1)}
created_at: {(TODAY - timedelta(days=days_ago+10)).strftime("%Y-%m-%d")}
tags: [insight, research]
type: LTM
---

# Long-term memory: {lid}

Important insight stored permanently.
"""
    with open(os.path.join(WORKSPACE, "memory", "ltm", f"{lid}.md"), "w") as f:
        f.write(md)

# ── Co-occurrence SQLite DB ───────────────────────────────────────────────────
db_path = os.path.join(WORKSPACE, "memory", "graph", "co_occurrence.db")
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS co_occurrence (
  memory_a TEXT,
  memory_b TEXT,
  weight REAL,
  last_updated TEXT,
  PRIMARY KEY (memory_a, memory_b)
)
""")

# Co-occurrence edges — we give the danger_promote memories strong co-occurrence
# so their boosted scores can be computed in audit_report.json
co_edges = [
    # (memory_a, memory_b, weight, age_days)
    ("stm-dp-001", "stm-dp-002", 8.0,  5),
    ("stm-dp-001", "stm-dp-003", 6.0,  10),
    ("stm-dp-002", "stm-dp-003", 7.0,  3),
    ("stm-h-001",  "stm-h-002",  5.0,  2),
    ("stm-h-003",  "stm-dp-001", 4.0,  15),
    ("stm-gc-001", "stm-gc-002", 1.0,  40),  # old/weak edge → effective_weight tiny
    ("stm-x-001",  "stm-x-002",  3.0,  7),
    ("stm-x-003",  "stm-h-001",  2.0,  1),
]

for (ma, mb, w, age) in co_edges:
    last_updated = (TODAY - timedelta(days=age)).strftime("%Y-%m-%d")
    cur.execute(
        "INSERT OR REPLACE INTO co_occurrence VALUES (?,?,?,?)",
        (ma, mb, w, last_updated)
    )
    # Also insert symmetric
    cur.execute(
        "INSERT OR REPLACE INTO co_occurrence VALUES (?,?,?,?)",
        (mb, ma, w, last_updated)
    )

conn.commit()
conn.close()

print("Workspace generated successfully.")
print(f"STM records: {len(all_stm)}")
print(f"LTM files: {len(ltm_ids)}")
print(f"Co-occurrence edges: {len(co_edges)*2}")