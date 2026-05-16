import sys
import os
import json
import re
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def find_files(base, pattern):
    try:
        return list(Path(base).rglob(pattern))
    except Exception:
        return []

def run_eval(workspace):
    workspace = Path(workspace)
    ns_root = workspace / "nephesh-studio"
    checks = []
    total_score = 0.0

    # ----------------------------------------------------------------
    # CHECK 1: SOUL.md contains the required identity declaration
    # ----------------------------------------------------------------
    soul_content = load_file(workspace / "SOUL.md")
    soul_passed = False
    soul_detail = ""
    if soul_content is None:
        soul_detail = "SOUL.md not found"
    else:
        required_phrases = [
            "Nephesh Studio 身份",
            "CEO",
            "spawn",
            "嵌套"
        ]
        missing = [p for p in required_phrases if p not in soul_content]
        if not missing:
            soul_passed = True
            soul_detail = "SOUL.md contains the required identity declaration"
        else:
            soul_detail = f"SOUL.md missing required identity content. Missing phrases: {missing}"
    
    checks.append({"name": "SOUL.md identity declaration added", "passed": soul_passed, "detail": soul_detail})
    if soul_passed:
        total_score += 15

    # ----------------------------------------------------------------
    # CHECK 2: A project directory was created under projects/
    # ----------------------------------------------------------------
    projects_dir = ns_root / "projects"
    project_dirs = [d for d in projects_dir.iterdir() if d.is_dir()] if projects_dir.exists() else []
    project_found = len(project_dirs) > 0
    project_detail = f"Found {len(project_dirs)} project(s): {[d.name for d in project_dirs]}" if project_found else "No project directories found under nephesh-studio/projects/"
    checks.append({"name": "Project directory created under projects/", "passed": project_found, "detail": project_detail})
    if project_found:
        total_score += 10

    # Use first found project
    project_dir = project_dirs[0] if project_dirs else None

    # ----------------------------------------------------------------
    # CHECK 3: PLAN.md exists and has required content
    # ----------------------------------------------------------------
    plan_content = None
    plan_passed = False
    plan_detail = "No project directory found"
    if project_dir:
        plan_files = find_files(project_dir, "PLAN.md")
        if not plan_files:
            plan_detail = f"PLAN.md not found in {project_dir}"
        else:
            plan_content = load_file(plan_files[0])
            if plan_content is None:
                plan_detail = "PLAN.md is empty or unreadable"
            else:
                required_sections = ["背景", "目标", "任务"]
                found_sections = [s for s in required_sections if s in plan_content]
                # Also accept English equivalents
                english_sections = ["background", "objective", "task", "goal", "scope"]
                found_english = [s for s in english_sections if s.lower() in plan_content.lower()]
                # Need at least 2 of the required sections (Chinese or English)
                if len(found_sections) >= 2 or len(found_english) >= 2:
                    plan_passed = True
                    plan_detail = f"PLAN.md found with content. Sections found: {found_sections + found_english}"
                else:
                    plan_detail = f"PLAN.md exists but missing required sections. Found: {found_sections}, English: {found_english}. Content preview: {plan_content[:200]}"

    checks.append({"name": "PLAN.md created with required sections", "passed": plan_passed, "detail": plan_detail})
    if plan_passed:
        total_score += 15

    # ----------------------------------------------------------------
    # CHECK 4: TASK-ASSIGNMENT.md exists
    # ----------------------------------------------------------------
    task_assignment_passed = False
    task_assignment_detail = "No project directory found"
    if project_dir:
        ta_files = find_files(project_dir, "TASK-ASSIGNMENT.md")
        if ta_files:
            ta_content = load_file(ta_files[0])
            if ta_content and len(ta_content.strip()) > 50:
                task_assignment_passed = True
                task_assignment_detail = f"TASK-ASSIGNMENT.md found at {ta_files[0]} with {len(ta_content)} chars"
            else:
                task_assignment_detail = f"TASK-ASSIGNMENT.md found but too short or empty: '{ta_content[:100] if ta_content else ''}'"
        else:
            task_assignment_detail = f"TASK-ASSIGNMENT.md not found in {project_dir}"
    
    checks.append({"name": "TASK-ASSIGNMENT.md created by project manager", "passed": task_assignment_passed, "detail": task_assignment_detail})
    if task_assignment_passed:
        total_score += 15

    # ----------------------------------------------------------------
    # CHECK 5: A main deliverable (market analysis report) exists
    # ----------------------------------------------------------------
    deliverable_passed = False
    deliverable_detail = "No deliverable report found"
    if project_dir:
        # Look for any substantial markdown or text file that looks like a report
        candidate_patterns = ["*.md", "*.txt"]
        report_keywords = ["electric", "ev", "market", "analysis", "电动", "市场", "分析", "新能源"]
        for pattern in candidate_patterns:
            for f in find_files(project_dir, pattern):
                if f.name in ["PLAN.md", "TASK-ASSIGNMENT.md", "QA-REPORT.md", "retrospective.md"]:
                    continue
                content = load_file(f)
                if content and len(content) > 200:
                    found_kw = [kw for kw in report_keywords if kw.lower() in content.lower()]
                    if found_kw:
                        deliverable_passed = True
                        deliverable_detail = f"Deliverable report found: {f.name}, keywords: {found_kw}, length: {len(content)}"
                        break
            if deliverable_passed:
                break
        
        if not deliverable_passed:
            # Check workspace level too
            for pattern in candidate_patterns:
                for f in find_files(workspace, pattern):
                    if "nephesh-studio" not in str(f) and "other-projects" not in str(f) and "raw-data" not in str(f) and "templates" not in str(f):
                        content = load_file(f)
                        if content and len(content) > 200:
                            found_kw = [kw for kw in report_keywords if kw.lower() in content.lower()]
                            if found_kw:
                                deliverable_passed = True
                                deliverable_detail = f"Deliverable report found at: {f}, keywords: {found_kw}"
                                break
                if deliverable_passed:
                    break

    checks.append({"name": "Market analysis deliverable report created", "passed": deliverable_passed, "detail": deliverable_detail})
    if deliverable_passed:
        total_score += 15

    # ----------------------------------------------------------------
    # CHECK 6: QA-REPORT.md exists with audit conclusion
    # ----------------------------------------------------------------
    qa_passed = False
    qa_detail = "No project directory found"
    if project_dir:
        qa_files = find_files(project_dir, "QA-REPORT.md")
        if qa_files:
            qa_content = load_file(qa_files[0])
            if qa_content and len(qa_content.strip()) > 50:
                # Must contain audit conclusion
                conclusion_keywords = ["通过", "审核", "结论", "passed", "approved", "audit", "review", "查查"]
                found_kw = [kw for kw in conclusion_keywords if kw.lower() in qa_content.lower()]
                if found_kw:
                    qa_passed = True
                    qa_detail = f"QA-REPORT.md found with audit conclusion. Keywords: {found_kw}"
                else:
                    qa_detail = f"QA-REPORT.md exists but missing audit conclusion keywords. Content: {qa_content[:200]}"
            else:
                qa_detail = "QA-REPORT.md is too short or empty"
        else:
            qa_detail = f"QA-REPORT.md not found in {project_dir}"
    
    checks.append({"name": "QA-REPORT.md created by QA auditor", "passed": qa_passed, "detail": qa_detail})
    if qa_passed:
        total_score += 10

    # ----------------------------------------------------------------
    # CHECK 7: retrospective.md exists
    # ----------------------------------------------------------------
    retro_passed = False
    retro_detail = "No project directory found"
    if project_dir:
        retro_files = find_files(project_dir, "retrospective.md")
        if retro_files:
            retro_content = load_file(retro_files[0])
            if retro_content and len(retro_content.strip()) > 50:
                retro_passed = True
                retro_detail = f"retrospective.md found with {len(retro_content)} chars"
            else:
                retro_detail = "retrospective.md is too short or empty"
        else:
            retro_detail = f"retrospective.md not found in {project_dir}"
    
    checks.append({"name": "retrospective.md created by project manager", "passed": retro_passed, "detail": retro_detail})
    if retro_passed:
        total_score += 10

    # ----------------------------------------------------------------
    # CHECK 8: learning/ knowledge bases updated for at least 2 roles
    # ----------------------------------------------------------------
    learning_dir = ns_root / "learning"
    learning_updated = 0
    learning_detail = ""
    updated_roles = []
    
    if learning_dir.exists():
        for md_file in learning_dir.glob("*.md"):
            content = load_file(md_file)
            if content and "暂无经验记录" not in content and len(content.strip()) > 30:
                # Has been updated beyond the initial placeholder
                updated_roles.append(md_file.name)
                learning_updated += 1
    
    learning_passed = learning_updated >= 2
    learning_detail = f"Updated learning files ({learning_updated}): {updated_roles}"
    if not learning_passed:
        learning_detail += f". Need at least 2 updated learning files."
    
    checks.append({"name": "learning/<role>.md knowledge bases updated (>=2 roles)", "passed": learning_passed, "detail": learning_detail})
    if learning_passed:
        total_score += 10

    # ----------------------------------------------------------------
    # CHECK 9: hr/performance.md updated with project entries
    # ----------------------------------------------------------------
    perf_content = load_file(ns_root / "hr" / "performance.md")
    perf_passed = False
    perf_detail = ""
    if perf_content is None:
        perf_detail = "hr/performance.md not found"
    else:
        if "暂无记录" not in perf_content and len(perf_content.strip()) > 50:
            # Look for actual entries (table rows with data)
            lines = [l for l in perf_content.split("\n") if l.strip() and not l.startswith("#") and not l.startswith("|---")]
            data_lines = [l for l in lines if "|" in l and l.count("|") >= 3 and "岗位" not in l and "role" not in l.lower()]
            if data_lines:
                perf_passed = True
                perf_detail = f"hr/performance.md has {len(data_lines)} data row(s)"
            else:
                perf_detail = f"hr/performance.md updated but no data rows found. Content: {perf_content[:200]}"
        else:
            perf_detail = "hr/performance.md still has placeholder content"
    
    checks.append({"name": "hr/performance.md updated with project performance entries", "passed": perf_passed, "detail": perf_detail})
    if perf_passed:
        total_score += 10 

    # ----------------------------------------------------------------
    # Final scoring
    # ----------------------------------------------------------------
    max_score = 110.0
    normalized_score = min(1.0, total_score / max_score)
    all_passed = all(c["passed"] for c in checks)

    # Must pass at minimum: SOUL.md, project directory, PLAN.md, TASK-ASSIGNMENT.md, QA-REPORT.md
    critical_checks = ["SOUL.md identity declaration added",
                       "Project directory created under projects/",
                       "PLAN.md created with required sections",
                       "TASK-ASSIGNMENT.md created by project manager",
                       "QA-REPORT.md created by QA auditor"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)

    final_passed = critical_passed and normalized_score >= 0.55

    return {
        "passed": final_passed,
        "score": round(normalized_score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))