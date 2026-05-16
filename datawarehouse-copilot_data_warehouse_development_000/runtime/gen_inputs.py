import os
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "resources/conventions",
    "resources",
    "data/raw/orders",
    "data/raw/users",
    "data/processed",
    "etl/scripts",
    "etl/configs",
    "ddl/ods",
    "ddl/dwd",
    "docs/legacy",
    "docs/meetings",
    "scheduler/jobs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── SKILL.md ────────────────────────────────────────────────────────────────
(WORKSPACE / "SKILL.md").write_text(textwrap.dedent("""\
    ---
    name: datawarehouse-copilot
    description: "基于 SpecKit SDD（Spec-Driven Development）方法论的数仓开发 Agent 技能。将自然语言需求经多阶段澄清与收敛，产出符合规范的 Spec 文档、执行计划及可直接落地的 DDL/ETL/调度配置代码。支持自定义平台技术栈和自定义项目公约。"
    ---

    # DataWarehouse Copilot

    基于 SDD（Spec-Driven Development）方法论，为数仓领域量身定制的规格驱动开发技能。

    ## 目录
    - [七阶段工作流](#七阶段工作流)
    - [产物规范](#产物规范)
    - [行为准则](#行为准则)
    - [资源文件索引](#资源文件索引)

    ---

    ## 七阶段工作流

    ```
    用户需求（自然语言）
         ↓
    [Phase 0] 需求澄清        ← 首先确认角色；主动提问消除模糊点
         ↓
    [Phase 1] 元数据收集      ← 五种采集方式（见 metadata-config.md）
         ↓
    [Phase 2] 生成 Spec       ← 输出 spec.md（做什么）
         ↓
    [Phase 3] ⏸ 用户确认 Spec ← ⛔ MUST：等待用户明确 OK
         ↓
    [Phase 4] 生成 Plan       ← 输出 plan.md（怎么做）
         ↓
    [Phase 5] ⏸ 用户确认 Plan ← ⛔ MUST：等待用户明确 OK
         ↓
    [Phase 6] 生成 Task       ← 输出 task.md（可执行代码）
    ```

    **角色说明**（Phase 0 首要任务）：

    | 角色 | 输出产物 |
    |------|----------|
    | 📋 **产品/业务同学** | spec.md + plan.md |
    | 🔧 **数仓开发同学** | spec.md + plan.md + task.md |

    角色不明确时直接询问，不默认。

    各阶段详细进入/退出条件及操作要点见 `resources/workflow-stages.md`（必读）。

    > **三层文档职责**：spec = 做什么（业务视角），plan = 怎么做（技术方案），task = 可执行落地（完整代码）。

    ---

    ## 产物规范

    | 产物 | 定位 | 模板 | 适用角色 |
    |------|------|------|----------|
    | spec.md | 业务需求规格，业务同学可直接阅读确认 | `resources/spec-template.md` | 所有角色 |
    | plan.md | 技术方案层，是 task 的直接输入 | `resources/plan-template.md` | 所有角色 |
    | task.md | 可执行落地，含完整代码、异常处理与验收标准（DoD） | `resources/task-template.md` | 仅数仓开发同学 |

    ---

    ## 行为准则

    ⛔ **MUST（不可违反）**：
    - **阶段顺序不可跳过**：必须按 Spec → Plan → Task 顺序推进，不可乱序
    - **确认点不可绕过**：Phase 3 和 Phase 5 必须收到用户明确回复才能继续，不可自行推断用户已同意；Spec 变更回到 Phase 2，Plan 变更回到 Phase 4

    **一般准则**：
    - **遇到模糊主动问**：需求或字段语义不清时直接询问，不猜测、不假设
    - **代码可追溯**：所有 DDL/ETL 必须能追溯到 Spec 中的对应条目
    - **规范缺失时主动询问并更新**：公约文件未明确记录的能力或规范，必须询问用户确认，不得臆想；确认后补充到对应公约文件（平台能力 → `platform-conventions.md`，团队约定 → `project-conventions.md`）

    ---

    ## 资源文件索引

    - `resources/workflow-stages.md` — 各阶段详细进入/退出条件与操作要点（**必读**）
    - `resources/spec-template.md` — spec.md 模板
    - `resources/plan-template.md` — plan.md 模板
    - `resources/task-template.md` — task.md 模板
    - `resources/conventions/metadata-config.md` — 元数据五种采集方式完整配置
    - `resources/conventions/project-conventions.md` — 团队公约（代码生成前必须查阅）
    - `resources/conventions/platform-conventions.md` — 平台能力与配置规范（代码生成前必须查阅）
"""))

# ── resources/workflow-stages.md ────────────────────────────────────────────
(WORKSPACE / "resources/workflow-stages.md").write_text(textwrap.dedent("""\
    # Workflow Stages — Detailed Entry/Exit Conditions

    ## Phase 0 — 需求澄清
    **进入条件**：收到任意用户需求。
    **操作要点**：
    1. 首先询问并确认角色（产品/业务同学 or 数仓开发同学）。
    2. 询问业务背景：数据来源、核心业务事件、下游消费方。
    3. 询问数据量级与更新频率。
    **退出条件**：角色已确认，核心需求无重大歧义。

    ## Phase 1 — 元数据收集
    **进入条件**：Phase 0 完成。
    **操作要点**：从 metadata-config.md 选择合适采集方式；本项目采用 **方式三：用户提供字段清单**。
    **退出条件**：字段清单已确认，数据类型与业务含义明确。

    ## Phase 2 — 生成 Spec
    **进入条件**：Phase 1 完成。
    **操作要点**：严格按 `spec-template.md` 填充，所有字段来自 Phase 1 产物。
    **退出条件**：spec.md 产出，等待用户确认。

    ## Phase 3 — 用户确认 Spec
    **进入条件**：spec.md 已产出。
    ⛔ 必须等待用户明确回复「OK」或等价确认语，方可进入 Phase 4。

    ## Phase 4 — 生成 Plan
    **进入条件**：Phase 3 用户已确认。
    **操作要点**：严格按 `plan-template.md` 填充；必须引用 spec.md 中的字段编号。
    **退出条件**：plan.md 产出，等待用户确认。

    ## Phase 5 — 用户确认 Plan
    **进入条件**：plan.md 已产出。
    ⛔ 必须等待用户明确回复「OK」或等价确认语，方可进入 Phase 6。

    ## Phase 6 — 生成 Task
    **进入条件**：Phase 5 用户已确认。
    **操作要点**：严格按 `task-template.md` 填充；DDL/ETL 每段代码末尾必须注释 `-- Spec: §<编号>`；调度配置必须使用平台 DSL（见 platform-conventions.md）。
    **退出条件**：task.md 产出，所有 DoD 项可验证。
"""))

# ── resources/spec-template.md ──────────────────────────────────────────────
(WORKSPACE / "resources/spec-template.md").write_text(textwrap.dedent("""\
    # Spec: <需求标题>

    ## 1. 背景与目标
    > 描述业务背景，说明为什么需要这张表/这条链路。

    ## 2. 数据范围
    | 属性 | 值 |
    |------|----|
    | 数据源 | <来源系统> |
    | 目标层 | <ODS/DWD/DWS/ADS> |
    | 更新策略 | <全量/增量/Upsert> |
    | 业务日期字段 | <字段名> |
    | 数据延迟 SLA | <小时数> |

    ## 3. 字段规格
    | 编号 | 字段名 | 类型 | 业务含义 | 是否分区 | 备注 |
    |------|--------|------|----------|----------|------|
    | §3.1 | ... | ... | ... | 否 | |
    | §3.2 | ... | ... | ... | 是 | 分区字段 |

    ## 4. 业务规则
    - BR-01: <规则描述>
    - BR-02: <规则描述>

    ## 5. 下游消费方
    | 消费方 | 用途 |
    |--------|------|
    | <系统/团队> | <用途描述> |

    ## 6. 验收标准（业务视角）
    - AC-01: <可验收的业务断言>
    - AC-02: <可验收的业务断言>
"""))

# ── resources/plan-template.md ──────────────────────────────────────────────
(WORKSPACE / "resources/plan-template.md").write_text(textwrap.dedent("""\
    # Plan: <需求标题>

    ## 1. 技术选型
    | 组件 | 选型 | 说明 |
    |------|------|------|
    | 存储格式 | <format> | |
    | 计算引擎 | <engine> | |
    | 调度系统 | <scheduler> | |

    ## 2. 表设计
    ### 2.1 目标表
    - 表名：`<prefix>_<name>`（遵循 project-conventions.md §命名规范）
    - 分区策略：按 `<分区字段>` 分区
    - 生命周期：<天数> 天

    ### 2.2 字段映射
    | Spec 编号 | 源字段 | 目标字段 | 转换逻辑 |
    |-----------|--------|----------|----------|
    | §3.1 | ... | ... | 直接映射 |

    ## 3. ETL 设计
    - 抽取方式：<方式>
    - 增量标识字段：<字段>
    - 异常处理策略：<策略>

    ## 4. 调度设计
    | 属性 | 值 |
    |------|----|
    | 调度周期 | <daily/hourly> |
    | 触发时间 | <cron 或平台 DSL> |
    | 依赖任务 | <上游任务名> |
    | 超时阈值 | <分钟> |

    ## 5. 风险与假设
    - RISK-01: <风险描述>
    - ASSUME-01: <假设描述>
"""))

# ── resources/task-template.md ──────────────────────────────────────────────
(WORKSPACE / "resources/task-template.md").write_text(textwrap.dedent("""\
    # Task: <需求标题>

    ## 1. DDL

    ```sql
    -- ============================================================
    -- 表名: <table_name>
    -- 负责人: <owner>
    -- 创建时间: <YYYY-MM-DD>
    -- ============================================================
    <DDL语句>
    -- Spec: §<编号>
    ```

    ## 2. ETL 脚本

    ```sql
    -- ============================================================
    -- ETL: <table_name>  加载逻辑
    -- ============================================================
    <INSERT/MERGE语句>
    -- Spec: §<编号>
    ```

    ## 3. 调度配置

    ```yaml
    # 使用平台 DSL（见 platform-conventions.md §调度 DSL）
    job:
      name: <job_name>
      schedule: <平台DSL表达式>
      timeout_minutes: <超时>
      on_failure: <失败策略>
      tasks:
        - name: load_ods
          type: sql
          file: <etl文件路径>
    ```

    ## 4. 异常处理

    - EX-01: <异常场景> → <处理方式>
    - EX-02: <异常场景> → <处理方式>

    ## 5. DoD（Definition of Done）

    - [ ] DDL 可在目标环境执行无报错
    - [ ] ETL 空跑（dry-run）通过
    - [ ] 调度配置通过平台 Lint 检查
    - [ ] 数据量与源系统误差 < 0.1%
    - [ ] 所有 AC（见 spec.md §6）均已验证
"""))

# ── resources/conventions/metadata-config.md ────────────────────────────────
(WORKSPACE / "resources/conventions/metadata-config.md").write_text(textwrap.dedent("""\
    # 元数据采集方式

    ## 方式一：连接元数据库（JDBC）
    适合：有权访问源系统 catalog 的场景。
    配置键：`metadata.source=jdbc`

    ## 方式二：解析 DDL 文件
    适合：已有 DDL 文件但无直连权限。
    配置键：`metadata.source=ddl_file`

    ## 方式三：用户提供字段清单
    适合：快速启动，字段由人工维护。
    配置键：`metadata.source=manual`
    格式要求：Markdown 表格，列顺序固定为 `字段名 | 类型 | 业务含义`。

    ## 方式四：接口文档解析（OpenAPI/Avro）
    适合：数据来源为微服务接口。
    配置键：`metadata.source=openapi`

    ## 方式五：血缘系统导出
    适合：已有数据血缘平台。
    配置键：`metadata.source=lineage_export`
"""))

# ── resources/conventions/project-conventions.md ───────────────────────────
(WORKSPACE / "resources/conventions/project-conventions.md").write_text(textwrap.dedent("""\
    # 项目公约（Project Conventions）

    ## 命名规范

    ### 表命名
    - ODS 层：`ods_<source_system>_<entity>_<load_mode>`
      - `load_mode` 取值：`full`（全量）、`inc`（增量）
      - 示例：`ods_mall_order_event_inc`
    - 字母全部小写，单词间用下划线分隔，不超过 64 字符。

    ### 字段命名
    - 分区字段固定命名为 `pt_date`，类型 `STRING`，格式 `YYYY-MM-DD`。
    - 创建时间字段统一命名为 `gmt_create`，修改时间字段统一命名为 `gmt_modified`。
    - 逻辑删除字段统一命名为 `is_deleted`，类型 `TINYINT`，0=正常 1=删除。

    ### 任务命名
    - 调度任务命名格式：`<layer>__<table_name>__<period>`
      - 示例：`ods__ods_mall_order_event_inc__daily`

    ## 注释规范
    - 每张表的 DDL 必须包含表级注释（`COMMENT`）和字段级注释。
    - 注释语言：中文。

    ## 生命周期规范
    - ODS 层默认生命周期：180 天。
    - DWD 层默认生命周期：365 天。

    ## 代码可追溯规范
    - DDL 与 ETL 中每个逻辑块末尾必须追加注释 `-- Spec: §<编号>`，编号对应 spec.md §3 字段规格表中的编号。
"""))

# ── resources/conventions/platform-conventions.md ──────────────────────────
(WORKSPACE / "resources/conventions/platform-conventions.md").write_text(textwrap.dedent("""\
    # 平台能力与配置规范（Platform Conventions）

    ## 计算引擎
    - 引擎：MaxCompute（ODPS）
    - SQL 方言：ODPS SQL（兼容 HiveQL，但分区语法使用 `PARTITIONED BY`，不支持 `PARTITION BY`）

    ## 存储格式
    - ODS 层默认存储格式：ORC
    - 必须在 DDL 中声明：`STORED AS ORC`
    - 必须追加表属性：`TBLPROPERTIES('orc.compress'='SNAPPY')`

    ## 调度系统 DSL
    本平台使用自研调度系统 **FlowX**，调度配置必须使用以下 DSL（YAML 格式）：

    ```yaml
    job:
      name: <任务名>
      schedule:
        type: cron_daily          # 固定值，日调度任务必须使用 cron_daily
        start_time: "HH:MM"       # 24小时制，每天触发时间
      timeout_minutes: <整数>
      on_failure: alert_and_retry # 固定值，ODS 层任务失败策略
      retry_times: 3              # ODS 层固定为 3 次
      tasks:
        - name: <步骤名>
          type: odps_sql           # MaxCompute 任务固定使用 odps_sql
          file: <相对路径>
          parameters:
            pt_date: "${bizdate}"  # 分区参数固定写法
    ```

    ## 数据血缘声明
    - 每个 ETL 任务必须在脚本头部声明血缘注释块：
    ```sql
    -- @lineage
    -- source: <源表名>
    -- target: <目标表名>
    -- @end_lineage
    ```

    ## 权限模型
    - ODS 表默认授权给角色 `role_dw_read`（只读）和 `role_dw_write`（写入）。
    - DDL 末尾必须包含授权语句：
    ```sql
    GRANT SELECT ON TABLE <table_name> TO ROLE role_dw_read;
    GRANT INSERT ON TABLE <table_name> TO ROLE role_dw_write;
    ```
"""))

# ── distractor files ─────────────────────────────────────────────────────────

# legacy DDL (wrong naming, wrong format — distractors)
(WORKSPACE / "ddl/ods/old_order_tbl.sql").write_text(textwrap.dedent("""\
    -- LEGACY: do not use
    CREATE TABLE tbl_order_old (
      order_id BIGINT,
      status VARCHAR(32),
      create_time TIMESTAMP
    ) STORED AS TEXTFILE;
"""))

(WORKSPACE / "ddl/dwd/dwd_order_detail.sql").write_text(textwrap.dedent("""\
    -- PLACEHOLDER — not finalized
    CREATE TABLE dwd_order_detail (
      order_id BIGINT COMMENT '订单ID'
    );
"""))

# old ETL scripts with wrong patterns
(WORKSPACE / "etl/scripts/load_order_old.sql").write_text(textwrap.dedent("""\
    INSERT INTO tbl_order_old
    SELECT order_id, status, create_time FROM source.orders;
    -- NOTE: deprecated, uses wrong table name
"""))

(WORKSPACE / "etl/configs/job_order_old.yaml").write_text(textwrap.dedent("""\
    # OLD FORMAT — not FlowX DSL
    job_name: load_order
    cron: "0 2 * * *"
    engine: hive
"""))

# data samples
(WORKSPACE / "data/raw/orders/sample_2024_01.json").write_text(textwrap.dedent("""\
    {"order_id":10001,"user_id":501,"event_type":"PLACED","amount":199.90,"currency":"CNY","event_time":"2024-01-15T10:23:45Z","order_status":"PENDING","is_deleted":0}
    {"order_id":10002,"user_id":502,"event_type":"PAID","amount":89.00,"currency":"CNY","event_time":"2024-01-15T11:00:00Z","order_status":"PAID","is_deleted":0}
"""))

(WORKSPACE / "data/raw/orders/sample_2024_02.json").write_text(textwrap.dedent("""\
    {"order_id":10003,"user_id":503,"event_type":"CANCELLED","amount":0.00,"currency":"CNY","event_time":"2024-02-01T08:00:00Z","order_status":"CANCELLED","is_deleted":1}
"""))

(WORKSPACE / "data/raw/users/user_dim_snapshot.csv").write_text(
    "user_id,username,city,tier\n501,alice,Beijing,Gold\n502,bob,Shanghai,Silver\n503,carol,Guangzhou,Bronze\n"
)

# meeting notes (distractor)
(WORKSPACE / "docs/meetings/kickoff_notes_2024.txt").write_text(textwrap.dedent("""\
    2024-01-10 Kickoff Meeting Notes
    - Team agreed on MaxCompute as compute engine
    - ODS layer to be built first
    - Daily scheduling, T+1
    - Downstream: BI dashboard team, risk control team
"""))

(WORKSPACE / "docs/legacy/old_design_v1.md").write_text(textwrap.dedent("""\
    # OLD DESIGN DOC (v1) — SUPERSEDED
    This design is outdated. Do not use.
    Table: order_events_v1
    Partition: dt (wrong naming)
    Format: Parquet (wrong for current platform)
"""))

# scheduler placeholder
(WORKSPACE / "scheduler/jobs/placeholder.yaml").write_text("# no jobs defined yet\n")

# a red-herring conventions file in the wrong place
(WORKSPACE / "docs/legacy/fake_conventions.md").write_text(textwrap.dedent("""\
    # FAKE CONVENTIONS (archived, do not use)
    Table prefix: tbl_
    Partition field: dt
    Format: Parquet
    Scheduler: Airflow
"""))

print("Workspace generated successfully.")
print("Files created:")
import subprocess
subprocess.run(["find", str(WORKSPACE), "-type", "f"], check=True)