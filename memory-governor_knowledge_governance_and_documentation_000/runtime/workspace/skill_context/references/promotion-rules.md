# Promotion Rules

## 总原则

升级不是复制粘贴，而是提炼。

只有当一条信息已经从“发生过什么”变成“以后怎么判断 / 怎么做”时，才值得升格。

## 规则

### daily → MEMORY

满足任意两个条件时，才考虑从 `memory/YYYY-MM-DD.md` 升到 `MEMORY.md`：

- 两周后大概率仍然有效
- 在多个任务里重复出现
- 会影响未来判断或协作方式
- 已经从事件变成稳定模式

### correction → learning_candidates

默认先把明确纠错写进 `learning_candidates`。

原因：

- 用户纠正的是这一次的错，不一定已经证明是长期规则
- 单次纠错太容易过拟合到当前任务
- 候选层让宿主先收集证据，再决定是否值得硬化

### learning_candidates → reusable_lessons

满足任意两个条件时，才考虑升到 `reusable_lessons`：

- 同类问题在多个任务、日期或上下文中重复出现
- 已经能被改写成脱离当前案例的通用原则
- 用户明确把它表述为以后都应遵守的规则
- 它会稳定影响未来判断、执行或协作质量

例子：

- 纠错：别写客服腔
- 候选：这次输出太像客服模板，需要更直接
- 规则：默认直接、简洁、有判断

### self-improving/* → AGENTS

当经验会改变启动流程、协作边界、默认路由时，升级到 `AGENTS.md`。

### self-improving/* → TOOLS

当经验主要约束工具、命令、平台格式、配置时，升级到 `TOOLS.md`。

### self-improving/* → SOUL

当经验改变长期表达风格、判断方式、人格边界时，升级到 `SOUL.md`。

### session-state / working-buffer → 其他层

这两层默认不能直接升格。  
必须先提炼成稳定事实或复用规则，再进入长期层。

### learning_candidates → system_rules / tool_rules / AGENTS / TOOLS / SOUL

候选层默认不能直接升到系统级文件。

正确顺序是：

1. 先升到 `reusable_lessons`
2. 再判断它是否已经改变全局启动、工具、表达或协作规则

capture 阶段遇到歧义时，先看 [routing-precedence.md](routing-precedence.md)。

## 禁止升级的情况

- 原始长日志直接升到长期层
- 未验证的猜测升到长期层
- 单次纠错直接升到 `reusable_lessons`
- 候选内容直接升到 `AGENTS.md` / `TOOLS.md` / `SOUL.md`
- 临时恢复线索直接升到 `MEMORY.md`
- 项目局部事实直接升到全局规则
