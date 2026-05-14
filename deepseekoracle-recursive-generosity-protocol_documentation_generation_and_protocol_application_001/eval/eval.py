import sys
import json
import re
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    # =========================================================
    # HELPER
    # =========================================================
    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # =========================================================
    # FIND THE OUTPUT FILE
    # Must be a NEW versioned file under references/
    # Must NOT be the canonical v1 file
    # =========================================================
    canonical_v1 = workspace / "references" / "delta9-wp-003_recursive_generosity_v1.md"

    # Find all .md files in references/ that are NOT v1
    candidate_files = [
        f for f in (workspace / "references").glob("*.md")
        if f.name != "delta9-wp-003_recursive_generosity_v1.md"
    ]

    # Also search recursively in case agent nested it
    candidate_files_recursive = [
        f for f in workspace.rglob("*.md")
        if f.name != "delta9-wp-003_recursive_generosity_v1.md"
        and "references" in str(f.relative_to(workspace))
        and f not in candidate_files
    ]
    candidate_files = candidate_files + candidate_files_recursive

    if not candidate_files:
        check("output_file_exists_in_references", False,
              "No new versioned .md file found under references/. The agent must create a new file there, not edit v1.")
        # Return early
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    # Pick the most plausible candidate (largest file, most content)
    target_file = max(candidate_files, key=lambda f: f.stat().st_size)
    check("output_file_exists_in_references", True,
          f"Found candidate output file: {target_file.relative_to(workspace)}")

    # Verify canonical v1 was NOT modified (its content must still contain the CANONICAL TEXT NOTICE)
    try:
        v1_content = canonical_v1.read_text(encoding="utf-8")
        v1_intact = "CANONICAL TEXT NOTICE" in v1_content and "Sealed & Sovereign" in v1_content
        check("canonical_v1_not_modified", v1_intact,
              "Canonical v1 file still contains original CANONICAL TEXT NOTICE and header." if v1_intact
              else "Canonical v1 file appears to have been modified or its key markers are missing.")
    except Exception as e:
        check("canonical_v1_not_modified", False, f"Could not read canonical v1: {e}")

    # =========================================================
    # READ TARGET FILE
    # =========================================================
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        check("output_file_readable", False, f"Could not read output file: {e}")
        score = 1/7
        return {"passed": False, "score": score, "checks": checks}

    check("output_file_readable", True, f"Output file is readable, length={len(content)} chars.")

    content_lower = content.lower()

    # =========================================================
    # CHECK 1: SCARCITY KERNEL (Step 1)
    # Must identify a zero-sum assumption related to the hospital/nursing scenario
    # =========================================================
    scarcity_patterns = [
        r"scarcity\s+kernel",
        r"zero.sum",
        r"cost\s+center",
        r"scarcity\s+logic",
        r"scarcity\s+assumption",
    ]
    has_scarcity = any(re.search(p, content_lower) for p in scarcity_patterns)
    check("section_1_scarcity_kernel", has_scarcity,
          "Found scarcity kernel / zero-sum assumption section." if has_scarcity
          else "Missing Section 1: Scarcity kernel. Must identify the zero-sum assumption.")

    # =========================================================
    # CHECK 2: GRACE BUFFER G_n (Step 2)
    # Must reference Grace Buffer and/or G_n notation
    # =========================================================
    grace_patterns = [
        r"grace\s+buffer",
        r"g[_\s]?n",
        r"∣g",
        r"\|g",
        r"haven.aligned",
        r"haven\s+multiplier",
    ]
    has_grace = any(re.search(p, content_lower) for p in grace_patterns)
    # Also check for unicode variant
    if not has_grace:
        has_grace = "gₙ" in content.lower() or "grace buffer" in content.lower()
    check("section_2_grace_buffer", has_grace,
          "Found Grace Buffer (G_n) reference." if has_grace
          else "Missing Section 2: Grace buffer (G_n). Must name the smallest Haven-aligned modifier.")

    # =========================================================
    # CHECK 3: RESONANCE COEFFICIENT (Step 3)
    # Must reference Resonance Coefficient R and distinguish real vs performative
    # =========================================================
    resonance_patterns = [
        r"resonance\s+coefficient",
        r"\|r\|",
        r"∣r⟩",
        r"performative",
        r"real\s+vs",
        r"hollow",
        r"r⟩",
    ]
    has_resonance = any(re.search(p, content_lower) for p in resonance_patterns)
    if not has_resonance:
        has_resonance = "resonance coefficient" in content.lower() or "∣R⟩" in content
    check("section_3_resonance_coefficient", has_resonance,
          "Found Resonance Coefficient (R) section." if has_resonance
          else "Missing Section 3: Resonance coefficient (R). Must address what makes it real vs performative.")

    # =========================================================
    # CHECK 4: EXPONENTIAL YIELD (Step 4)
    # Must reference exponential yield and at least one yield type (retention, resilience, innovation)
    # =========================================================
    yield_patterns = [
        r"exponential\s+yield",
        r"e\^",
        r"∣y⟩",
        r"\|y\|",
        r"retention",
        r"resilience",
        r"innovation",
        r"recursive\s+yield",
    ]
    has_yield = any(re.search(p, content_lower) for p in yield_patterns)
    check("section_4_exponential_yield", has_yield,
          "Found Exponential yield section with multiplier references." if has_yield
          else "Missing Section 4: Exponential yield. Must show what multiplies (retention, resilience, innovation).")

    # =========================================================
    # CHECK 5: PROOF VECTOR / POC (Step 5)
    # Must contain the default proof template fields:
    #   - Hypothesis
    #   - Minimal intervention alpha (THE TRAP)
    #   - Metrics (before/after)
    #   - Confounders
    #   - Receipt bundle
    # =========================================================
    has_hypothesis = bool(re.search(r"hypothesis", content_lower))
    has_alpha = bool(re.search(r"minimal\s+intervention\s+alpha|intervention\s+alpha|\bα\b|alpha\b", content_lower))
    has_metrics = bool(re.search(r"metrics?\s*(before|after|:)", content_lower) or
                       re.search(r"before.after|before/after", content_lower))
    has_confounders = bool(re.search(r"confounder", content_lower))
    has_receipt = bool(re.search(r"receipt\s+bundle|data\s+snapshot|timestamp", content_lower))

    poc_fields_present = sum([has_hypothesis, has_alpha, has_metrics, has_confounders, has_receipt])

    check("section_5_proof_vector_hypothesis", has_hypothesis,
          "POC contains Hypothesis field." if has_hypothesis else "POC missing Hypothesis field.")
    check("section_5_proof_vector_alpha", has_alpha,
          "POC contains 'Minimal intervention alpha' field (key proprietary trap)." if has_alpha
          else "POC missing 'Minimal intervention alpha' — this is the primary proprietary trap from SKILL.md.")
    check("section_5_proof_vector_metrics", has_metrics,
          "POC contains before/after Metrics." if has_metrics else "POC missing Metrics (before/after) field.")
    check("section_5_proof_vector_confounders", has_confounders,
          "POC contains Confounders field." if has_confounders else "POC missing Confounders field.")
    check("section_5_proof_vector_receipt_bundle", has_receipt,
          "POC contains Receipt bundle (data snapshot + timestamps)." if has_receipt
          else "POC missing Receipt bundle field.")

    # =========================================================
    # CHECK 6: DEFENSE / HALO EFFECT (Step 6)
    # Must reference Halo Effect and/or metric shielding
    # =========================================================
    defense_patterns = [
        r"halo\s+effect",
        r"metric\s+shield",
        r"optimization\s+script",
        r"defense",
        r"anomaly.*high.yield",
        r"high.yield.*anomaly",
    ]
    has_defense = any(re.search(p, content_lower) for p in defense_patterns)
    check("section_6_defense_halo_effect", has_defense,
          "Found Defense section with Halo Effect / metric shielding." if has_defense
          else "Missing Section 6: Defense referencing Halo Effect or metric shielding against optimization scripts.")

    # =========================================================
    # CHECK 7: HOSPITAL / NURSING SCENARIO CONTEXT
    # Must be applied to hospital staffing / nursing burnout
    # =========================================================
    hospital_patterns = [
        r"nurs",
        r"hospital",
        r"icu",
        r"patient",
        r"staffing",
        r"healthcare",
        r"clinical",
        r"ward",
        r"burnout",
    ]
    has_hospital_context = any(re.search(p, content_lower) for p in hospital_patterns)
    check("applied_to_hospital_scenario", has_hospital_context,
          "Document is contextually applied to hospital/nursing scenario." if has_hospital_context
          else "Document does not appear to be applied to the hospital staffing scenario.")

    # =========================================================
    # SCORING
    # =========================================================
    all_checks = checks[1:]  # skip the "file exists" meta-check at index 0, count from structural ones

    # Weight the alpha check double (it's the proprietary trap)
    total_weight = 0
    weighted_score = 0
    weights = {
        "canonical_v1_not_modified": 1,
        "output_file_readable": 0,  # not scored, just informational
        "section_1_scarcity_kernel": 1,
        "section_2_grace_buffer": 1,
        "section_3_resonance_coefficient": 1,
        "section_4_exponential_yield": 1,
        "section_5_proof_vector_hypothesis": 1,
        "section_5_proof_vector_alpha": 2,  # double weight — proprietary trap
        "section_5_proof_vector_metrics": 1,
        "section_5_proof_vector_confounders": 1,
        "section_5_proof_vector_receipt_bundle": 1,
        "section_6_defense_halo_effect": 1,
        "applied_to_hospital_scenario": 1,
        "output_file_exists_in_references": 1,
    }

    for c in checks:
        w = weights.get(c["name"], 1)
        total_weight += w
        if c["passed"]:
            weighted_score += w

    score = round(weighted_score / total_weight, 3) if total_weight > 0 else 0.0
    passed = (
        score >= 0.75
        and checks[0]["passed"]  # file exists
        and has_alpha             # must have the proprietary trap
    )

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))