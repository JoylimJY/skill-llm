import sys
import json
import os
from pathlib import Path

def load_call_log():
    calls = []
    log_path = "/tmp/memos_call_log.jsonl"
    try:
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    calls.append(json.loads(line))
    except Exception as e:
        pass
    return calls

def load_state():
    try:
        with open("/tmp/memos_state.json") as f:
            return json.load(f)
    except Exception:
        return {"installed_skills": [], "published_skills": [], "public_memories": []}

def main(workspace_dir):
    checks = []
    
    # Load all API call records
    calls = load_call_log()
    state = load_state()
    
    endpoints_called = [c["endpoint"] for c in calls]
    
    # ---- CHECK 1: memory_search was called ----
    search_calls = [c for c in calls if c["endpoint"] == "memory_search"]
    check1_passed = len(search_calls) > 0
    checks.append({
        "name": "memory_search_called",
        "passed": check1_passed,
        "detail": f"memory_search called {len(search_calls)} times" if check1_passed else "memory_search was never called"
    })
    
    # ---- CHECK 2: memory_search used role='user' (PROPRIETARY TRAP) ----
    role_user_calls = []
    for c in search_calls:
        try:
            params = c.get("params", {})
            if isinstance(params, str):
                params = json.loads(params)
            if params.get("role") == "user":
                role_user_calls.append(c)
        except Exception:
            pass
    check2_passed = len(role_user_calls) > 0
    checks.append({
        "name": "memory_search_role_user_filter",
        "passed": check2_passed,
        "detail": "memory_search called with role='user' to find user-spoken content" if check2_passed else "CRITICAL: memory_search was never called with role='user'. Agent must filter by role='user' to find user preferences per SKILL.md."
    })
    
    # ---- CHECK 3: minScore was not set below floor 0.35 ----
    invalid_score_calls = []
    for c in search_calls:
        try:
            params = c.get("params", {})
            if isinstance(params, str):
                params = json.loads(params)
            score = params.get("minScore")
            if score is not None and float(score) < 0.35:
                invalid_score_calls.append(c)
        except Exception:
            pass
    check3_passed = len(invalid_score_calls) == 0
    checks.append({
        "name": "minScore_floor_respected",
        "passed": check3_passed,
        "detail": "minScore floor of 0.35 respected in all calls" if check3_passed else f"Agent set minScore below the 0.35 floor in {len(invalid_score_calls)} call(s)"
    })
    
    # ---- CHECK 4: task_summary was called with correct task_id ----
    task_summary_calls = [c for c in calls if c["endpoint"] == "task_summary"]
    task_summary_correct = False
    for c in task_summary_calls:
        try:
            params = c.get("params", {})
            if isinstance(params, str):
                params = json.loads(params)
            if params.get("taskId") == "task_pcr_brca1_2024":
                task_summary_correct = True
                break
        except Exception:
            pass
    checks.append({
        "name": "task_summary_called_correctly",
        "passed": task_summary_correct,
        "detail": "task_summary called with taskId='task_pcr_brca1_2024'" if task_summary_correct else "task_summary was not called with the correct taskId from memory_search results"
    })
    
    # ---- CHECK 5: skill_get was called for the task or skill ----
    skill_get_calls = [c for c in calls if c["endpoint"] == "skill_get"]
    skill_get_correct = False
    for c in skill_get_calls:
        try:
            params = c.get("params", {})
            if isinstance(params, str):
                params = json.loads(params)
            if params.get("taskId") == "task_pcr_brca1_2024" or params.get("skillId") == "skill_pcr_protocol_v2":
                skill_get_correct = True
                break
        except Exception:
            pass
    checks.append({
        "name": "skill_get_called",
        "passed": skill_get_correct,
        "detail": "skill_get called with correct taskId or skillId" if skill_get_correct else "skill_get was not called with correct taskId/skillId"
    })
    
    # ---- CHECK 6: skill_install was called BEFORE skill_publish ----
    skill_install_calls = [c for c in calls if c["endpoint"] == "skill_install"]
    skill_publish_calls = [c for c in calls if c["endpoint"] == "skill_publish"]
    
    install_correct_skill = any(
        (c.get("params", {}) if isinstance(c.get("params", {}), dict) else json.loads(c.get("params", "{}"))).get("skillId") == "skill_pcr_protocol_v2"
        for c in skill_install_calls
    )
    publish_correct_skill = any(
        (c.get("params", {}) if isinstance(c.get("params", {}), dict) else json.loads(c.get("params", "{}"))).get("skillId") == "skill_pcr_protocol_v2"
        for c in skill_publish_calls
    )
    
    # Check ordering: install before publish
    install_timestamp = None
    publish_timestamp = None
    for c in calls:
        if c["endpoint"] == "skill_install":
            try:
                params = c.get("params", {})
                if isinstance(params, str):
                    params = json.loads(params)
                if params.get("skillId") == "skill_pcr_protocol_v2":
                    install_timestamp = c.get("timestamp")
            except Exception:
                pass
        if c["endpoint"] == "skill_publish":
            try:
                params = c.get("params", {})
                if isinstance(params, str):
                    params = json.loads(params)
                if params.get("skillId") == "skill_pcr_protocol_v2":
                    publish_timestamp = c.get("timestamp")
            except Exception:
                pass
    
    order_correct = (install_timestamp is not None and publish_timestamp is not None and 
                     install_timestamp <= publish_timestamp)
    
    check6_passed = install_correct_skill and publish_correct_skill and order_correct
    checks.append({
        "name": "skill_install_before_publish",
        "passed": check6_passed,
        "detail": "skill_pcr_protocol_v2 was installed and then published in correct order" if check6_passed else f"skill_install_before_publish failed: install_correct={install_correct_skill}, publish_correct={publish_correct_skill}, order_correct={order_correct}"
    })
    
    # ---- CHECK 7: State confirms skill is installed and published ----
    skill_installed_in_state = "skill_pcr_protocol_v2" in state.get("installed_skills", [])
    skill_published_in_state = "skill_pcr_protocol_v2" in state.get("published_skills", [])
    check7_passed = skill_installed_in_state and skill_published_in_state
    checks.append({
        "name": "skill_state_correct",
        "passed": check7_passed,
        "detail": f"State: installed={skill_installed_in_state}, published={skill_published_in_state}" 
    })
    
    # ---- CHECK 8: memory_write_public was called with meaningful content ----
    pub_mem_calls = [c for c in calls if c["endpoint"] == "memory_write_public"]
    pub_mem_correct = False
    for c in pub_mem_calls:
        try:
            params = c.get("params", {})
            if isinstance(params, str):
                params = json.loads(params)
            content = params.get("content", "")
            summary = params.get("summary", "")
            # Content must be substantial (>50 chars) and mention PCR/BRCA1/protocol
            if (len(content) > 50 and 
                any(kw in content.lower() for kw in ["pcr", "brca1", "protocol", "primer", "annealing"])):
                pub_mem_correct = True
                break
        except Exception:
            pass
    checks.append({
        "name": "memory_write_public_meaningful",
        "passed": pub_mem_correct,
        "detail": "memory_write_public called with meaningful PCR protocol content" if pub_mem_correct else "memory_write_public not called or content is not meaningful/relevant to the PCR protocol"
    })
    
    # ---- CHECK 9: memory_write_public included summary field ----
    pub_mem_has_summary = False
    for c in pub_mem_calls:
        try:
            params = c.get("params", {})
            if isinstance(params, str):
                params = json.loads(params)
            if params.get("summary") and len(params.get("summary", "")) > 10:
                pub_mem_has_summary = True
                break
        except Exception:
            pass
    checks.append({
        "name": "memory_write_public_has_summary",
        "passed": pub_mem_has_summary,
        "detail": "memory_write_public included a summary field (optional but best-practice)" if pub_mem_has_summary else "memory_write_public was missing the summary field"
    })
    
    # ---- CHECK 10: handoff_report.json exists and has required fields ----
    report_files = list(Path(workspace_dir).rglob("handoff_report.json"))
    report_check_passed = False
    report_detail = "handoff_report.json not found"
    
    if report_files:
        try:
            with open(report_files[0]) as f:
                report = json.load(f)
            
            required_keys = ["task_id", "skill_id", "protocol_summary"]
            missing = [k for k in required_keys if k not in report]
            
            # Check content quality
            protocol_summary = str(report.get("protocol_summary", ""))
            has_pcr_content = any(kw in protocol_summary.lower() for kw in ["pcr", "brca1", "primer", "58", "annealing", "35 cycle"])
            task_id_correct = report.get("task_id") == "task_pcr_brca1_2024"
            skill_id_correct = report.get("skill_id") == "skill_pcr_protocol_v2"
            
            if not missing and has_pcr_content and task_id_correct and skill_id_correct:
                report_check_passed = True
                report_detail = f"handoff_report.json found at {report_files[0]} with all required fields and correct content"
            else:
                report_detail = f"handoff_report.json found but issues: missing_keys={missing}, has_pcr_content={has_pcr_content}, task_id_correct={task_id_correct}, skill_id_correct={skill_id_correct}"
        except json.JSONDecodeError as e:
            report_detail = f"handoff_report.json is not valid JSON: {e}"
        except Exception as e:
            report_detail = f"Error reading handoff_report.json: {e}"
    
    checks.append({
        "name": "handoff_report_json_correct",
        "passed": report_check_passed,
        "detail": report_detail
    })
    
    # ---- SCORING ----
    # Weights: critical checks get more weight
    weights = {
        "memory_search_called": 0.05,
        "memory_search_role_user_filter": 0.15,  # PROPRIETARY TRAP - high weight
        "minScore_floor_respected": 0.05,
        "task_summary_called_correctly": 0.10,
        "skill_get_called": 0.10,
        "skill_install_before_publish": 0.15,  # ordering matters
        "skill_state_correct": 0.10,
        "memory_write_public_meaningful": 0.10,
        "memory_write_public_has_summary": 0.05,
        "handoff_report_json_correct": 0.15,
    }
    
    total_score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.05)
        if check["passed"]:
            total_score += w
    
    all_critical_passed = (
        checks[1]["passed"] and  # role='user'
        checks[3]["passed"] and  # task_summary correct
        checks[5]["passed"] and  # install before publish
        checks[9]["passed"]      # handoff_report.json
    )
    
    final_passed = all_critical_passed and total_score >= 0.70
    
    result = {
        "passed": final_passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)