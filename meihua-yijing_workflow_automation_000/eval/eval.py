import sys
import json
import subprocess
import re
from pathlib import Path

def run_checks(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    # === Reference: what meihua.py numbers 6 7 3 actually outputs ===
    try:
        result = subprocess.run(
            ["python3", str(workspace / "meihua.py"), "numbers", "6", "7", "3"],
            capture_output=True, text=True, timeout=15
        )
        reference_output = result.stdout.strip()
    except Exception as e:
        reference_output = ""
        checks.append({"name": "reference_script_execution", "passed": False, "detail": f"Failed to run meihua.py: {e}"})

    # === Find the output report file ===
    # Agent should create CR-20241115-007_report.txt or similar
    report_files = list(workspace.rglob("CR-20241115-007_report*")) + \
                   list(workspace.rglob("divination_report*")) + \
                   list(workspace.rglob("*陈美华*")) + \
                   list(workspace.rglob("*report_007*")) + \
                   list(workspace.rglob("*20241115*007*"))
    
    # Broaden search: any .txt file not in distractor locations that was recently created
    if not report_files:
        # Search for any new txt file that looks like a report
        all_txt = list(workspace.rglob("*.txt"))
        distractor_paths = {
            "client_records/2024/Q1", "client_records/2024/Q2", "client_records/2024/Q3",
            "client_records/2024/Q4_pending", "client_records/archive",
            "templates", "tools", "reports", "logs"
        }
        for f in all_txt:
            rel = str(f.relative_to(workspace))
            is_distractor = any(rel.startswith(d) for d in distractor_paths)
            if not is_distractor:
                report_files.append(f)
        # Also check if any existing file was modified (like Q4_pending client file)
        if not report_files:
            report_files = list(workspace.rglob("*.txt"))

    # Check 1: A report file exists
    report_content = ""
    report_path = None
    found_report = False
    for f in report_files:
        try:
            content = f.read_text(encoding="utf-8")
            # Must contain divination output markers
            if "梅花易数" in content or "起卦" in content or "本卦" in content:
                report_content = content
                report_path = f
                found_report = True
                break
        except Exception:
            continue

    checks.append({
        "name": "report_file_exists",
        "passed": found_report,
        "detail": f"Found report at: {report_path}" if found_report else "No divination report file found in workspace"
    })

    if not found_report:
        return checks

    # Check 2: Script was called with correct numbers (6 7 3) - verify via content matching
    has_numbers_method = "数字起卦" in report_content
    checks.append({
        "name": "correct_divination_method",
        "passed": has_numbers_method,
        "detail": f"Report uses 数字起卦 method: {has_numbers_method}"
    })

    has_correct_numbers = ("6" in report_content and "7" in report_content and "3" in report_content)
    # More specifically: "数字 6 7 3" should appear
    has_exact_numbers = bool(re.search(r"数字\s*6\s*7\s*3", report_content))
    checks.append({
        "name": "correct_numbers_used",
        "passed": has_exact_numbers or has_correct_numbers,
        "detail": f"Numbers 6,7,3 present: {has_correct_numbers}. Exact format '数字 6 7 3': {has_exact_numbers}"
    })

    # Check 3: Required output format sections are present
    required_sections = ["【起卦方式】", "【起卦信息】", "【本卦】", "【互卦】", "【变卦】", "【体用分析】", "【吉凶判断】", "【建议】"]
    missing_sections = [s for s in required_sections if s not in report_content]
    has_all_sections = len(missing_sections) == 0
    checks.append({
        "name": "required_format_sections",
        "passed": has_all_sections,
        "detail": f"Missing sections: {missing_sections}" if missing_sections else "All required sections present"
    })

    # Check 4: 本卦 content matches reference script output
    # Extract 本卦 line from reference
    ref_bengua_match = re.search(r"【本卦】：(.+)", reference_output)
    rep_bengua_match = re.search(r"【本卦】：(.+)", report_content)
    bengua_matches = False
    if ref_bengua_match and rep_bengua_match:
        ref_bengua = ref_bengua_match.group(1).strip()
        rep_bengua = rep_bengua_match.group(1).strip()
        bengua_matches = ref_bengua == rep_bengua
        checks.append({
            "name": "bengua_matches_script_output",
            "passed": bengua_matches,
            "detail": f"Expected: '{ref_bengua}', Got: '{rep_bengua}'"
        })
    else:
        checks.append({
            "name": "bengua_matches_script_output",
            "passed": False,
            "detail": f"Could not extract 本卦. Ref: {ref_bengua_match}, Rep: {rep_bengua_match}"
        })

    # Check 5: 体用分析 section has ti/yong entries with wuxing (五行)
    has_tiyong = ("体卦" in report_content and "用卦" in report_content and "五行" in report_content)
    checks.append({
        "name": "tiyong_analysis_present",
        "passed": has_tiyong,
        "detail": f"体卦, 用卦, 五行 all present: {has_tiyong}"
    })

    # Check 6: 吉凶判断 content matches reference
    ref_jixiong_match = re.search(r"【吉凶判断】：(.+)", reference_output)
    rep_jixiong_match = re.search(r"【吉凶判断】：(.+)", report_content)
    jixiong_matches = False
    if ref_jixiong_match and rep_jixiong_match:
        ref_jx = ref_jixiong_match.group(1).strip()
        rep_jx = rep_jixiong_match.group(1).strip()
        jixiong_matches = ref_jx == rep_jx
        checks.append({
            "name": "jixiong_matches_script_output",
            "passed": jixiong_matches,
            "detail": f"Expected: '{ref_jx}', Got: '{rep_jx}'"
        })
    else:
        checks.append({
            "name": "jixiong_matches_script_output",
            "passed": False,
            "detail": f"Could not extract 吉凶判断. Ref: {ref_jixiong_match}, Rep: {rep_jixiong_match}"
        })

    # Check 7: Relation (关系) matches reference
    ref_rel_match = re.search(r"关系：(.+?)（", reference_output)
    rep_rel_match = re.search(r"关系：(.+?)（", report_content)
    rel_matches = False
    if ref_rel_match and rep_rel_match:
        ref_rel = ref_rel_match.group(1).strip()
        rep_rel = rep_rel_match.group(1).strip()
        rel_matches = ref_rel == rep_rel
        checks.append({
            "name": "tiyong_relation_correct",
            "passed": rel_matches,
            "detail": f"Expected relation: '{ref_rel}', Got: '{rep_rel}'"
        })
    else:
        checks.append({
            "name": "tiyong_relation_correct",
            "passed": False,
            "detail": f"Could not extract 关系 field. Ref: {ref_rel_match}, Rep: {rep_rel_match}"
        })

    # Check 8: Report contains 建议 content (non-empty)
    jianyi_match = re.search(r"【建议】：(.+)", report_content, re.DOTALL)
    has_jianyi = bool(jianyi_match and len(jianyi_match.group(1).strip()) > 5)
    checks.append({
        "name": "jianyi_section_nonempty",
        "passed": has_jianyi,
        "detail": f"建议 content present and non-trivial: {has_jianyi}"
    })

    return checks


def main():
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks = run_checks(workspace_dir)
    except Exception as e:
        checks = [{"name": "eval_error", "passed": False, "detail": str(e)}]

    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall_passed = passed_count == total

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()