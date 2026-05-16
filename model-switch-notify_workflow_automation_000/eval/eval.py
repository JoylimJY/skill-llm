#!/usr/bin/env python3
"""
Evaluation script for the model-switch-notify skill task.
Checks:
1. session_audit.json exists and has correct structure/content
2. The pending notification was correctly surfaced (pendingNotify=true, correct prefix)
3. The simultaneous model change was detected (changed=true, correct models)
4. After check, pending_notify is cleared in DB (auto-clear)
5. agents_status.json exists and lists expected agents (list command output)
6. heartbeat was called for the "analyst" agent (last_heartbeat updated)
"""

import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta

def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    total_score = 0.0

    # ── Find session_audit.json ────────────────────────────────────────────────
    audit_files = list(workspace.rglob("session_audit.json"))
    audit_data = None

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # CHECK 1: session_audit.json exists
    if audit_files:
        try:
            audit_data = load_json(audit_files[0])
            score = add_check(
                "session_audit.json exists and is valid JSON",
                True,
                f"Found at {audit_files[0]}"
            )
            total_score += score
        except Exception as e:
            total_score += add_check(
                "session_audit.json exists and is valid JSON",
                False,
                f"File found but invalid JSON: {e}"
            )
    else:
        total_score += add_check(
            "session_audit.json exists and is valid JSON",
            False,
            "session_audit.json not found anywhere in workspace"
        )

    # CHECK 2: pendingNotify is true (interrupt was set and check surfaced it)
    if audit_data is not None:
        pn = audit_data.get("pendingNotify", None)
        total_score += add_check(
            "pendingNotify is true in session_audit.json",
            pn is True,
            f"pendingNotify = {pn!r} (expected true)"
        )
    else:
        total_score += add_check(
            "pendingNotify is true in session_audit.json",
            False,
            "Cannot check: session_audit.json missing or invalid"
        )

    # CHECK 3: pendingMessage has correct [上次未发送] prefix
    if audit_data is not None:
        pm = audit_data.get("pendingMessage", None)
        correct_prefix = isinstance(pm, str) and pm.startswith("[上次未发送]")
        total_score += add_check(
            "pendingMessage has correct [上次未发送] prefix",
            correct_prefix,
            f"pendingMessage = {pm!r}"
        )
    else:
        total_score += add_check(
            "pendingMessage has correct [上次未发送] prefix",
            False,
            "Cannot check: audit data missing"
        )

    # CHECK 4: changed is true and correct model switch detected
    if audit_data is not None:
        changed = audit_data.get("changed", False)
        current_model = audit_data.get("currentModel", "")
        prev_model = audit_data.get("previousModel", "")
        # The analyst was last on "ollama/deepseek-r1:7b"
        # The interrupt stores the model the interrupt was called with
        # The new check should be with a DIFFERENT model from deepseek-r1:7b
        # We check: changed=true, currentModel is not deepseek-r1:7b
        correct_change = (
            changed is True and
            current_model != "" and
            "deepseek-r1" not in current_model
        )
        total_score += add_check(
            "Model change detected (changed=true, currentModel updated)",
            correct_change,
            f"changed={changed}, currentModel={current_model!r}, previousModel={prev_model!r}"
        )
    else:
        total_score += add_check(
            "Model change detected (changed=true, currentModel updated)",
            False,
            "Cannot check: audit data missing"
        )

    # CHECK 5: shouldNotify is true
    if audit_data is not None:
        sn = audit_data.get("shouldNotify", False)
        total_score += add_check(
            "shouldNotify is true",
            sn is True,
            f"shouldNotify = {sn!r}"
        )
    else:
        total_score += add_check(
            "shouldNotify is true",
            False,
            "Cannot check: audit data missing"
        )

    # CHECK 6: notifyMessage contains correct model switch template
    if audit_data is not None:
        nm = audit_data.get("notifyMessage", None)
        # Should contain "老板，模型已切换，当前使用：" + current model
        correct_msg = isinstance(nm, str) and "老板，模型已切换，当前使用：" in nm
        total_score += add_check(
            "notifyMessage contains correct model switch template (老板，模型已切换)",
            correct_msg,
            f"notifyMessage = {nm!r}"
        )
    else:
        total_score += add_check(
            "notifyMessage contains correct model switch template",
            False,
            "Cannot check: audit data missing"
        )

    # CHECK 7: DB state — pending_notify is cleared for analyst after check
    db_path = Path.home() / ".openclaw" / "data" / "model-switch.db"
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM model_states WHERE agent_id=?", ("analyst",)
        ).fetchone()
        if row:
            pending_cleared = row["pending_notify"] == 0
            total_score += add_check(
                "pending_notify cleared in DB after check",
                pending_cleared,
                f"pending_notify={row['pending_notify']} in DB for analyst"
            )
        else:
            total_score += add_check(
                "pending_notify cleared in DB after check",
                False,
                "analyst row not found in DB — check was never called"
            )
        conn.close()
    except Exception as e:
        total_score += add_check(
            "pending_notify cleared in DB after check",
            False,
            f"DB read error: {e}"
        )

    # CHECK 8: agents_status.json exists and lists agents
    status_files = list(workspace.rglob("agents_status.json"))
    agents_status = None
    if status_files:
        try:
            agents_status = load_json(status_files[0])
            # Must be a list of agent records
            is_list = isinstance(agents_status, list)
            has_agents = is_list and len(agents_status) >= 2
            agent_ids = [r.get("agent_id") for r in agents_status] if is_list else []
            has_analyst = "analyst" in agent_ids
            score = add_check(
                "agents_status.json is valid list with expected agents",
                has_agents and has_analyst,
                f"agents found: {agent_ids}"
            )
            total_score += score
        except Exception as e:
            total_score += add_check(
                "agents_status.json is valid list with expected agents",
                False,
                f"Invalid JSON: {e}"
            )
    else:
        total_score += add_check(
            "agents_status.json exists and lists agents",
            False,
            "agents_status.json not found anywhere in workspace"
        )

    # CHECK 9: heartbeat was updated for analyst (last_heartbeat is recent)
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT last_heartbeat, last_model FROM model_states WHERE agent_id=?",
            ("analyst",)
        ).fetchone()
        if row and row["last_heartbeat"]:
            hb_str = row["last_heartbeat"]
            # Accept any recent ISO datetime (within last 10 minutes)
            try:
                hb_dt = datetime.fromisoformat(hb_str.rstrip("Z"))
                recent = (datetime.utcnow() - hb_dt) < timedelta(minutes=10)
                total_score += add_check(
                    "heartbeat updated recently for analyst agent",
                    recent,
                    f"last_heartbeat={hb_str}"
                )
            except Exception as pe:
                total_score += add_check(
                    "heartbeat updated recently for analyst agent",
                    False,
                    f"Could not parse heartbeat timestamp: {hb_str} / {pe}"
                )
        else:
            total_score += add_check(
                "heartbeat updated recently for analyst agent",
                False,
                "No last_heartbeat found for analyst"
            )
        conn.close()
    except Exception as e:
        total_score += add_check(
            "heartbeat updated recently for analyst agent",
            False,
            f"DB error: {e}"
        )

    # ── Final scoring ──────────────────────────────────────────────────────────
    num_checks = len(checks)
    final_score = total_score / num_checks if num_checks > 0 else 0.0
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed,
        "score": round(final_score, 3),
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()