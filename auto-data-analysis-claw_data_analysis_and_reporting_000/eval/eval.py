import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
total_score = 0.0
max_score = 0.0

def make_check(name, passed, detail, weight=1.0):
    return {"name": name, "passed": passed, "detail": detail, "_weight": weight}

# ─── CHECK 1: Cleaned data file exists ───────────────────────────────────────
max_score += 1.0
try:
    cleaned_files = list(workspace.rglob("*clean*.csv")) + list(workspace.rglob("*cleaned*.csv"))
    # Also accept files in data/processed/
    processed_files = list((workspace / "data/processed").glob("*.csv"))
    all_candidates = cleaned_files + [f for f in processed_files if f not in cleaned_files]
    
    if all_candidates:
        import pandas as pd
        import numpy as np
        
        # Pick the most recently-touched candidate or just first
        df_clean = pd.read_csv(all_candidates[0])
        checks.append(make_check(
            "cleaned_csv_exists",
            True,
            f"Found cleaned CSV at {all_candidates[0]} with {len(df_clean)} rows and {len(df_clean.columns)} columns",
            1.0
        ))
        total_score += 1.0
    else:
        checks.append(make_check("cleaned_csv_exists", False, "No cleaned CSV found in workspace", 1.0))
except Exception as e:
    checks.append(make_check("cleaned_csv_exists", False, f"Exception: {e}", 1.0))

# ─── CHECK 2: Cleaned data has no or reduced nulls ───────────────────────────
max_score += 1.0
try:
    if all_candidates:
        df_clean = pd.read_csv(all_candidates[0])
        df_clean.replace("", np.nan, inplace=True)
        null_rate = df_clean.isnull().mean().mean()
        # After cleaning, numeric columns should have very few nulls
        num_nulls = df_clean.select_dtypes(include=[np.number]).isnull().sum().sum()
        passed = num_nulls == 0
        checks.append(make_check(
            "nulls_filled_in_numeric_cols",
            passed,
            f"Numeric null cells remaining: {num_nulls} (should be 0 after median fill)",
            1.0
        ))
        if passed:
            total_score += 1.0
    else:
        checks.append(make_check("nulls_filled_in_numeric_cols", False, "No cleaned CSV to check", 1.0))
except Exception as e:
    checks.append(make_check("nulls_filled_in_numeric_cols", False, f"Exception: {e}", 1.0))

# ─── CHECK 3: KPI config JSON exists with correct formula syntax ──────────────
max_score += 1.5
try:
    kpi_configs = list(workspace.rglob("kpi_config*.json")) + list(workspace.rglob("*kpi*.json"))
    # Exclude old distractor
    kpi_configs = [f for f in kpi_configs if "old" not in str(f)]
    
    if kpi_configs:
        with open(kpi_configs[0]) as f:
            kpi_cfg = json.load(f)
        
        kpis = kpi_cfg.get("kpis", [])
        
        # Validate formula syntax: must be func(col) pattern
        valid_funcs = {"sum", "mean", "count", "max", "min"}
        formula_pattern = re.compile(r"^(sum|mean|count|max|min)\(\w+\)$")
        
        all_valid = all(
            formula_pattern.match(kpi.get("formula", ""))
            for kpi in kpis
        )
        has_revenue_kpi = any("revenue" in kpi.get("formula", "").lower() or "revenue" in kpi.get("name", "").lower() for kpi in kpis)
        has_margin_kpi = any("margin" in kpi.get("formula", "").lower() or "margin" in kpi.get("name", "").lower() for kpi in kpis)
        has_count_kpi = any(kpi.get("formula", "").startswith("count(") for kpi in kpis)
        
        passed = all_valid and len(kpis) >= 2
        detail = (f"Found {len(kpis)} KPIs. All formulas valid: {all_valid}. "
                  f"Has revenue: {has_revenue_kpi}, margin: {has_margin_kpi}, count: {has_count_kpi}")
        checks.append(make_check("kpi_config_valid_formula_syntax", passed, detail, 1.5))
        if passed:
            total_score += 1.5
    else:
        checks.append(make_check("kpi_config_valid_formula_syntax", False, "No KPI config JSON found (excluding distractors)", 1.5))
except Exception as e:
    checks.append(make_check("kpi_config_valid_formula_syntax", False, f"Exception: {e}", 1.5))

# ─── CHECK 4: KPI results JSON exists with numeric values ────────────────────
max_score += 1.5
try:
    kpi_results = list(workspace.rglob("kpi_results*.json")) + list(workspace.rglob("*kpi*result*.json"))
    if not kpi_results:
        # fallback: any json with numeric top-level values that isn't config
        all_jsons = [f for f in workspace.rglob("*.json") if "config" not in f.name and "old" not in str(f)]
        kpi_results = [f for f in all_jsons if any(
            isinstance(v, (int, float)) for v in json.load(open(f)).values()
        ) if f.stat().st_size < 50000]
    
    if kpi_results:
        with open(kpi_results[0]) as f:
            results = json.load(f)
        
        numeric_values = {k: v for k, v in results.items() if isinstance(v, (int, float))}
        has_large_revenue = any(v > 100000 for v in numeric_values.values())
        
        passed = len(numeric_values) >= 2 and has_large_revenue
        checks.append(make_check(
            "kpi_results_contain_valid_numbers",
            passed,
            f"KPI result file at {kpi_results[0]}. Numeric KPIs: {len(numeric_values)}. Has large revenue value: {has_large_revenue}",
            1.5
        ))
        if passed:
            total_score += 1.5
    else:
        checks.append(make_check("kpi_results_contain_valid_numbers", False, "No KPI results JSON found", 1.5))
except Exception as e:
    checks.append(make_check("kpi_results_contain_valid_numbers", False, f"Exception: {e}", 1.5))

# ─── CHECK 5: Final Markdown report exists ───────────────────────────────────
max_score += 1.5
try:
    # Look specifically for the requested filename
    report_files = list(workspace.rglob("quarterly_performance_report.md"))
    if not report_files:
        # Fallback: any markdown report in reports/ dir
        report_files = list((workspace / "reports").glob("*.md"))
    if not report_files:
        report_files = list(workspace.rglob("*.md"))
        report_files = [f for f in report_files if "performance" in f.name.lower() or "report" in f.name.lower() or "analysis" in f.name.lower()]
    
    if report_files:
        content = report_files[0].read_text(encoding="utf-8")
        has_h1 = content.strip().startswith("#")
        has_h2 = "##" in content
        has_table_or_content = "|" in content or len(content) > 500
        passed = has_h1 and has_h2 and has_table_or_content
        checks.append(make_check(
            "markdown_report_exists_and_structured",
            passed,
            f"Report at {report_files[0]}. Has H1: {has_h1}, H2 sections: {has_h2}, Content: {has_table_or_content}",
            1.5
        ))
        if passed:
            total_score += 1.5
    else:
        checks.append(make_check("markdown_report_exists_and_structured", False, "No markdown report found", 1.5))
except Exception as e:
    checks.append(make_check("markdown_report_exists_and_structured", False, f"Exception: {e}", 1.5))

# ─── CHECK 6: Report config JSON has required structure ──────────────────────
max_score += 1.5
try:
    report_configs = list(workspace.rglob("report_config*.json")) + list(workspace.rglob("*report*config*.json"))
    report_configs = [f for f in report_configs if "old" not in str(f) and "generic" not in str(f)]
    
    if report_configs:
        with open(report_configs[0]) as f:
            rcfg = json.load(f)
        
        has_title = "title" in rcfg
        has_metadata = "metadata" in rcfg
        has_sections = "sections" in rcfg and isinstance(rcfg["sections"], list)
        sections_have_title = all("title" in s for s in rcfg.get("sections", []))
        sections_have_content = all("content" in s for s in rcfg.get("sections", []))
        at_least_two_sections = len(rcfg.get("sections", [])) >= 2
        
        passed = has_title and has_metadata and has_sections and sections_have_title and sections_have_content and at_least_two_sections
        checks.append(make_check(
            "report_config_has_required_structure",
            passed,
            (f"Report config at {report_configs[0]}. title: {has_title}, metadata: {has_metadata}, "
             f"sections: {has_sections}, all-have-title: {sections_have_title}, "
             f"all-have-content: {sections_have_content}, >=2 sections: {at_least_two_sections}"),
            1.5
        ))
        if passed:
            total_score += 1.5
    else:
        checks.append(make_check("report_config_has_required_structure", False, "No report config JSON found", 1.5))
except Exception as e:
    checks.append(make_check("report_config_has_required_structure", False, f"Exception: {e}", 1.5))

# ─── CHECK 7: Report contains KPI-derived numbers ────────────────────────────
max_score += 1.0
try:
    if report_files and kpi_results:
        report_content = report_files[0].read_text(encoding="utf-8")
        # Report should contain some large number (revenue in millions range)
        numbers_in_report = re.findall(r"[\d,]+\.?\d*", report_content)
        large_numbers = [n for n in numbers_in_report if len(n.replace(",", "").replace(".", "")) > 5]
        has_data_driven_content = len(large_numbers) >= 1 or any(
            word in report_content for word in ["总收入", "毛利", "revenue", "Revenue", "收入", "KPI"]
        )
        passed = has_data_driven_content
        checks.append(make_check(
            "report_references_kpi_data",
            passed,
            f"Report contains large numbers or KPI references: {has_data_driven_content}",
            1.0
        ))
        if passed:
            total_score += 1.0
    else:
        checks.append(make_check("report_references_kpi_data", False, "Missing report or KPI results to cross-check", 1.0))
except Exception as e:
    checks.append(make_check("report_references_kpi_data", False, f"Exception: {e}", 1.0))

# ─── Final scoring ────────────────────────────────────────────────────────────
# Remove internal weight key from output
clean_checks = [{"name": c["name"], "passed": c["passed"], "detail": c["detail"]} for c in checks]
final_score = round(total_score / max_score, 4) if max_score > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": all_passed,
    "score": final_score,
    "checks": clean_checks
}, ensure_ascii=False, indent=2))