import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    total_score = 0.0
    max_checks = 6

    # -----------------------------------------------------------------------
    # Check 1: .env file exists with correct configuration
    # -----------------------------------------------------------------------
    env_path = Path(workspace) / ".env"
    env_check = {"name": "env_file_exists_with_correct_config", "passed": False, "detail": ""}
    try:
        if not env_path.exists():
            env_check["detail"] = ".env file not found in workspace root"
        else:
            content = env_path.read_text()
            has_max_rows = False
            max_rows_value = None
            has_keep_empty = False
            keep_empty_value = None

            for line in content.splitlines():
                line = line.strip()
                if line.startswith("EXCEL_MAX_ROWS="):
                    try:
                        max_rows_value = int(line.split("=", 1)[1].strip())
                        has_max_rows = True
                    except:
                        pass
                if line.startswith("EXCEL_KEEP_EMPTY_ROWS="):
                    keep_empty_value = line.split("=", 1)[1].strip().lower()
                    has_keep_empty = True

            if not has_max_rows:
                env_check["detail"] = ".env found but EXCEL_MAX_ROWS not set"
            elif max_rows_value != 50:
                env_check["detail"] = f".env has EXCEL_MAX_ROWS={max_rows_value}, expected 50"
            elif not has_keep_empty:
                env_check["detail"] = ".env found but EXCEL_KEEP_EMPTY_ROWS not set"
            elif keep_empty_value not in ("false", "0", "no"):
                env_check["detail"] = f"EXCEL_KEEP_EMPTY_ROWS={keep_empty_value}, expected false"
            else:
                env_check["passed"] = True
                env_check["detail"] = f"EXCEL_MAX_ROWS={max_rows_value}, EXCEL_KEEP_EMPTY_ROWS={keep_empty_value}"
                total_score += 1
    except Exception as e:
        env_check["detail"] = f"Exception reading .env: {e}"
    checks.append(env_check)

    # -----------------------------------------------------------------------
    # Check 2: audit_report.json exists
    # -----------------------------------------------------------------------
    report_candidates = list(Path(workspace).rglob("audit_report.json"))
    report_check = {"name": "audit_report_json_exists", "passed": False, "detail": ""}
    report_data = None
    report_path = None
    try:
        if not report_candidates:
            report_check["detail"] = "audit_report.json not found anywhere in workspace"
        else:
            report_path = report_candidates[0]
            content = report_path.read_text(encoding="utf-8")
            report_data = json.loads(content)
            report_check["passed"] = True
            report_check["detail"] = f"Found at {report_path}"
            total_score += 1
    except json.JSONDecodeError as e:
        report_check["detail"] = f"audit_report.json found but invalid JSON: {e}"
    except Exception as e:
        report_check["detail"] = f"Exception: {e}"
    checks.append(report_check)

    # -----------------------------------------------------------------------
    # Check 3: audit_report.json contains all 3 departments with correct schema
    # -----------------------------------------------------------------------
    schema_check = {"name": "audit_report_schema_and_all_departments", "passed": False, "detail": ""}
    try:
        if report_data is None:
            schema_check["detail"] = "No report data to validate"
        else:
            # Must be a list or dict containing entries for 3 files
            # Accept either a list of file entries or a dict
            entries = []
            if isinstance(report_data, list):
                entries = report_data
            elif isinstance(report_data, dict):
                # Could be keyed by filename or have a 'files'/'departments' key
                if "files" in report_data:
                    entries = report_data["files"]
                elif "departments" in report_data:
                    entries = report_data["departments"]
                elif "results" in report_data:
                    entries = report_data["results"]
                else:
                    # Could be dict of filename -> data
                    entries = list(report_data.values())

            # Check we have 3 entries
            if len(entries) < 3:
                schema_check["detail"] = f"Expected 3 department entries, found {len(entries)}"
            else:
                # Each entry must have at least: sheet_count, total_cells, engine fields
                valid_entries = 0
                for entry in entries:
                    if isinstance(entry, dict):
                        has_sheet_count = "sheet_count" in entry
                        has_total_cells = "total_cells" in entry
                        has_engine = "engine" in entry
                        if has_sheet_count and has_total_cells and has_engine:
                            valid_entries += 1

                if valid_entries < 3:
                    schema_check["detail"] = f"Only {valid_entries}/3 entries have required fields (sheet_count, total_cells, engine)"
                else:
                    schema_check["passed"] = True
                    schema_check["detail"] = f"All 3 entries present with correct schema fields"
                    total_score += 1
    except Exception as e:
        schema_check["detail"] = f"Exception during schema check: {e}"
    checks.append(schema_check)

    # -----------------------------------------------------------------------
    # Check 4: EXCEL_MAX_ROWS=50 was respected — marketing_budget.xlsx
    #          Q3_Expenses sheet originally has 80 rows (1 header + 79 data),
    #          so with max_rows=50, row_count must be <= 50
    # -----------------------------------------------------------------------
    row_limit_check = {"name": "max_rows_limit_enforced", "passed": False, "detail": ""}
    try:
        if report_data is None:
            row_limit_check["detail"] = "No report data to validate"
        else:
            # Find the marketing entry
            entries = []
            if isinstance(report_data, list):
                entries = report_data
            elif isinstance(report_data, dict):
                for key in ("files", "departments", "results"):
                    if key in report_data:
                        entries = report_data[key]
                        break
                if not entries:
                    entries = list(report_data.values())

            marketing_entry = None
            for entry in entries:
                if isinstance(entry, dict):
                    # Look for marketing in filename or name field
                    fname = str(entry.get("file", "") or entry.get("filename", "") or entry.get("name", "")).lower()
                    if "marketing" in fname:
                        marketing_entry = entry
                        break
                    # Also check sheets field
                    sheets = entry.get("sheets", [])
                    if isinstance(sheets, list) and sheets:
                        for sh in sheets:
                            if isinstance(sh, dict) and sh.get("name", "").lower() in ("q3_expenses", "summary"):
                                marketing_entry = entry
                                break

            if marketing_entry is None:
                row_limit_check["detail"] = "Could not find marketing_budget entry in report"
            else:
                # Check that no sheet has row_count > 50
                sheets = marketing_entry.get("sheets", [])
                max_rows_found = max((sh.get("row_count", 0) for sh in sheets if isinstance(sh, dict)), default=0)
                if max_rows_found > 50:
                    row_limit_check["detail"] = f"marketing entry has row_count={max_rows_found} which exceeds EXCEL_MAX_ROWS=50 limit"
                else:
                    row_limit_check["passed"] = True
                    row_limit_check["detail"] = f"Max rows found in marketing entry: {max_rows_found} (<= 50)"
                    total_score += 1
    except Exception as e:
        row_limit_check["detail"] = f"Exception: {e}"
    checks.append(row_limit_check)

    # -----------------------------------------------------------------------
    # Check 5: Text previews produced (one .txt per Excel file OR consolidated)
    #          Must match the proprietary format: === Excel文件: xxx ===
    # -----------------------------------------------------------------------
    text_preview_check = {"name": "text_previews_in_proprietary_format", "passed": False, "detail": ""}
    try:
        # Look for text preview files
        txt_files = list(Path(workspace).rglob("*.txt"))
        # Filter out distractor txt files (they're in specific paths we created)
        distractor_paths = {
            "finance/Q3_2024/templates/budget_template_notes.txt",
            "finance/archive/2023/summary_2023.txt",
            "finance/archive/2022/legacy_report.txt",
            "reports/drafts/draft_notes.md",
            "tools/scripts/convert_old.py",
            "tools/configs/db_config.ini",
            "data/raw/README_raw.txt",
            "data/staging/staging_notes.txt",
            "finance/Q3_2024/processing_log.txt",
            "reports/processed/index.txt",
        }
        candidate_txt = [f for f in txt_files
                         if not any(str(f).endswith(d.replace("/", os.sep)) for d in distractor_paths)]

        # Also check if text is embedded in audit_report.json
        text_from_report = []
        if report_data is not None:
            entries = []
            if isinstance(report_data, list):
                entries = report_data
            elif isinstance(report_data, dict):
                for key in ("files", "departments", "results"):
                    if key in report_data:
                        entries = report_data[key]
                        break
                if not entries:
                    entries = list(report_data.values())
            for entry in entries:
                if isinstance(entry, dict) and "text" in entry:
                    text_from_report.append(entry["text"])

        proprietary_format_found = 0
        # Check text files for proprietary format
        for txt_f in candidate_txt:
            try:
                content = txt_f.read_text(encoding="utf-8", errors="ignore")
                if "=== Excel文件:" in content or "--- 工作表:" in content:
                    proprietary_format_found += 1
            except:
                pass

        # Check text in report
        for txt in text_from_report:
            if "=== Excel文件:" in txt or "--- 工作表:" in txt or "工作表数量:" in txt:
                proprietary_format_found += 1

        if proprietary_format_found >= 3:
            text_preview_check["passed"] = True
            text_preview_check["detail"] = f"Found {proprietary_format_found} proprietary-formatted text previews"
            total_score += 1
        elif proprietary_format_found >= 1:
            text_preview_check["passed"] = True
            text_preview_check["detail"] = f"Found {proprietary_format_found} proprietary-formatted text previews (partial credit)"
            total_score += 0.5
        else:
            text_preview_check["detail"] = (
                f"No proprietary format text found. Checked {len(candidate_txt)} txt files "
                f"and {len(text_from_report)} text fields in JSON. "
                "Expected '=== Excel文件:' or '--- 工作表:' markers."
            )
    except Exception as e:
        text_preview_check["detail"] = f"Exception: {e}"
    checks.append(text_preview_check)

    # -----------------------------------------------------------------------
    # Check 6: Engine field reflects actual parser used (calamine or fallback)
    # -----------------------------------------------------------------------
    engine_check = {"name": "engine_field_populated_from_skill", "passed": False, "detail": ""}
    try:
        if report_data is None:
            engine_check["detail"] = "No report data"
        else:
            entries = []
            if isinstance(report_data, list):
                entries = report_data
            elif isinstance(report_data, dict):
                for key in ("files", "departments", "results"):
                    if key in report_data:
                        entries = report_data[key]
                        break
                if not entries:
                    entries = list(report_data.values())

            valid_engines = {"python-calamine", "xlrd", "openpyxl", "calamine"}
            engines_found = []
            for entry in entries:
                if isinstance(entry, dict):
                    eng = entry.get("engine", "")
                    if eng:
                        engines_found.append(eng)

            if not engines_found:
                engine_check["detail"] = "No 'engine' fields found with values in any entry"
            elif all(e in valid_engines for e in engines_found):
                engine_check["passed"] = True
                engine_check["detail"] = f"Engines found: {engines_found}"
                total_score += 1
            else:
                unknown = [e for e in engines_found if e not in valid_engines]
                engine_check["detail"] = f"Unknown engine values: {unknown}. Valid: {valid_engines}"
    except Exception as e:
        engine_check["detail"] = f"Exception: {e}"
    checks.append(engine_check)

    # -----------------------------------------------------------------------
    # Final scoring
    # -----------------------------------------------------------------------
    final_score = round(total_score / max_checks, 4)
    passed = total_score >= (max_checks * 0.75)  # 75% threshold

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))