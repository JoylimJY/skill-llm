import os
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# ── 1. Create the bundled English template (assets/project-template-en/)
template_en = WORKSPACE / "assets" / "project-template-en"
template_en.mkdir(parents=True, exist_ok=True)

(template_en / "README.md").write_text(textwrap.dedent("""\
    # Project: <project-name>

    ## Goal
    <!-- One sentence: what must this project achieve? -->

    ## Scope
    <!-- What is in and out of scope? -->

    ## Success Criteria
    <!-- How will we know it is done? -->

    ## Key Entry Points
    <!-- Important files, services, or systems to understand first -->
"""))

(template_en / "STATUS.md").write_text(textwrap.dedent("""\
    # Status

    **Updated:** <date>

    ## Current Goal
    <!-- What must happen right now? -->

    ## Current Judgment
    <!-- What seems true and why? -->

    ## Progress
    <!-- What has been done? -->

    ## Blockers
    <!-- What is in the way? -->

    ## Next Action
    <!-- The exact next step -->
"""))

(template_en / "TODO.md").write_text(textwrap.dedent("""\
    # TODO

    ## High Priority
    - [ ] <task>

    ## Medium Priority
    - [ ] <task>

    ## Low Priority / Nice to Have
    - [ ] <task>
"""))

(template_en / "DECISIONS.md").write_text(textwrap.dedent("""\
    # Decisions

    ## <YYYY-MM-DD> — <Decision Title>
    **Context:** <!-- Why did this decision need to be made? -->
    **Decision:** <!-- What was decided? -->
    **Tradeoffs:** <!-- What was accepted or rejected? -->
"""))

(template_en / "LOG.md").write_text(textwrap.dedent("""\
    # Work Log

    ## <YYYY-MM-DD>
    - <!-- What was done, discovered, or observed? -->
"""))

(template_en / "REFERENCES.md").write_text(textwrap.dedent("""\
    # References

    ## Key Files
    - <!-- path/to/file — description -->

    ## Commands
    - <!-- command — what it does -->

    ## Links
    - <!-- URL — description -->
"""))

(template_en / "HANDOFF.md").write_text(textwrap.dedent("""\
    # Handoff

    **Checkpoint Date:** <date>

    ## What This Project Is
    <!-- One sentence summary -->

    ## Current State
    <!-- What is done, what is not -->

    ## Next Action
    <!-- The exact next step to take when resuming -->

    ## First File to Read
    <!-- Which file should be opened first when resuming? -->

    ## Open Loops
    <!-- Unresolved questions or risks -->
"""))

# ── 2. Create Chinese template (assets/project-template/) as distractor
template_zh = WORKSPACE / "assets" / "project-template"
template_zh.mkdir(parents=True, exist_ok=True)

(template_zh / "README.md").write_text("# 项目：<项目名>\n\n## 目标\n<!-- 一句话说明项目要实现什么 -->\n")
(template_zh / "STATUS.md").write_text("# 状态\n\n**更新：** <日期>\n\n## 当前目标\n<!-- 现在必须做什么 -->\n")
(template_zh / "TODO.md").write_text("# 待办事项\n\n## 高优先级\n- [ ] <任务>\n")
(template_zh / "DECISIONS.md").write_text("# 决策记录\n\n## <YYYY-MM-DD> — <决策标题>\n")
(template_zh / "LOG.md").write_text("# 工作日志\n\n## <YYYY-MM-DD>\n- <!-- 完成、发现或观察到的内容 -->\n")
(template_zh / "REFERENCES.md").write_text("# 参考资料\n\n## 关键文件\n- <!-- 路径 — 描述 -->\n")
(template_zh / "HANDOFF.md").write_text("# 交接\n\n**检查点日期：** <日期>\n\n## 下一步行动\n<!-- 恢复时要做的具体下一步 -->\n")

# ── 3. Distractor files: simulate an existing messy engineering repo
distractor_dirs = [
    WORKSPACE / "infra" / "terraform" / "modules" / "rds",
    WORKSPACE / "infra" / "terraform" / "modules" / "vpc",
    WORKSPACE / "infra" / "ansible" / "playbooks",
    WORKSPACE / "scripts" / "migrations" / "pg12",
    WORKSPACE / "scripts" / "migrations" / "pg16",
    WORKSPACE / "scripts" / "monitoring",
    WORKSPACE / "docs" / "architecture",
    WORKSPACE / "docs" / "runbooks",
    WORKSPACE / "ci" / "pipelines",
    WORKSPACE / "tests" / "integration",
]

for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor file contents
distractors = {
    WORKSPACE / "infra" / "terraform" / "modules" / "rds" / "main.tf":
        'resource "aws_db_instance" "pg12" {\n  engine         = "postgres"\n  engine_version = "12.14"\n  instance_class = "db.r6g.xlarge"\n}\n',
    WORKSPACE / "infra" / "terraform" / "modules" / "rds" / "variables.tf":
        'variable "db_password" {\n  description = "Master DB password"\n  type        = string\n  sensitive   = true\n}\n',
    WORKSPACE / "infra" / "terraform" / "modules" / "vpc" / "main.tf":
        'resource "aws_vpc" "main" {\n  cidr_block = "10.0.0.0/16"\n}\n',
    WORKSPACE / "infra" / "ansible" / "playbooks" / "pg_upgrade.yml":
        '---\n- name: Upgrade PostgreSQL\n  hosts: db_servers\n  tasks:\n    - name: Stop old service\n      service:\n        name: postgresql-12\n        state: stopped\n',
    WORKSPACE / "scripts" / "migrations" / "pg12" / "schema_dump.sql":
        '-- pg12 schema dump 2024-01-15\nCREATE TABLE accounts (\n  id BIGSERIAL PRIMARY KEY,\n  balance NUMERIC(18,4) NOT NULL\n);\n',
    WORKSPACE / "scripts" / "migrations" / "pg16" / "schema_v2.sql":
        '-- Target schema for pg16\nCREATE TABLE accounts (\n  id BIGSERIAL PRIMARY KEY,\n  balance NUMERIC(18,4) NOT NULL,\n  created_at TIMESTAMPTZ DEFAULT now()\n);\n',
    WORKSPACE / "scripts" / "monitoring" / "check_replication_lag.sh":
        '#!/usr/bin/env bash\npsql -h $PRIMARY_HOST -c "SELECT now() - pg_last_xact_replay_timestamp() AS replication_lag;"\n',
    WORKSPACE / "docs" / "architecture" / "db_topology.md":
        '# DB Topology\n\nPrimary: pg12-primary.internal\nReplica 1: pg12-replica-1.internal\nReplica 2: pg12-replica-2.internal\n\n## Planned\nPrimary: pg16-primary.internal (target)\n',
    WORKSPACE / "docs" / "runbooks" / "failover.md":
        '# Failover Runbook\n\n1. Promote replica\n2. Update DNS CNAME\n3. Restart application pods\n4. Verify connections\n',
    WORKSPACE / "ci" / "pipelines" / "migration_test.yml":
        'stages:\n  - validate\n  - migrate\n  - verify\n\nmigrate:\n  script:\n    - ./scripts/run_pglogical_migration.sh\n',
    WORKSPACE / "tests" / "integration" / "test_accounts_schema.py":
        'import psycopg2\nimport pytest\n\ndef test_accounts_table_exists(pg_conn):\n    cur = pg_conn.cursor()\n    cur.execute("SELECT to_regclass(\'public.accounts\')")\n    assert cur.fetchone()[0] is not None\n',
    WORKSPACE / "scripts" / "migrations" / "pg12" / "migration_notes.txt":
        'NOTES (outdated, do not rely on these):\n- pglogical extension must be installed on both sides\n- Replication set must include all tables\n- wal_level = logical required\nStatus: DRAFT - needs review\n',
}

for path, content in distractors.items():
    path.write_text(content)

# ── 4. A stale partial attempt at a project folder (wrong structure, wrong location)
stale = WORKSPACE / "old-notes" / "pg-migration"
stale.mkdir(parents=True, exist_ok=True)
(stale / "notes.md").write_text("# Random notes\n\n- talked to DBA team on Monday\n- need to check pglogical version compatibility\n- TODO: ask about maintenance window\n")
(stale / "tasks.txt").write_text("1. read pglogical docs\n2. provision test cluster\n3. run schema diff\n")

print("Workspace scaffold complete.")
print(f"Template EN: {template_en}")
print(f"Template ZH: {template_zh}")
print(f"Distractor files: {len(distractors)}")