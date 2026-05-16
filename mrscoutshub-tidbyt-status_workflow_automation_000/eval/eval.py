import json
import sys
import os
import subprocess
import time
import signal
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    score_parts = []

    # ── 1. Find the saved JSON snapshot ──────────────────────────────────────
    snapshot_paths = list(Path(workspace).rglob("agent_status_snapshot.json"))
    # Also check home dir
    home_candidates = list(Path.home().rglob("agent_status_snapshot.json"))
    all_candidates = snapshot_paths + home_candidates

    if not all_candidates:
        checks.append({
            "name": "snapshot_file_exists",
            "passed": False,
            "detail": "agent_status_snapshot.json not found anywhere under workspace or home directory"
        })
        return checks, 0.0

    # Use the first found
    snapshot_file = all_candidates[0]
    checks.append({
        "name": "snapshot_file_exists",
        "passed": True,
        "detail": f"Found snapshot at {snapshot_file}"
    })
    score_parts.append(0.1)

    # ── 2. Parse JSON ─────────────────────────────────────────────────────────
    try:
        with open(snapshot_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        checks.append({"name": "json_parseable", "passed": True, "detail": "Valid JSON"})
        score_parts.append(0.05)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return checks, sum(score_parts)

    # ── 3. Required fields present ────────────────────────────────────────────
    required_fields = ["agent", "emoji", "status", "timestamp", "active_tasks", "last_activity", "recent_activity"]
    missing = [f for f in required_fields if f not in data]
    if not missing:
        checks.append({"name": "required_fields_present", "passed": True,
                        "detail": f"All required fields present: {required_fields}"})
        score_parts.append(0.1)
    else:
        checks.append({"name": "required_fields_present", "passed": False,
                        "detail": f"Missing fields: {missing}"})

    # ── 4. Agent name = "Scout" ───────────────────────────────────────────────
    agent_ok = data.get("agent") == "Scout"
    checks.append({
        "name": "agent_name_is_Scout",
        "passed": agent_ok,
        "detail": f"agent={data.get('agent')!r} (expected 'Scout')"
    })
    if agent_ok:
        score_parts.append(0.05)

    # ── 5. Emoji = 🦅 ─────────────────────────────────────────────────────────
    emoji_ok = data.get("emoji") == "🦅"
    checks.append({
        "name": "emoji_is_eagle",
        "passed": emoji_ok,
        "detail": f"emoji={data.get('emoji')!r} (expected '🦅')"
    })
    if emoji_ok:
        score_parts.append(0.1)

    # ── 6. Status = "working" ─────────────────────────────────────────────────
    status_ok = data.get("status") == "working"
    checks.append({
        "name": "status_is_working",
        "passed": status_ok,
        "detail": f"status={data.get('status')!r} (expected 'working')"
    })
    if status_ok:
        score_parts.append(0.2)

    # ── 7. active_tasks = 2 ───────────────────────────────────────────────────
    tasks_ok = data.get("active_tasks") == 2
    checks.append({
        "name": "active_tasks_equals_2",
        "passed": tasks_ok,
        "detail": f"active_tasks={data.get('active_tasks')!r} (expected 2)"
    })
    if tasks_ok:
        score_parts.append(0.25)

    # ── 8. Verify sessions directory was correctly populated ──────────────────
    sessions_dir = Path.home() / ".openclaw" / "agents" / "main" / "sessions"
    if sessions_dir.exists():
        all_jsonl = list(sessions_dir.glob("*.jsonl"))
        now = time.time()
        # Sub-agent sessions: recently modified, name does not contain 'main'
        fresh_sub = [f for f in all_jsonl
                     if "main" not in f.stem.lower()
                     and (now - f.stat().st_mtime) < 300]
        sessions_check = len(fresh_sub) >= 2
        checks.append({
            "name": "sessions_dir_has_2_fresh_subagent_files",
            "passed": sessions_check,
            "detail": (f"Found {len(fresh_sub)} fresh sub-agent .jsonl files in "
                       f"{sessions_dir} (need >=2). All files: {[f.name for f in all_jsonl]}")
        })
        if sessions_check:
            score_parts.append(0.1)
    else:
        checks.append({
            "name": "sessions_dir_has_2_fresh_subagent_files",
            "passed": False,
            "detail": f"Sessions directory not found: {sessions_dir}"
        })

    # ── 9. Verify non-default port was used (PORT env captured indirectly) ────
    # We check if the snapshot was produced from a non-8765 port by inspecting
    # whether the agent started the server with a custom port configuration.
    # We look for evidence in common locations: process args, log files, or
    # by re-querying on the custom port 9123 if still alive.
    custom_port_evidence = False
    try:
        import urllib.request
        # Try port 9123 first (documented custom port hint in task)
        for port in [9123]:
            try:
                with urllib.request.urlopen(f"http://localhost:{port}/status", timeout=2) as resp:
                    live_data = json.loads(resp.read().decode())
                    if live_data.get("status") == "working" and live_data.get("active_tasks") == 2:
                        custom_port_evidence = True
                        break
            except Exception:
                pass
    except Exception:
        pass

    # Also check log files for port evidence
    if not custom_port_evidence:
        log_locations = [
            Path("/tmp/scout-status.log"),
            Path("/tmp/status_server.log"),
            Path(workspace) / "scout-status.log",
        ]
        for log_path in log_locations:
            try:
                content = log_path.read_text()
                if "9123" in content or "port 9123" in content.lower():
                    custom_port_evidence = True
                    break
            except Exception:
                pass

    checks.append({
        "name": "custom_port_9123_used",
        "passed": custom_port_evidence,
        "detail": ("Server confirmed running on port 9123 with correct state"
                   if custom_port_evidence
                   else "Could not confirm server ran on port 9123 (server may have stopped or wrong port used)")
    })
    if custom_port_evidence:
        score_parts.append(0.05)

    final_score = min(1.0, sum(score_parts))
    return checks, final_score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, score = run_checks(workspace)
    passed = score >= 0.6 and any(c["name"] == "status_is_working" and c["passed"] for c in checks) \
             and any(c["name"] == "active_tasks_equals_2" and c["passed"] for c in checks)
    print(json.dumps({
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()