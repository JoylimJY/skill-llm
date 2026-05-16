import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    home = Path.home()
    base = home / "meal-planner"

    # ── Helper ──────────────────────────────────────────────────────────────
    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1: Find the weekly plan file
    # Must be weeks/2026-W15.md (the task specifies week 15 of 2026)
    # ══════════════════════════════════════════════════════════════════════════
    weeks_dir = base / "weeks"
    week_files = list(weeks_dir.glob("*.md")) if weeks_dir.exists() else []

    # Accept 2026-W15.md
    target_week_file = weeks_dir / "2026-W15.md"
    week_content = ""
    week_found = False

    try:
        if target_week_file.exists():
            week_content = target_week_file.read_text()
            week_found = True
            check("week_file_correct_name", True,
                  f"Found correctly named week file: {target_week_file.name}")
        else:
            # Check if any week file exists at all
            if week_files:
                names = [f.name for f in week_files]
                check("week_file_correct_name", False,
                      f"Expected weeks/2026-W15.md but found: {names}. "
                      "File naming must follow YYYY-WXX format.")
            else:
                check("week_file_correct_name", False,
                      "No week files found in weeks/ directory.")
    except Exception as e:
        check("week_file_correct_name", False, f"Error reading week file: {e}")

    # ── 1a. Week file has required header ────────────────────────────────────
    try:
        has_week_header = bool(re.search(r'#\s*Week\s+2026-W15', week_content))
        check("week_file_has_header",
              has_week_header,
              "Week file must have '# Week 2026-W15' header" if not has_week_header
              else "Week header present.")
    except Exception as e:
        check("week_file_has_header", False, f"Error: {e}")

    # ── 1b. Overview section with budget target ───────────────────────────────
    try:
        has_overview = "## Overview" in week_content
        has_budget = bool(re.search(r'[Bb]udget\s+target\s*[:=]\s*\$\d+', week_content))
        ok = has_overview and has_budget
        check("week_has_overview_with_budget", ok,
              "Week file must have ## Overview section with budget target ($120 per memory.md)"
              if not ok else "Overview section with budget found.")
    except Exception as e:
        check("week_has_overview_with_budget", False, f"Error: {e}")

    # ── 1c. All 7 days present ────────────────────────────────────────────────
    try:
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        missing_days = [d for d in days if f"## {d}" not in week_content]
        ok = len(missing_days) == 0
        check("week_has_all_7_days", ok,
              f"Missing days: {missing_days}" if not ok
              else "All 7 days present.")
    except Exception as e:
        check("week_has_all_7_days", False, f"Error: {e}")

    # ── 1d. Meals have Prep times ─────────────────────────────────────────────
    try:
        prep_count = len(re.findall(r'Prep:\s*\d+\s*min', week_content))
        ok = prep_count >= 7  # at least 7 meal entries with prep time
        check("week_meals_have_prep_times", ok,
              f"Only {prep_count} meals have 'Prep: X min' annotations. Need at least 7."
              if not ok else f"Found {prep_count} meals with prep times.")
    except Exception as e:
        check("week_meals_have_prep_times", False, f"Error: {e}")

    # ── 1e. Batch Prep (Sunday) section with checkboxes ──────────────────────
    try:
        has_batch = bool(re.search(r'##\s*Batch\s*Prep\s*\(?Sunday\)?', week_content, re.IGNORECASE))
        has_checkboxes = bool(re.search(r'- \[[ x]\]', week_content))
        ok = has_batch and has_checkboxes
        check("week_has_batch_prep_section", ok,
              "Week file must include '## Batch Prep (Sunday)' section with checkbox items"
              if not ok else "Batch Prep (Sunday) section with checkboxes found.")
    except Exception as e:
        check("week_has_batch_prep_section", False, f"Error: {e}")

    # ── 1f. Shopping Needed section ───────────────────────────────────────────
    try:
        has_shopping_section = bool(re.search(r'##\s*Shopping\s*Needed', week_content, re.IGNORECASE))
        check("week_has_shopping_needed_section", has_shopping_section,
              "Week file must include '## Shopping Needed' section"
              if not has_shopping_section else "Shopping Needed section present.")
    except Exception as e:
        check("week_has_shopping_needed_section", False, f"Error: {e}")

    # ── 1g. Flex slot(s) present ──────────────────────────────────────────────
    try:
        flex_indicators = [
            r'[Ff]lex', r'[Ee]at\s+out', r'[Tt]akeout', r'[Ss]pontane',
            r'[Ff]ree\s+meal', r'[Ee]ating\s+out', r'[Ll]eftovers?\s+or',
            r'TBD', r'tbd'
        ]
        has_flex = any(re.search(p, week_content) for p in flex_indicators)
        check("week_has_flex_slot", has_flex,
              "Week plan must leave 1-2 flex slots for spontaneity or eating out (SKILL.md §3)"
              if not has_flex else "Flex slot found in week plan.")
    except Exception as e:
        check("week_has_flex_slot", False, f"Error: {e}")

    # ── 1h. No tree nuts in any meal ─────────────────────────────────────────
    try:
        nut_pattern = r'\b(walnut|cashew|almond|pistachio|pecan|hazelnut|macadamia|pine\s*nut|nut\s*butter|almond\s*milk|cashew\s*cream)\b'
        nut_matches = re.findall(nut_pattern, week_content, re.IGNORECASE)
        # almond milk is dairy-free but still tree nut — must be excluded
        ok = len(nut_matches) == 0
        check("week_no_tree_nuts_alex_allergy", ok,
              f"CRITICAL: Week plan contains tree nuts (life-threatening for Alex): {set(nut_matches)}"
              if not ok else "No tree nuts found — Alex's allergy respected.")
    except Exception as e:
        check("week_no_tree_nuts_alex_allergy", False, f"Error: {e}")

    # ── 1i. No heavy dairy (milk/cream/ice cream) for Jordan ─────────────────
    try:
        heavy_dairy = r'\b(cow\s*milk|whole\s*milk|heavy\s*cream|whipping\s*cream|ice\s*cream|sour\s*cream|cream\s*sauce|alfredo|bechamel)\b'
        dairy_matches = re.findall(heavy_dairy, week_content, re.IGNORECASE)
        ok = len(dairy_matches) == 0
        check("week_no_heavy_dairy_jordan", ok,
              f"Week plan contains heavy dairy (Jordan's intolerance): {set(dairy_matches)}"
              if not ok else "No heavy dairy — Jordan's intolerance respected.")
    except Exception as e:
        check("week_no_heavy_dairy_jordan", False, f"Error: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2: Find the shopping list file
    # Must be in shopping/ directory, named YYYY-MM-DD.md
    # ══════════════════════════════════════════════════════════════════════════
    shopping_dir = base / "shopping"
    shop_content = ""
    shop_found = False

    # Exclude the old file from gen_inputs
    old_shopping = "2025-03-24.md"
    try:
        new_shop_files = [
            f for f in shopping_dir.glob("*.md")
            if f.name != old_shopping
        ] if shopping_dir.exists() else []

        if new_shop_files:
            shop_file = new_shop_files[0]  # take the newest
            shop_content = shop_file.read_text()
            shop_found = True
            # Validate naming: must match YYYY-MM-DD.md
            name_ok = bool(re.match(r'^\d{4}-\d{2}-\d{2}\.md$', shop_file.name))
            check("shopping_file_correct_name", name_ok,
                  f"Shopping file '{shop_file.name}' must follow YYYY-MM-DD.md format"
                  if not name_ok else f"Shopping file correctly named: {shop_file.name}")
        else:
            check("shopping_file_correct_name", False,
                  "No new shopping list file found in shopping/ directory.")
    except Exception as e:
        check("shopping_file_correct_name", False, f"Error finding shopping file: {e}")

    # ── 2a. Shopping list header format ──────────────────────────────────────
    try:
        has_shop_header = bool(re.search(
            r'##\s*Shopping\s*List\s*[—\-–]\s*\d{4}-\d{2}-\d{2}',
            shop_content
        ))
        check("shopping_has_correct_header", has_shop_header,
              "Shopping list must start with '## Shopping List — YYYY-MM-DD' header"
              if not has_shop_header else "Shopping list header format correct.")
    except Exception as e:
        check("shopping_has_correct_header", False, f"Error: {e}")

    # ── 2b. Has categorized sections (Produce, Proteins, etc.) ───────────────
    try:
        categories = [r'###\s*Produce', r'###\s*Proteins?', r'###\s*Pantry']
        found_cats = [bool(re.search(c, shop_content, re.IGNORECASE)) for c in categories]
        ok = sum(found_cats) >= 2
        check("shopping_has_categorized_sections", ok,
              f"Shopping list needs at least 2 of: Produce, Proteins, Pantry sections. Found: {sum(found_cats)}"
              if not ok else "Shopping list has categorized sections.")
    except Exception as e:
        check("shopping_has_categorized_sections", False, f"Error: {e}")

    # ── 2c. Items use checkbox format ─────────────────────────────────────────
    try:
        checkbox_items = re.findall(r'- \[ \]', shop_content)
        ok = len(checkbox_items) >= 3
        check("shopping_items_use_checkboxes", ok,
              f"Shopping items must use '- [ ] ...' checkbox format. Found {len(checkbox_items)} items."
              if not ok else f"Found {len(checkbox_items)} checkbox items.")
    except Exception as e:
        check("shopping_items_use_checkboxes", False, f"Error: {e}")

    # ── 2d. Items linked to meals ─────────────────────────────────────────────
    try:
        # Items should have " — Mon/Tue/Wed" style meal linkage
        linked_items = re.findall(
            r'- \[ \].+?—.+?(Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|meal|lunch|dinner|breakfast)',
            shop_content, re.IGNORECASE
        )
        ok = len(linked_items) >= 2
        check("shopping_items_linked_to_meals", ok,
              f"Shopping items must link to specific meals (e.g., '— Mon stir-fry, Wed soup'). Found {len(linked_items)} linked items."
              if not ok else f"Found {len(linked_items)} items linked to meals.")
    except Exception as e:
        check("shopping_items_linked_to_meals", False, f"Error: {e}")

    # ── 2e. Budget estimate present ───────────────────────────────────────────
    try:
        has_budget = bool(re.search(r'\*\*Budget\s+estimate\*\*\s*:\s*\$\d+', shop_content))
        check("shopping_has_budget_estimate", has_budget,
              "Shopping list must include '**Budget estimate:** $XX' line"
              if not has_budget else "Budget estimate found in shopping list.")
    except Exception as e:
        check("shopping_has_budget_estimate", False, f"Error: {e}")

    # ── 2f. Pantry items note to check inventory ──────────────────────────────
    try:
        inventory_awareness = bool(re.search(
            r'(check\s+inventory|already\s+have|in\s+pantry|pantry\s+stock|skip|have\s+enough|in\s+stock|not\s+needed)',
            shop_content, re.IGNORECASE
        ))
        # Also check if pantry section is small (showing they used existing stock)
        pantry_section = re.search(r'###\s*Pantry.*?(?=###|\Z)', shop_content, re.DOTALL | re.IGNORECASE)
        pantry_text = pantry_section.group(0) if pantry_section else ""
        # Staples from pantry that are FULL (rice, pasta, olive oil, cumin) should NOT appear as needed
        # OR if they do appear, they should note "check inventory"
        rice_in_list = bool(re.search(r'- \[ \]\s*[Rr]ice', shop_content))
        pasta_in_list = bool(re.search(r'- \[ \]\s*[Pp]asta\b|[Pp]enne', shop_content))
        olive_oil_in_list = bool(re.search(r'- \[ \]\s*[Oo]live\s+oil', shop_content))
        # These are FULL in pantry — if in list, must say "check inventory" nearby
        unnecessary_items = []
        if rice_in_list and not re.search(r'rice.{0,60}(check|have|full|pantry|skip)', shop_content, re.IGNORECASE):
            unnecessary_items.append("rice (Full in pantry)")
        if pasta_in_list and not re.search(r'pasta.{0,60}(check|have|full|pantry|skip)', shop_content, re.IGNORECASE):
            unnecessary_items.append("pasta (Full in pantry)")
        if olive_oil_in_list and not re.search(r'olive.oil.{0,60}(check|have|full|pantry|skip)', shop_content, re.IGNORECASE):
            unnecessary_items.append("olive oil (Full in pantry)")
        ok = len(unnecessary_items) == 0
        check("shopping_respects_existing_inventory", ok,
              f"Shopping list includes items already FULL in pantry without noting to check inventory: {unnecessary_items}"
              if not ok else "Shopping list respects existing pantry inventory.")
    except Exception as e:
        check("shopping_respects_existing_inventory", False, f"Error: {e}")

    # ── 2g. No tree nuts in shopping list ────────────────────────────────────
    try:
        nut_in_shop = re.findall(
            r'\b(walnut|cashew|almond|pistachio|pecan|hazelnut|macadamia)\b',
            shop_content, re.IGNORECASE
        )
        ok = len(nut_in_shop) == 0
        check("shopping_no_tree_nuts", ok,
              f"CRITICAL: Shopping list includes tree nuts (Alex's allergy): {set(nut_in_shop)}"
              if not ok else "No tree nuts in shopping list.")
    except Exception as e:
        check("shopping_no_tree_nuts", False, f"Error: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3: Grandparent visit handling (April 19-20 is in Week 2026-W15? 
    # The task specifies w/e of April 13-19, 2026 — W16 starts Apr 13.
    # 2026-W15 = Apr 6–12. W16 = Apr 13–19. 
    # The task says "week of April 13" → 2026-W16.
    # But we said "Week 15" in the prompt — let's check agent handled
    # the notes.md grandparent/birthday mention if it applies.
    # Actually we need to re-examine: week 15 of 2026 = Apr 6–12.
    # Jordan's birthday is April 18 (W16). Grandparents come April 19-20 (W16).
    # Week 15 does NOT include those. So we check the agent did NOT falsely add 
    # grandparent vegetarian constraint for W15.
    # Actually, let's just check: if grandparents are in the week plan,
    # vegetarian options should be present.
    # This check is lenient — only penalize if grandparents flagged but no veg meal.
    # ══════════════════════════════════════════════════════════════════════════
    try:
        grandparent_mentioned = bool(re.search(r'grandparent', week_content, re.IGNORECASE))
        if grandparent_mentioned:
            has_veg_meal = bool(re.search(
                r'(vegetarian|vegan|chickpea|pasta|salad|veggie|plant.based)',
                week_content, re.IGNORECASE
            ))
            ok = has_veg_meal
            check("grandparent_vegetarian_if_mentioned", ok,
                  "Grandparents are vegetarian (from notes.md). If they're in the plan, vegetarian meals must be included."
                  if not ok else "Grandparents mentioned with vegetarian accommodation.")
        else:
            # Week 15 doesn't have grandparents — that's fine
            check("grandparent_vegetarian_if_mentioned", True,
                  "Grandparents not mentioned in W15 (correct — they visit W16). No issue.")
    except Exception as e:
        check("grandparent_vegetarian_if_mentioned", False, f"Error: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # SCORE COMPUTATION
    # ══════════════════════════════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    all_passed = passed_count == total

    # Hard-fail conditions: safety-critical checks must pass
    safety_checks = [
        "week_no_tree_nuts_alex_allergy",
        "shopping_no_tree_nuts",
    ]
    for sc in safety_checks:
        match = next((c for c in checks if c["name"] == sc), None)
        if match and not match["passed"]:
            all_passed = False

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else str(Path.home())
    evaluate(workspace)