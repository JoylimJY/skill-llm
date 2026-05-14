import os
import json
import random

random.seed(42)

base = "/workspace"

# --- Directory structure ---
dirs = [
    "validators/validator-a",
    "validators/validator-b",
    "validators/validator-c",
    "attestation/edge_cases",
    "attestation/results",
    "traces/validator-a",
    "traces/validator-b",
    "traces/validator-c",
    "skills/payment-router",
    "audit/archive",
    "audit/current",
    "config/policies",
    "config/thresholds",
    "reports/old",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# --- Distractor files ---
distractor_contents = {
    "validators/validator-a/changelog.md": "# Validator-A Changelog\n## v2.1\n- Updated detection rules\n## v2.0\n- Initial release",
    "validators/validator-b/changelog.md": "# Validator-B Changelog\n## v1.8\n- Minor bug fixes\n## v1.7\n- Added SQL injection checks",
    "validators/validator-c/changelog.md": "# Validator-C Changelog\n## v3.0\n- Complete rewrite\n## v2.9\n- Legacy support",
    "audit/archive/old_report_2024.txt": "Legacy audit report from 2024. Not applicable to current pipeline.",
    "audit/archive/old_report_2023.txt": "Legacy audit report from 2023. Archived.",
    "audit/current/org_diversity.json": json.dumps({
        "assessment": "organizational_diversity",
        "validators": ["Validator-A", "Validator-B", "Validator-C"],
        "orgs": ["PayAudit Inc", "SecureCheck Ltd", "TrustLab Systems"],
        "verdict": "DIVERSE",
        "note": "All three validators belong to different organizations."
    }, indent=2),
    "config/policies/attestation_policy.json": json.dumps({
        "required_validators": 3,
        "min_pass_threshold": 0.8,
        "policy_version": "2.1",
        "last_updated": "2025-01-15"
    }, indent=2),
    "config/thresholds/alert_thresholds.json": json.dumps({
        "high_risk_score": 0.7,
        "medium_risk_score": 0.4,
        "low_risk_score": 0.2
    }, indent=2),
    "reports/old/correlation_report_draft_2024.txt": "DRAFT - DO NOT USE\nOld correlation report, methodology superseded.",
    "skills/payment-router/manifest.yaml": """name: payment-router
version: 3.1
description: Routes payment transactions to appropriate processors
capabilities:
  - outbound_http
  - database_read
  - crypto_operations
attestation_required: true
validators_required: 3
""",
    "skills/payment-router/SECURITY_NOTES.txt": "Known edge cases: large-value transactions, FX conversion, retry logic under network failure.",
}

for path, content in distractor_contents.items():
    full_path = os.path.join(base, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- Validator provenance / metadata ---
validator_a_meta = {
    "validator_id": "Validator-A",
    "organization": "PayAudit Inc",
    "version": "2.1.0",
    "provenance": {
        "base_model": "GPT-class (gpt-security-base-v3)",
        "fine_tuning_dataset": "FinSecCorpus-v4",
        "training_pipeline": "standard-rlhf-v2",
        "disclosure_status": "DISCLOSED"
    },
    "capabilities": ["transaction_risk", "api_security", "data_exfiltration"],
    "contact": "audits@payaudit.example.com"
}

validator_b_meta = {
    "validator_id": "Validator-B",
    "organization": "SecureCheck Ltd",
    "version": "1.8.2",
    "provenance": {
        "base_model": "GPT-class (gpt-security-base-v3)",
        "fine_tuning_dataset": "FinSecCorpus-v4",
        "training_pipeline": "standard-rlhf-v2",
        "disclosure_status": "DISCLOSED"
    },
    "capabilities": ["transaction_risk", "api_security", "compliance_check"],
    "contact": "security@securecheck.example.com"
}

validator_c_meta = {
    "validator_id": "Validator-C",
    "organization": "TrustLab Systems",
    "version": "3.0.1",
    "provenance": {
        "base_model": "UNDISCLOSED",
        "fine_tuning_dataset": "UNDISCLOSED",
        "training_pipeline": "UNDISCLOSED",
        "disclosure_status": "UNDISCLOSED"
    },
    "capabilities": ["transaction_risk", "privacy_compliance", "supply_chain"],
    "contact": "trust@trustlab.example.com"
}

with open(os.path.join(base, "validators/validator-a/metadata.json"), "w") as f:
    json.dump(validator_a_meta, f, indent=2)

with open(os.path.join(base, "validators/validator-b/metadata.json"), "w") as f:
    json.dump(validator_b_meta, f, indent=2)

with open(os.path.join(base, "validators/validator-c/metadata.json"), "w") as f:
    json.dump(validator_c_meta, f, indent=2)

# --- Edge-case attestation results ---
# 50 edge cases. We encode the per-validator pass/fail.
# Design: A-B agreement ~91% (46/50 cases agree), A-C ~68% (34/50), B-C ~72% (36/50)
# Agreement means both PASS or both FAIL.

# Build result arrays carefully:
# Strategy:
#   - Cases 1-30: A=PASS, B=PASS, C=PASS  (30 agree on all)
#   - Cases 31-34: A=FAIL, B=FAIL, C=FAIL (4 agree on all)
#   - Cases 35-38: A=PASS, B=PASS, C=FAIL (4 cases: A-B agree, C disagrees)  -> A-B +4, A-C -4, B-C -4
#   - Cases 39-42: A=FAIL, B=FAIL, C=PASS (4 cases: A-B agree, C disagrees)  -> A-B +4, A-C -4, B-C -4
#   - Cases 43-46: A=PASS, B=FAIL, C=PASS (4 cases: A-C agree, A-B disagree, B-C disagree) -> A-B -4, A-C +4, B-C -4
#   - Cases 47-50: A=FAIL, B=PASS, C=FAIL (4 cases: A-C agree on FAIL, B disagrees) -> A-B -4, A-C +4, B-C -4
#
# Count:
# A-B agreements: cases 1-34 (34 agree) + cases 35-42 (8 agree) = 42 out of 50... wait let me recount
# A-B: agree on 1-34 (all three same: 30+4=34) + 35-38 (A=P,B=P agree) + 39-42 (A=F,B=F agree) = 34+4+4=42
# A-C: agree on 1-34 (34) + 43-46 (A=P,C=P agree) + 47-50 (A=F,C=F agree) = 34+4+4=42... hmm
# Let me redesign:

# New design for 50 cases:
# Group 1 (cases 1-28): A=PASS, B=PASS, C=PASS
# Group 2 (cases 29-33): A=FAIL, B=FAIL, C=FAIL  (5 cases)
# Group 3 (cases 34-38): A=PASS, B=PASS, C=FAIL  (5 cases: A-B agree, C=FAIL)
# Group 4 (cases 39-43): A=FAIL, B=FAIL, C=PASS  (5 cases: A-B agree, C=PASS)
# Group 5 (cases 44-46): A=PASS, B=FAIL, C=FAIL  (3 cases: B-C agree FAIL, A=PASS)
# Group 6 (cases 47-50): A=FAIL, B=PASS, C=PASS  (4 cases: B-C agree PASS, A=FAIL)
#
# A-B agreements: G1(28) + G2(5) + G3(5) + G4(5) = 43/50 = 86%
# A-C agreements: G1(28) + G2(5) + G5(3) + G6(4 A=FAIL,C=PASS -> disagree) = 28+5+3=36... wait
# G5: A=PASS, C=FAIL -> disagree. G6: A=FAIL, C=PASS -> disagree.
# A-C: G1(28,agree) + G2(5,agree) + G3(A=PASS,C=FAIL,disagree) + G4(A=FAIL,C=PASS,disagree) + G5(A=PASS,C=FAIL,disagree) + G6(A=FAIL,C=PASS,disagree)
# A-C agreements: 28+5 = 33/50 = 66% -- too low. Let me add more agreement.
# B-C: G1(28) + G2(5) + G5(B=FAIL,C=FAIL agree) + G6(B=PASS,C=PASS agree) = 28+5+3+4 = 40/50 = 80%... too high

# Let me just directly assign verdicts to hit targets:
# Target: A-B=91% (46/50), A-C=68% (34/50), B-C=72% (36/50)
# Agreement counts: A-B=46, A-C=34, B-C=36

# Use variables: let x=both-PASS, y=both-FAIL (both for same pair)
# For 3 validators with verdicts (a,b,c) in {P,F}^3:
# Patterns: PPP, PPF, PFP, PFF, FPP, FPF, FFP, FFF
# Let n[ppp], n[ppf], n[pfp], n[pff], n[fpp], n[fpf], n[ffp], n[fff] be counts.
# Total = 50
# A-B agree: PPP + PPF + FFF + FFP = 46
# A-C agree: PPP + PFP + FFF + FFP... wait:
# A-B agree: cases where a==b: PPP(ab=PP), PPF(ab=PP), FPP(ab=FP... no a=F,b=P disagree)
# Let me be precise:
# A=first, B=second, C=third
# PPP: a=P,b=P,c=P -> A-B agree, A-C agree, B-C agree
# PPF: a=P,b=P,c=F -> A-B agree, A-C disagree, B-C disagree
# PFP: a=P,b=F,c=P -> A-B disagree, A-C agree, B-C disagree
# PFF: a=P,b=F,c=F -> A-B disagree, A-C disagree, B-C agree
# FPP: a=F,b=P,c=P -> A-B disagree, A-C disagree, B-C agree
# FPF: a=F,b=P,c=F -> A-B disagree, A-C agree, B-C disagree
# FFP: a=F,b=F,c=P -> A-B agree, A-C disagree, B-C disagree
# FFF: a=F,b=F,c=F -> A-B agree, A-C agree, B-C agree
#
# A-B agree count = PPP + PPF + FFP + FFF
# A-C agree count = PPP + PFP + FPF + FFF
# B-C agree count = PPP + PFF + FPP + FFF
#
# Targets: A-B=46, A-C=34, B-C=36
# Let me solve:
# PPP + PPF + FFP + FFF = 46
# PPP + PFP + FPF + FFF = 34
# PPP + PFF + FPP + FFF = 36
# Total: PPP+PPF+PFP+PFF+FPP+FPF+FFP+FFF = 50
#
# Subtract eq1-eq2: PPF + FFP - PFP - FPF = 12
# Subtract eq1-eq3: PPF + FFP - PFF - FPP = 10
#
# Let's set: PPP=28, FFF=4 (contribute to all agreements)
# Then:
# PPF + FFP = 46 - 28 - 4 = 14
# PFP + FPF = 34 - 28 - 4 = 2
# PFF + FPP = 36 - 28 - 4 = 4
# Remaining = 50 - 28 - 4 - 14 - 2 - 4 = -2... too many.
#
# Let's reduce: PPP=26, FFF=3
# PPF + FFP = 46-26-3=17
# PFP + FPF = 34-26-3=5
# PFF + FPP = 36-26-3=7
# Total so far: 26+3+17+5+7=58 > 50. Too many.
#
# Try PPP=22, FFF=2:
# PPF+FFP=22, PFP+FPF=10, PFF+FPP=12
# Total: 22+2+22+10+12=68>50
#
# The constraints are tight. Let me reformulate:
# Let s=PPP+FFF (both-same triples), then:
# PPF+FFP = 46-s
# PFP+FPF = 34-s
# PFF+FPP = 36-s
# Other pairs (PFP,FPF are distinct from PFF,FPP)
# Total = s + (46-s) + (34-s) + (36-s) = 116 - 2s = 50
# 2s = 66, s = 33
# So PPP+FFF=33
# PPF+FFP = 13
# PFP+FPF = 1
# PFF+FPP = 3
# Total = 33+13+1+3=50 ✓
#
# Let PPP=30, FFF=3: s=33 ✓
# Set PPF=10, FFP=3
# Set PFP=1, FPF=0
# Set PFF=2, FPP=1
# Verify: 30+3+10+3+1+0+2+1=50 ✓
# A-B: PPP+PPF+FFP+FFF = 30+10+3+3=46 ✓
# A-C: PPP+PFP+FPF+FFF = 30+1+0+3=34 ✓
# B-C: PPP+PFF+FPP+FFF = 30+2+1+3=36 ✓

# Build the 50 edge cases:
edge_cases = []
skill_names = [f"edge-case-payment-{i:03d}" for i in range(1, 51)]

pattern_counts = {
    "PPP": 30, "PPF": 10, "FFP": 3, "FFF": 3,
    "PFP": 1, "FPF": 0, "PFF": 2, "FPP": 1
}

idx = 0
case_list = []
for pattern, count in pattern_counts.items():
    for _ in range(count):
        a_verdict = "PASS" if pattern[0] == "P" else "FAIL"
        b_verdict = "PASS" if pattern[1] == "P" else "FAIL"
        c_verdict = "PASS" if pattern[2] == "P" else "FAIL"
        case_list.append({
            "skill": skill_names[idx],
            "validator_a": a_verdict,
            "validator_b": b_verdict,
            "validator_c": c_verdict
        })
        idx += 1

# Write edge case results as a CSV-like file (messy, realistic)
csv_lines = ["skill_id,Validator-A,Validator-B,Validator-C,risk_category,notes"]
risk_categories = ["transaction_risk", "api_security", "data_exfiltration", "compliance_check", "privacy_compliance"]
for i, case in enumerate(case_list):
    risk = risk_categories[i % len(risk_categories)]
    note = random.choice(["nominal", "high-value tx", "FX edge", "retry-loop", "timeout-edge", "concurrent-session", ""])
    csv_lines.append(f"{case['skill']},{case['validator_a']},{case['validator_b']},{case['validator_c']},{risk},{note}")

with open(os.path.join(base, "attestation/results/edge_case_verdicts.csv"), "w") as f:
    f.write("\n".join(csv_lines))

# --- Evasion transferability data ---
# Skills that evaded Validator-A: 8 specific skills
# Same skills vs B: 6/8 = 75% transfer (correlated)  
# Same skills vs C: 3/8 = 37.5% transfer (independent)
evading_a = ["edge-case-payment-031", "edge-case-payment-032", "edge-case-payment-033",
             "edge-case-payment-034", "edge-case-payment-035", "edge-case-payment-036",
             "edge-case-payment-037", "edge-case-payment-038"]

# B evades same 6 of 8
evading_b_of_a = evading_a[:6]
evading_c_of_a = evading_a[:3]

evasion_data = {
    "skill": "payment-router",
    "version": "3.1",
    "analysis_date": "2025-06-15",
    "evasion_test": {
        "skills_evading_validator_a": evading_a,
        "count": len(evading_a),
        "same_skills_result_validator_b": {
            "evaded": evading_b_of_a,
            "count": len(evading_b_of_a),
            "transfer_rate": f"{len(evading_b_of_a)}/{len(evading_a)}"
        },
        "same_skills_result_validator_c": {
            "evaded": evading_c_of_a,
            "count": len(evading_c_of_a),
            "transfer_rate": f"{len(evading_c_of_a)}/{len(evading_a)}"
        }
    }
}

with open(os.path.join(base, "attestation/edge_cases/evasion_transferability.json"), "w") as f:
    json.dump(evasion_data, f, indent=2)

# --- Evaluation traces ---
# Validator-A and Validator-B traces: highly similar (87% overlap)
# Validator-C traces: independent (39% overlap with A, 42% with B)

# We'll represent traces as structured JSON with: issue_sequence, risk_categories_cited, mitigation_framing
# For A and B: same issues in same order, same risk categories, same mitigations
# For C: different issue order, different risk categories, different mitigations

skill_ids_for_traces = [f"edge-case-payment-{i:03d}" for i in range(1, 21)]  # 20 traces per validator

def make_trace_a(skill_id, seed_val):
    random.seed(seed_val)
    return {
        "skill_id": skill_id,
        "validator": "Validator-A",
        "timestamp": f"2025-06-15T{random.randint(8,17):02d}:{random.randint(0,59):02d}:00Z",
        "reasoning_chain": [
            {"step": 1, "issue": "outbound_payment_endpoint_exposure", "risk_category": "transaction_integrity", "severity": "HIGH",
             "detail": "Skill exposes outbound payment endpoints without rate limiting on high-value transactions."},
            {"step": 2, "issue": "api_key_in_memory_during_routing", "risk_category": "credential_exposure", "severity": "MEDIUM",
             "detail": "API credentials held in process memory during routing operation window."},
            {"step": 3, "issue": "retry_loop_amplification", "risk_category": "transaction_integrity", "severity": "MEDIUM",
             "detail": "Retry logic may amplify duplicate transactions under network partition."},
            {"step": 4, "issue": "insufficient_idempotency_key_scope", "risk_category": "data_consistency", "severity": "LOW",
             "detail": "Idempotency key scope does not cover FX conversion leg."},
            {"step": 5, "issue": "audit_log_completeness", "risk_category": "compliance", "severity": "LOW",
             "detail": "Audit logs may omit sub-cent rounding events."}
        ],
        "mitigation_recommendation": "Implement sandbox isolation with strict payment endpoint allowlist; enforce idempotency across full transaction scope.",
        "verdict": "CONDITIONAL_PASS" if random.random() > 0.3 else "FAIL",
        "confidence": round(random.uniform(0.75, 0.95), 2)
    }

def make_trace_b(skill_id, seed_val):
    random.seed(seed_val + 1000)
    # Very similar to A: same 5 issues, same order, same risk categories, slightly different wording
    return {
        "skill_id": skill_id,
        "validator": "Validator-B",
        "timestamp": f"2025-06-15T{random.randint(8,17):02d}:{random.randint(0,59):02d}:00Z",
        "reasoning_chain": [
            {"step": 1, "issue": "outbound_payment_endpoint_exposure", "risk_category": "transaction_integrity", "severity": "HIGH",
             "detail": "Outbound payment endpoints lack rate limiting controls for high-value transaction routing."},
            {"step": 2, "issue": "api_key_in_memory_during_routing", "risk_category": "credential_exposure", "severity": "MEDIUM",
             "detail": "Authentication credentials remain in memory throughout payment routing lifecycle."},
            {"step": 3, "issue": "retry_loop_amplification", "risk_category": "transaction_integrity", "severity": "MEDIUM",
             "detail": "Retry mechanism can cause transaction duplication under network fault conditions."},
            {"step": 4, "issue": "insufficient_idempotency_key_scope", "risk_category": "data_consistency", "severity": "LOW",
             "detail": "Idempotency enforcement does not extend to currency conversion operations."},
            {"step": 5, "issue": "audit_log_completeness", "risk_category": "compliance", "severity": "LOW",
             "detail": "Sub-cent rounding transactions may not appear in audit trail."}
        ],
        "mitigation_recommendation": "Deploy payment endpoint sandboxing with allowlist enforcement; extend idempotency key scope to cover all transaction legs.",
        "verdict": "CONDITIONAL_PASS" if random.random() > 0.3 else "FAIL",
        "confidence": round(random.uniform(0.75, 0.95), 2)
    }

def make_trace_c(skill_id, seed_val):
    random.seed(seed_val + 2000)
    # Different: starts with permission scope, different risk categories (data_residency, not transaction_integrity first), different mitigations
    issues_c = [
        {"step": 1, "issue": "excessive_permission_scope", "risk_category": "least_privilege", "severity": "HIGH",
         "detail": "Skill requests broad payment processor permissions beyond minimum required for routing function."},
        {"step": 2, "issue": "cross_border_data_residency", "risk_category": "data_residency", "severity": "HIGH",
         "detail": "Transaction metadata may traverse jurisdictions without adequate residency controls."},
        {"step": 3, "issue": "third_party_processor_supply_chain", "risk_category": "supply_chain_risk", "severity": "MEDIUM",
         "detail": "Reliance on third-party processor SDK introduces unvetted supply chain dependency."},
        {"step": 4, "issue": "pii_in_routing_metadata", "risk_category": "privacy_compliance", "severity": "MEDIUM",
         "detail": "Cardholder PII fields present in routing metadata passed to downstream processors."},
        {"step": 5, "issue": "missing_fallback_authorization", "risk_category": "availability", "severity": "LOW",
         "detail": "No fallback authorization path if primary processor is unavailable."}
    ]
    # Randomly omit one or add minor variation
    selected = issues_c[:5]
    return {
        "skill_id": skill_id,
        "validator": "Validator-C",
        "timestamp": f"2025-06-15T{random.randint(8,17):02d}:{random.randint(0,59):02d}:00Z",
        "reasoning_chain": selected,
        "mitigation_recommendation": "Apply principle of least privilege to permission scope; implement data residency controls for cross-border transaction metadata.",
        "verdict": "CONDITIONAL_PASS" if random.random() > 0.25 else "FAIL",
        "confidence": round(random.uniform(0.70, 0.92), 2)
    }

traces_a = [make_trace_a(sid, i*7) for i, sid in enumerate(skill_ids_for_traces)]
traces_b = [make_trace_b(sid, i*7) for i, sid in enumerate(skill_ids_for_traces)]
traces_c = [make_trace_c(sid, i*7) for i, sid in enumerate(skill_ids_for_traces)]

with open(os.path.join(base, "traces/validator-a/evaluation_traces.json"), "w") as f:
    json.dump({"validator": "Validator-A", "skill": "payment-router", "traces": traces_a}, f, indent=2)

with open(os.path.join(base, "traces/validator-b/evaluation_traces.json"), "w") as f:
    json.dump({"validator": "Validator-B", "skill": "payment-router", "traces": traces_b}, f, indent=2)

with open(os.path.join(base, "traces/validator-c/evaluation_traces.json"), "w") as f:
    json.dump({"validator": "Validator-C", "skill": "payment-router", "traces": traces_c}, f, indent=2)

# --- Task brief file (non-technical manager perspective) ---
task_brief = """ATTESTATION CORRELATION REVIEW - PAYMENT-ROUTER SKILL v3.1
===========================================================

Our security team needs a correlation report for the payment-router skill's
attestation process. We are using three validators: Validator-A (PayAudit Inc),
Validator-B (SecureCheck Ltd), and Validator-C (TrustLab Systems).

The compliance board wants to know if these three validators are truly
independent, or if some of them are epistemically redundant and just providing
the same check under different names.

Available data:
- Validator metadata/provenance: validators/validator-a/metadata.json, etc.
- Edge case verdicts (50 skills): attestation/results/edge_case_verdicts.csv
- Evasion transferability data: attestation/edge_cases/evasion_transferability.json
- Evaluation traces: traces/validator-*/evaluation_traces.json

Please produce the correlation report as: correlation_report.txt
"""

with open(os.path.join(base, "TASK_BRIEF.txt"), "w") as f:
    f.write(task_brief)

# Also write a summary of what the org-diversity analysis already found (distractor)
with open(os.path.join(base, "audit/current/org_diversity_summary.txt"), "w") as f:
    f.write("""Organizational Diversity Summary (pre-existing analysis)
==========================================================
Result: All three validators are from different organizations.
- Validator-A: PayAudit Inc
- Validator-B: SecureCheck Ltd  
- Validator-C: TrustLab Systems

Org-level diversity: CONFIRMED DIVERSE
Note: This analysis covers organizational independence only.
Epistemic independence (training provenance overlap) was NOT assessed here.
""")

print("Workspace generated successfully.")
print(f"Edge case pattern verification:")
print(f"  Expected A-B agreement: 46/50 = 92%")
print(f"  Expected A-C agreement: 34/50 = 68%")
print(f"  Expected B-C agreement: 36/50 = 72%")