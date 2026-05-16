import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    
    # ---- Locate the two output files ----
    # 1. mapping_catalog.json
    catalog_files = list(Path(workspace).rglob("mapping_catalog.json"))
    # 2. mapping_report.md
    report_files = list(Path(workspace).rglob("mapping_report.md"))

    # CHECK 1: mapping_catalog.json exists
    catalog_exists = len(catalog_files) > 0
    checks.append({
        "name": "mapping_catalog.json exists",
        "passed": catalog_exists,
        "detail": f"Found at: {catalog_files[0]}" if catalog_exists else "File not found anywhere in workspace"
    })

    # CHECK 2: mapping_report.md exists
    report_exists = len(report_files) > 0
    checks.append({
        "name": "mapping_report.md exists",
        "passed": report_exists,
        "detail": f"Found at: {report_files[0]}" if report_exists else "File not found anywhere in workspace"
    })

    catalog_data = []
    if catalog_exists:
        try:
            with open(catalog_files[0]) as f:
                catalog_data = json.load(f)
        except Exception as e:
            checks.append({
                "name": "mapping_catalog.json is valid JSON",
                "passed": False,
                "detail": str(e)
            })
            catalog_data = []
    
    if catalog_data:
        checks.append({
            "name": "mapping_catalog.json is valid JSON",
            "passed": True,
            "detail": f"Loaded {len(catalog_data)} entries"
        })

    # CHECK 3: Target ontology is MASTERFORMAT (not IFC)
    # All auto-generated mappings should target masterformat
    try:
        mf_targets = [e for e in catalog_data if e.get("target_ontology") == "masterformat"]
        ifc_targets = [e for e in catalog_data if e.get("target_ontology") == "ifc"]
        # There should be masterformat entries and the manual ones should be masterformat
        has_masterformat = len(mf_targets) >= 2
        checks.append({
            "name": "Catalog contains MasterFormat target mappings",
            "passed": has_masterformat,
            "detail": f"Found {len(mf_targets)} masterformat entries, {len(ifc_targets)} ifc entries. Need >=2 masterformat."
        })
    except Exception as e:
        checks.append({
            "name": "Catalog contains MasterFormat target mappings",
            "passed": False,
            "detail": str(e)
        })

    # CHECK 4: Manual mapping for "trade_code" -> "09" (Finishes), relation=related, created_by=manual
    try:
        trade_code_mappings = [
            e for e in catalog_data
            if e.get("source") == "trade_code"
            and e.get("target") == "09"
            and e.get("target_ontology") == "masterformat"
        ]
        trade_code_ok = len(trade_code_mappings) > 0
        detail = f"Found: {trade_code_mappings}" if trade_code_ok else "No matching entry for trade_code->09 in masterformat"
        checks.append({
            "name": "Manual mapping: trade_code -> MasterFormat 09",
            "passed": trade_code_ok,
            "detail": detail
        })
    except Exception as e:
        checks.append({
            "name": "Manual mapping: trade_code -> MasterFormat 09",
            "passed": False,
            "detail": str(e)
        })

    # CHECK 5: Manual mapping for "project_ref" -> "03" (Concrete), relation=related
    try:
        project_ref_mappings = [
            e for e in catalog_data
            if e.get("source") == "project_ref"
            and e.get("target") == "03"
            and e.get("target_ontology") == "masterformat"
        ]
        project_ref_ok = len(project_ref_mappings) > 0
        detail = f"Found: {project_ref_mappings}" if project_ref_ok else "No matching entry for project_ref->03 in masterformat"
        checks.append({
            "name": "Manual mapping: project_ref -> MasterFormat 03",
            "passed": project_ref_ok,
            "detail": detail
        })
    except Exception as e:
        checks.append({
            "name": "Manual mapping: project_ref -> MasterFormat 03",
            "passed": False,
            "detail": str(e)
        })

    # CHECK 6: Both manual mappings have relation=related
    try:
        manual_related = [
            e for e in catalog_data
            if e.get("source") in ("trade_code", "project_ref")
            and e.get("relation") == "related"
        ]
        both_related = len(manual_related) >= 2
        checks.append({
            "name": "Manual mappings use RelationType.RELATED",
            "passed": both_related,
            "detail": f"Found {len(manual_related)} entries with relation=related among manual fields"
        })
    except Exception as e:
        checks.append({
            "name": "Manual mappings use RelationType.RELATED",
            "passed": False,
            "detail": str(e)
        })

    # CHECK 7: The catalog contains auto-mapped fields from legacy schema
    # (at least concrete/masonry/plumbing type mappings)
    try:
        all_sources = {e.get("source") for e in catalog_data}
        # Some of the schema sample values should appear as sources in auto-mappings
        # OR field names should appear. The map_schema uses sample values as source_concept.
        # After create_mapping, manual ones use field names as source.
        # We check that at least some MasterFormat entries exist beyond the 2 manual ones
        auto_mf = [
            e for e in catalog_data
            if e.get("target_ontology") == "masterformat"
            and e.get("source") not in ("trade_code", "project_ref")
        ]
        has_auto = len(auto_mf) >= 1
        checks.append({
            "name": "Catalog contains auto-mapped MasterFormat entries beyond manual ones",
            "passed": has_auto,
            "detail": f"Found {len(auto_mf)} auto-mapped masterformat entries. Sources: {[e.get('source') for e in auto_mf]}"
        })
    except Exception as e:
        checks.append({
            "name": "Catalog contains auto-mapped MasterFormat entries beyond manual ones",
            "passed": False,
            "detail": str(e)
        })

    # CHECK 8: Markdown report contains expected sections
    report_text = ""
    if report_exists:
        try:
            with open(report_files[0]) as f:
                report_text = f.read()
        except Exception as e:
            report_text = ""

    try:
        has_summary = "## Summary" in report_text
        has_coverage = "Coverage" in report_text
        has_mappings_section = "## Mappings" in report_text
        has_total_fields = "Total Fields" in report_text
        report_structure_ok = has_summary and has_coverage and has_mappings_section and has_total_fields
        checks.append({
            "name": "Markdown report has required structure (Summary, Coverage, Mappings)",
            "passed": report_structure_ok,
            "detail": f"summary={has_summary}, coverage={has_coverage}, mappings_section={has_mappings_section}, total_fields={has_total_fields}"
        })
    except Exception as e:
        checks.append({
            "name": "Markdown report has required structure",
            "passed": False,
            "detail": str(e)
        })

    # CHECK 9: Report reflects correct total_fields count (9 fields in the schema)
    try:
        import re
        match = re.search(r"\*\*Total Fields:\*\*\s*(\d+)", report_text)
        if match:
            total = int(match.group(1))
            # The schema has 9 fields
            total_ok = total == 9
            checks.append({
                "name": "Report total_fields == 9 (correct schema field count)",
                "passed": total_ok,
                "detail": f"Report says Total Fields: {total}, expected 9"
            })
        else:
            checks.append({
                "name": "Report total_fields == 9 (correct schema field count)",
                "passed": False,
                "detail": "Could not find 'Total Fields' count in report markdown"
            })
    except Exception as e:
        checks.append({
            "name": "Report total_fields == 9 (correct schema field count)",
            "passed": False,
            "detail": str(e)
        })

    # CHECK 10: Catalog is a JSON array (not an object/dict), as export_mappings produces a list
    try:
        is_list = isinstance(catalog_data, list)
        checks.append({
            "name": "mapping_catalog.json is a JSON array (correct export_mappings format)",
            "passed": is_list,
            "detail": f"Type is: {type(catalog_data).__name__}"
        })
    except Exception as e:
        checks.append({
            "name": "mapping_catalog.json is a JSON array",
            "passed": False,
            "detail": str(e)
        })

    # Scoring
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    all_passed = passed_checks == total_checks

    return {
        "passed": all_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))