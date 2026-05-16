import sys
import json
import re
from pathlib import Path

def find_output_file(workspace: Path):
    """Search for the expected output file."""
    candidates = list(workspace.rglob("patient_P247_simplified.txt"))
    if not candidates:
        # Also accept .md or .json as secondary, but .txt is expected
        candidates = list(workspace.rglob("patient_P247_simplified.*"))
    return candidates[0] if candidates else None

def load_output(workspace: Path):
    f = find_output_file(workspace)
    if f is None:
        return None, "Output file 'patient_P247_simplified.txt' not found anywhere in workspace."
    try:
        return f.read_text(encoding="utf-8"), str(f)
    except Exception as e:
        return None, f"Could not read file: {e}"

def check_language_spanish(text: str) -> tuple[bool, str]:
    """Check that the output is primarily in Spanish."""
    spanish_markers = [
        r'\b(el|la|los|las|un|una|su|sus|que|con|para|por|como|este|esta|estos|estas|también|más|pero|donde)\b',
        r'\b(médico|médica|paciente|resultado|prueba|diagnóstico|tratamiento|síntoma|dolor|hospital)\b',
        r'\b(resumen|sección|términos|preguntas|recordatorio|explicación)\b',
        # accent characters common in Spanish
        r'[áéíóúñü¿¡]',
    ]
    total_hits = 0
    for pattern in spanish_markers:
        hits = len(re.findall(pattern, text, re.IGNORECASE))
        total_hits += hits
    if total_hits >= 8:
        return True, f"Spanish language markers found ({total_hits} hits)."
    return False, f"Output does not appear to be in Spanish (only {total_hits} Spanish markers found)."

def check_reading_level_teen(text: str) -> tuple[bool, str]:
    """
    Teen reading level: clear, direct, no medical jargon unexplained.
    Heuristic: text should NOT be excessively long, should avoid very complex
    sentence structures. We check that the tone feels appropriate — no academic
    phrasing like 'it is imperative' or 'one must consider'.
    Also: no use of 'Dear Patient' (adult template language).
    """
    adult_formal_markers = [
        r'\bestimado/a\s+paciente\b',   # "Dear Patient" in Spanish formal
        r'\bestimado\s+señor\b',
        r'\bdiferencial\b',  # differential diagnosis — not appropriate for teen
    ]
    for pat in adult_formal_markers:
        if re.search(pat, text, re.IGNORECASE):
            return False, f"Found adult/formal phrasing pattern '{pat}' not appropriate for Teen level."
    return True, "No adult-formal phrasing patterns found; consistent with Teen reading level."

def check_tone_reassuring(text: str) -> tuple[bool, str]:
    """
    Reassuring tone: calm, supportive, acknowledges worry.
    Look for reassuring phrases in Spanish.
    """
    reassuring_patterns = [
        r'\b(no te preocupes|no hay que preocuparse|esto es normal|tranquil|calma|apoyo|acompañar|juntos|estamos aquí)\b',
        r'\b(importante que sepas|queremos que entiendas|esto puede ayudarte)\b',
        r'\b(no estás solo|no estás sola)\b',
        # English reassuring fallback (if partially English)
        r'\b(don\'t worry|you are not alone|it\'s okay|reassur|support)\b',
    ]
    for pat in reassuring_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True, f"Reassuring tone markers found (pattern: '{pat}')."
    # Softer check: presence of supportive/calming words
    soft_patterns = [r'\b(important|importante|recuerda|recuerdan|apoyo|bien|cuid)\w*\b']
    hits = 0
    for pat in soft_patterns:
        hits += len(re.findall(pat, text, re.IGNORECASE))
    if hits >= 3:
        return True, f"Soft reassuring vocabulary present ({hits} hits); tone appears supportive."
    return False, "Output lacks reassuring tone markers — expected calm, supportive language."

def check_brief_length(text: str) -> tuple[bool, str]:
    """
    Brief length: key points only, 2–3 paragraphs in Summary.
    The total output should not be excessively long.
    We allow a full structured output but the Summary section specifically
    should be brief (not more than ~150 words).
    """
    # Extract summary section
    summary_match = re.search(
        r'(?:resumen|summary)[^\n]*\n(.*?)(?:\n\s*\n|\Z)',
        text, re.IGNORECASE | re.DOTALL
    )
    if summary_match:
        summary_text = summary_match.group(1).strip()
        word_count = len(summary_text.split())
        if word_count <= 200:
            return True, f"Summary section is {word_count} words — within Brief limit."
        else:
            return False, f"Summary section is {word_count} words — exceeds Brief length (should be ≤200 words / 2–3 paragraphs)."
    # If no clear summary section, check overall length
    total_words = len(text.split())
    if total_words <= 800:
        return True, f"Total output is {total_words} words — consistent with Brief length."
    return False, f"Total output is {total_words} words — may be too long for Brief setting (no distinct Summary section found)."

def check_five_sections(text: str) -> tuple[bool, str]:
    """
    Output must contain all 5 required sections:
    1. Summary
    2. Section breakdown
    3. Medical terms
    4. Questions for your doctor
    5. Reminder
    """
    # Accept both English and Spanish section headers
    section_patterns = {
        "Summary": [r'\bResumen\b', r'\bSummary\b'],
        "Section breakdown": [r'\bDesglose\b', r'\bSección\b', r'\bSection\b', r'\bBreakdown\b', r'\bSecciones\b'],
        "Medical terms": [r'\bTérminos\b', r'\bTerminos\b', r'\bMedical terms\b', r'\bGlosario\b', r'\btérminos médicos\b'],
        "Questions for your doctor": [r'\bPreguntas\b', r'\bQuestions\b', r'\bmédico\b.*\?', r'\bpreguntar\b'],
        "Reminder": [r'\bRecordatorio\b', r'\bReminder\b', r'\baviso\b', r'\bnota\b'],
    }
    missing = []
    found = []
    for section_name, patterns in section_patterns.items():
        matched = any(re.search(p, text, re.IGNORECASE) for p in patterns)
        if matched:
            found.append(section_name)
        else:
            missing.append(section_name)
    if not missing:
        return True, f"All 5 required sections present: {found}."
    return False, f"Missing sections: {missing}. Found: {found}."

def check_reminder_text(text: str) -> tuple[bool, str]:
    """
    The Reminder section must contain the canonical reminder message (in Spanish or English):
    English: "This is a simplified explanation to help you understand your medical information.
              Always discuss your care with your healthcare provider."
    Spanish equivalent expected.
    """
    # Check for English verbatim
    english_reminder = (
        r'This is a simplified explanation to help you understand your medical information'
    )
    spanish_reminder_patterns = [
        r'explicación simplificada',
        r'explicacion simplificada',
        r'para ayudarte? a entender',
        r'información médica',
        r'siempre (consulta|habla|discute)',
        r'(proveedor|profesional|médico) de (salud|atención)',
    ]
    if re.search(english_reminder, text, re.IGNORECASE):
        return True, "Verbatim English reminder text found."
    spanish_hits = sum(
        1 for p in spanish_reminder_patterns
        if re.search(p, text, re.IGNORECASE)
    )
    if spanish_hits >= 3:
        return True, f"Spanish reminder text present ({spanish_hits}/6 key phrases found)."
    if spanish_hits >= 2:
        return True, f"Spanish reminder text partially present ({spanish_hits}/6 phrases); acceptable."
    return False, (
        f"Reminder text is missing or incomplete ({spanish_hits}/6 Spanish reminder phrases found). "
        "Expected: simplified explanation disclaimer + advise to consult healthcare provider."
    )

def check_no_diagnosis(text: str) -> tuple[bool, str]:
    """
    Core Rule 2: No diagnosis, no treatment recommendation.
    The letter explicitly says no diagnosis confirmed — the output must reflect this.
    Must NOT state that the patient HAS a specific condition like Crohn's/colitis/IBD definitively.
    """
    diagnosis_assertion_patterns = [
        r'\b(tienes|tiene|you have|padeces)\s+(enfermedad\s+de\s+crohn|colitis|crohn|ibd|enfermedad\s+inflamatoria)\b',
        r'\b(diagnóstico\s+de|diagnosed\s+with)\s+(crohn|colitis|ibd)\b',
        r'\besto\s+es\s+causado\s+por\b',  # "this is caused by" — causal reasoning
        r'\bla\s+causa\s+es\b',            # "the cause is"
        r'\bsabemos\s+que\s+es\b',         # "we know it is"
    ]
    for pat in diagnosis_assertion_patterns:
        if re.search(pat, text, re.IGNORECASE):
            return False, f"Potential diagnosis assertion found (pattern: '{pat}'). Core Rule 2 violated."
    return True, "No definitive diagnosis assertions found. Core rules appear respected."

def check_preserve_uncertainty(text: str) -> tuple[bool, str]:
    """
    Core Rule 5: Preserve uncertainty — the letter says results are pending and
    no single cause determined. Output must reflect this ambiguity.
    """
    uncertainty_patterns = [
        r'\b(pendiente|pendientes|pending|aún no|todavía no|no\s+se\s+sabe|no\s+se\s+ha\s+confirmado)\b',
        r'\b(posible|posibles|possible|puede\s+ser|podría|could\s+be|might\s+be)\b',
        r'\b(no\s+se\s+ha\s+determinado|no\s+confirmado|no\s+confirmed|unclear|no\s+está\s+claro)\b',
    ]
    hits = sum(
        len(re.findall(p, text, re.IGNORECASE))
        for p in uncertainty_patterns
    )
    if hits >= 3:
        return True, f"Uncertainty preserved ({hits} uncertainty markers found)."
    return False, f"Insufficient uncertainty markers ({hits} found). The output may be resolving uncertainty that should be preserved (Core Rule 5)."

def check_patient_name_present(text: str) -> tuple[bool, str]:
    """The output should reference the patient Jamie or the letter context."""
    if re.search(r'\bJamie\b', text, re.IGNORECASE):
        return True, "Patient name 'Jamie' referenced in output."
    return False, "Patient name 'Jamie' not found in output. The explanation should be personalised to the patient."

def check_questions_for_doctor(text: str) -> tuple[bool, str]:
    """Must include 3–5 suggested questions."""
    # Count question marks as a proxy
    questions = re.findall(r'\?', text)
    # Also look for numbered question patterns
    numbered = re.findall(r'^\s*[1-5][\.\)]\s+.{10,}\?', text, re.MULTILINE)
    total_q = max(len(questions), len(numbered))
    if total_q >= 3:
        return True, f"At least 3 questions found ({total_q} question marks or numbered questions)."
    return False, f"Only {total_q} questions detected. The output should include 3–5 follow-up questions."

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []

    text, location_detail = load_output(workspace)

    file_found_check = {
        "name": "output_file_exists",
        "passed": text is not None,
        "detail": location_detail if text is None else f"Output file found at: {location_detail}",
    }
    checks.append(file_found_check)

    if text is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks,
        }

    # Run all checks
    check_functions = [
        ("language_is_spanish",         check_language_spanish),
        ("reading_level_teen",          check_reading_level_teen),
        ("tone_reassuring",             check_tone_reassuring),
        ("length_is_brief",             check_brief_length),
        ("five_sections_present",       check_five_sections),
        ("reminder_text_present",       check_reminder_text),
        ("no_diagnosis_asserted",       check_no_diagnosis),
        ("uncertainty_preserved",       check_preserve_uncertainty),
        ("patient_name_present",        check_patient_name_present),
        ("questions_for_doctor",        check_questions_for_doctor),
    ]

    for check_name, fn in check_functions:
        try:
            passed, detail = fn(text)
        except Exception as e:
            passed, detail = False, f"Check raised exception: {e}"
        checks.append({"name": check_name, "passed": passed, "detail": detail})

    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = round(passed_count / total_count, 3)

    # Must pass file_exists + at least 8 of the 10 content checks to pass overall
    content_checks = [c for c in checks if c["name"] != "output_file_exists"]
    content_passed = sum(1 for c in content_checks if c["passed"])
    overall_passed = file_found_check["passed"] and content_passed >= 8

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))