#!/usr/bin/env python3
"""
Evaluation script for the opencode skill task.
Verifies:
  1. opencode was invoked at least once with --agent plan
  2. opencode was invoked at least once with --agent build
  3. --continue flag was used on ALL invocations
  4. plan was invoked BEFORE build (correct ordering)
  5. All invocations used `cd [repo] && opencode run ...` pattern (cwd is repo dir)
  6. The /health endpoint actually exists and is correct in routes.py
  7. A test for the /health endpoint exists and is non-trivial
"""

import sys
import json
import os
from pathlib import Path

def main(workspace: str):
    checks = []
    score_parts = []

    log_path = Path(workspace) / ".opencode_logs" / "invocations.jsonl"
    repo_path = Path(workspace) / "inventory-service"
    routes_path = repo_path / "app" / "routes.py"

    # ── Load invocation log ────────────────────────────────────────────────────
    invocations = []
    try:
        with open(log_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    invocations.append(json.loads(line))
        log_loaded = True
    except FileNotFoundError:
        log_loaded = False
    except Exception as e:
        log_loaded = False

    # CHECK 1: opencode was called at all
    check_called = {
        "name": "opencode_was_invoked",
        "passed": log_loaded and len(invocations) > 0,
        "detail": (
            f"Found {len(invocations)} invocation(s) in log."
            if log_loaded
            else "Invocation log not found — opencode was never called."
        )
    }
    checks.append(check_called)
    score_parts.append(1.0 if check_called["passed"] else 0.0)

    # CHECK 2: plan agent was used
    plan_invocations = [inv for inv in invocations if inv.get("agent") == "plan"]
    check_plan_used = {
        "name": "plan_agent_used",
        "passed": len(plan_invocations) > 0,
        "detail": (
            f"plan agent invoked {len(plan_invocations)} time(s)."
            if len(plan_invocations) > 0
            else "No invocation used --agent plan. Plan was skipped — violates mandatory plan-first rule."
        )
    }
    checks.append(check_plan_used)
    score_parts.append(1.0 if check_plan_used["passed"] else 0.0)

    # CHECK 3: build agent was used
    build_invocations = [inv for inv in invocations if inv.get("agent") == "build"]
    check_build_used = {
        "name": "build_agent_used",
        "passed": len(build_invocations) > 0,
        "detail": (
            f"build agent invoked {len(build_invocations)} time(s)."
            if len(build_invocations) > 0
            else "No invocation used --agent build."
        )
    }
    checks.append(check_build_used)
    score_parts.append(1.0 if check_build_used["passed"] else 0.0)

    # CHECK 4: plan was invoked BEFORE build (ordering)
    first_plan_idx = next(
        (i for i, inv in enumerate(invocations) if inv.get("agent") == "plan"), None
    )
    first_build_idx = next(
        (i for i, inv in enumerate(invocations) if inv.get("agent") == "build"), None
    )
    if first_plan_idx is not None and first_build_idx is not None:
        ordering_ok = first_plan_idx < first_build_idx
        ordering_detail = (
            f"plan (index {first_plan_idx}) came before build (index {first_build_idx}). Correct."
            if ordering_ok
            else f"build (index {first_build_idx}) was invoked BEFORE plan (index {first_plan_idx}). Plan-first rule violated."
        )
    elif first_plan_idx is None:
        ordering_ok = False
        ordering_detail = "plan was never invoked, cannot verify ordering."
    elif first_build_idx is None:
        ordering_ok = False
        ordering_detail = "build was never invoked, cannot verify ordering."
    else:
        ordering_ok = False
        ordering_detail = "Neither plan nor build was invoked."

    check_ordering = {
        "name": "plan_before_build_ordering",
        "passed": ordering_ok,
        "detail": ordering_detail
    }
    checks.append(check_ordering)
    score_parts.append(1.0 if check_ordering["passed"] else 0.0)

    # CHECK 5: --continue flag used on ALL invocations
    invocations_missing_continue = [
        inv for inv in invocations if not inv.get("continue_flag", False)
    ]
    check_continue = {
        "name": "continue_flag_used_on_all_invocations",
        "passed": len(invocations) > 0 and len(invocations_missing_continue) == 0,
        "detail": (
            f"All {len(invocations)} invocation(s) used --continue. Correct."
            if len(invocations) > 0 and len(invocations_missing_continue) == 0
            else (
                f"{len(invocations_missing_continue)} invocation(s) were missing --continue flag: "
                + str([inv.get("agent") for inv in invocations_missing_continue])
                if invocations
                else "No invocations found."
            )
        )
    }
    checks.append(check_continue)
    score_parts.append(1.0 if check_continue["passed"] else 0.0)

    # CHECK 6: cwd of invocations points to the repo directory
    repo_str = str(repo_path.resolve())
    invocations_wrong_cwd = [
        inv for inv in invocations
        if not inv.get("cwd", "").startswith(repo_str) and inv.get("cwd", "") != repo_str
    ]
    check_cwd = {
        "name": "invocations_run_from_repo_directory",
        "passed": len(invocations) > 0 and len(invocations_wrong_cwd) == 0,
        "detail": (
            f"All invocations ran from the correct repo directory ({repo_str})."
            if len(invocations) > 0 and len(invocations_wrong_cwd) == 0
            else (
                f"{len(invocations_wrong_cwd)} invocation(s) did NOT run from {repo_str}. "
                + "Got cwds: " + str([inv.get("cwd") for inv in invocations_wrong_cwd])
                if invocations
                else "No invocations found."
            )
        )
    }
    checks.append(check_cwd)
    score_parts.append(1.0 if check_cwd["passed"] else 0.0)

    # CHECK 7: /health route exists in routes.py
    try:
        routes_content = routes_path.read_text()
        has_health_route = (
            '"/health"' in routes_content or "'/health'" in routes_content
        )
        has_status_ok = '"ok"' in routes_content or "'ok'" in routes_content
        route_ok = has_health_route and has_status_ok
        check_route = {
            "name": "health_route_added_to_routes_py",
            "passed": route_ok,
            "detail": (
                "GET /health route with {\"status\": \"ok\"} response found in app/routes.py."
                if route_ok
                else (
                    f"app/routes.py is missing /health route or status:ok response. "
                    f"has_route={has_health_route}, has_ok={has_status_ok}"
                )
            )
        }
    except FileNotFoundError:
        check_route = {
            "name": "health_route_added_to_routes_py",
            "passed": False,
            "detail": "app/routes.py not found."
        }
    checks.append(check_route)
    score_parts.append(1.0 if check_route["passed"] else 0.0)

    # CHECK 8: A test for the /health endpoint exists
    try:
        test_files = list(repo_path.rglob("test_health.py")) + list(repo_path.rglob("test_health_*.py"))
        # Also search all test files for a test function exercising /health
        all_test_content = ""
        for tf in (repo_path / "tests").glob("test_*.py"):
            try:
                all_test_content += tf.read_text()
            except Exception:
                pass

        has_health_test_fn = "def test_health" in all_test_content
        has_health_get = '"/health"' in all_test_content or "'/health'" in all_test_content
        test_ok = has_health_test_fn and has_health_get

        check_test = {
            "name": "health_endpoint_test_exists",
            "passed": test_ok,
            "detail": (
                "test_health function exercising GET /health found in tests/."
                if test_ok
                else (
                    f"No test for /health found. "
                    f"has_test_fn={has_health_test_fn}, has_get_call={has_health_get}"
                )
            )
        }
    except Exception as e:
        check_test = {
            "name": "health_endpoint_test_exists",
            "passed": False,
            "detail": f"Error scanning test files: {e}"
        }
    checks.append(check_test)
    score_parts.append(1.0 if check_test["passed"] else 0.0)

    # ── Aggregate ──────────────────────────────────────────────────────────────
    total_score = sum(score_parts) / len(score_parts) if score_parts else 0.0
    passed = all(c["passed"] for c in checks)

    result = {
        "passed": passed,
        "score": round(total_score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)