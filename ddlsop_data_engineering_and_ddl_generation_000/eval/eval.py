import sys
import re
import json
from pathlib import Path

def find_target_file(workspace: Path) -> Path | None:
    candidates = list(workspace.rglob("dwd_usr_user_click_log_hinc.sql"))
    if candidates:
        return candidates[0]
    return None

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0

    # Locate file
    target = find_target_file(workspace)
    if target is None:
        checks.append(check("file_exists", False, "Could not find 'dwd_usr_user_click_log_hinc.sql' anywhere in workspace."))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append(check("file_exists", True, f"Found at: {target}"))
    total_score += 0.05

    try:
        content = target.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, f"Could not read file: {e}"))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append(check("file_readable", True, "File is readable."))
    content_lower = content.lower()

    # ---------------------------------------------------------------
    # CHECK 1: Table name includes correct workspace prefix (test_workspace)
    # ---------------------------------------------------------------
    table_name_pattern = re.search(
        r'create\s+table\s+(?:if\s+not\s+exists\s+)?([`"\[]?test_workspace[`"\]]?\.[`"\[]?dwd_usr_user_click_log_hinc[`"\]]?)',
        content,
        re.IGNORECASE
    )
    if table_name_pattern:
        checks.append(check("correct_table_name_with_workspace",
                            True,
                            f"Found correct table reference: {table_name_pattern.group(1)}"))
        total_score += 0.15
    else:
        # Also accept without backticks
        alt_pattern = re.search(
            r'create\s+table\s+(?:if\s+not\s+exists\s+)?test_workspace\.dwd_usr_user_click_log_hinc',
            content,
            re.IGNORECASE
        )
        if alt_pattern:
            checks.append(check("correct_table_name_with_workspace", True,
                                "Found correct table reference (no quotes)."))
            total_score += 0.15
        else:
            checks.append(check("correct_table_name_with_workspace", False,
                                "Table must be named exactly 'test_workspace.dwd_usr_user_click_log_hinc'. "
                                "Check workspace prefix and naming convention."))

    # ---------------------------------------------------------------
    # CHECK 2: All 8 required business fields present
    # ---------------------------------------------------------------
    required_fields = [
        "user_id", "session_id", "event_type", "item_id",
        "page_name", "duration_sec", "client_ip", "event_time"
    ]
    missing_fields = []
    for field in required_fields:
        pattern = re.compile(r'\b' + re.escape(field) + r'\b', re.IGNORECASE)
        if not pattern.search(content):
            missing_fields.append(field)

    if not missing_fields:
        checks.append(check("all_required_fields_present", True,
                            "All 8 required business fields are present."))
        total_score += 0.10
    else:
        checks.append(check("all_required_fields_present", False,
                            f"Missing fields: {missing_fields}"))

    # ---------------------------------------------------------------
    # CHECK 3: Audit fields present (gmt_create, gmt_modified, ds)
    # ---------------------------------------------------------------
    audit_fields = ["gmt_create", "gmt_modified", "ds"]
    missing_audit = [f for f in audit_fields if not re.search(r'\b' + f + r'\b', content, re.IGNORECASE)]
    if not missing_audit:
        checks.append(check("audit_fields_present", True,
                            "gmt_create, gmt_modified, ds are all present."))
        total_score += 0.10
    else:
        checks.append(check("audit_fields_present", False,
                            f"Missing audit fields: {missing_audit}. "
                            "The skill requires these standard audit fields."))

    # ---------------------------------------------------------------
    # CHECK 4: All non-partition fields have COMMENT
    # ---------------------------------------------------------------
    # Count column definitions (lines with a type keyword) vs those with COMMENT
    col_lines = re.findall(
        r'`?\w+`?\s+(?:STRING|BIGINT|DOUBLE|DATETIME|DECIMAL|INT|VARCHAR)[^,\n]*',
        content,
        re.IGNORECASE
    )
    lines_without_comment = [l.strip() for l in col_lines
                              if 'comment' not in l.lower()
                              and 'partitioned' not in l.lower()]
    if not lines_without_comment:
        checks.append(check("all_fields_have_comment", True,
                            "All detected column definitions include COMMENT."))
        total_score += 0.10
    else:
        checks.append(check("all_fields_have_comment", False,
                            f"These column lines lack COMMENT: {lines_without_comment[:5]}"))

    # ---------------------------------------------------------------
    # CHECK 5: Table-level COMMENT is present (not empty)
    # ---------------------------------------------------------------
    # Must have a COMMENT at table level (after the column list)
    table_comment_match = re.search(
        r'\)\s*\n?\s*COMMENT\s+[\'"](.+?)[\'"]',
        content,
        re.IGNORECASE | re.DOTALL
    )
    if table_comment_match:
        tc = table_comment_match.group(1).strip()
        checks.append(check("table_comment_exists", True, f"Table comment found: '{tc[:80]}'"))
        total_score += 0.05
    else:
        checks.append(check("table_comment_exists", False,
                            "No table-level COMMENT found after the column list closing paren."))

    # ---------------------------------------------------------------
    # CHECK 6: DUAL partition for hourly table (ds + hr) — THE TRAP
    # ---------------------------------------------------------------
    partitioned_block = re.search(
        r'PARTITIONED\s+BY\s*\((.+?)\)',
        content,
        re.IGNORECASE | re.DOTALL
    )
    if partitioned_block:
        partition_content = partitioned_block.group(1)
        has_ds = bool(re.search(r'\bds\b', partition_content, re.IGNORECASE))
        has_hr = bool(re.search(r'\bhr\b', partition_content, re.IGNORECASE))
        if has_ds and has_hr:
            checks.append(check("hourly_dual_partition_ds_and_hr", True,
                                "Correct dual partition: both 'ds' and 'hr' found in PARTITIONED BY."))
            total_score += 0.20
        elif has_ds:
            checks.append(check("hourly_dual_partition_ds_and_hr", False,
                                "Only 'ds' partition found. Hourly tables require BOTH 'ds' AND 'hr' partitions "
                                "per the skill specification."))
        else:
            checks.append(check("hourly_dual_partition_ds_and_hr", False,
                                f"Partition definition '{partition_content.strip()}' is missing 'ds' and/or 'hr'."))
    else:
        checks.append(check("hourly_dual_partition_ds_and_hr", False,
                            "No PARTITIONED BY clause found. Hourly incremental tables must be partitioned."))

    # ---------------------------------------------------------------
    # CHECK 7: STORED AS ALIORC
    # ---------------------------------------------------------------
    if re.search(r'STORED\s+AS\s+ALIORC', content, re.IGNORECASE):
        checks.append(check("stored_as_aliorc", True, "STORED AS ALIORC found."))
        total_score += 0.10
    else:
        checks.append(check("stored_as_aliorc", False,
                            "Missing 'STORED AS ALIORC'. The skill mandates this as the default storage format."))

    # ---------------------------------------------------------------
    # CHECK 8: Lifecycle TTL set with TBLPROPERTIES syntax, value 180-365
    # ---------------------------------------------------------------
    lifecycle_match = re.search(
        r"TBLPROPERTIES\s*\([^)]*'lifecycle'\s*=\s*'(\d+)'[^)]*\)",
        content,
        re.IGNORECASE
    )
    if lifecycle_match:
        ttl_val = int(lifecycle_match.group(1))
        if 180 <= ttl_val <= 365:
            checks.append(check("lifecycle_tblproperties_correct", True,
                                f"lifecycle='{ttl_val}' is within DWD recommended range [180, 365]."))
            total_score += 0.15
        else:
            checks.append(check("lifecycle_tblproperties_correct", False,
                                f"lifecycle='{ttl_val}' is outside DWD recommended range [180, 365]."))
    else:
        checks.append(check("lifecycle_tblproperties_correct", False,
                            "No valid TBLPROPERTIES lifecycle found. Must use: "
                            "TBLPROPERTIES ('lifecycle'='<number>') with value between 180 and 365."))

    # ---------------------------------------------------------------
    # Final verdict
    # ---------------------------------------------------------------
    # Normalize score
    total_score = min(round(total_score, 3), 1.0)

    # Must pass critical checks to be considered passing
    critical_checks = [
        "correct_table_name_with_workspace",
        "hourly_dual_partition_ds_and_hr",
        "stored_as_aliorc",
        "lifecycle_tblproperties_correct",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    overall_passed = critical_passed and total_score >= 0.70

    print(json.dumps({
        "passed": overall_passed,
        "score": total_score,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(ws)