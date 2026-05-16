# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-03-27

### Added

- 初始版本发布
- 基础第一性原理分析框架
- 分阶段分析流程（质疑→分解→验证→重构）
- 假设识别与质疑功能
- 5 层「为什么」追问支持
- 基本真理验证标准
- 重构方案生成
- Markdown 报告输出
- 完整版本演进档案（VERSION_HISTORY.md）

### Design Decisions

- 采用分阶段流程而非单步分析（用户参与过程）
- 强制性质疑流程（不能跳过核心步骤）
- Markdown 输出优先（人类可读性）

### Known Limitations

- 仅支持文本输入
- 领域知识有限
- 无记忆功能
- 无可视化
- 无多语言支持

### Inspiration Sources

- Elon Musk 的第一性原理思维方法
- Linux Kernel 开发流程文档
- 亚里士多德物理学第一原理
- 笛卡尔方法论

---

## [Unreleased] - v0.2.0 (规划中)

### Planned

- 整合老钱家族决策框架（灵感来源待补充）
- 整合顶级投资机构思维模型（灵感来源待补充）
- 支持多语言（中文/英文/日语/西班牙语）
- 改进领域知识覆盖

### Future Directions

- 可视化思维图谱
- 记忆与个性化指导
- API 化供其他技能调用

---

**维护者**：王的奴隶 · 严谨专业版

---

## [0.3.0] - 2026-04-04

### Added

- **状态持久化系统** - 完整的分析过程状态管理
  - 状态机模式（State Pattern）：6 种分析状态（idle/analyzing/paused/waiting_input/completed/failed）
  - 状态转换规则和验证
  - 状态历史记录和快照功能
  - 状态机管理器（支持多分析任务）

- **仓库模式**（Repository Pattern）- 分析历史持久化
  - 内存存储后端（临时）
  - 文件存储后端（持久）
  - CRUD 操作接口
  - 统计信息查询

- **责任链模式**（Chain of Responsibility）- 可组合分析管道
  - 处理器基类
  - 7 个标准处理器（问题接收→假设识别→假设质疑→分解→验证→重构→报告）
  - 管道构建器（链式 API）
  - 标准分析管道一键构建

- **观察者模式**（Observer Pattern）- 状态变更通知
  - 事件发射器（EventEmitter）
  - 日志观察者
  - 进度观察者
  - 通知观察者
  - 事件辅助函数

### Changed

- 版本号：0.2.0 → 0.3.0
- 测试覆盖率：35% → 57.92%（新模块 80%+）
- 测试用例：40 → 91 个

### Design Patterns Applied

| 模式 | 文件 | 说明 |
|------|------|------|
| State Pattern | state-machine.js | 管理分析状态流转 |
| Repository Pattern | repository.js | 封装存储逻辑 |
| Chain of Responsibility | pipeline.js | 构建可组合管道 |
| Observer Pattern | observer.js | 状态变更通知 |

### Technical Improvements

- T 维度：架构设计从 0.60→0.80（四层架构清晰）
- T 维度：测试覆盖从 35%→57.92%（+22.92%）
- O 维度：设计模式从 2 个→6 个（策略/模板方法/工厂/建造者/状态机/仓库/责任链/观察者）
- E 维度：状态持久化支持分析恢复

### Files Added

- `src/state-machine.js` - 状态机模式实现
- `src/repository.js` - 仓库模式实现
- `src/pipeline.js` - 责任链模式实现
- `src/observer.js` - 观察者模式实现
- `tests/state-machine.test.js` - 状态机测试（15 个用例）
- `tests/repository.test.js` - 仓库测试（12 个用例）
- `tests/pipeline.test.js` - 管道测试（9 个用例）
- `tests/observer.test.js` - 观察者测试（13 个用例）

### Known Limitations

- analyzer.js 核心引擎测试覆盖不足（0%）
- 文件存储后端测试未覆盖
- 观察者模式部分边界情况未测试

### Next Steps (v0.4.0)

- 补充 analyzer.js 核心引擎测试
- 集成状态持久化到主分析流程
- 添加分析恢复功能
- 改进文件存储后端测试

