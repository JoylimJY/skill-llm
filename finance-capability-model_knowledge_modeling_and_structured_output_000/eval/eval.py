import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # ── 1. Find the output file ──────────────────────────────────────────────
    found_files = list(Path(workspace).rglob("finance_capability_model.json"))
    file_exists = len(found_files) > 0
    checks.append({
        "name": "Output file finance_capability_model.json exists",
        "passed": file_exists,
        "detail": f"Found at: {found_files[0]}" if file_exists else "File not found anywhere in workspace"
    })
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 2. Parse JSON ────────────────────────────────────────────────────────
    try:
        with open(found_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        is_list = isinstance(data, list)
        checks.append({
            "name": "Output is a valid JSON array",
            "passed": is_list,
            "detail": f"Type is {type(data).__name__}"
        })
        if not is_list:
            return {"passed": False, "score": 0.05, "checks": checks}
    except Exception as e:
        checks.append({
            "name": "Output is a valid JSON array",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── 3. Must have exactly 6 entries ───────────────────────────────────────
    has_six = len(data) == 6
    checks.append({
        "name": "JSON array contains exactly 6 capability entries",
        "passed": has_six,
        "detail": f"Found {len(data)} entries"
    })

    # ── 4. Required fields present in every entry ────────────────────────────
    REQUIRED_FIELDS = {
        "capability_name",
        "sub_capabilities",
        "key_tools_metrics",
        "key_deliverables",
        "assessment_questions",
    }
    all_have_required = True
    missing_detail = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            all_have_required = False
            missing_detail.append(f"Entry {i} is not a dict")
            continue
        missing = REQUIRED_FIELDS - set(entry.keys())
        if missing:
            all_have_required = False
            missing_detail.append(f"Entry {i} missing fields: {missing}")

    checks.append({
        "name": "All 5 required fields present in every entry (capability_name, sub_capabilities, key_tools_metrics, key_deliverables, assessment_questions)",
        "passed": all_have_required,
        "detail": "; ".join(missing_detail) if missing_detail else "All entries have all required fields"
    })

    # ── 5. Canonical Chinese dimension names coverage ────────────────────────
    CANONICAL_NAMES = [
        "资金管理与流动性风险驾驭能力",
        "资本结构与融资筹划能力",
        "全面预算与战略资源配置能力",
        "资产管控与资本运作能力",
        "经营分析与决策支持能力",
        "数字化金融与合规风控能力",
    ]
    found_names = []
    for entry in data:
        if isinstance(entry, dict) and "capability_name" in entry:
            found_names.append(entry["capability_name"])

    matched_canonical = []
    unmatched_canonical = []
    for cn in CANONICAL_NAMES:
        if cn in found_names:
            matched_canonical.append(cn)
        else:
            unmatched_canonical.append(cn)

    all_canonical_present = len(unmatched_canonical) == 0
    checks.append({
        "name": "All 6 canonical Chinese capability dimension names are correctly used",
        "passed": all_canonical_present,
        "detail": (
            f"Matched: {matched_canonical}. Missing canonical names: {unmatched_canonical}. Found names: {found_names}"
            if not all_canonical_present
            else f"All 6 canonical names matched: {matched_canonical}"
        )
    })

    # ── 6. sub_capabilities must be non-empty lists ──────────────────────────
    sub_cap_ok = True
    sub_cap_detail = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            continue
        sc = entry.get("sub_capabilities", None)
        if not isinstance(sc, list) or len(sc) == 0:
            sub_cap_ok = False
            sub_cap_detail.append(f"Entry {i} ('{entry.get('capability_name','?')}') has invalid sub_capabilities: {sc}")
    checks.append({
        "name": "sub_capabilities is a non-empty list in all entries",
        "passed": sub_cap_ok,
        "detail": "; ".join(sub_cap_detail) if sub_cap_detail else "OK"
    })

    # ── 7. key_tools_metrics must be non-empty lists ─────────────────────────
    ktm_ok = True
    ktm_detail = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            continue
        ktm = entry.get("key_tools_metrics", None)
        if not isinstance(ktm, list) or len(ktm) == 0:
            ktm_ok = False
            ktm_detail.append(f"Entry {i} ('{entry.get('capability_name','?')}') has invalid key_tools_metrics: {ktm}")
    checks.append({
        "name": "key_tools_metrics is a non-empty list in all entries",
        "passed": ktm_ok,
        "detail": "; ".join(ktm_detail) if ktm_detail else "OK"
    })

    # ── 8. key_deliverables must be non-empty lists ───────────────────────────
    kd_ok = True
    kd_detail = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            continue
        kd = entry.get("key_deliverables", None)
        if not isinstance(kd, list) or len(kd) == 0:
            kd_ok = False
            kd_detail.append(f"Entry {i} ('{entry.get('capability_name','?')}') has invalid key_deliverables: {kd}")
    checks.append({
        "name": "key_deliverables is a non-empty list in all entries",
        "passed": kd_ok,
        "detail": "; ".join(kd_detail) if kd_detail else "OK"
    })

    # ── 9. assessment_questions must be non-empty lists of question strings ──
    aq_ok = True
    aq_detail = []
    for i, entry in enumerate(data):
        if not isinstance(entry, dict):
            continue
        aq = entry.get("assessment_questions", None)
        if not isinstance(aq, list) or len(aq) == 0:
            aq_ok = False
            aq_detail.append(f"Entry {i} ('{entry.get('capability_name','?')}') has empty/invalid assessment_questions")
            continue
        # Each item should be a non-empty string (actual question)
        for j, q in enumerate(aq):
            if not isinstance(q, str) or len(q.strip()) < 5:
                aq_ok = False
                aq_detail.append(f"Entry {i} question {j} is not a valid string: {repr(q)}")

    checks.append({
        "name": "assessment_questions is a non-empty list of substantive question strings in all entries",
        "passed": aq_ok,
        "detail": "; ".join(aq_detail) if aq_detail else "OK"
    })

    # ── 10. Spot-check: SKILL.md sub-capabilities in relevant dimensions ─────
    # Check dimension 1 (资金管理) has cash-flow/treasury-related sub-caps
    spot_ok = False
    spot_detail = "Could not find 资金管理与流动性风险驾驭能力 entry"
    for entry in data:
        if isinstance(entry, dict) and entry.get("capability_name") == "资金管理与流动性风险驾驭能力":
            sc = entry.get("sub_capabilities", [])
            sc_text = " ".join(sc).lower() if sc else ""
            # Should contain something related to cash flow or liquidity or 资金
            keywords = ["现金", "cash", "资金", "流动", "liquidity", "pool", "池"]
            if any(kw in sc_text for kw in keywords):
                spot_ok = True
                spot_detail = f"sub_capabilities for 资金管理 look relevant: {sc}"
            else:
                spot_detail = f"sub_capabilities for 资金管理 don't seem relevant to cash/treasury: {sc}"
            break

    checks.append({
        "name": "Spot-check: 资金管理与流动性风险驾驭能力 has relevant sub-capabilities",
        "passed": spot_ok,
        "detail": spot_detail
    })

    # ── Score calculation ────────────────────────────────────────────────────
    weights = {
        0: 0.05,   # file exists
        1: 0.05,   # valid JSON array
        2: 0.10,   # 6 entries
        3: 0.20,   # all 5 fields present
        4: 0.25,   # canonical names
        5: 0.08,   # sub_capabilities lists
        6: 0.08,   # key_tools_metrics lists
        7: 0.08,   # key_deliverables lists
        8: 0.08,   # assessment_questions
        9: 0.03,   # spot-check
    }
    score = sum(weights[i] for i, c in enumerate(checks) if c["passed"])
    passed = all(c["passed"] for c in checks)

    return {"passed": passed, "score": round(score, 3), "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))