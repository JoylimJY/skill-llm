import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    # Find the output file
    target_files = list(Path(workspace).rglob("handover_diagnostic_report.md"))
    
    if not target_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "handover_diagnostic_report.md not found anywhere in workspace"}]
        }
    
    report_path = target_files[0]
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }
    
    # CHECK 1: Commands use $ prefix format
    # Must have at least 5 commands with "$ " prefix inside code blocks
    cmd_dollar_matches = re.findall(r'^\$\s+\S+', content, re.MULTILINE)
    check1_passed = len(cmd_dollar_matches) >= 5
    checks.append({
        "name": "command_dollar_prefix",
        "passed": check1_passed,
        "detail": f"Found {len(cmd_dollar_matches)} lines with '$ <command>' prefix format (need ≥5)"
    })
    
    # CHECK 2: Normal output blocks use "# 输出：" marker (Chinese, with full-width colon)
    normal_output_markers = re.findall(r'#\s*输出：', content)
    check2_passed = len(normal_output_markers) >= 3
    checks.append({
        "name": "chinese_output_marker",
        "passed": check2_passed,
        "detail": f"Found {len(normal_output_markers)} '# 输出：' markers (need ≥3). Note: must use Chinese full-width colon '：' not ASCII ':'"
    })
    
    # CHECK 3: Error output block must use "# 输出（错误）：" marker
    error_output_marker = re.search(r'#\s*输出（错误）：', content)
    check3_passed = error_output_marker is not None
    checks.append({
        "name": "error_output_marker",
        "passed": check3_passed,
        "detail": "Must contain '# 输出（错误）：' for the failed curl command"
    })
    
    # CHECK 4: Error block must contain "# 错误信息：" section
    error_info_marker = re.search(r'#\s*错误信息：', content)
    check4_passed = error_info_marker is not None
    checks.append({
        "name": "error_info_block",
        "passed": check4_passed,
        "detail": "Must contain '# 错误信息：' block after the error output"
    })
    
    # CHECK 5: Error block must contain exit code "退出码：" with value 7
    exit_code_match = re.search(r'退出码[：:]\s*7', content)
    check5_passed = exit_code_match is not None
    checks.append({
        "name": "exit_code_7",
        "passed": check5_passed,
        "detail": "Error block must contain '退出码：7' (the curl exit code from the notes)"
    })
    
    # CHECK 6: Long output truncation — must show truncation notice for the journalctl output
    # The log had 127 lines total, must be truncated with "... (共 127 行" or similar pattern
    truncation_pattern = re.search(r'\.\.\.\s*\(共\s*\d+\s*行', content)
    check6_passed = truncation_pattern is not None
    # Also check it contains the specific 50-line limit language
    truncation_detail = f"Found truncation notice: '{truncation_pattern.group(0)}'" if truncation_pattern else "No truncation notice found. Long output (127 lines) must be truncated with '... (共 N 行，需要看完整输出吗？)'"
    checks.append({
        "name": "long_output_truncation",
        "passed": check6_passed,
        "detail": truncation_detail
    })
    
    # CHECK 7: Multi-step workflow separators — must use ━━━ separators for steps
    step_separators = re.findall(r'━{5,}', content)
    check7_passed = len(step_separators) >= 4  # At least 2 steps × 2 separators each
    checks.append({
        "name": "step_separators",
        "passed": check7_passed,
        "detail": f"Found {len(step_separators)} '━━━' separator lines (need ≥4 for multi-step format)"
    })
    
    # CHECK 8: Step headers in format "步骤 N/M:" 
    step_headers = re.findall(r'步骤\s*\d+/\d+', content)
    check8_passed = len(step_headers) >= 3  # At least 3 steps documented
    checks.append({
        "name": "step_headers",
        "passed": check8_passed,
        "detail": f"Found {len(step_headers)} '步骤 N/M' headers (need ≥3)"
    })
    
    # CHECK 9: Output interpretation/解读 block
    interpretation_marker = re.search(r'#\s*解读[：:]', content)
    check9_passed = interpretation_marker is not None
    checks.append({
        "name": "output_interpretation",
        "passed": check9_passed,
        "detail": "Must contain at least one '# 解读：' block with bullet-point interpretation of output"
    })
    
    # CHECK 10: The report must include ALL 5 steps from the session notes
    # Check for presence of the 5 commands from the notes
    has_df = bool(re.search(r'\$\s+df\s+-h', content))
    has_systemctl = bool(re.search(r'\$\s+systemctl', content))
    has_journalctl = bool(re.search(r'\$\s+journalctl', content))
    has_curl = bool(re.search(r'\$\s+curl', content))
    has_tree = bool(re.search(r'\$\s+tree', content))
    all_commands = all([has_df, has_systemctl, has_journalctl, has_curl, has_tree])
    check10_passed = all_commands
    checks.append({
        "name": "all_five_commands_present",
        "passed": check10_passed,
        "detail": f"Commands found: df={has_df}, systemctl={has_systemctl}, journalctl={has_journalctl}, curl={has_curl}, tree={has_tree}. All 5 must be present."
    })
    
    # CHECK 11: The first 50 lines of journalctl output must be shown (spot-check first log line)
    has_first_log_line = bool(re.search(r'Gateway starting on port 19922', content))
    check11_passed = has_first_log_line
    checks.append({
        "name": "long_output_first_lines_shown",
        "passed": check11_passed,
        "detail": "The first lines of the journalctl output must be visible before truncation (e.g., 'Gateway starting on port 19922')"
    })
    
    # CHECK 12: The "# 输出：\n（无输出）" pattern or at least one "success" indicator (✅)
    success_check = bool(re.search(r'✅', content))
    checks.append({
        "name": "success_indicators_present",
        "passed": success_check,
        "detail": "Report must contain ✅ success indicators for completed steps"
    })
    
    # Scoring: weighted
    weights = {
        "command_dollar_prefix": 1.0,
        "chinese_output_marker": 1.5,
        "error_output_marker": 1.5,
        "error_info_block": 1.0,
        "exit_code_7": 1.0,
        "long_output_truncation": 1.5,
        "step_separators": 1.0,
        "step_headers": 1.0,
        "output_interpretation": 1.0,
        "all_five_commands_present": 1.5,
        "long_output_first_lines_shown": 1.0,
        "success_indicators_present": 0.5,
    }
    
    total_weight = sum(weights.values())
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"])
    score = round(earned_weight / total_weight, 3)
    
    # Must pass at least 8/12 checks and score >= 0.65 to pass overall
    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = passed_count >= 8 and score >= 0.65
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))