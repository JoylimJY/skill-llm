import sys
import os
import json
import subprocess
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []

def check(name, condition, detail):
    checks.append({"name": name, "passed": bool(condition), "detail": detail})
    return bool(condition)

# ---- 1. Run the agent's script ----
script_path = os.path.join(workspace, "warehouse-orchestration.js")
run_result = None
stdout_output = ""
stderr_output = ""

try:
    result = subprocess.run(
        ["node", script_path],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=workspace
    )
    stdout_output = result.stdout
    stderr_output = result.stderr
    run_ok = result.returncode == 0
    check("script_runs_without_error",
          run_ok,
          f"Exit code: {result.returncode}. stderr: {stderr_output[:500] if stderr_output else 'none'}")
except subprocess.TimeoutExpired:
    check("script_runs_without_error", False, "Script timed out after 120 seconds")
    run_ok = False
except FileNotFoundError:
    check("script_runs_without_error", False, f"Script not found: {script_path}")
    run_ok = False
except Exception as e:
    check("script_runs_without_error", False, f"Unexpected error: {e}")
    run_ok = False

# ---- 2. Check data/ directory was created with persistent state files ----
data_dir = os.path.join(workspace, "data")

# ---- 3. Validate project state file ----
project_file = os.path.join(data_dir, "warehouse-opt-2024-project.json")
project_data = None
try:
    with open(project_file) as f:
        project_data = json.load(f)
    check("project_state_file_exists",
          True,
          f"Found: {project_file}")
except FileNotFoundError:
    # Try to find it anywhere under workspace
    found = list(Path(workspace).rglob("warehouse-opt-2024-project.json"))
    if found:
        try:
            with open(found[0]) as f:
                project_data = json.load(f)
            check("project_state_file_exists", True, f"Found at alternate path: {found[0]}")
        except Exception as e:
            check("project_state_file_exists", False, f"File found but unreadable: {e}")
    else:
        check("project_state_file_exists", False, f"No warehouse-opt-2024-project.json found under {workspace}")
except Exception as e:
    check("project_state_file_exists", False, f"Error reading project file: {e}")

# ---- 4. Validate project goal and status ----
if project_data:
    goal_ok = project_data.get("goal", "").lower().find("rfid") != -1 or \
              project_data.get("goal", "").lower().find("warehouse") != -1 or \
              project_data.get("goal", "").lower().find("optimize") != -1
    check("project_goal_correct",
          goal_ok,
          f"Goal: {project_data.get('goal', 'MISSING')}")

    status_ok = project_data.get("status") == "complete"
    check("project_status_complete",
          status_ok,
          f"Status: {project_data.get('status', 'MISSING')}")

    project_id_ok = project_data.get("projectId") == "warehouse-opt-2024"
    check("project_id_correct",
          project_id_ok,
          f"projectId: {project_data.get('projectId', 'MISSING')}")
else:
    check("project_goal_correct", False, "No project data to inspect")
    check("project_status_complete", False, "No project data to inspect")
    check("project_id_correct", False, "No project data to inspect")

# ---- 5. Validate tasks include all three phases ----
if project_data:
    tasks = project_data.get("tasks", [])
    task_types = [t.get("type", "") for t in tasks]

    has_planning = "planning" in task_types
    has_development = "development" in task_types
    has_audit = "audit" in task_types

    check("tasks_include_planning_phase",
          has_planning,
          f"Task types found: {list(set(task_types))}")
    check("tasks_include_development_phase",
          has_development,
          f"Task types found: {list(set(task_types))}")
    check("tasks_include_audit_phase",
          has_audit,
          f"Task types found: {list(set(task_types))}")

    # Check audit tasks specifically match the custom template
    audit_tasks = [t for t in tasks if t.get("type") == "audit"]
    audit_names = [t.get("name", "") for t in audit_tasks]

    audit_step1_ok = any("compliance" in n.lower() or "review" in n.lower() for n in audit_names)
    audit_step2_ok = any("validate" in n.lower() or "system" in n.lower() for n in audit_names)
    audit_step3_ok = any("sign" in n.lower() or "deliverable" in n.lower() for n in audit_names)

    check("custom_audit_template_step1",
          audit_step1_ok,
          f"Audit task names: {audit_names}")
    check("custom_audit_template_step2",
          audit_step2_ok,
          f"Audit task names: {audit_names}")
    check("custom_audit_template_step3",
          audit_step3_ok,
          f"Audit task names: {audit_names}")

    # All audit tasks should be complete
    audit_all_complete = all(t.get("status") == "complete" for t in audit_tasks) if audit_tasks else False
    check("audit_tasks_all_complete",
          audit_all_complete,
          f"Audit task statuses: {[t.get('status') for t in audit_tasks]}")
else:
    for c in ["tasks_include_planning_phase", "tasks_include_development_phase",
              "tasks_include_audit_phase", "custom_audit_template_step1",
              "custom_audit_template_step2", "custom_audit_template_step3",
              "audit_tasks_all_complete"]:
        check(c, False, "No project data to inspect")

# ---- 6. Validate agent memory files exist for all 3 agents ----
agent_ids = ["logistics", "engineering", "compliance"]
for aid in agent_ids:
    # The framework saves as [agent-id]-memory.json where agent-id = "agent-" + registered_id
    # From README: "id": "agent-research" when registered as 'research'
    memory_file_v1 = os.path.join(data_dir, f"agent-{aid}-memory.json")
    memory_file_v2 = os.path.join(data_dir, f"{aid}-memory.json")

    found_memory = None
    if os.path.exists(memory_file_v1):
        found_memory = memory_file_v1
    elif os.path.exists(memory_file_v2):
        found_memory = memory_file_v2
    else:
        # Search broadly
        candidates = list(Path(workspace).rglob(f"*{aid}*memory*.json"))
        if candidates:
            found_memory = str(candidates[0])

    memory_data = None
    if found_memory:
        try:
            with open(found_memory) as f:
                memory_data = json.load(f)
        except Exception:
            pass

    if memory_data:
        tasks_completed = memory_data.get("tasksCompleted", 0)
        check(f"agent_{aid}_memory_tasks_completed",
              tasks_completed > 0,
              f"Agent {aid} tasksCompleted: {tasks_completed} (file: {found_memory})")
    else:
        check(f"agent_{aid}_memory_tasks_completed",
              False,
              f"No memory file found for agent '{aid}' in {data_dir}")

# ---- 7. Validate correct capabilities assigned ----
# Check logistics agent has planning+research, compliance has audit+planning
for aid, expected_caps in [("logistics", ["planning", "research"]),
                             ("engineering", ["development", "design"]),
                             ("compliance", ["audit", "planning"])]:
    memory_file_v1 = os.path.join(data_dir, f"agent-{aid}-memory.json")
    memory_file_v2 = os.path.join(data_dir, f"{aid}-memory.json")

    mem = None
    for mf in [memory_file_v1, memory_file_v2]:
        if os.path.exists(mf):
            try:
                with open(mf) as f:
                    mem = json.load(f)
                break
            except Exception:
                pass

    if not mem:
        candidates = list(Path(workspace).rglob(f"*{aid}*memory*.json"))
        if candidates:
            try:
                with open(candidates[0]) as f:
                    mem = json.load(f)
            except Exception:
                pass

    if mem:
        actual_caps = mem.get("capabilities", [])
        caps_ok = all(c in actual_caps for c in expected_caps)
        check(f"agent_{aid}_capabilities_correct",
              caps_ok,
              f"Agent {aid} capabilities: {actual_caps}, expected to include: {expected_caps}")
    else:
        check(f"agent_{aid}_capabilities_correct",
              False,
              f"Could not read memory for agent {aid}")

# ---- 8. Final progress output check ----
progress_ok = "100" in stdout_output or \
              '"progress": 100' in stdout_output or \
              '"progress":100' in stdout_output or \
              "complete" in stdout_output.lower()
check("output_indicates_completion",
      progress_ok,
      f"stdout snippet: {stdout_output[:300]}")

# ---- Scoring ----
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 3) if total > 0 else 0.0
passed = score >= 0.75

print(json.dumps({
    "passed": passed,
    "score": score,
    "checks": checks
}, indent=2))