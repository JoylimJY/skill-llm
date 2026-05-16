#!/usr/bin/env python3
"""
Evaluation script for the openclaw-agency-agents sandbox task.

Expected workflow the agent MUST have executed:
  1. Run setup.sh  → creates active_agent.conf with agent=none
  2. Run search.sh 跨境  → discovers 跨境电商运营专家
  3. Run activate.sh 跨境电商运营专家
       → backup_1.conf = {agent=none} (pre-activation state)
       → active_agent.conf = {agent=跨境电商运营专家}
  4. Run activate.sh 小红书运营
       → backup_2.conf = {agent=跨境电商运营专家}
       → active_agent.conf = {agent=小红书运营}
  5. Run restore.sh 2
       → restores backup_2.conf → active_agent.conf = {agent=跨境电商运营专家}
       → backup_3.conf = {agent=小红书运营} (auto-saved before restore)

Final state to verify:
  - active_agent.conf: agent=跨境电商运营专家
  - backup_1.conf exists and contains agent=none (or empty agent)
  - backup_2.conf exists and contains agent=跨境电商运营专家
  - At least 3 backup files exist (showing full workflow was executed)
"""

import sys
import json
from pathlib import Path

def read_conf(path: Path) -> dict:
    """Parse a simple key=value config file into a dict."""
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result

def main(workspace_dir: str):
    checks = []
    
    HOME = Path.home()
    SKILL_BASE = HOME / ".openclaw" / "workspace" / "skills" / "openclaw-agency-agents"
    ACTIVE_CONFIG = SKILL_BASE / "active_agent.conf"
    BACKUPS_DIR = SKILL_BASE / "backups"
    REPO_DIR = SKILL_BASE / "repo"

    # ── Check 1: setup.sh was run (active_agent.conf exists) ─────────────────
    try:
        assert ACTIVE_CONFIG.exists(), "active_agent.conf does not exist"
        conf = read_conf(ACTIVE_CONFIG)
        assert "agent" in conf, "active_agent.conf missing 'agent' key"
        checks.append({
            "name": "setup_initialized",
            "passed": True,
            "detail": f"active_agent.conf exists with agent='{conf.get('agent')}'"
        })
    except Exception as e:
        checks.append({
            "name": "setup_initialized",
            "passed": False,
            "detail": f"setup.sh was not run or active_agent.conf is malformed: {e}"
        })

    # ── Check 2: repo initialized ─────────────────────────────────────────────
    try:
        initialized_marker = REPO_DIR / ".initialized"
        assert initialized_marker.exists(), ".initialized marker not found in repo dir"
        checks.append({
            "name": "repo_initialized",
            "passed": True,
            "detail": f"Repo directory initialized at {REPO_DIR}"
        })
    except Exception as e:
        checks.append({
            "name": "repo_initialized",
            "passed": False,
            "detail": f"Repo not initialized: {e}"
        })

    # ── Check 3: At least 2 backup files exist (proves multiple activations) ──
    try:
        backup_files = sorted(BACKUPS_DIR.glob("backup_*.conf"))
        assert len(backup_files) >= 2, \
            f"Expected at least 2 backups (got {len(backup_files)}). " \
            f"Agent must have activated at least 2 personas."
        checks.append({
            "name": "multiple_activations_performed",
            "passed": True,
            "detail": f"Found {len(backup_files)} backup files: {[f.name for f in backup_files]}"
        })
    except Exception as e:
        checks.append({
            "name": "multiple_activations_performed",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 4: backup_1.conf contains agent=none (initial state was backed up)
    try:
        b1 = BACKUPS_DIR / "backup_1.conf"
        assert b1.exists(), "backup_1.conf not found"
        b1_conf = read_conf(b1)
        b1_agent = b1_conf.get("agent", "MISSING")
        assert b1_agent == "none", \
            f"backup_1.conf should contain agent=none (the pre-setup state), got agent='{b1_agent}'"
        checks.append({
            "name": "backup1_is_initial_state",
            "passed": True,
            "detail": f"backup_1.conf correctly contains agent=none (pre-activation state)"
        })
    except Exception as e:
        checks.append({
            "name": "backup1_is_initial_state",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 5: backup_2.conf contains agent=跨境电商运营专家 ──────────────────
    try:
        b2 = BACKUPS_DIR / "backup_2.conf"
        assert b2.exists(), "backup_2.conf not found"
        b2_conf = read_conf(b2)
        b2_agent = b2_conf.get("agent", "MISSING")
        assert b2_agent == "跨境电商运营专家", \
            f"backup_2.conf should contain agent=跨境电商运营专家, got agent='{b2_agent}'"
        checks.append({
            "name": "backup2_is_cross_border_agent",
            "passed": True,
            "detail": f"backup_2.conf correctly contains agent=跨境电商运营专家"
        })
    except Exception as e:
        checks.append({
            "name": "backup2_is_cross_border_agent",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 6: Final active agent is 跨境电商运营专家 (restored state) ─────────
    try:
        assert ACTIVE_CONFIG.exists(), "active_agent.conf missing"
        final_conf = read_conf(ACTIVE_CONFIG)
        final_agent = final_conf.get("agent", "MISSING")
        assert final_agent == "跨境电商运营专家", \
            f"Expected active agent to be '跨境电商运营专家' after restore, got '{final_agent}'"
        checks.append({
            "name": "final_active_agent_is_cross_border",
            "passed": True,
            "detail": f"Active agent correctly restored to '跨境电商运营专家'"
        })
    except Exception as e:
        checks.append({
            "name": "final_active_agent_is_cross_border",
            "passed": False,
            "detail": str(e)
        })

    # ── Check 7: Restore created an additional safety backup (≥3 total) ───────
    try:
        backup_files = sorted(BACKUPS_DIR.glob("backup_*.conf"))
        assert len(backup_files) >= 3, \
            f"restore.sh should auto-save current state before restoring, creating ≥3 backups total. " \
            f"Found only {len(backup_files)}."
        # Verify the 3rd backup (auto-saved during restore) contains 小红书运营
        b3 = BACKUPS_DIR / "backup_3.conf"
        if b3.exists():
            b3_conf = read_conf(b3)
            b3_agent = b3_conf.get("agent", "MISSING")
            assert b3_agent == "小红书运营", \
                f"backup_3.conf (auto-saved before restore) should be agent=小红书运营, got '{b3_agent}'"
            detail = f"backup_3.conf correctly preserves the pre-restore state (agent=小红书运营)"
        else:
            # Accept if there are >= 3 backups even if named differently
            detail = f"Found {len(backup_files)} backups; restore auto-backup confirmed"
        checks.append({
            "name": "restore_created_safety_backup",
            "passed": True,
            "detail": detail
        })
    except Exception as e:
        checks.append({
            "name": "restore_created_safety_backup",
            "passed": False,
            "detail": str(e)
        })

    # ── Score calculation ─────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    # Task is only fully passed if the critical final-state check passes
    critical_checks = ["final_active_agent_is_cross_border", "backup2_is_cross_border_agent",
                       "multiple_activations_performed"]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    overall_passed = critical_passed and score >= 0.85

    result = {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if overall_passed else 1

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    sys.exit(main(workspace))