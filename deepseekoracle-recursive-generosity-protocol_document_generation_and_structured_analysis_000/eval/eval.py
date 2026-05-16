import sys
import json
import hashlib
import re
from pathlib import Path

def read_file_safe(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    # =========================================================
    # CHECK 0: Canonical v1 was NOT modified (versioning rule)
    # =========================================================
    v1_path = workspace / "references" / "delta9-wp-003_recursive_generosity_v1.md"
    hash_record_path = workspace / ".v1_canonical_hash"
    
    try:
        original_hash_line = hash_record_path.read_text().strip()
        original_md5 = original_hash_line.split()[0]
        
        v1_content = v1_path.read_bytes()
        current_md5 = hashlib.md5(v1_content).hexdigest()
        
        v1_untouched = (original_md5 == current_md5)
        checks.append({
            "name": "v1_canonical_not_modified",
            "passed": v1_untouched,
            "detail": f"v1 hash original={original_md5}, current={current_md5}. Versioning rule: must not edit canonical in-place."
        })
    except Exception as e:
        checks.append({
            "name": "v1_canonical_not_modified",
            "passed": False,
            "detail": f"Error checking v1 hash: {e}"
        })

    # =========================================================
    # CHECK 1: New v2 file exists in references/ directory
    # =========================================================
    v2_candidates = list(workspace.rglob("delta9-wp-003_recursive_generosity_v2.md"))
    
    # Filter to only files inside references/
    v2_in_references = [f for f in v2_candidates if "references" in f.parts]
    
    v2_found = len(v2_in_references) > 0
    v2_path = v2_in_references[0] if v2_found else None
    
    checks.append({
        "name": "v2_file_exists_in_references",
        "passed": v2_found,
        "detail": f"Found v2 files in references/: {[str(f.relative_to(workspace)) for f in v2_in_references]}" if v2_found else "No delta9-wp-003_recursive_generosity_v2.md found under references/"
    })
    
    if not v2_found:
        # Can't do content checks if file missing
        for name in [
            "section_scarcity_kernel",
            "section_grace_buffer_Gn",
            "section_resonance_coefficient_R",
            "section_exponential_yield",
            "section_proof_vector_poc",
            "poc_hypothesis_present",
            "poc_minimal_intervention_alpha",
            "poc_metrics_before_after",
            "poc_confounders",
            "poc_receipt_bundle",
            "section_defense_halo_effect",
            "mercycore_scenario_addressed",
            "proprietary_equation_or_notation",
        ]:
            checks.append({"name": name, "passed": False, "detail": "v2 file not found — cannot evaluate content."})
        
        total = sum(1 for c in checks if c["passed"])
        score = total / len(checks)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    content = read_file_safe(v2_path)
    if content is None:
        checks.append({"name": "v2_readable", "passed": False, "detail": "v2 file exists but could not be read."})
        total = sum(1 for c in checks if c["passed"])
        score = total / len(checks)
        return {"passed": False, "score": round(score, 3), "checks": checks}
    
    content_lower = content.lower()

    # =========================================================
    # CHECK 2: Section 1 — Scarcity kernel
    # =========================================================
    has_scarcity_kernel = bool(re.search(
        r'scarcity[\s\-_]*(kernel|logic|assumption|zero.sum)',
        content_lower
    ))
    checks.append({
        "name": "section_scarcity_kernel",
        "passed": has_scarcity_kernel,
        "detail": f"Must identify the scarcity kernel / zero-sum assumption. Found: {has_scarcity_kernel}"
    })

    # =========================================================
    # CHECK 3: Section 2 — Grace buffer G_n notation
    # =========================================================
    has_grace_buffer_gn = bool(re.search(
        r'grace\s*buffer.*?g[_\s]?n|g[_\s]?n.*?grace\s*buffer|∣?g[ₙn]∣?|grace\s+buffer',
        content_lower
    )) or bool(re.search(r'g_n|gₙ|g\s*n\b', content))
    
    checks.append({
        "name": "section_grace_buffer_Gn",
        "passed": has_grace_buffer_gn,
        "detail": f"Must reference Grace Buffer with G_n notation. Found: {has_grace_buffer_gn}"
    })

    # =========================================================
    # CHECK 4: Section 3 — Resonance coefficient R
    # =========================================================
    has_resonance_coeff = bool(re.search(
        r'resonance\s*(coefficient|coeff)',
        content_lower
    )) and bool(re.search(r'\bR\b|\|R\||∣R∣', content))
    
    checks.append({
        "name": "section_resonance_coefficient_R",
        "passed": has_resonance_coeff,
        "detail": f"Must include Resonance Coefficient R. Has 'resonance coefficient': {bool(re.search(r'resonance coefficient', content_lower))}; has R symbol: {bool(re.search(r'\\bR\\b|\\|R\\||∣R∣', content))}"
    })

    # =========================================================
    # CHECK 5: Section 4 — Exponential yield
    # =========================================================
    has_exponential_yield = bool(re.search(
        r'exponential\s*(yield|resonance|return|result)',
        content_lower
    ))
    # Also accept the equation notation
    if not has_exponential_yield:
        has_exponential_yield = bool(re.search(r'e\^.*R|∣Y⟩|yield.*multipl', content_lower))
    
    checks.append({
        "name": "section_exponential_yield",
        "passed": has_exponential_yield,
        "detail": f"Must describe what should multiply (exponential yield). Found: {has_exponential_yield}"
    })

    # =========================================================
    # CHECK 6: Section 5 — Proof vector / POC section present
    # =========================================================
    has_proof_vector = bool(re.search(
        r'proof\s*(vector|of\s*concept|poc)|poc\b|kpi.*experiment|kpi.*visible',
        content_lower
    ))
    checks.append({
        "name": "section_proof_vector_poc",
        "passed": has_proof_vector,
        "detail": f"Must contain a Proof Vector / POC section. Found: {has_proof_vector}"
    })

    # =========================================================
    # CHECK 7: POC — Hypothesis (scarcity prediction vs expected yield)
    # =========================================================
    has_hypothesis = bool(re.search(
        r'hypothesis|scarcity\s*prediction|expected\s*yield',
        content_lower
    ))
    checks.append({
        "name": "poc_hypothesis_present",
        "passed": has_hypothesis,
        "detail": f"POC must include Hypothesis (scarcity prediction vs expected yield). Found: {has_hypothesis}"
    })

    # =========================================================
    # CHECK 8: POC — Minimal intervention alpha
    # =========================================================
    has_alpha = bool(re.search(
        r'minimal\s*intervention|intervention\s*alpha|\balpha\b.*modifier|\bα\b|alpha\s*=|\bα\s*=',
        content_lower
    )) or bool(re.search(r'\bα\b', content))
    
    checks.append({
        "name": "poc_minimal_intervention_alpha",
        "passed": has_alpha,
        "detail": f"POC must include Minimal Intervention Alpha. Found: {has_alpha}"
    })

    # =========================================================
    # CHECK 9: POC — Metrics (before/after)
    # =========================================================
    has_metrics = bool(re.search(
        r'metrics?\s*(before|after|before.*after|improvement)|before.*after|baseline.*result',
        content_lower
    ))
    checks.append({
        "name": "poc_metrics_before_after",
        "passed": has_metrics,
        "detail": f"POC must include Metrics (before/after). Found: {has_metrics}"
    })

    # =========================================================
    # CHECK 10: POC — Confounders
    # =========================================================
    has_confounders = bool(re.search(
        r'confounder|confound|control\s*variable|alternative\s*explanation|exogenous',
        content_lower
    ))
    checks.append({
        "name": "poc_confounders",
        "passed": has_confounders,
        "detail": f"POC must include Confounders section. Found: {has_confounders}"
    })

    # =========================================================
    # CHECK 11: POC — Receipt bundle (data snapshot + timestamps)
    # =========================================================
    has_receipt_bundle = bool(re.search(
        r'receipt\s*bundle|data\s*snapshot|timestamp|receipt\s*package',
        content_lower
    ))
    checks.append({
        "name": "poc_receipt_bundle",
        "passed": has_receipt_bundle,
        "detail": f"POC must include Receipt bundle (data snapshot + timestamps). Found: {has_receipt_bundle}"
    })

    # =========================================================
    # CHECK 12: Section 6 — Defense: Halo Effect
    # =========================================================
    has_halo_defense = bool(re.search(
        r'halo\s*effect|metric\s*shield|optimization\s*script|protect.*anomaly|defend.*grace',
        content_lower
    ))
    checks.append({
        "name": "section_defense_halo_effect",
        "passed": has_halo_defense,
        "detail": f"Must include Defense section with Halo Effect / metric shielding. Found: {has_halo_defense}"
    })

    # =========================================================
    # CHECK 13: MercyCore scenario is actually addressed
    # =========================================================
    has_mercycore = bool(re.search(
        r'mercycore|nurse\s*well.?being|nwbi|hospital.*network|nursing\s*staff',
        content_lower
    ))
    checks.append({
        "name": "mercycore_scenario_addressed",
        "passed": has_mercycore,
        "detail": f"Document must address the MercyCore / nurse well-being scenario. Found: {has_mercycore}"
    })

    # =========================================================
    # CHECK 14: Uses proprietary equation notation or key formula
    # =========================================================
    has_equation = bool(re.search(
        r'∣Y⟩|Σ.*G.*e\^|recursive\s*yield\s*equation|total\s*systemic\s*yield',
        content
    ))
    if not has_equation:
        # Accept textual description of the equation
        has_equation = bool(re.search(
            r'total\s*systemic\s*yield|yield\s*=\s*sum.*grace|sum.*gn.*resonance',
            content_lower
        ))
    checks.append({
        "name": "proprietary_equation_or_notation",
        "passed": has_equation,
        "detail": f"Must reference the Recursive Yield Equation notation (|Y>, Σ(|Gn|)•e^|R|) or describe total systemic yield formula. Found: {has_equation}"
    })

    # =========================================================
    # FINAL SCORING
    # =========================================================
    total_passed = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(total_passed / total_checks, 3)
    
    # Must pass v1 untouched + v2 exists + at least 10 content checks
    critical_passed = (
        checks[0]["passed"] and  # v1 not modified
        checks[1]["passed"]      # v2 exists in references/
    )
    overall_pass = critical_passed and (total_passed >= 11)

    return {
        "passed": overall_pass,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [], "error": "No workspace path provided"}))
        sys.exit(1)
    
    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))