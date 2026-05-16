import sys
import json
import re
from pathlib import Path

def count_words(text):
    """Count words in text, stripping markdown formatting."""
    clean = re.sub(r'\*+', '', text)
    clean = re.sub(r'#+\s*', '', clean)
    clean = re.sub(r'\n+', ' ', clean)
    words = clean.strip().split()
    return len(words)

def count_lines_in_paragraph(paragraph):
    """Count non-empty lines in a paragraph block."""
    lines = [l for l in paragraph.split('\n') if l.strip()]
    return len(lines)

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # ── CHECK 1: File exists ───────────────────────────────────────────────────
    candidates = list(workspace.rglob("resposta.md"))
    file_found = len(candidates) > 0
    checks.append({
        "name": "resposta_md_exists",
        "passed": file_found,
        "detail": f"Found {len(candidates)} file(s) named resposta.md" if file_found else "No resposta.md file found in workspace"
    })

    if not file_found:
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    resposta_path = candidates[0]
    try:
        content = resposta_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── CHECK 2: Word count ≤ 500 ──────────────────────────────────────────────
    word_count = count_words(content)
    within_limit = word_count <= 500
    checks.append({
        "name": "word_count_under_500",
        "passed": within_limit,
        "detail": f"Word count: {word_count} (limit: 500)"
    })

    # ── CHECK 3: Base legal section with exact emoji marker ────────────────────
    has_base_legal = bool(re.search(r'📋\s*\*Base legal:\*', content))
    checks.append({
        "name": "base_legal_section_with_emoji",
        "passed": has_base_legal,
        "detail": "Found '📋 *Base legal:*' marker" if has_base_legal else "Missing '📋 *Base legal:*' section with clipboard emoji"
    })

    # ── CHECK 4: Aviso section with exact emoji marker ─────────────────────────
    has_aviso = bool(re.search(r'⚠️\s*\*Aviso:\*', content))
    checks.append({
        "name": "aviso_section_with_emoji",
        "passed": has_aviso,
        "detail": "Found '⚠️ *Aviso:*' marker" if has_aviso else "Missing '⚠️ *Aviso:*' section with warning emoji"
    })

    # ── CHECK 5: Aviso mentions AI / inteligência artificial ──────────────────
    aviso_match = re.search(r'⚠️.*?(?=\n\n|\Z)', content, re.DOTALL | re.IGNORECASE)
    if aviso_match:
        aviso_text = aviso_match.group(0)
        mentions_ai = bool(re.search(r'intelig[eê]ncia artificial|gerado por ia|ia |gerada por intelig', aviso_text, re.IGNORECASE))
    else:
        aviso_text = ""
        mentions_ai = False
    checks.append({
        "name": "aviso_mentions_ai",
        "passed": mentions_ai,
        "detail": "Aviso mentions AI/inteligência artificial" if mentions_ai else "Aviso section does not mention AI generation"
    })

    # ── CHECK 6: Substantive legal content from Registro de Candidatura ────────
    registro_keywords = [
        r'registro de candidatura',
        r'DRAP|Demonstrativo de Regularidade',
        r'RARC|Requerimento de Registro',
        r'elegibilidade|inelegibilidade',
        r'Ficha Limpa',
        r'9\.504|9504',
        r'64/1990|LC\s*64',
        r'23\.609|23609',
        r'filia[çc][aã]o partid',
        r'domicílio eleitoral',
        r'impugna[çc][aã]o',
    ]
    registro_matches = sum(1 for kw in registro_keywords if re.search(kw, content, re.IGNORECASE))
    has_registro_content = registro_matches >= 3
    checks.append({
        "name": "substantive_registro_candidatura_content",
        "passed": has_registro_content,
        "detail": f"Matched {registro_matches}/11 Registro de Candidatura keywords (need ≥3)"
    })

    # ── CHECK 7: Substantive legal content from Propaganda Eleitoral ──────────
    propaganda_keywords = [
        r'propaganda eleitoral',
        r'16 de agosto',
        r'propaganda antecipada',
        r'outdoor|santinho|panfleto|carro de som',
        r'HGPE|hor[aá]rio gr[au]tu[íi]to',
        r'redes sociais|internet',
        r'bens p[úu]blicos',
        r'9\.504|9504',
        r'23\.610|23610',
        r'impulsionamento',
        r'propagan[d]a.*irregul',
    ]
    propaganda_matches = sum(1 for kw in propaganda_keywords if re.search(kw, content, re.IGNORECASE))
    has_propaganda_content = propaganda_matches >= 3
    checks.append({
        "name": "substantive_propaganda_eleitoral_content",
        "passed": has_propaganda_content,
        "detail": f"Matched {propaganda_matches}/11 Propaganda Eleitoral keywords (need ≥3)"
    })

    # ── CHECK 8: Uses bold formatting (asterisks) ──────────────────────────────
    bold_matches = re.findall(r'\*[^*\n]{2,40}\*', content)
    has_bold = len(bold_matches) >= 2
    checks.append({
        "name": "uses_bold_formatting",
        "passed": has_bold,
        "detail": f"Found {len(bold_matches)} bold-formatted terms (need ≥2)"
    })

    # ── CHECK 9: Paragraph line constraint (no paragraph > 4 lines) ───────────
    # Split on double newlines to get paragraphs
    paragraphs = re.split(r'\n{2,}', content.strip())
    oversized_paragraphs = []
    for i, p in enumerate(paragraphs):
        non_empty_lines = [l for l in p.split('\n') if l.strip() and not l.strip().startswith('#')]
        if len(non_empty_lines) > 4:
            oversized_paragraphs.append((i, len(non_empty_lines)))
    
    paragraphs_ok = len(oversized_paragraphs) == 0
    checks.append({
        "name": "paragraph_line_limit",
        "passed": paragraphs_ok,
        "detail": "All paragraphs within 4-line limit" if paragraphs_ok else f"Paragraphs exceeding 4 lines: {oversized_paragraphs}"
    })

    # ── CHECK 10: Response is not empty/trivial (min 80 words) ────────────────
    not_trivial = word_count >= 80
    checks.append({
        "name": "response_not_trivial",
        "passed": not_trivial,
        "detail": f"Word count {word_count} >= 80 minimum" if not_trivial else f"Response too short ({word_count} words)"
    })

    # ── SCORING ───────────────────────────────────────────────────────────────
    # Weight critical checks more heavily
    weights = {
        "resposta_md_exists": 1.0,
        "word_count_under_500": 1.5,
        "base_legal_section_with_emoji": 2.0,
        "aviso_section_with_emoji": 2.0,
        "aviso_mentions_ai": 1.5,
        "substantive_registro_candidatura_content": 2.0,
        "substantive_propaganda_eleitoral_content": 2.0,
        "uses_bold_formatting": 1.0,
        "paragraph_line_limit": 1.0,
        "response_not_trivial": 1.0,
    }

    total_weight = sum(weights.values())
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned_weight / total_weight, 4)

    # Must pass critical structural checks to pass overall
    critical_checks = [
        "resposta_md_exists",
        "base_legal_section_with_emoji",
        "aviso_section_with_emoji",
        "aviso_mentions_ai",
        "substantive_registro_candidatura_content",
        "substantive_propaganda_eleitoral_content",
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = critical_passed and score >= 0.70

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))