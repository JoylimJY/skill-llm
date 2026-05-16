import sys
import json
import pathlib

workspace = pathlib.Path(sys.argv[1])

checks = []
score_parts = []

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    score_parts.append((passed, weight))

# --- Find the mission report JSON ---
# The prompt asks the agent to save the report as 'mission_report.json'
report_files = list(workspace.rglob("mission_report.json"))

if not report_files:
    add_check("report_file_exists", False, "No file named 'mission_report.json' found anywhere in workspace.", weight=2.0)
    # Cannot proceed without the file
    total_weight = sum(w for _, w in score_parts) + 6.0  # remaining weights
    earned = sum(w for p, w in score_parts if p)
    score = round(earned / (total_weight), 3)
    result = {"passed": False, "score": score, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

report_path = report_files[0]
add_check("report_file_exists", True, f"Found mission_report.json at {report_path}", weight=2.0)

# --- Load and parse the report ---
try:
    with open(report_path) as f:
        report = json.load(f)
    add_check("report_is_valid_json", True, "mission_report.json is valid JSON.", weight=1.0)
except Exception as e:
    add_check("report_is_valid_json", False, f"Failed to parse mission_report.json: {e}", weight=1.0)
    total_weight = sum(w for _, w in score_parts) + 5.0
    earned = sum(w for p, w in score_parts if p)
    score = round(earned / total_weight, 3)
    result = {"passed": False, "score": score, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

# --- Check schema fields ---
try:
    sdna_ok = report.get("sdna") == "AOI-2026-0215-SDNA-SQUAD01"
    add_check(
        "report_sdna_correct",
        sdna_ok,
        f"Expected sdna='AOI-2026-0215-SDNA-SQUAD01', got '{report.get('sdna')}'",
        weight=1.0
    )
except Exception as e:
    add_check("report_sdna_correct", False, f"Error checking sdna: {e}", weight=1.0)

try:
    preset_ok = report.get("preset") == "builder-security-operator"
    add_check(
        "report_preset_correct",
        preset_ok,
        f"Expected preset='builder-security-operator', got '{report.get('preset')}'",
        weight=1.5
    )
except Exception as e:
    add_check("report_preset_correct", False, f"Error checking preset: {e}", weight=1.5)

try:
    task_val = report.get("task", "")
    task_ok = "vulnerability" in task_val.lower() or "perimeter" in task_val.lower() or "security assessment" in task_val.lower() or "assess" in task_val.lower()
    add_check(
        "report_task_relevant",
        task_ok,
        f"Task field should relate to vulnerability/security assessment. Got: '{task_val}'",
        weight=1.0
    )
except Exception as e:
    add_check("report_task_relevant", False, f"Error checking task: {e}", weight=1.0)

try:
    status_ok = report.get("status") == "completed"
    add_check(
        "report_status_completed",
        status_ok,
        f"Expected status='completed', got '{report.get('status')}'",
        weight=0.5
    )
except Exception as e:
    add_check("report_status_completed", False, f"Error checking status: {e}", weight=0.5)

# --- Check team composition ---
try:
    team = report.get("team", {})
    # The preset builder-security-operator has roles: builder, security, operator
    has_builder = "builder" in team
    has_security = "security" in team
    has_operator = "operator" in team
    roles_ok = has_builder and has_security and has_operator
    add_check(
        "team_has_correct_roles",
        roles_ok,
        f"Team must have 'builder', 'security', 'operator' keys. Got: {list(team.keys())}",
        weight=1.5
    )
except Exception as e:
    add_check("team_has_correct_roles", False, f"Error checking team roles: {e}", weight=1.5)

# --- Check that security role was renamed to "Sentinel Kestrel" ---
# (The task requires renaming the 'security' role to "Sentinel Kestrel")
try:
    team = report.get("team", {})
    security_name = team.get("security", "")
    renamed_ok = security_name == "Sentinel Kestrel"
    add_check(
        "security_role_renamed_to_Sentinel_Kestrel",
        renamed_ok,
        f"Expected team['security']='Sentinel Kestrel', got '{security_name}'",
        weight=2.5
    )
except Exception as e:
    add_check("security_role_renamed_to_Sentinel_Kestrel", False, f"Error checking rename: {e}", weight=2.5)

# --- Check that operator role was renamed to "Phantom Relay" ---
try:
    team = report.get("team", {})
    operator_name = team.get("operator", "")
    op_renamed_ok = operator_name == "Phantom Relay"
    add_check(
        "operator_role_renamed_to_Phantom_Relay",
        op_renamed_ok,
        f"Expected team['operator']='Phantom Relay', got '{operator_name}'",
        weight=2.5
    )
except Exception as e:
    add_check("operator_role_renamed_to_Phantom_Relay", False, f"Error checking operator rename: {e}", weight=2.5)

# --- Verify squad_names.json was updated correctly by CLI ---
try:
    squad_path = pathlib.Path.home() / ".openclaw" / "aoi" / "squad_names.json"
    with open(squad_path) as f:
        squad_data = json.load(f)
    bso = squad_data.get("builder-security-operator", {})
    store_security_ok = bso.get("security") == "Sentinel Kestrel"
    store_operator_ok = bso.get("operator") == "Phantom Relay"
    store_ok = store_security_ok and store_operator_ok
    add_check(
        "squad_names_json_updated_correctly",
        store_ok,
        f"~/.openclaw/aoi/squad_names.json should have security='Sentinel Kestrel' and operator='Phantom Relay'. "
        f"Got security='{bso.get('security')}', operator='{bso.get('operator')}'",
        weight=2.0
    )
except Exception as e:
    add_check("squad_names_json_updated_correctly", False, f"Error reading squad_names.json: {e}", weight=2.0)

# --- Check schema_version field exists ---
try:
    sv_ok = "schema_version" in report
    add_check(
        "report_has_schema_version",
        sv_ok,
        f"Report should include 'schema_version' field. Present: {sv_ok}",
        weight=0.5
    )
except Exception as e:
    add_check("report_has_schema_version", False, f"Error: {e}", weight=0.5)

# --- Final scoring ---
total_weight = sum(w for _, w in score_parts)
earned_weight = sum(w for p, w in score_parts if p)
score = round(earned_weight / total_weight, 3) if total_weight > 0 else 0.0
passed = all(c["passed"] for c in checks)

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))