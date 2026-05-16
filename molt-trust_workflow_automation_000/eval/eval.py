#!/usr/bin/env python3
"""
Evaluation script for the molt-trust procurement vetting task.
Reads the invocation log written by mock CLI tools and validates
that the agent executed the correct multi-step workflow.
"""

import sys
import json
import os

def load_invocations(workspace):
    log_path = os.path.join(workspace, ".molt_invocations", "invocations.jsonl")
    if not os.path.exists(log_path):
        return None, f"Invocation log not found at {log_path}"
    invocations = []
    try:
        with open(log_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    invocations.append(json.loads(line))
        return invocations, None
    except Exception as e:
        return None, f"Failed to parse invocation log: {e}"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

    checks = []
    total_score = 0.0

    # Load invocations
    invocations, err = load_invocations(workspace)
    if invocations is None:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "invocation_log_exists", "passed": False, "detail": err}]
        }))
        return

    # Helper: get all calls for a given tool
    def get_calls(tool_name):
        return [inv for inv in invocations if inv.get("tool") == tool_name]

    # -------------------------------------------------------
    # CHECK 1: manage_peers called with action="trust" and
    #           walletAddress="0xA1B2C3D4E5F6a1b2c3d4e5f6a1b2c3d4e5f6A1B2"
    # -------------------------------------------------------
    TARGET_WALLET = "0xA1B2C3D4E5F6a1b2c3d4e5f6a1b2c3d4e5f6A1B2"
    manage_calls = get_calls("manage_peers")
    peer_trust_ok = False
    peer_trust_detail = "manage_peers with action='trust' and correct wallet not found."
    for call in manage_calls:
        p = call.get("params", {})
        if p.get("action") == "trust" and p.get("walletAddress", "").lower() == TARGET_WALLET.lower():
            peer_trust_ok = True
            peer_trust_detail = f"manage_peers(action='trust', walletAddress='{p['walletAddress']}') correctly called."
            break

    checks.append({
        "name": "manage_peers_trust_wallet",
        "passed": peer_trust_ok,
        "detail": peer_trust_detail
    })
    if peer_trust_ok:
        total_score += 25.0

    # -------------------------------------------------------
    # CHECK 2: audit_agent called for agentId="7"
    # -------------------------------------------------------
    audit_calls = get_calls("audit_agent")
    audit_agent7 = [c for c in audit_calls if c.get("params", {}).get("agentId") == "7"]
    audit_found = len(audit_agent7) > 0

    checks.append({
        "name": "audit_agent_called_for_agent7",
        "passed": audit_found,
        "detail": f"audit_agent for agentId='7' {'found' if audit_found else 'NOT found'}."
    })
    if audit_found:
        total_score += 10.0

    # -------------------------------------------------------
    # CHECK 3: audit_agent must use strictMode="true"
    # -------------------------------------------------------
    strict_ok = False
    strict_detail = "audit_agent was not called with strictMode='true'."
    for call in audit_agent7:
        p = call.get("params", {})
        if p.get("strictMode") == "true":
            strict_ok = True
            strict_detail = "audit_agent correctly called with strictMode='true' (Fortress Mode)."
            break

    checks.append({
        "name": "audit_agent_strict_mode",
        "passed": strict_ok,
        "detail": strict_detail
    })
    if strict_ok:
        total_score += 25.0

    # -------------------------------------------------------
    # CHECK 4: audit_agent must use minScore >= 15
    #           (draft contract specifies "ignore scores below 15")
    # -------------------------------------------------------
    minscore_ok = False
    minscore_detail = "audit_agent not called with minScore >= 15."
    for call in audit_agent7:
        p = call.get("params", {})
        ms = p.get("minScore")
        if ms is not None:
            try:
                if int(ms) >= 15:
                    minscore_ok = True
                    minscore_detail = f"audit_agent called with minScore='{ms}' (>= 15). Correct spam filter."
                    break
                else:
                    minscore_detail = f"audit_agent called with minScore='{ms}', but required >= 15."
            except ValueError:
                minscore_detail = f"minScore='{ms}' is not a valid integer."

    checks.append({
        "name": "audit_agent_min_score",
        "passed": minscore_ok,
        "detail": minscore_detail
    })
    if minscore_ok:
        total_score += 15.0

    # -------------------------------------------------------
    # CHECK 5: manage_peers called BEFORE audit_agent (ordering)
    # -------------------------------------------------------
    order_ok = False
    order_detail = "manage_peers(trust) was not called before audit_agent, or one of them is missing."
    if peer_trust_ok and audit_found:
        # Find timestamps of the relevant calls
        manage_ts = None
        for call in manage_calls:
            p = call.get("params", {})
            if p.get("action") == "trust" and p.get("walletAddress", "").lower() == TARGET_WALLET.lower():
                manage_ts = call.get("timestamp")
                break
        audit_ts = None
        for call in audit_agent7:
            if call.get("params", {}).get("strictMode") == "true":
                audit_ts = call.get("timestamp")
                break
        if manage_ts and audit_ts:
            if manage_ts <= audit_ts:
                order_ok = True
                order_detail = f"manage_peers(trust) at {manage_ts} correctly precedes audit_agent at {audit_ts}."
            else:
                order_detail = f"manage_peers(trust) at {manage_ts} came AFTER audit_agent at {audit_ts}. Peer must be added first."

    checks.append({
        "name": "manage_peers_before_audit",
        "passed": order_ok,
        "detail": order_detail
    })
    if order_ok:
        total_score += 10.0

    # -------------------------------------------------------
    # CHECK 6: rate_agent called for agentId="7" with a score
    # -------------------------------------------------------
    rate_calls = get_calls("rate_agent")
    rate_agent7 = [c for c in rate_calls if c.get("params", {}).get("agentId") == "7"]
    rate_found = len(rate_agent7) > 0

    checks.append({
        "name": "rate_agent_called_for_agent7",
        "passed": rate_found,
        "detail": f"rate_agent for agentId='7' {'found' if rate_found else 'NOT found'}."
    })
    if rate_found:
        total_score += 5.0

    # -------------------------------------------------------
    # CHECK 7: rate_agent must include proofTx
    #           (the specific hash from the contract draft)
    # -------------------------------------------------------
    EXPECTED_PROOF_TX = "0xdeadbeef1234567890abcdef1234567890abcdef1234567890abcdef12345678"
    proof_ok = False
    proof_detail = "rate_agent not called with the required proofTx hash."
    for call in rate_agent7:
        p = call.get("params", {})
        proof_tx = p.get("proofTx", "")
        if proof_tx.lower() == EXPECTED_PROOF_TX.lower():
            proof_ok = True
            proof_detail = f"rate_agent correctly called with proofTx='{proof_tx}'."
            break
        elif proof_tx:
            proof_detail = f"rate_agent called with proofTx='{proof_tx}', but expected '{EXPECTED_PROOF_TX}'."

    checks.append({
        "name": "rate_agent_with_proof_tx",
        "passed": proof_ok,
        "detail": proof_detail
    })
    if proof_ok:
        total_score += 10.0

    # -------------------------------------------------------
    # FINAL RESULT
    # -------------------------------------------------------
    # All critical checks: manage_peers(trust), strict mode, minScore, proofTx, ordering
    critical_checks = [
        "manage_peers_trust_wallet",
        "audit_agent_strict_mode",
        "audit_agent_min_score",
        "manage_peers_before_audit",
        "rate_agent_with_proof_tx",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    passed = critical_passed and total_score >= 85.0

    print(json.dumps({
        "passed": passed,
        "score": round(total_score, 2),
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()