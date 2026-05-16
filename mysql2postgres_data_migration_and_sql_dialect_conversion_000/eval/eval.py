import sys
import json
import re
import os
from pathlib import Path

def load_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def check(name, condition, detail=""):
    return {"name": name, "passed": bool(condition), "detail": detail}

workspace = sys.argv[1]
checks = []

# ── File paths (hardcoded, created by gen_inputs_script) ──────────────────────
app_yaml_path = os.path.join(workspace, "src/main/resources/application.yaml")
order_xml_path = os.path.join(workspace, "src/main/resources/mapper/OrderMapper.xml")
detail_xml_path = os.path.join(workspace, "src/main/resources/mapper/OrderDetailMapper.xml")

# ── Eval helper ───────────────────────────────────────────────────────────────
def find_sequence_sql(workspace):
    """Find any .sql file in workspace that contains CREATE SEQUENCE."""
    for p in Path(workspace).rglob("*.sql"):
        content = p.read_text(encoding="utf-8", errors="ignore")
        if "CREATE SEQUENCE" in content.upper() or "create sequence" in content.lower():
            return content
    return None

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 1: application.yaml checks
# ══════════════════════════════════════════════════════════════════════════════
try:
    yaml_content = load_file(app_yaml_path)

    # 1a. JDBC URL changed to PostgreSQL
    has_pg_url = "jdbc:postgresql://" in yaml_content
    has_mysql_url = "jdbc:mysql://" in yaml_content
    checks.append(check(
        "YAML: JDBC URL changed to PostgreSQL",
        has_pg_url and not has_mysql_url,
        f"pg_url={has_pg_url}, mysql_url_still_present={has_mysql_url}"
    ))

    # 1b. currentSchema parameter present in URL
    has_current_schema = "currentSchema=" in yaml_content
    checks.append(check(
        "YAML: currentSchema parameter in JDBC URL",
        has_current_schema,
        f"currentSchema found: {has_current_schema}"
    ))

    # 1c. validation-query / connection-test-query has no FROM DUAL
    has_dual = "DUAL" in yaml_content.upper()
    has_select1 = re.search(r"(?:validation-query|connection-test-query)\s*:\s*SELECT 1\s*$", yaml_content, re.MULTILINE) is not None
    checks.append(check(
        "YAML: validation-query is 'SELECT 1' without FROM DUAL",
        has_select1 and not has_dual,
        f"select1_correct={has_select1}, DUAL_still_present={has_dual}"
    ))

    # 1d. logic-delete-value is B'1' (PG BIT literal)
    # Accept both quoted and unquoted forms: "B'1'" or B'1'
    logic_delete_correct = bool(re.search(r"logic-delete-value\s*:\s*[\"']?B'1'[\"']?", yaml_content))
    checks.append(check(
        "YAML: logic-delete-value is B'1' (PG BIT literal)",
        logic_delete_correct,
        f"Found correct BIT literal: {logic_delete_correct}. Content snippet: {[l for l in yaml_content.splitlines() if 'logic-delete' in l]}"
    ))

    # 1e. logic-not-delete-value is B'0'
    logic_not_delete_correct = bool(re.search(r"logic-not-delete-value\s*:\s*[\"']?B'0'[\"']?", yaml_content))
    checks.append(check(
        "YAML: logic-not-delete-value is B'0' (PG BIT literal)",
        logic_not_delete_correct,
        f"Found correct BIT literal: {logic_not_delete_correct}. Content snippet: {[l for l in yaml_content.splitlines() if 'logic-not' in l]}"
    ))

except Exception as e:
    checks.append(check("YAML: File readable", False, str(e)))

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 2: OrderMapper.xml checks
# ══════════════════════════════════════════════════════════════════════════════
try:
    order_xml = load_file(order_xml_path)

    # 2a. IFNULL replaced with COALESCE
    has_ifnull = "IFNULL" in order_xml.upper()
    has_coalesce = "COALESCE" in order_xml.upper()
    checks.append(check(
        "OrderMapper.xml: IFNULL replaced with COALESCE",
        not has_ifnull and has_coalesce,
        f"ifnull_remaining={has_ifnull}, coalesce_present={has_coalesce}"
    ))

    # 2b. DATE_FORMAT replaced with TO_CHAR
    has_date_format = "DATE_FORMAT" in order_xml.upper()
    has_to_char = "TO_CHAR" in order_xml.upper()
    checks.append(check(
        "OrderMapper.xml: DATE_FORMAT replaced with TO_CHAR",
        not has_date_format and has_to_char,
        f"date_format_remaining={has_date_format}, to_char_present={has_to_char}"
    ))

    # 2c. CURDATE() replaced with CURRENT_DATE
    has_curdate = "CURDATE()" in order_xml.upper()
    has_current_date = "CURRENT_DATE" in order_xml.upper()
    checks.append(check(
        "OrderMapper.xml: CURDATE() replaced with CURRENT_DATE",
        not has_curdate and has_current_date,
        f"curdate_remaining={has_curdate}, current_date_present={has_current_date}"
    ))

    # 2d. DATE_ADD INTERVAL syntax converted to PG style (+ INTERVAL '...')
    has_date_add = "DATE_ADD" in order_xml.upper()
    has_pg_interval = bool(re.search(r"INTERVAL\s+'[^']*'", order_xml, re.IGNORECASE))
    checks.append(check(
        "OrderMapper.xml: DATE_ADD replaced with PG interval arithmetic",
        not has_date_add and has_pg_interval,
        f"date_add_remaining={has_date_add}, pg_interval_syntax={has_pg_interval}"
    ))

    # 2e. INSERT IGNORE replaced with ON CONFLICT DO NOTHING
    has_insert_ignore = "INSERT IGNORE" in order_xml.upper()
    has_on_conflict_nothing = bool(re.search(r"ON CONFLICT.*DO NOTHING", order_xml, re.IGNORECASE | re.DOTALL))
    checks.append(check(
        "OrderMapper.xml: INSERT IGNORE replaced with ON CONFLICT DO NOTHING",
        not has_insert_ignore and has_on_conflict_nothing,
        f"insert_ignore_remaining={has_insert_ignore}, on_conflict_do_nothing={has_on_conflict_nothing}"
    ))

    # 2f. ON DUPLICATE KEY UPDATE replaced with ON CONFLICT (...) DO UPDATE SET
    has_dup_key = "ON DUPLICATE KEY" in order_xml.upper()
    has_on_conflict_update = bool(re.search(r"ON CONFLICT\s*\([^)]+\)\s*DO UPDATE SET", order_xml, re.IGNORECASE))
    checks.append(check(
        "OrderMapper.xml: ON DUPLICATE KEY UPDATE replaced with ON CONFLICT DO UPDATE SET",
        not has_dup_key and has_on_conflict_update,
        f"dup_key_remaining={has_dup_key}, on_conflict_update={has_on_conflict_update}"
    ))

    # 2g. UPDATE...INNER JOIN converted to UPDATE...FROM...WHERE
    has_update_join = bool(re.search(r"UPDATE\s+\w+\s+\w+\s+INNER JOIN", order_xml, re.IGNORECASE))
    has_update_from = bool(re.search(r"UPDATE\s+\w+\s+\w*\s*SET\s+[^;]+FROM\s+\w+", order_xml, re.IGNORECASE | re.DOTALL))
    checks.append(check(
        "OrderMapper.xml: UPDATE JOIN converted to UPDATE FROM WHERE",
        not has_update_join and has_update_from,
        f"update_join_remaining={has_update_join}, update_from_present={has_update_from}"
    ))

    # 2h. CAST(x AS DATETIME) → CAST(x AS TIMESTAMP)
    has_cast_datetime = bool(re.search(r"CAST\s*\([^)]+AS\s+DATETIME\)", order_xml, re.IGNORECASE))
    has_cast_timestamp = bool(re.search(r"CAST\s*\([^)]+AS\s+TIMESTAMP\)", order_xml, re.IGNORECASE))
    checks.append(check(
        "OrderMapper.xml: CAST AS DATETIME replaced with CAST AS TIMESTAMP",
        not has_cast_datetime and has_cast_timestamp,
        f"cast_datetime_remaining={has_cast_datetime}, cast_timestamp={has_cast_timestamp}"
    ))

    # 2i. DATE(x) replaced with CAST(x AS DATE)
    has_date_func = bool(re.search(r"\bDATE\s*\(", order_xml, re.IGNORECASE))
    has_cast_date = bool(re.search(r"CAST\s*\([^)]+AS\s+DATE\)", order_xml, re.IGNORECASE))
    checks.append(check(
        "OrderMapper.xml: DATE(x) replaced with CAST(x AS DATE)",
        not has_date_func and has_cast_date,
        f"date_func_remaining={has_date_func}, cast_date={has_cast_date}"
    ))

    # 2j. deleted = 0 / deleted = 1 replaced with deleted = B'0' / deleted = B'1'
    has_deleted_int = bool(re.search(r"deleted\s*=\s*[01](?!\s*[B'])", order_xml))
    has_deleted_bit = bool(re.search(r"deleted\s*=\s*B'[01]'", order_xml))
    checks.append(check(
        "OrderMapper.xml: deleted = 0/1 replaced with deleted = B'0'/B'1'",
        not has_deleted_int and has_deleted_bit,
        f"deleted_int_remaining={has_deleted_int}, deleted_bit_present={has_deleted_bit}"
    ))

except Exception as e:
    checks.append(check("OrderMapper.xml: File readable", False, str(e)))

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 3: OrderDetailMapper.xml checks
# ══════════════════════════════════════════════════════════════════════════════
try:
    detail_xml = load_file(detail_xml_path)

    # 3a. GROUP BY: non-aggregated columns (flag_col, status_col) wrapped in aggregate
    # Check that flag_col and status_col are either in GROUP BY or wrapped in MAX/MIN/etc.
    has_raw_flag_col = bool(re.search(r"SELECT[^;]*\bd\.flag_col\b(?!\s*,?\s*(?:FROM|WHERE|GROUP|ORDER|LIMIT|HAVING))[^;]*GROUP BY o\.id", detail_xml, re.IGNORECASE | re.DOTALL))
    # Better: check that selectOrderSummary query uses MAX/MIN on flag_col and status_col
    summary_block = re.search(r'id="selectOrderSummary".*?</select>', detail_xml, re.IGNORECASE | re.DOTALL)
    if summary_block:
        sb = summary_block.group(0)
        flag_aggregated = bool(re.search(r"(?:MAX|MIN|SUM|COUNT|BOOL_OR)\s*\(\s*d\.flag_col\s*\)", sb, re.IGNORECASE))
        status_aggregated = bool(re.search(r"(?:MAX|MIN|SUM|COUNT|BOOL_OR)\s*\(\s*d\.status_col\s*\)", sb, re.IGNORECASE))
        checks.append(check(
            "OrderDetailMapper.xml: flag_col aggregated in GROUP BY query",
            flag_aggregated,
            f"flag_col properly aggregated: {flag_aggregated}. Snippet: {sb[:300]}"
        ))
        checks.append(check(
            "OrderDetailMapper.xml: status_col aggregated in GROUP BY query",
            status_aggregated,
            f"status_col properly aggregated: {status_aggregated}. Snippet: {sb[:300]}"
        ))
    else:
        checks.append(check("OrderDetailMapper.xml: selectOrderSummary block found", False, "Could not locate selectOrderSummary"))
        checks.append(check("OrderDetailMapper.xml: status_col aggregated", False, "Block not found"))

    # 3b. INSERT IGNORE replaced in detail mapper
    has_insert_ignore_d = "INSERT IGNORE" in detail_xml.upper()
    has_conflict_d = bool(re.search(r"ON CONFLICT.*DO NOTHING", detail_xml, re.IGNORECASE | re.DOTALL))
    checks.append(check(
        "OrderDetailMapper.xml: INSERT IGNORE replaced with ON CONFLICT DO NOTHING",
        not has_insert_ignore_d and has_conflict_d,
        f"insert_ignore={has_insert_ignore_d}, on_conflict={has_conflict_d}"
    ))

    # 3c. UPDATE JOIN converted in detail mapper
    has_update_join_d = bool(re.search(r"UPDATE\s+\w+\s+\w+\s+INNER JOIN", detail_xml, re.IGNORECASE))
    has_update_from_d = bool(re.search(r"UPDATE\s+\w+\s+\w*\s*SET\s+[^;]+FROM\s+\w+", detail_xml, re.IGNORECASE | re.DOTALL))
    checks.append(check(
        "OrderDetailMapper.xml: UPDATE JOIN converted to UPDATE FROM WHERE",
        not has_update_join_d and has_update_from_d,
        f"update_join_remaining={has_update_join_d}, update_from={has_update_from_d}"
    ))

    # 3d. deleted = 0/1 BIT fix in detail mapper
    has_deleted_int_d = bool(re.search(r"deleted\s*=\s*[01](?!\s*[B'])", detail_xml))
    has_deleted_bit_d = bool(re.search(r"deleted\s*=\s*B'[01]'", detail_xml))
    checks.append(check(
        "OrderDetailMapper.xml: deleted = 0/1 replaced with B'0'/B'1'",
        not has_deleted_int_d and has_deleted_bit_d,
        f"deleted_int={has_deleted_int_d}, deleted_bit={has_deleted_bit_d}"
    ))

    # 3e. flag_col = 1 (BIT comparison) fixed
    has_flag_int = bool(re.search(r"flag_col\s*=\s*1(?!\s*[B'])", detail_xml))
    has_flag_bit = bool(re.search(r"flag_col\s*=\s*B'1'", detail_xml))
    checks.append(check(
        "OrderDetailMapper.xml: flag_col = 1 replaced with flag_col = B'1'",
        not has_flag_int and has_flag_bit,
        f"flag_int={has_flag_int}, flag_bit={has_flag_bit}"
    ))

except Exception as e:
    checks.append(check("OrderDetailMapper.xml: File readable", False, str(e)))

# ══════════════════════════════════════════════════════════════════════════════
# BLOCK 4: CREATE SEQUENCE SQL file
# ══════════════════════════════════════════════════════════════════════════════
try:
    seq_sql = find_sequence_sql(workspace)
    if seq_sql is None:
        checks.append(check("Sequence SQL file: exists", False, "No .sql file with CREATE SEQUENCE found in workspace"))
        checks.append(check("Sequence SQL: order_seq with correct START WITH", False, "File not found"))
        checks.append(check("Sequence SQL: order_detail_seq with correct START WITH", False, "File not found"))
    else:
        checks.append(check("Sequence SQL file: exists", True, "Found SQL file with CREATE SEQUENCE"))

        # orders.max_id=10500 → START WITH must be >= 10501
        order_seq_match = re.search(
            r"CREATE\s+SEQUENCE\s+\S*order_seq\b[^;]*START\s+WITH\s+(\d+)",
            seq_sql, re.IGNORECASE | re.DOTALL
        )
        if order_seq_match:
            order_start = int(order_seq_match.group(1))
            checks.append(check(
                "Sequence SQL: order_seq START WITH > 10500",
                order_start > 10500,
                f"order_seq START WITH = {order_start}, must be > 10500 (max_id=10500)"
            ))
        else:
            checks.append(check(
                "Sequence SQL: order_seq START WITH > 10500",
                False,
                f"Could not find CREATE SEQUENCE for order_seq with START WITH clause. SQL snippet: {seq_sql[:500]}"
            ))

        # order_detail.max_id=87300 → START WITH must be >= 87301
        detail_seq_match = re.search(
            r"CREATE\s+SEQUENCE\s+\S*order_detail_seq\b[^;]*START\s+WITH\s+(\d+)",
            seq_sql, re.IGNORECASE | re.DOTALL
        )
        if detail_seq_match:
            detail_start = int(detail_seq_match.group(1))
            checks.append(check(
                "Sequence SQL: order_detail_seq START WITH > 87300",
                detail_start > 87300,
                f"order_detail_seq START WITH = {detail_start}, must be > 87300 (max_id=87300)"
            ))
        else:
            checks.append(check(
                "Sequence SQL: order_detail_seq START WITH > 87300",
                False,
                f"Could not find CREATE SEQUENCE for order_detail_seq with START WITH clause. SQL snippet: {seq_sql[:500]}"
            ))

except Exception as e:
    checks.append(check("Sequence SQL: evaluation error", False, str(e)))

# ── Final scoring ──────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4) if total > 0 else 0.0
all_passed = passed_count == total

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2, ensure_ascii=False))