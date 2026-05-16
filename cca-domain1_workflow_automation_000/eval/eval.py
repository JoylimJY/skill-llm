#!/usr/bin/env python3
"""
Evaluation script for CCA Domain 1 task.
Checks that the agent correctly implemented:
1. PostToolUseHook: Unix timestamp -> ISO 8601 normalization
2. PreconditionHook: Programmatic enforcement of get_customer before process_refund
3. RefundCoordinator: Explicit context injection into subagent prompts
4. agent_loop.py: stop_reason-based control flow (not text parsing or iteration cap)
"""

import sys
import json
import subprocess
import traceback
from pathlib import Path
from datetime import datetime, timezone

def run_check(name: str, fn) -> dict:
    try:
        detail = fn()
        return {"name": name, "passed": True, "detail": detail}
    except AssertionError as e:
        return {"name": name, "passed": False, "detail": str(e)}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {type(e).__name__}: {e}\n{traceback.format_exc()}"}


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    workspace = Path(workspace)
    
    # Add workspace to Python path
    sys.path.insert(0, str(workspace))
    
    checks = []
    
    # ── CHECK 1: PostToolUseHook normalizes timestamp fields ─────────────────
    def check_post_tool_hook_created_at():
        from refund_system.hooks.tool_hooks import PostToolUseHook
        hook = PostToolUseHook()
        result = hook("get_customer", {
            "customer": {
                "customer_id": "C-1001",
                "created_at": 1704067200,
                "name": "Alice"
            }
        })
        val = result["customer"]["created_at"]
        assert isinstance(val, str), \
            f"created_at must be str (ISO 8601), got {type(val).__name__}: {val}"
        assert "2024-01-01" in val, \
            f"1704067200 should map to 2024-01-01..., got: {val}"
        assert val.endswith("Z") or "+" in val or "T" in val, \
            f"ISO 8601 format required, got: {val}"
        # Non-timestamp fields unchanged
        assert result["customer"]["name"] == "Alice"
        assert result["customer"]["customer_id"] == "C-1001"
        return f"created_at correctly normalized to: {val}"
    
    checks.append(run_check(
        "PostToolUseHook: created_at Unix->ISO8601 normalization",
        check_post_tool_hook_created_at
    ))
    
    # ── CHECK 2: PostToolUseHook normalizes 'timestamp' field ────────────────
    def check_post_tool_hook_timestamp():
        from refund_system.hooks.tool_hooks import PostToolUseHook
        hook = PostToolUseHook()
        result = hook("get_order", {
            "order": {
                "order_id": "ORD-5001",
                "amount": 299.99,
                "timestamp": 1709251200
            }
        })
        val = result["order"]["timestamp"]
        assert isinstance(val, str), \
            f"timestamp must be str (ISO 8601), got {type(val).__name__}: {val}"
        assert "2024-03-01" in val or "2024-02-29" in val or "2024-03" in val, \
            f"1709251200 should be ~2024-03-01, got: {val}"
        # Non-timestamp numeric fields should remain unchanged
        assert result["order"]["amount"] == 299.99, \
            "amount (non-timestamp) must not be modified"
        return f"timestamp correctly normalized to: {val}"
    
    checks.append(run_check(
        "PostToolUseHook: 'timestamp' field Unix->ISO8601 normalization",
        check_post_tool_hook_timestamp
    ))
    
    # ── CHECK 3: Non-timestamp integers are NOT converted ────────────────────
    def check_post_tool_hook_no_spurious_conversion():
        from refund_system.hooks.tool_hooks import PostToolUseHook
        hook = PostToolUseHook()
        result = hook("get_order", {
            "order": {
                "order_id": "ORD-5001",
                "amount": 299,
                "item_count": 2,
                "status": "delivered"
            }
        })
        assert result["order"]["amount"] == 299, \
            f"'amount' must not be converted (not a timestamp field), got: {result['order']['amount']}"
        assert result["order"]["item_count"] == 2, \
            f"'item_count' must not be converted (not a timestamp field)"
        return "Non-timestamp integers correctly left unchanged"
    
    checks.append(run_check(
        "PostToolUseHook: non-timestamp integers unchanged",
        check_post_tool_hook_no_spurious_conversion
    ))
    
    # ── CHECK 4: PreconditionHook blocks process_refund without get_customer ─
    def check_precondition_blocks_without_verification():
        from refund_system.hooks.tool_hooks import PreconditionHook, BlockedToolError
        hook = PreconditionHook()
        try:
            hook.on_before_tool_call("process_refund", {
                "customer_id": "C-1001",
                "order_id": "ORD-5001",
                "amount": 100.0,
                "reason": "defective"
            })
            raise AssertionError("process_refund should have been blocked but was allowed")
        except BlockedToolError as e:
            assert e.tool_name == "process_refund", \
                f"BlockedToolError.tool_name should be 'process_refund', got '{e.tool_name}'"
            assert e.escalation_required is True, \
                f"BlockedToolError.escalation_required must be True"
            return f"Correctly blocked with escalation_required=True, reason: {e.reason}"
    
    checks.append(run_check(
        "PreconditionHook: blocks process_refund before get_customer",
        check_precondition_blocks_without_verification
    ))
    
    # ── CHECK 5: PreconditionHook allows process_refund after verification ───
    def check_precondition_allows_after_verification():
        from refund_system.hooks.tool_hooks import PreconditionHook, BlockedToolError
        hook = PreconditionHook()
        hook.on_after_tool_call("get_customer", {
            "success": True,
            "customer": {"customer_id": "C-1001", "verified": True}
        })
        result = hook.on_before_tool_call("process_refund", {
            "customer_id": "C-1001",
            "order_id": "ORD-5001",
            "amount": 100.0,
            "reason": "defective"
        })
        assert result is not None, "Should return tool_input when allowed"
        assert result["customer_id"] == "C-1001"
        return "process_refund correctly allowed after get_customer success"
    
    checks.append(run_check(
        "PreconditionHook: allows process_refund after successful get_customer",
        check_precondition_allows_after_verification
    ))
    
    # ── CHECK 6: PreconditionHook tracks verified_customer_id ───────────────
    def check_precondition_tracks_verified_id():
        from refund_system.hooks.tool_hooks import PreconditionHook
        hook = PreconditionHook()
        assert hook.verified_customer_id is None, \
            "verified_customer_id should start as None"
        hook.on_after_tool_call("get_customer", {
            "success": True,
            "customer": {"customer_id": "C-1002", "verified": True}
        })
        assert hook.verified_customer_id == "C-1002", \
            f"verified_customer_id should be 'C-1002', got: {hook.verified_customer_id}"
        return "verified_customer_id correctly set to C-1002"
    
    checks.append(run_check(
        "PreconditionHook: tracks verified_customer_id after get_customer",
        check_precondition_tracks_verified_id
    ))
    
    # ── CHECK 7: Failed get_customer does NOT unlock process_refund ──────────
    def check_precondition_failed_get_customer():
        from refund_system.hooks.tool_hooks import PreconditionHook, BlockedToolError
        hook = PreconditionHook()
        hook.on_after_tool_call("get_customer", {
            "success": False,
            "error": "Customer not found"
        })
        try:
            hook.on_before_tool_call("process_refund", {
                "customer_id": "C-9999",
                "order_id": "ORD-5001",
                "amount": 50.0,
                "reason": "test"
            })
            raise AssertionError("Should have been blocked after failed get_customer")
        except BlockedToolError:
            return "Correctly blocked: failed get_customer does not unlock process_refund"
    
    checks.append(run_check(
        "PreconditionHook: failed get_customer does not unlock process_refund",
        check_precondition_failed_get_customer
    ))
    
    # ── CHECK 8: Coordinator injects context into subagent prompts ───────────
    def check_coordinator_context_injection():
        from refund_system.agents.coordinator import RefundCoordinator
        coord = RefundCoordinator()
        findings = {
            "customer_id": "C-1001",
            "customer_name": "Alice Johnson",
            "verified": True,
            "order_ids": ["ORD-5001", "ORD-5002"],
            "total_claimed": 1049.99
        }
        prompt = coord.spawn_subagent("validate_refund_eligibility", findings)
        assert isinstance(prompt, str), f"spawn_subagent must return a string, got {type(prompt)}"
        assert "C-1001" in prompt, \
            f"Subagent prompt must contain customer_id 'C-1001'. Got: {prompt[:200]}"
        assert "Alice Johnson" in prompt, \
            f"Subagent prompt must contain customer name. Got: {prompt[:200]}"
        assert ("ORD-5001" in prompt or "ORD-5002" in prompt), \
            f"Subagent prompt must contain order IDs. Got: {prompt[:200]}"
        return f"Coordinator correctly injects findings. Prompt preview: {prompt[:100]}..."
    
    checks.append(run_check(
        "Coordinator: explicit context injection into subagent prompt",
        check_coordinator_context_injection
    ))
    
    # ── CHECK 9: Coordinator aggregate_results builds handoff_summary ────────
    def check_coordinator_handoff_summary():
        from refund_system.agents.coordinator import RefundCoordinator
        coord = RefundCoordinator()
        results = [
            {"task": "validate_refund_eligibility", "resolved": True, "amount": 299.99},
            {"task": "investigate_order_history", "resolved": True, "order_count": 2}
        ]
        summary = coord.aggregate_results(results)
        assert summary["case_resolved"] is True
        assert summary["subagent_count"] == 2
        assert summary["handoff_summary"] is not None, \
            "aggregate_results must build handoff_summary (not None)"
        assert summary["handoff_summary"] != {}, \
            "handoff_summary must be non-empty"
        hs = summary["handoff_summary"]
        if isinstance(hs, dict):
            # Should contain meaningful content
            hs_str = json.dumps(hs).lower()
            # Must have some content (not just an empty shell)
            assert len(hs_str) > 10, "handoff_summary dict must have meaningful content"
        return f"handoff_summary built: {str(summary['handoff_summary'])[:100]}"
    
    checks.append(run_check(
        "Coordinator: aggregate_results builds structured handoff_summary",
        check_coordinator_handoff_summary
    ))
    
    # ── CHECK 10: agent_loop.py uses stop_reason, not text parsing ───────────
    def check_agent_loop_stop_reason():
        import inspect
        from refund_system.agents import agent_loop
        source = inspect.getsource(agent_loop)
        
        # Must check stop_reason
        assert "stop_reason" in source, \
            "agent_loop must check stop_reason"
        assert ('"end_turn"' in source or "'end_turn'" in source), \
            "agent_loop must handle 'end_turn' stop reason"
        assert ('"tool_use"' in source or "'tool_use'" in source), \
            "agent_loop must handle 'tool_use' stop reason"
        
        # Must NOT use text content parsing as primary mechanism
        # Check that old broken patterns are removed
        bad_text_checks = [
            ('"complete" in text' in source.lower()),
            ('"done" in text' in source.lower()),
            ('"done" in' in source and 'stop_reason' not in source),
        ]
        # The "for iteration in range(5)" as PRIMARY with no stop_reason check
        has_bad_iteration_primary = (
            "for iteration in range(5)" in source and
            source.count("stop_reason") < 2
        )
        assert not has_bad_iteration_primary, \
            "Loop must not use iteration cap as primary mechanism; use stop_reason"
        
        # Additional: must append tool results
        assert ("tool_result" in source or "tool_use_id" in source), \
            "agent_loop must handle tool results (tool_result / tool_use_id)"
        assert ("messages.append" in source or "messages +=" in source or "extend" in source), \
            "agent_loop must append tool results to conversation history"
        
        return "agent_loop correctly uses stop_reason-based control flow"
    
    checks.append(run_check(
        "agent_loop: stop_reason-based control flow (not text parsing)",
        check_agent_loop_stop_reason
    ))
    
    # ── CHECK 11: Run pytest to catch any remaining issues ───────────────────
    def check_pytest_suite():
        result = subprocess.run(
            [sys.executable, "-m", "pytest", 
             str(workspace / "refund_system/tests/test_system.py"),
             "-v", "--tb=short", "-q",
             "--no-header"],
            capture_output=True, text=True,
            cwd=str(workspace),
            env={**__import__("os").environ, "PYTHONPATH": str(workspace)}
        )
        output = result.stdout + result.stderr
        # Count passed/failed
        lines = output.split("\n")
        passed_count = sum(1 for l in lines if " PASSED" in l)
        failed_count = sum(1 for l in lines if " FAILED" in l or " ERROR" in l)
        
        if result.returncode == 0:
            return f"All pytest tests passed ({passed_count} passed)"
        else:
            # Partial credit - note what failed
            failed_lines = [l for l in lines if "FAILED" in l or "ERROR" in l]
            raise AssertionError(
                f"{failed_count} pytest tests failed, {passed_count} passed.\n"
                f"Failures: {chr(10).join(failed_lines[:5])}\n"
                f"Output tail: {output[-800:]}"
            )
    
    checks.append(run_check(
        "Full pytest suite passes (test_system.py)",
        check_pytest_suite
    ))
    
    # ── Compute score ────────────────────────────────────────────────────────
    total = len(checks)
    passed = sum(1 for c in checks if c["passed"])
    score = round(passed / total, 4)
    
    output = {
        "passed": score >= 0.85,  # Need at least 85% of checks
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(output, indent=2))
    return 0 if output["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())