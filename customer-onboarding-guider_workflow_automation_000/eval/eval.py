import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    # Find the output file
    output_files = list(Path(workspace).rglob("onboarding_guide.md"))
    
    # ── CHECK 1: File exists ─────────────────────────────────────────────────
    if not output_files:
        checks.append({"name": "output_file_exists", "passed": False, 
                        "detail": "onboarding_guide.md not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    output_file = output_files[0]
    checks.append({"name": "output_file_exists", "passed": True, 
                   "detail": f"Found at {output_file}"})
    
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully"})
    
    # ── CHECK 2: All 8 steps present ─────────────────────────────────────────
    step_patterns = [
        r"第\s*[1１一]\s*步",
        r"第\s*[2２二]\s*步",
        r"第\s*[3３三]\s*步",
        r"第\s*[4４四]\s*步",
        r"第\s*[5５五]\s*步",
        r"第\s*[6６六]\s*步",
        r"第\s*[7７七]\s*步",
        r"第\s*[8８八]\s*步",
    ]
    
    steps_found = []
    for i, pattern in enumerate(step_patterns, 1):
        found = bool(re.search(pattern, content))
        steps_found.append(found)
    
    all_8_steps = all(steps_found)
    missing = [i+1 for i, f in enumerate(steps_found) if not f]
    checks.append({
        "name": "all_8_steps_present",
        "passed": all_8_steps,
        "detail": "All 8 steps found" if all_8_steps else f"Missing steps: {missing}"
    })
    
    # ── CHECK 3: Correct step names for all 8 steps ───────────────────────────
    step_names = [
        "确定使用接口",
        "网络接入信息",
        "客户访问服务器",
        "开通测试网络",
        "提供测试数据",
        "联调测试",
        "生产上线",
        "上线验证",
    ]
    names_found = [bool(re.search(name, content)) for name in step_names]
    all_names = all(names_found)
    missing_names = [step_names[i] for i, f in enumerate(names_found) if not f]
    checks.append({
        "name": "correct_step_names",
        "passed": all_names,
        "detail": "All step names present" if all_names else f"Missing names: {missing_names}"
    })
    
    # ── CHECK 4: 执行方/配合方 fields present ──────────────────────────────────
    has_executor = bool(re.search(r"执行方", content))
    has_cooperator = bool(re.search(r"配合方", content))
    fields_present = has_executor and has_cooperator
    checks.append({
        "name": "executor_cooperator_fields",
        "passed": fields_present,
        "detail": f"执行方: {has_executor}, 配合方: {has_cooperator}"
    })
    
    # ── CHECK 5: 工作内容 field present ────────────────────────────────────────
    has_work_content = bool(re.search(r"工作内容", content))
    checks.append({
        "name": "work_content_field",
        "passed": has_work_content,
        "detail": "工作内容 field found" if has_work_content else "工作内容 field missing"
    })
    
    # ── CHECK 6: Bold markdown formatting (**field**: value) ──────────────────
    bold_patterns = [r"\*\*工作内容\*\*", r"\*\*执行方\*\*", r"\*\*配合方\*\*"]
    bold_found = [bool(re.search(p, content)) for p in bold_patterns]
    bold_ok = any(bold_found)  # at least some bold formatting used
    checks.append({
        "name": "bold_markdown_formatting",
        "passed": bold_ok,
        "detail": f"Bold fields found: {bold_found}" if bold_ok else "No **bold** field formatting detected"
    })
    
    # ── CHECK 7: Step 6 联调测试 has detailed content + key note ───────────────
    # The skill says step 6 is the critical step and detailed single-step format
    # should include execution details
    step6_section = ""
    # Try to extract step 6 section
    step6_match = re.search(r"第\s*[6６六]\s*步.*?(?=第\s*[7７七]\s*步|$)", content, re.DOTALL)
    if step6_match:
        step6_section = step6_match.group(0)
    
    has_step6_detail = bool(re.search(r"(测试用例|联调|开发|测试报告|技术支持)", step6_section))
    has_step6_key_note = bool(re.search(r"(关键|充足时间|key|重要)", content, re.IGNORECASE))
    
    step6_ok = has_step6_detail and has_step6_key_note
    checks.append({
        "name": "step6_critical_highlighted",
        "passed": step6_ok,
        "detail": f"Step6 detail: {has_step6_detail}, key note: {has_step6_key_note}"
    })
    
    # ── CHECK 8: Duration/timeline mentioned (2-4 weeks) ─────────────────────
    has_duration = bool(re.search(r"(2.?4\s*周|两.?四\s*周|2\s*[-~到至]\s*4\s*周)", content))
    checks.append({
        "name": "overall_duration_mentioned",
        "passed": has_duration,
        "detail": "2-4 week duration found" if has_duration else "Overall duration (2-4周) not mentioned"
    })
    
    # ── CHECK 9: Correct bank vs enterprise responsibility assignment ──────────
    # Step 4 (开通测试网络) and Step 5 (提供测试数据): executor = 银行
    # Step 1,2,3,6,7,8: executor = 企业
    # Check that at least step 4 and 5 show 银行 as executor
    step4_match = re.search(r"第\s*[4４四]\s*步.*?(?=第\s*[5５五]\s*步|$)", content, re.DOTALL)
    step5_match = re.search(r"第\s*[5５五]\s*步.*?(?=第\s*[6６六]\s*步|$)", content, re.DOTALL)
    
    step4_bank_executor = False
    step5_bank_executor = False
    
    if step4_match:
        s4 = step4_match.group(0)
        # Should show 银行 as 执行方
        step4_bank_executor = bool(re.search(r"执行方.*?银行|银行.*?执行方", s4))
    if step5_match:
        s5 = step5_match.group(0)
        step5_bank_executor = bool(re.search(r"执行方.*?银行|银行.*?执行方", s5))
    
    # More lenient: just check that 银行 appears in step 4 and 5 sections
    if not step4_bank_executor and step4_match:
        step4_bank_executor = bool(re.search(r"银行", step4_match.group(0)))
    if not step5_bank_executor and step5_match:
        step5_bank_executor = bool(re.search(r"银行", step5_match.group(0)))
    
    responsibility_ok = step4_bank_executor and step5_bank_executor
    checks.append({
        "name": "bank_enterprise_responsibility",
        "passed": responsibility_ok,
        "detail": f"Step4 bank executor: {step4_bank_executor}, Step5 bank executor: {step5_bank_executor}"
    })
    
    # ── CHECK 10: 执行内容 field present (proprietary trap) ───────────────────
    # The skill format requires 执行内容 as a separate field from 工作内容
    has_exec_content = bool(re.search(r"执行内容", content))
    checks.append({
        "name": "execution_content_field",
        "passed": has_exec_content,
        "detail": "执行内容 field present" if has_exec_content else "执行内容 field missing — this is required by the proprietary format"
    })
    
    # ── CHECK 11: Not using old 6-step count ──────────────────────────────────
    # Should say 8 steps, not 6
    has_correct_count = bool(re.search(r"[8八]\s*[个步]", content))
    has_wrong_count = bool(re.search(r"(?<![1-9])[6六]\s*[个步](?![0-9])", content))
    count_ok = has_correct_count and not has_wrong_count
    checks.append({
        "name": "correct_step_count_8_not_6",
        "passed": count_ok,
        "detail": f"Has '8步/个': {has_correct_count}, Has wrong '6步/个': {has_wrong_count}"
    })
    
    # ── SCORING ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    
    # Must pass core checks to be considered passing overall
    core_checks = ["output_file_exists", "all_8_steps_present", "correct_step_names", 
                   "executor_cooperator_fields", "execution_content_field"]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)
    
    overall_passed = core_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))