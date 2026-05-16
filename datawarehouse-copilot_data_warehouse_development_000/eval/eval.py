import sys
import json
import re
from pathlib import Path

def load_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def evaluate(workspace_dir: str):
    ws = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ════════════════════════════════════════════════════════════════════════
    # FIND ARTIFACTS
    # ════════════════════════════════════════════════════════════════════════
    spec_files  = list(ws.rglob("spec.md"))
    plan_files  = list(ws.rglob("plan.md"))
    task_files  = list(ws.rglob("task.md"))

    spec_text = load_file(spec_files[0])  if spec_files  else None
    plan_text = load_file(plan_files[0])  if plan_files  else None
    task_text = load_file(task_files[0])  if task_files  else None

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 1 — spec.md exists and has required template sections
    # ════════════════════════════════════════════════════════════════════════
    if spec_text is None:
        total_score += add_check("spec.md exists", False, "spec.md not found anywhere in workspace.")
    else:
        total_score += add_check("spec.md exists", True, f"Found at {spec_files[0]}")

        # Required sections from spec-template.md
        required_spec_sections = [
            r"##\s+1[.\s]+背景",
            r"##\s+2[.\s]+数据范围",
            r"##\s+3[.\s]+字段规格",
            r"##\s+4[.\s]+业务规则",
            r"##\s+5[.\s]+下游",
            r"##\s+6[.\s]+验收",
        ]
        for pattern in required_spec_sections:
            found = bool(re.search(pattern, spec_text))
            total_score += add_check(
                f"spec.md section: {pattern}",
                found,
                f"Section matching '{pattern}' {'found' if found else 'MISSING'} in spec.md",
                weight=0.5
            )

        # Must have §-style field numbering
        has_field_numbers = bool(re.search(r'§3\.\d+', spec_text))
        total_score += add_check(
            "spec.md has §3.x field numbering",
            has_field_numbers,
            "spec.md must use §3.x numbering (e.g., §3.1) for each field row" if not has_field_numbers else "§3.x numbering found"
        )

        # ODS layer must be declared
        has_ods = bool(re.search(r'\bODS\b', spec_text, re.IGNORECASE))
        total_score += add_check(
            "spec.md declares ODS target layer",
            has_ods,
            "spec.md must declare ODS as the target layer"
        )

        # Must reference pt_date (business date partition field per project-conventions.md)
        has_pt_date_spec = bool(re.search(r'pt_date', spec_text))
        total_score += add_check(
            "spec.md references pt_date as partition field",
            has_pt_date_spec,
            "spec.md should reference 'pt_date' as the partition field per project-conventions.md"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 2 — plan.md exists and references spec sections
    # ════════════════════════════════════════════════════════════════════════
    if plan_text is None:
        total_score += add_check("plan.md exists", False, "plan.md not found anywhere in workspace.")
    else:
        total_score += add_check("plan.md exists", True, f"Found at {plan_files[0]}")

        required_plan_sections = [
            r"##\s+1[.\s]+技术选型",
            r"##\s+2[.\s]+表设计",
            r"##\s+3[.\s]+ETL",
            r"##\s+4[.\s]+调度",
        ]
        for pattern in required_plan_sections:
            found = bool(re.search(pattern, plan_text))
            total_score += add_check(
                f"plan.md section: {pattern}",
                found,
                f"Section matching '{pattern}' {'found' if found else 'MISSING'} in plan.md",
                weight=0.5
            )

        # plan.md must reference spec §3.x numbers
        has_spec_ref = bool(re.search(r'§3\.\d+', plan_text))
        total_score += add_check(
            "plan.md references spec §3.x field numbers",
            has_spec_ref,
            "plan.md must reference §3.x numbers from spec.md in the field mapping section"
        )

        # table name must follow ods_<source>_<entity>_inc naming convention
        correct_table_name = bool(re.search(r'ods_[a-z]+_[a-z_]+_inc\b', plan_text))
        total_score += add_check(
            "plan.md table name follows ods_*_*_inc convention",
            correct_table_name,
            "Table name must follow pattern ods_<source>_<entity>_inc per project-conventions.md"
        )

        # Must mention ORC storage
        has_orc = bool(re.search(r'\bORC\b', plan_text, re.IGNORECASE))
        total_score += add_check(
            "plan.md specifies ORC storage",
            has_orc,
            "plan.md must specify ORC as storage format per platform-conventions.md"
        )

        # Must mention MaxCompute / ODPS
        has_odps = bool(re.search(r'MaxCompute|ODPS|odps', plan_text))
        total_score += add_check(
            "plan.md mentions MaxCompute/ODPS engine",
            has_odps,
            "plan.md must specify MaxCompute (ODPS) as compute engine per platform-conventions.md"
        )

        # 180-day lifecycle for ODS
        has_lifecycle = bool(re.search(r'180', plan_text))
        total_score += add_check(
            "plan.md specifies 180-day ODS lifecycle",
            has_lifecycle,
            "ODS layer lifecycle must be 180 days per project-conventions.md"
        )

        # FlowX scheduler reference
        has_flowx = bool(re.search(r'FlowX|flowx|cron_daily', plan_text))
        total_score += add_check(
            "plan.md references FlowX scheduler DSL",
            has_flowx,
            "Scheduler must be FlowX with cron_daily DSL per platform-conventions.md"
        )

    # ════════════════════════════════════════════════════════════════════════
    # CHECK GROUP 3 — task.md exists and has correct proprietary content
    # ════════════════════════════════════════════════════════════════════════
    if task_text is None:
        total_score += add_check("task.md exists", False, "task.md not found anywhere in workspace.")
    else:
        total_score += add_check("task.md exists", True, f"Found at {task_files[0]}")

        required_task_sections = [
            r"##\s+1[.\s]+DDL",
            r"##\s+2[.\s]+ETL",
            r"##\s+3[.\s]+调度",
            r"##\s+4[.\s]+异常",
            r"##\s+5[.\s]+DoD",
        ]
        for pattern in required_task_sections:
            found = bool(re.search(pattern, task_text))
            total_score += add_check(
                f"task.md section: {pattern}",
                found,
                f"Section matching '{pattern}' {'found' if found else 'MISSING'} in task.md",
                weight=0.5
            )

        # DDL must use correct table naming convention
        correct_ddl_table = bool(re.search(r'ods_[a-z]+_[a-z_]+_inc', task_text))
        total_score += add_check(
            "task.md DDL uses ods_*_*_inc table naming",
            correct_ddl_table,
            "DDL table name must follow ods_<source>_<entity>_inc per project-conventions.md"
        )

        # PARTITIONED BY pt_date STRING
        has_pt_date_ddl = bool(re.search(r'PARTITIONED\s+BY\s*\([^)]*pt_date\s+STRING', task_text, re.IGNORECASE))
        total_score += add_check(
            "task.md DDL uses PARTITIONED BY pt_date STRING",
            has_pt_date_ddl,
            "DDL must include 'PARTITIONED BY (pt_date STRING)' per project-conventions.md"
        )

        # STORED AS ORC
        has_stored_orc = bool(re.search(r'STORED\s+AS\s+ORC', task_text, re.IGNORECASE))
        total_score += add_check(
            "task.md DDL contains STORED AS ORC",
            has_stored_orc,
            "DDL must declare 'STORED AS ORC' per platform-conventions.md"
        )

        # TBLPROPERTIES orc.compress=SNAPPY
        has_snappy = bool(re.search(r"orc\.compress.*SNAPPY|SNAPPY.*orc\.compress", task_text, re.IGNORECASE))
        total_score += add_check(
            "task.md DDL contains TBLPROPERTIES orc.compress=SNAPPY",
            has_snappy,
            "DDL must include TBLPROPERTIES('orc.compress'='SNAPPY') per platform-conventions.md"
        )

        # -- Spec: §x.x traceability annotation
        has_spec_trace = bool(re.search(r'--\s*Spec:\s*§\d+\.\d+', task_text))
        total_score += add_check(
            "task.md contains -- Spec: §x.x traceability comments",
            has_spec_trace,
            "DDL/ETL must include '-- Spec: §x.x' comments per project-conventions.md traceability rule"
        )

        # @lineage block in ETL
        has_lineage = bool(re.search(r'@lineage', task_text))
        total_score += add_check(
            "task.md ETL has @lineage declaration block",
            has_lineage,
            "ETL script must include @lineage ... @end_lineage block per platform-conventions.md"
        )

        # FlowX DSL: schedule type cron_daily
        has_cron_daily = bool(re.search(r'cron_daily', task_text))
        total_score += add_check(
            "task.md scheduler config uses cron_daily type",
            has_cron_daily,
            "Scheduler config must use 'type: cron_daily' per platform-conventions.md FlowX DSL"
        )

        # on_failure: alert_and_retry
        has_on_failure = bool(re.search(r'alert_and_retry', task_text))
        total_score += add_check(
            "task.md scheduler config uses on_failure: alert_and_retry",
            has_on_failure,
            "ODS tasks must set 'on_failure: alert_and_retry' per platform-conventions.md"
        )

        # retry_times: 3
        has_retry = bool(re.search(r'retry_times\s*:\s*3', task_text))
        total_score += add_check(
            "task.md scheduler config has retry_times: 3",
            has_retry,
            "ODS layer tasks must have 'retry_times: 3' per platform-conventions.md"
        )

        # type: odps_sql
        has_odps_sql = bool(re.search(r'odps_sql', task_text))
        total_score += add_check(
            "task.md scheduler config uses type: odps_sql",
            has_odps_sql,
            "MaxCompute tasks must use 'type: odps_sql' per platform-conventions.md"
        )

        # pt_date: ${bizdate}
        has_bizdate = bool(re.search(r'\$\{bizdate\}', task_text))
        total_score += add_check(
            "task.md scheduler uses ${bizdate} partition parameter",
            has_bizdate,
            "Partition parameter must be '${bizdate}' per platform-conventions.md"
        )

        # GRANT statements for role_dw_read and role_dw_write
        has_grant_read = bool(re.search(r'GRANT\s+SELECT.*role_dw_read', task_text, re.IGNORECASE))
        has_grant_write = bool(re.search(r'GRANT\s+INSERT.*role_dw_write', task_text, re.IGNORECASE))
        total_score += add_check(
            "task.md DDL has GRANT to role_dw_read",
            has_grant_read,
            "DDL must include 'GRANT SELECT ON TABLE ... TO ROLE role_dw_read' per platform-conventions.md"
        )
        total_score += add_check(
            "task.md DDL has GRANT to role_dw_write",
            has_grant_write,
            "DDL must include 'GRANT INSERT ON TABLE ... TO ROLE role_dw_write' per platform-conventions.md"
        )

        # task naming convention: ods__<table>__daily
        has_task_naming = bool(re.search(r'ods__ods_[a-z_]+__daily', task_text))
        total_score += add_check(
            "task.md scheduler job name follows ods__<table>__daily convention",
            has_task_naming,
            "Job name must follow '<layer>__<table_name>__<period>' per project-conventions.md"
        )

        # gmt_create / gmt_modified field naming
        has_gmt_fields = bool(re.search(r'gmt_create|gmt_modified', task_text))
        total_score += add_check(
            "task.md DDL uses gmt_create/gmt_modified field naming",
            has_gmt_fields,
            "Timestamp fields must be named gmt_create/gmt_modified per project-conventions.md"
        )

        # is_deleted field TINYINT
        has_is_deleted = bool(re.search(r'is_deleted\s+TINYINT', task_text, re.IGNORECASE))
        total_score += add_check(
            "task.md DDL contains is_deleted TINYINT field",
            has_is_deleted,
            "Logical delete field must be named is_deleted with type TINYINT per project-conventions.md"
        )

        # DoD checklist items present
        has_dod = bool(re.search(r'\[\s*[xX ]?\s*\]\s+DDL', task_text))
        total_score += add_check(
            "task.md has DoD checklist",
            has_dod,
            "task.md must contain DoD checklist items ([ ] DDL ...) per task-template.md"
        )

    # ════════════════════════════════════════════════════════════════════════
    # NORMALIZE SCORE
    # ════════════════════════════════════════════════════════════════════════
    max_possible = sum([
        1,  # spec exists
        6 * 0.5,  # spec sections
        1,  # §3.x numbering
        1,  # ODS declared
        1,  # pt_date in spec
        1,  # plan exists
        4 * 0.5,  # plan sections
        1,  # plan refs §3.x
        1,  # table naming
        1,  # ORC
        1,  # MaxCompute
        1,  # 180 days
        1,  # FlowX
        1,  # task exists
        5 * 0.5,  # task sections
        1,  # table naming DDL
        1,  # pt_date STRING
        1,  # STORED AS ORC
        1,  # SNAPPY
        1,  # Spec trace
        1,  # lineage
        1,  # cron_daily
        1,  # alert_and_retry
        1,  # retry_times 3
        1,  # odps_sql
        1,  # bizdate
        1,  # grant read
        1,  # grant write
        1,  # task naming
        1,  # gmt fields
        1,  # is_deleted
        1,  # DoD
    ])

    normalized = round(total_score / max_possible, 4) if max_possible > 0 else 0.0
    passed = normalized >= 0.70

    return {
        "passed": passed,
        "score": normalized,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))