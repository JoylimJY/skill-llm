#!/usr/bin/env python3
"""
Generate the sandbox workspace for the CCA Domain 1 evaluation task.
Creates a realistic financial case management system skeleton with
deliberately broken/incomplete implementations that the agent must fix.
"""

import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "refund_system",
    "refund_system/agents",
    "refund_system/hooks",
    "refund_system/tools",
    "refund_system/tests",
    "refund_system/config",
    "refund_system/logs",
    "legacy_code",
    "legacy_code/old_loops",
    "legacy_code/deprecated_hooks",
    "docs",
    "docs/specs",
    "scratch",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)


# ── Distractor files (realistic but irrelevant) ──────────────────────────────

(WORKSPACE / "legacy_code/old_loops/loop_v1.py").write_text("""\
# DEPRECATED: Old agent loop - DO NOT USE
# This uses text parsing to detect completion - known to be unreliable

def run_agent_loop_bad(client, messages):
    for i in range(10):  # Bad: uses iteration cap as primary mechanism
        response = client.messages.create(model="claude-3", messages=messages)
        text = response.content[0].text if response.content else ""
        if "DONE" in text or "completed" in text.lower():  # Bad: text parsing
            return text
        messages.append({"role": "assistant", "content": text})
    return "Max iterations reached"
""")

(WORKSPACE / "legacy_code/deprecated_hooks/old_hook.py").write_text("""\
# Deprecated hook implementation - replaced by new SDK pattern
class OldHook:
    def on_tool_result(self, result):
        # Just logs, doesn't transform
        print(f"Tool result: {result}")
        return result
""")

(WORKSPACE / "legacy_code/old_loops/coordinator_v0.py").write_text("""\
# v0 coordinator - broken: subagents implicitly share state
class CoordinatorV0:
    def __init__(self):
        self.shared_history = []  # WRONG: subagents shouldn't share history
    
    def delegate(self, subagent_id, task):
        # WRONG: passes entire shared history to subagent
        return self.shared_history
""")

(WORKSPACE / "docs/specs/refund_policy.md").write_text("""\
# Refund Policy Specification

## Rules
- Maximum automated refund: $500.00
- Refunds above $500 require escalation to human supervisor
- Customer identity MUST be verified before any refund is processed
- All timestamps in audit logs must be ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)
- Refund requests must include: customer_id, order_id, amount, reason

## Workflow
1. Receive refund request
2. Look up customer record (mandatory first step)
3. Validate customer identity
4. Process refund if <= $500
5. Escalate if > $500

## Audit Requirements
- Every tool invocation must be logged
- Timestamps from backend services arrive as Unix epoch integers
- These MUST be converted to ISO 8601 before storing in audit log
""")

(WORKSPACE / "docs/specs/subagent_design.md").write_text("""\
# Subagent Design Notes

## Context Isolation
Subagents operate in isolated contexts.
They do NOT inherit coordinator conversation history.
All relevant findings must be explicitly passed in the subagent prompt.

## Communication Pattern
All inter-agent communication routes through the coordinator.
Subagents never communicate directly with each other.
""")

(WORKSPACE / "refund_system/config/settings.json").write_text(json.dumps({
    "max_auto_refund": 500.0,
    "model": "claude-3-5-haiku-20241022",
    "max_tokens": 1024,
    "escalation_queue": "supervisor_review",
    "audit_log_path": "refund_system/logs/audit.jsonl"
}, indent=2))

(WORKSPACE / "scratch/notes.txt").write_text("""\
TODO: fix the timestamp issue - backend returns unix epoch, UI needs ISO 8601
TODO: make sure customer lookup happens BEFORE refund - currently nothing enforces this
TODO: subagents keep getting empty context - need to explicitly pass coordinator findings
""")

(WORKSPACE / "refund_system/logs/.gitkeep").write_text("")

# ── THE BROKEN IMPLEMENTATIONS the agent must fix/complete ──────────────────

# 1. Broken agent loop (uses text parsing + iteration cap as primary)
(WORKSPACE / "refund_system/agents/agent_loop.py").write_text('''\
"""
Agent loop implementation for refund case management.
STATUS: BROKEN - needs to be rewritten per architecture spec
"""
import anthropic
from refund_system.tools.tool_registry import get_tools, execute_tool


def run_agent(client: anthropic.Anthropic, system_prompt: str, user_message: str) -> str:
    """
    Run the agentic loop for a refund request.
    
    CURRENT ISSUES (must fix):
    - Uses iteration count as primary termination mechanism
    - Checks assistant text content for completion signal
    - Does not properly append tool results to conversation history
    """
    messages = [{"role": "user", "content": user_message}]
    tools = get_tools()
    
    # WRONG: iteration cap as primary mechanism
    for iteration in range(5):
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            system=system_prompt,
            tools=tools,
            messages=messages,
        )
        
        # WRONG: checking text content for termination
        if response.content and hasattr(response.content[0], "text"):
            text = response.content[0].text
            if "complete" in text.lower() or "done" in text.lower():
                return text
        
        # WRONG: not checking stop_reason at all
        # WRONG: not appending assistant response to messages
        # WRONG: not appending tool results to messages
        
        if response.stop_reason == "end_turn":
            return response.content[0].text if response.content else ""
    
    return "Loop ended without proper completion"
''')

# 2. Broken hooks (PostToolUse doesn't normalize timestamps; precondition not enforced)
(WORKSPACE / "refund_system/hooks/tool_hooks.py").write_text('''\
"""
Hook implementations for the refund processing system.
STATUS: INCOMPLETE - timestamp normalization and precondition enforcement missing
"""
import json
from datetime import datetime, timezone
from typing import Any, Dict


class PostToolUseHook:
    """
    Intercepts tool results BEFORE the model processes them.
    Must normalize Unix timestamps to ISO 8601 format.
    
    CURRENT STATUS: Stub - does not normalize timestamps
    """
    
    def __call__(self, tool_name: str, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Find any integer fields named 'timestamp', 'created_at', 'updated_at'
        # and convert them from Unix epoch to ISO 8601 string format
        # Example: 1704067200 -> "2024-01-01T00:00:00Z"
        
        # Currently broken: just returns result unchanged
        return tool_result


class PreconditionHook:
    """
    Programmatic enforcement: process_refund cannot execute until
    get_customer has been called and returned a validated customer_id.
    
    CURRENT STATUS: Stub - does not enforce ordering
    """
    
    def __init__(self):
        self.verified_customer_id = None  # Set by get_customer success
    
    def on_before_tool_call(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns the tool_input if allowed, raises BlockedToolError if not.
        
        TODO: If tool_name == "process_refund" and self.verified_customer_id is None,
        raise BlockedToolError with escalation info.
        """
        # Currently broken: allows process_refund without customer verification
        return tool_input
    
    def on_after_tool_call(self, tool_name: str, tool_result: Dict[str, Any]) -> None:
        """Update state after successful tool calls."""
        # TODO: If tool_name == "get_customer" and result contains valid customer_id,
        # set self.verified_customer_id
        pass


class BlockedToolError(Exception):
    """Raised when a tool call is blocked by a precondition hook."""
    def __init__(self, tool_name: str, reason: str, escalation_required: bool = False):
        self.tool_name = tool_name
        self.reason = reason
        self.escalation_required = escalation_required
        super().__init__(f"Tool '{tool_name}' blocked: {reason}")
''')

# 3. Broken coordinator (doesn't inject context into subagent prompts)
(WORKSPACE / "refund_system/agents/coordinator.py").write_text('''\
"""
Coordinator-Subagent orchestration for complex refund investigations.
STATUS: BROKEN - subagents receive empty context (missing explicit injection)
"""
from typing import Dict, Any, List


class RefundCoordinator:
    """
    Hub-and-spoke coordinator managing refund investigation subagents.
    
    Architecture:
    - Coordinator receives complex multi-issue refund cases
    - Spawns specialized subagents for each issue
    - Aggregates results and synthesizes unified response
    
    CURRENT ISSUES:
    - spawn_subagent() does not inject coordinator findings into subagent prompt
    - Subagents receive empty context instead of relevant case data
    - No explicit context passing mechanism
    """
    
    def __init__(self):
        self.findings: List[Dict[str, Any]] = []
        self.subagent_results: List[Dict[str, Any]] = []
    
    def analyze_case(self, case_data: Dict[str, Any]) -> List[str]:
        """Decompose a complex case into sub-tasks."""
        subtasks = []
        if case_data.get("refund_amount"):
            subtasks.append("validate_refund_eligibility")
        if case_data.get("multiple_orders"):
            subtasks.append("investigate_order_history")
        if case_data.get("customer_complaint"):
            subtasks.append("assess_complaint_severity")
        return subtasks
    
    def spawn_subagent(self, task_type: str, coordinator_findings: Dict[str, Any]) -> str:
        """
        Spawn a subagent for a specific task.
        
        BROKEN: Does not pass coordinator_findings into the subagent prompt.
        Subagents need explicit context injection since they run in isolated contexts.
        """
        # WRONG: Empty prompt - subagent gets no context from coordinator
        subagent_prompt = f"Please investigate: {task_type}"
        # Missing: coordinator_findings should be serialized and injected into prompt
        
        return subagent_prompt  # Returns prompt that would be sent to subagent
    
    def aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate subagent results into unified response."""
        return {
            "case_resolved": all(r.get("resolved", False) for r in results),
            "subagent_count": len(results),
            "findings": results,
            "handoff_summary": None  # TODO: build structured handoff
        }
''')

# 4. Tool registry (complete - these are the tools the agent loop uses)
(WORKSPACE / "refund_system/tools/__init__.py").write_text("")
(WORKSPACE / "refund_system/tools/tool_registry.py").write_text('''\
"""
Tool registry for the refund processing system.
These tools simulate the backend services.
"""
import json
import time
from typing import Any, Dict, List


# Simulated backend data
CUSTOMER_DB = {
    "C-1001": {
        "customer_id": "C-1001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "verified": True,
        "created_at": 1704067200,   # Unix timestamp - must be normalized
        "tier": "premium"
    },
    "C-1002": {
        "customer_id": "C-1002", 
        "name": "Bob Smith",
        "email": "bob@example.com",
        "verified": True,
        "created_at": 1706745600,   # Unix timestamp - must be normalized
        "tier": "standard"
    }
}

ORDER_DB = {
    "ORD-5001": {
        "order_id": "ORD-5001",
        "customer_id": "C-1001",
        "amount": 299.99,
        "status": "delivered",
        "timestamp": 1709251200,    # Unix timestamp - must be normalized
        "items": ["item_A", "item_B"]
    },
    "ORD-5002": {
        "order_id": "ORD-5002",
        "customer_id": "C-1001", 
        "amount": 750.00,
        "status": "delivered",
        "timestamp": 1711929600,    # Unix timestamp - must be normalized
        "items": ["item_C"]
    },
    "ORD-5003": {
        "order_id": "ORD-5003",
        "customer_id": "C-1002",
        "amount": 125.50,
        "status": "delivered",
        "timestamp": 1714521600,    # Unix timestamp - must be normalized
        "items": ["item_D", "item_E"]
    }
}


def get_tools() -> List[Dict[str, Any]]:
    """Return tool definitions in Anthropic API format."""
    return [
        {
            "name": "get_customer",
            "description": "Retrieve customer record by customer ID. Must be called before any refund processing. Returns customer details including verification status.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string", "description": "The customer ID (e.g., C-1001)"}
                },
                "required": ["customer_id"]
            }
        },
        {
            "name": "get_order",
            "description": "Retrieve order details by order ID. Returns order amount, status, and timestamps.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "The order ID (e.g., ORD-5001)"}
                },
                "required": ["order_id"]
            }
        },
        {
            "name": "process_refund",
            "description": "Process a refund for a verified customer. Requires prior customer verification via get_customer. Amounts above $500 will be escalated.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "order_id": {"type": "string"},
                    "amount": {"type": "number"},
                    "reason": {"type": "string"}
                },
                "required": ["customer_id", "order_id", "amount", "reason"]
            }
        },
        {
            "name": "escalate_case",
            "description": "Escalate a case to human supervisor when automated processing is not possible (e.g., amount exceeds limit, policy violation).",
            "input_schema": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "case_details": {"type": "object"}
                },
                "required": ["customer_id", "reason"]
            }
        }
    ]


def execute_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool and return its result."""
    if tool_name == "get_customer":
        cid = tool_input.get("customer_id")
        if cid in CUSTOMER_DB:
            return {"success": True, "customer": CUSTOMER_DB[cid]}
        return {"success": False, "error": f"Customer {cid} not found"}
    
    elif tool_name == "get_order":
        oid = tool_input.get("order_id")
        if oid in ORDER_DB:
            return {"success": True, "order": ORDER_DB[oid]}
        return {"success": False, "error": f"Order {oid} not found"}
    
    elif tool_name == "process_refund":
        amount = tool_input.get("amount", 0)
        if amount > 500:
            return {
                "success": False,
                "escalation_required": True,
                "reason": f"Amount ${amount} exceeds $500 automated limit",
                "timestamp": int(time.time())
            }
        return {
            "success": True,
            "refund_id": f"REF-{int(time.time())}",
            "amount": amount,
            "status": "processed",
            "timestamp": int(time.time())
        }
    
    elif tool_name == "escalate_case":
        return {
            "success": True,
            "escalation_id": f"ESC-{int(time.time())}",
            "queue": "supervisor_review",
            "timestamp": int(time.time())
        }
    
    return {"error": f"Unknown tool: {tool_name}"}
''')

(WORKSPACE / "refund_system/tools/tool_registry.py").parent.joinpath("__init__.py").write_text("")
(WORKSPACE / "refund_system/__init__.py").write_text("")
(WORKSPACE / "refund_system/agents/__init__.py").write_text("")
(WORKSPACE / "refund_system/hooks/__init__.py").write_text("")

# 5. Test file that the agent should make pass
(WORKSPACE / "refund_system/tests/test_system.py").write_text('''\
"""
Integration tests for the refund case management system.
Run with: pytest refund_system/tests/test_system.py -v

These tests define the REQUIRED behavior of the fixed implementation.
"""
import pytest
import json
import sys
import os

sys.path.insert(0, "/workspace")

from refund_system.hooks.tool_hooks import PostToolUseHook, PreconditionHook, BlockedToolError
from refund_system.agents.coordinator import RefundCoordinator


class TestPostToolUseHook:
    """Tests for Unix timestamp -> ISO 8601 normalization."""
    
    def test_normalizes_timestamp_field(self):
        hook = PostToolUseHook()
        result = hook("get_customer", {
            "customer": {
                "customer_id": "C-1001",
                "created_at": 1704067200,
                "name": "Alice"
            }
        })
        # Must convert Unix int to ISO 8601 string
        assert isinstance(result["customer"]["created_at"], str), \
            "created_at must be converted to ISO 8601 string"
        assert "2024-01-01" in result["customer"]["created_at"], \
            "Timestamp 1704067200 should be 2024-01-01T00:00:00Z"
        assert result["customer"]["customer_id"] == "C-1001"
        assert result["customer"]["name"] == "Alice"
    
    def test_normalizes_timestamp_in_nested_order(self):
        hook = PostToolUseHook()
        result = hook("get_order", {
            "order": {
                "order_id": "ORD-5001",
                "amount": 299.99,
                "timestamp": 1709251200
            }
        })
        assert isinstance(result["order"]["timestamp"], str), \
            "timestamp must be converted to ISO 8601 string"
        assert "2024-03-01" in result["order"]["timestamp"]
    
    def test_non_timestamp_integers_unchanged(self):
        hook = PostToolUseHook()
        result = hook("get_order", {
            "order": {
                "order_id": "ORD-5001",
                "amount": 299,
                "item_count": 2
            }
        })
        # amount and item_count should not be touched (not timestamp fields)
        assert result["order"]["amount"] == 299
        assert result["order"]["item_count"] == 2
    
    def test_already_string_timestamp_unchanged(self):
        hook = PostToolUseHook()
        result = hook("get_customer", {
            "customer": {"created_at": "2024-01-01T00:00:00Z"}
        })
        assert result["customer"]["created_at"] == "2024-01-01T00:00:00Z"


class TestPreconditionHook:
    """Tests for programmatic tool ordering enforcement."""
    
    def test_blocks_process_refund_without_customer_verification(self):
        hook = PreconditionHook()
        with pytest.raises(BlockedToolError) as exc_info:
            hook.on_before_tool_call("process_refund", {
                "customer_id": "C-1001",
                "order_id": "ORD-5001",
                "amount": 100.0,
                "reason": "defective"
            })
        assert exc_info.value.tool_name == "process_refund"
        assert exc_info.value.escalation_required is True
    
    def test_allows_get_customer_without_prior_verification(self):
        hook = PreconditionHook()
        result = hook.on_before_tool_call("get_customer", {"customer_id": "C-1001"})
        assert result["customer_id"] == "C-1001"
    
    def test_allows_process_refund_after_customer_verified(self):
        hook = PreconditionHook()
        # Simulate get_customer succeeding
        hook.on_after_tool_call("get_customer", {
            "success": True,
            "customer": {"customer_id": "C-1001", "verified": True}
        })
        # Now process_refund should be allowed
        result = hook.on_before_tool_call("process_refund", {
            "customer_id": "C-1001",
            "order_id": "ORD-5001",
            "amount": 100.0,
            "reason": "defective"
        })
        assert result["customer_id"] == "C-1001"
    
    def test_verified_customer_id_set_after_get_customer(self):
        hook = PreconditionHook()
        assert hook.verified_customer_id is None
        hook.on_after_tool_call("get_customer", {
            "success": True,
            "customer": {"customer_id": "C-1002", "verified": True}
        })
        assert hook.verified_customer_id == "C-1002"
    
    def test_failed_get_customer_does_not_unlock_process_refund(self):
        hook = PreconditionHook()
        hook.on_after_tool_call("get_customer", {
            "success": False,
            "error": "Customer not found"
        })
        with pytest.raises(BlockedToolError):
            hook.on_before_tool_call("process_refund", {
                "customer_id": "C-9999",
                "order_id": "ORD-5001",
                "amount": 50.0,
                "reason": "test"
            })


class TestCoordinator:
    """Tests for coordinator-subagent context injection."""
    
    def test_spawn_subagent_includes_coordinator_findings_in_prompt(self):
        coord = RefundCoordinator()
        findings = {
            "customer_id": "C-1001",
            "customer_name": "Alice Johnson",
            "verified": True,
            "order_ids": ["ORD-5001", "ORD-5002"],
            "total_claimed": 1049.99
        }
        prompt = coord.spawn_subagent("validate_refund_eligibility", findings)
        
        # Subagent prompt MUST explicitly contain coordinator findings
        assert "C-1001" in prompt, \
            "Subagent prompt must contain customer_id from coordinator findings"
        assert "Alice Johnson" in prompt, \
            "Subagent prompt must contain customer name"
        assert "ORD-5001" in prompt or "ORD-5002" in prompt, \
            "Subagent prompt must contain order IDs"
    
    def test_spawn_subagent_includes_task_type(self):
        coord = RefundCoordinator()
        prompt = coord.spawn_subagent("investigate_order_history", {"customer_id": "C-1002"})
        assert "investigate_order_history" in prompt or "order history" in prompt.lower()
    
    def test_aggregate_results_builds_handoff_summary(self):
        coord = RefundCoordinator()
        results = [
            {"task": "validate_refund_eligibility", "resolved": True, "amount": 299.99},
            {"task": "investigate_order_history", "resolved": True, "order_count": 2}
        ]
        summary = coord.aggregate_results(results)
        assert summary["case_resolved"] is True
        assert summary["subagent_count"] == 2
        # handoff_summary must be populated (not None)
        assert summary["handoff_summary"] is not None, \
            "aggregate_results must build a structured handoff_summary"
    
    def test_unresolved_results_mark_case_not_resolved(self):
        coord = RefundCoordinator()
        results = [
            {"task": "validate_refund_eligibility", "resolved": False},
        ]
        summary = coord.aggregate_results(results)
        assert summary["case_resolved"] is False


class TestAgentLoop:
    """Tests for correct stop_reason-based control flow."""
    
    def test_agent_loop_module_exists_and_importable(self):
        from refund_system.agents.agent_loop import run_agent
        assert callable(run_agent)
    
    def test_agent_loop_uses_stop_reason_not_text_parsing(self):
        """Verify the loop implementation checks stop_reason, not text content."""
        import inspect
        from refund_system.agents import agent_loop
        source = inspect.getsource(agent_loop)
        
        # Must check stop_reason
        assert "stop_reason" in source, "Loop must check stop_reason"
        assert '"end_turn"' in source or "'end_turn'" in source, \
            "Loop must handle end_turn stop reason"
        assert '"tool_use"' in source or "'tool_use'" in source, \
            "Loop must handle tool_use stop reason"
        
        # Must NOT use text parsing as termination mechanism
        bad_patterns = [
            '"complete" in', "complete' in", 
            '"done" in', "done' in",
            '"DONE" in', "DONE' in",
            ".lower()", 
        ]
        # Check if the old bad patterns are still present as primary mechanism
        # (the source should not rely on text content for loop control)
        assert "for iteration in range" not in source or \
               source.count("stop_reason") >= 2, \
            "Loop must use stop_reason as primary control, not iteration cap"
    
    def test_agent_loop_appends_tool_results_to_messages(self):
        """Verify tool results are appended to conversation history."""
        import inspect
        from refund_system.agents import agent_loop
        source = inspect.getsource(agent_loop)
        
        # Must append tool results
        assert "tool_result" in source or "tool_use_id" in source, \
            "Loop must append tool results to message history"
        assert "messages.append" in source or "messages +=" in source or \
               "extend" in source, \
            "Loop must maintain conversation history with tool results"
''')

# 6. Main entry point stub
(WORKSPACE / "refund_system/main.py").write_text('''\
"""
Main entry point for the refund case management system.
Demonstrates the full workflow.
"""
import sys
import os
sys.path.insert(0, "/workspace")

# Example usage (will work once implementations are fixed)
from refund_system.hooks.tool_hooks import PostToolUseHook, PreconditionHook
from refund_system.agents.coordinator import RefundCoordinator


def demo_workflow():
    """
    Demonstrate the complete refund workflow:
    1. PostToolUseHook normalizes timestamps
    2. PreconditionHook enforces get_customer -> process_refund ordering
    3. Coordinator spawns subagents with explicit context injection
    """
    print("Refund Case Management System - Demo")
    print("=" * 50)
    
    # Test hook
    hook = PostToolUseHook()
    raw_result = {"customer": {"customer_id": "C-1001", "created_at": 1704067200}}
    normalized = hook("get_customer", raw_result)
    print(f"Normalized timestamp: {normalized['customer']['created_at']}")
    
    # Test precondition
    pre_hook = PreconditionHook()
    try:
        pre_hook.on_before_tool_call("process_refund", {"customer_id": "C-1001", "amount": 100})
        print("ERROR: Should have been blocked!")
    except Exception as e:
        print(f"Correctly blocked: {e}")


if __name__ == "__main__":
    demo_workflow()
''')

# 7. Additional distractor files
(WORKSPACE / "scratch/refund_calculations.py").write_text("""\
# Scratch calculations - ignore
# tax_rate = 0.08
# base_amount = 250
# total = base_amount * (1 + tax_rate)  # 270.0
""")

(WORKSPACE / "refund_system/config/escalation_rules.json").write_text(json.dumps({
    "rules": [
        {"condition": "amount > 500", "action": "escalate", "queue": "supervisor_review"},
        {"condition": "customer.tier == 'premium'", "action": "priority_review"},
        {"condition": "order.age_days > 90", "action": "manual_review"}
    ]
}, indent=2))

(WORKSPACE / "docs/specs/api_reference.md").write_text("""\
# Backend API Reference (Internal)

## Timestamp Formats
All timestamps from the backend database are returned as Unix epoch integers.
Example: 1704067200 = January 1, 2024 00:00:00 UTC

## Field Names
Timestamp fields include: timestamp, created_at, updated_at

## ISO 8601 Format Required
All client-facing and audit systems require ISO 8601:
Format: YYYY-MM-DDTHH:MM:SSZ
Example: 2024-01-01T00:00:00Z
""")

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")