#!/usr/bin/env python3
"""
Evaluation script for the memory-attention-router task.
Usage: python3 eval.py /workspace
"""

import sys
import json
import os
import subprocess
import sqlite3
from pathlib import Path

def run_router(router_path: str, db_path: str, *args) -> dict:
    """Run memory_router.py and return parsed JSON output."""
    env = os.environ.copy()
    env["MAR_DB_PATH"] = db_path
    result = subprocess.run(
        ["python3", router_path] + list(args),
        capture_output=True, text=True, env=env
    )
    try:
        return json.loads(result.stdout)
    except Exception:
        return {"_raw_stdout": result.stdout, "_raw_stderr": result.stderr, "_returncode": result.returncode}

def find_router(workspace: Path) -> str:
    candidates = [
        workspace / "skills" / "memory-attention-router" / "scripts" / "memory_router.py",
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    found = list(workspace.rglob("memory_router.py"))
    if found:
        return str(found[0])
    system = subprocess.run(["find", "/", "-name", "memory_router.py", "-maxdepth", "10"],
                            capture_output=True, text=True)
    hits = [l.strip() for l in system.stdout.splitlines() if l.strip()]
    if hits:
        return hits[0]
    return ""

def find_db(workspace: Path) -> str:
    """Find the SQLite DB used by the agent."""
    # Check env var first
    env_db = os.environ.get("MAR_DB_PATH", "")
    if env_db and Path(env_db).exists():
        return env_db
    # Check default path from SKILL.md
    default = workspace / ".openclaw-memory-router.sqlite3"
    if default.exists():
        return str(default)
    # Check /tmp
    for candidate in ["/tmp/platform-memory-test.sqlite3",
                      "/tmp/memory-attention-router-test.sqlite3"]:
        if Path(candidate).exists():
            return candidate
    # Search
    found = list(workspace.rglob("*.sqlite3"))
    if found:
        return str(found[0])
    tmp_found = subprocess.run(["find", "/tmp", "-name", "*.sqlite3"],
                               capture_output=True, text=True)
    hits = [l.strip() for l in tmp_found.stdout.splitlines() if l.strip()]
    if hits:
        return hits[0]
    return ""

def find_report(workspace: Path) -> Path | None:
    hits = list(workspace.rglob("memory_audit_report.json"))
    if hits:
        return hits[0]
    return None

def query_db(db_path: str, sql: str, params=()):
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        return []

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []

    def add_check(name: str, passed: bool, detail: str):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── Locate key artifacts ─────────────────────────────────────
    router_path = find_router(workspace)
    db_path = find_db(workspace)
    report_path = find_report(workspace)

    add_check(
        "router_exists",
        bool(router_path),
        f"Router found at: {router_path}" if router_path else "memory_router.py not found anywhere"
    )

    add_check(
        "database_exists",
        bool(db_path),
        f"DB found at: {db_path}" if db_path else "No SQLite DB found"
    )

    add_check(
        "report_file_exists",
        report_path is not None,
        f"Report found at: {report_path}" if report_path else "memory_audit_report.json not found"
    )

    if not router_path or not db_path:
        score = sum(c["passed"] for c in checks) / max(len(checks), 1)
        print(json.dumps({"passed": False, "score": round(score, 3), "checks": checks}))
        return

    # ── Load report if available ─────────────────────────────────
    report = {}
    if report_path:
        try:
            report = json.loads(report_path.read_text())
        except Exception as e:
            add_check("report_parseable", False, f"Failed to parse report: {e}")
            report = {}
    else:
        add_check("report_parseable", False, "Report file missing")

    # ── CHECK 1: DB has memories ──────────────────────────────────
    all_memories = query_db(db_path, "SELECT * FROM memories")
    add_check(
        "memories_stored",
        len(all_memories) >= 5,
        f"Found {len(all_memories)} memories in DB (need >= 5)"
    )

    # ── CHECK 2: Stale/replaced preference is inactive ───────────
    # The old "verbose JSON blobs" preference should be retired
    old_prefs = query_db(
        db_path,
        "SELECT * FROM memories WHERE memory_type='preference' AND is_active=0"
    )
    verbose_retired = any(
        m for m in old_prefs
        if any(kw in (m.get("summary", "") + m.get("title", "")).lower()
               for kw in ["verbose", "json blob", "json blobs"])
    )
    # Also check via replaced_by_memory_id
    replaced_prefs = query_db(
        db_path,
        "SELECT * FROM memories WHERE memory_type='preference' AND replaced_by_memory_id IS NOT NULL AND replaced_by_memory_id != ''"
    )
    has_replacement_chain = len(replaced_prefs) >= 1
    add_check(
        "stale_preference_retired",
        verbose_retired or has_replacement_chain,
        f"Stale verbose-output preference retired (is_active=0): {verbose_retired}. "
        f"Replaced_by set on any preference: {has_replacement_chain}. "
        f"Old inactive preferences: {len(old_prefs)}"
    )

    # ── CHECK 3: Retired memory has retired_reason set ───────────
    inactive_with_reason = query_db(
        db_path,
        "SELECT * FROM memories WHERE is_active=0 AND retired_reason IS NOT NULL AND retired_reason != ''"
    )
    add_check(
        "retired_reason_stored",
        len(inactive_with_reason) >= 1,
        f"Inactive memories with retired_reason: {len(inactive_with_reason)}"
    )

    # ── CHECK 4: Reflection memory exists ────────────────────────
    reflections = query_db(
        db_path,
        "SELECT * FROM memories WHERE memory_type='reflection' AND is_active=1"
    )
    add_check(
        "reflection_memory_created",
        len(reflections) >= 1,
        f"Active reflection memories: {len(reflections)}"
    )

    # ── CHECK 5: Procedure memory exists (from reflect or direct add) ──
    procedures = query_db(
        db_path,
        "SELECT * FROM memories WHERE memory_type='procedure' AND is_active=1"
    )
    add_check(
        "procedure_memory_created",
        len(procedures) >= 1,
        f"Active procedure memories: {len(procedures)}"
    )

    # ── CHECK 6: Stale summary refreshed (is_active=0) ───────────
    stale_summaries = query_db(
        db_path,
        "SELECT * FROM memories WHERE memory_type='summary' AND is_active=0"
    )
    add_check(
        "stale_summary_refreshed",
        len(stale_summaries) >= 1,
        f"Inactive summary memories (refreshed): {len(stale_summaries)}"
    )

    # ── CHECK 7: Working memory packets were generated ────────────
    packets = query_db(db_path, "SELECT * FROM working_memory_packets ORDER BY created_at DESC LIMIT 10")
    add_check(
        "packets_generated",
        len(packets) >= 1,
        f"Working memory packets in DB: {len(packets)}"
    )

    # ── CHECK 8: Executor packet has hard_constraints ─────────────
    # Inspect packets for executor role
    exec_packet_data = None
    for pkt in packets:
        try:
            raw = pkt.get("packet_json") or pkt.get("packet") or ""
            data = json.loads(raw) if isinstance(raw, str) and raw else raw
            req_raw = pkt.get("route_request_json") or pkt.get("request") or ""
            req = json.loads(req_raw) if isinstance(req_raw, str) and req_raw else req_raw
            if isinstance(req, dict) and req.get("step_role") == "executor":
                exec_packet_data = data
                break
            # Some versions store role in packet itself
            if isinstance(data, dict):
                inner = data.get("packet", data)
                if isinstance(inner, dict):
                    # Check if it looks executor-ish by presence of hard_constraints
                    if "hard_constraints" in inner:
                        exec_packet_data = inner
        except Exception:
            pass

    # Also try reading from report
    if not exec_packet_data and report:
        exec_packet_data = report.get("executor_packet") or report.get("executor_route")

    # Run a fresh executor route to verify current DB state
    fresh_exec_result = {}
    if router_path and db_path:
        try:
            env = os.environ.copy()
            env["MAR_DB_PATH"] = db_path
            r = subprocess.run(
                ["python3", router_path, "route", "--input-json", json.dumps({
                    "goal": "Execute the platform deployment workflow for Q3 sprint release",
                    "step_role": "executor",
                    "session_id": "sess_platform_q3",
                    "task_id": "task_deploy_wf",
                    "user_constraints": ["Keep outputs under 3 bullets"],
                    "recent_failures": ["OOM on node pool when pre-flight skipped"],
                    "unresolved_questions": ["Is canary threshold set correctly?"]
                })],
                capture_output=True, text=True, env=env
            )
            fresh_exec_result = json.loads(r.stdout)
        except Exception as e:
            fresh_exec_result = {}

    exec_pkt = {}
    if fresh_exec_result:
        exec_pkt = fresh_exec_result.get("packet", fresh_exec_result)

    hard_constraints = exec_pkt.get("hard_constraints", [])
    has_bullet_constraint = any(
        "bullet" in str(c).lower() or "3" in str(c) or "under" in str(c).lower()
        for c in hard_constraints
    )
    add_check(
        "executor_packet_has_hard_constraints",
        len(hard_constraints) >= 1,
        f"executor packet hard_constraints: {hard_constraints}"
    )

    add_check(
        "executor_hard_constraints_cap",
        len(hard_constraints) <= 4,
        f"hard_constraints count={len(hard_constraints)}, cap=4"
    )

    # ── CHECK 9: Executor packet has procedures_to_follow ─────────
    procedures_to_follow = exec_pkt.get("procedures_to_follow", [])
    add_check(
        "executor_packet_has_procedures",
        len(procedures_to_follow) >= 1,
        f"executor packet procedures_to_follow: {procedures_to_follow}"
    )
    add_check(
        "executor_procedures_cap",
        len(procedures_to_follow) <= 3,
        f"procedures_to_follow count={len(procedures_to_follow)}, cap=3"
    )

    # ── CHECK 10: Executor packet has pitfalls_to_avoid ───────────
    pitfalls = exec_pkt.get("pitfalls_to_avoid", [])
    add_check(
        "executor_packet_has_pitfalls",
        len(pitfalls) >= 1,
        f"executor packet pitfalls_to_avoid: {pitfalls}"
    )
    add_check(
        "executor_pitfalls_cap",
        len(pitfalls) <= 3,
        f"pitfalls_to_avoid count={len(pitfalls)}, cap=3"
    )

    # ── CHECK 11: selected_memory_ids cap ─────────────────────────
    sel_ids = exec_pkt.get("selected_memory_ids", [])
    add_check(
        "executor_selected_ids_cap",
        len(sel_ids) <= 5,
        f"selected_memory_ids count={len(sel_ids)}, cap=5"
    )

    # ── CHECK 12: Critic packet has reflection content ─────────────
    fresh_critic_result = {}
    if router_path and db_path:
        try:
            env = os.environ.copy()
            env["MAR_DB_PATH"] = db_path
            r = subprocess.run(
                ["python3", router_path, "route", "--input-json", json.dumps({
                    "goal": "Review the Q3 platform deployment for correctness and policy compliance",
                    "step_role": "critic",
                    "session_id": "sess_platform_q3",
                    "task_id": "task_deploy_wf",
                    "user_constraints": [],
                    "recent_failures": [],
                    "unresolved_questions": ["Were all rollback conditions tested?"]
                })],
                capture_output=True, text=True, env=env
            )
            fresh_critic_result = json.loads(r.stdout)
        except Exception:
            fresh_critic_result = {}

    critic_pkt = fresh_critic_result.get("packet", fresh_critic_result)
    critic_pitfalls = critic_pkt.get("pitfalls_to_avoid", [])
    critic_constraints = critic_pkt.get("hard_constraints", [])
    critic_facts = critic_pkt.get("relevant_facts", [])
    add_check(
        "critic_packet_non_empty",
        len(critic_pitfalls) + len(critic_constraints) + len(critic_facts) >= 1,
        f"critic packet: pitfalls={len(critic_pitfalls)}, constraints={len(critic_constraints)}, facts={len(critic_facts)}"
    )

    # ── CHECK 13: Edges table has graph edges ─────────────────────
    edges = query_db(db_path, "SELECT * FROM memory_edges")
    add_check(
        "graph_edges_created",
        len(edges) >= 1,
        f"Memory graph edges found: {len(edges)} (expects supports or contradicts edges)"
    )

    # ── CHECK 14: Contradiction or supports edge exists ───────────
    typed_edges = query_db(
        db_path,
        "SELECT * FROM memory_edges WHERE edge_type IN ('contradicts', 'supports', 'derived_from')"
    )
    add_check(
        "meaningful_graph_edges",
        len(typed_edges) >= 1,
        f"Contradicts/supports/derived_from edges: {len(typed_edges)}"
    )

    # ── CHECK 15: Report file has executor and critic sections ─────
    if report:
        has_exec = bool(report.get("executor_packet") or report.get("executor_route") or
                        report.get("executor") or
                        any("executor" in str(k).lower() for k in report.keys()))
        has_critic = bool(report.get("critic_packet") or report.get("critic_route") or
                         report.get("critic") or
                         any("critic" in str(k).lower() for k in report.keys()))
        has_memory_ids = any(
            "memory" in str(k).lower() or "id" in str(k).lower()
            for k in report.keys()
        )
        add_check(
            "report_has_executor_section",
            has_exec,
            f"Report keys: {list(report.keys())[:10]}"
        )
        add_check(
            "report_has_critic_section",
            has_critic,
            f"Report keys: {list(report.keys())[:10]}"
        )
    else:
        add_check("report_has_executor_section", False, "Report not loaded")
        add_check("report_has_critic_section", False, "Report not loaded")

    # ── CHECK 16: Relevant_facts cap ──────────────────────────────
    rel_facts = exec_pkt.get("relevant_facts", [])
    add_check(
        "relevant_facts_cap",
        len(rel_facts) <= 3,
        f"relevant_facts count={len(rel_facts)}, cap=3"
    )

    # ── CHECK 17: Active preference exists (the NEW one) ─────────
    active_prefs = query_db(
        db_path,
        "SELECT * FROM memories WHERE memory_type='preference' AND is_active=1"
    )
    concise_pref = any(
        any(kw in (m.get("summary", "") + m.get("title", "")).lower()
            for kw in ["bullet", "concise", "under 3", "3 bullet"])
        for m in active_prefs
    )
    add_check(
        "active_concise_preference_exists",
        len(active_prefs) >= 1,
        f"Active preferences: {len(active_prefs)}. "
        f"Concise/bullet preference found: {concise_pref}"
    )

    # ── Final scoring ─────────────────────────────────────────────
    n_passed = sum(1 for c in checks if c["passed"])
    n_total = len(checks)
    score = round(n_passed / n_total, 3) if n_total > 0 else 0.0
    passed = score >= 0.75  # 75% threshold

    output = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()