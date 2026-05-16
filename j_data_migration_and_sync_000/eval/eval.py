import sys
import json
import csv
import os
from pathlib import Path

def load_json_safe(path):
    with open(path, "r") as f:
        return json.load(f)

def load_csv_safe(path):
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames

def run_checks(workspace):
    checks = []
    passed_all = True

    # -------------------------------------------------------
    # PART 1: Find and validate the merged sales CSV
    # -------------------------------------------------------

    # Expected: a single CSV with all 8 sales rows (no duplicate headers),
    # enriched with region columns (region_name, country, sales_manager)

    enriched_csv_candidates = list(Path(workspace).rglob("enriched_sales.csv"))
    
    check_enriched_exists = {
        "name": "enriched_sales.csv exists",
        "passed": False,
        "detail": ""
    }
    if not enriched_csv_candidates:
        check_enriched_exists["detail"] = "File 'enriched_sales.csv' not found anywhere in workspace."
        checks.append(check_enriched_exists)
        passed_all = False
        # Can't do further checks on this file
        enriched_rows = None
        enriched_fields = None
    else:
        enriched_csv_path = enriched_csv_candidates[0]
        check_enriched_exists["passed"] = True
        check_enriched_exists["detail"] = f"Found at {enriched_csv_path}"
        checks.append(check_enriched_exists)
        try:
            enriched_rows, enriched_fields = load_csv_safe(enriched_csv_path)
        except Exception as e:
            enriched_rows = None
            enriched_fields = None
            checks.append({
                "name": "enriched_sales.csv is valid CSV",
                "passed": False,
                "detail": f"Parse error: {e}"
            })
            passed_all = False

    # Check row count (all 8 sales rows)
    check_row_count = {
        "name": "enriched_sales.csv has exactly 8 data rows",
        "passed": False,
        "detail": ""
    }
    if enriched_rows is not None:
        if len(enriched_rows) == 8:
            check_row_count["passed"] = True
            check_row_count["detail"] = f"Row count: {len(enriched_rows)}"
        else:
            check_row_count["detail"] = f"Expected 8 rows, got {len(enriched_rows)}. Duplicate headers or missing data likely."
            passed_all = False
    else:
        check_row_count["detail"] = "Could not check: file missing or unparseable."
        passed_all = False
    checks.append(check_row_count)

    # Check no duplicate header rows (a naive cat would produce this)
    check_no_dup_headers = {
        "name": "enriched_sales.csv contains no duplicate header rows in data",
        "passed": False,
        "detail": ""
    }
    if enriched_rows is not None:
        dup_header_rows = [r for r in enriched_rows if r.get("id", "").strip().lower() == "id"]
        if len(dup_header_rows) == 0:
            check_no_dup_headers["passed"] = True
            check_no_dup_headers["detail"] = "No duplicate header rows found in data."
        else:
            check_no_dup_headers["detail"] = f"Found {len(dup_header_rows)} duplicate header row(s) in data body."
            passed_all = False
    else:
        check_no_dup_headers["detail"] = "Cannot check: file missing or unparseable."
        passed_all = False
    checks.append(check_no_dup_headers)

    # Check all original sales IDs are present
    expected_ids = {"S001", "S002", "S003", "S004", "S005", "S006", "S007", "S008"}
    check_all_ids = {
        "name": "enriched_sales.csv contains all 8 sale IDs (S001-S008)",
        "passed": False,
        "detail": ""
    }
    if enriched_rows is not None:
        found_ids = {r.get("id", "").strip() for r in enriched_rows}
        missing = expected_ids - found_ids
        if not missing:
            check_all_ids["passed"] = True
            check_all_ids["detail"] = f"All IDs found: {sorted(found_ids)}"
        else:
            check_all_ids["detail"] = f"Missing IDs: {sorted(missing)}"
            passed_all = False
    else:
        check_all_ids["detail"] = "Cannot check: file missing or unparseable."
        passed_all = False
    checks.append(check_all_ids)

    # Check enrichment columns exist
    check_enrichment_cols = {
        "name": "enriched_sales.csv has region_name, country, sales_manager columns",
        "passed": False,
        "detail": ""
    }
    if enriched_fields is not None:
        required_cols = {"region_name", "country", "sales_manager"}
        fields_set = set(f.strip() for f in enriched_fields)
        missing_cols = required_cols - fields_set
        if not missing_cols:
            check_enrichment_cols["passed"] = True
            check_enrichment_cols["detail"] = f"Columns present: {sorted(fields_set)}"
        else:
            check_enrichment_cols["detail"] = f"Missing columns: {sorted(missing_cols)}"
            passed_all = False
    else:
        check_enrichment_cols["detail"] = "Cannot check: file missing or unparseable."
        passed_all = False
    checks.append(check_enrichment_cols)

    # Check join correctness: S001 (R01) -> North-East
    check_join_values = {
        "name": "Join correctness: S001 maps to region_name=North-East",
        "passed": False,
        "detail": ""
    }
    if enriched_rows is not None:
        s001_rows = [r for r in enriched_rows if r.get("id", "").strip() == "S001"]
        if s001_rows:
            val = s001_rows[0].get("region_name", "").strip()
            if val == "North-East":
                check_join_values["passed"] = True
                check_join_values["detail"] = f"S001 region_name = '{val}' ✓"
            else:
                check_join_values["detail"] = f"S001 region_name = '{val}', expected 'North-East'"
                passed_all = False
        else:
            check_join_values["detail"] = "S001 not found in enriched file."
            passed_all = False
    else:
        check_join_values["detail"] = "Cannot check: file missing or unparseable."
        passed_all = False
    checks.append(check_join_values)

    # Check another join: S004 (R03) -> South-Central
    check_join_values2 = {
        "name": "Join correctness: S004 maps to region_name=South-Central",
        "passed": False,
        "detail": ""
    }
    if enriched_rows is not None:
        s004_rows = [r for r in enriched_rows if r.get("id", "").strip() == "S004"]
        if s004_rows:
            val = s004_rows[0].get("region_name", "").strip()
            if val == "South-Central":
                check_join_values2["passed"] = True
                check_join_values2["detail"] = f"S004 region_name = '{val}' ✓"
            else:
                check_join_values2["detail"] = f"S004 region_name = '{val}', expected 'South-Central'"
                passed_all = False
        else:
            check_join_values2["detail"] = "S004 not found in enriched file."
            passed_all = False
    else:
        check_join_values2["detail"] = "Cannot check: file missing or unparseable."
        passed_all = False
    checks.append(check_join_values2)

    # -------------------------------------------------------
    # PART 2: Find and validate the deep-merged config JSON
    # -------------------------------------------------------

    merged_json_candidates = list(Path(workspace).rglob("merged_config.json"))

    check_merged_json_exists = {
        "name": "merged_config.json exists",
        "passed": False,
        "detail": ""
    }
    if not merged_json_candidates:
        check_merged_json_exists["detail"] = "File 'merged_config.json' not found anywhere in workspace."
        checks.append(check_merged_json_exists)
        passed_all = False
        merged_cfg = None
    else:
        merged_json_path = merged_json_candidates[0]
        check_merged_json_exists["passed"] = True
        check_merged_json_exists["detail"] = f"Found at {merged_json_path}"
        checks.append(check_merged_json_exists)
        try:
            merged_cfg = load_json_safe(merged_json_path)
        except Exception as e:
            merged_cfg = None
            checks.append({
                "name": "merged_config.json is valid JSON",
                "passed": False,
                "detail": f"Parse error: {e}"
            })
            passed_all = False

    # Check top-level keys from all three configs are present
    check_top_keys = {
        "name": "merged_config.json has all top-level keys: service_name, version, database, features, logging, deployment",
        "passed": False,
        "detail": ""
    }
    if merged_cfg is not None:
        required_keys = {"service_name", "version", "database", "features", "logging", "deployment"}
        present = set(merged_cfg.keys())
        missing_k = required_keys - present
        if not missing_k:
            check_top_keys["passed"] = True
            check_top_keys["detail"] = f"All required top-level keys present: {sorted(present)}"
        else:
            check_top_keys["detail"] = f"Missing top-level keys: {sorted(missing_k)}"
            passed_all = False
    else:
        check_top_keys["detail"] = "Cannot check: file missing or unparseable."
        passed_all = False
    checks.append(check_top_keys)

    # Deep merge check: database must have host (from A), port (from B overrides A), name (from B), pool_size (from A)
    # With deep merge: database.host = "db-primary.internal", database.port = 5433, database.name = "analytics_db", database.pool_size = 10
    check_deep_database = {
        "name": "Deep merge: database has host, port=5433, name='analytics_db', pool_size=10",
        "passed": False,
        "detail": ""
    }
    if merged_cfg is not None and isinstance(merged_cfg.get("database"), dict):
        db = merged_cfg["database"]
        issues = []
        if db.get("host") != "db-primary.internal":
            issues.append(f"host='{db.get('host')}' (expected 'db-primary.internal')")
        if db.get("port") != 5433:
            issues.append(f"port={db.get('port')} (expected 5433, shallow merge would give 5432)")
        if db.get("name") != "analytics_db":
            issues.append(f"name='{db.get('name')}' (expected 'analytics_db')")
        if db.get("pool_size") != 10:
            issues.append(f"pool_size={db.get('pool_size')} (expected 10)")
        if not issues:
            check_deep_database["passed"] = True
            check_deep_database["detail"] = f"database section: {db}"
        else:
            check_deep_database["detail"] = "Issues: " + "; ".join(issues)
            passed_all = False
    else:
        check_deep_database["detail"] = "database key missing or not a dict."
        passed_all = False
    checks.append(check_deep_database)

    # Deep merge check: features must have caching=True (B overrides A), retries=3 (from A), rate_limiting=True (from B), metrics=True (from C)
    check_deep_features = {
        "name": "Deep merge: features has caching=True, retries=3, rate_limiting=True, metrics=True",
        "passed": False,
        "detail": ""
    }
    if merged_cfg is not None and isinstance(merged_cfg.get("features"), dict):
        ft = merged_cfg["features"]
        issues = []
        if ft.get("caching") is not True:
            issues.append(f"caching={ft.get('caching')} (expected True)")
        if ft.get("retries") != 3:
            issues.append(f"retries={ft.get('retries')} (expected 3)")
        if ft.get("rate_limiting") is not True:
            issues.append(f"rate_limiting={ft.get('rate_limiting')} (expected True)")
        if ft.get("metrics") is not True:
            issues.append(f"metrics={ft.get('metrics')} (expected True)")
        if not issues:
            check_deep_features["passed"] = True
            check_deep_features["detail"] = f"features section: {ft}"
        else:
            check_deep_features["detail"] = "Issues: " + "; ".join(issues)
            passed_all = False
    else:
        check_deep_features["detail"] = "features key missing or not a dict."
        passed_all = False
    checks.append(check_deep_features)

    # Deep merge check: logging must have level="INFO", format="json" (from B), destination="cloudwatch" (from C)
    check_deep_logging = {
        "name": "Deep merge: logging has level='INFO', format='json', destination='cloudwatch'",
        "passed": False,
        "detail": ""
    }
    if merged_cfg is not None and isinstance(merged_cfg.get("logging"), dict):
        lg = merged_cfg["logging"]
        issues = []
        if lg.get("level") != "INFO":
            issues.append(f"level='{lg.get('level')}' (expected 'INFO')")
        if lg.get("format") != "json":
            issues.append(f"format='{lg.get('format')}' (expected 'json')")
        if lg.get("destination") != "cloudwatch":
            issues.append(f"destination='{lg.get('destination')}' (expected 'cloudwatch')")
        if not issues:
            check_deep_logging["passed"] = True
            check_deep_logging["detail"] = f"logging section: {lg}"
        else:
            check_deep_logging["detail"] = "Issues: " + "; ".join(issues)
            passed_all = False
    else:
        check_deep_logging["detail"] = "logging key missing or not a dict."
        passed_all = False
    checks.append(check_deep_logging)

    # deployment from C
    check_deep_deployment = {
        "name": "Deep merge: deployment has region='us-east-1', replicas=3",
        "passed": False,
        "detail": ""
    }
    if merged_cfg is not None and isinstance(merged_cfg.get("deployment"), dict):
        dp = merged_cfg["deployment"]
        issues = []
        if dp.get("region") != "us-east-1":
            issues.append(f"region='{dp.get('region')}' (expected 'us-east-1')")
        if dp.get("replicas") != 3:
            issues.append(f"replicas={dp.get('replicas')} (expected 3)")
        if not issues:
            check_deep_deployment["passed"] = True
            check_deep_deployment["detail"] = f"deployment section: {dp}"
        else:
            check_deep_deployment["detail"] = "Issues: " + "; ".join(issues)
            passed_all = False
    else:
        check_deep_deployment["detail"] = "deployment key missing or not a dict."
        passed_all = False
    checks.append(check_deep_deployment)

    # -------------------------------------------------------
    # Compute score
    # -------------------------------------------------------
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)

    return {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))