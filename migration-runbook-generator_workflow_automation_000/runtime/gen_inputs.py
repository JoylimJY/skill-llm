#!/usr/bin/env python3
"""
Workspace generator for the migration-runbook-generator evaluation task.
Creates the full skill directory, distractor files, and the messy raw input.
"""
import os
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ─────────────────────────────────────────────
# 1. SKILL DIRECTORY STRUCTURE
# ─────────────────────────────────────────────
skill_dir = WORKSPACE / "skills" / "migration-runbook-generator"
(skill_dir / "scripts").mkdir(parents=True, exist_ok=True)
(skill_dir / "resources").mkdir(parents=True, exist_ok=True)
(skill_dir / "examples").mkdir(parents=True, exist_ok=True)
(skill_dir / "tests").mkdir(parents=True, exist_ok=True)

# --- spec.json ---
spec = {
    "version": "1.0.0",
    "name": "migration-runbook-generator",
    "required_sections": [
        "前置检查",
        "迁移步骤",
        "切换窗口",
        "验证信号",
        "回滚方案",
        "责任分工"
    ],
    "optional_sections": [
        "待确认项"
    ],
    "output_format": "markdown",
    "generated_by_marker": "<!-- generated-by: migration-runbook-generator v1.0.0 -->",
    "rules": {
        "missing_info": "list as 待确认项, do not fabricate",
        "high_risk": "add boundary statement",
        "default_mode": "reviewable draft first"
    }
}
(skill_dir / "resources" / "spec.json").write_text(
    json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

# --- template.md ---
template_md = textwrap.dedent("""\
    <!-- generated-by: migration-runbook-generator v1.0.0 -->
    # 迁移 Runbook：{{ title }}

    > 草案版本（Draft）— 仅供审阅，未经批准不可执行。

    ---

    ## 待确认项
    {% if pending_items %}
    {% for item in pending_items %}
    - [ ] {{ item }}
    {% endfor %}
    {% else %}
    （无）
    {% endif %}

    ---

    ## 前置检查
    {% for check in pre_checks %}
    - {{ check }}
    {% endfor %}

    ---

    ## 迁移步骤
    {% for step in migration_steps %}
    {{ loop.index }}. {{ step }}
    {% endfor %}

    ---

    ## 切换窗口
    - 计划窗口：{{ switch_window }}
    - 持续时间：{{ window_duration }}

    ---

    ## 验证信号
    {% for signal in validation_signals %}
    - {{ signal }}
    {% endfor %}

    ---

    ## 回滚方案
    {% for step in rollback_steps %}
    {{ loop.index }}. {{ step }}
    {% endfor %}

    ---

    ## 责任分工
    {% for role, person in assignments.items() %}
    | {{ role }} | {{ person }} |
    {% endfor %}

    ---
    *本文档由迁移 Runbook 生成器自动产出，请在执行前完成待确认项的确认。*
""")
(skill_dir / "resources" / "template.md").write_text(template_md, encoding="utf-8")

# --- scripts/run.py ---
# This is the proprietary script the agent must invoke.
run_py = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    Migration Runbook Generator — run.py
    Usage: python3 run.py --input <input_file> --output <output_file>
    \"\"\"
    import argparse
    import json
    import re
    import sys
    from pathlib import Path

    try:
        from jinja2 import Template
    except ImportError:
        print("[ERROR] jinja2 is required. Install with: pip install jinja2", file=sys.stderr)
        sys.exit(1)

    BASE_DIR = Path(__file__).parent.parent
    SPEC_PATH = BASE_DIR / "resources" / "spec.json"
    TEMPLATE_PATH = BASE_DIR / "resources" / "template.md"

    def load_spec():
        return json.loads(SPEC_PATH.read_text(encoding="utf-8"))

    def load_template():
        return TEMPLATE_PATH.read_text(encoding="utf-8")

    def parse_input(text: str) -> dict:
        \"\"\"
        Parse a free-form migration plan text into structured fields.
        Missing fields are collected as pending_items.
        \"\"\"
        data = {
            "title": "未命名迁移任务",
            "pending_items": [],
            "pre_checks": [],
            "migration_steps": [],
            "switch_window": "【待确认】",
            "window_duration": "【待确认】",
            "validation_signals": [],
            "rollback_steps": [],
            "assignments": {},
        }

        lines = [l.strip() for l in text.splitlines() if l.strip()]

        # Extract title
        for line in lines:
            if re.search(r"(迁移|migration|migrate)", line, re.IGNORECASE):
                data["title"] = line[:80]
                break

        # Extract switch window hints
        window_match = re.search(
            r"(切换窗口|maintenance.?window|switch.?window)[：:\s]*([^\n]+)",
            text, re.IGNORECASE
        )
        if window_match:
            data["switch_window"] = window_match.group(2).strip()
        else:
            data["pending_items"].append("切换窗口未指定，请确认具体日期和时间段")

        # Extract duration
        dur_match = re.search(
            r"(持续时间|duration|window.?duration)[：:\s]*([^\n]+)",
            text, re.IGNORECASE
        )
        if dur_match:
            data["window_duration"] = dur_match.group(2).strip()
        else:
            data["pending_items"].append("迁移窗口持续时间未指定")

        # Extract pre-checks section
        in_section = False
        section_map = {
            "pre_checks": re.compile(r"(前置检查|pre.?check|checklist)", re.IGNORECASE),
            "migration_steps": re.compile(r"(迁移步骤|migration.?step|steps)", re.IGNORECASE),
            "validation_signals": re.compile(r"(验证信号|validat|acceptance)", re.IGNORECASE),
            "rollback_steps": re.compile(r"(回滚|rollback|roll.?back)", re.IGNORECASE),
        }
        current_section = None
        for line in lines:
            matched = False
            for key, pattern in section_map.items():
                if pattern.search(line):
                    current_section = key
                    matched = True
                    break
            if not matched and current_section and (line.startswith("-") or line.startswith("*") or re.match(r"^\\d+[.).]", line)):
                clean = re.sub(r"^[-*\\d+.)]\\s*", "", line).strip()
                if clean:
                    data[current_section].append(clean)

        # Extract assignments / 责任分工
        assign_match = re.findall(
            r"(责任人|负责人|owner|DRI|on.?call)[：:\s]*([^\n,，]+)",
            text, re.IGNORECASE
        )
        for role, person in assign_match:
            data["assignments"][role.strip()] = person.strip()

        # Check rollback owner
        rollback_owner_found = bool(re.search(
            r"(回滚负责人|rollback.?owner|rollback.?dri)[：:\s]*\S",
            text, re.IGNORECASE
        ))
        if not rollback_owner_found:
            data["pending_items"].append("回滚负责人未指定，需在执行前确认")

        # Check compliance
        compliance_found = bool(re.search(
            r"(合规|compliance|audit.?approval|变更审批|change.?approval)",
            text, re.IGNORECASE
        ))
        if not compliance_found:
            data["pending_items"].append("合规/变更审批状态未确认，请补充变更单号或审批记录")

        # Fallback steps
        if not data["pre_checks"]:
            # Try numbered items anywhere
            for line in lines:
                if re.match(r"^\\d+[.).]\\s+.*(check|确认|验证|备份|backup)", line, re.IGNORECASE):
                    data["pre_checks"].append(line)

        if not data["migration_steps"]:
            data["pending_items"].append("迁移步骤未结构化提供，请补充详细步骤清单")

        if not data["rollback_steps"]:
            data["pending_items"].append("回滚步骤未提供，请补充回滚操作清单")

        if not data["validation_signals"]:
            data["pending_items"].append("验证信号未指定，请定义迁移成功的可观测标准")

        return data

    def render(data: dict, template_text: str) -> str:
        from jinja2 import Template
        tpl = Template(template_text, trim_blocks=True, lstrip_blocks=True)
        return tpl.render(**data)

    def main():
        parser = argparse.ArgumentParser(description="Migration Runbook Generator")
        parser.add_argument("--input", required=True, help="Path to input migration plan file")
        parser.add_argument("--output", required=True, help="Path to output runbook file")
        args = parser.parse_args()

        input_path = Path(args.input)
        output_path = Path(args.output)

        if not input_path.exists():
            print(f"[ERROR] Input file not found: {input_path}", file=sys.stderr)
            sys.exit(1)

        spec = load_spec()
        template_text = load_template()

        raw_text = input_path.read_text(encoding="utf-8")
        data = parse_input(raw_text)

        rendered = render(data, template_text)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")

        print(f"[OK] Runbook generated: {output_path}")
        print(f"[INFO] Pending items found: {len(data['pending_items'])}")
        for item in data["pending_items"]:
            print(f"  - {item}")

    if __name__ == "__main__":
        main()
""")
(skill_dir / "scripts" / "run.py").write_text(run_py, encoding="utf-8")
os.chmod(skill_dir / "scripts" / "run.py", 0o755)

# --- examples/ ---
example_input = textwrap.dedent("""\
    # Redis 缓存层迁移示例

    切换窗口：2024-03-15 02:00-04:00 (UTC+8)
    持续时间：2小时

    前置检查：
    - 确认 Redis 6.2 版本兼容性
    - 备份现有 RDB 快照

    迁移步骤：
    1. 停止写入流量
    2. 同步数据到新集群
    3. 切换 DNS

    验证信号：
    - 延迟 P99 < 10ms
    - 错误率 < 0.01%

    回滚方案：
    1. DNS 切回旧集群
    2. 恢复 RDB 快照

    责任人：张工
    回滚负责人：李工
    合规审批：变更单 CHG-20240315-001
""")
(skill_dir / "examples" / "input_redis_migration.txt").write_text(example_input, encoding="utf-8")

example_output = textwrap.dedent("""\
    <!-- generated-by: migration-runbook-generator v1.0.0 -->
    # 迁移 Runbook：Redis 缓存层迁移示例

    > 草案版本（Draft）— 仅供审阅，未经批准不可执行。

    ---

    ## 待确认项
    （无）

    ---

    ## 前置检查
    - 确认 Redis 6.2 版本兼容性
    - 备份现有 RDB 快照

    ---

    ## 迁移步骤
    1. 停止写入流量
    2. 同步数据到新集群
    3. 切换 DNS

    ---

    ## 切换窗口
    - 计划窗口：2024-03-15 02:00-04:00 (UTC+8)
    - 持续时间：2小时

    ---

    ## 验证信号
    - 延迟 P99 < 10ms
    - 错误率 < 0.01%

    ---

    ## 回滚方案
    1. DNS 切回旧集群
    2. 恢复 RDB 快照

    ---

    ## 责任分工
    | 责任人 | 张工 |
    | 回滚负责人 | 李工 |

    ---
    *本文档由迁移 Runbook 生成器自动产出，请在执行前完成待确认项的确认。*
""")
(skill_dir / "examples" / "output_redis_migration.md").write_text(example_output, encoding="utf-8")

# --- tests/smoke-test.md ---
smoke_test = textwrap.dedent("""\
    # Smoke Test

    ## Test 1: Basic generation
    Run:
        python3 scripts/run.py --input examples/input_redis_migration.txt --output /tmp/smoke_out.md

    Expected:
    - Exit code 0
    - File /tmp/smoke_out.md contains '<!-- generated-by: migration-runbook-generator v1.0.0 -->'
    - All 6 required sections present

    ## Test 2: Missing info detection
    Run with an input that omits rollback owner and switch window.
    Expected:
    - 待确认项 section lists at least 2 items
""")
(skill_dir / "tests" / "smoke-test.md").write_text(smoke_test, encoding="utf-8")

# ─────────────────────────────────────────────
# 2. PROJECT DIRECTORY — THE MESSY INPUT
# ─────────────────────────────────────────────
project_dir = WORKSPACE / "project" / "pg-cloud-migration"
(project_dir / "docs").mkdir(parents=True, exist_ok=True)
(project_dir / "infra" / "terraform").mkdir(parents=True, exist_ok=True)
(project_dir / "infra" / "ansible").mkdir(parents=True, exist_ok=True)
(project_dir / "ci").mkdir(parents=True, exist_ok=True)
(project_dir / "monitoring").mkdir(parents=True, exist_ok=True)
(project_dir / "backups").mkdir(parents=True, exist_ok=True)
(project_dir / "meeting-notes").mkdir(parents=True, exist_ok=True)

# THE ACTUAL MESSY INPUT — intentionally missing critical fields
raw_plan = textwrap.dedent("""\
    PostgreSQL 核心交易库迁移方案 v0.3 (DRAFT)
    ============================================
    项目背景：
    由于数据中心合同到期，需将核心交易数据库（PostgreSQL 14，约 2.8TB）
    从自建机房迁移至托管云服务（AWS RDS Aurora PostgreSQL-compatible）。
    本次迁移涉及 3 个生产库：trade_db、risk_db、settlement_db。

    迁移目标：
    - 零数据丢失（RPO = 0）
    - 停机时间 < 4 小时
    - 兼容现有应用连接层（不改 DSN 格式）

    前置检查：
    - 确认 Aurora PG 14 兼容模式已开启
    - 验证 DMS 任务配置（trade_db、risk_db、settlement_db）
    - 确认 VPC peering 及安全组规则
    - 应用层读写分离配置已冻结
    - 存量 pg_dump 备份已在 S3 落位

    迁移步骤：
    1. 启动 AWS DMS 全量复制任务
    2. 监控 DMS 延迟，等待增量同步追平（latency < 1s）
    3. 发送业务暂停通知（T-30min）
    4. 冻结写入：在 trade_db 主库执行 SET default_transaction_read_only = on
    5. 验证 DMS 增量同步完毕（行数对齐）
    6. 更新 Route53 CNAME：db.internal → aurora-cluster.rds.amazonaws.com
    7. 重启应用连接池（各服务 rolling restart）
    8. 业务恢复通知

    切换窗口：待排期（倾向于下个季度某个周末凌晨，具体时间 TBD）

    验证信号：
    - 交易下单成功率 ≥ 99.95%
    - P99 查询延迟 < 80ms
    - DMS 任务状态 = Load complete, replication ongoing
    - Aurora CloudWatch 指标：DatabaseConnections > 0，WriteIOPS > 0

    回滚方案：
    - 如切换后 15 分钟内出现错误，立即回滚
    - 回滚操作：将 Route53 CNAME 切回原机房 PG 主库 IP
    - 重启应用连接池
    - 通知相关方
    （注：回滚时需要谁来执行？暂未指定）

    团队联系人：
    迁移负责人：王磊（DBA Team Lead）
    应用负责人：陈晓（Backend Arch）
    监控告警：运维平台组（值班系统）

    附注：本文档尚未经过合规部门评审，也未提交变更审批系统。
    网络割接需要网络部门配合，联系人待确认。
""")
(project_dir / "docs" / "raw_migration_plan.txt").write_text(raw_plan, encoding="utf-8")

# ─────────────────────────────────────────────
# 3. DISTRACTOR FILES (10+)
# ─────────────────────────────────────────────

# distractor 1: old ERD
(project_dir / "docs" / "erd_v2_legacy.txt").write_text(
    "Entity-Relationship Diagram (legacy)\ntrade_db: orders(id, user_id, amount, ts)\nrisk_db: risk_events(id, order_id, score)\n",
    encoding="utf-8"
)

# distractor 2: terraform main
(project_dir / "infra" / "terraform" / "main.tf").write_text(
    'provider "aws" { region = "ap-northeast-1" }\nresource "aws_rds_cluster" "aurora" { engine = "aurora-postgresql" }\n',
    encoding="utf-8"
)

# distractor 3: terraform variables
(project_dir / "infra" / "terraform" / "variables.tf").write_text(
    'variable "db_instance_class" { default = "db.r6g.2xlarge" }\nvariable "retention_period" { default = 7 }\n',
    encoding="utf-8"
)

# distractor 4: ansible playbook
(project_dir / "infra" / "ansible" / "pg_backup.yml").write_text(
    "- hosts: pg_masters\n  tasks:\n    - name: run pg_dump\n      shell: pg_dump -Fc trade_db > /backups/trade_db.dump\n",
    encoding="utf-8"
)

# distractor 5: CI config
(project_dir / "ci" / ".gitlab-ci.yml").write_text(
    "stages:\n  - test\n  - deploy\ntest-job:\n  stage: test\n  script: pytest tests/\n",
    encoding="utf-8"
)

# distractor 6: monitoring dashboard config
(project_dir / "monitoring" / "grafana_dashboard_export.json").write_text(
    json.dumps({"title": "Aurora PG Monitoring", "panels": [{"title": "Write IOPS"}, {"title": "DB Connections"}]}, indent=2),
    encoding="utf-8"
)

# distractor 7: backup manifest
(project_dir / "backups" / "backup_manifest_2024Q4.txt").write_text(
    "trade_db_20241201.dump  SHA256: abc123\nrisk_db_20241201.dump   SHA256: def456\nsettlement_db_20241201.dump SHA256: 789ghi\n",
    encoding="utf-8"
)

# distractor 8: meeting notes
(project_dir / "meeting-notes" / "kickoff_2024-11-15.txt").write_text(
    "Attendees: 王磊, 陈晓, 财务代表\nAction items:\n- 确认 AWS 账号配额\n- 申请 DMS 权限\n- 下次会议：12月初\n",
    encoding="utf-8"
)

# distractor 9: stale runbook attempt (incorrect format, missing sections)
(project_dir / "docs" / "runbook_draft_STALE_DO_NOT_USE.txt").write_text(
    "OLD DRAFT - ABANDONED\n\n步骤1: 备份\n步骤2: 迁移\n步骤3: 验证\n（无回滚方案，此版本作废）\n",
    encoding="utf-8"
)

# distractor 10: network topology
(project_dir / "docs" / "network_topology.txt").write_text(
    "IDC -> VPN -> VPC (ap-northeast-1)\nSubnets: 10.0.1.0/24 (app), 10.0.2.0/24 (db)\nSecurity Groups: sg-app -> sg-aurora (5432)\n",
    encoding="utf-8"
)

# distractor 11: DMS task config
(project_dir / "infra" / "dms_task_config.json").write_text(
    json.dumps({
        "tasks": [
            {"name": "trade_db_full_load", "source": "pg-idc-primary", "target": "aurora-pg"},
            {"name": "risk_db_cdc", "source": "pg-idc-primary", "target": "aurora-pg"}
        ],
        "replication_instance": "dms.r5.xlarge"
    }, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

# distractor 12: application DSN config (shows what must NOT change)
(project_dir / "docs" / "app_dsn_requirements.txt").write_text(
    "Connection string format must remain:\npostgresql://app_user:***@db.internal:5432/trade_db\nNo application code changes allowed during cutover.\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Skill dir: {skill_dir}")
print(f"Raw input: {project_dir / 'docs' / 'raw_migration_plan.txt'}")