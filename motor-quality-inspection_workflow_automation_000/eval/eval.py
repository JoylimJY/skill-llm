import sys
import os
import json
import subprocess
import re
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def check_iqc_report(workspace):
    """IQC report: must contain 北方磁材有限公司 and B2024033"""
    # Search for any file containing IQC report content
    candidates = list(Path(workspace).rglob("*.txt")) + list(Path(workspace).rglob("*.md")) + list(Path(workspace).rglob("*.log"))
    # Also check stdout-captured files - look for files with IQC content
    all_text_files = list(Path(workspace).rglob("*"))
    found_supplier = False
    found_batch = False
    found_iqc_header = False
    found_file = None

    for f in all_text_files:
        if f.is_file():
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if "来料检验报告" in content or "IQC" in content:
                    if "北方磁材有限公司" in content:
                        found_supplier = True
                        found_file = str(f)
                    if "B2024033" in content:
                        found_batch = True
                    if "来料检验报告" in content:
                        found_iqc_header = True
            except Exception:
                continue

    passed = found_supplier and found_batch and found_iqc_header
    detail = (
        f"IQC report found={found_file}, "
        f"supplier=北方磁材有限公司:{found_supplier}, "
        f"batch=B2024033:{found_batch}, "
        f"header:来料检验报告:{found_iqc_header}"
    )
    return passed, detail

def check_pqc_report(workspace):
    """PQC report: must contain PMSM-1kW and 20240078"""
    all_files = list(Path(workspace).rglob("*"))
    found_model = False
    found_sn = False
    found_header = False
    found_file = None

    for f in all_files:
        if f.is_file():
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if "过程检验报告" in content or "PQC" in content:
                    if "PMSM-1kW" in content:
                        found_model = True
                        found_file = str(f)
                    if "20240078" in content:
                        found_sn = True
                    if "过程检验报告" in content:
                        found_header = True
            except Exception:
                continue

    passed = found_model and found_sn and found_header
    detail = (
        f"PQC report found={found_file}, "
        f"model=PMSM-1kW:{found_model}, "
        f"sn=20240078:{found_sn}, "
        f"header:过程检验报告:{found_header}"
    )
    return passed, detail

def check_oqc_report_file(workspace):
    """OQC report must be saved to file 'oqc_report_20240091.txt' (exact filename from prompt)"""
    # The prompt specifies exact filename
    candidates = list(Path(workspace).rglob("oqc_report_20240091.txt"))
    if not candidates:
        return False, "File 'oqc_report_20240091.txt' not found anywhere in workspace"
    
    found_file = candidates[0]
    try:
        content = found_file.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return False, f"Could not read oqc_report_20240091.txt: {e}"

    has_oqc_header = "出厂检验报告" in content
    has_model = "BLDC-200W" in content
    has_sn = "20240091" in content
    has_gjb = "GJB9001C" in content or "GJB179A" in content
    has_checklist = "外观检查" in content and "绝缘电阻" in content

    passed = has_oqc_header and has_model and has_sn and has_gjb and has_checklist
    detail = (
        f"File: {found_file}, "
        f"OQC header:{has_oqc_header}, "
        f"model=BLDC-200W:{has_model}, "
        f"sn=20240091:{has_sn}, "
        f"GJB refs:{has_gjb}, "
        f"checklist items:{has_checklist}"
    )
    return passed, detail

def check_oqc_content_quality(workspace):
    """OQC report must include the GJB179A sampling scheme section"""
    candidates = list(Path(workspace).rglob("oqc_report_20240091.txt"))
    if not candidates:
        return False, "File 'oqc_report_20240091.txt' not found"
    
    content = candidates[0].read_text(encoding="utf-8", errors="ignore")
    # The OQC report must include sampling scheme details (GJB179A)
    has_sampling = "抽样" in content or "样本" in content or "判定" in content
    has_checklist_items = all(kw in content for kw in ["空载运行", "负载运行", "随机文件"])
    has_voltage = "1500V" in content

    passed = has_sampling and has_checklist_items and has_voltage
    detail = (
        f"Sampling section:{has_sampling}, "
        f"Checklist completeness (空载/负载/随机文件):{has_checklist_items}, "
        f"Voltage spec 1500V:{has_voltage}"
    )
    return passed, detail

def check_correct_script_usage(workspace):
    """Verify the agent used the inspection_report.py script (not a hand-crafted file) 
       by checking that the script is present and executable and the output matches known format"""
    script_path = Path(workspace) / "scripts" / "inspection_report.py"
    if not script_path.exists():
        return False, "scripts/inspection_report.py missing (should not happen)"
    
    # Run the script's --list to confirm it's intact and functional
    try:
        result = subprocess.run(
            ["python", str(script_path), "--list"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        has_iqc = "iqc" in output
        has_oqc = "oqc" in output
        has_pqc = "pqc" in output
        has_fqc = "fqc" in output
        passed = has_iqc and has_oqc and has_pqc and has_fqc
        detail = f"--list output types: iqc={has_iqc}, pqc={has_pqc}, fqc={has_fqc}, oqc={has_oqc}"
        return passed, detail
    except Exception as e:
        return False, f"Script execution failed: {e}"

def check_no_iqc_wrong_flags(workspace):
    """IQC report must have supplier and batch info - not model/SN which belong to other types"""
    all_files = list(Path(workspace).rglob("*"))
    for f in all_files:
        if f.is_file():
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if "来料检验报告" in content and "北方磁材有限公司" in content:
                    # Good - has supplier
                    # Check it also has batch
                    has_batch = "B2024033" in content
                    return has_batch, f"IQC report has correct batch B2024033: {has_batch}"
            except Exception:
                continue
    return False, "No valid IQC report found with correct supplier+batch combination"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = [
        run_check("script_functional", lambda: check_correct_script_usage(workspace)),
        run_check("iqc_report_generated", lambda: check_iqc_report(workspace)),
        run_check("iqc_correct_flags_supplier_batch", lambda: check_no_iqc_wrong_flags(workspace)),
        run_check("pqc_report_generated", lambda: check_pqc_report(workspace)),
        run_check("oqc_report_saved_to_file", lambda: check_oqc_report_file(workspace)),
        run_check("oqc_report_content_quality", lambda: check_oqc_content_quality(workspace)),
    ]

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total

    result = {
        "passed": passed_count == total,
        "score": round(score, 4),
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()