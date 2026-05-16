# 使用示例

本文档包含 Memory Palace 的常见使用场景和示例。

---

## 记住用户偏好

### 写入用户偏好

```bash
npx memory-palace write --content "用户喜欢简洁的回复" --tags "偏好" --importance 0.8
```

或通过工具调用:

```json
{
  "tool": "memory_palace_write",
  "parameters": {
    "content": "用户喜欢简洁的回复",
    "tags": ["偏好"],
    "importance": 0.8,
    "type": "preference"
  }
}
```

### 搜索偏好记忆

```bash
npx memory-palace search --query "用户喜欢" --tags "偏好"
```

---

## 开发经验管理

### 记录开发经验

```bash
npx memory-palace record-experience \
  --content "OpenClaw 配置文件支持 JSON5 格式" \
  --category development \
  --applicability "读取 OpenClaw 配置时" \
  --source memory-palace-dev
```

### 验证经验有效性

```bash
npx memory-palace verify-experience --id <experience-id> --effective true
```

经验需要 2+ 次正面验证才标记为已验证。

### 查找相关经验

```bash
npx memory-palace get-relevant-experiences --context "需要解析用户配置文件"
```

---

## 智能搜索

### 语义搜索

```bash
npx memory-palace search --query "用户设置"
```

### 带标签过滤

```bash
npx memory-palace search --query "配置" --tags "开发" --top-k 5
```

---

## LLM 增强功能

### 智能总结长记忆

```bash
npx memory-palace summarize --id <memory-id>
```

返回:
```json
{
  "summary": "用户偏好深色模式，这是最重要的UI设置",
  "keyPoints": ["深色模式", "UI设置", "高优先级"],
  "importance": 0.9,
  "suggestedTags": ["ui", "主题", "偏好"],
  "category": "preference"
}
```

### LLM 时间解析

```bash
npx memory-palace parse-time-llm --expression "下周三之前的那天"
```

返回:
```json
{
  "date": "2024-01-15",
  "confidence": 0.9
}
```

### 概念扩展搜索

```bash
npx memory-palace expand-concepts-llm --query "用户偏好"
```

返回:
```json
{
  "keywords": ["用户偏好", "设置", "配置", "选项"],
  "domains": ["preferences", "settings"]
}
```

---

## 记忆管理

### 查看所有记忆

```bash
npx memory-palace list
```

### 查看统计信息

```bash
npx memory-palace stats
```

### 更新记忆

```bash
npx memory-palace update --id <memory-id> --content "新内容" --importance 0.9
```

### 删除记忆

```bash
npx memory-palace delete --id <memory-id>
```

### 恢复记忆

```bash
npx memory-palace restore --id <memory-id>
```

---

## 完整工作流示例

### 1. 首次使用：安装向量模型

```bash
cd memory-palace
bash scripts/install-vector-dependencies.sh
```

### 2. 写入用户信息

```bash
# 记住用户偏好
npx memory-palace write \
  --content "用户盘古是中国开发者，时区 Asia/Shanghai" \
  --tags "用户信息" \
  --importance 0.9

# 记住项目偏好
npx memory-palace write \
  --content "用户喜欢使用 TypeScript 而不是 Python" \
  --tags "技术偏好" \
  --importance 0.7
```

### 3. 记录开发经验

```bash
npx memory-palace record-experience \
  --content "OpenClaw 配置在 ~/.openclaw/workspace" \
  --category development \
  --applicability "需要查找 OpenClaw 配置时" \
  --source onboarding-task
```

### 4. 后续查询

```bash
# 搜索用户偏好
npx memory-palace search --query "盘古" --top-k 5

# 查找相关经验
npx memory-palace get-relevant-experiences --context "OpenClaw 配置"
```

---

## CLI 命令速查

| 命令 | 说明 |
|------|------|
| `npx memory-palace write` | 写入记忆 |
| `npx memory-palace get` | 获取记忆 |
| `npx memory-palace update` | 更新记忆 |
| `npx memory-palace delete` | 删除记忆 |
| `npx memory-palace search` | 搜索记忆 |
| `npx memory-palace list` | 列出记忆 |
| `npx memory-palace stats` | 统计信息 |
| `npx memory-palace restore` | 恢复记忆 |
| `npx memory-palace record-experience` | 记录经验 |
| `npx memory-palace get-experiences` | 获取经验 |
| `npx memory-palace verify-experience` | 验证经验 |
| `npx memory-palace get-relevant-experiences` | 相关经验 |
| `npx memory-palace summarize` | 智能总结 |
| `npx memory-palace extract-experience` | 提取经验 |
| `npx memory-palace parse-time-llm` | 时间解析 |
| `npx memory-palace expand-concepts-llm` | 概念扩展 |
| `npx memory-palace compress` | 智能压缩 |
| `npx memory-palace time-parse` | 规则时间解析 |
| `npx memory-palace concept-expand` | 规则概念扩展 |