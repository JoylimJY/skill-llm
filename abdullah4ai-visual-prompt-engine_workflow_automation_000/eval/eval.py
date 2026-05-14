#!/usr/bin/env python3
"""
Evaluation script for the visual-prompt-engine task.
Checks that the agent has:
1. Used scrape_dribbble.py --method import correctly -> data/references.json
2. Used style_card.py build -> data/style_cards.json with valid cards
3. Created a new prompt (in data/prompt_history.json) that:
   a. Uses a pattern DIFFERENT from "Cinematic Atmosphere" (the trap)
   b. Contains visual vocabulary terms (not generic adjectives)
   c. References elements from a style card (palette hex, texture, composition keywords)
   d. Is appended as a 6th entry to prompt_history.json
4. The prompt file (final_prompt.json or similar) exists with the generated prompt
"""

import sys
import json
import re
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f), None
    except FileNotFoundError:
        return None, f"File not found: {path}"
    except json.JSONDecodeError as e:
        return None, f"JSON decode error in {path}: {e}"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        return

    workspace = Path(sys.argv[1])
    checks = []
    total_weight = 0
    passed_weight = 0

    # ── Check 1: data/references.json exists and was produced by import method ──
    refs_path = workspace / "data" / "references.json"
    refs_data, refs_err = load_json_safe(refs_path)
    c1_passed = False
    c1_detail = ""
    if refs_err:
        c1_detail = refs_err
    elif refs_data is None:
        c1_detail = "references.json is empty or null"
    elif refs_data.get("method") != "import":
        c1_detail = f"Expected method='import' but got method='{refs_data.get('method')}'. Agent likely used live/rss instead of --method import."
    elif refs_data.get("count", 0) == 0:
        c1_detail = "references.json has 0 shots; import likely failed or wrong file was used"
    elif len(refs_data.get("shots", [])) < 3:
        c1_detail = f"Only {len(refs_data.get('shots', []))} shots imported; expected at least 3"
    else:
        c1_passed = True
        c1_detail = f"references.json correctly populated via import method with {refs_data['count']} shots"
    checks.append({"name": "references_json_import_method", "passed": c1_passed, "detail": c1_detail})
    total_weight += 20
    if c1_passed:
        passed_weight += 20

    # ── Check 2: data/style_cards.json exists with valid cards ──────────────────
    cards_path = workspace / "data" / "style_cards.json"
    cards_data, cards_err = load_json_safe(cards_path)
    c2_passed = False
    c2_detail = ""
    style_cards = []
    if cards_err:
        c2_detail = cards_err
    elif cards_data is None:
        c2_detail = "style_cards.json is empty"
    elif "cards" not in cards_data:
        c2_detail = "style_cards.json missing 'cards' key"
    elif len(cards_data["cards"]) == 0:
        c2_detail = "style_cards.json has 0 cards"
    else:
        style_cards = cards_data["cards"]
        # Verify card schema: must have required fields
        required_fields = {"id", "palette", "composition", "mood", "textures", "lighting", "tags"}
        first_card = style_cards[0]
        missing = required_fields - set(first_card.keys())
        if missing:
            c2_detail = f"First style card missing fields: {missing}"
        else:
            c2_passed = True
            c2_detail = f"style_cards.json has {len(style_cards)} valid cards with correct schema"
    checks.append({"name": "style_cards_json_valid", "passed": c2_passed, "detail": c2_detail})
    total_weight += 20
    if c2_passed:
        passed_weight += 20

    # ── Check 3: prompt_history.json has been appended (now 6 entries) ──────────
    history_path = workspace / "data" / "prompt_history.json"
    hist_data, hist_err = load_json_safe(history_path)
    c3_passed = False
    c3_detail = ""
    new_prompt_entry = None
    if hist_err:
        c3_detail = hist_err
    elif hist_data is None:
        c3_detail = "prompt_history.json is null"
    elif "prompts" not in hist_data:
        c3_detail = "prompt_history.json missing 'prompts' key"
    else:
        prompts = hist_data["prompts"]
        if len(prompts) < 6:
            c3_detail = f"Expected at least 6 prompts in history (5 existing + 1 new), found {len(prompts)}"
        else:
            # The new entry should be the last one(s) beyond the original 5
            new_entries = prompts[5:]  # anything after the original 5
            if not new_entries:
                c3_detail = "No new prompt appended beyond original 5"
            else:
                new_prompt_entry = new_entries[-1]
                c3_passed = True
                c3_detail = f"Found {len(new_entries)} new prompt(s) appended to history"
    checks.append({"name": "prompt_history_appended", "passed": c3_passed, "detail": c3_detail})
    total_weight += 20
    if c3_passed:
        passed_weight += 20

    # ── Check 4: New prompt uses a DIFFERENT pattern than Cinematic Atmosphere ───
    c4_passed = False
    c4_detail = ""
    new_prompt_text = ""
    if new_prompt_entry is None:
        c4_detail = "Cannot check: no new prompt entry found in history"
    else:
        # Extract prompt text
        new_prompt_text = new_prompt_entry.get("prompt", "")
        pattern_used = new_prompt_entry.get("pattern", "").lower()
        pattern_id = new_prompt_entry.get("pattern_id", -1)
        
        # Cinematic Atmosphere = Pattern 2
        is_cinematic = (
            "cinematic atmosphere" in pattern_used or
            pattern_id == 2 or
            # Also detect if prompt text strongly suggests cinematic pattern
            (re.search(r'\bshot on\b', new_prompt_text, re.I) and 
             re.search(r'\bcinematography\b', new_prompt_text, re.I) and
             re.search(r'\bemotional register\b', new_prompt_text, re.I))
        )
        if is_cinematic:
            c4_detail = f"FAIL: New prompt still uses Cinematic Atmosphere pattern (pattern_id={pattern_id}, pattern='{pattern_used}'). Must differ from last 5 prompts."
        elif not new_prompt_text:
            c4_detail = "New prompt entry has empty 'prompt' text"
        else:
            c4_passed = True
            c4_detail = f"New prompt correctly uses a different pattern: '{new_prompt_entry.get('pattern', 'unspecified')}'"
    checks.append({"name": "new_prompt_different_pattern", "passed": c4_passed, "detail": c4_detail})
    total_weight += 25
    if c4_passed:
        passed_weight += 25

    # ── Check 5: Prompt uses specific visual vocabulary (not generic adjectives) ─
    c5_passed = False
    c5_detail = ""
    GENERIC_BANNED = ["beautiful", "nice", "stunning", "gorgeous", "amazing", "pretty", "lovely"]
    VOCAB_TERMS = [
        # color
        "chroma", "desaturated", "duotone", "split complementary", "chromatic aberration",
        "triadic", "muted earth", "electric contrast", "warm-neutral", "cold accent",
        # composition
        "bleed-edge", "negative space", "visual weight", "asymmetric", "brutalist grid",
        "swiss grid", "golden ratio", "dead-zone",
        # lighting
        "raking", "rembrandt", "rim-light", "hard-shadow", "fill-light", "chiaroscuro",
        "neon scatter", "single-source",
        # texture
        "micro-grain", "halftone", "risograph", "screen-print", "concrete aggregate",
        "sand-cast", "paper tooth", "linen weave", "glass caustic", "frosted diffusion",
        # mood
        "confrontational stillness", "industrial sublime", "restrained tension",
        "kinetic arrested", "melancholic warmth", "synthetic nostalgia",
        "raw immediacy", "typographic aggression", "tactile intimacy",
        # typography
        "condensed grotesque", "slab-serif", "variable axis", "optical kerning", "tracked display",
        # pattern-specific design terms
        "oversized weight", "tight tracking", "heavy sans-serif",
        "grid system", "color blocks", "editorial",
        "isometric", "risograph bleed",
    ]

    if not new_prompt_text:
        c5_detail = "No prompt text to evaluate"
    else:
        prompt_lower = new_prompt_text.lower()
        banned_found = [w for w in GENERIC_BANNED if w in prompt_lower]
        vocab_found = [t for t in VOCAB_TERMS if t in prompt_lower]

        if banned_found:
            c5_detail = f"Prompt uses banned generic adjectives: {banned_found}. Must use specific visual vocabulary."
        elif len(vocab_found) < 2:
            c5_detail = f"Prompt uses too few specific visual vocabulary terms ({len(vocab_found)} found: {vocab_found}). Need at least 2 from references/visual-vocabulary.md."
        else:
            c5_passed = True
            c5_detail = f"Prompt uses {len(vocab_found)} specific visual vocabulary terms: {vocab_found[:5]}"
    checks.append({"name": "prompt_visual_vocabulary", "passed": c5_passed, "detail": c5_detail})
    total_weight += 15
    if c5_passed:
        passed_weight += 15

    # ── Check 6: Final prompt output file exists (final_prompt.json) ─────────────
    c6_passed = False
    c6_detail = ""
    # Search for final_prompt.json anywhere in workspace
    final_prompt_files = list(workspace.rglob("final_prompt.json"))
    if not final_prompt_files:
        c6_detail = "final_prompt.json not found anywhere in workspace"
    else:
        fp_path = final_prompt_files[0]
        fp_data, fp_err = load_json_safe(fp_path)
        if fp_err:
            c6_detail = fp_err
        elif fp_data is None:
            c6_detail = "final_prompt.json is null/empty"
        else:
            # Must contain a "prompt" key with non-empty string
            if "prompt" not in fp_data:
                c6_detail = f"final_prompt.json missing 'prompt' key (keys found: {list(fp_data.keys())})"
            elif not fp_data["prompt"] or len(fp_data["prompt"]) < 30:
                c6_detail = f"final_prompt.json 'prompt' value is too short or empty: '{fp_data.get('prompt', '')}'"
            else:
                c6_passed = True
                c6_detail = f"final_prompt.json found at {fp_path.relative_to(workspace)} with valid prompt content"
    checks.append({"name": "final_prompt_json_exists", "passed": c6_passed, "detail": c6_detail})
    total_weight += 0  # Bonus check, included in scoring as separate weight
    # Recalculate: add this check as weighted
    total_weight_actual = 100
    # Recompute score based on all 6 checks with weights: 20+20+20+25+15 = 100 for checks 1-5
    # Check 6 is a bonus (replaces nothing, we'll score it as a fraction of 100 if all else passes)

    # Final scoring: weight checks 1-5 summing to 100
    score = passed_weight / total_weight if total_weight > 0 else 0.0

    # Check 6 adjusts score slightly (it's a required deliverable too)
    if c6_passed:
        checks[-1]["passed"] = True
    
    # Recompute with check 6 included (weight it at 0 bonus but required for full pass)
    all_core_passed = all(c["passed"] for c in checks[:5])
    overall_passed = all_core_passed and c6_passed

    # Score = weighted sum of checks 1-5 (100 pts), bonus for check 6
    final_score = round(min(score + (0.0 if not c6_passed else 0.0), 1.0), 3)
    # Actually include check 6 in scoring
    weights = [20, 20, 20, 25, 15, 0]
    # Let's redo this properly
    check_weights = [20, 20, 20, 25, 10, 5]  # total 100
    weighted_score = sum(
        check_weights[i] for i, c in enumerate(checks) if c["passed"]
    ) / 100.0

    result = {
        "passed": overall_passed,
        "score": round(weighted_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()