import sys
import json
import os
from pathlib import Path

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_output_file(workspace):
    # Look for the specifically requested file
    candidates = list(Path(workspace).rglob("legal_analysis.json"))
    if candidates:
        return candidates[0]
    return None

def check_field_contains(obj, *keys):
    """Navigate nested dict by keys and return the final value, or None."""
    cur = obj
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return None
    return cur

def text_contains_any(text, terms):
    if not isinstance(text, str):
        text = json.dumps(text)
    text_lower = text.lower()
    return any(t.lower() in text_lower for t in terms)

def run_eval(workspace):
    checks = []
    total_score = 0.0
    max_score = 0.0

    # Find output file
    output_file = find_output_file(workspace)
    file_found = output_file is not None

    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found legal_analysis.json at {output_file}" if file_found else "legal_analysis.json not found anywhere in workspace"
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        data = load_json_file(output_file)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": f"Failed to parse JSON: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "json_parseable", "passed": True, "detail": "File is valid JSON"})

    # Convert entire output to string for broad searches
    data_str = json.dumps(data).lower()

    # ============================================================
    # CHECK GROUP 1: ISSUE_1 - Pre-ratification obligations
    # Must invoke VCLT Art. 18 (not Art. 11/26/31) as the source of
    # pre-ratification obligation not to defeat object and purpose.
    # ============================================================
    max_score += 20.0

    # 1a: Must mention Art. 18 (or article 18) in context of pre-ratification
    art18_mentioned = "18" in data_str and any(t in data_str for t in ["pre-ratif", "preratif", "before ratif", "prior to ratif", "object and purpose", "object & purpose", "defeat"])
    checks.append({
        "name": "issue1_vclt_art18",
        "passed": art18_mentioned,
        "detail": "Must reference VCLT Article 18 obligation not to defeat object and purpose prior to ratification"
    })
    if art18_mentioned:
        total_score += 10.0

    # 1b: Must NOT claim Ruritania was fully bound by treaty obligations before ratification
    # (i.e., should acknowledge treaty was not yet in force for Ruritania pre-ratification,
    # but Art. 18 creates a limited negative obligation)
    incorrect_claim = any(t in data_str for t in [
        "fully bound", "completely bound", "absolutely bound"
    ]) and "pre-ratif" in data_str
    # Actually check that the analysis distinguishes the Art 18 obligation from full treaty binding
    art18_nuance = any(t in data_str for t in [
        "not yet in force", "not entered into force", "not bound by all", "limited obligation",
        "negative obligation", "only obligation", "solely obliged", "merely", "not fully"
    ])
    checks.append({
        "name": "issue1_pre_ratification_nuance",
        "passed": art18_nuance,
        "detail": "Must clarify that Art. 18 imposes only a limited/negative obligation (not full treaty binding) before ratification"
    })
    if art18_nuance:
        total_score += 10.0

    # ============================================================
    # CHECK GROUP 2: ISSUE_2 - Material breach + treaty termination procedure
    # Key proprietary trap: material breach does NOT automatically terminate;
    # VCLT Arts. 65-68 procedural steps are mandatory.
    # A press release is NOT a valid termination method.
    # ============================================================
    max_score += 30.0

    # 2a: Must reference VCLT Art. 60 (material breach)
    art60_mentioned = "60" in data_str and any(t in data_str for t in ["material breach", "breach"])
    checks.append({
        "name": "issue2_vclt_art60",
        "passed": art60_mentioned,
        "detail": "Must reference VCLT Article 60 (material breach) as grounds for treaty termination"
    })
    if art60_mentioned:
        total_score += 8.0

    # 2b: Must state that material breach does NOT ipso facto terminate the treaty
    no_auto_termination = any(t in data_str for t in [
        "ipso facto", "not automatically", "does not automatically", "automatically terminate",
        "merely provides", "only a ground", "only provides", "gives rise", "does not itself terminate",
        "basis for", "entitlement to"
    ])
    checks.append({
        "name": "issue2_no_ipso_facto_termination",
        "passed": no_auto_termination,
        "detail": "Must state that material breach does not ipso facto (automatically) terminate the treaty"
    })
    if no_auto_termination:
        total_score += 10.0

    # 2c: Must reference Arts. 65-68 procedural requirements
    arts_65_68 = any(t in data_str for t in ["65", "66", "67", "68"]) and any(t in data_str for t in [
        "procedur", "notification", "notify", "notice", "formal", "step", "requirement"
    ])
    checks.append({
        "name": "issue2_vclt_art65_68_procedure",
        "passed": arts_65_68,
        "detail": "Must reference VCLT Arts. 65-68 mandatory procedural steps for treaty termination"
    })
    if arts_65_68:
        total_score += 7.0

    # 2d: Must conclude press release is legally defective/insufficient
    press_release_defect = any(t in data_str for t in [
        "press release", "defective", "insufficient", "invalid", "ineffective", "not valid",
        "procedurally", "failed to comply", "did not comply", "inadequate"
    ])
    checks.append({
        "name": "issue2_press_release_defective",
        "passed": press_release_defect,
        "detail": "Must conclude Ruritania's press release termination is legally defective/ineffective"
    })
    if press_release_defect:
        total_score += 5.0

    # ============================================================
    # CHECK GROUP 3: ISSUE_3 - Customary international law analysis
    # Must apply two-element test: state practice + opinio juris
    # Must correctly analyze persistent objector doctrine for Gondoria/Pacifica/Norstland
    # ============================================================
    max_score += 30.0

    # 3a: Must identify both elements of CIL formation
    state_practice_mentioned = any(t in data_str for t in ["state practice", "state's practice", "states practice", "national practice", "general practice"])
    opinio_juris_mentioned = any(t in data_str for t in ["opinio juris", "legal obligation", "sense of legal", "belief that", "acting as law", "accepted as law"])
    both_cil_elements = state_practice_mentioned and opinio_juris_mentioned
    checks.append({
        "name": "issue3_cil_two_elements",
        "passed": both_cil_elements,
        "detail": f"Must identify both CIL elements. State practice: {state_practice_mentioned}, Opinio juris: {opinio_juris_mentioned}"
    })
    if both_cil_elements:
        total_score += 8.0

    # 3b: Must address the 2/52 states that practice moratorium as "courtesy" - this affects opinio juris
    opinio_juris_nuance = any(t in data_str for t in [
        "courtesy", "2 states", "two states", "not legally required",
        "not consider", "not as legal", "excluding", "opinio juris issue",
        "absence of opinio"
    ])
    checks.append({
        "name": "issue3_opinio_juris_nuance",
        "passed": opinio_juris_nuance,
        "detail": "Should address that 2 states practice the moratorium without considering it legally required (affects opinio juris)"
    })
    if opinio_juris_nuance:
        total_score += 5.0

    # 3c: Must correctly apply persistent objector doctrine
    persistent_objector_mentioned = any(t in data_str for t in [
        "persistent objector", "persistent object"
    ])
    checks.append({
        "name": "issue3_persistent_objector_mentioned",
        "passed": persistent_objector_mentioned,
        "detail": "Must invoke the persistent objector doctrine for Gondoria, Pacifica, and Norstland"
    })
    if persistent_objector_mentioned:
        total_score += 8.0

    # 3d: Persistent objector TIMING - objection must be during formation, not after
    # Gondoria etc. objected since 1992, DURING formation -> valid persistent objectors
    # -> they are NOT bound by the CIL rule
    persistent_objector_outcome = any(t in data_str for t in [
        "not bound", "exempt", "not applicable", "does not bind", "excluded from",
        "not subject to", "free from", "immune"
    ]) and any(t in data_str for t in ["gondoria", "pacifica", "norstland", "three states", "persistent objector"])
    checks.append({
        "name": "issue3_persistent_objector_not_bound",
        "passed": persistent_objector_outcome,
        "detail": "Must conclude that valid persistent objectors (Gondoria/Pacifica/Norstland) are NOT bound by the CIL drilling moratorium rule"
    })
    if persistent_objector_outcome:
        total_score += 9.0

    # ============================================================
    # CHECK GROUP 4: ISSUE_4 - Treaty interpretation (VCLT Arts. 31-32)
    # Must use Art. 31 first (text, context, object/purpose, subsequent practice)
    # May use Art. 32 (travaux) only if Art. 31 leaves ambiguity
    # ============================================================
    max_score += 20.0

    # 4a: Must reference Art. 31 for primary interpretation
    art31_mentioned = "31" in data_str and any(t in data_str for t in [
        "interpret", "ordinary meaning", "object and purpose", "context", "subsequent practice"
    ])
    checks.append({
        "name": "issue4_vclt_art31",
        "passed": art31_mentioned,
        "detail": "Must apply VCLT Art. 31 as primary interpretation method"
    })
    if art31_mentioned:
        total_score += 8.0

    # 4b: Must treat travaux as supplementary (Art. 32) only after Art. 31 ambiguity
    art32_supplementary = any(t in data_str for t in [
        "32", "travaux", "preparatory work", "supplementary", "subsidiary"
    ]) and any(t in data_str for t in [
        "ambiguous", "ambiguity", "obscure", "supplementary means", "after", "only if", "remaining"
    ])
    checks.append({
        "name": "issue4_vclt_art32_supplementary",
        "passed": art32_supplementary,
        "detail": "Must treat travaux préparatoires (Art. 32) as SUPPLEMENTARY means, applicable only when Art. 31 yields ambiguity"
    })
    if art32_supplementary:
        total_score += 12.0

    # ============================================================
    # BONUS CHECK: References landmark cases (Norwegian Fisheries or North Sea Continental Shelf)
    # ============================================================
    case_reference = any(t in data_str for t in [
        "norwegian fisheries", "north sea continental shelf", "north sea",
        "nicaraguan", "nicaragua", "military and paramilitary",
        "continental shelf"
    ])
    checks.append({
        "name": "bonus_case_references",
        "passed": case_reference,
        "detail": "Bonus: References at least one landmark ICJ case relevant to CIL analysis"
    })
    if case_reference:
        total_score += 2.0
        max_score += 2.0  # only add to max if it can be earned

    # ============================================================
    # OVERALL SCORING
    # ============================================================
    base_max = 100.0
    score_ratio = min(total_score / max_score, 1.0) if max_score > 0 else 0.0
    
    # Must pass at least 6 of the 12 non-bonus checks
    core_checks = [c for c in checks if not c["name"].startswith("bonus") and c["name"] not in ("output_file_exists", "json_parseable")]
    core_passed = sum(1 for c in core_checks if c["passed"])
    overall_passed = core_passed >= 7 and score_ratio >= 0.60

    return {
        "passed": overall_passed,
        "score": round(score_ratio, 4),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = run_eval(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crashed", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))