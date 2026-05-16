import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Find cleaned_paper.tex
    candidates = list(Path(workspace_dir).rglob("cleaned_paper.tex"))
    
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "cleaned_paper.tex not found anywhere in workspace"}]
        }
    
    # Use the first found
    cleaned_path = candidates[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {cleaned_path}"})
    
    try:
        content = cleaned_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "file_readable", "passed": False, "detail": str(e)}]
        }

    checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully"})

    # ─────────────────────────────────────────────────────────────
    # CHECK 1: Citation spacing — no `Word(Author et al., YEAR)` pattern
    # Pattern: a non-space character immediately followed by `(`
    # where inside the parens is a citation-like pattern
    # ─────────────────────────────────────────────────────────────
    citation_no_space = re.findall(
        r'[^\s\\(]\((?:[A-Z][a-zA-Z\s&]+(?:et al\.)?),\s*\d{4}',
        content
    )
    # Filter out LaTeX math/commands like \frac(, \text(, etc.
    # Only flag actual word-chars immediately before `(`
    citation_no_space_filtered = [
        m for m in citation_no_space
        if not m.startswith('\\')
    ]
    
    cite_check_passed = len(citation_no_space_filtered) == 0
    checks.append({
        "name": "citation_space_before_paren",
        "passed": cite_check_passed,
        "detail": f"Found {len(citation_no_space_filtered)} citation(s) missing space before '(': {citation_no_space_filtered[:5]}"
    })

    # ─────────────────────────────────────────────────────────────
    # CHECK 2: Em-dash connecting clauses removed
    # An em-dash (—) flanked by text on both sides is a clause connector
    # We check that such patterns are largely gone
    # ─────────────────────────────────────────────────────────────
    emdash_pattern = re.findall(r'[a-zA-Z,\s]+—[a-zA-Z,\s]+—', content)
    emdash_single = re.findall(r'\w[^—\n]*—[^—\n]*\w', content)
    
    # Count em-dashes total
    total_emdash = content.count('—')
    emdash_passed = total_emdash == 0
    checks.append({
        "name": "emdash_clauses_removed",
        "passed": emdash_passed,
        "detail": f"Found {total_emdash} em-dash(es) (—) remaining. All must be removed/replaced."
    })

    # ─────────────────────────────────────────────────────────────
    # CHECK 3: Scare/emphasis quotes removed
    # Quotes used for emphasis around common non-proper-noun phrases
    # The original file has: "predicting the next action correctly",
    # "annotation burden", "generalization capability", "long-horizon",
    # "data bottleneck", "sim-to-real transfer", "visual backbone"
    # These should all be stripped of quotes in the cleaned version.
    # ─────────────────────────────────────────────────────────────
    
    # These are the specific emphasis-quote phrases from the original
    emphasis_quoted_phrases = [
        r'"predicting the next action correctly"',
        r'"annotation burden"',
        r'"generalization capability"',
        r'"long-horizon"',
        r'"data bottleneck"',
        r'"sim-to-real transfer"',
        r'"visual backbone"',
    ]
    remaining_emphasis = []
    for phrase in emphasis_quoted_phrases:
        # Match both straight and curly quotes
        straight = phrase  # already has straight quotes
        if re.search(re.escape(straight), content):
            remaining_emphasis.append(straight)
        # Also check LaTeX-style ``...''
        inner = re.sub(r'^"|"$', '', straight)
        if re.search(r'``' + re.escape(inner.strip('"')) + r"''", content):
            remaining_emphasis.append(f"``{inner.strip()}''")
    
    emphasis_passed = len(remaining_emphasis) == 0
    checks.append({
        "name": "emphasis_quotes_removed",
        "passed": emphasis_passed,
        "detail": f"Found {len(remaining_emphasis)} emphasis-quoted phrases still present: {remaining_emphasis}"
    })

    # ─────────────────────────────────────────────────────────────
    # CHECK 4: Math notation — vectors must use \mathbf{}
    # In the original: $x$, $a_t$, $v$, $q$, $z$ are vectors/embeddings
    # and should be \mathbf{x}, \mathbf{a}_t, etc.
    # Matrices W, K, V should use \mathbf{W}, \mathbf{K}, \mathbf{V}
    # Check: the file should contain \mathbf occurrences for vector/matrix vars
    # Also check that bare $x$, $v$, $q$, $z$ as standalone math (not subscripted
    # as scalars like $t$, $\alpha$, $N$, $d$, $i$) are converted
    # ─────────────────────────────────────────────────────────────
    
    # Count \mathbf usages (should be non-zero and cover key vectors)
    mathbf_count = len(re.findall(r'\\mathbf\{', content))
    
    # These specific vector/matrix variables from the paper MUST appear as \mathbf
    required_mathbf = [
        r'\\mathbf\{x\}',   # joint config vector x
        r'\\mathbf\{W\}',   # weight matrix W  
        r'\\mathbf\{v\}',   # visual feature vector v (or z)
    ]
    mathbf_found = []
    mathbf_missing = []
    for pattern in required_mathbf:
        if re.search(pattern, content):
            mathbf_found.append(pattern)
        else:
            mathbf_missing.append(pattern)
    
    # Also check that bare standalone $W$ (matrix) no longer appears without \mathbf
    bare_W = re.findall(r'\$W\$|\$W_', content)
    bare_x = re.findall(r'\$x\$', content)
    bare_v = re.findall(r'\$v\$', content)
    
    math_passed = (mathbf_count >= 3) and (len(bare_W) == 0) and (len(bare_x) == 0)
    checks.append({
        "name": "math_vector_notation",
        "passed": math_passed,
        "detail": (
            f"\\mathbf occurrences: {mathbf_count}. "
            f"Missing required mathbf patterns: {mathbf_missing}. "
            f"Bare $W$ remaining: {bare_W}. "
            f"Bare $x$ remaining: {bare_x}. "
            f"Bare $v$ remaining: {bare_v}."
        )
    })

    # ─────────────────────────────────────────────────────────────
    # CHECK 5: Over-citation outside Related Work
    # Paragraphs outside \section{Related Work} should not have 5+ citations
    # A citation is a `(Author..., YEAR)` pattern
    # ─────────────────────────────────────────────────────────────
    
    # Split content into sections
    sections = re.split(r'\\section\{', content)
    
    over_cited_paragraphs = []
    for i, section_text in enumerate(sections):
        # Skip Related Work section
        if section_text.lower().startswith('related work'):
            continue
        # Split into paragraphs (double newline)
        paragraphs = re.split(r'\n\s*\n', section_text)
        for para in paragraphs:
            # Count citation instances: (AuthorName..., YEAR) patterns
            cites = re.findall(r'\([A-Z][a-zA-Z\s&]+(?:et al\.)?,\s*\d{4}', para)
            if len(cites) >= 5:
                over_cited_paragraphs.append({
                    "citation_count": len(cites),
                    "snippet": para[:100].replace('\n', ' ')
                })
    
    overcite_passed = len(over_cited_paragraphs) == 0
    checks.append({
        "name": "no_overcitation_outside_related_work",
        "passed": overcite_passed,
        "detail": f"Found {len(over_cited_paragraphs)} paragraph(s) outside Related Work with 5+ citations: {over_cited_paragraphs[:2]}"
    })

    # ─────────────────────────────────────────────────────────────
    # CHECK 6: Document still valid LaTeX (has \begin{document} and \end{document})
    # ─────────────────────────────────────────────────────────────
    has_begin = r'\begin{document}' in content
    has_end = r'\end{document}' in content
    valid_latex = has_begin and has_end
    checks.append({
        "name": "valid_latex_structure",
        "passed": valid_latex,
        "detail": f"\\begin{{document}}: {has_begin}, \\end{{document}}: {has_end}"
    })

    # ─────────────────────────────────────────────────────────────
    # SCORING
    # ─────────────────────────────────────────────────────────────
    # Weights:
    # citation_space: 20%
    # emdash: 20%
    # emphasis_quotes: 20%
    # math_notation: 20%
    # overcitation: 15%
    # valid_latex: 5%
    
    weights = {
        "citation_space_before_paren": 0.20,
        "emdash_clauses_removed": 0.20,
        "emphasis_quotes_removed": 0.20,
        "math_vector_notation": 0.20,
        "no_overcitation_outside_related_work": 0.15,
        "valid_latex_structure": 0.05,
    }
    
    score = 0.0
    check_map = {c["name"]: c["passed"] for c in checks}
    for check_name, weight in weights.items():
        if check_map.get(check_name, False):
            score += weight
    
    # file_exists and file_readable are prerequisites, not scored separately
    all_core_passed = all(check_map.get(k, False) for k in weights)
    
    return {
        "passed": all_core_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))