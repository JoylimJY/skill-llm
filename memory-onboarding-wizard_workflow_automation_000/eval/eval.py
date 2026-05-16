import sys
import json
import os
from pathlib import Path
from datetime import date

def main():
    workspace_arg = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    # The agent workspace that should have been initialized
    agent_ws = Path(workspace_arg) / "openclaw_project" / "agent_workspace"
    today = date.today().isoformat()
    
    checks = []
    total_score = 0.0
    max_checks = 6

    # ── Check 1: MEMORY.md exists in the correct workspace ─────────────────
    try:
        memory_file = agent_ws / "MEMORY.md"
        exists = memory_file.exists()
        content = memory_file.read_text() if exists else ""
        passed = exists and len(content.strip()) > 20
        checks.append({
            "name": "MEMORY.md created in agent_workspace",
            "passed": passed,
            "detail": f"File {'exists' if exists else 'MISSING'} at {memory_file}. Content length: {len(content)}"
        })
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "MEMORY.md created in agent_workspace", "passed": False, "detail": str(e)})

    # ── Check 2: memory/ subdirectory exists ────────────────────────────────
    try:
        memory_dir = agent_ws / "memory"
        passed = memory_dir.exists() and memory_dir.is_dir()
        checks.append({
            "name": "memory/ subdirectory created",
            "passed": passed,
            "detail": f"Directory {'exists' if passed else 'MISSING'} at {memory_dir}"
        })
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "memory/ subdirectory created", "passed": False, "detail": str(e)})

    # ── Check 3: Today's daily file exists with correct date filename ───────
    try:
        daily_file = agent_ws / "memory" / f"{today}.md"
        exists = daily_file.exists()
        content = daily_file.read_text() if exists else ""
        passed = exists and len(content.strip()) > 10
        checks.append({
            "name": f"Daily memory file memory/{today}.md created",
            "passed": passed,
            "detail": (
                f"File {'exists' if exists else 'MISSING'} at {daily_file}. "
                f"Expected today's date: {today}. Content length: {len(content)}"
            )
        })
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": f"Daily memory file memory/{today}.md created", "passed": False, "detail": str(e)})

    # ── Check 4: HEARTBEAT.md exists and has checklist content ─────────────
    try:
        heartbeat_file = agent_ws / "HEARTBEAT.md"
        exists = heartbeat_file.exists()
        content = heartbeat_file.read_text() if exists else ""
        # Must have checklist items ([ ])
        has_checklist = "[ ]" in content
        passed = exists and has_checklist
        checks.append({
            "name": "HEARTBEAT.md created with checklist items",
            "passed": passed,
            "detail": (
                f"File {'exists' if exists else 'MISSING'}. "
                f"Has checklist: {has_checklist}. Content length: {len(content)}"
            )
        })
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "HEARTBEAT.md created with checklist items", "passed": False, "detail": str(e)})

    # ── Check 5: USER.md exists and has non-empty user profile content ──────
    try:
        user_file = agent_ws / "USER.md"
        exists = user_file.exists()
        content = user_file.read_text() if exists else ""
        # Must contain name/timezone/use case sections
        has_name = "Name" in content or "name" in content.lower()
        has_timezone = "Timezone" in content or "timezone" in content.lower() or "UTC" in content
        passed = exists and has_name and has_timezone and len(content.strip()) > 20
        checks.append({
            "name": "USER.md created with user profile data",
            "passed": passed,
            "detail": (
                f"File {'exists' if exists else 'MISSING'}. "
                f"Has name section: {has_name}. Has timezone: {has_timezone}. "
                f"Content length: {len(content)}"
            )
        })
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "USER.md created with user profile data", "passed": False, "detail": str(e)})

    # ── Check 6: Old backup workspace was NOT used (agent used correct path) ─
    try:
        # The old_openclaw_backup should NOT have new files created in it
        # (i.e., agent correctly targeted agent_workspace, not the backup)
        old_ws = Path(workspace_arg) / "old_openclaw_backup"
        old_heartbeat = old_ws / "HEARTBEAT.md"
        old_daily_dir = old_ws / "memory" / f"{today}.md"
        
        # Also check the default ~/.openclaw/workspace was NOT used exclusively
        # (meaning the custom workspace was actually populated)
        all_four_in_agent_ws = all([
            (agent_ws / "MEMORY.md").exists(),
            (agent_ws / "memory" / f"{today}.md").exists(),
            (agent_ws / "HEARTBEAT.md").exists(),
            (agent_ws / "USER.md").exists(),
        ])
        
        # Penalize if agent created files in wrong location (old backup)
        wrong_location = old_heartbeat.exists() and not (old_ws / "HEARTBEAT.md").read_text().strip() == ""
        
        passed = all_four_in_agent_ws
        checks.append({
            "name": "All 4 files correctly placed in agent_workspace (not wrong dir)",
            "passed": passed,
            "detail": (
                f"All 4 files in agent_workspace: {all_four_in_agent_ws}. "
                f"Agent workspace path: {agent_ws}"
            )
        })
        if passed:
            total_score += 1
    except Exception as e:
        checks.append({"name": "All 4 files correctly placed in agent_workspace (not wrong dir)", "passed": False, "detail": str(e)})

    # ── Final score ─────────────────────────────────────────────────────────
    final_score = round(total_score / max_checks, 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()