#!/usr/bin/env python3
"""
Evaluation script for the NL2SQL report generation task.
Checks:
1. schema_linking.json exists and has correct dotted format
2. schema_linking.json covers the necessary tables/columns
3. sales_report.md exists with the correct 5-section Markdown structure
4. Report contains actual numeric data (SQL was executed and results used)
5. SQL in the appendix is a valid SELECT-only query addressing the business question
6. SQL correctly handles order_date as INTEGER (YYYYMMDD format) and filters on 'completed' status
7. SQL handles NULL province (e.g., excludes or uses COALESCE)
8. Results in the report are consistent with actual DB query results
"""

import sys
import json
import re
import sqlite3
from pathlib import Path

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Ground truth from actual DB ───────────────────────────────────────────
    db_path = ws / "data" / "ecommerce.db"
    gt_data = {}
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        # The correct query: join orders with stores, filter completed + June 2024 (YYYYMMDD between 20240601 and 20240630)
        cur.execute("""
            SELECT
                COALESCE(s.province, 'Online/Unknown') AS province,
                ROUND(SUM(o.order_amount), 2) AS total_sales,
                ROUND(AVG(o.order_amount), 2) AS avg_order_value,
                COUNT(o.order_id) AS order_count
            FROM orders o
            JOIN stores s ON o.store_id = s.store_id
            WHERE o.status = 'completed'
              AND o.order_date >= 20240601
              AND o.order_date <= 20240630
            GROUP BY s.province
            ORDER BY total_sales DESC
            LIMIT 5
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        gt_data["top5"] = rows
        gt_data["top_province"] = rows[0]["province"] if rows else None
        gt_data["provinces"] = [r["province"] for r in rows]
    except Exception as e:
        gt_data["error"] = str(e)

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 1: schema_linking.json exists
    # ══════════════════════════════════════════════════════════════════════════
    schema_files = list(ws.rglob("schema_linking.json"))
    schema_file = schema_files[0] if schema_files else None

    if schema_file and schema_file.exists():
        total_score += add_check(
            "schema_linking.json exists",
            True,
            f"Found at {schema_file.relative_to(ws)}"
        )
    else:
        total_score += add_check(
            "schema_linking.json exists",
            False,
            "schema_linking.json not found anywhere in workspace"
        )

    # ── CHECK 2: schema_linking.json format (dotted notation) ─────────────────
    schema_valid_format = False
    schema_content = []
    if schema_file and schema_file.exists():
        try:
            raw = schema_file.read_text(encoding="utf-8")
            schema_content = json.loads(raw)
            # Must be a list of strings
            if isinstance(schema_content, list) and all(isinstance(x, str) for x in schema_content):
                # Each entry must match pattern: word.word.word
                dotted = all(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*$', x) for x in schema_content)
                if dotted and len(schema_content) >= 3:
                    schema_valid_format = True
                    total_score += add_check(
                        "schema_linking.json format: dotted database.table.column",
                        True,
                        f"All {len(schema_content)} entries use correct dotted notation"
                    )
                else:
                    total_score += add_check(
                        "schema_linking.json format: dotted database.table.column",
                        False,
                        f"Entries don't all match 'db.table.col' pattern or too few. Sample: {schema_content[:3]}"
                    )
            else:
                total_score += add_check(
                    "schema_linking.json format: dotted database.table.column",
                    False,
                    f"Expected JSON array of strings, got: {type(schema_content)}"
                )
        except Exception as e:
            total_score += add_check(
                "schema_linking.json format: dotted database.table.column",
                False,
                f"Failed to parse schema_linking.json: {e}"
            )
    else:
        total_score += add_check(
            "schema_linking.json format: dotted database.table.column",
            False,
            "File not found, skipping format check"
        )

    # ── CHECK 3: schema_linking covers required tables ─────────────────────────
    required_tables = {"orders", "stores"}
    if schema_valid_format and schema_content:
        referenced_tables = set()
        for entry in schema_content:
            parts = entry.split(".")
            if len(parts) == 3:
                referenced_tables.add(parts[1])
        covered = required_tables.issubset(referenced_tables)
        total_score += add_check(
            "schema_linking covers orders and stores tables",
            covered,
            f"Referenced tables: {referenced_tables}. Required: {required_tables}"
        )
        # Check that ecommerce is used as the database name
        db_names = set(entry.split(".")[0] for entry in schema_content)
        total_score += add_check(
            "schema_linking uses 'ecommerce' as database prefix",
            "ecommerce" in db_names,
            f"Database prefixes found: {db_names}"
        )
    else:
        total_score += add_check(
            "schema_linking covers orders and stores tables",
            False, "schema_linking.json invalid or missing"
        )
        total_score += add_check(
            "schema_linking uses 'ecommerce' as database prefix",
            False, "schema_linking.json invalid or missing"
        )

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 4: sales_report.md exists
    # ══════════════════════════════════════════════════════════════════════════
    report_files = list(ws.rglob("sales_report.md"))
    report_file = report_files[0] if report_files else None

    if report_file and report_file.exists():
        total_score += add_check(
            "sales_report.md exists",
            True,
            f"Found at {report_file.relative_to(ws)}"
        )
    else:
        total_score += add_check(
            "sales_report.md exists",
            False,
            "sales_report.md not found anywhere in workspace"
        )
        # Can't do further checks
        final_score = total_score / 12.0
        return {
            "passed": final_score >= 0.6,
            "score": round(final_score, 3),
            "checks": checks
        }

    report_text = ""
    try:
        report_text = report_file.read_text(encoding="utf-8")
    except Exception as e:
        total_score += add_check("sales_report.md readable", False, str(e))
        final_score = total_score / 12.0
        return {"passed": False, "score": round(final_score, 3), "checks": checks}

    # ── CHECK 5: Markdown structure — 5 required sections ─────────────────────
    required_sections = {
        "h1_title": r'^#\s+.+',
        "summary": r'^##\s+摘要',
        "analysis": r'^##\s+数据分析',
        "conclusion": r'^##\s+结论与建议',
        "appendix_sql": r'^##\s+附录[：:]\s*SQL',
    }
    lines = report_text.split("\n")
    section_found = {}
    for line in lines:
        for key, pattern in required_sections.items():
            if re.match(pattern, line.strip()):
                section_found[key] = True

    all_sections = len(section_found) == len(required_sections)
    missing = [k for k in required_sections if k not in section_found]
    total_score += add_check(
        "Report has all 5 required sections (H1 title, 摘要, 数据分析, 结论与建议, 附录:SQL)",
        all_sections,
        f"Missing sections: {missing}" if missing else "All sections present"
    )

    # ── CHECK 6: Fenced SQL code block in appendix ─────────────────────────────
    sql_block_match = re.search(r'```sql\s*([\s\S]+?)\s*```', report_text, re.IGNORECASE)
    has_sql_block = bool(sql_block_match)
    total_score += add_check(
        "Report appendix contains fenced ```sql code block",
        has_sql_block,
        "Found ```sql block" if has_sql_block else "No ```sql...``` block found in report"
    )

    # ── CHECK 7: SQL is SELECT-only ────────────────────────────────────────────
    if sql_block_match:
        sql_in_report = sql_block_match.group(1).strip()
        write_ops = re.search(r'\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\b', sql_in_report, re.IGNORECASE)
        is_select_only = not bool(write_ops)
        total_score += add_check(
            "SQL in report is SELECT/WITH only (no write operations)",
            is_select_only,
            f"SQL starts with: {sql_in_report[:80]}" if is_select_only else f"Write operation found: {write_ops.group()}"
        )
        # ── CHECK 8: SQL handles order_date as INTEGER YYYYMMDD ───────────────
        # Must compare to integers (e.g., >= 20240601 or CAST or strftime with cast)
        handles_int_date = bool(
            re.search(r'20240[0-9]{3}', sql_in_report) or  # integer literals like 20240601
            re.search(r'CAST.*order_date', sql_in_report, re.IGNORECASE) or
            re.search(r'order_date.*20240', sql_in_report, re.IGNORECASE)
        )
        total_score += add_check(
            "SQL handles order_date as INTEGER (YYYYMMDD format) correctly",
            handles_int_date,
            f"SQL references order_date with integer comparison: {handles_int_date}"
        )
        # ── CHECK 9: SQL filters on 'completed' status ─────────────────────────
        has_completed_filter = bool(re.search(r"status\s*=\s*['\"]completed['\"]", sql_in_report, re.IGNORECASE))
        total_score += add_check(
            "SQL filters orders by status='completed'",
            has_completed_filter,
            "Found status='completed' filter" if has_completed_filter else "Missing status='completed' filter"
        )
        # ── CHECK 10: SQL joins orders and stores ──────────────────────────────
        has_join = bool(re.search(r'\bJOIN\b.*stores|stores.*\bJOIN\b', sql_in_report, re.IGNORECASE))
        total_score += add_check(
            "SQL joins orders with stores to get province",
            has_join,
            "Found JOIN with stores" if has_join else "No JOIN with stores detected"
        )
    else:
        for check_name in [
            "SQL in report is SELECT/WITH only (no write operations)",
            "SQL handles order_date as INTEGER (YYYYMMDD format) correctly",
            "SQL filters orders by status='completed'",
            "SQL joins orders with stores to get province",
        ]:
            total_score += add_check(check_name, False, "No SQL block found to evaluate")

    # ── CHECK 11: Report contains actual province names from DB ────────────────
    if gt_data.get("top5"):
        found_provinces = []
        # Check if at least 2 of the top 5 real provinces appear in the report
        for row in gt_data["top5"][:5]:
            prov = row["province"]
            if prov and prov in report_text:
                found_provinces.append(prov)
        has_real_data = len(found_provinces) >= 2
        total_score += add_check(
            "Report contains actual province data from DB query (≥2 of top-5 provinces)",
            has_real_data,
            f"Found in report: {found_provinces} out of expected top provinces: {gt_data['provinces']}"
        )
        # ── CHECK 12: Report mentions numerical values (GMV or AOV) ──────────
        has_numbers = bool(re.search(r'\d+[,.]?\d*', report_text))
        has_meaningful_numbers = bool(re.search(r'\d{3,}', report_text))  # at least 3-digit numbers
        total_score += add_check(
            "Report contains meaningful numerical values (sales figures)",
            has_meaningful_numbers,
            "Found multi-digit numbers in report" if has_meaningful_numbers else "Report lacks numeric data from query results"
        )
    else:
        total_score += add_check(
            "Report contains actual province data from DB query",
            False,
            f"Could not verify: DB query error: {gt_data.get('error', 'unknown')}"
        )
        total_score += add_check(
            "Report contains meaningful numerical values (sales figures)",
            False,
            "Could not verify without DB ground truth"
        )

    # ── Final scoring ──────────────────────────────────────────────────────────
    n_checks = 12
    final_score = total_score / n_checks
    passed = final_score >= 0.65  # Must pass at least 8/12 checks

    return {
        "passed": passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))