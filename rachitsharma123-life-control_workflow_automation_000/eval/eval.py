#!/usr/bin/env python3
"""
Evaluation script for the Life Control skill task.
Checks:
  1. agents-config.json created with all 4 correct OpenClaw personas
  2. All 4 personas registered in the DB (lc fleet)
  3. At least one goal added per persona (all 4 agent IDs present in goals table)
  4. qlog entries exist for at least 3 distinct metric types across agents
  5. At least one routine log file exists (logs/<agent_id>-<routine>.log)
  6. At least one notification queue file exists (db/notify-queue-<agent_id>.txt)
"""
import sys
import json
import sqlite3
import os
from pathlib import Path

def main(workspace: str):
    ws = Path(workspace)
    db_path = ws / "skills/life-control/db/life-control.db"
    ref_dir  = ws / "skills/life-control/references"
    log_dir  = ws / "skills/life-control/logs"
    db_dir   = ws / "skills/life-control/db"

    checks = []
    total_score = 0.0

    EXPECTED_AGENTS = {
        "oc-001": {"name": "Aurelius", "domain_kw": "wellness"},
        "oc-002": {"name": "Cassian",  "domain_kw": "finance"},
        "oc-003": {"name": "Vesper",   "domain_kw": "social"},
        "oc-004": {"name": "Solenne",  "domain_kw": "spiritual"},
    }

    # ── Check 1: agents-config.json exists and is correct ─────────────────────
    config_files = list(ref_dir.rglob("agents-config.json"))
    if not config_files:
        checks.append({
            "name": "agents-config.json created",
            "passed": False,
            "detail": "File not found in skills/life-control/references/"
        })
    else:
        try:
            cfg = json.loads(config_files[0].read_text())
            agents_in_cfg = {a["agent_id"]: a for a in cfg.get("agents", [])}
            missing = [aid for aid in EXPECTED_AGENTS if aid not in agents_in_cfg]
            wrong_names = []
            for aid, expected in EXPECTED_AGENTS.items():
                if aid in agents_in_cfg:
                    actual_name = agents_in_cfg[aid].get("name", "")
                    if actual_name.lower() != expected["name"].lower():
                        wrong_names.append(
                            f"{aid}: expected '{expected['name']}', got '{actual_name}'"
                        )
            if missing:
                checks.append({
                    "name": "agents-config.json created",
                    "passed": False,
                    "detail": f"Missing agent IDs: {missing}"
                })
            elif wrong_names:
                checks.append({
                    "name": "agents-config.json created",
                    "passed": False,
                    "detail": f"Wrong persona names: {wrong_names}"
                })
            else:
                checks.append({
                    "name": "agents-config.json created",
                    "passed": True,
                    "detail": f"Found correct 4 personas in {config_files[0]}"
                })
                total_score += 20
        except Exception as e:
            checks.append({
                "name": "agents-config.json created",
                "passed": False,
                "detail": f"Parse error: {e}"
            })

    # ── Check 2: DB exists and all 4 agents registered ────────────────────────
    if not db_path.exists():
        checks.append({
            "name": "DB initialized with all 4 personas",
            "passed": False,
            "detail": f"DB not found at {db_path}"
        })
    else:
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT agent_id, name, domain, status FROM agents ORDER BY agent_id"
            ).fetchall()
            registered = {r["agent_id"]: r for r in rows}
            missing_in_db = [aid for aid in EXPECTED_AGENTS if aid not in registered]
            inactive = [aid for aid in EXPECTED_AGENTS
                        if aid in registered and registered[aid]["status"] != "active"]
            wrong_db_names = []
            for aid, expected in EXPECTED_AGENTS.items():
                if aid in registered:
                    actual = registered[aid]["name"]
                    if actual.lower() != expected["name"].lower():
                        wrong_db_names.append(
                            f"{aid}: expected '{expected['name']}', got '{actual}'"
                        )
            if missing_in_db:
                checks.append({
                    "name": "DB initialized with all 4 personas",
                    "passed": False,
                    "detail": f"Missing from DB: {missing_in_db}"
                })
            elif inactive:
                checks.append({
                    "name": "DB initialized with all 4 personas",
                    "passed": False,
                    "detail": f"Agents not active: {inactive}"
                })
            elif wrong_db_names:
                checks.append({
                    "name": "DB initialized with all 4 personas",
                    "passed": False,
                    "detail": f"Name mismatch in DB: {wrong_db_names}"
                })
            else:
                checks.append({
                    "name": "DB initialized with all 4 personas",
                    "passed": True,
                    "detail": f"All 4 personas active in DB: {list(registered.keys())}"
                })
                total_score += 20
            conn.close()
        except Exception as e:
            checks.append({
                "name": "DB initialized with all 4 personas",
                "passed": False,
                "detail": f"DB error: {e}"
            })

    # ── Check 3: At least one goal per persona ────────────────────────────────
    if not db_path.exists():
        checks.append({
            "name": "Goals added for all personas",
            "passed": False,
            "detail": "DB not found"
        })
    else:
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            # Ensure goals table exists
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
            if "goals" not in tables:
                checks.append({
                    "name": "Goals added for all personas",
                    "passed": False,
                    "detail": "Goals table does not exist"
                })
            else:
                goals = conn.execute(
                    "SELECT DISTINCT agent_id FROM goals"
                ).fetchall()
                agents_with_goals = {r["agent_id"] for r in goals}
                missing_goals = [aid for aid in EXPECTED_AGENTS
                                 if aid not in agents_with_goals]
                if missing_goals:
                    checks.append({
                        "name": "Goals added for all personas",
                        "passed": False,
                        "detail": f"No goals for: {missing_goals}"
                    })
                else:
                    checks.append({
                        "name": "Goals added for all personas",
                        "passed": True,
                        "detail": f"Goals present for: {sorted(agents_with_goals)}"
                    })
                    total_score += 20
            conn.close()
        except Exception as e:
            checks.append({
                "name": "Goals added for all personas",
                "passed": False,
                "detail": f"DB error: {e}"
            })

    # ── Check 4: qlog entries with valid metric types ─────────────────────────
    VALID_METRICS = {"protein", "water", "workout", "expense", "meditate"}
    if not db_path.exists():
        checks.append({
            "name": "qlog entries with >=3 distinct metric types",
            "passed": False,
            "detail": "DB not found"
        })
    else:
        try:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
            if "logs" not in tables:
                checks.append({
                    "name": "qlog entries with >=3 distinct metric types",
                    "passed": False,
                    "detail": "Logs table does not exist"
                })
            else:
                log_rows = conn.execute(
                    "SELECT DISTINCT metric FROM logs WHERE metric IN "
                    "('protein','water','workout','expense','meditate')"
                ).fetchall()
                found_metrics = {r["metric"] for r in log_rows}
                invalid_rows = conn.execute(
                    "SELECT metric FROM logs WHERE metric NOT IN "
                    "('protein','water','workout','expense','meditate')"
                ).fetchall()
                invalid_metrics = [r["metric"] for r in invalid_rows]
                if len(found_metrics) < 3:
                    checks.append({
                        "name": "qlog entries with >=3 distinct metric types",
                        "passed": False,
                        "detail": (
                            f"Only {len(found_metrics)} valid metric types logged: "
                            f"{found_metrics}. Need at least 3 from {VALID_METRICS}."
                            + (f" Invalid entries found: {invalid_metrics}" if invalid_metrics else "")
                        )
                    })
                else:
                    checks.append({
                        "name": "qlog entries with >=3 distinct metric types",
                        "passed": True,
                        "detail": f"Valid metric types logged: {sorted(found_metrics)}"
                    })
                    total_score += 20
            conn.close()
        except Exception as e:
            checks.append({
                "name": "qlog entries with >=3 distinct metric types",
                "passed": False,
                "detail": f"DB error: {e}"
            })

    # ── Check 5: Routine log file exists ─────────────────────────────────────
    log_files = list(log_dir.glob("oc-*-*.log"))
    # Filter out .gitkeep
    log_files = [f for f in log_files if f.stat().st_size > 0]
    if not log_files:
        checks.append({
            "name": "Routine executed and log produced",
            "passed": False,
            "detail": f"No routine log files found in {log_dir}"
        })
    else:
        # Verify at least one log has valid routine content
        valid_log = None
        for lf in log_files:
            content = lf.read_text()
            if "Routine complete" in content or "Running for agent" in content:
                valid_log = lf
                break
        if valid_log:
            checks.append({
                "name": "Routine executed and log produced",
                "passed": True,
                "detail": f"Valid routine log: {valid_log.name}"
            })
            total_score += 10
        else:
            checks.append({
                "name": "Routine executed and log produced",
                "passed": False,
                "detail": f"Log files exist but none contain valid routine output: {[f.name for f in log_files]}"
            })

    # ── Check 6: Notification queue file ─────────────────────────────────────
    queue_files = list(db_dir.glob("notify-queue-oc-*.txt"))
    queue_files = [f for f in queue_files if f.stat().st_size > 0]
    if not queue_files:
        checks.append({
            "name": "Notification queued for at least one persona",
            "passed": False,
            "detail": f"No notify-queue-oc-*.txt files in {db_dir}"
        })
    else:
        # Verify queue file has valid format: timestamp|message
        valid_queue = None
        for qf in queue_files:
            lines = [l.strip() for l in qf.read_text().splitlines() if l.strip()]
            for line in lines:
                if "|" in line:
                    valid_queue = qf
                    break
            if valid_queue:
                break
        if valid_queue:
            checks.append({
                "name": "Notification queued for at least one persona",
                "passed": True,
                "detail": f"Valid queue file: {valid_queue.name}"
            })
            total_score += 10
        else:
            checks.append({
                "name": "Notification queued for at least one persona",
                "passed": False,
                "detail": f"Queue files exist but none have valid format: {[f.name for f in queue_files]}"
            })

    passed = all(c["passed"] for c in checks)
    score = round(total_score / 100.0, 2)

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return 0 if passed else 1

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    sys.exit(main(workspace))