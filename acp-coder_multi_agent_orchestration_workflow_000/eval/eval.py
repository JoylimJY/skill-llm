#!/usr/bin/env python3
"""
Evaluation script for ACP orchestration task.
Validates that the agent correctly followed the ACP multi-agent orchestration protocol.
"""

import sys
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

def load_call_log(workspace: str) -> List[Dict]:
    log_path = os.path.join(workspace, "call_log.jsonl")
    calls = []
    try:
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    calls.append(json.loads(line))
    except FileNotFoundError:
        pass
    except Exception as e:
        pass
    return calls

def get_calls_by_tool(calls: List[Dict], tool: str) -> List[Dict]:
    return [c for c in calls if c.get("tool") == tool]

def get_spawn_calls(calls: List[Dict]) -> List[Dict]:
    return get_calls_by_tool(calls, "sessions_spawn")

def get_yield_calls(calls: List[Dict]) -> List[Dict]:
    return get_calls_by_tool(calls, "sessions_yield")

def get_list_calls(calls: List[Dict]) -> List[Dict]:
    return get_calls_by_tool(calls, "sessions_list")

def get_history_calls(calls: List[Dict]) -> List[Dict]:
    return get_calls_by_tool(calls, "sessions_history")

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    calls = load_call_log(workspace)
    spawn_calls = get_spawn_calls(calls)
    yield_calls = get_yield_calls(calls)
    list_calls = get_list_calls(calls)
    history_calls = get_history_calls(calls)

    checks = []

    # ── CHECK 1: At least 4 sessions_spawn calls (3 stages + 1 resumeSessionId for truncation) ──
    try:
        # Must have at least 3 new spawns for template C + 1 resume spawn for truncated content
        total_spawns = len(spawn_calls)
        new_spawns = [s for s in spawn_calls if not s["params"].get("resumeSessionId")]
        resume_spawns = [s for s in spawn_calls if s["params"].get("resumeSessionId")]
        passed = total_spawns >= 4 and len(new_spawns) >= 3 and len(resume_spawns) >= 1
        checks.append({
            "name": "template_C_three_stage_plus_resume_spawn",
            "passed": passed,
            "detail": f"Total spawns: {total_spawns}, new: {len(new_spawns)}, resume: {len(resume_spawns)}. "
                      f"Expected >=4 total, >=3 new (plan/implement/review), >=1 resume (for truncated stage)."
        })
    except Exception as e:
        checks.append({"name": "template_C_three_stage_plus_resume_spawn", "passed": False, "detail": str(e)})

    # ── CHECK 2: All spawn calls must have streamTo: "parent" ──
    try:
        missing_stream_to = [
            i for i, s in enumerate(spawn_calls)
            if s.get("params", {}).get("streamTo") != "parent"
        ]
        passed = len(missing_stream_to) == 0
        checks.append({
            "name": "all_spawns_have_streamTo_parent",
            "passed": passed,
            "detail": f"Spawn calls missing streamTo='parent': indices {missing_stream_to}. "
                      f"ALL sessions_spawn calls must include streamTo: 'parent'."
        })
    except Exception as e:
        checks.append({"name": "all_spawns_have_streamTo_parent", "passed": False, "detail": str(e)})

    # ── CHECK 3: No spawn has both timeoutSeconds/runTimeoutSeconds AND streamTo: parent ──
    try:
        conflicting = [
            i for i, s in enumerate(spawn_calls)
            if s.get("params", {}).get("streamTo") == "parent"
            and (
                "timeoutSeconds" in s.get("params", {})
                or "runTimeoutSeconds" in s.get("params", {})
            )
        ]
        passed = len(conflicting) == 0
        checks.append({
            "name": "no_timeout_with_streamTo_parent",
            "passed": passed,
            "detail": f"Spawn calls with timeoutSeconds/runTimeoutSeconds AND streamTo='parent': {conflicting}. "
                      f"These must NOT be combined (causes sync mode conflict)."
        })
    except Exception as e:
        checks.append({"name": "no_timeout_with_streamTo_parent", "passed": False, "detail": str(e)})

    # ── CHECK 4: sessions_yield called at least 4 times (once after each spawn) ──
    try:
        passed = len(yield_calls) >= 4
        checks.append({
            "name": "sessions_yield_called_after_each_spawn",
            "passed": passed,
            "detail": f"sessions_yield called {len(yield_calls)} times. "
                      f"Expected >=4 (non-blocking protocol: yield after every spawn)."
        })
    except Exception as e:
        checks.append({"name": "sessions_yield_called_after_each_spawn", "passed": False, "detail": str(e)})

    # ── CHECK 5: sessions_list called after each new spawn (to capture sessionId) ──
    try:
        passed = len(list_calls) >= 3
        checks.append({
            "name": "sessions_list_called_to_capture_session_ids",
            "passed": passed,
            "detail": f"sessions_list called {len(list_calls)} times. "
                      f"Expected >=3: must call after each new spawn to get sessionId for potential resumeSessionId."
        })
    except Exception as e:
        checks.append({"name": "sessions_list_called_to_capture_session_ids", "passed": False, "detail": str(e)})

    # ── CHECK 6: Stage 1 uses claude (planning/architecture) ──
    try:
        # Find the first new spawn (stage 1 = planning)
        first_new_spawn = next(
            (s for s in spawn_calls if not s["params"].get("resumeSessionId")), None
        )
        if first_new_spawn is None:
            passed = False
            detail = "No new spawn calls found."
        else:
            agent = first_new_spawn["params"].get("agentId", "")
            passed = agent == "claude"
            detail = f"Stage 1 (planning) agentId='{agent}'. Expected 'claude' for analysis/planning tasks."
        checks.append({"name": "stage1_planning_uses_claude", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "stage1_planning_uses_claude", "passed": False, "detail": str(e)})

    # ── CHECK 7: Stage 2 uses codex (implementation) ──
    try:
        new_spawns = [s for s in spawn_calls if not s["params"].get("resumeSessionId")]
        if len(new_spawns) < 2:
            passed = False
            detail = f"Only {len(new_spawns)} new spawn calls found; need >=2 to check stage 2."
        else:
            agent = new_spawns[1]["params"].get("agentId", "")
            passed = agent == "codex"
            detail = f"Stage 2 (implementation) agentId='{agent}'. Expected 'codex' for coding/implementation."
        checks.append({"name": "stage2_implementation_uses_codex", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "stage2_implementation_uses_codex", "passed": False, "detail": str(e)})

    # ── CHECK 8: Stage 3 uses claude (review/verification) ──
    try:
        new_spawns = [s for s in spawn_calls if not s["params"].get("resumeSessionId")]
        if len(new_spawns) < 3:
            passed = False
            detail = f"Only {len(new_spawns)} new spawn calls; need >=3 for stage 3."
        else:
            agent = new_spawns[2]["params"].get("agentId", "")
            passed = agent == "claude"
            detail = f"Stage 3 (review) agentId='{agent}'. Expected 'claude' for review/verification."
        checks.append({"name": "stage3_review_uses_claude", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "stage3_review_uses_claude", "passed": False, "detail": str(e)})

    # ── CHECK 9: resume spawn uses a valid resumeSessionId (not made up, must be from sessions_list) ──
    try:
        resume_spawns = [s for s in spawn_calls if s["params"].get("resumeSessionId")]
        if not resume_spawns:
            passed = False
            detail = "No resume spawn calls found. Required: use resumeSessionId when content is truncated."
        else:
            # The resumeSessionId must match a sessionId from a previous sessions_list response
            all_listed_session_ids = set()
            for lc in list_calls:
                for sess in lc.get("result", {}).get("sessions", []):
                    sid = sess.get("sessionId")
                    if sid:
                        all_listed_session_ids.add(sid)

            valid_resumes = []
            for rs in resume_spawns:
                rid = rs["params"].get("resumeSessionId", "")
                # Check if this resumeSessionId was found in a sessions_list response
                if rid in all_listed_session_ids:
                    valid_resumes.append(rid)

            passed = len(valid_resumes) >= 1
            detail = (
                f"Found {len(resume_spawns)} resume spawn(s). "
                f"Valid resumeSessionIds (matched from sessions_list): {len(valid_resumes)}. "
                f"Listed session IDs available: {len(all_listed_session_ids)}. "
                f"Must use sessionId from sessions_list output, not sessionKey or invented value."
            )
        checks.append({"name": "resume_spawn_uses_valid_session_id_from_list", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "resume_spawn_uses_valid_session_id_from_list", "passed": False, "detail": str(e)})

    # ── CHECK 10: resume spawn uses claude agentId (fixing truncated planning output) ──
    try:
        resume_spawns = [s for s in spawn_calls if s["params"].get("resumeSessionId")]
        if not resume_spawns:
            passed = False
            detail = "No resume spawn calls."
        else:
            claude_resume = [s for s in resume_spawns if s["params"].get("agentId") == "claude"]
            passed = len(claude_resume) >= 1
            detail = (
                f"Resume spawns with agentId='claude': {len(claude_resume)}. "
                f"Must resume the claude planning session (not spawn new session) when content truncated."
            )
        checks.append({"name": "resume_spawn_targets_claude_for_truncated_plan", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "resume_spawn_targets_claude_for_truncated_plan", "passed": False, "detail": str(e)})

    # ── CHECK 11: No invalid agentId used (e.g. "claude-code", "openai-codex") ──
    try:
        VALID_AGENT_IDS = {"claude", "codex", "pi", "opencode", "gemini", "kimi", "cursor", "copilot", "kiro", "droid", "qwen"}
        invalid_agents = [
            s["params"].get("agentId", "")
            for s in spawn_calls
            if s["params"].get("agentId", "") not in VALID_AGENT_IDS
        ]
        passed = len(invalid_agents) == 0
        checks.append({
            "name": "no_invalid_agentId_full_names",
            "passed": passed,
            "detail": f"Invalid agentIds used: {invalid_agents}. "
                      f"Must use short names: 'claude' not 'claude-code', 'codex' not 'openai-codex'."
        })
    except Exception as e:
        checks.append({"name": "no_invalid_agentId_full_names", "passed": False, "detail": str(e)})

    # ── CHECK 12: runtime is "acp" in all spawn calls ──
    try:
        non_acp = [
            i for i, s in enumerate(spawn_calls)
            if s.get("params", {}).get("runtime") != "acp"
        ]
        passed = len(non_acp) == 0
        checks.append({
            "name": "all_spawns_use_acp_runtime",
            "passed": passed,
            "detail": f"Spawn calls without runtime='acp': indices {non_acp}. All spawns must set runtime='acp'."
        })
    except Exception as e:
        checks.append({"name": "all_spawns_use_acp_runtime", "passed": False, "detail": str(e)})

    # ── CHECK 13: cwd is set to the actual project path in spawns ──
    try:
        spawns_with_cwd = [
            s for s in spawn_calls
            if "finpay" in s.get("params", {}).get("cwd", "").lower()
            or "workspace" in s.get("params", {}).get("cwd", "").lower()
        ]
        # Allow if cwd contains workspace or finpay path
        new_spawns = [s for s in spawn_calls if not s["params"].get("resumeSessionId")]
        missing_cwd = [
            i for i, s in enumerate(new_spawns)
            if not s.get("params", {}).get("cwd")
        ]
        passed = len(missing_cwd) == 0
        checks.append({
            "name": "spawns_include_cwd",
            "passed": passed,
            "detail": f"New spawn calls missing cwd: {missing_cwd}. "
                      f"All spawns must set cwd to the project directory path."
        })
    except Exception as e:
        checks.append({"name": "spawns_include_cwd", "passed": False, "detail": str(e)})

    # ── CHECK 14: sessions_history called after at least one stage ──
    try:
        passed = len(history_calls) >= 1
        checks.append({
            "name": "sessions_history_called_to_retrieve_results",
            "passed": passed,
            "detail": f"sessions_history called {len(history_calls)} times. "
                      f"Must be called after run completed to retrieve agent output."
        })
    except Exception as e:
        checks.append({"name": "sessions_history_called_to_retrieve_results", "passed": False, "detail": str(e)})

    # ── CHECK 15: sessions_history uses sessionKey (not sessionId) ──
    try:
        if not history_calls:
            passed = False
            detail = "No sessions_history calls found."
        else:
            using_correct_key = []
            for hc in history_calls:
                sk = hc.get("params", {}).get("sessionKey", "")
                # sessionKey should look like agent:xxx:acp:xxx
                if sk.startswith("agent:") and ":acp:" in sk:
                    using_correct_key.append(sk)

            passed = len(using_correct_key) >= 1
            detail = (
                f"sessions_history calls with valid sessionKey format: {len(using_correct_key)}/{len(history_calls)}. "
                f"sessions_history must receive 'sessionKey' (agent:xxx:acp:UUID format), "
                f"NOT the sessionId UUID. These are distinct fields."
            )
        checks.append({"name": "sessions_history_uses_sessionKey_not_sessionId", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "sessions_history_uses_sessionKey_not_sessionId", "passed": False, "detail": str(e)})

    # ── Compute final score ──
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = passed_count >= int(total * 0.80)  # 80% threshold

    output = {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()