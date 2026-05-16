# 工具详细参数

本文档包含 Memory Palace 所有工具的完整参数说明。

---

## 基础操作

### memory_palace_write

写入一条新记忆。

**参数**:
- `content` (必填): 记忆内容，字符串
- `location` (可选): 存储位置，默认 "default"
- `tags` (可选): 标签数组，如 ["ui", "偏好"]
- `importance` (可选): 重要性 0-1，默认 0.5
- `type` (可选): 类型 fact/experience/lesson/preference/decision

**示例**:
```json
{
  "content": "用户偏好深色模式",
  "location": "preferences",
  "tags": ["ui", "偏好"],
  "importance": 0.8,
  "type": "preference"
}
```

---

### memory_palace_get

获取单条记忆。

**参数**:
- `id` (必填): 记忆ID

**返回**: 完整的记忆对象

---

### memory_palace_update

更新记忆内容。

**参数**:
- `id` (必填): 记忆ID
- `content` (可选): 新内容
- `tags` (可选): 新标签
- `importance` (可选): 新重要性值

---

### memory_palace_delete

删除记忆。

**参数**:
- `id` (必填): 记忆ID

---

### memory_palace_search

搜索记忆。

**参数**:
- `query` (必填): 搜索关键词
- `tags` (可选): 标签过滤数组
- `top_k` (可选): 返回数量，默认 10
- `min_score` (可选): 最低相关性分数，默认 0.3

**示例**:
```json
{
  "query": "用户偏好",
  "tags": ["偏好"],
  "top_k": 5
}
```

---

### memory_palace_list

列出所有记忆。

**参数**:
- `location` (可选): 按位置过滤
- `type` (可选): 按类型过滤
- `limit` (可选): 返回数量限制

---

### memory_palace_stats

获取记忆统计信息。

**参数**: 无

**返回**: 记忆总数、位置分布、类型分布、平均重要性等

---

### memory_palace_restore

从回收站恢复记忆。

**参数**:
- `id` (必填): 记忆ID

---

## 经验管理

### memory_palace_record_experience

记录一条可复用的经验。

**参数**:
- `content` (必填): 经验内容
- `category` (可选): 类别 development/operations/product/communication/general
- `applicability` (必填): 适用场景描述
- `source` (必填): 来源标识

**示例**:
```json
{
  "content": "TypeScript 的 as const 可以让类型推断更精确",
  "category": "development",
  "applicability": "需要精确类型推断的场景",
  "source": "task-123"
}
```

---

### memory_palace_get_experiences

获取所有经验。

**参数**:
- `category` (可选): 按类别过滤
- `verified_only` (可选): 仅返回已验证的，默认 false

---

### memory_palace_verify_experience

验证经验是否有效。

**参数**:
- `id` (必填): 经验ID
- `effective` (必填): 是否有效 (true/false)

**说明**: 经验需要 2+ 次正面验证才标记为已验证。

---

### memory_palace_get_relevant_experiences

查找相关经验。

**参数**:
- `context` (必填): 上下文描述
- `category` (可选): 类别过滤
- `limit` (可选): 返回数量，默认 5

---

### memory_palace_get_frequently_accessed

获取最常访问的记忆。

**参数**:
- `limit` (可选): 返回数量，默认 10

**返回**: 按访问频率排序的记忆列表

---

### memory_palace_record_access

记录记忆被访问（更新 lastAccessedAt 时间戳）。

**参数**:
- `ids` (必填): 记忆ID数组

---

## LLM 增强

### memory_palace_summarize

LLM 智能总结记忆。

**参数**:
- `id` (必填): 记忆ID
- `save_summary` (可选): 是否保存到记忆，默认 true

**超时**: 60 秒

**返回**:
```json
{
  "summary": "总结内容",
  "keyPoints": ["要点1", "要点2"],
  "importance": 0.8,
  "suggestedTags": ["标签1"],
  "category": "fact"
}
```

---

### memory_palace_extract_experience

从记忆内容中提取可复用的经验。

**参数**:
- `memory_ids` (可选): 记忆ID数组，默认处理所有记忆

**超时**: 60 秒

---

### memory_palace_parse_time_llm

LLM 解析复杂时间表达式。

**参数**:
- `expression` (必填): 时间表达式

**支持**: "下周三之前的那天"、"三个月后的第一个周一" 等复杂表达

**超时**: 10 秒

**返回**:
```json
{
  "date": "2024-01-15",
  "confidence": 0.9
}
```

---

### memory_palace_expand_concepts_llm

LLM 动态扩展搜索概念。

**参数**:
- `query` (必填): 搜索词

**超时**: 15 秒

**返回**:
```json
{
  "keywords": ["用户偏好", "设置", "配置"],
  "domains": ["preferences", "settings"]
}
```

---

### memory_palace_compress

智能压缩多条记忆。

**参数**:
- `memory_ids` (必填): 记忆ID数组

**超时**: 60 秒

---

## 辅助工具

### memory_palace_time_parse

基于规则的时间解析。

**参数**:
- `query` (必填): 时间查询字符串

**支持**: 简单的时间表达式，如 "昨天"、"上周"、"2024年1月"

---

### memory_palace_concept_expand

基于规则的概念扩展。

**参数**:
- `query` (必填): 查询词

**返回**: 扩展后的关键词列表

---

## 向量模型

### memory_palace_check_model_status

检查 BGE 向量模型是否已安装。

**返回**:
```json
{
  "isInstalled": true,
  "modelName": "BAAI/bge-small-zh-v1.5",
  "cacheDir": "/data/agent-memory-palace/model_cache",
  "message": "Model BAAI/bge-small-zh-v1.5 is installed at /data/agent-memory-palace/model_cache"
}
```

### memory_palace_install_model

触发向量模型安装（执行安装脚本）。

**注意**: 建议直接运行 `bash scripts/install-vector-model.sh`