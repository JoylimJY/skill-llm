# 更新日志 / Changelog

---

## v2.1.1 (2026-03-24)

### 🐛 Bug Fixes

- 修复：`can_upgrade` 返回值逻辑错误（已是开发者却返回 True）
  - 修复后端 `check_upgrade` 逻辑：已是开发者时正确返回 `can_upgrade: False`
  - 避免前端收到 True 后继续调用升级接口，触发 400 报错

### ✨ New Features

- **轻量降级模式**：Ollama 不可用时自动降级为 BM25-only 检索
  - `_detect_ollama()` 启动时探测 Ollama 可用性
  - `bm25_only_search()` 无向量依赖的纯关键词搜索
  - 搜索结果标记 `search_type: "bm25_only"`

### 🔧 Improvements

- **数据目录与代码完全分离**：
  - 数据迁移到 `~/.openclaw/memory-workflow-data/`
  - `hot_sessions.json`、`memory_state.json`、`memories/` 全部移出 skill 目录
  - 打包分发更安全，更新 skill 不覆盖用户数据

- **错误处理增强**：
  - Rerank 服务不可用时静默降级，不中断搜索流程
  - MiniMax API 超限（429）时打印警告但不阻断
  - Ollama 连接失败时明确提示降级信息

- **文档完善**：
  - SKILL.md 重写，新增局限性说明
  - RAGAs 评估脚本标注"开发中"
  - 新增中英双语 README

---

## v2.1.0 (2026-03-23)

### ✨ New Features

- 数据目录独立：`MEMORY_WORKFLOW_DATA` 环境变量支持自定义数据路径
- 两阶段搜索精排：Stage 1 RRF + Rerank → 取前1/3 → Stage 2 二次 RRF 融合
- Query Expansion：HyDE + Query Rewriting 多查询变体扩展

### 🔧 Improvements

- Milvus 降级为可选依赖，不配置则默认文件系统存储
- SKILL.md 外部依赖明确标注必须/推荐/可选

---

## v2.0.0 (2026-03-22)

- 完全重构，移除强制 Milvus 依赖
- 文件系统存储 + 后台自动存储线程
- 移除 `rag_integration.py` 依赖
- 简化安装，开箱即用
