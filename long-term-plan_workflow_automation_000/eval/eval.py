import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_dir):
    ws = Path(workspace_dir)
    checks = []
    
    # =========================================================
    # PART 1: New plan file creation for "model-retrain"
    # =========================================================
    
    # Find the new plan file
    plan_files = list((ws / "memory" / "tasks").glob("model-retrain*.md")) + \
                 list((ws / "memory" / "tasks").glob("*retrain*plan*.md")) + \
                 list((ws / "memory" / "tasks").glob("*model*retrain*.md"))
    
    # Also try rglob in case agent put it elsewhere
    if not plan_files:
        plan_files = [f for f in ws.rglob("*retrain*plan*.md") if "drift" not in f.name]
    if not plan_files:
        plan_files = [f for f in ws.rglob("*model*plan*.md")]
    
    new_plan_file = None
    for f in plan_files:
        if "drift" not in f.name and "quarterly" not in f.name:
            new_plan_file = f
            break
    
    if new_plan_file is None:
        checks.append(check("new_plan_file_exists", False, 
            "Could not find a new model-retrain plan file under memory/tasks/"))
        # Can't do further checks on new plan
        new_plan_content = ""
    else:
        new_plan_content = new_plan_file.read_text(encoding="utf-8", errors="replace")
        checks.append(check("new_plan_file_exists", True, 
            f"Found new plan file: {new_plan_file.relative_to(ws)}"))
    
    # Check: file is in memory/tasks/
    if new_plan_file:
        in_correct_dir = str(new_plan_file.parent).endswith("memory/tasks") or \
                         "memory/tasks" in str(new_plan_file)
        checks.append(check("new_plan_in_memory_tasks", in_correct_dir,
            f"File location: {new_plan_file.parent if new_plan_file else 'N/A'}"))
    
    # Check: has 目标 section (one-sentence goal)
    has_goal = bool(re.search(r'##\s*目标', new_plan_content))
    checks.append(check("new_plan_has_goal_section", has_goal,
        "Plan must have a '## 目标' section" if not has_goal else "Found '## 目标'"))
    
    # Check: has 策略/原则 section with 3-5 items
    has_strategy = bool(re.search(r'##\s*策略', new_plan_content))
    checks.append(check("new_plan_has_strategy_section", has_strategy,
        "Plan must have a '## 策略' section"))
    
    if has_strategy:
        strategy_block = re.search(r'##\s*策略[^\n]*\n(.*?)(?=\n---|\n##)', new_plan_content, re.DOTALL)
        if strategy_block:
            items = re.findall(r'^\s*\d+\.', strategy_block.group(1), re.MULTILINE)
            strategy_count_ok = 3 <= len(items) <= 5
            checks.append(check("new_plan_strategy_3_to_5_items", strategy_count_ok,
                f"Strategy items found: {len(items)} (need 3-5)"))
        else:
            checks.append(check("new_plan_strategy_3_to_5_items", False, "Could not parse strategy block"))
    
    # Check: current phase has correct structure — 阶段目标 BEFORE 具体任务 (goal-first ordering)
    goal_pos = new_plan_content.find('### 阶段目标')
    task_pos = new_plan_content.find('### 具体任务')
    review_pos = new_plan_content.find('### 复盘检查点')
    
    goal_before_tasks = (goal_pos != -1 and task_pos != -1 and goal_pos < task_pos)
    checks.append(check("new_plan_goal_before_tasks", goal_before_tasks,
        f"'### 阶段目标' (pos {goal_pos}) must appear before '### 具体任务' (pos {task_pos})"))
    
    tasks_before_review = (task_pos != -1 and review_pos != -1 and task_pos < review_pos)
    checks.append(check("new_plan_tasks_before_review", tasks_before_review,
        f"'### 具体任务' (pos {task_pos}) must appear before '### 复盘检查点' (pos {review_pos})"))
    
    # Check: phase window is 3-5 days
    date_range = re.findall(r'(\d{4}-\d{2}-\d{2})\s*[-–]\s*(\d{4}-\d{2}-\d{2})', new_plan_content)
    phase_window_ok = False
    phase_window_detail = "No date range found in plan"
    if date_range:
        from dateutil.parser import parse as dparse
        for start_str, end_str in date_range:
            try:
                start = dparse(start_str)
                end = dparse(end_str)
                delta = (end - start).days
                if 2 <= delta <= 4:  # 3-5 days inclusive means delta of 2,3,4
                    phase_window_ok = True
                    phase_window_detail = f"Phase window: {start_str} to {end_str} = {delta+1} days"
                    break
                elif delta == 1 or delta == 5:
                    phase_window_ok = True
                    phase_window_detail = f"Phase window: {start_str} to {end_str} = {delta+1} days"
                    break
            except Exception as e:
                phase_window_detail = f"Date parse error: {e}"
    
    # More lenient: just check that a date range exists in the current phase header
    current_phase_header = re.search(r'##\s*当前阶段[^(]*\(([^)]+)\)', new_plan_content)
    if current_phase_header:
        dates_in_header = re.findall(r'\d{4}-\d{2}-\d{2}', current_phase_header.group(1))
        if len(dates_in_header) >= 2:
            try:
                from dateutil.parser import parse as dparse
                d1 = dparse(dates_in_header[0])
                d2 = dparse(dates_in_header[1])
                delta = abs((d2 - d1).days)
                phase_window_ok = 2 <= delta <= 5
                phase_window_detail = f"Phase: {dates_in_header[0]} to {dates_in_header[1]}, delta={delta} days"
            except:
                pass
    
    checks.append(check("new_plan_phase_window_3_to_5_days", phase_window_ok, phase_window_detail))
    
    # Check: has 复盘检查点 with a date
    has_review_checkpoint = bool(re.search(r'###\s*复盘检查点', new_plan_content))
    checks.append(check("new_plan_has_review_checkpoint", has_review_checkpoint,
        "Must have '### 复盘检查点' section in current phase"))
    
    # Check: has 历史归档 section
    has_archive = bool(re.search(r'##\s*历史归档', new_plan_content))
    checks.append(check("new_plan_has_archive_section", has_archive,
        "Must have '## 历史归档' section"))
    
    # Check: has 创建 and 当前阶段截止 footer
    has_created_date = bool(re.search(r'\*创建：\d{4}-\d{2}-\d{2}\*', new_plan_content))
    has_deadline = bool(re.search(r'\*当前阶段截止：\d{4}-\d{2}-\d{2}\*', new_plan_content))
    checks.append(check("new_plan_has_created_date_footer", has_created_date,
        "Must have '*创建：YYYY-MM-DD*' footer"))
    checks.append(check("new_plan_has_deadline_footer", has_deadline,
        "Must have '*当前阶段截止：YYYY-MM-DD*' footer"))
    
    # =========================================================
    # PART 2: drift-monitor-plan.md rollover (phase archive)
    # =========================================================
    
    drift_plan_path = ws / "memory" / "tasks" / "drift-monitor-plan.md"
    try:
        drift_content = drift_plan_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append(check("drift_plan_file_accessible", False, str(e)))
        drift_content = ""
    
    # Check: old phase "基线建立" is now in 历史归档
    old_phase_archived = bool(re.search(r'##\s*历史归档.*基线建立', drift_content, re.DOTALL))
    checks.append(check("drift_plan_old_phase_archived", old_phase_archived,
        "Old phase '基线建立' must be moved to '## 历史归档' section"))
    
    # Check: archived phase has ONLY 3 lines of content (not the full task list)
    archive_section = re.search(r'##\s*历史归档(.*?)(?=\n---|\n##\s*\w|\Z)', drift_content, re.DOTALL)
    archive_ok = False
    archive_detail = "Could not parse 历史归档 section"
    if archive_section:
        archive_text = archive_section.group(1).strip()
        # Count non-empty, non-header lines inside the archive entry
        lines = [l.strip() for l in archive_text.split('\n') 
                 if l.strip() and not l.strip().startswith('#')]
        # The 3-line rule: should have roughly 3 content lines (完成了/数据/复盘结论)
        # We allow some flexibility: 2-5 lines total
        archive_ok = 2 <= len(lines) <= 6
        archive_detail = f"Archive section has {len(lines)} non-empty content lines: {lines}"
    checks.append(check("drift_plan_archive_max_3_lines", archive_ok, archive_detail))
    
    # Check: old phase detailed task list is NOT in the current active section
    # The old phase's specific checkboxes should not appear in 当前阶段 section
    current_section = re.search(r'##\s*当前阶段(.*?)(?=\n##\s*历史归档|\n---\s*\n##\s*历史|\Z)', 
                                  drift_content, re.DOTALL)
    old_tasks_not_in_current = True
    if current_section:
        current_text = current_section.group(1)
        # Old tasks were: "部署 drift_detector.py", "采集 feature1", "设定初始阈值"
        old_task_remnants = re.findall(
            r'(部署 drift_detector|采集.*基线分布|设定初始阈值|验证告警通知链路|输出基线报告)', 
            current_text
        )
        old_tasks_not_in_current = len(old_task_remnants) == 0
        if not old_tasks_not_in_current:
            checks.append(check("drift_plan_old_tasks_not_in_current", False,
                f"Old phase tasks still in current section: {old_task_remnants}"))
        else:
            checks.append(check("drift_plan_old_tasks_not_in_current", True,
                "Old phase tasks correctly removed from current active section"))
    else:
        checks.append(check("drift_plan_old_tasks_not_in_current", False,
            "Could not find 当前阶段 section or it's missing"))
    
    # Check: drift plan has a NEW current phase (new phase name != "基线建立")
    new_phase_match = re.search(r'##\s*当前阶段：([^（(]+)', drift_content)
    has_new_phase = False
    new_phase_detail = "No current phase found"
    if new_phase_match:
        phase_name = new_phase_match.group(1).strip()
        has_new_phase = "基线建立" not in phase_name
        new_phase_detail = f"Current phase name: '{phase_name}'"
    checks.append(check("drift_plan_has_new_current_phase", has_new_phase, new_phase_detail))
    
    # Check: new phase in drift plan also has 阶段目标 BEFORE 具体任务
    drift_goal_pos = drift_content.find('### 阶段目标')
    drift_task_pos = drift_content.find('### 具体任务')
    drift_goal_first = (drift_goal_pos != -1 and drift_task_pos != -1 and drift_goal_pos < drift_task_pos)
    checks.append(check("drift_plan_new_phase_goal_before_tasks", drift_goal_first,
        f"In drift plan: '阶段目标' pos={drift_goal_pos}, '具体任务' pos={drift_task_pos}"))
    
    # =========================================================
    # PART 3: MEMORY.md — single reference line
    # =========================================================
    
    memory_path = ws / "memory" / "MEMORY.md"
    try:
        memory_content = memory_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append(check("memory_md_accessible", False, str(e)))
        memory_content = ""
    
    # Check: MEMORY.md has a reference to the new model-retrain plan
    has_retrain_ref = bool(re.search(r'(retrain|重训|model.*plan)', memory_content, re.IGNORECASE))
    checks.append(check("memory_md_has_retrain_reference", has_retrain_ref,
        "MEMORY.md must have a reference line pointing to the new model-retrain plan"))
    
    # Check: The reference is in 待办提醒 section
    todo_section = re.search(r'##\s*待办提醒(.*?)(?=\n##|\Z)', memory_content, re.DOTALL)
    ref_in_todo = False
    if todo_section:
        todo_text = todo_section.group(1)
        ref_in_todo = bool(re.search(r'(retrain|重训)', todo_text, re.IGNORECASE))
    checks.append(check("memory_md_ref_in_todo_section", ref_in_todo,
        "The reference to retrain plan must be in the '待办提醒' section"))
    
    # Check: reference is only ONE line (not a block summary)
    if todo_section:
        todo_lines = [l.strip() for l in todo_section.group(1).split('\n') 
                      if re.search(r'(retrain|重训)', l, re.IGNORECASE)]
        single_line_ref = len(todo_lines) <= 1
        checks.append(check("memory_md_ref_is_single_line", single_line_ref,
            f"Found {len(todo_lines)} line(s) referencing retrain plan in 待办提醒 (should be 1)"))
    
    # Check: reference line points to the plan file path
    has_path_ref = bool(re.search(r'memory/tasks/.*retrain.*\.md', memory_content, re.IGNORECASE))
    checks.append(check("memory_md_ref_has_file_path", has_path_ref,
        "Reference line must include path like 'memory/tasks/{name}-plan.md'"))
    
    # =========================================================
    # PART 4: CURRENT_STATE.md — today's tasks only
    # =========================================================
    
    state_path = ws / "memory" / "CURRENT_STATE.md"
    try:
        state_content = state_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append(check("current_state_accessible", False, str(e)))
        state_content = ""
    
    # Check: CURRENT_STATE.md references today's retrain plan tasks
    has_retrain_task = bool(re.search(r'(retrain|重训|model.*retrain)', state_content, re.IGNORECASE))
    checks.append(check("current_state_has_retrain_task", has_retrain_task,
        "CURRENT_STATE.md must include today's tasks from the new model-retrain plan"))
    
    # Check: CURRENT_STATE.md does NOT list tasks for multiple future days
    # It should not have day-by-day breakdown for future dates
    future_day_pattern = re.findall(
        r'(第[2-9]天|Day [2-9]|明天|后天|\d{1,2}/\d{1,2}.*\d{1,2}/\d{1,2}.*\d{1,2}/\d{1,2})', 
        state_content
    )
    no_future_multidayplan = len(future_day_pattern) == 0
    checks.append(check("current_state_no_multiday_future_plan", no_future_multidayplan,
        f"CURRENT_STATE.md should only list today's tasks, not multi-day future breakdown. Found: {future_day_pattern}"))
    
    # =========================================================
    # FINAL SCORE
    # =========================================================
    
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall = score >= 0.75
    
    return {
        "passed": overall,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))