# 记忆管理脚本

## 📚 功能说明

三层记忆架构：**每天 → 每周 → 长期**

## 🔧 脚本列表

### 1. memory-loader.sh - 加载记忆

加载三层记忆到 `SESSION-STATE.md` 缓存文件。

```bash
bash scripts/memory-loader.sh
```

**加载内容**:
- 今日记忆 (memory/daily/YYYY-MM-DD.md)
- 昨日记忆
- 最近 3 天 daily 记忆（前 50 行）
- 长期记忆 (MEMORY.md, 前 150 行)
- 最近 weekly 记忆（前 80 行）

**输出**: `~/.openclaw/workspace/SESSION-STATE.md`

---

### 2. memory-search.sh - 搜索记忆

在加载的记忆缓存中搜索关键词。

```bash
bash scripts/memory-search.sh "搜索关键词"
```

**例子**:
```bash
# 搜索 CSS 相关内容
bash scripts/memory-search.sh "CSS"

# 搜索模板开发
bash scripts/memory-search.sh "模板"

# 搜索 Ollama 配置
bash scripts/memory-search.sh "Ollama"
```

**输出**: 带上下文的搜索结果（前后 3 行）

---

### 3. memory-refresh.sh - 智能刷新记忆缓存

**智能检查**：只在记忆文件最近 10 分钟内更新过时才刷新。

```bash
bash ~/.openclaw/workspace/skills/memory-archiver/scripts/memory-refresh.sh
```

**工作流程**:
1. 检查今日记忆文件是否存在
2. 检查文件最后修改时间
3. 如果最近 10 分钟内更新过 → 重新加载全部记忆
4. 否则 → 跳过刷新（避免无效刷新）

**使用场景**:
- ✅ 记忆及时写入 cron 任务完成后（**自动触发**）
- 手动更新记忆文件后
- 确保缓存与文件同步

**自动化**:
- 每 10 分钟的记忆及时写入任务完成后，自动调用刷新脚本
- 智能判断：无更新时跳过，节省资源

---

### 4. memory-dedup.sh - 长期记忆自动去重

检测并清理 MEMORY.md 中的**重复内容、无意义日常、重复任务进度**。

```bash
bash scripts/memory-dedup.sh
```

**工作流程**:
1. 备份 MEMORY.md 到 `MEMORY.md.backup.YYYYMMDD-HHMMSS`
2. 检测并删除：
   - ❌ 重复的上下文
   - ❌ 毫无意义的日常（无事发生）
   - ❌ 重复的任务进度提示
   - ❌ 相似段落
3. 保留唯一有价值内容
4. 显示去重统计

**使用场景**:
- ✅ 每周记忆总结完成后（**自动触发**）
- 手动整理长期记忆后
- 定期维护（建议每周一次）

**自动化**:
- 每周日 22:00 记忆总结后自动调用
- 自动备份，可恢复

---

## 💬 在对话中使用

### 加载记忆
```
加载记忆
```
→ 运行 `memory-loader.sh`

### 搜索记忆
```
搜索记忆：CSS 框架
```
→ 运行 `memory-search.sh "CSS 框架"`

### 刷新记忆
```
刷新记忆
```
→ 运行 `memory-refresh.sh`

---

## 📊 文件结构

```
~/.openclaw/workspace/
├── skills/memory-archiver/scripts/
│   ├── memory-loader.sh          # 加载记忆
│   ├── memory-search.sh          # 搜索记忆
│   ├── memory-refresh.sh         # 智能刷新
│   ├── memory-dedup.sh           # 自动去重
│   ├── auto-memory-search.sh     # 自动触发搜索
│   └── README.md                 # 本文件
├── SESSION-STATE.md              # 记忆缓存（自动生成）
├── MEMORY.md                     # 长期记忆
└── memory/
    ├── daily/                    # 每日记忆
    └── weekly/                   # 每周记忆
```

---

## 🔄 自动化

### Cron 任务集成

在记忆及时写入任务后添加刷新：

```bash
# 记忆及时写入后刷新缓存
bash ~/.openclaw/workspace/scripts/memory-refresh.sh
```

---

*最后更新：2026-03-20*
`memory-search.sh "CSS 框架"`

### 刷新记忆
```
刷新记忆
```
→ 运行 `memory-refresh.sh`

---

## 📊 文件结构

```
~/.openclaw/workspace/
├── scripts/
│   ├── memory-loader.sh      # 加载记忆
│   ├── memory-search.sh      # 搜索记忆
│   ├── memory-refresh.sh     # 智能刷新
│   ├── memory-dedup.sh       # 自动去重
│   └── README.md             # 本文件
├── SESSION-STATE.md          # 记忆缓存（自动生成）
├── MEMORY.md                 # 长期记忆
└── memory/
    ├── daily/                # 每日记忆
    └── weekly/               # 每周记忆
```

---

## 🔄 自动化

### Cron 任务集成

在记忆及时写入任务后添加刷新：

```bash
# 记忆及时写入后刷新缓存
bash ~/.openclaw/workspace/scripts/memory-refresh.sh
```

---

*最后更新：2026-03-20*
