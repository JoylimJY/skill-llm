import sys
import json
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
NAS_HOME = Path("/nas_home")
NAS_USER = "nas-user"
NAS_HOST = "localhost"

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

def ssh_exists(remote_path):
    """Check if a path exists on the mock NAS via SSH."""
    try:
        result = subprocess.run(
            ["ssh", f"{NAS_USER}@{NAS_HOST}", f"test -e {remote_path} && echo EXISTS || echo MISSING"],
            capture_output=True, text=True, timeout=10
        )
        return "EXISTS" in result.stdout
    except Exception as e:
        return False

def ssh_isdir(remote_path):
    try:
        result = subprocess.run(
            ["ssh", f"{NAS_USER}@{NAS_HOST}", f"test -d {remote_path} && echo DIR || echo NOTDIR"],
            capture_output=True, text=True, timeout=10
        )
        return "DIR" in result.stdout
    except Exception:
        return False

def ssh_read(remote_path):
    try:
        result = subprocess.run(
            ["ssh", f"{NAS_USER}@{NAS_HOST}", f"cat {remote_path}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout
        return None
    except Exception:
        return None

# ---- CHECK 1: _agents/ directories for all 5 agents ----
required_agents = ["coordinator", "editor", "renderer", "sound", "marketing"]
agent_dirs_ok = []
agent_dirs_fail = []
for agent in required_agents:
    path = f"~/_agents/{agent}"
    # Resolve ~ for nas-user
    resolved = f"/nas_home/_agents/{agent}"
    if ssh_isdir(resolved):
        agent_dirs_ok.append(agent)
    else:
        agent_dirs_fail.append(agent)

if len(agent_dirs_ok) == len(required_agents):
    add_check(
        "NAS _agents/ subdirectories for all 5 agents",
        True,
        f"All agent dirs found: {agent_dirs_ok}"
    )
else:
    add_check(
        "NAS _agents/ subdirectories for all 5 agents",
        False,
        f"Missing: {agent_dirs_fail}, Found: {agent_dirs_ok}"
    )

# ---- CHECK 2: _shared/ structure ----
shared_config_ok = ssh_isdir("/nas_home/_shared/config")
shared_templates_ok = ssh_isdir("/nas_home/_shared/templates")
shared_ok = shared_config_ok and shared_templates_ok
add_check(
    "NAS _shared/config and _shared/templates directories",
    shared_ok,
    f"_shared/config: {shared_config_ok}, _shared/templates: {shared_templates_ok}"
)

# ---- CHECK 3: _backups/ structure ----
backups_memory_ok = ssh_isdir("/nas_home/_backups/memory")
add_check(
    "NAS _backups/memory directory",
    backups_memory_ok,
    f"_backups/memory exists: {backups_memory_ok}"
)

# ---- CHECK 4: agent-directory.json existence ----
agent_dir_path = "/nas_home/_shared/config/agent-directory.json"
agent_dir_content = ssh_read(agent_dir_path)
if agent_dir_content:
    add_check("agent-directory.json exists at _shared/config/", True, "File found and readable.")
else:
    add_check("agent-directory.json exists at _shared/config/", False, "File not found or unreadable.")

# ---- CHECK 5: agent-directory.json schema correctness ----
if agent_dir_content:
    try:
        data = json.loads(agent_dir_content)
        schema_issues = []

        # Must have top-level keys: agents, shared, basePath
        for key in ["agents", "shared", "basePath"]:
            if key not in data:
                schema_issues.append(f"Missing top-level key: '{key}'")

        # Each agent entry must have 'role' and 'path'
        if "agents" in data:
            agents_data = data["agents"]
            for agent in required_agents:
                if agent not in agents_data:
                    schema_issues.append(f"Agent '{agent}' missing from 'agents' dict")
                else:
                    entry = agents_data[agent]
                    if "role" not in entry:
                        schema_issues.append(f"Agent '{agent}' missing 'role' field")
                    if "path" not in entry:
                        schema_issues.append(f"Agent '{agent}' missing 'path' field")
                    else:
                        # path must reference _agents/{agent}
                        if f"_agents/{agent}" not in entry["path"]:
                            schema_issues.append(f"Agent '{agent}' path '{entry['path']}' doesn't reference _agents/{agent}/")

        # coordinator must be File Master role
        if "agents" in data and "coordinator" in data["agents"]:
            coord_role = data["agents"]["coordinator"].get("role", "")
            # Accept role names containing "File Master" or "Coordinator" — per task brief coordinator is File Master
            # Per skill.md the File Master is explicitly designated; task says coordinator is File Master
            if "file master" not in coord_role.lower() and "coordinator" not in coord_role.lower():
                schema_issues.append(f"coordinator role '{coord_role}' doesn't match expected role")

        # shared must reference _shared
        if "shared" in data and "_shared" not in str(data["shared"]):
            schema_issues.append(f"'shared' value '{data['shared']}' doesn't reference _shared/")

        # basePath should be ~/ or /nas_home/ or similar home ref
        if "basePath" in data:
            bp = str(data["basePath"])
            if not (bp.startswith("~/") or bp == "~/" or "/nas_home" in bp or bp == "~/"):
                schema_issues.append(f"'basePath' value '{bp}' doesn't look like a home path (expected ~/ or similar)")

        if not schema_issues:
            add_check(
                "agent-directory.json schema correctness",
                True,
                f"Schema valid. Agents found: {list(data.get('agents', {}).keys())}"
            )
        else:
            add_check(
                "agent-directory.json schema correctness",
                False,
                f"Schema issues: {'; '.join(schema_issues)}"
            )
    except json.JSONDecodeError as e:
        add_check("agent-directory.json schema correctness", False, f"JSON parse error: {e}")
else:
    add_check("agent-directory.json schema correctness", False, "File not available for schema check.")

# ---- CHECK 6: backup-cron.json exists in workspace ----
cron_files = list(workspace.rglob("backup-cron.json"))
if cron_files:
    cron_file = cron_files[0]
    add_check("backup-cron.json exists in workspace", True, f"Found at: {cron_file}")
else:
    cron_file = None
    add_check("backup-cron.json exists in workspace", False, "backup-cron.json not found anywhere in workspace.")

# ---- CHECK 7: backup-cron.json proprietary schema ----
if cron_file:
    try:
        cron_data = json.loads(cron_file.read_text())
        cron_issues = []

        # Must have 'schedule' with kind=cron, expr, tz
        schedule = cron_data.get("schedule", {})
        if not isinstance(schedule, dict):
            cron_issues.append("'schedule' must be an object")
        else:
            if schedule.get("kind") != "cron":
                cron_issues.append(f"schedule.kind must be 'cron', got: '{schedule.get('kind')}'")
            expr = schedule.get("expr", "")
            if expr != "0 3 * * *":
                cron_issues.append(f"schedule.expr must be '0 3 * * *' (daily at 3am UTC), got: '{expr}'")
            tz = schedule.get("tz", "")
            if tz != "UTC":
                cron_issues.append(f"schedule.tz must be 'UTC', got: '{tz}'")

        # Must have 'payload' with kind=agentTurn and a message
        payload = cron_data.get("payload", {})
        if not isinstance(payload, dict):
            cron_issues.append("'payload' must be an object")
        else:
            if payload.get("kind") != "agentTurn":
                cron_issues.append(f"payload.kind must be 'agentTurn', got: '{payload.get('kind')}'")
            msg = payload.get("message", "")
            if not msg:
                cron_issues.append("payload.message must be non-empty")
            else:
                # Message should reference backup and agents
                msg_lower = msg.lower()
                if "backup" not in msg_lower and "rsync" not in msg_lower:
                    cron_issues.append(f"payload.message should reference backup operation, got: '{msg[:80]}'")
                # Should reference agent workspaces/memory
                if "memory" not in msg_lower and "workspace" not in msg_lower and "agent" not in msg_lower:
                    cron_issues.append(f"payload.message should reference agent workspaces or memory")

        # Must have sessionTarget = isolated
        session_target = cron_data.get("sessionTarget", "")
        if session_target != "isolated":
            cron_issues.append(f"sessionTarget must be 'isolated', got: '{session_target}'")

        if not cron_issues:
            add_check(
                "backup-cron.json proprietary schema correctness",
                True,
                f"All proprietary fields correct: schedule={schedule}, sessionTarget=isolated"
            )
        else:
            add_check(
                "backup-cron.json proprietary schema correctness",
                False,
                f"Schema issues: {'; '.join(cron_issues)}"
            )
    except json.JSONDecodeError as e:
        add_check("backup-cron.json proprietary schema correctness", False, f"JSON parse error: {e}")
else:
    add_check("backup-cron.json proprietary schema correctness", False, "backup-cron.json not available.")

# ---- CHECK 8: memory-backup subdirs exist for agents (bonus/rsync structure) ----
# Per SKILL.md: rsync backs up to ~/_agents/{agent}/memory-backup/
# At least verify the structure makes sense — optional but shows full workflow
memory_backup_agents = []
for agent in required_agents:
    path = f"/nas_home/_agents/{agent}/memory-backup"
    if ssh_isdir(path):
        memory_backup_agents.append(agent)

if len(memory_backup_agents) >= 1:
    add_check(
        "memory-backup subdirectories exist under agent folders",
        True,
        f"memory-backup dirs found for: {memory_backup_agents}"
    )
else:
    add_check(
        "memory-backup subdirectories exist under agent folders",
        False,
        "No _agents/{agent}/memory-backup/ directories found. Expected per SKILL.md backup structure."
    )

# ---- SCORING ----
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
# Weight critical checks more heavily
critical_checks = [
    "NAS _agents/ subdirectories for all 5 agents",
    "agent-directory.json schema correctness",
    "backup-cron.json proprietary schema correctness",
]
critical_passed = sum(1 for c in checks if c["passed"] and c["name"] in critical_checks)
critical_total = len(critical_checks)

# Score: 60% weight on critical checks, 40% on others
if critical_total > 0 and (total - critical_total) > 0:
    critical_score = (critical_passed / critical_total) * 0.60
    other_passed = sum(1 for c in checks if c["passed"] and c["name"] not in critical_checks)
    other_score = (other_passed / (total - critical_total)) * 0.40
    score = round(critical_score + other_score, 3)
else:
    score = round(passed_count / total, 3) if total > 0 else 0.0

overall_passed = (critical_passed == critical_total) and (passed_count >= total - 2)

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))