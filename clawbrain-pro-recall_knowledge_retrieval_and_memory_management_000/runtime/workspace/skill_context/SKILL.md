---
name: clawbrain-pro-recall
description: 给龙虾添加"回忆"能力：搜索历史对话、查找旧文件、检索归档记忆。再也不会说"我不记得了"。
user-invocable: true
metadata: {"openclaw": {"emoji": "🔍", "requires": {"bins": ["grep", "find"]}}}
---

# ClawBrain Recall

让你的龙虾拥有"回忆"能力——能搜索和检索过去的对话、文件和记忆。

## 解决什么问题

默认的 OpenClaw Agent 只能看到当前对话上下文。一旦对话结束或上下文被压缩，之前的内容就"忘了"。Recall 让 Agent 能够：

- 搜索历史对话记忆
- 查找之前生成的文件和数据
- 检索归档的旧记忆
- 基于历史上下文给出更准确的回答

## 工作原理

当用户提到过去的事情时，Agent 自动执行多层搜索：

```
第 1 层：memory/*.md（近期记忆）
    ↓ 找不到
第 2 层：memory/archive/*.md（归档记忆）
    ↓ 找不到
第 3 层：workspace 全局搜索（文件、数据、文档）
    ↓ 找不到
诚实告知，请用户补充
```

## 触发方式

以下表达会自动触发回忆搜索：
- "之前我们讨论过..."
- "你还记得...吗"
- "找一下上次的..."
- "之前那个文件在哪"
- "看看 #标签"

## 搜索命令

Agent 会使用以下命令搜索：
```bash
# 搜索记忆文件
grep -rl '关键词' memory/ memory/archive/

# 搜索工作区文件
find . -name '*.md' -exec grep -l '关键词' {} \;

# 按日期查找
ls -lt memory/ | head -20
```

## 建议配合使用

- **clawbrain-pro-memory**：主动记录 + 被动回忆，完整的记忆体系
- **ClawBrain Pro Auto**：智能决策引擎，复杂问题深度思考

了解更多：https://clawbrain.dev
