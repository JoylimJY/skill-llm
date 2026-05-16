import sys
import json
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # --- CHECK 1: File exists at workspace root ---
    def check_file_exists():
        candidates = list(Path(workspace).glob("analysis_brief.json"))
        if not candidates:
            return False, "analysis_brief.json not found in workspace root"
        if len(candidates) > 1:
            return False, f"Multiple files found: {candidates}"
        return True, f"Found at {candidates[0]}"

    c1 = run_check("file_exists_at_root", check_file_exists)
    checks.append(c1)

    if not c1["passed"]:
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    # Load the file
    brief_path = list(Path(workspace).glob("analysis_brief.json"))[0]
    try:
        with open(brief_path) as f:
            brief = json.load(f)
    except Exception as e:
        checks.append({"name": "file_parseable_json", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result))
        return

    checks.append({"name": "file_parseable_json", "passed": True, "detail": "Valid JSON"})

    # --- CHECK 2: Top-level keys ---
    def check_top_level_keys():
        has_a = "problem_a" in brief
        has_b = "problem_b" in brief
        if has_a and has_b:
            return True, "Both 'problem_a' and 'problem_b' keys present"
        missing = []
        if not has_a: missing.append("problem_a")
        if not has_b: missing.append("problem_b")
        return False, f"Missing keys: {missing}"

    checks.append(run_check("top_level_keys", check_top_level_keys))

    # --- CHECK 3: problem_a uses diagnostic profile ---
    def check_problem_a_profile():
        pa = brief.get("problem_a", {})
        # The JSON output from ideonomy should have a 'profile' field or similar
        # Check various possible structures
        pa_str = json.dumps(pa).lower()
        
        # Look for diagnostic profile indicator
        if "diagnostic" in pa_str:
            return True, "Found 'diagnostic' profile in problem_a"
        
        # Also acceptable: the output structure itself (lenses array etc.)
        return False, f"Could not find 'diagnostic' profile indicator in problem_a. Keys found: {list(pa.keys()) if isinstance(pa, dict) else type(pa)}"

    checks.append(run_check("problem_a_diagnostic_profile", check_problem_a_profile))

    # --- CHECK 4: problem_a contains CAUSES and ANALOGIES divisions ---
    def check_problem_a_divisions():
        pa = brief.get("problem_a", {})
        pa_str = json.dumps(pa).upper()
        has_causes = "CAUSES" in pa_str
        has_analogies = "ANALOGIES" in pa_str
        if has_causes and has_analogies:
            return True, "Found CAUSES and ANALOGIES division names in problem_a"
        missing = []
        if not has_causes: missing.append("CAUSES")
        if not has_analogies: missing.append("ANALOGIES")
        return False, f"Missing divisions in problem_a: {missing}"

    checks.append(run_check("problem_a_has_required_divisions", check_problem_a_divisions))

    # --- CHECK 5: problem_a has exactly 3 lenses ---
    def check_problem_a_lens_count():
        pa = brief.get("problem_a", {})
        # ideonomy --json output structure: look for 'lenses' array
        lenses = None
        if isinstance(pa, dict):
            if "lenses" in pa:
                lenses = pa["lenses"]
            # Sometimes nested
            for key in pa:
                if isinstance(pa[key], dict) and "lenses" in pa[key]:
                    lenses = pa[key]["lenses"]
                    break
                if isinstance(pa[key], list):
                    # Could be the lenses array directly
                    lenses = pa[key]
                    break
        
        if lenses is None:
            # Try to count division occurrences as fallback
            pa_str = json.dumps(pa).upper()
            # Count how many known division names appear
            all_divisions = [
                "ANALOGIES", "CAUSES", "LIMITS", "OPPOSITES", "INVERSIONS",
                "COMPONENTS", "PROPERTIES", "RELATIONS", "EFFECTS", "FUNCTIONS",
                "PROCESSES", "STATES", "STRUCTURES", "PATTERNS", "CONTEXTS",
                "CONSTRAINTS", "RESOURCES", "AGENTS", "GOALS", "MEASURES",
                "ERRORS", "ALTERNATIVES", "COMBINATIONS", "SEQUENCES",
                "HIERARCHIES", "TRANSFORMATIONS", "MAPPINGS", "PRINCIPLES"
            ]
            found = [d for d in all_divisions if d in pa_str]
            count = len(found)
            if count == 3:
                return True, f"Found exactly 3 divisions in problem_a: {found}"
            return False, f"Expected 3 lens/division entries in problem_a, found ~{count}: {found}"
        
        count = len(lenses)
        if count == 3:
            return True, f"problem_a has exactly 3 lenses"
        return False, f"problem_a has {count} lenses, expected 3"

    checks.append(run_check("problem_a_exactly_3_lenses", check_problem_a_lens_count))

    # --- CHECK 6: problem_b uses strategic profile ---
    def check_problem_b_profile():
        pb = brief.get("problem_b", {})
        pb_str = json.dumps(pb).lower()
        if "strategic" in pb_str or "strategy" in pb_str:
            return True, "Found 'strategic' profile in problem_b"
        return False, f"Could not find 'strategic' profile indicator in problem_b. Keys: {list(pb.keys()) if isinstance(pb, dict) else type(pb)}"

    checks.append(run_check("problem_b_strategic_profile", check_problem_b_profile))

    # --- CHECK 7: problem_b has exactly 4 lenses ---
    def check_problem_b_lens_count():
        pb = brief.get("problem_b", {})
        lenses = None
        if isinstance(pb, dict):
            if "lenses" in pb:
                lenses = pb["lenses"]
            for key in pb:
                if isinstance(pb[key], dict) and "lenses" in pb[key]:
                    lenses = pb[key]["lenses"]
                    break
                if isinstance(pb[key], list):
                    lenses = pb[key]
                    break
        
        if lenses is None:
            pa_str = json.dumps(pb).upper()
            all_divisions = [
                "ANALOGIES", "CAUSES", "LIMITS", "OPPOSITES", "INVERSIONS",
                "COMPONENTS", "PROPERTIES", "RELATIONS", "EFFECTS", "FUNCTIONS",
                "PROCESSES", "STATES", "STRUCTURES", "PATTERNS", "CONTEXTS",
                "CONSTRAINTS", "RESOURCES", "AGENTS", "GOALS", "MEASURES",
                "ERRORS", "ALTERNATIVES", "COMBINATIONS", "SEQUENCES",
                "HIERARCHIES", "TRANSFORMATIONS", "MAPPINGS", "PRINCIPLES"
            ]
            found = [d for d in all_divisions if d in pa_str]
            count = len(found)
            if count == 4:
                return True, f"Found exactly 4 divisions in problem_b: {found}"
            return False, f"Expected 4 lens/division entries in problem_b, found ~{count}: {found}"
        
        count = len(lenses)
        if count == 4:
            return True, f"problem_b has exactly 4 lenses"
        return False, f"problem_b has {count} lenses, expected 4"

    checks.append(run_check("problem_b_exactly_4_lenses", check_problem_b_lens_count))

    # --- CHECK 8: problem_b output is concise (minimal fields) ---
    def check_problem_b_concise():
        pb = brief.get("problem_b", {})
        pb_str = json.dumps(pb)
        # Concise mode suppresses guiding_questions, cross_domain_sparks, conceptual_palette
        # Check that it's notably shorter / lacks these rich fields
        has_guiding = "guiding_questions" in pb_str.lower() or "guiding" in pb_str.lower()
        has_sparks = "cross_domain" in pb_str.lower() or "sparks" in pb_str.lower()
        has_palette = "conceptual_palette" in pb_str.lower() or "palette" in pb_str.lower()
        
        # Concise mode should NOT have these rich fields
        if not has_guiding and not has_sparks and not has_palette:
            return True, "problem_b appears to be in concise mode (no guiding_questions/sparks/palette fields)"
        
        rich_fields = []
        if has_guiding: rich_fields.append("guiding_questions")
        if has_sparks: rich_fields.append("cross_domain_sparks")
        if has_palette: rich_fields.append("conceptual_palette")
        
        # Soft fail: concise mode might still include some fields depending on version
        # Be lenient — if it has 4 lenses and strategic profile, partial credit
        return False, f"problem_b may not be in concise mode — found rich fields: {rich_fields}"

    checks.append(run_check("problem_b_is_concise_mode", check_problem_b_concise))

    # --- CHECK 9: Both outputs are actual ideonomy JSON (not hand-crafted stubs) ---
    def check_outputs_are_real_ideonomy():
        pa = brief.get("problem_a", {})
        pb = brief.get("problem_b", {})
        
        pa_str = json.dumps(pa)
        pb_str = json.dumps(pb)
        
        # Real ideonomy output should contain reasoning-related content
        # and not be trivially empty or fake
        min_len_a = len(pa_str) > 200
        min_len_b = len(pb_str) > 100
        
        # Check for some ideonomy-characteristic fields
        ideonomy_markers = ["division", "lens", "core_question", "theme", "question", "reasoning"]
        found_a = any(m in pa_str.lower() for m in ideonomy_markers)
        found_b = any(m in pb_str.lower() for m in ideonomy_markers)
        
        if min_len_a and min_len_b and (found_a or found_b):
            return True, f"Both outputs appear to be real ideonomy output (len_a={len(pa_str)}, len_b={len(pb_str)})"
        
        issues = []
        if not min_len_a: issues.append(f"problem_a too short ({len(pa_str)} chars)")
        if not min_len_b: issues.append(f"problem_b too short ({len(pb_str)} chars)")
        if not found_a: issues.append("problem_a lacks ideonomy marker fields")
        if not found_b: issues.append("problem_b lacks ideonomy marker fields")
        return False, f"Outputs may not be real ideonomy output: {issues}"

    checks.append(run_check("outputs_are_real_ideonomy_json", check_outputs_are_real_ideonomy))

    # --- SCORING ---
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 7  # Must pass at least 7/9 checks

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()