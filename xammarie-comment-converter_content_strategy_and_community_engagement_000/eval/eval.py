import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    score = 0.0

    # --- Find the output file ---
    output_files = list(Path(workspace_dir).rglob("comment_variants.md")) + \
                   list(Path(workspace_dir).rglob("comment_variants.txt")) + \
                   list(Path(workspace_dir).rglob("comment_variants.json"))

    if not output_files:
        # Also accept any file named with "comment_variants" in the community/responses area
        output_files = list(Path(workspace_dir).rglob("*comment_variants*"))

    if not output_files:
        checks.append({
            "name": "output_file_exists",
            "passed": False,
            "detail": "No file named 'comment_variants.*' found anywhere in workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "output_file_exists",
        "passed": True,
        "detail": f"Found output file: {output_files[0]}"
    })
    score += 0.05

    try:
        content = output_files[0].read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "output_file_readable",
            "passed": False,
            "detail": f"Could not read file: {e}"
        })
        return {"passed": False, "score": score, "checks": checks}

    content_lower = content.lower()

    # --- CHECK 1: All 5 required comment styles are present ---
    required_styles = [
        ("direct answer", r"direct\s*answer"),
        ("checklist response", r"checklist\s*(response)?"),
        ("case response", r"case\s*(response)?"),
        ("nuanced counterpoint", r"nuanced\s*(counterpoint)?"),
        ("cta-light response", r"cta[\s\-]?light\s*(response)?"),
    ]

    all_styles_found = True
    missing_styles = []
    for style_name, pattern in required_styles:
        found = bool(re.search(pattern, content_lower))
        if not found:
            all_styles_found = False
            missing_styles.append(style_name)

    checks.append({
        "name": "all_5_comment_styles_present",
        "passed": all_styles_found,
        "detail": f"Missing styles: {missing_styles}" if missing_styles else "All 5 styles found."
    })
    if all_styles_found:
        score += 0.20

    # --- CHECK 2: Each variant has the 3 required sub-fields ---
    # Required: Goal, Draft comment, Why it should work
    has_goal = bool(re.search(r"\bgoal\b", content_lower))
    has_draft = bool(re.search(r"\bdraft\s*(comment)?\b", content_lower))
    has_why = bool(re.search(r"\bwhy\s+it\s+should\s+work\b", content_lower))

    three_fields_present = has_goal and has_draft and has_why
    checks.append({
        "name": "three_sub_fields_per_variant",
        "passed": three_fields_present,
        "detail": (
            f"Goal: {has_goal}, Draft comment: {has_draft}, Why it should work: {has_why}. "
            "All three sub-fields (Goal, Draft comment, Why it should work in this thread) must appear."
        )
    })
    if three_fields_present:
        score += 0.20

    # --- CHECK 3: First comment (direct answer or first variant) has NO hard CTA / no link leading ---
    # Find the first variant block. Look for patterns of direct sell, "check out", "visit our", "sign up"
    # Strategy: extract content before the second major style header
    style_headers = [m.start() for m in re.finditer(
        r"(direct\s*answer|checklist\s*response|case\s*response|nuanced\s*counterpoint|cta[\s\-]?light)",
        content_lower
    )]

    first_variant_text = ""
    if len(style_headers) >= 2:
        first_variant_text = content_lower[style_headers[0]:style_headers[1]]
    elif len(style_headers) == 1:
        first_variant_text = content_lower[style_headers[0]:style_headers[0]+800]
    else:
        first_variant_text = content_lower[:800]

    hard_sell_patterns = [
        r"check\s+out\s+(our|my|pipelineiq)",
        r"visit\s+(our|my)\s+site",
        r"sign\s+up",
        r"try\s+(our|pipelineiq)",
        r"https?://",
        r"click\s+here",
        r"buy\s+(now|today)",
        r"free\s+trial",
    ]
    first_comment_clean = not any(re.search(p, first_variant_text) for p in hard_sell_patterns)

    checks.append({
        "name": "first_variant_pure_value_no_hard_cta",
        "passed": first_comment_clean,
        "detail": (
            "First comment variant must be pure value with no hard sell, links, or sign-up CTAs. "
            + ("PASS: No hard sell detected in first variant." if first_comment_clean
               else "FAIL: Hard sell or link detected in first variant.")
        )
    })
    if first_comment_clean:
        score += 0.15

    # --- CHECK 4: Specific numbers/examples used (not vague) ---
    # Must include actual numbers from inputs or specific percentages/timeframes
    number_patterns = [
        r"\b\d+\s*(min(utes?)?|%|seconds?|hours?|engineers?|tests?|ms|deployments?)\b",
        r"\b\d+[\-–]\d+\s*(min(utes?)?|%)\b",
    ]
    has_specifics = any(re.search(p, content_lower) for p in number_patterns)

    checks.append({
        "name": "specific_numbers_and_examples",
        "passed": has_specifics,
        "detail": (
            "Comments must include specific numbers, benchmarks, or examples (e.g., '8-12 min', '47 deployments', '60%'). "
            + ("PASS: Numeric specifics found." if has_specifics else "FAIL: No numeric specifics detected.")
        )
    })
    if has_specifics:
        score += 0.10

    # --- CHECK 5: Subreddit vibe matching — technical language for r/devops ---
    # Should mention technical terms relevant to the thread
    technical_terms = [
        r"\bpipeline\b",
        r"\bci(/cd)?\b",
        r"\btest\s*(suite|split|impact|flak)",
        r"\bmonorepo\b",
        r"\bgithub\s*actions\b",
        r"\bparallel(ism|ize)?\b",
        r"\bflak(y|iness)\b",
        r"\bcache\b",
        r"\brunner\b",
    ]
    tech_term_count = sum(1 for p in technical_terms if re.search(p, content_lower))
    is_technical = tech_term_count >= 3

    checks.append({
        "name": "subreddit_vibe_technical_language",
        "passed": is_technical,
        "detail": (
            f"Thread is r/devops — responses must use technical CI/CD vocabulary. "
            f"Found {tech_term_count}/9 expected technical terms. Minimum 3 required."
        )
    })
    if is_technical:
        score += 0.10

    # --- CHECK 6: No AI clichés or corporate tone ---
    ai_cliche_patterns = [
        r"\bgreat\s+question\b",
        r"\bI\s+hope\s+this\s+helps\b",
        r"\bfeel\s+free\s+to\b",
        r"\bcertainly\b",
        r"\babsolutely\b",
        r"\bof\s+course\b",
        r"\bpleasure\b",
        r"\bI'd\s+be\s+happy\s+to\b",
        r"\bas\s+an\s+ai\b",
        r"\bI\s+understand\s+your\s+(concern|question|need)\b",
        r"\bthank\s+you\s+for\s+(your\s+question|sharing|asking)\b",
        r"\bin\s+conclusion\b",
        r"\bto\s+summarize\b",
        r"\bsynergy\b",
        r"\bleverage\b",
        r"\bseamless(ly)?\b",
        r"\brobust\s+solution\b",
        r"\bholistic\b",
    ]
    cliche_hits = [p for p in ai_cliche_patterns if re.search(p, content_lower)]
    no_cliches = len(cliche_hits) <= 1  # allow at most 1 borderline hit

    checks.append({
        "name": "no_ai_cliches_or_corporate_tone",
        "passed": no_cliches,
        "detail": (
            f"Found {len(cliche_hits)} AI/corporate clichés: {cliche_hits[:5]}. Max 1 allowed."
            if not no_cliches else "PASS: No significant AI clichés detected."
        )
    })
    if no_cliches:
        score += 0.10

    # --- CHECK 7: Checklist variant actually contains a list/steps ---
    checklist_match = re.search(
        r"checklist\s*(response)?(.{0,2000}?)(?=direct\s*answer|case\s*response|nuanced|cta[\s\-]?light|\Z)",
        content_lower, re.DOTALL
    )
    has_checklist_items = False
    if checklist_match:
        checklist_section = checklist_match.group(2)
        # Must have at least 3 list items (numbered or bulleted)
        list_items = re.findall(r"(\n\s*[-*•]\s+|\n\s*\d+[\.\)]\s+)", checklist_section)
        has_checklist_items = len(list_items) >= 3
    else:
        # Try to find numbered/bulleted list anywhere near "checklist"
        checklist_pos = content_lower.find("checklist")
        if checklist_pos != -1:
            nearby = content_lower[checklist_pos:checklist_pos + 1500]
            list_items = re.findall(r"(\n\s*[-*•]\s+|\n\s*\d+[\.\)]\s+)", nearby)
            has_checklist_items = len(list_items) >= 3

    checks.append({
        "name": "checklist_variant_has_actual_steps",
        "passed": has_checklist_items,
        "detail": (
            "Checklist response variant must include at least 3 bulleted/numbered steps. "
            + ("PASS: List items found." if has_checklist_items else "FAIL: No list structure found in checklist variant.")
        )
    })
    if has_checklist_items:
        score += 0.10

    # --- FINAL SCORING ---
    # Normalize score to max 1.0
    score = min(round(score, 3), 1.0)

    # Must pass at minimum: file exists, all 5 styles, 3 sub-fields, first variant pure value
    critical_checks = [
        "output_file_exists",
        "all_5_comment_styles_present",
        "three_sub_fields_per_variant",
        "first_variant_pure_value_no_hard_cta",
    ]
    passed_critical = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    overall_passed = passed_critical and score >= 0.55

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation_error", "passed": False, "detail": "No workspace path provided."}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))