#!/usr/bin/env python3
"""
Evaluation script for the AgentMesh governance onboarding task.
Checks that the agent produced a correct governance_report.json by:
1. Correctly generating a DID identity for 'quant-analyst-agent'
2. Creating a policy.yaml with the correct firm-specific fields
3. Checking all 5 proposed actions and correctly classifying allowed/blocked
4. Recording 5 collaboration interactions in the correct order
5. Computing the final trust score correctly (deterministic arithmetic)
6. Verifying audit log integrity
7. governance_report.json has all required top-level sections
"""

import sys
import json
import math
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Helper ────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail=""):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
        return bool(passed)

    # ── 1. Find governance_report.json ────────────────────────────────────────
    report_files = list(workspace_path.rglob("governance_report.json"))
    if not report_files:
        add_check("governance_report.json exists", False, "File not found anywhere in workspace")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    report_path = report_files[0]
    add_check("governance_report.json exists", True, str(report_path))

    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        add_check("governance_report.json is valid JSON", False, str(e))
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("governance_report.json is valid JSON", True)

    # ── 2. Check policy.yaml was created ─────────────────────────────────────
    import yaml

    policy_files = list(workspace_path.rglob("policy.yaml"))
    if not policy_files:
        add_check("policy.yaml created", False, "No policy.yaml found in workspace")
    else:
        try:
            with open(policy_files[0]) as f:
                policy = yaml.safe_load(f)

            # Check required fields from the requirements brief
            checks_policy = []

            name_ok = policy.get("name") == "trading-firm-prod"
            checks_policy.append(("policy name is trading-firm-prod", name_ok, f"got: {policy.get('name')}"))

            mt_ok = policy.get("max_tokens") == 4096
            checks_policy.append(("max_tokens == 4096", mt_ok, f"got: {policy.get('max_tokens')}"))

            allowed = policy.get("allowed_tools", [])
            required_allowed = {"market_data_fetch", "file_read", "summarize", "risk_report"}
            allowed_ok = required_allowed.issubset(set(allowed))
            checks_policy.append(("allowed_tools contains required 4 tools", allowed_ok,
                                   f"got: {allowed}"))

            blocked = policy.get("blocked_tools", [])
            required_blocked = {"shell_exec", "file_delete", "database_write"}
            blocked_ok = required_blocked.issubset(set(blocked))
            checks_policy.append(("blocked_tools contains shell_exec, file_delete, database_write",
                                   blocked_ok, f"got: {blocked}"))

            patterns = policy.get("blocked_patterns", [])
            # Must have at least the 5 documented patterns
            required_patterns = {"rm -rf", "DROP TABLE", "BEGIN CERTIFICATE", "exec(", "os.system("}
            # Check each is a substring of some pattern entry
            patterns_ok = all(any(rp in str(p) for p in patterns) for rp in required_patterns)
            checks_policy.append(("blocked_patterns contains all 5 required patterns", patterns_ok,
                                   f"got: {patterns}"))

            ct_ok = abs(policy.get("confidence_threshold", 0) - 0.75) < 0.001
            checks_policy.append(("confidence_threshold == 0.75", ct_ok,
                                   f"got: {policy.get('confidence_threshold')}"))

            mtc_ok = policy.get("max_tool_calls") == 10
            checks_policy.append(("max_tool_calls == 10", mtc_ok,
                                   f"got: {policy.get('max_tool_calls')}"))

            for cname, cpassed, cdetail in checks_policy:
                add_check(f"policy.yaml: {cname}", cpassed, cdetail)

        except Exception as e:
            add_check("policy.yaml parseable", False, str(e))

    # ── 3. Identity section in report ─────────────────────────────────────────
    try:
        identity = report.get("identity", report.get("agent_identity", {}))
        if not identity:
            # Try to find it nested
            for key in report:
                if isinstance(report[key], dict) and "did" in report[key]:
                    identity = report[key]
                    break

        did_val = identity.get("did", "")
        did_ok = did_val.startswith("did:agentmesh:")
        add_check("report: identity.did starts with did:agentmesh:", did_ok, f"got: {did_val}")

        name_val = identity.get("name", "")
        name_ok = "quant-analyst-agent" in str(name_val) or "quant-analyst-agent" in str(report)
        add_check("report: quant-analyst-agent identity present", name_ok,
                  f"name field: {name_val}")

        # Public key present
        pk_val = identity.get("public_key", identity.get("pubkey", ""))
        pk_ok = len(str(pk_val)) > 5
        add_check("report: identity has public_key", pk_ok, f"got: {pk_val}")

        # Capabilities include the 4 required ones
        caps = identity.get("capabilities", identity.get("capability_manifest", {}).get("tools_authorized", []))
        if isinstance(caps, list):
            required_caps = {"market_data_fetch", "summarize", "file_read", "risk_report"}
            caps_ok = required_caps.issubset(set(caps))
        else:
            caps_ok = False
        add_check("report: identity capabilities include all 4 required", caps_ok, f"got: {caps}")

    except Exception as e:
        add_check("report: identity section parseable", False, str(e))

    # ── 4. Policy compliance checks in report ─────────────────────────────────
    try:
        # Expected results for the 5 actions:
        # 1. market_data_fetch / 2000 tokens → allowed (in allowlist, under limit)
        # 2. shell_exec / 100 tokens → BLOCKED (in blocklist)
        # 3. summarize / 3500 tokens → allowed (in allowlist, under limit)
        # 4. file_delete / 50 tokens → BLOCKED (in blocklist)
        # 5. file_read / 800 tokens → allowed (in allowlist, under limit)

        expected_compliance = {
            "market_data_fetch": True,
            "shell_exec": False,
            "summarize": True,
            "file_delete": False,
            "file_read": True,
        }

        # Find policy checks section
        policy_checks = report.get("policy_checks",
                       report.get("compliance_checks",
                       report.get("action_checks", [])))

        if isinstance(policy_checks, list) and len(policy_checks) >= 5:
            found_results = {}
            for item in policy_checks:
                action = item.get("action", "")
                allowed_val = item.get("allowed", item.get("result", item.get("status")))
                if isinstance(allowed_val, str):
                    allowed_val = allowed_val.lower() in ("allowed", "true", "pass", "ok")
                if action:
                    found_results[action] = allowed_val

            for action, expected in expected_compliance.items():
                if action in found_results:
                    ok = found_results[action] == expected
                    add_check(f"report: {action} allowed={expected}", ok,
                              f"got allowed={found_results[action]}")
                else:
                    add_check(f"report: {action} in policy_checks", False,
                              f"action '{action}' not found in report checks")
        else:
            # Try to verify from raw report text
            report_str = json.dumps(report)
            blocked_mentioned = "shell_exec" in report_str and "file_delete" in report_str
            add_check("report: policy_checks section with 5 actions", False,
                      f"policy_checks not found or insufficient entries. "
                      f"blocked tools mentioned: {blocked_mentioned}")

    except Exception as e:
        add_check("report: policy_checks parseable", False, str(e))

    # ── 5. Trust score arithmetic check ───────────────────────────────────────
    # Starting score: 0.70
    # Interaction 1: success → +0.01 → 0.71
    # Interaction 2: success → +0.01 → 0.72
    # Interaction 3: failure severity=0.05 → -0.05 → 0.67
    # Interaction 4: success → +0.01 → 0.68
    # Interaction 5: failure severity=0.08 → -0.08 → 0.60
    EXPECTED_FINAL_SCORE = round(0.70 + 0.01 + 0.01 - 0.05 + 0.01 - 0.08, 6)  # = 0.60

    try:
        trust_section = report.get("trust_score",
                        report.get("trust",
                        report.get("final_trust_score", {})))

        final_score = None
        if isinstance(trust_section, dict):
            final_score = trust_section.get("composite_trust_score",
                          trust_section.get("score",
                          trust_section.get("final_score",
                          trust_section.get("composite"))))
        elif isinstance(trust_section, (int, float)):
            final_score = trust_section

        if final_score is not None:
            score_ok = abs(float(final_score) - EXPECTED_FINAL_SCORE) < 0.005
            add_check(f"report: final trust score ≈ {EXPECTED_FINAL_SCORE}",
                      score_ok, f"got: {final_score}")
        else:
            add_check("report: trust_score section with final score", False,
                      f"trust_section content: {trust_section}")

        # Status: 0.60 > 0.5 → active, delegation allowed
        status_str = json.dumps(trust_section).lower() if trust_section else json.dumps(report).lower()
        active_ok = "active" in status_str or "delegation_allowed" in status_str
        add_check("report: trust status is active (score > 0.5)", active_ok,
                  "active/delegation_allowed not found in trust section")

    except Exception as e:
        add_check("report: trust_score section parseable", False, str(e))

    # ── 6. Audit log integrity verification in report ─────────────────────────
    try:
        audit_section = report.get("audit_log",
                        report.get("audit",
                        report.get("audit_verification", {})))

        report_str = json.dumps(report).lower()
        integrity_mentioned = (
            "integrity" in report_str or
            "merkle" in report_str or
            "verified" in report_str or
            "chain" in report_str
        )
        add_check("report: audit log / merkle verification result present",
                  integrity_mentioned, f"Not found in report keys: {list(report.keys())}")

        # Integrity should be true (no tampering in mock)
        integrity_ok = (
            "integrity_verified\": true" in json.dumps(report) or
            "merkle_chain_valid\": true" in json.dumps(report) or
            "\"verified\": true" in json.dumps(report) or
            (isinstance(audit_section, dict) and
             (audit_section.get("integrity_verified") is True or
              audit_section.get("merkle_chain_valid") is True))
        )
        add_check("report: audit integrity confirmed as valid (no tampering)",
                  integrity_ok, f"audit section: {audit_section}")

    except Exception as e:
        add_check("report: audit_log section parseable", False, str(e))

    # ── 7. Interaction history in report ─────────────────────────────────────
    try:
        report_str = json.dumps(report)
        interactions_present = (
            "data-feed-agent" in report_str or
            "risk-engine-agent" in report_str or
            "record_interaction" in report_str or
            "interactions" in report_str
        )
        add_check("report: collaboration interactions referenced", interactions_present,
                  "No mention of partner agents or interaction history")

        # Verify 5 interactions tracked
        interactions_section = report.get("interactions",
                               report.get("collaboration_history",
                               report.get("interaction_history", [])))
        count_ok = isinstance(interactions_section, list) and len(interactions_section) >= 5
        if not count_ok:
            # Search report string
            count_ok = report_str.count('"outcome"') >= 5 or report_str.count("success") + report_str.count("failure") >= 5
        add_check("report: at least 5 interactions recorded", count_ok,
                  f"interactions section: {interactions_section}")

    except Exception as e:
        add_check("report: interactions section parseable", False, str(e))

    # ── Final scoring ─────────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3) if total_checks > 0 else 0.0

    # Hard pass: must pass file exists + valid JSON + at least 70% of other checks
    critical_passed = checks[0]["passed"] and checks[1]["passed"]
    overall_passed = critical_passed and score >= 0.70

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))