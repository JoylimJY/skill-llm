import json
import math
import sys
import re
import yaml
from pathlib import Path

def cosine_similarity(v1, v2):
    dot = sum(a*b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a**2 for a in v1))
    norm2 = math.sqrt(sum(b**2 for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

def extract_frontmatter(text):
    match = re.match(r'^---\s*\n(.*?)\n---', text, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except Exception:
        return None

def normalize(v):
    norm = math.sqrt(sum(x**2 for x in v))
    if norm == 0:
        return v
    return [x/norm for x in v]

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []

    H_dir_raw = [0.82, 0.75, 0.55]
    H_unit = normalize(H_dir_raw)

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 1: All 5 new vector notes exist in vault with COMPLETE frontmatter
    # ──────────────────────────────────────────────────────────────────────────
    vectors_dir = workspace / "obsidian-vault/compass/vectors"
    md_files = list(vectors_dir.glob("*.md"))

    REQUIRED_FIELDS = ["type", "date", "what", "why_surface", "why_essence",
                       "direction", "intensity", "confidence", "weight", "domain",
                       "cluster", "tags"]

    valid_vectors = []
    complete_count = 0
    incomplete_details = []

    for mf in md_files:
        try:
            text = mf.read_text()
            fm = extract_frontmatter(text)
            if fm and fm.get("type") == "vector":
                missing = [f for f in REQUIRED_FIELDS if f not in fm]
                if not missing:
                    complete_count += 1
                    valid_vectors.append(fm)
                else:
                    incomplete_details.append(f"{mf.name}: missing {missing}")
        except Exception as e:
            incomplete_details.append(f"{mf.name}: read error {e}")

    # We need at least 5 complete vectors (the 5 new ones from the batch)
    check1_passed = complete_count >= 5
    checks.append({
        "name": "vault_vector_notes_complete",
        "passed": check1_passed,
        "detail": f"{complete_count} complete vector notes found (need ≥5). Incomplete: {incomplete_details[:3]}"
    })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 2: vectors.json exists and contains ≥5 valid vectors
    # ──────────────────────────────────────────────────────────────────────────
    vectors_json_path = workspace / "scripts/vectors.json"
    try:
        vectors_json = json.loads(vectors_json_path.read_text())
        vj_count = len(vectors_json)
        check2_passed = vj_count >= 5
        checks.append({
            "name": "vectors_json_populated",
            "passed": check2_passed,
            "detail": f"vectors.json has {vj_count} vectors (need ≥5)"
        })
    except Exception as e:
        vectors_json = []
        checks.append({
            "name": "vectors_json_populated",
            "passed": False,
            "detail": f"Could not read vectors.json: {e}"
        })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 3: magnetization.json is fresh (not the stale stub)
    # ──────────────────────────────────────────────────────────────────────────
    mag_path = workspace / "scripts/magnetization.json"
    try:
        mag_data = json.loads(mag_path.read_text())
        is_stale = (
            mag_data.get("computed_at") == "2026-01-01" or
            mag_data.get("vector_count", 0) == 0 or
            "STALE" in mag_data.get("H_one_liner", "")
        )
        has_clusters = isinstance(mag_data.get("clusters"), dict) and len(mag_data["clusters"]) > 0
        has_mag_value = isinstance(mag_data.get("magnetization_magnitude"), float)
        check3_passed = (not is_stale) and has_clusters and has_mag_value
        checks.append({
            "name": "magnetization_json_fresh",
            "passed": check3_passed,
            "detail": f"computed_at={mag_data.get('computed_at')}, clusters={list(mag_data.get('clusters',{}).keys())}, M={mag_data.get('magnetization_magnitude')}, stale={is_stale}"
        })
    except Exception as e:
        mag_data = {}
        checks.append({
            "name": "magnetization_json_fresh",
            "passed": False,
            "detail": f"Could not read magnetization.json: {e}"
        })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 4: compass_data.json exists and has correct top-level structure
    # ──────────────────────────────────────────────────────────────────────────
    compass_path = workspace / "scripts/compass_data.json"
    try:
        compass_data = json.loads(compass_path.read_text())
        has_identity = isinstance(compass_data.get("identity"), list)
        has_opps = isinstance(compass_data.get("opportunities"), list)
        has_H = isinstance(compass_data.get("H"), dict) and "dir" in compass_data["H"] and "mag" in compass_data["H"]
        has_oneliner = isinstance(compass_data.get("oneLiner"), str) and len(compass_data["oneLiner"]) > 5
        has_clusters = isinstance(compass_data.get("clusters"), list) and len(compass_data["clusters"]) > 0
        check4_passed = all([has_identity, has_opps, has_H, has_oneliner, has_clusters])
        checks.append({
            "name": "compass_data_json_structure",
            "passed": check4_passed,
            "detail": f"identity={has_identity}({len(compass_data.get('identity',[]))}), opportunities={has_opps}({len(compass_data.get('opportunities',[]))}), H={has_H}, oneLiner={has_oneliner}, clusters={has_clusters}"
        })
    except Exception as e:
        compass_data = {}
        checks.append({
            "name": "compass_data_json_structure",
            "passed": False,
            "detail": f"Could not read compass_data.json: {e}"
        })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 5: identity vs opportunity split is correct
    # ──────────────────────────────────────────────────────────────────────────
    try:
        identity_beads = compass_data.get("identity", [])
        opp_beads = compass_data.get("opportunities", [])
        
        # identity should contain non-company vectors (vec_001, vec_002)
        # opportunities should contain company vectors (vec_003, vec_004, vec_005)
        
        identity_whats = [b.get("what","").lower() for b in identity_beads]
        opp_whats = [b.get("what","").lower() for b in opp_beads]
        
        # Check that company/opportunity vectors are in opportunities
        company_keywords = ["meridian", "neuroscale", "techcorp", "ml research role", "staff engineer"]
        opps_correct = sum(1 for kw in company_keywords 
                          if any(kw in w for w in opp_whats)) >= 2
        
        # Check that personal vectors are in identity
        personal_keywords = ["pm role", "paper", "management", "ml paper", "rejected senior", "deep-dive"]
        identity_correct = sum(1 for kw in personal_keywords 
                               if any(kw in w for w in identity_whats)) >= 1
        
        check5_passed = opps_correct and identity_correct
        checks.append({
            "name": "identity_opportunity_split",
            "passed": check5_passed,
            "detail": f"identity_whats={identity_whats[:3]}, opp_whats={opp_whats[:3]}, opps_correct={opps_correct}, identity_correct={identity_correct}"
        })
    except Exception as e:
        checks.append({
            "name": "identity_opportunity_split",
            "passed": False,
            "detail": f"Error checking split: {e}"
        })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 6: 'cl' field color classification is correct per SKILL.md thresholds
    # The PROPRIETARY TRAP: exact thresholds matter
    # ──────────────────────────────────────────────────────────────────────────
    try:
        opp_beads = compass_data.get("opportunities", [])
        
        # Known vectors and their expected cl values based on cosine similarity with H_unit
        # vec_003 Meridian: dir=[0.85, 0.78, 0.52] -> cos_sim computed below
        # vec_004 NeuroScale: dir=[0.55, 0.80, 0.25]
        # vec_005 TechCorp: dir=[-0.30, -0.20, 0.60], weight=8

        meridian_dir = normalize([0.85, 0.78, 0.52])
        neuroscale_dir = normalize([0.55, 0.80, 0.25])
        techcorp_dir = normalize([-0.30, -0.20, 0.60])

        meridian_cos = cosine_similarity(meridian_dir, H_unit)
        neuroscale_cos = cosine_similarity(neuroscale_dir, H_unit)
        techcorp_cos = cosine_similarity(techcorp_dir, H_unit)

        # Expected cl values:
        # Meridian: cos ~0.99+ -> "hot" (≥0.85) -- actually high similarity
        # NeuroScale: need to compute
        # TechCorp: cos with H will be negative/low, weight=8 >=6, match <0.6 -> "tension"

        # Compute exact expected values
        def expected_cl(cos_sim, weight, status=""):
            if status in ["submitted", "applied", "active"]:
                return "active"
            if cos_sim >= 0.85:
                return "hot"
            if cos_sim < 0.6 and weight >= 6:
                return "tension"
            if 0.65 <= cos_sim < 0.85:
                return "warm"
            if 0.5 <= cos_sim < 0.65:
                return "cool"
            if cos_sim < 0.5:
                return "avoid"
            return "warm"

        exp_meridian = expected_cl(meridian_cos, 8, "considering")
        exp_neuroscale = expected_cl(neuroscale_cos, 7, "considering")
        exp_techcorp = expected_cl(techcorp_cos, 8, "received")

        cl_results = {}
        for bead in opp_beads:
            what = bead.get("what", "").lower()
            cl = bead.get("cl", "")
            if "meridian" in what:
                cl_results["meridian"] = cl
            elif "neuroscale" in what or "neuro" in what:
                cl_results["neuroscale"] = cl
            elif "techcorp" in what or "staff" in what:
                cl_results["techcorp"] = cl

        meridian_ok = cl_results.get("meridian") == exp_meridian
        neuroscale_ok = cl_results.get("neuroscale") == exp_neuroscale
        techcorp_ok = cl_results.get("techcorp") == exp_techcorp

        correct_count = sum([meridian_ok, neuroscale_ok, techcorp_ok])
        check6_passed = correct_count >= 2  # At least 2/3 must be correct

        checks.append({
            "name": "cl_color_classification_correct",
            "passed": check6_passed,
            "detail": (
                f"Meridian cos={meridian_cos:.3f} expected={exp_meridian} got={cl_results.get('meridian','?')} ok={meridian_ok} | "
                f"NeuroScale cos={neuroscale_cos:.3f} expected={exp_neuroscale} got={cl_results.get('neuroscale','?')} ok={neuroscale_ok} | "
                f"TechCorp cos={techcorp_cos:.3f} expected={exp_techcorp} got={cl_results.get('techcorp','?')} ok={techcorp_ok}"
            )
        })
    except Exception as e:
        checks.append({
            "name": "cl_color_classification_correct",
            "passed": False,
            "detail": f"Error checking cl classification: {e}"
        })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 7: clusters list in compass_data.json has correct format
    # Each cluster must have: name (UPPERCASE), m (float), color (hex)
    # ──────────────────────────────────────────────────────────────────────────
    try:
        clusters = compass_data.get("clusters", [])
        valid_cluster_count = 0
        cluster_details = []
        
        DEFAULT_COLORS = {
            "AUTONOMY-FIRST": "#00c8ff",
            "DEPTH-BUILDER": "#a855f7",
            "INNOVATION-DRIVE": "#00ff88"
        }
        
        for c in clusters:
            name = c.get("name", "")
            m_val = c.get("m")
            color = c.get("color", "")
            
            name_uppercase = name == name.upper() and len(name) > 0
            m_is_float = isinstance(m_val, (int, float))
            color_is_hex = bool(re.match(r'^#[0-9a-fA-F]{6}$', str(color)))
            
            if name_uppercase and m_is_float and color_is_hex:
                valid_cluster_count += 1
                cluster_details.append(f"{name}:{color}:m={m_val}")
        
        check7_passed = valid_cluster_count >= 1
        checks.append({
            "name": "clusters_format_correct",
            "passed": check7_passed,
            "detail": f"{valid_cluster_count} valid clusters: {cluster_details}"
        })
    except Exception as e:
        checks.append({
            "name": "clusters_format_correct",
            "passed": False,
            "detail": f"Error checking clusters: {e}"
        })

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 8: match field present on opportunity beads with correct cosine value
    # ──────────────────────────────────────────────────────────────────────────
    try:
        opp_beads = compass_data.get("opportunities", [])
        match_correct_count = 0
        match_details = []
        
        for bead in opp_beads:
            what = bead.get("what", "").lower()
            match_val = bead.get("match")
            dir_val = bead.get("dir")
            
            if match_val is None:
                match_details.append(f"{what}: missing match field")
                continue
            
            if dir_val and len(dir_val) == 3:
                expected_match = cosine_similarity(normalize(dir_val), H_unit)
                tolerance = 0.05
                if abs(match_val - expected_match) <= tolerance:
                    match_correct_count += 1
                    match_details.append(f"{what}: match={match_val:.3f} (expected≈{expected_match:.3f}) ✓")
                else:
                    match_details.append(f"{what}: match={match_val:.3f} expected≈{expected_match:.3f} ✗")
        
        check8_passed = match_correct_count >= 2
        checks.append({
            "name": "opportunity_match_scores_correct",
            "passed": check8_passed,
            "detail": f"{match_correct_count} correct match scores. Details: {match_details[:4]}"
        })
    except Exception as e:
        checks.append({
            "name": "opportunity_match_scores_correct",
            "passed": False,
            "detail": f"Error checking match scores: {e}"
        })

    # ──────────────────────────────────────────────────────────────────────────
    # FINAL SCORE
    # ──────────────────────────────────────────────────────────────────────────
    weights = {
        "vault_vector_notes_complete": 2.0,
        "vectors_json_populated": 1.5,
        "magnetization_json_fresh": 1.5,
        "compass_data_json_structure": 2.0,
        "identity_opportunity_split": 1.5,
        "cl_color_classification_correct": 3.0,   # The proprietary trap
        "clusters_format_correct": 1.5,
        "opportunity_match_scores_correct": 2.0,
    }

    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)
    passed = score >= 0.70

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))