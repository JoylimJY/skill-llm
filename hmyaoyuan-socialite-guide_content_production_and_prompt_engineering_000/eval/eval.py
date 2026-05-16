import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Locate the output file ────────────────────────────────────────────────
    candidates = list(workspace_path.rglob("socialite_prompts.json"))
    if not candidates:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "socialite_prompts.json not found anywhere in workspace."})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    output_file = candidates[0]
    checks.append({"name": "output_file_exists", "passed": True,
                    "detail": f"Found at {output_file}"})

    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False,
                        "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "json_parseable", "passed": True, "detail": "Valid JSON."})

    # ── Structural check: must be a list or dict with 3 entries ──────────────
    prompts = None
    if isinstance(data, list) and len(data) >= 3:
        prompts = data
    elif isinstance(data, dict):
        # Allow {"prompts": [...]} or {"CB-2026-001": {...}, ...}
        for key in ["prompts", "results", "entries", "shoots"]:
            if key in data and isinstance(data[key], list) and len(data[key]) >= 3:
                prompts = data[key]
                break
        if prompts is None:
            # Try dict-of-dicts keyed by brief_id
            values = list(data.values())
            if len(values) >= 3 and all(isinstance(v, dict) for v in values):
                prompts = values

    if prompts is None or len(prompts) < 3:
        checks.append({"name": "three_prompts_present", "passed": False,
                        "detail": f"Expected 3 prompt entries, got structure: {type(data).__name__}"})
        return {"passed": False, "score": 0.1, "checks": checks}

    checks.append({"name": "three_prompts_present", "passed": True,
                    "detail": f"Found {len(prompts)} prompt entries."})

    # ── Helper: extract all text from an entry ────────────────────────────────
    def extract_text(entry) -> str:
        if isinstance(entry, str):
            return entry.lower()
        if isinstance(entry, dict):
            return " ".join(str(v) for v in entry.values()).lower()
        return str(entry).lower()

    # ── Helper: find entry by brief_id or by index ────────────────────────────
    def find_entry(brief_id: str, index: int):
        # Try to find by brief_id field
        for p in prompts:
            if isinstance(p, dict):
                for v in p.values():
                    if isinstance(v, str) and brief_id.lower() in v.lower():
                        return p
        # Fallback: by index
        if index < len(prompts):
            return prompts[index]
        return None

    # ════════════════════════════════════════════════════════════════════════
    # CHECK SET A: CB-2026-001 (Lumière Collective — Relaxed Chic / 松弛感)
    # ════════════════════════════════════════════════════════════════════════
    e1 = find_entry("CB-2026-001", 0)
    t1 = extract_text(e1) if e1 is not None else ""

    # A1: Style classification — must be "Relaxed Chic" or 松弛感 equivalent
    a1_passed = bool(
        re.search(r"relax(ed)?\s*chic|松弛感|effortless\s*elegance", t1, re.I)
    )
    checks.append({"name": "A1_CB001_style_classification",
                    "passed": a1_passed,
                    "detail": f"Entry 1 must identify 'Relaxed Chic/松弛感'. Found: '{t1[:200]}'"})

    # A2: Must begin with masterpiece, best quality (anywhere in prompt field)
    def find_prompt_string(entry) -> str:
        """Extract the actual AI prompt string from an entry."""
        if isinstance(entry, str):
            return entry.lower()
        if isinstance(entry, dict):
            for key in ["prompt", "ai_prompt", "generated_prompt", "text", "content", "output"]:
                if key in entry and isinstance(entry[key], str):
                    return entry[key].lower()
            # Return all concatenated
            return " ".join(str(v) for v in entry.values()).lower()
        return str(entry).lower()

    p1 = find_prompt_string(e1) if e1 is not None else ""
    a2_passed = bool(re.search(r"masterpiece[,\s]+best\s+quality", p1, re.I))
    checks.append({"name": "A2_CB001_quality_tags",
                    "passed": a2_passed,
                    "detail": f"Prompt must start with 'masterpiece, best quality'. Prompt excerpt: '{p1[:200]}'"})

    # A3: Must include Relaxed Chic formula keywords
    a3_keywords = ["soft natural lighting", "pastel color palette", "cozy cafe", "home setting", "relaxed pose"]
    a3_found = [kw for kw in a3_keywords if kw.lower() in p1]
    a3_passed = len(a3_found) >= 3
    checks.append({"name": "A3_CB001_relaxed_chic_formula_keywords",
                    "passed": a3_passed,
                    "detail": f"Need ≥3 of {a3_keywords}. Found: {a3_found}"})

    # A4: Lighting — must use soft natural lighting (NOT butterfly/Rembrandt/cinematic)
    a4_wrong = bool(re.search(r"butterfly\s+lighting|rembrandt\s+lighting|cinematic\s+lighting", p1, re.I))
    a4_correct = "soft natural lighting" in p1
    a4_passed = a4_correct and not a4_wrong
    checks.append({"name": "A4_CB001_correct_lighting_no_studio",
                    "passed": a4_passed,
                    "detail": f"Must use 'soft natural lighting', must NOT use studio/cinematic lighting. correct={a4_correct}, wrong_found={a4_wrong}"})

    # A5: Pose — holding coffee or sitting/relaxed pose (from skill taxonomy)
    a5_passed = bool(re.search(r"holding\s+coffee|relaxed\s+pose|leaning\s+on\s+armrest|crossed\s+legs", p1, re.I))
    checks.append({"name": "A5_CB001_pose_keyword",
                    "passed": a5_passed,
                    "detail": f"Must include a skill-defined sitting/relaxed pose keyword. Prompt: '{p1[:200]}'"})

    # ════════════════════════════════════════════════════════════════════════
    # CHECK SET B: CB-2026-002 (Sovereign & Co. — Expensive/Noble / 贵气感)
    # ════════════════════════════════════════════════════════════════════════
    e2 = find_entry("CB-2026-002", 1)
    t2 = extract_text(e2) if e2 is not None else ""
    p2 = find_prompt_string(e2) if e2 is not None else ""

    # B1: Style classification — Expensive/Noble or 贵气感
    b1_passed = bool(
        re.search(r"expensive|noble|贵气感|old\s*money|haute\s*couture", t2, re.I)
    )
    checks.append({"name": "B1_CB002_style_classification",
                    "passed": b1_passed,
                    "detail": f"Entry 2 must identify 'Expensive/Noble/贵气感/Old Money'. Found: '{t2[:200]}'"})

    # B2: Quality tags
    b2_passed = bool(re.search(r"masterpiece[,\s]+best\s+quality", p2, re.I))
    checks.append({"name": "B2_CB002_quality_tags",
                    "passed": b2_passed,
                    "detail": f"Prompt must include 'masterpiece, best quality'. Excerpt: '{p2[:200]}'"})

    # B3: Must include Noble formula keywords
    b3_keywords = ["golden accents", "flawless makeup", "luxury hotel lobby", "elegant jewelry"]
    b3_found = [kw for kw in b3_keywords if kw.lower() in p2]
    b3_passed = len(b3_found) >= 3
    checks.append({"name": "B3_CB002_noble_formula_keywords",
                    "passed": b3_passed,
                    "detail": f"Need ≥3 of {b3_keywords}. Found: {b3_found}"})

    # B4: CRITICAL PROPRIETARY TRAP — "most flattering face-sculpting lighting" = butterfly lighting
    # Brief says "face-sculpting" -> skill doc says butterfly lighting is FOR FACE
    b4_passed = bool(re.search(r"butterfly\s+lighting", p2, re.I))
    checks.append({"name": "B4_CB002_butterfly_lighting_for_face",
                    "passed": b4_passed,
                    "detail": f"Brief requests face-sculpting lighting. Skill doc specifies 'butterfly lighting' (for face). Must appear in prompt. Found: {'yes' if b4_passed else 'no'}"})

    # B5: Must NOT use soft natural lighting (wrong style)
    b5_wrong = bool(re.search(r"soft\s+natural\s+lighting", p2, re.I))
    b5_passed = not b5_wrong
    checks.append({"name": "B5_CB002_no_relaxed_lighting",
                    "passed": b5_passed,
                    "detail": f"Noble style must not use 'soft natural lighting' (that's Relaxed Chic). Found wrong kw: {b5_wrong}"})

    # B6: Standing pose with authority (S-curve or weight on one leg)
    b6_passed = bool(re.search(r"s-curve\s+pose|weight\s+on\s+one\s+leg|side\s+profile|looking\s+back\s+over\s+shoulder", p2, re.I))
    checks.append({"name": "B6_CB002_standing_pose",
                    "passed": b6_passed,
                    "detail": f"Must include a standing pose keyword from skill taxonomy. Prompt: '{p2[:200]}'"})

    # ════════════════════════════════════════════════════════════════════════
    # CHECK SET C: CB-2026-003 (Maison Éclat — Refined Detail / 精致感)
    # ════════════════════════════════════════════════════════════════════════
    e3 = find_entry("CB-2026-003", 2)
    t3 = extract_text(e3) if e3 is not None else ""
    p3 = find_prompt_string(e3) if e3 is not None else ""

    # C1: Style classification — Refined Detail or 精致感
    c1_passed = bool(
        re.search(r"refined\s*(detail|elegance)|精致感|magazine\s*editorial", t3, re.I)
    )
    checks.append({"name": "C1_CB003_style_classification",
                    "passed": c1_passed,
                    "detail": f"Entry 3 must identify 'Refined Detail/精致感'. Found: '{t3[:200]}'"})

    # C2: Quality tags — Refined Detail requires ultra-detailed per bible doc
    c2_passed = bool(re.search(r"masterpiece[,\s]+best\s+quality", p3, re.I)) and \
                bool(re.search(r"ultra-?detailed", p3, re.I))
    checks.append({"name": "C2_CB003_quality_tags_with_ultradetailed",
                    "passed": c2_passed,
                    "detail": f"Refined Detail requires 'masterpiece, best quality' AND 'ultra-detailed'. Prompt: '{p3[:200]}'"})

    # C3: Must include Refined Detail formula keywords
    c3_keywords = ["symmetrical composition", "detail-focused", "soft shadows", "silk", "tweed"]
    c3_found = [kw for kw in c3_keywords if kw.lower() in p3]
    c3_passed = len(c3_found) >= 3
    checks.append({"name": "C3_CB003_refined_detail_formula_keywords",
                    "passed": c3_passed,
                    "detail": f"Need ≥3 of {c3_keywords}. Found: {c3_found}"})

    # C4: Must NOT use film grain (tech doc says film grain conflicts with ultra-detailed)
    c4_wrong = bool(re.search(r"film\s+grain", p3, re.I))
    c4_passed = not c4_wrong
    checks.append({"name": "C4_CB003_no_film_grain_conflict",
                    "passed": c4_passed,
                    "detail": f"Tech doc states: 'film grain and ultra-detailed cannot be used together'. film_grain_found: {c4_wrong}"})

    # C5: Lighting — soft shadows → studio softbox or soft lighting (NOT cinematic moody)
    c5_correct = bool(re.search(r"soft\s+shadows|softbox|soft\s+lighting", p3, re.I))
    c5_wrong_cinematic = bool(re.search(r"moody\s+shadows|cinematic\s+lighting|rembrandt\s+lighting", p3, re.I))
    c5_passed = c5_correct and not c5_wrong_cinematic
    checks.append({"name": "C5_CB003_correct_soft_lighting",
                    "passed": c5_passed,
                    "detail": f"Must have soft/softbox lighting, must NOT have moody/cinematic. correct={c5_correct}, wrong={c5_wrong_cinematic}"})

    # C6: Sitting pose (subject is sitting in brief)
    c6_passed = bool(re.search(r"crossed\s+legs|elegant\s+sitting|leaning\s+on\s+armrest|hand\s+on\s+cheek", p3, re.I))
    checks.append({"name": "C6_CB003_sitting_pose",
                    "passed": c6_passed,
                    "detail": f"Must include a sitting pose keyword from skill taxonomy. Prompt: '{p3[:200]}'"})

    # ════════════════════════════════════════════════════════════════════════
    # CHECK SET D: Prompt Construction Order (global formula compliance)
    # ════════════════════════════════════════════════════════════════════════
    # Check that quality tags appear BEFORE style keywords in at least 2 of 3 prompts
    def order_check(prompt_str: str) -> bool:
        """Quality tags must appear before style keywords."""
        if not prompt_str:
            return False
        quality_match = re.search(r"masterpiece", prompt_str, re.I)
        style_matches = [
            re.search(r"relaxed\s+chic|old\s+money|refined\s+elegance|magazine\s+editorial|effortless\s+elegance|haute\s+couture", prompt_str, re.I)
        ]
        if not quality_match:
            return False
        style_match = next((m for m in style_matches if m), None)
        if style_match:
            return quality_match.start() < style_match.start()
        return True  # Style keyword not present but quality tag is — acceptable

    order_results = [order_check(p) for p in [p1, p2, p3]]
    d1_passed = sum(order_results) >= 2
    checks.append({"name": "D1_prompt_construction_order",
                    "passed": d1_passed,
                    "detail": f"Quality tags must appear before style keywords. Per-prompt results: {order_results}"})

    # ── Score calculation ─────────────────────────────────────────────────────
    all_checks_names_weights = {
        "output_file_exists": 2,
        "json_parseable": 2,
        "three_prompts_present": 2,
        "A1_CB001_style_classification": 3,
        "A2_CB001_quality_tags": 4,
        "A3_CB001_relaxed_chic_formula_keywords": 5,
        "A4_CB001_correct_lighting_no_studio": 5,
        "A5_CB001_pose_keyword": 3,
        "B1_CB002_style_classification": 3,
        "B2_CB002_quality_tags": 4,
        "B3_CB002_noble_formula_keywords": 5,
        "B4_CB002_butterfly_lighting_for_face": 8,  # Proprietary trap — high weight
        "B5_CB002_no_relaxed_lighting": 4,
        "B6_CB002_standing_pose": 3,
        "C1_CB003_style_classification": 3,
        "C2_CB003_quality_tags_with_ultradetailed": 5,
        "C3_CB003_refined_detail_formula_keywords": 5,
        "C4_CB003_no_film_grain_conflict": 6,  # Proprietary trap — high weight
        "C5_CB003_correct_soft_lighting": 5,
        "C6_CB003_sitting_pose": 3,
        "D1_prompt_construction_order": 4,
    }

    total_weight = sum(all_checks_names_weights.values())
    earned_weight = 0
    for check in checks:
        w = all_checks_names_weights.get(check["name"], 0)
        if check["passed"]:
            earned_weight += w

    score = round(earned_weight / total_weight, 4)
    passed = score >= 0.75

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))