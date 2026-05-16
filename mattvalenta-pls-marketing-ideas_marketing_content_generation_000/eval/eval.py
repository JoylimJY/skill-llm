import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []

    # --- Locate the output file ---
    target_files = list(Path(workspace_dir).rglob("campaign_brief.md"))
    if not target_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "campaign_brief.md not found anywhere in workspace."}]
        }

    fpath = target_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {fpath}"})

    try:
        content = fpath.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_readable", "passed": False, "detail": str(e)}]
        }

    content_lower = content.lower()

    # --- CHECK 1: Two distinct campaign concepts present ---
    # Must have at least 2 campaign sections. Look for campaign template structure.
    # SKILL.md defines: Challenge, Controversy, Behind-the-Scenes, Social Proof, Educational
    campaign_template_keywords = [
        "challenge", "controversy", "behind-the-scenes", "behind the scenes",
        "social proof", "educational"
    ]
    found_templates = [kw for kw in campaign_template_keywords if kw in content_lower]
    has_two_campaigns = len(found_templates) >= 2
    checks.append({
        "name": "two_distinct_campaign_templates",
        "passed": has_two_campaigns,
        "detail": f"Found campaign types: {found_templates}. Need at least 2 distinct template types from SKILL.md."
    })

    # --- CHECK 2: Challenge Campaign uses [N]-Day Challenge naming format ---
    # SKILL.md: Name: [N]-Day Challenge (e.g. "30-Day Challenge")
    challenge_name_pattern = re.search(r'\d+\s*[-–]\s*day\s+challenge', content_lower)
    has_challenge_name = challenge_name_pattern is not None
    checks.append({
        "name": "challenge_campaign_nday_format",
        "passed": has_challenge_name,
        "detail": f"Expected '[N]-Day Challenge' naming (e.g., '30-Day Challenge'). Match: {challenge_name_pattern}"
    })

    # --- CHECK 3: Each campaign has Hook and Angle fields ---
    # SKILL.md campaign templates always define: Hook and Angle
    hook_count = len(re.findall(r'\bhook\b', content_lower))
    angle_count = len(re.findall(r'\bangle\b', content_lower))
    # Need at least 2 Hooks and 2 Angles (one per campaign)
    has_hook_and_angle = hook_count >= 2 and angle_count >= 2
    checks.append({
        "name": "hook_and_angle_per_campaign",
        "passed": has_hook_and_angle,
        "detail": f"Found {hook_count} 'Hook' and {angle_count} 'Angle' references. Need >= 2 each for two campaigns."
    })

    # --- CHECK 4: At least one recognized SKILL.md framework referenced ---
    # SKILL.md frameworks: PAS, AIDA, Jobs To Be Done, StoryBrand
    frameworks = {
        "PAS": bool(re.search(r'\bpas\b', content_lower)),
        "AIDA": bool(re.search(r'\baida\b', content_lower)),
        "Jobs To Be Done": bool(re.search(r'jobs\s+to\s+be\s+done', content_lower)),
        "StoryBrand": bool(re.search(r'storybrand', content_lower)),
    }
    found_frameworks = [k for k, v in frameworks.items() if v]
    has_framework = len(found_frameworks) >= 1
    checks.append({
        "name": "framework_referenced",
        "passed": has_framework,
        "detail": f"Frameworks found: {found_frameworks}. Must reference at least one of: PAS, AIDA, Jobs To Be Done, StoryBrand."
    })

    # --- CHECK 5: Trigger category explicitly identified ---
    # SKILL.md: Product feature/launch, Pain point, Customer feedback
    triggers = {
        "Product feature/launch": bool(re.search(r'product\s+(feature|launch)', content_lower)),
        "Pain point": bool(re.search(r'pain\s+point', content_lower)),
        "Customer feedback": bool(re.search(r'customer\s+feedback', content_lower)),
    }
    found_triggers = [k for k, v in triggers.items() if v]
    has_trigger = len(found_triggers) >= 1
    checks.append({
        "name": "trigger_category_identified",
        "passed": has_trigger,
        "detail": f"Trigger categories found: {found_triggers}. Must identify at least one of: Product feature/launch, Pain point, Customer feedback."
    })

    # --- CHECK 6: Idea Generation Checklist present with all 5 items ---
    # SKILL.md checklist items (exact):
    checklist_items = [
        r'validates?\s+pain\s+point',
        r'differentiat\w*\s+from\s+competition',
        r'aligns?\s+with\s+brand\s+voice',
        r'clear\s+cta',
        r'measurable\s+success\s+potential',
    ]
    checklist_labels = [
        "Validates pain point",
        "Differentiates from competition",
        "Aligns with brand voice",
        "Clear CTA",
        "Measurable success potential",
    ]
    found_checklist = []
    missing_checklist = []
    for item_re, label in zip(checklist_items, checklist_labels):
        if re.search(item_re, content_lower):
            found_checklist.append(label)
        else:
            missing_checklist.append(label)
    all_checklist_present = len(found_checklist) == 5
    checks.append({
        "name": "idea_generation_checklist_all_5_items",
        "passed": all_checklist_present,
        "detail": f"Found {len(found_checklist)}/5 checklist items. Missing: {missing_checklist}"
    })

    # --- CHECK 7: Hook Templates from SKILL.md used (Pattern Interrupts or Curiosity Gaps) ---
    # Pattern Interrupts: "Most X are doing this wrong", "I'll probably get hate", "This cost us $X to learn"
    # Curiosity Gaps: "The one change that...", "Why [X] are failing..."
    hook_template_patterns = [
        r'doing\s+this\s+wrong',
        r"i'?ll\s+probably\s+get\s+hate",
        r'cost\s+us\s+\$[\d,]+\s+to\s+learn',
        r'the\s+one\s+change\s+that',
        r'why\s+\w+\s+are\s+failing',
        r'pattern\s+interrupt',
        r'curiosity\s+gap',
    ]
    found_hook_templates = [p for p in hook_template_patterns if re.search(p, content_lower)]
    has_hook_template = len(found_hook_templates) >= 1
    checks.append({
        "name": "hook_template_pattern_used",
        "passed": has_hook_template,
        "detail": f"Found hook template patterns: {found_hook_templates}. Must use at least one Pattern Interrupt or Curiosity Gap from SKILL.md."
    })

    # --- CHECK 8: Challenge Campaign has a "Can we [achieve result] in [timeframe]?" hook format ---
    # SKILL.md: Hook: "Can we [achieve result] in [timeframe]?"
    can_we_pattern = re.search(r'can\s+we\s+.{5,50}\s+in\s+\d+', content_lower)
    has_can_we = can_we_pattern is not None
    checks.append({
        "name": "challenge_campaign_can_we_hook",
        "passed": has_can_we,
        "detail": f"Expected 'Can we [achieve result] in [timeframe]?' hook. Match: {can_we_pattern}"
    })

    # --- Scoring ---
    passed_checks = [c for c in checks if c["passed"]]
    total_checks = len(checks)
    score = len(passed_checks) / total_checks

    # Must pass critical checks to pass overall
    critical_checks = [
        "two_distinct_campaign_templates",
        "idea_generation_checklist_all_5_items",
        "hook_and_angle_per_campaign",
        "framework_referenced",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))