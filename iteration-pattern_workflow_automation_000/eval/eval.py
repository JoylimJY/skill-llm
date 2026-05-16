import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ---- CHECK 1: data_auditor.py exists and is functional ----
    auditor_files = list(workspace_path.rglob("data_auditor.py"))
    # Exclude the stub
    auditor_files = [f for f in auditor_files if "STUB" not in f.name]
    
    auditor_exists = len(auditor_files) > 0
    add_check(
        "data_auditor.py exists (non-stub)",
        auditor_exists,
        f"Found at: {auditor_files[0]}" if auditor_exists else "No data_auditor.py found (excluding stub)"
    )

    auditor_runnable = False
    if auditor_exists:
        import subprocess
        try:
            result = subprocess.run(
                ["python", str(auditor_files[0]),
                 str(workspace_path / "data/raw/uploads/customers.csv"),
                 str(workspace_path / "data/raw/uploads/orders.csv")],
                capture_output=True, text=True, timeout=30
            )
            auditor_runnable = result.returncode == 0
            detail = f"returncode={result.returncode}"
            if not auditor_runnable:
                detail += f" stderr={result.stderr[:300]}"
            add_check("data_auditor.py runs without error", auditor_runnable, detail)
        except Exception as e:
            add_check("data_auditor.py runs without error", False, f"Exception: {e}")
    else:
        add_check("data_auditor.py runs without error", False, "File not found, skipping run check")

    # ---- CHECK 2: Structured requirements document exists ----
    # Must have a requirements/task definition document (markdown or txt) with
    # task goal, completion criteria, test methods, iteration limit — per the skill's mandatory pre-work
    req_docs = []
    for pattern in ["*.md", "*.txt"]:
        req_docs.extend(workspace_path.rglob(pattern))
    
    # Exclude distractor files we know about
    distractor_names = {
        "summary.txt", "q4_report.md", "endpoints.md", "onboarding.md",
        "pipeline.log", "rejected_batch_003.txt", "requirements_draft.txt",
        "data_auditor_STUB.py", ".gitkeep"
    }
    req_docs = [f for f in req_docs if f.name not in distractor_names and "STUB" not in f.name]

    found_req_doc = None
    req_doc_score = 0

    for doc in req_docs:
        try:
            content = doc.read_text(encoding="utf-8", errors="ignore").lower()
            score = 0
            # Must have task goal / deliverable statement
            if any(kw in content for kw in ["任务目标", "task goal", "产出物", "deliverable", "目标"]):
                score += 1
            # Must have completion criteria
            if any(kw in content for kw in ["完成标准", "completion criteria", "标准", "criteria", "[ ]", "[x]", "[✓]"]):
                score += 1
            # Must have test methods
            if any(kw in content for kw in ["测试方法", "test method", "验证方式", "命令", "command", "grep", "python"]):
                score += 1
            # Must mention iteration limit
            if any(kw in content for kw in ["迭代上限", "最大迭代", "iteration", "max iter", "次"]):
                score += 1
            if score > req_doc_score:
                req_doc_score = score
                found_req_doc = doc
        except Exception:
            pass

    req_doc_adequate = req_doc_score >= 3
    add_check(
        "Structured requirements document exists with goal/criteria/test-methods/iteration-limit",
        req_doc_adequate,
        f"Best doc: {found_req_doc} (score {req_doc_score}/4)" if found_req_doc else "No adequate requirements document found"
    )

    # ---- CHECK 3: Completion report exists with required structure ----
    # Must have: iteration count, per-criterion pass/fail (✅/❌ or equivalent), conclusion
    completion_report = None
    report_score = 0

    candidate_docs = list(workspace_path.rglob("*.md")) + list(workspace_path.rglob("*.txt"))
    candidate_docs = [f for f in candidate_docs if f.name not in distractor_names]

    for doc in candidate_docs:
        try:
            content = doc.read_text(encoding="utf-8", errors="ignore")
            score = 0
            # Must contain iteration count mention
            if re.search(r'迭代次数|iteration.*count|次数.*[0-9]|[0-9].*次', content, re.IGNORECASE):
                score += 1
            # Must contain pass/fail markers
            if re.search(r'[✅❌✓✗☑☒]|passed|failed|\[x\]|\[ \]', content, re.IGNORECASE):
                score += 1
            # Must contain a conclusion
            if re.search(r'结论|conclusion|任务完成|部分完成|无法完成|completed|partially', content, re.IGNORECASE):
                score += 1
            # Must mention deliverable file path
            if re.search(r'data_auditor\.py|文件路径|file path|deliverable', content, re.IGNORECASE):
                score += 1
            if score > report_score:
                report_score = score
                completion_report = doc
        except Exception:
            pass

    report_adequate = report_score >= 3
    add_check(
        "Completion report has iteration count, pass/fail per criterion, and conclusion",
        report_adequate,
        f"Best report: {completion_report} (score {report_score}/4)" if completion_report else "No adequate completion report found"
    )

    # ---- CHECK 4: Conclusion uses valid Chinese/English value ----
    valid_conclusion = False
    conclusion_detail = "No valid conclusion found"
    if completion_report:
        try:
            content = completion_report.read_text(encoding="utf-8", errors="ignore")
            if re.search(r'任务完成|部分完成|无法完成|task complete|partially complete|cannot complete', content, re.IGNORECASE):
                valid_conclusion = True
                m = re.search(r'(任务完成|部分完成|无法完成|task complete[d]?|partially complete[d]?|cannot complete)', content, re.IGNORECASE)
                conclusion_detail = f"Found conclusion: '{m.group(0)}' in {completion_report}"
        except Exception as e:
            conclusion_detail = f"Error reading report: {e}"
    add_check("Conclusion uses a valid value (完成/部分完成/无法完成)", valid_conclusion, conclusion_detail)

    # ---- CHECK 5: data_auditor.py addresses key data quality issues ----
    # The script must check for duplicates AND missing values (at minimum)
    auditor_quality_score = 0
    auditor_quality_detail = "Auditor not found"
    if auditor_exists:
        try:
            content = auditor_files[0].read_text(encoding="utf-8", errors="ignore").lower()
            checks_found = []
            if re.search(r'duplicat|重复', content):
                auditor_quality_score += 1
                checks_found.append("duplicate check")
            if re.search(r'missing|null|none|nan|空值|缺失', content):
                auditor_quality_score += 1
                checks_found.append("missing value check")
            if re.search(r'email|format|格式', content):
                auditor_quality_score += 1
                checks_found.append("format/email check")
            if re.search(r'negative|负值|invalid.*date|date.*invalid|类型', content):
                auditor_quality_score += 1
                checks_found.append("type/range check")
            auditor_quality_detail = f"Checks implemented: {checks_found} (score {auditor_quality_score}/4)"
        except Exception as e:
            auditor_quality_detail = f"Error reading auditor: {e}"

    auditor_quality_ok = auditor_quality_score >= 3
    add_check(
        "data_auditor.py implements at least 3 of 4 data quality checks",
        auditor_quality_ok,
        auditor_quality_detail
    )

    # ---- CHECK 6: Requirements doc was created SEPARATELY from completion report ----
    # The skill mandates filling requirements BEFORE starting — so these should be different files
    # OR the same file has a clear "before" section followed by iteration records
    separate_docs = False
    separate_detail = "Unable to verify separate pre/post documents"
    
    if found_req_doc and completion_report:
        if found_req_doc.resolve() != completion_report.resolve():
            separate_docs = True
            separate_detail = f"Requirements: {found_req_doc.name}, Report: {completion_report.name}"
        else:
            # Same file — check if it has both a pre-work section and a completion section
            try:
                content = found_req_doc.read_text(encoding="utf-8", errors="ignore")
                has_prereq = bool(re.search(r'任务目标|task goal|产出物', content, re.IGNORECASE))
                has_report = bool(re.search(r'完成报告|completion report|结论|conclusion', content, re.IGNORECASE))
                separate_docs = has_prereq and has_report
                separate_detail = f"Single file with both sections: prereq={has_prereq}, report={has_report}"
            except Exception as e:
                separate_detail = f"Error: {e}"
    elif found_req_doc:
        separate_detail = "Requirements doc found but no completion report"
    elif completion_report:
        separate_detail = "Completion report found but no requirements doc"

    add_check(
        "Iteration workflow shows pre-work requirements AND completion report (separate or in-sequence)",
        separate_docs,
        separate_detail
    )

    # ---- Scoring ----
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks

    # Must pass checks 1 (exists), 3 (report), 4 (conclusion), 5 (quality) to pass overall
    critical = [
        checks[0]["passed"],  # auditor exists
        checks[2]["passed"],  # completion report
        checks[3]["passed"],  # valid conclusion
        checks[4]["passed"],  # quality checks
    ]
    overall_passed = all(critical) and passed_checks >= 5

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))