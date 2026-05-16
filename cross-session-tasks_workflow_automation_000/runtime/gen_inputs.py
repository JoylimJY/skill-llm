import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── 1. Create the core ~/.openclaw/workspace-like structure inside /workspace ──
openclaw_ws = workspace / ".openclaw" / "workspace"
openclaw_ws.mkdir(parents=True, exist_ok=True)

projects_dir = openclaw_ws / "projects"
projects_dir.mkdir(parents=True, exist_ok=True)

archive_dir = projects_dir / "_archive"
archive_dir.mkdir(parents=True, exist_ok=True)

# ── 2. ACTIVE-TASKS.md (messy, realistic, contains 3 tasks) ──
active_tasks_content = """# ACTIVE TASKS

| 任务名 | 状态 | 负责人 | 上次更新 | 截止日期 | 下一步 |
|--------|------|--------|----------|----------|--------|
| api-redesign | ✅ 完成 | @alice | 2024-06-10 | 2024-06-15 | 已全部完成，待归档 |
| data-pipeline-migration | 🔄 进行中 | @bob | 2024-06-01 | 2024-07-30 | 尚未创建 progress.md，需初始化 |
| infra-monitoring-setup | 🔄 进行中 | @carol | 2024-05-28 | 2024-07-01 | 配置 Prometheus alerting rules |

_最后整理时间：2024-06-10_
"""
(openclaw_ws / "ACTIVE-TASKS.md").write_text(active_tasks_content, encoding="utf-8")

# ── 3. CLOSED-TASKS.md (exists but has only one old entry) ──
closed_tasks_content = """# CLOSED TASKS

| 任务名 | 完成日期 | 负责人 | 备注 |
|--------|----------|--------|------|
| legacy-auth-refactor | 2024-04-20 | @alice | 顺利完成，迁移至 OAuth2 |

"""
(openclaw_ws / "CLOSED-TASKS.md").write_text(closed_tasks_content, encoding="utf-8")

# ── 4. api-redesign project folder (the COMPLETED task — needs archival) ──
api_project = projects_dir / "api-redesign"
api_project.mkdir(parents=True, exist_ok=True)

api_progress_content = """# api-redesign progress

## 基本信息
- 项目名：API Redesign v2
- 编号：PROJ-042
- 截止日期：2024-06-15
- 相关文件：/workspace/src/api/v2/

## 进度检查清单
- [x] 分析现有 API 结构
- [x] 设计新的 REST 端点
- [x] 实现核心端点
- [x] 撰写 OpenAPI 规范文档
- [x] 通过所有集成测试
- [x] 部署到 staging 环境
- [x] 生产发布

## 关键决策与规则
- 使用 REST + JSON，不采用 GraphQL
- 版本号放在 URL path 中（/v2/）
- 所有错误返回 RFC 7807 格式

## 文件位置
- `/workspace/src/api/v2/` — 主要源码
- `/workspace/docs/api-v2-spec.yaml` — OpenAPI 规范
- `/workspace/tests/integration/api_v2/` — 集成测试

## 下次开始时需要知道的
- 项目已全部完成并发布，无遗留问题
- 旧 v1 API 将在 2024-09-01 下线
- 监控告警已配置在 Grafana dashboard
"""
(api_project / "progress.md").write_text(api_progress_content, encoding="utf-8")

# A couple of extra files in api-redesign project
(api_project / "notes.md").write_text("# Quick notes\n- Remember to update changelog\n", encoding="utf-8")
(api_project / "review-checklist.txt").write_text("[ ] Security review\n[x] Performance review\n[x] Code review\n", encoding="utf-8")

# ── 5. infra-monitoring-setup project folder (ongoing, distractor) ──
infra_project = projects_dir / "infra-monitoring-setup"
infra_project.mkdir(parents=True, exist_ok=True)

infra_progress_content = """# infra-monitoring-setup progress

## 基本信息
- 项目名：Infrastructure Monitoring Setup
- 编号：PROJ-044
- 截止日期：2024-07-01
- 相关文件：/workspace/infra/monitoring/

## 进度检查清单
- [x] 安装 Prometheus
- [x] 配置基础 metrics scraping
- [ ] 配置 alerting rules
- [ ] 接入 PagerDuty
- [ ] 文档整理

## 关键决策与规则
- 使用 Prometheus + Grafana 技术栈
- AlertManager 负责通知路由

## 文件位置
- `/workspace/infra/monitoring/prometheus.yml`
- `/workspace/infra/monitoring/alerts/`

## 下次开始时需要知道的
- 下一步是配置 alerting rules，模板在 /infra/monitoring/alerts/template.yml
- PagerDuty integration key 存在 vault 中
- Grafana 默认端口已改为 3001
- Carol 负责这个任务，找她要最新的 dashboard JSON
"""
(infra_project / "progress.md").write_text(infra_progress_content, encoding="utf-8")

# ── 6. Distractor files to make the workspace realistic ──

# Source code directories
src_dirs = [
    workspace / "src" / "api" / "v1",
    workspace / "src" / "api" / "v2",
    workspace / "src" / "pipeline" / "connectors",
    workspace / "src" / "pipeline" / "transformers",
    workspace / "src" / "common" / "utils",
    workspace / "infra" / "monitoring" / "alerts",
    workspace / "infra" / "terraform" / "modules",
    workspace / "tests" / "integration" / "api_v2",
    workspace / "tests" / "unit" / "pipeline",
    workspace / "docs" / "architecture",
]
for d in src_dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor source files
(workspace / "src" / "api" / "v2" / "endpoints.py").write_text(
    "# API v2 endpoints\ndef list_users(): pass\ndef get_user(id): pass\n", encoding="utf-8")
(workspace / "src" / "api" / "v1" / "endpoints.py").write_text(
    "# Legacy API v1 - DEPRECATED\ndef list_users(): pass\n", encoding="utf-8")
(workspace / "src" / "pipeline" / "connectors" / "postgres_connector.py").write_text(
    "# PostgreSQL connector\nclass PGConnector:\n    pass\n", encoding="utf-8")
(workspace / "src" / "pipeline" / "connectors" / "kafka_connector.py").write_text(
    "# Kafka connector - WIP\nclass KafkaConnector:\n    pass\n", encoding="utf-8")
(workspace / "src" / "pipeline" / "transformers" / "normalize.py").write_text(
    "# Data normalization transformer\ndef normalize(df): return df\n", encoding="utf-8")
(workspace / "src" / "common" / "utils" / "logging.py").write_text(
    "import logging\nlogger = logging.getLogger(__name__)\n", encoding="utf-8")
(workspace / "infra" / "monitoring" / "prometheus.yml").write_text(
    "global:\n  scrape_interval: 15s\nscrape_configs:\n  - job_name: 'api'\n", encoding="utf-8")
(workspace / "infra" / "monitoring" / "alerts" / "template.yml").write_text(
    "groups:\n  - name: api_alerts\n    rules: []\n", encoding="utf-8")
(workspace / "infra" / "terraform" / "modules" / "vpc.tf").write_text(
    'resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"\n}\n', encoding="utf-8")
(workspace / "tests" / "integration" / "api_v2" / "test_endpoints.py").write_text(
    "def test_list_users(): assert True\ndef test_get_user(): assert True\n", encoding="utf-8")
(workspace / "tests" / "unit" / "pipeline" / "test_normalize.py").write_text(
    "def test_normalize(): assert True\n", encoding="utf-8")
(workspace / "docs" / "architecture" / "system-design.md").write_text(
    "# System Design\n## Overview\nMicroservices architecture with event-driven pipeline.\n", encoding="utf-8")
(workspace / "docs" / "api-v2-spec.yaml").write_text(
    "openapi: 3.0.0\ninfo:\n  title: API v2\n  version: 2.0.0\npaths: {}\n", encoding="utf-8")

# A raw migration notes file (context for data-pipeline-migration task)
migration_notes = workspace / "data-pipeline-migration-notes.txt"
migration_notes.write_text("""Data Pipeline Migration Project Notes
=====================================
Task owner: @bob
Project ID: PROJ-045
Deadline: 2024-07-30
Ticket: https://jira.internal/PROJ-045

Current state (as of 2024-06-01):
- Legacy ETL pipeline runs on on-prem servers using Python 2.7
- Target: migrate to cloud-native Airflow on GKE
- Estimated effort: 8 weeks

Steps planned:
1. Audit existing DAGs and dependencies
2. Set up Airflow on GKE (dev environment)
3. Port DAGs to Python 3.11
4. Validate data consistency (sample testing)
5. Shadow mode: run both pipelines in parallel
6. Cutover: switch production traffic
7. Decommission legacy servers

Completed so far:
- Step 1 DONE: 47 DAGs audited, 12 need rewrite
- Step 2 DONE: Dev Airflow running on GKE cluster
- Step 3 IN PROGRESS: 8 of 12 complex DAGs ported

Key decisions made:
- Use Airflow 2.7 (not Airflow 3.x, too unstable)
- All DAGs must pass data validation before cutover
- Legacy pipeline stays live until 30-day shadow period completes
- Rollback plan: re-route traffic back to on-prem if error rate > 0.1%

Related files:
- /workspace/src/pipeline/connectors/
- /workspace/src/pipeline/transformers/
- /workspace/infra/terraform/modules/

Blockers:
- 4 remaining complex DAGs need Bob's review
- PagerDuty alerting integration not yet done for new pipeline
""", encoding="utf-8")

# A changelog file (distractor)
(workspace / "CHANGELOG.md").write_text(
    "# Changelog\n## 2024-06-10\n- Released API v2\n## 2024-05-01\n- Initial pipeline connector\n", encoding="utf-8")

print("Workspace generated successfully.")
print(f"Structure created under: {workspace}")