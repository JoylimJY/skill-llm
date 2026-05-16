import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def find_file(workspace, filename):
    matches = list(Path(workspace).rglob(filename))
    if not matches:
        return None
    # prefer root-level
    for m in matches:
        if m.parent == Path(workspace):
            return m
    return matches[0]

def evaluate(workspace):
    ws = Path(workspace)
    checks = []
    score = 0.0
    total_weight = 0.0

    # ── Locate output files ────────────────────────────────────────────
    study_notes_path   = find_file(workspace, "study-notes.md")
    quick_ref_path     = find_file(workspace, "quick-reference.md")
    exam_qa_path       = find_file(workspace, "exam-qa.md")

    # Check existence
    for fname, fpath, weight in [
        ("study-notes.md",    study_notes_path,  1.0),
        ("quick-reference.md",quick_ref_path,     1.0),
        ("exam-qa.md",        exam_qa_path,       1.0),
    ]:
        exists = fpath is not None and fpath.exists()
        checks.append(check(f"File exists: {fname}", exists,
                            f"Found at {fpath}" if exists else f"{fname} not found"))
        total_weight += weight
        if exists:
            score += weight

    # Read files safely
    def read(p):
        try:
            return p.read_text(encoding="utf-8") if p and p.exists() else ""
        except Exception as e:
            return ""

    notes   = read(study_notes_path)
    qref    = read(quick_ref_path)
    eqa     = read(exam_qa_path)

    # ── STUDY-NOTES.MD CHECKS ─────────────────────────────────────────

    # 1. Per-concept blocks: required sub-sections present
    required_sections = ["What it is", "Intuition", "Formal Treatment", "Worked Example",
                         "Connections", "Common Misconceptions"]
    if notes:
        present = [s for s in required_sections if re.search(re.escape(s), notes, re.IGNORECASE)]
        all_present = len(present) == len(required_sections)
        checks.append(check(
            "study-notes.md: all six per-concept sub-sections present",
            all_present,
            f"Found: {present}" if not all_present else "All six sub-sections present"
        ))
        total_weight += 2.0
        if all_present:
            score += 2.0
    else:
        checks.append(check("study-notes.md: all six per-concept sub-sections present",
                            False, "study-notes.md missing or empty"))
        total_weight += 2.0

    # 2. Source traceability: section numbers cited (e.g., [Section 1.2] or Section 3.3)
    if notes:
        section_refs = re.findall(r'\[?[Ss]ection\s+\d+\.\d+\]?', notes)
        has_traceability = len(section_refs) >= 5
        checks.append(check(
            "study-notes.md: source traceability (≥5 section references)",
            has_traceability,
            f"Found {len(section_refs)} section references: {section_refs[:5]}"
        ))
        total_weight += 1.5
        if has_traceability:
            score += 1.5
    else:
        total_weight += 1.5

    # 3. LaTeX formulas present (formal treatment requirement)
    if notes:
        latex_inline  = re.findall(r'\$[^$\n]+\$', notes)
        latex_block   = re.findall(r'\$\$[\s\S]+?\$\$', notes)
        has_latex = len(latex_inline) + len(latex_block) >= 3
        checks.append(check(
            "study-notes.md: LaTeX formulas present (≥3)",
            has_latex,
            f"Found {len(latex_inline)} inline, {len(latex_block)} block LaTeX expressions"
        ))
        total_weight += 1.0
        if has_latex:
            score += 1.0
    else:
        total_weight += 1.0

    # 4. Priority topic: Dijkstra's Algorithm — deeper treatment (≥2 worked examples)
    if notes:
        dijkstra_section = ""
        m = re.search(r'(?i)(dijkstra[\s\S]{0,3000}?)(?=\n##\s|\Z)', notes)
        if m:
            dijkstra_section = m.group(1)
        # Count "worked example" headings or step-by-step blocks in Dijkstra section
        worked_ex_count = len(re.findall(r'(?i)worked example', dijkstra_section))
        # Also check for multiple numbered steps (indicates worked examples)
        step_patterns = len(re.findall(r'(?m)^(step\s*\d|iteration\s*\d|\d+\.\s+[A-Z])', dijkstra_section, re.IGNORECASE))
        has_deep_dijkstra = worked_ex_count >= 2 or step_patterns >= 4
        checks.append(check(
            "study-notes.md: Dijkstra (priority topic) has extended treatment (≥2 worked examples or ≥4 step iterations)",
            has_deep_dijkstra,
            f"Dijkstra section: {worked_ex_count} 'worked example' headings, {step_patterns} step patterns found"
        ))
        total_weight += 2.0
        if has_deep_dijkstra:
            score += 2.0
    else:
        total_weight += 2.0

    # 5. Priority topic: DP Fundamentals present in study notes
    if notes:
        has_dp = bool(re.search(r'(?i)(dynamic programming|dp fundamental|optimal substructure|overlapping subproblem)', notes))
        checks.append(check(
            "study-notes.md: DP Fundamentals (priority topic) present",
            has_dp,
            "Found DP content" if has_dp else "No DP content found"
        ))
        total_weight += 1.0
        if has_dp:
            score += 1.0
    else:
        total_weight += 1.0

    # 6. [Standard curriculum knowledge] tags present (Phase 3 offline expansion rule)
    if notes:
        std_tags = re.findall(r'\[Standard curriculum knowledge\]', notes)
        has_std_tags = len(std_tags) >= 1
        checks.append(check(
            "study-notes.md or expansion: [Standard curriculum knowledge] tags used",
            has_std_tags,
            f"Found {len(std_tags)} [Standard curriculum knowledge] tags"
        ))
        total_weight += 1.0
        if has_std_tags:
            score += 1.0
    else:
        total_weight += 1.0

    # ── QUICK-REFERENCE.MD CHECKS ─────────────────────────────────────

    if qref:
        # 7. One-line-per-entry enforcement: check that entries don't have multi-line prose
        # Find all entry lines (lines starting with ** or ★ **)
        entry_lines = re.findall(r'(?m)^[★]?\s*\*\*[^*]+\*\*:.*$', qref)
        # Check for multi-line prose blocks (paragraphs longer than ~120 chars that aren't headers)
        long_prose_blocks = re.findall(r'(?m)^(?!#)(?!\*\*)[A-Z][a-z].{100,}$', qref)
        no_prose_violations = len(long_prose_blocks) == 0
        checks.append(check(
            "quick-reference.md: no multi-line prose (one-line-per-entry rule)",
            no_prose_violations,
            f"Found {len(long_prose_blocks)} potential prose violations: {long_prose_blocks[:2]}"
            if not no_prose_violations else f"Clean: {len(entry_lines)} one-line entries found"
        ))
        total_weight += 2.0
        if no_prose_violations:
            score += 2.0

        # 8. Priority topics marked with ★ in quick-reference
        has_dijkstra_star = bool(re.search(r'★.*[Dd]ijkstra', qref))
        has_dp_star        = bool(re.search(r'★.*([Dd]ynamic [Pp]rogramming|DP [Ff]undamental|[Oo]ptimal [Ss]ubstructure)', qref))
        priority_marked = has_dijkstra_star and has_dp_star
        checks.append(check(
            "quick-reference.md: priority topics marked with ★",
            priority_marked,
            f"Dijkstra ★: {has_dijkstra_star}, DP ★: {has_dp_star}"
        ))
        total_weight += 2.0
        if priority_marked:
            score += 2.0

        # 9. All major topic clusters covered in quick-reference
        major_topics = ["Tree", "Hash", "Graph", "Dynamic"]
        covered = [t for t in major_topics if re.search(t, qref, re.IGNORECASE)]
        all_covered = len(covered) == len(major_topics)
        checks.append(check(
            "quick-reference.md: all 4 major topic clusters present",
            all_covered,
            f"Found: {covered}" if not all_covered else "All 4 topic clusters present"
        ))
        total_weight += 1.0
        if all_covered:
            score += 1.0
    else:
        checks.append(check("quick-reference.md: no multi-line prose", False, "File missing"))
        checks.append(check("quick-reference.md: priority topics marked with ★", False, "File missing"))
        checks.append(check("quick-reference.md: all 4 major topic clusters present", False, "File missing"))
        total_weight += 5.0

    # ── EXAM-QA.MD CHECKS ─────────────────────────────────────────────

    if eqa:
        # 10. Source citations in every answer ([Source: Section X.Y] or [Source: ...])
        source_citations = re.findall(r'\[Source:.*?\]', eqa)
        total_questions  = len(re.findall(r'(?m)^\*?\*?Q\d+', eqa))
        # Require at least 60% of questions have citations (lenient to account for format variation)
        if total_questions > 0:
            citation_ratio = len(source_citations) / max(total_questions, 1)
            good_citations = citation_ratio >= 0.6 and len(source_citations) >= 5
        else:
            good_citations = len(source_citations) >= 5
        checks.append(check(
            "exam-qa.md: source citations present (≥5, ≥60% of questions)",
            good_citations,
            f"Found {len(source_citations)} [Source:...] citations for {total_questions} questions"
        ))
        total_weight += 2.0
        if good_citations:
            score += 2.0

        # 11. Minimum 3 questions per major topic
        topics_with_questions = {}
        for topic in ["Tree", "Hash", "Graph", "Dynamic"]:
            section_match = re.search(
                rf'(?i)## .*{topic}[\s\S]{{0,3000}}?(?=\n## |\Z)', eqa
            )
            if section_match:
                q_count = len(re.findall(r'(?m)^\*?\*?Q\d+', section_match.group(0)))
                topics_with_questions[topic] = q_count
            else:
                topics_with_questions[topic] = 0
        enough_questions = all(v >= 3 for v in topics_with_questions.values())
        checks.append(check(
            "exam-qa.md: minimum 3 questions per topic cluster",
            enough_questions,
            f"Questions per topic: {topics_with_questions}"
        ))
        total_weight += 1.5
        if enough_questions:
            score += 1.5

        # 12. Priority topics get ★ marker AND ≥5 questions
        dijkstra_section_eqa = re.search(
            r'(?i)(★.*dijkstra[\s\S]{0,2000}?)(?=\n## |\Z)', eqa
        )
        dp_section_eqa = re.search(
            r'(?i)(★.*dynamic programming[\s\S]{0,2000}?)(?=\n## |\Z)', eqa
        )

        # Alternative: find sections with Dijkstra/DP content and count questions
        def count_qs_in_topic(text, keyword):
            # Find the section
            m = re.search(rf'(?i)##.*{keyword}[\s\S]{{0,3000}}?(?=\n## |\Z)', text)
            if m:
                return len(re.findall(r'(?m)^\*?\*?Q\d+|\*\*Q\d+', m.group(0)))
            return 0

        dijkstra_q_count = count_qs_in_topic(eqa, "Dijkstra")
        dp_q_count       = count_qs_in_topic(eqa, r'Dynamic\s+Programming|DP\s+Fundamental')
        
        # Also check for ★ on any Dijkstra or DP questions
        dijkstra_star_eqa = bool(re.search(r'★.*[Dd]ijkstra|★.*\*\*Q\d+.*[Dd]ijkstra', eqa)) or \
                            bool(re.search(r'\*\*Q\d+.*★.*[Dd]ijkstra|★\s*\*\*Q', eqa))
        
        priority_5q = dijkstra_q_count >= 5 and dp_q_count >= 5
        checks.append(check(
            "exam-qa.md: priority topics have ≥5 questions each",
            priority_5q,
            f"Dijkstra: {dijkstra_q_count} questions, DP: {dp_q_count} questions"
        ))
        total_weight += 2.0
        if priority_5q:
            score += 2.0
    else:
        checks.append(check("exam-qa.md: source citations present", False, "File missing"))
        checks.append(check("exam-qa.md: minimum 3 questions per topic cluster", False, "File missing"))
        checks.append(check("exam-qa.md: priority topics have ≥5 questions each", False, "File missing"))
        total_weight += 5.5

    # ── Cross-file check: priority topics appear in ALL three files ───
    if notes and qref and eqa:
        dijkstra_in_all = (
            bool(re.search(r'(?i)dijkstra', notes)) and
            bool(re.search(r'(?i)dijkstra', qref)) and
            bool(re.search(r'(?i)dijkstra', eqa))
        )
        dp_in_all = (
            bool(re.search(r'(?i)dynamic programming', notes)) and
            bool(re.search(r'(?i)dynamic programming', qref)) and
            bool(re.search(r'(?i)dynamic programming', eqa))
        )
        priority_in_all = dijkstra_in_all and dp_in_all
        checks.append(check(
            "Priority topics (Dijkstra + DP) appear in all three output files",
            priority_in_all,
            f"Dijkstra in all 3: {dijkstra_in_all}, DP in all 3: {dp_in_all}"
        ))
        total_weight += 2.0
        if priority_in_all:
            score += 2.0
    else:
        checks.append(check(
            "Priority topics (Dijkstra + DP) appear in all three output files",
            False,
            "One or more output files missing"
        ))
        total_weight += 2.0

    # ── Final score ────────────────────────────────────────────────────
    final_score = round(score / total_weight, 4) if total_weight > 0 else 0.0
    passed = final_score >= 0.70

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))