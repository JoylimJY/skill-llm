import sys
import json
import re
from pathlib import Path

def count_words(text):
    return len(text.split())

def find_positioning_file(workspace):
    candidates = list(Path(workspace).rglob("positioning.md"))
    if not candidates:
        return None
    return candidates[0]

def run_checks(workspace):
    checks = []
    
    # --- Find the file ---
    pos_file = find_positioning_file(workspace)
    
    if pos_file is None:
        checks.append({"name": "file_exists", "passed": False, "detail": "positioning.md not found anywhere in workspace"})
        return checks, 0.0
    
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {pos_file}"})
    
    try:
        content = pos_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"})
        return checks, 0.0
    
    checks.append({"name": "file_readable", "passed": True, "detail": f"File read successfully, {len(content)} chars"})
    
    content_lower = content.lower()

    # -----------------------------------------------------------------------
    # CHECK 1: Positioning Statement uses the exact template structure
    # Must contain: For ... who ..., [Product] is a ... that ...
    # Unlike ..., we ...
    # -----------------------------------------------------------------------
    ps_pattern = re.compile(
        r'\bfor\b.{5,200}\bwho\b.{5,200}\bis\s+a\b.{5,200}\bthat\b.{5,200}\bunlike\b.{5,200}\bwe\b',
        re.IGNORECASE | re.DOTALL
    )
    ps_match = ps_pattern.search(content)
    checks.append({
        "name": "positioning_statement_template",
        "passed": bool(ps_match),
        "detail": "Positioning statement must follow 'For [X] who [Y], [Product] is a [cat] that [benefit]. Unlike [alt], we [diff].' template" if not ps_match else "Template structure found"
    })

    # -----------------------------------------------------------------------
    # CHECK 2: One-Liner present and <= 10 words
    # Look for a section labeled "One-Liner" or "one liner" with actual content
    # -----------------------------------------------------------------------
    one_liner_section = re.search(
        r'one[-\s]liner[:\s*#]*\n+([^\n]+)',
        content,
        re.IGNORECASE
    )
    one_liner_passed = False
    one_liner_detail = "One-Liner section not found"
    if one_liner_section:
        one_liner_text = one_liner_section.group(1).strip().lstrip('*#>-').strip()
        word_count = count_words(one_liner_text)
        if word_count <= 10 and word_count >= 3:
            one_liner_passed = True
            one_liner_detail = f"One-liner found: '{one_liner_text}' ({word_count} words)"
        else:
            one_liner_detail = f"One-liner has {word_count} words (must be <= 10): '{one_liner_text}'"
    checks.append({
        "name": "one_liner_10_words_or_less",
        "passed": one_liner_passed,
        "detail": one_liner_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 3: Elevator Pitch present and approximately 75 words (60-90 range)
    # -----------------------------------------------------------------------
    elevator_section = re.search(
        r'elevator\s+pitch[:\s*#]*\n+([\s\S]{50,600}?)(?=\n#{1,3}\s|\n\*\*[A-Z]|\Z)',
        content,
        re.IGNORECASE
    )
    elevator_passed = False
    elevator_detail = "Elevator Pitch section not found"
    if elevator_section:
        elevator_text = elevator_section.group(1).strip()
        word_count = count_words(elevator_text)
        if 50 <= word_count <= 110:
            elevator_passed = True
            elevator_detail = f"Elevator pitch is {word_count} words (target ~75)"
        else:
            elevator_detail = f"Elevator pitch is {word_count} words, expected ~75 (50-110 acceptable range)"
    checks.append({
        "name": "elevator_pitch_approx_75_words",
        "passed": elevator_passed,
        "detail": elevator_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 4: Key Differentiators - max 3 bullet points
    # -----------------------------------------------------------------------
    diff_section = re.search(
        r'key\s+differentiator[s]?[:\s*#]*\n+([\s\S]{10,600}?)(?=\n#{1,3}\s|\n\*\*[A-Z]|\Z)',
        content,
        re.IGNORECASE
    )
    diff_passed = False
    diff_detail = "Key Differentiators section not found"
    if diff_section:
        diff_text = diff_section.group(1).strip()
        bullets = re.findall(r'^\s*[-*•]\s+.+', diff_text, re.MULTILINE)
        if 1 <= len(bullets) <= 3:
            diff_passed = True
            diff_detail = f"Found {len(bullets)} bullet(s) - within max 3 limit"
        else:
            diff_detail = f"Found {len(bullets)} bullets in Key Differentiators (must be 1-3 max)"
    checks.append({
        "name": "key_differentiators_max_3_bullets",
        "passed": diff_passed,
        "detail": diff_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 5: Target Customer Profile - must be 1 paragraph (prose, not bullets)
    # -----------------------------------------------------------------------
    tcp_section = re.search(
        r'target\s+customer\s+profile[:\s*#]*\n+([\s\S]{30,800}?)(?=\n#{1,3}\s|\n\*\*[A-Z]|\Z)',
        content,
        re.IGNORECASE
    )
    tcp_passed = False
    tcp_detail = "Target Customer Profile section not found"
    if tcp_section:
        tcp_text = tcp_section.group(1).strip()
        # Should be prose paragraph, not primarily bullets
        bullets_in_tcp = re.findall(r'^\s*[-*•]\s+.+', tcp_text, re.MULTILINE)
        paragraphs = [p.strip() for p in tcp_text.split('\n\n') if p.strip()]
        word_count = count_words(tcp_text)
        if word_count >= 30 and len(bullets_in_tcp) <= 1:
            tcp_passed = True
            tcp_detail = f"Target Customer Profile is a paragraph with {word_count} words"
        else:
            tcp_detail = f"Target Customer Profile appears to be bullet list or too short ({len(bullets_in_tcp)} bullets, {word_count} words) - must be 1 prose paragraph"
    checks.append({
        "name": "target_customer_profile_one_paragraph",
        "passed": tcp_passed,
        "detail": tcp_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 6: Competitive Position - exactly 1 sentence "vs" statement
    # -----------------------------------------------------------------------
    comp_pos_section = re.search(
        r'competitive\s+position[:\s*#]*\n+([\s\S]{10,400}?)(?=\n#{1,3}\s|\n\*\*[A-Z]|\Z)',
        content,
        re.IGNORECASE
    )
    comp_pos_passed = False
    comp_pos_detail = "Competitive Position section not found"
    if comp_pos_section:
        comp_text = comp_pos_section.group(1).strip()
        # Count sentences (roughly)
        sentences = re.split(r'[.!?]+', comp_text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        if len(sentences) == 1:
            comp_pos_passed = True
            comp_pos_detail = f"Competitive Position is 1 sentence: '{comp_text}'"
        else:
            comp_pos_detail = f"Competitive Position has {len(sentences)} sentences (must be exactly 1)"
    checks.append({
        "name": "competitive_position_one_sentence",
        "passed": comp_pos_passed,
        "detail": comp_pos_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 7: Competitive Mapping Table present with required rows
    # The "Vs Framework" table must include "They win when" row
    # -----------------------------------------------------------------------
    has_table = bool(re.search(r'\|.+\|.+\|', content))
    has_they_win = bool(re.search(r'they\s+win\s+when', content_lower))
    has_best_for = bool(re.search(r'best\s+for', content_lower))
    has_approach = bool(re.search(r'approach', content_lower))
    has_tradeoff = bool(re.search(r'tradeoff|trade.off', content_lower))
    
    table_passed = has_table and has_they_win and has_best_for
    checks.append({
        "name": "competitive_mapping_table_with_they_win_when",
        "passed": table_passed,
        "detail": f"Table: {has_table}, 'They win when': {has_they_win}, 'Best for': {has_best_for}, 'Approach': {has_approach}, 'Tradeoff': {has_tradeoff}"
    })

    # -----------------------------------------------------------------------
    # CHECK 8: Content is relevant to veterinary/PawManager context
    # Must reference vet/veterinary/clinic/pawmanager
    # -----------------------------------------------------------------------
    vet_keywords = ['vet', 'veterinar', 'clinic', 'pawmanager', 'animal', 'paw manager']
    has_vet_context = any(kw in content_lower for kw in vet_keywords)
    checks.append({
        "name": "content_relevant_to_veterinary_domain",
        "passed": has_vet_context,
        "detail": "Content must reference veterinary/clinic context from product brief" if not has_vet_context else "Veterinary domain context confirmed"
    })

    # -----------------------------------------------------------------------
    # CHECK 9: All 6 required output sections are present
    # -----------------------------------------------------------------------
    required_sections = [
        ("positioning_statement", r'positioning\s+statement'),
        ("one_liner", r'one[-\s]liner'),
        ("elevator_pitch", r'elevator\s+pitch'),
        ("key_differentiators", r'key\s+differentiator'),
        ("target_customer_profile", r'target\s+customer\s+profile'),
        ("competitive_position", r'competitive\s+position'),
    ]
    
    missing_sections = []
    for section_name, pattern in required_sections:
        if not re.search(pattern, content, re.IGNORECASE):
            missing_sections.append(section_name)
    
    all_sections_passed = len(missing_sections) == 0
    checks.append({
        "name": "all_6_required_sections_present",
        "passed": all_sections_passed,
        "detail": f"Missing sections: {missing_sections}" if missing_sections else "All 6 required sections found"
    })

    # -----------------------------------------------------------------------
    # CHECK 10: "Only we" or unfair advantage mentioned somewhere
    # -----------------------------------------------------------------------
    has_only_we = bool(re.search(r'only\s+we|unfair\s+advantage|uniquely|only\s+pawmanager', content_lower))
    checks.append({
        "name": "differentiator_only_we_statement",
        "passed": has_only_we,
        "detail": "Must articulate 'only we' or unique advantage" if not has_only_we else "Unique differentiator/only-we statement found"
    })

    # --- Calculate score ---
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)
    
    return checks, score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        checks = [{"name": "eval_error", "passed": False, "detail": str(e)}]
        score = 0.0
    
    passed = score >= 0.75  # Must pass at least 75% of checks
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()