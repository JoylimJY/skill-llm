import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    total_score = 0.0
    weight_sum = 0.0

    workspace = Path(workspace_dir)

    # --- Find the target file ---
    candidates = list(workspace.rglob("rawbite_ad_production_plan.md"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} candidate(s): {[str(c) for c in candidates]}"
    })
    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    target = candidates[0]
    try:
        content = target.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"Read {len(content)} characters from {target}"})
    content_lower = content.lower()

    # --- CHECK 1: All 5 required deliverable sections present ---
    # From SKILL.md: 1. Final shot list, 2. Prompt set, 3. Generation and edit log, 4. Final export summary, 5. Next-iteration recommendations
    section_patterns = [
        (r"shot\s*list", "Section 1: Final Shot List"),
        (r"prompt\s*set", "Section 2: Prompt Set"),
        (r"(generation|edit)\s*(and|&)?\s*(edit|generation)?\s*log|generation.*log|edit.*log", "Section 3: Generation and Edit Log"),
        (r"export\s*summary|final\s*export", "Section 4: Final Export Summary"),
        (r"next.{0,15}iteration|next.{0,15}recommendation|improvement|future.{0,15}iteration", "Section 5: Next-Iteration Recommendations"),
    ]
    all_sections_present = True
    for pattern, name in section_patterns:
        found = bool(re.search(pattern, content_lower))
        if not found:
            all_sections_present = False
        checks.append({
            "name": f"deliverable_section_{name.replace(' ', '_').lower()}",
            "passed": found,
            "detail": f"Pattern '{pattern}' {'found' if found else 'NOT found'} in document"
        })

    weight_sections = 2.0
    weight_sum += weight_sections
    sections_score = sum(1 for p, n in section_patterns if re.search(p, content_lower)) / len(section_patterns) * weight_sections
    total_score += sections_score

    # --- CHECK 2: Shot count between 5-9 (fast default: 6) ---
    # Look for numbered shots: "Shot 1", "Shot 2", etc., or "## Shot 1" etc.
    shot_numbers = re.findall(r'\bshot\s*[:#\-]?\s*(\d+)\b', content_lower)
    # Deduplicate and find max shot number referenced
    unique_shot_nums = set(int(n) for n in shot_numbers)
    # Count unique shots
    shot_count = len(unique_shot_nums) if unique_shot_nums else 0
    shot_count_valid = 5 <= shot_count <= 9
    checks.append({
        "name": "shot_count_5_to_9",
        "passed": shot_count_valid,
        "detail": f"Found {shot_count} unique shot numbers (unique: {sorted(unique_shot_nums)}). Required: 5-9."
    })
    weight_shots = 1.5
    weight_sum += weight_shots
    total_score += weight_shots if shot_count_valid else 0.0

    # --- CHECK 3: Each shot has required fields ---
    # Required: shot number, scene goal, subject+environment, camera style, on-screen line/dialogue intent
    shot_field_patterns = [
        (r"scene\s*goal|goal|objective|purpose", "scene_goal field"),
        (r"subject|environment|setting|location", "subject+environment field"),
        (r"camera\s*(style|framing|move|motion|angle)|framing|lens", "camera_style field"),
        (r"dialogue|on.?screen|line|narration|caption|cta|call.?to.?action", "dialogue_or_onscreen_line field"),
    ]
    shot_fields_score = 0
    for pattern, fname in shot_field_patterns:
        found = bool(re.search(pattern, content_lower))
        shot_fields_score += 1 if found else 0
        checks.append({
            "name": f"shot_field_{fname.replace(' ', '_')}",
            "passed": found,
            "detail": f"Shot field pattern '{pattern}' {'found' if found else 'NOT found'}"
        })
    weight_shot_fields = 1.5
    weight_sum += weight_shot_fields
    total_score += (shot_fields_score / len(shot_field_patterns)) * weight_shot_fields

    # --- CHECK 4: Nano Banana prompt pattern compliance ---
    # Required shape: [subject], [action], in [environment], [lighting], [camera framing], [style anchors], ultra-clean composition, ad-grade, no text overlays
    nb_mandatory_phrases = [
        (r"ultra.?clean\s*composition", "ultra-clean composition"),
        (r"ad.?grade", "ad-grade"),
        (r"no\s*text\s*overlays", "no text overlays"),
    ]
    nb_score = 0
    for pattern, name in nb_mandatory_phrases:
        found = bool(re.search(pattern, content_lower))
        nb_score += 1 if found else 0
        checks.append({
            "name": f"nano_banana_prompt_phrase_{name.replace(' ', '_')}",
            "passed": found,
            "detail": f"Nano Banana required phrase '{name}' {'found' if found else 'NOT found'}"
        })
    weight_nb = 2.0
    weight_sum += weight_nb
    total_score += (nb_score / len(nb_mandatory_phrases)) * weight_nb

    # --- CHECK 5: Kling prompt pattern compliance ---
    # Required shape: "Animate this still with [motion], keep subject identity stable, cinematic realism, [timing], [dialogue/emotion cue], smooth transitions"
    kling_mandatory_phrases = [
        (r"animate\s*this\s*still", "animate this still"),
        (r"keep\s*subject\s*identity\s*stable|subject\s*identity\s*stable", "keep subject identity stable"),
        (r"cinematic\s*realism", "cinematic realism"),
        (r"smooth\s*transitions", "smooth transitions"),
    ]
    kling_score = 0
    for pattern, name in kling_mandatory_phrases:
        found = bool(re.search(pattern, content_lower))
        kling_score += 1 if found else 0
        checks.append({
            "name": f"kling_prompt_phrase_{name.replace(' ', '_')}",
            "passed": found,
            "detail": f"Kling required phrase '{name}' {'found' if found else 'NOT found'}"
        })
    weight_kling = 2.0
    weight_sum += weight_kling
    total_score += (kling_score / len(kling_mandatory_phrases)) * weight_kling

    # --- CHECK 6: Fast defaults respected ---
    # Clip length: 3-4 seconds per clip
    clip_length_patterns = [
        r'\b[34][\s\-]?s(ec(ond)?s?)?\b',   # "3s", "4s", "3 seconds", "4sec"
        r'\b[34]\s*-\s*[34]\s*(sec|s\b)',   # "3-4s", "3-4 seconds"
        r'3[\s\-]4\s*s',
    ]
    clip_len_found = any(re.search(p, content_lower) for p in clip_length_patterns)
    # Also check for "3-4 second" phrasing
    clip_len_found = clip_len_found or bool(re.search(r'3[\s\-]4\s*second', content_lower))
    checks.append({
        "name": "clip_length_3_to_4_seconds",
        "passed": clip_len_found,
        "detail": f"Clip length of 3-4 seconds {'found' if clip_len_found else 'NOT found'} in document"
    })
    weight_defaults = 1.5
    weight_sum += weight_defaults

    # Runtime 20-30 seconds
    runtime_found = bool(re.search(r'(2[0-9]|30)\s*s(ec(ond)?s?)?|20[\s\-]30\s*(sec|s\b|second)', content_lower))
    # Also accept "25 seconds" as explicitly in brief
    runtime_found = runtime_found or bool(re.search(r'25\s*s(ec(ond)?s?)?', content_lower))
    checks.append({
        "name": "runtime_20_to_30_seconds",
        "passed": runtime_found,
        "detail": f"Runtime 20-30s {'found' if runtime_found else 'NOT found'} in document"
    })

    defaults_score = (int(clip_len_found) + int(runtime_found)) / 2
    total_score += defaults_score * weight_defaults

    # --- CHECK 7: Export summary contains required fields ---
    # Required: total clips, credits used + estimated cost, final runtime, export ratio(s), improvement notes
    export_fields = [
        (r"total\s*clips|clip\s*count|clips\s*generated", "total clips"),
        (r"credits|credit\s*cost|credits\s*used", "credits used"),
        (r"(estimated|est\.?)\s*cost|cost\s*estimate|\$\d+", "estimated cost"),
        (r"final\s*runtime|total\s*runtime|run\s*time|runtime", "final runtime"),
        (r"export\s*ratio|aspect\s*ratio|9.?:?.?16|1080|vertical", "export ratio"),
    ]
    export_score = 0
    for pattern, name in export_fields:
        found = bool(re.search(pattern, content_lower))
        export_score += 1 if found else 0
        checks.append({
            "name": f"export_summary_{name.replace(' ', '_')}",
            "passed": found,
            "detail": f"Export summary field '{name}' {'found' if found else 'NOT found'}"
        })
    weight_export = 2.0
    weight_sum += weight_export
    total_score += (export_score / len(export_fields)) * weight_export

    # --- CHECK 8: Budget ceiling respected (80 credits) ---
    budget_mentioned = bool(re.search(r'80\s*credit|credit.*80|budget.*80|80.*budget', content_lower))
    checks.append({
        "name": "budget_ceiling_80_credits_acknowledged",
        "passed": budget_mentioned,
        "detail": f"Budget ceiling of 80 credits {'found' if budget_mentioned else 'NOT found'} in document"
    })
    weight_budget = 1.0
    weight_sum += weight_budget
    total_score += weight_budget if budget_mentioned else 0.0

    # --- CHECK 9: Narrative structure: Hook, Value, CTA ---
    narrative_patterns = [
        (r'\bhook\b', "hook"),
        (r'\bvalue\b|\bvalue\s*demo|\bdemonstration\b', "value demonstration"),
        (r'\bcta\b|\bcall\s*to\s*action\b|\btry\s*rawbite\b', "CTA"),
    ]
    narrative_score = 0
    for pattern, name in narrative_patterns:
        found = bool(re.search(pattern, content_lower))
        narrative_score += 1 if found else 0
        checks.append({
            "name": f"narrative_structure_{name.replace(' ', '_')}",
            "passed": found,
            "detail": f"Narrative element '{name}' {'found' if found else 'NOT found'}"
        })
    weight_narrative = 1.0
    weight_sum += weight_narrative
    total_score += (narrative_score / len(narrative_patterns)) * weight_narrative

    # --- CHECK 10: Variations per shot acknowledged (3 variations per shot = fast default) ---
    variations_found = bool(re.search(r'3\s*variation|variation.*3|var.*3|3.*var', content_lower))
    checks.append({
        "name": "variations_per_shot_3",
        "passed": variations_found,
        "detail": f"3 variations per shot {'found' if variations_found else 'NOT found'} in document"
    })
    weight_variations = 0.5
    weight_sum += weight_variations
    total_score += weight_variations if variations_found else 0.0

    # --- Normalize score to 0-1 ---
    final_score = total_score / weight_sum if weight_sum > 0 else 0.0
    final_score = round(min(max(final_score, 0.0), 1.0), 4)

    # Determine pass: need at least 0.70 and must have all 5 deliverable sections + both Nano Banana AND Kling proprietary phrases
    nb_mandatory_passed = nb_score == len(nb_mandatory_phrases)
    kling_mandatory_passed = kling_score >= 3  # allow 1 miss on kling
    sections_all_passed = all(re.search(p, content_lower) for p, n in section_patterns)
    passed = (final_score >= 0.70 and nb_mandatory_passed and kling_mandatory_passed and sections_all_passed and shot_count_valid)

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))