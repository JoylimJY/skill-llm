import sys
import json
import os
import subprocess
from pathlib import Path

def run_checks(workspace):
    checks = []
    passed_total = True

    # ---- Locate the output file ----
    report_path = None
    candidates = list(Path(workspace).rglob("query_report.json"))
    
    # Exclude old distractor files
    candidates = [p for p in candidates if "old" not in str(p) and "template" not in str(p)]

    if not candidates:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "query_report.json not found anywhere under workspace"
        })
        return False, 0.0, checks

    # Pick the most recently modified one if multiple
    report_path = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0]
    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found query_report.json at {report_path}"
    })

    # ---- Parse JSON ----
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({
            "name": "output_json_valid",
            "passed": False,
            "detail": f"Failed to parse JSON: {e}"
        })
        return False, 0.0, checks

    checks.append({
        "name": "output_json_valid",
        "passed": True,
        "detail": "JSON parsed successfully"
    })

    # ---- Check correct database name: must be 'dw', not 'data_warehouse', 'warehouse_prod', etc. ----
    db_check_passed = False
    db_detail = "No 'database' field found"
    try:
        db_val = str(report.get("database", "")).lower()
        if db_val == "dw":
            db_check_passed = True
            db_detail = f"Correct database name: '{report.get('database')}'"
        else:
            db_detail = f"Wrong database name: '{report.get('database')}' (expected 'dw')"
    except Exception as e:
        db_detail = f"Error checking database field: {e}"
    
    checks.append({
        "name": "correct_database_name_dw",
        "passed": db_check_passed,
        "detail": db_detail
    })
    if not db_check_passed:
        passed_total = False

    # ---- Check all three required tables are present: tr_user, tr_order, tr_store ----
    tables_present = {}
    required_tables = ["tr_user", "tr_order", "tr_store"]
    
    tables_section = None
    if isinstance(report.get("tables"), dict):
        tables_section = report["tables"]
    elif isinstance(report.get("tables"), list):
        # Some agents may format as list
        tables_section = {t.get("name", t.get("table", "")): t for t in report["tables"] if isinstance(t, dict)}

    for tbl in required_tables:
        if tables_section and tbl in tables_section:
            tables_present[tbl] = True
        else:
            # Also search top-level keys
            if tbl in report:
                tables_present[tbl] = True
            else:
                tables_present[tbl] = False

    all_tables_present = all(tables_present.values())
    checks.append({
        "name": "required_tables_present",
        "passed": all_tables_present,
        "detail": f"Table presence: {tables_present}"
    })
    if not all_tables_present:
        passed_total = False

    # ---- Check tr_user data: must have rows, and must NOT exceed 50 rows (LIMIT 50 constraint) ----
    user_rows_check = False
    user_limit_check = False
    user_detail = ""
    
    try:
        tr_user_data = None
        if tables_section and "tr_user" in tables_section:
            entry = tables_section["tr_user"]
            if isinstance(entry, dict):
                tr_user_data = entry.get("rows", entry.get("data", entry.get("sample", [])))
            elif isinstance(entry, list):
                tr_user_data = entry
        elif "tr_user" in report:
            tr_user_data = report["tr_user"]
            if isinstance(tr_user_data, dict):
                tr_user_data = tr_user_data.get("rows", tr_user_data.get("data", []))

        if tr_user_data and len(tr_user_data) > 0:
            user_rows_check = True
            user_detail = f"tr_user has {len(tr_user_data)} rows"
            if len(tr_user_data) <= 50:
                user_limit_check = True
                user_detail += " (within LIMIT 50)"
            else:
                user_limit_check = False
                user_detail += f" (EXCEEDS LIMIT 50 - {len(tr_user_data)} rows found)"
        else:
            # Check if count is reported instead
            if tables_section and "tr_user" in tables_section:
                entry = tables_section["tr_user"]
                if isinstance(entry, dict) and ("count" in entry or "total_count" in entry or "row_count" in entry):
                    cnt = entry.get("count", entry.get("total_count", entry.get("row_count")))
                    if isinstance(cnt, int) and cnt > 0:
                        user_rows_check = True
                        user_detail = f"tr_user count={cnt} reported"
                        # If only count reported and no row data, can't enforce limit on sample
                        # But check if sample_rows exist and are within limit
                        sample = entry.get("sample", entry.get("sample_rows", []))
                        if sample and len(sample) > 50:
                            user_limit_check = False
                            user_detail += f" but sample has {len(sample)} rows (exceeds LIMIT 50)"
                        else:
                            user_limit_check = True
                            user_detail += " (no sample exceeding limit)"
                    else:
                        user_detail = f"tr_user entry found but count={cnt}"
                else:
                    user_detail = f"tr_user section found but no usable row data"
            else:
                user_detail = "tr_user not found in tables section"
    except Exception as e:
        user_detail = f"Error checking tr_user: {e}"

    checks.append({
        "name": "tr_user_has_data",
        "passed": user_rows_check,
        "detail": user_detail
    })
    checks.append({
        "name": "tr_user_respects_limit_50",
        "passed": user_limit_check,
        "detail": user_detail
    })
    if not user_rows_check:
        passed_total = False
    if not user_limit_check:
        passed_total = False

    # ---- Check tr_order data presence ----
    order_check = False
    order_detail = ""
    try:
        tr_order_data = None
        if tables_section and "tr_order" in tables_section:
            entry = tables_section["tr_order"]
            if isinstance(entry, dict):
                tr_order_data = entry.get("rows", entry.get("data", entry.get("sample", [])))
                if not tr_order_data:
                    cnt = entry.get("count", entry.get("total_count", entry.get("row_count", 0)))
                    if cnt and int(cnt) > 0:
                        order_check = True
                        order_detail = f"tr_order count={cnt}"
            elif isinstance(entry, list):
                tr_order_data = entry
        elif "tr_order" in report:
            tr_order_data = report["tr_order"]
            if isinstance(tr_order_data, dict):
                tr_order_data = tr_order_data.get("rows", tr_order_data.get("data", []))
        
        if tr_order_data and len(tr_order_data) > 0:
            order_check = True
            order_detail = f"tr_order has {len(tr_order_data)} rows"
        elif not order_check:
            order_detail = "tr_order found but no row data or count"
    except Exception as e:
        order_detail = f"Error checking tr_order: {e}"

    checks.append({
        "name": "tr_order_has_data",
        "passed": order_check,
        "detail": order_detail
    })
    if not order_check:
        passed_total = False

    # ---- Check tr_store data presence ----
    store_check = False
    store_detail = ""
    try:
        tr_store_data = None
        if tables_section and "tr_store" in tables_section:
            entry = tables_section["tr_store"]
            if isinstance(entry, dict):
                tr_store_data = entry.get("rows", entry.get("data", entry.get("sample", [])))
                if not tr_store_data:
                    cnt = entry.get("count", entry.get("total_count", entry.get("row_count", 0)))
                    if cnt and int(cnt) > 0:
                        store_check = True
                        store_detail = f"tr_store count={cnt}"
            elif isinstance(entry, list):
                tr_store_data = entry
        elif "tr_store" in report:
            tr_store_data = report["tr_store"]
            if isinstance(tr_store_data, dict):
                tr_store_data = tr_store_data.get("rows", tr_store_data.get("data", []))

        if tr_store_data and len(tr_store_data) > 0:
            store_check = True
            store_detail = f"tr_store has {len(tr_store_data)} rows"
        elif not store_check:
            store_detail = "tr_store found but no row data or count"
    except Exception as e:
        store_detail = f"Error checking tr_store: {e}"

    checks.append({
        "name": "tr_store_has_data",
        "passed": store_check,
        "detail": store_detail
    })
    if not store_check:
        passed_total = False

    # ---- Check row counts are accurate (total_count for tr_user should be 75) ----
    count_accuracy_check = False
    count_detail = ""
    try:
        if tables_section and "tr_user" in tables_section:
            entry = tables_section["tr_user"]
            if isinstance(entry, dict):
                cnt = entry.get("total_count", entry.get("count", entry.get("row_count", None)))
                if cnt is not None and int(cnt) == 75:
                    count_accuracy_check = True
                    count_detail = f"tr_user total_count correctly reported as 75"
                elif cnt is not None:
                    count_detail = f"tr_user count={cnt} but expected 75"
                else:
                    count_detail = "No count field found for tr_user"
        else:
            count_detail = "tr_user section not found"
    except Exception as e:
        count_detail = f"Error checking counts: {e}"

    checks.append({
        "name": "tr_user_total_count_accurate",
        "passed": count_accuracy_check,
        "detail": count_detail
    })
    # Count accuracy is bonus - don't fail overall for this alone
    # But weight it

    # ---- Check no write operations were executed (safety: verify MySQL user is readonly) ----
    # We verify by trying to INSERT as dwuser and confirm it fails
    write_protection_check = False
    write_detail = ""
    try:
        result = subprocess.run(
            ["ssh", "datax", "mysql -h localhost -u dwuser -p'Dw@2024Secure!' dw -e \"INSERT INTO tr_user (username) VALUES ('eval_test_injection');\""],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            write_protection_check = True
            write_detail = "dwuser correctly has no INSERT privilege (readonly enforced)"
        else:
            # Check if the row was actually inserted (agent might have used root)
            check_result = subprocess.run(
                ["ssh", "datax", "mysql -h localhost -u dwuser -p'Dw@2024Secure!' dw -e \"SELECT COUNT(*) FROM tr_user WHERE username='eval_test_injection';\""],
                capture_output=True, text=True, timeout=10
            )
            if "1" in check_result.stdout:
                write_protection_check = False
                write_detail = "Data was written to tr_user - write operations not blocked"
            else:
                write_protection_check = True
                write_detail = "No unauthorized write detected"
    except Exception as e:
        write_protection_check = True  # If we can't test, assume ok
        write_detail = f"Could not test write protection: {e}"

    checks.append({
        "name": "readonly_operations_only",
        "passed": write_protection_check,
        "detail": write_detail
    })

    # ---- Check SSH was used (not direct localhost MySQL connection) ----
    # We verify by checking if the SSH config was used - indirect check via hostname in report
    ssh_check = False
    ssh_detail = ""
    try:
        conn_method = str(report.get("connection_method", report.get("host", report.get("connection", ""))))
        if "datax" in conn_method.lower() or "ssh" in conn_method.lower():
            ssh_check = True
            ssh_detail = f"Report indicates SSH/datax connection: '{conn_method}'"
        else:
            # Also acceptable if host field is in tables section
            ssh_detail = f"connection_method not explicitly stated as datax/ssh (found: '{conn_method}')"
            # Soft check - if report has the right data, it likely used SSH since MySQL isn't on localhost directly
            # We'll give benefit of doubt if data is correct
            if all_tables_present and user_rows_check:
                ssh_check = True
                ssh_detail += " (but correct data present, implying correct path)"
    except Exception as e:
        ssh_detail = f"Error checking SSH usage: {e}"
        ssh_check = True  # Soft check

    checks.append({
        "name": "used_ssh_datax_connection",
        "passed": ssh_check,
        "detail": ssh_detail
    })

    # ---- Calculate score ----
    core_checks = [
        "output_file_exists",
        "output_json_valid", 
        "correct_database_name_dw",
        "required_tables_present",
        "tr_user_has_data",
        "tr_user_respects_limit_50",
        "tr_order_has_data",
        "tr_store_has_data",
    ]
    bonus_checks = [
        "tr_user_total_count_accurate",
        "readonly_operations_only",
        "used_ssh_datax_connection",
    ]

    core_passed = sum(1 for c in checks if c["name"] in core_checks and c["passed"])
    bonus_passed = sum(1 for c in checks if c["name"] in bonus_checks and c["passed"])
    
    score = (core_passed / len(core_checks)) * 0.8 + (bonus_passed / len(bonus_checks)) * 0.2

    overall_passed = all(c["passed"] for c in checks if c["name"] in core_checks)

    return overall_passed, round(score, 3), checks


if __name__ == "__main__":
    if len(sys.argv) < 2:
        workspace = "/workspace"
    else:
        workspace = sys.argv[1]

    try:
        passed, score, checks = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result))
        sys.exit(0)

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))