import sys
import json
import re
import unicodedata
from pathlib import Path

def find_output(workspace: str) -> Path | None:
    candidates = list(Path(workspace).rglob("launch_announcement_final.md"))
    if candidates:
        return candidates[0]
    return None

def has_curly_quotes(text: str) -> bool:
    curly = ['\u201c', '\u201d', '\u2018', '\u2019']
    return any(c in text for c in curly)

def has_em_dash_overuse(text: str) -> bool:
    # More than 1 em dash is overuse per the skill
    return text.count('\u2014') > 1

def has_inline_header_list(text: str) -> bool:
    # Pattern: bullet starting with bold header + colon
    return bool(re.search(r'^\s*[-*]\s+\*\*[^*]+:\*\*', text, re.MULTILINE))

def has_emoji(text: str) -> bool:
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F9FF"
        "\u2600-\u26FF"
        "\u2700-\u27BF"
        "\u2B50"
        "\u2705\u2728]+",
        flags=re.UNICODE
    )
    return bool(emoji_pattern.search(text))

def has_title_case_heading(text: str) -> bool:
    # A heading where more than half the words are capitalized (excluding small words)
    small_words = {'a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor',
                   'on', 'at', 'to', 'by', 'in', 'of', 'up', 'as', 'is', 'it'}
    for line in text.splitlines():
        if line.startswith('#'):
            words = re.findall(r'[A-Za-z]+', line.lstrip('#').strip())
            if len(words) < 2:
                continue
            cap_words = [w for w in words if w[0].isupper() and w.lower() not in small_words]
            if len(cap_words) > len(words) * 0.5 and len(words) >= 3:
                return True
    return False

def has_ai_vocab(text: str) -> bool:
    ai_words = [
        r'\btapestry\b', r'\blandscape\b', r'\bpivotal\b', r'\bgroundbreaking\b',
        r'\bunderscore[sd]?\b', r'\bdelve\b', r'\bfoster(ing|s|ed)?\b',
        r'\bvibrant\b', r'\bshowcase[sd]?\b', r'\bshowcasing\b',
        r'\btestament\b', r'\bintricac(y|ies)\b', r'\bintricate\b',
        r'\bnestled\b', r'\bbreathtaking\b', r'\bboasts?\b',
        r'\bgroundbreaking\b', r'\bseamless\b', r'\bunparalleled\b',
    ]
    lower_text = text.lower()
    for pattern in ai_words:
        if re.search(pattern, lower_text):
            return True
    return False

def has_sycophancy(text: str) -> bool:
    patterns = [
        r'great question',
        r"you'?re absolutely right",
        r"that'?s an excellent point",
        r'i hope this helps',
        r'let me know if you',
        r'here is an overview',
        r'certainly!',
        r'of course!',
    ]
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)

def has_collaborative_artifacts(text: str) -> bool:
    patterns = [
        r'i hope this helps',
        r'let me know if you',
        r'here is an overview',
        r'would you like me to',
    ]
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)

def has_knowledge_cutoff_disclaimer(text: str) -> bool:
    patterns = [
        r'as of my last (training update|knowledge cutoff)',
        r'up to my last training',
        r'based on available information',
        r'specific details.*not.*documented',
    ]
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)

def has_negative_parallelism(text: str) -> bool:
    patterns = [
        r"it'?s not just",
        r"it'?s not merely",
        r'not only.*but',
        r"it'?s not just about",
    ]
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)

def has_challenges_section(text: str) -> bool:
    patterns = [
        r'despite (its|these) (challenges|complexity)',
        r'faces (several |typical )?challenges',
        r'future (outlook|looks bright)',
        r'exciting times lie ahead',
        r'journey toward excellence',
        r'major step in the right direction',
    ]
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)

def has_excessive_hedging(text: str) -> bool:
    patterns = [
        r'could potentially possibly',
        r'might possibly',
        r'potentially possibly',
    ]
    lower = text.lower()
    return any(re.search(p, lower) for p in patterns)

def has_excessive_bold(text: str) -> bool:
    # More than 4 bold phrases is overuse
    bold_instances = re.findall(r'\*\*[^*]+\*\*', text)
    return len(bold_instances) > 4

def has_false_range(text: str) -> bool:
    lower = text.lower()
    return bool(re.search(r'from the chaos of.*to the (precision|certainty)', lower))

def has_elegant_variation(text: str) -> bool:
    # Check for repeated synonym cycling for the platform name
    synonyms = ['main system', 'core platform', 'central engine', 'primary solution']
    found = sum(1 for s in synonyms if s in text.lower())
    return found >= 3

def has_generic_positive_conclusion(text: str) -> bool:
    lower = text.lower()
    patterns = [
        r'the future looks bright',
        r'exciting times lie ahead',
        r'journey toward excellence',
        r'major step in the right direction',
    ]
    return any(re.search(p, lower) for p in patterns)

def has_vague_attribution(text: str) -> bool:
    lower = text.lower()
    patterns = [
        r'industry experts (believe|say|argue)',
        r'experts argue',
        r'observers have (cited|noted)',
    ]
    return any(re.search(p, lower) for p in patterns)

def has_significance_inflation(text: str) -> bool:
    lower = text.lower()
    patterns = [
        r'serves as a testament',
        r'marks a pivotal moment',
        r'evolving (landscape|technological landscape)',
        r'setting the stage for',
        r'enduring mission',
        r'groundbreaking release',
    ]
    return any(re.search(p, lower) for p in patterns)

def has_rule_of_three(text: str) -> bool:
    # Look for the specific rule-of-three combos from the original
    lower = text.lower()
    combos = [
        r'powerful integrations.*seamless workflows.*unparalleled performance',
        r'innovation.*inspiration.*industry insights',
    ]
    return any(re.search(c, lower) for c in combos)

def has_soul(text: str) -> bool:
    """
    Check for signs of personality injection:
    - First person voice (I, we with opinion)
    - Specific numbers/facts (not just vague claims)
    - Varied sentence length (mix of short and long)
    - Opinion/feeling language
    """
    has_first_person_opinion = bool(re.search(
        r"\bI (keep|genuinely|think|find|wonder|can't|notice)\b", text
    )) or bool(re.search(r"\bHere'?s what\b", text, re.IGNORECASE))

    has_specific_detail = bool(re.search(
        r'\b\d+\s?(ms|seconds?|days?|hours?|percent|%|users?|teams?|events?)\b',
        text, re.IGNORECASE
    ))

    # Check sentence length variation
    sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
    if len(sentences) >= 4:
        lengths = [len(s.split()) for s in sentences]
        max_len = max(lengths)
        min_len = min(lengths)
        has_varied_rhythm = (max_len - min_len) >= 6
    else:
        has_varied_rhythm = False

    return has_first_person_opinion or has_specific_detail or has_varied_rhythm

def evaluate(workspace: str):
    checks = []

    output_file = find_output(workspace)
    if output_file is None:
        checks.append({"name": "output_file_exists", "passed": False,
                        "detail": "launch_announcement_final.md not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        text = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "output_file_readable", "passed": False,
                        "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "output_file_exists", "passed": True,
                    "detail": f"Found at {output_file}"})

    # ── Individual pattern checks ──────────────────────────────────────────
    def check(name: str, condition_violated: bool, detail_fail: str, detail_pass: str):
        passed = not condition_violated
        checks.append({"name": name, "passed": passed,
                        "detail": detail_fail if condition_violated else detail_pass})

    check("no_curly_quotes",
          has_curly_quotes(text),
          "Curly/smart quotes still present (\u201c\u201d\u2018\u2019)",
          "Straight quotes used correctly")

    check("no_em_dash_overuse",
          has_em_dash_overuse(text),
          "More than 1 em dash (\u2014) found — overuse not fixed",
          "Em dash usage is minimal or absent")

    check("no_inline_header_list",
          has_inline_header_list(text),
          "Inline-header bullet list pattern still present (**Header:** text)",
          "No inline-header lists found")

    check("no_emoji",
          has_emoji(text),
          "Emojis still present in text",
          "No emojis found")

    check("no_title_case_heading",
          has_title_case_heading(text),
          "Title Case heading(s) still present",
          "Headings use sentence case")

    check("no_ai_vocabulary",
          has_ai_vocab(text),
          "High-frequency AI vocabulary words still present",
          "AI vocabulary cleaned up")

    check("no_sycophancy",
          has_sycophancy(text),
          "Sycophantic/servile language still present",
          "No sycophantic language")

    check("no_collaborative_artifacts",
          has_collaborative_artifacts(text),
          "Chatbot communication artifacts still present (e.g. 'I hope this helps')",
          "No collaborative artifacts")

    check("no_knowledge_cutoff_disclaimer",
          has_knowledge_cutoff_disclaimer(text),
          "Knowledge-cutoff disclaimer still present",
          "No knowledge-cutoff disclaimers")

    check("no_negative_parallelism",
          has_negative_parallelism(text),
          "Negative parallelism still present ('not just...it's...')",
          "No negative parallelisms found")

    check("no_challenges_section_boilerplate",
          has_challenges_section(text),
          "Formulaic Challenges/Future Prospects boilerplate still present",
          "Challenges boilerplate removed")

    check("no_excessive_hedging",
          has_excessive_hedging(text),
          "Excessive hedging still present ('could potentially possibly')",
          "No excessive hedging")

    check("no_excessive_bold",
          has_excessive_bold(text),
          "More than 4 bolded phrases — bold overuse not fixed",
          "Bold usage is minimal")

    check("no_false_range",
          has_false_range(text),
          "False range construction still present ('from X to Y' on non-scale items)",
          "No false ranges detected")

    check("no_elegant_variation",
          has_elegant_variation(text),
          "Elegant variation (synonym cycling) still present for the platform",
          "No excessive synonym cycling")

    check("no_generic_positive_conclusion",
          has_generic_positive_conclusion(text),
          "Generic positive conclusion still present",
          "Generic positive conclusion removed")

    check("no_vague_attribution",
          has_vague_attribution(text),
          "Vague attribution still present ('Industry experts believe')",
          "No vague attributions")

    check("no_significance_inflation",
          has_significance_inflation(text),
          "Significance inflation still present ('testament', 'pivotal moment', etc.)",
          "Significance inflation removed")

    check("no_rule_of_three",
          has_rule_of_three(text),
          "Rule-of-three pattern still present",
          "No forced rule-of-three groupings")

    # Soul check — positive requirement
    soul_present = has_soul(text)
    checks.append({"name": "has_soul_and_voice",
                    "passed": soul_present,
                    "detail": "Text has personality, specific details, or varied rhythm" if soul_present
                              else "Text is sterile/voiceless — no personality injected despite pattern removal"})

    # Minimum length — ensure text wasn't just deleted
    non_empty = len(text.strip()) > 200
    checks.append({"name": "substantial_content_remains",
                    "passed": non_empty,
                    "detail": f"Output length: {len(text.strip())} chars" if non_empty
                              else "Output too short — content was over-deleted"})

    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = round(len(passed_checks) / total, 4)
    overall = score >= 0.80  # must pass at least 80% of checks

    return {
        "passed": overall,
        "score": score,
        "checks": checks,
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))