# Stateful Targets

## Goal

有些 target class 不是“越写越多越好”，而是必须保持当前真相。

这份文档定义：

- 哪些 target class 是状态型
- 它们该用 append、replace 还是 merge
- 多个 skill 一起写时，什么算 canonical state

## Classification

### Append-Oriented

这些更像日志或档案：

- `daily_memory`
- `reusable_lessons`
- `project_facts` 中的历史记录部分

默认行为：

- append
- 允许按主题整理
- 不要求始终只有一个“当前值”

### State-Oriented

这些更像当前状态槽位：

- `proactive_state`
- `working_buffer`

默认行为：

- 优先维护“当前真相”
- 不应无限 append 成流水账
- 必须能快速看出最新状态

## Canonical Write Semantics

### `proactive_state`

`proactive_state` 是一个 state family，不一定只对应一个文件。

宿主可以有两种实现：

- combined file
- split adapter: durable boundary slice + current task state slice

默认写语义：

- replace for canonical fields
- append only for very short change notes if the host explicitly wants them

最小推荐字段：

- `updated_at`
- `current_objective`
- `current_blocker`
- `next_move`
- optional `durable_boundaries`
- `owner` or `source_skill` when multiple writers exist

规则：

- 新状态覆盖旧状态，不要把每次变化都当历史日志
- 如果 adapter 是 split implementation，`session-state` slice 负责当前任务真相，boundary slice 负责 durable proactive boundaries
- 如果多个 skill 都会写，宿主必须定义 canonical writer 或 merge policy
- 没有明确 merge policy 时，latest valid update wins

### `working_buffer`

默认写语义：

- append for short-lived breadcrumbs
- prune aggressively

最小推荐字段：

- `updated_at`
- `task_ref` if available
- `breadcrumb`
- optional `source_skill`

规则：

- 一条 breadcrumb 只服务当前恢复，不要把它写成长期说明
- 完成恢复后，删除、合并或提炼
- 同一 task 下重复 breadcrumb 应合并，不应无限重复

## Multi-Writer Rule

如果多个 skill 会写同一个 stateful target：

1. host should define a canonical writer if possible
2. if not, require `updated_at`
3. if not, require `source_skill`
4. conflicts resolve to the newest valid state unless the host defines stronger precedence

不要把“谁先写进去”当成权威。

## Anti-Patterns

- 把 `proactive_state` 写成操作日志
- 把 `working_buffer` 写成永久草稿箱
- 多个 skill 同时 append 当前状态，没人负责覆盖旧值
- 没有时间戳也没有 source，就宣称这份状态是“当前真相”
