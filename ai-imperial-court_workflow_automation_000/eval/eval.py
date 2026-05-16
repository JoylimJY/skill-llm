import sys
import os
import re
import json
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    records_dir = workspace / "records"
    
    checks = []
    total_score = 0.0
    max_score = 10.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ─────────────────────────────────────────────
    # HELPER: Find files in records/ matching pattern
    # ─────────────────────────────────────────────
    def find_records(suffix):
        """Find all files in records/ ending with a given suffix."""
        if not records_dir.exists():
            return []
        return list(records_dir.glob(f"*{suffix}"))

    # ─────────────────────────────────────────────
    # CHECK 1: records/ directory exists with files
    # ─────────────────────────────────────────────
    try:
        has_records_dir = records_dir.exists() and records_dir.is_dir()
        record_files = list(records_dir.iterdir()) if has_records_dir else []
        passed = has_records_dir and len(record_files) >= 3
        total_score += add_check(
            "records_directory_exists",
            passed,
            f"records/ dir exists: {has_records_dir}, files found: {len(record_files)}",
            weight=0.5
        )
    except Exception as e:
        total_score += add_check("records_directory_exists", False, f"Exception: {e}", weight=0.5)

    # ─────────────────────────────────────────────
    # CHECK 2: Naming convention {id}-draft.md
    # Files must follow the pattern: records/{id}-draft.md
    # ─────────────────────────────────────────────
    try:
        draft_files = find_records("-draft.md")
        passed = len(draft_files) >= 1
        detail = f"Found draft files: {[f.name for f in draft_files]}"
        total_score += add_check("draft_file_naming_convention", passed, detail, weight=1.0)
        draft_file = draft_files[0] if draft_files else None
        # Extract task ID from filename
        task_id = draft_file.stem.replace("-draft", "") if draft_file else None
    except Exception as e:
        total_score += add_check("draft_file_naming_convention", False, f"Exception: {e}", weight=1.0)
        draft_file = None
        task_id = None

    # ─────────────────────────────────────────────
    # CHECK 3: Draft contains required 中书省 sections
    # Must have: ## 诏令草案, ### 任务分析, ### 执行计划, ### 预期产出, 起草：中书省, 时间：
    # ─────────────────────────────────────────────
    try:
        if draft_file and draft_file.exists():
            draft_content = draft_file.read_text(encoding="utf-8")
            required_elements = [
                ("诏令草案", "诏令草案 header"),
                ("任务分析", "任务分析 section"),
                ("执行计划", "执行计划 section"),
                ("预期产出", "预期产出 section"),
                ("中书省", "起草：中书省 signature"),
                ("时间：", "ISO时间 field"),
            ]
            missing = []
            for pattern, name in required_elements:
                if pattern not in draft_content:
                    missing.append(name)
            passed = len(missing) == 0
            detail = f"Missing elements: {missing}" if missing else "All required elements found"
            total_score += add_check("draft_required_sections", passed, detail, weight=1.5)
        else:
            total_score += add_check("draft_required_sections", False, "No draft file found", weight=1.5)
    except Exception as e:
        total_score += add_check("draft_required_sections", False, f"Exception: {e}", weight=1.5)

    # ─────────────────────────────────────────────
    # CHECK 4: Draft assigns tasks to specific 六部 departments
    # Must mention at least 2 of the six departments
    # ─────────────────────────────────────────────
    try:
        if draft_file and draft_file.exists():
            draft_content = draft_file.read_text(encoding="utf-8")
            departments = ["吏部", "户部", "礼部", "兵部", "刑部", "工部"]
            found_depts = [d for d in departments if d in draft_content]
            passed = len(found_depts) >= 2
            detail = f"Departments mentioned in draft: {found_depts}"
            total_score += add_check("draft_assigns_six_ministries", passed, detail, weight=1.0)
        else:
            total_score += add_check("draft_assigns_six_ministries", False, "No draft file found", weight=1.0)
    except Exception as e:
        total_score += add_check("draft_assigns_six_ministries", False, f"Exception: {e}", weight=1.0)

    # ─────────────────────────────────────────────
    # CHECK 5: review file naming convention {id}-review.md
    # ─────────────────────────────────────────────
    try:
        review_files = find_records("-review.md")
        passed = len(review_files) >= 1
        detail = f"Found review files: {[f.name for f in review_files]}"
        total_score += add_check("review_file_naming_convention", passed, detail, weight=1.0)
        review_file = review_files[0] if review_files else None
    except Exception as e:
        total_score += add_check("review_file_naming_convention", False, f"Exception: {e}", weight=1.0)
        review_file = None

    # ─────────────────────────────────────────────
    # CHECK 6: Review file contains 门下省审核表 with all four checklist sections
    # Must have: 可行性检查, 风险检查, 遗漏检查, and 审核：门下省
    # ─────────────────────────────────────────────
    try:
        if review_file and review_file.exists():
            review_content = review_file.read_text(encoding="utf-8")
            required_review_elements = [
                ("门下省审核", "门下省审核表 header"),
                ("可行性检查", "可行性检查 section"),
                ("风险检查", "风险检查 section"),
                ("遗漏检查", "遗漏检查 section"),
                ("门下省", "审核：门下省 signature"),
                ("时间：", "ISO时间 field"),
            ]
            missing = []
            for pattern, name in required_review_elements:
                if pattern not in review_content:
                    missing.append(name)
            passed = len(missing) == 0
            detail = f"Missing elements: {missing}" if missing else "All required review elements found"
            total_score += add_check("review_required_sections", passed, detail, weight=1.5)
        else:
            total_score += add_check("review_required_sections", False, "No review file found", weight=1.5)
    except Exception as e:
        total_score += add_check("review_required_sections", False, f"Exception: {e}", weight=1.5)

    # ─────────────────────────────────────────────
    # CHECK 7: Review contains 封驳 decision (initial rejection)
    # The task involves a payment/financial system which should trigger the 封驳 workflow
    # Either the review file itself shows 封驳, OR there are multiple review files (re-submission cycle)
    # We check: review file has either "封驳" keyword OR there are >=2 review files
    # OR the review has both an initial rejection AND a final approval documented
    # ─────────────────────────────────────────────
    try:
        if review_file and review_file.exists():
            review_content = review_file.read_text(encoding="utf-8")
            # Check for 封驳 keyword anywhere in review
            has_fengbo = "封驳" in review_content
            # Check for multiple review files (re-submission cycle)
            all_review_files = find_records("-review.md")
            multiple_reviews = len(all_review_files) >= 2
            # Check for evidence of rejection then approval in a single file
            has_rejection_cycle = has_fengbo and ("通过" in review_content)
            
            passed = has_fengbo or multiple_reviews
            detail = (f"封驳 found: {has_fengbo}, "
                      f"multiple review files: {multiple_reviews} ({len(all_review_files)} files), "
                      f"rejection+approval cycle: {has_rejection_cycle}")
            total_score += add_check("fengbo_rejection_workflow", passed, detail, weight=1.5)
        else:
            # Check if there are multiple review files even if first not found
            all_review_files = find_records("-review.md")
            passed = len(all_review_files) >= 2
            detail = f"No primary review file, multiple reviews: {len(all_review_files)}"
            total_score += add_check("fengbo_rejection_workflow", passed, detail, weight=1.5)
    except Exception as e:
        total_score += add_check("fengbo_rejection_workflow", False, f"Exception: {e}", weight=1.5)

    # ─────────────────────────────────────────────
    # CHECK 8: execution report file naming convention {id}-exec.md
    # ─────────────────────────────────────────────
    try:
        exec_files = find_records("-exec.md")
        passed = len(exec_files) >= 1
        detail = f"Found exec files: {[f.name for f in exec_files]}"
        total_score += add_check("exec_file_naming_convention", passed, detail, weight=1.0)
        exec_file = exec_files[0] if exec_files else None
    except Exception as e:
        total_score += add_check("exec_file_naming_convention", False, f"Exception: {e}", weight=1.0)
        exec_file = None

    # ─────────────────────────────────────────────
    # CHECK 9: Execution report has proper markdown table and 尚书省 structure
    # Must have: ## 执行报告, ### 执行状态, proper markdown table with 4 columns,
    #            ### 最终产出, 执行：尚书省, 时间：
    # ─────────────────────────────────────────────
    try:
        if exec_file and exec_file.exists():
            exec_content = exec_file.read_text(encoding="utf-8")
            required_exec_elements = [
                ("执行报告", "执行报告 header"),
                ("执行状态", "执行状态 section"),
                ("最终产出", "最终产出 section"),
                ("尚书省", "执行：尚书省 signature"),
                ("时间：", "ISO时间 field"),
            ]
            missing = []
            for pattern, name in required_exec_elements:
                if pattern not in exec_content:
                    missing.append(name)
            
            # Check for markdown table with correct columns (部门|任务|状态|产出)
            has_table = bool(re.search(r'\|.+部门.+\|.+任务.+\|.+状态.+\|.+产出.+\|', exec_content))
            if not has_table:
                missing.append("execution status table with 部门|任务|状态|产出 columns")
            
            passed = len(missing) == 0
            detail = f"Missing elements: {missing}" if missing else "All required exec report elements found"
            total_score += add_check("exec_report_required_sections", passed, detail, weight=1.5)
        else:
            total_score += add_check("exec_report_required_sections", False, "No exec file found", weight=1.5)
    except Exception as e:
        total_score += add_check("exec_report_required_sections", False, f"Exception: {e}", weight=1.5)

    # ─────────────────────────────────────────────
    # CHECK 10: Execution report dispatches six ministries (六部)
    # At least 3 departments must appear in the exec report's table
    # ─────────────────────────────────────────────
    try:
        if exec_file and exec_file.exists():
            exec_content = exec_file.read_text(encoding="utf-8")
            departments = ["吏部", "户部", "礼部", "兵部", "刑部", "工部"]
            found_in_exec = [d for d in departments if d in exec_content]
            passed = len(found_in_exec) >= 3
            detail = f"Departments dispatched in exec report: {found_in_exec} ({len(found_in_exec)}/6)"
            total_score += add_check("exec_dispatches_six_ministries", passed, detail, weight=1.0)
        else:
            total_score += add_check("exec_dispatches_six_ministries", False, "No exec file found", weight=1.0)
    except Exception as e:
        total_score += add_check("exec_dispatches_six_ministries", False, f"Exception: {e}", weight=1.0)

    # ─────────────────────────────────────────────
    # CHECK 11: Consistent task ID across files (matching {id} prefix)
    # All three files should share the same ID prefix
    # ─────────────────────────────────────────────
    try:
        draft_files_all = find_records("-draft.md")
        review_files_all = find_records("-review.md")
        exec_files_all = find_records("-exec.md")
        
        if draft_files_all and review_files_all and exec_files_all:
            # Extract IDs
            draft_ids = set(f.name.replace("-draft.md", "") for f in draft_files_all)
            review_ids = set(f.name.replace("-review.md", "") for f in review_files_all)
            exec_ids = set(f.name.replace("-exec.md", "") for f in exec_files_all)
            
            # Check if there's at least one common ID across all three
            common_draft_review = draft_ids & review_ids
            common_all = draft_ids & review_ids & exec_ids
            # Allow for the case where review has multiple files (封驳 + approval)
            # as long as at least one review shares the same ID
            passed = len(common_draft_review) >= 1 and len(exec_ids & draft_ids) >= 1
            detail = (f"Draft IDs: {draft_ids}, Review IDs: {review_ids}, "
                      f"Exec IDs: {exec_ids}, Common all: {common_all}")
            total_score += add_check("consistent_task_id_across_files", passed, detail, weight=0.5)
        else:
            passed = False
            detail = (f"Not all file types present: "
                      f"drafts={len(draft_files_all)}, "
                      f"reviews={len(review_files_all)}, "
                      f"execs={len(exec_files_all)}")
            total_score += add_check("consistent_task_id_across_files", passed, detail, weight=0.5)
    except Exception as e:
        total_score += add_check("consistent_task_id_across_files", False, f"Exception: {e}", weight=0.5)

    # ─────────────────────────────────────────────
    # Compute final score
    # ─────────────────────────────────────────────
    # Weights: 0.5 + 1.0 + 1.5 + 1.0 + 1.0 + 1.5 + 1.5 + 1.0 + 1.5 + 1.0 + 0.5 = 12.0 total weight
    # We normalize to a 0.0-1.0 scale
    weight_total = 12.0
    normalized_score = round(total_score / weight_total, 3)
    
    all_passed = all(c["passed"] for c in checks)
    
    result = {
        "passed": normalized_score >= 0.75,
        "score": normalized_score,
        "checks": checks
    }
    
    return result


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "eval_invocation", "passed": False, "detail": "Usage: eval.py <workspace_dir>"}
        ]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))