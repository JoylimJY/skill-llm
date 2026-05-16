---
name: apollo-state-machine
description: >
  基于Claude Code状态机架构的AI任务协调模式。核心：while+switch状态机驱动任务执行，
  保证每步完成才切换下一步，支持用户随时打断并从中断处恢复。
  触发词：状态机、任务卡死、打断恢复、步骤控制、AI执行流程。
version: 1.0.0
read_when:
  - 设计复杂AI工作流程时
  - 任务执行顺序混乱时
  - 需要支持用户打断时
  - 构建多阶段任务系统时
  - AI执行不受控制时
metadata:
  openclaw:
    emoji: "⚙️"
    requires:
      bins: []
      env: []
    triggers:
      - 状态机
      - 任务卡死
      - 打断恢复
      - 步骤控制
      - AI执行流程
    suite: apollo
---

# Apollo State Machine - 状态机驱动原则

## 核心准则

**用最简单的 while+switch 状态机驱动 AI 任务执行。每步完成才切换下一步，支持用户随时打断。**

Claude Code 的状态机核心：

```
queued → awaiting-basic → awaiting-response → awaiting-tool-calls → (循环)
```

## 为什么重要

- **可中断**：用户可以随时发消息打断，状态机从 `interrupted` → `queued` 恢复
- **可控**：每步完成才切换，不会乱跑
- **可追踪**：状态字段明确知道现在在哪一步
- **简单胜于复杂**：不需要复杂的异步框架，一个 while 循环足够

## 三种核心状态流转

| 状态 | 做什么 | 切换条件 |
|------|--------|---------|
| awaiting-basic | 等待用户输入或继续 | 有输入则编译 |
| awaiting-response | AI 生成响应 | 有工具调用则执行，否则完成 |
| awaiting-tool-calls | 执行工具调用 | 执行完返回 awaiting-basic |

## 用户打断处理

```
用户发消息 → 
  状态变为 interrupted → 
  enqueueUserMessage() →
  状态变为 queued →
  从头继续执行
```

## 状态机设计检查表

- [ ] 所有可能的状态是否都已定义？
- [ ] 每个状态是否有明确的进入/退出条件？
- [ ] 是否支持用户打断并正确恢复？
- [ ] 状态转换是否是原子的（不会半途而废）？
- [ ] 是否有 idle 状态表示任务完成？

## 应用场景

**适合用状态机的场景：**
- 复杂多步骤任务（代码生成→测试→修复→验证）
- 需要支持用户中途介入的任务
- 长时间运行的后台任务
- 多轮对话中的任务追踪

**不适合的场景：**
- 简单的一次性问答
- 完全独立的短任务
- 不需要关心中间状态的操作

## 参考

来源：Claude Code coordinator/index.ts，512,000行源码研究
