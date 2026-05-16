import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ── Locate the oral argument script ─────────────────────────────────────
    script_files = list(workspace_path.rglob("oral_argument_script.md"))
    if not script_files:
        add_check("oral_argument_script.md exists", False, "File not found anywhere in workspace.")
    else:
        add_check("oral_argument_script.md exists", True, f"Found at {script_files[0]}")

    script_content = ""
    if script_files:
        try:
            script_content = script_files[0].read_text(encoding="utf-8")
        except Exception as e:
            add_check("oral_argument_script.md readable", False, str(e))

    # ── Locate the question list ─────────────────────────────────────────────
    qlist_files = list(workspace_path.rglob("question_list.md"))
    if not qlist_files:
        add_check("question_list.md exists", False, "File not found anywhere in workspace.")
    else:
        add_check("question_list.md exists", True, f"Found at {qlist_files[0]}")

    qlist_content = ""
    if qlist_files:
        try:
            qlist_content = qlist_files[0].read_text(encoding="utf-8")
        except Exception as e:
            add_check("question_list.md readable", False, str(e))

    sc = script_content.lower()

    # ════════════════════════════════════════════════════════════════════════
    # SCRIPT CHECKS
    # ════════════════════════════════════════════════════════════════════════

    # CHECK 1 – Correct ICC judge title "Your Honor" (not "Your Excellency")
    has_your_honor = bool(re.search(r'\byour\s+honor\b', sc, re.IGNORECASE))
    has_your_excellency = bool(re.search(r'\byour\s+excellency\b', sc, re.IGNORECASE))
    passed_title = has_your_honor and not has_your_excellency
    add_check(
        "Correct ICC judge title ('Your Honor', not 'Your Excellency')",
        passed_title,
        f"Found 'Your Honor': {has_your_honor}; Found 'Your Excellency': {has_your_excellency}"
    )

    # CHECK 2 – No first-person singular pronouns (I, me, my, mine, myself)
    # Exclude "I" when used inside words like "jurisdiction", "identify", etc.
    # We do a word-boundary check on the raw script
    singular_pattern = re.compile(r'\b(I|me|my|mine|myself)\b', re.IGNORECASE)
    # But don't flag "I" inside words — re.compile with \b handles that
    # Actually we want to avoid false positives: search in original script
    singular_hits = singular_pattern.findall(script_content)
    # Filter out false positives that are part of larger words  
    # re with \b already handles this; but let's also exclude common legal terms
    # where 'I' appears as part of Roman numerals (Issue I, Section I) - allow Roman numeral I
    # Remove Roman numeral usages: "Issue I", "Section I", "Claim I", "Part I"
    clean_content_for_pronoun = re.sub(r'\b(Issue|Section|Claim|Part|Article|Annex|Exhibit|Schedule|No)\s+I\b', '', script_content)
    singular_hits_clean = singular_pattern.findall(clean_content_for_pronoun)
    no_singular = len(singular_hits_clean) == 0
    add_check(
        "No first-person singular pronouns (I/me/my/mine/myself)",
        no_singular,
        f"Singular pronoun occurrences found (excluding Roman numerals): {singular_hits_clean[:10]}"
    )

    # CHECK 3 – Uses correct collective/representative pronouns (we, our, Applicant, Claimant)
    has_collective = (
        bool(re.search(r'\bwe\b', script_content, re.IGNORECASE)) or
        bool(re.search(r'\bour\b', script_content, re.IGNORECASE)) or
        bool(re.search(r'\bapplicant\b', script_content, re.IGNORECASE)) or
        bool(re.search(r'\bclaimant\b', script_content, re.IGNORECASE)) or
        bool(re.search(r'\bnovatech\b', script_content, re.IGNORECASE))
    )
    add_check(
        "Uses collective/representative pronouns or party name (we/our/Applicant/Claimant/NovaTech)",
        has_collective,
        f"At least one correct pronoun/party reference found: {has_collective}"
    )

    # CHECK 4 – 5-part structure present: intro, opening/statement, roadmap, submission, conclusion
    has_intro = bool(re.search(r'\b(introduc|counsel for|appearing|represent|on behalf of)\b', sc))
    has_roadmap = bool(re.search(r'\b(roadmap|will address|will argue|will submit|will cover|first.*second|two (issues|claims|submissions))\b', sc))
    has_conclusion = bool(re.search(r'\b(conclude|conclusion|respectfully request|respectfully submit|pray|relief)\b', sc))
    has_structure = has_intro and has_roadmap and has_conclusion
    add_check(
        "Script has 5-part structure (intro + opening + roadmap + main submission + conclusion)",
        has_structure,
        f"Intro signals: {has_intro}, Roadmap signals: {has_roadmap}, Conclusion signals: {has_conclusion}"
    )

    # CHECK 5 – Two claims addressed (Jurisdiction and Force Majeure)
    has_jurisdiction = bool(re.search(r'\b(jurisdiction|jurisdictional)\b', sc))
    has_force_majeure = bool(re.search(r'\bforce\s+majeure\b', sc))
    has_two_claims = has_jurisdiction and has_force_majeure
    add_check(
        "Script addresses both claims: Jurisdiction and Force Majeure",
        has_two_claims,
        f"Jurisdiction: {has_jurisdiction}, Force Majeure: {has_force_majeure}"
    )

    # CHECK 6 – No banned phrases "Thank you for your question" or "I understand your concern"
    has_banned_tyq = bool(re.search(r'thank\s+you\s+for\s+your\s+question', sc))
    has_banned_iuyc = bool(re.search(r'i\s+understand\s+your\s+concern', sc))
    no_banned_phrases = not has_banned_tyq and not has_banned_iuyc
    add_check(
        "No banned phrases ('Thank you for your question' / 'I understand your concern')",
        no_banned_phrases,
        f"'Thank you for your question': {has_banned_tyq}; 'I understand your concern': {has_banned_iuyc}"
    )

    # CHECK 7 – No excessive absolute words: all, every, any (in argumentation context)
    # We check for patterns that suggest argumentative absolute claims
    absolute_pattern = re.compile(
        r'\b(all\s+(provisions|cases|evidence|arbitrators|parties|laws)|'
        r'every\s+(provision|case|rule|instance)|'
        r'any\s+(reasonable|court|tribunal)\s+(must|will|would|shall)\b)',
        re.IGNORECASE
    )
    absolute_hits = absolute_pattern.findall(script_content)
    no_excessive_absolutes = len(absolute_hits) == 0
    add_check(
        "No impermissible absolute argumentative claims (all provisions/every case/any court must...)",
        no_excessive_absolutes,
        f"Absolute hits: {absolute_hits}"
    )

    # CHECK 8 – Signpost / transition words present (structure clarity)
    signpost_pattern = re.compile(
        r'\b(first(ly)?|second(ly)?|third(ly)?|turning to|moving to|furthermore|in addition|'
        r'in conclusion|finally|with respect to|with regard to|submits? that|'
        r'next|accordingly|therefore|thus)\b',
        re.IGNORECASE
    )
    signpost_hits = signpost_pattern.findall(script_content)
    has_signposts = len(signpost_hits) >= 3
    add_check(
        "Script uses signpost/transition words for structure (at least 3 occurrences)",
        has_signposts,
        f"Signpost count: {len(signpost_hits)}; samples: {signpost_hits[:5]}"
    )

    # CHECK 9 – Latin pronunciation: "opinio juris" should NOT be written with "(JEW-ris)" note
    # and ideally references the correct pronunciation concept (iuris) or avoids the wrong gloss
    has_wrong_juris_pronunciation = bool(
        re.search(r'opinio\s+juris.*\bJEW[-\s]?ris\b', script_content, re.IGNORECASE) or
        re.search(r'\bJEW[-\s]?ris\b', script_content, re.IGNORECASE)
    )
    no_wrong_pronunciation = not has_wrong_juris_pronunciation
    add_check(
        "No incorrect Latin pronunciation annotation ('JEW-ris' for opinio juris)",
        no_wrong_pronunciation,
        f"Wrong pronunciation found: {has_wrong_juris_pronunciation}"
    )

    # ════════════════════════════════════════════════════════════════════════
    # QUESTION LIST CHECKS
    # ════════════════════════════════════════════════════════════════════════

    # CHECK 10 – Question list has at least 5 questions for Issue 1 (Jurisdiction)
    if qlist_content:
        # Count question marks in sections about jurisdiction
        juris_section = ""
        in_juris = False
        for line in qlist_content.split('\n'):
            if re.search(r'\b(jurisdiction|issue\s*1|issue\s*one)\b', line, re.IGNORECASE):
                in_juris = True
            if in_juris and re.search(r'\b(force\s+majeure|issue\s*2|issue\s*two)\b', line, re.IGNORECASE):
                in_juris = False
            if in_juris:
                juris_section += line + '\n'

        juris_questions = len(re.findall(r'\?', juris_section))
        # If no clear section, count total questions
        total_questions = len(re.findall(r'\?', qlist_content))
        has_enough_juris_questions = juris_questions >= 5 or total_questions >= 10
        add_check(
            "Question list has at least 5 questions for Jurisdiction issue (or 10+ total)",
            has_enough_juris_questions,
            f"Jurisdiction section questions: {juris_questions}; Total questions: {total_questions}"
        )

        # CHECK 11 – Question list has at least 5 questions for Issue 2 (Force Majeure)
        fm_section = ""
        in_fm = False
        for line in qlist_content.split('\n'):
            if re.search(r'\b(force\s+majeure|issue\s*2|issue\s*two)\b', line, re.IGNORECASE):
                in_fm = True
            if in_fm:
                fm_section += line + '\n'

        fm_questions = len(re.findall(r'\?', fm_section))
        has_enough_fm_questions = fm_questions >= 5 or total_questions >= 10
        add_check(
            "Question list has at least 5 questions for Force Majeure issue (or 10+ total)",
            has_enough_fm_questions,
            f"Force Majeure section questions: {fm_questions}; Total questions: {total_questions}"
        )

        # CHECK 12 – Question list has paragraph annotations (¶ or "para" or "paragraph" or "¶")
        has_para_annotations = bool(
            re.search(r'(¶\s*\d+|\bpara(graph)?\s*\.?\s*\d+|\bp\.\s*\d+)', qlist_content, re.IGNORECASE)
        )
        add_check(
            "Question list includes paragraph source annotations (¶N or para N)",
            has_para_annotations,
            f"Paragraph annotations found: {has_para_annotations}"
        )
    else:
        add_check("Question list has enough questions for Issue 1", False,
                  "Question list file missing or empty.")
        add_check("Question list has enough questions for Issue 2", False,
                  "Question list file missing or empty.")
        add_check("Question list includes paragraph annotations", False,
                  "Question list file missing or empty.")

    # ════════════════════════════════════════════════════════════════════════
    # Scoring
    # ════════════════════════════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.75 and checks[0]["passed"] and (checks[3]["passed"] if len(checks) > 3 else True)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "workspace arg", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))