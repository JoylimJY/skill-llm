import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    # ── Locate the output file ────────────────────────────────────────────────
    target = workspace / "project/manuscript/discussion_section.md"
    candidates = list(workspace.rglob("discussion_section.md"))
    
    if not target.exists():
        if candidates:
            content = candidates[0].read_text(encoding="utf-8", errors="replace")
            checks.append(check("file_location", False,
                f"File found at {candidates[0]} instead of project/manuscript/discussion_section.md"))
        else:
            checks.append(check("file_location", False, "discussion_section.md not found anywhere in workspace"))
            score = 0.0
            return {"passed": False, "score": score, "checks": checks}
    else:
        content = target.read_text(encoding="utf-8", errors="replace")
        checks.append(check("file_location", True, "File found at project/manuscript/discussion_section.md"))
    
    content_lower = content.lower()
    
    # ── CHECK 1: Minimum length (substantive content) ─────────────────────────
    word_count = len(content.split())
    passed_length = word_count >= 400
    checks.append(check("minimum_length",
        passed_length,
        f"Word count: {word_count} (minimum 400 required for a substantive discussion section)"))
    
    # ── CHECK 2: Required 6-part structure headings ───────────────────────────
    required_sections = [
        (r'\bopening\b', "Opening"),
        (r'\binterpretation\b', "Interpretation"),
        (r'\bcomparison.{0,20}literature\b', "Comparison to Literature"),
        (r'\bimplications\b', "Implications"),
        (r'\blimitations\b', "Limitations"),
        (r'\bconclusion\b', "Conclusion"),
    ]
    
    missing_sections = []
    for pattern, label in required_sections:
        if not re.search(pattern, content_lower):
            missing_sections.append(label)
    
    passed_structure = len(missing_sections) == 0
    checks.append(check("six_part_structure",
        passed_structure,
        f"Missing sections: {missing_sections}" if missing_sections else "All 6 required sections present"))
    
    # ── CHECK 3: Limitations use the 3-part template ─────────────────────────
    has_limitation_label = bool(re.search(r'\blimitation\s*:', content, re.IGNORECASE))
    has_impact_label = bool(re.search(r'\bimpact\s*:', content, re.IGNORECASE))
    has_mitigation_label = bool(re.search(r'\bmitigation\s*/\s*future\s*direction\s*:', content, re.IGNORECASE))
    
    passed_limitations_template = has_limitation_label and has_impact_label and has_mitigation_label
    checks.append(check("limitations_three_part_template",
        passed_limitations_template,
        (f"Limitation label: {has_limitation_label}, Impact label: {has_impact_label}, "
         f"Mitigation/Future direction label: {has_mitigation_label}. "
         "All three are required in the Limitations subsection.")))
    
    # ── CHECK 4: All 4 key results addressed ─────────────────────────────────
    result_signals = [
        (r'tmt.{0,10}b|trail.making', "TMT-B / Trail Making result"),
        (r'stroop', "Stroop result"),
        (r'age.{0,20}interact|interact.{0,20}age|older.{0,20}particip|particip.{0,20}older', "Age interaction result"),
        (r'null|not significant|no significant|p\s*=\s*0\.4[0-9]|gender.*subgroup|subgroup.*gender|female.*depriv|depriv.*female', "Null finding (gender subgroup)"),
    ]
    
    missing_results = []
    for pattern, label in result_signals:
        if not re.search(pattern, content_lower):
            missing_results.append(label)
    
    passed_all_results = len(missing_results) == 0
    checks.append(check("all_findings_addressed",
        passed_all_results,
        f"Missing results: {missing_results}" if missing_results else "All 4 key findings addressed"))
    
    # ── CHECK 5: Hedged language ──────────────────────────────────────────────
    hedge_words = [
        r'\bsuggests?\b', r'\bindicates?\b', r'\bmay\s+reflect\b', r'\bmay\s+indicate\b',
        r'\bmay\s+suggest\b', r'\bappears?\s+to\b', r'\bconsistent\s+with\b',
        r'\bpossible\b', r'\bone\s+possible\s+explanation\b', r'\blikely\b',
        r'\bperhaps\b', r'\bmight\b', r'\bcould\b'
    ]
    found_hedges = [hw for hw in hedge_words if re.search(hw, content_lower)]
    passed_hedging = len(found_hedges) >= 3
    checks.append(check("hedged_language",
        passed_hedging,
        f"Found {len(found_hedges)} hedging patterns (need ≥3): {found_hedges[:5]}"))
    
    # ── CHECK 6: Literature citations present ─────────────────────────────────
    lit_signals = [
        (r'harrison.{0,20}horne|horne.{0,20}harrison', "Harrison & Horne (2000)"),
        (r'lim.{0,20}dinges|dinges.{0,20}lim', "Lim & Dinges (2010)"),
        (r'wimmer', "Wimmer et al. (2012)"),
    ]
    missing_lit = []
    for pattern, label in lit_signals:
        if not re.search(pattern, content_lower):
            missing_lit.append(label)
    
    passed_lit = len(missing_lit) == 0
    checks.append(check("literature_citations",
        passed_lit,
        f"Missing citations: {missing_lit}" if missing_lit else "All 3 required prior studies referenced"))
    
    # ── CHECK 7: Conclusion ties back to research question ────────────────────
    conclusion_match = re.search(
        r'(conclusion|conclusions?)(.*?)$', content_lower, re.DOTALL | re.IGNORECASE)
    
    if conclusion_match:
        conclusion_text = conclusion_match.group(2)[:1500]
        rq_signals = [
            r'sleep\s+depriv', r'cognitive\s+flex', r'university\s+student|student',
            r'research\s+question', r'findings?\s+suggest|findings?\s+indicate',
            r'future\s+(research|studi|work|invest)'
        ]
        found_rq = [s for s in rq_signals if re.search(s, conclusion_text)]
        passed_conclusion = len(found_rq) >= 2
        checks.append(check("conclusion_ties_to_rq",
            passed_conclusion,
            f"Conclusion found. RQ signals matched: {found_rq} (need ≥2)"))
    else:
        checks.append(check("conclusion_ties_to_rq",
            False,
            "No conclusion section text found after 'Conclusion' heading"))
    
    # ── CHECK 8: No new data introduced ──────────────────────────────────────
    # Flag if suspiciously specific numbers not in the results appear
    original_numbers = {'61.3', '40.8', '9.1', '7.4', '12.4', '71.2', '89.7',
                        '11.3', '8.6', '9.8', '5.62', '0.020', '0.055', '0.41', '96'}
    found_numbers = set(re.findall(r'\d+\.\d+', content))
    novel_numbers = found_numbers - original_numbers
    # Allow years and small decimals likely from citations (e.g., 2000, 2010, 2012)
    likely_citations = {n for n in novel_numbers if re.match(r'^(19|20)\d{2}$', n.replace('.', ''))}
    suspicious_novel = novel_numbers - likely_citations
    # Being lenient: only flag if there are many novel precise decimals (>5)
    passed_no_new_data = len(suspicious_novel) <= 5
    checks.append(check("no_new_data_introduced",
        passed_no_new_data,
        f"Novel numeric values not in original results: {list(suspicious_novel)[:10]} "
        f"({'acceptable' if passed_no_new_data else 'too many new numbers — possible new data introduced'})"))
    
    # ── CHECK 9: Null finding acknowledged without dismissal ──────────────────
    null_region = re.search(
        r'(null|no\s+significant|not\s+significant|p\s*=\s*0\.4)(.*?)(\.|\n\n)',
        content_lower, re.DOTALL)
    if null_region:
        null_text = null_region.group(0)
        # It shouldn't just say "irrelevant" or "not important"
        dismissive = re.search(r'irrelevant|unimportant|discard|ignore', null_text)
        passed_null = not dismissive
        checks.append(check("null_finding_not_dismissed",
            passed_null,
            "Null finding mentioned without dismissive language" if passed_null
            else "Null finding appears to be dismissed"))
    else:
        checks.append(check("null_finding_not_dismissed",
            False,
            "Null finding (p=0.41, gender subgroup) not explicitly mentioned"))
    
    # ── SCORING ───────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    
    # Hard gates: structure + limitations template + all findings must pass
    hard_gates = ["six_part_structure", "limitations_three_part_template", "all_findings_addressed"]
    hard_passed = all(c["passed"] for c in checks if c["name"] in hard_gates)
    
    overall_passed = hard_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = run_eval(workspace_dir)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_error", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, indent=2))