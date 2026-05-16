import sys
import json
import re
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ─── 1. article.md must exist ───────────────────────────────────────────
    article_path = workspace_path / "article.md"
    try:
        article_text = article_path.read_text(encoding="utf-8")
        checks.append({"name": "article.md exists", "passed": True, "detail": "File found."})
    except Exception as e:
        checks.append({"name": "article.md exists", "passed": False, "detail": str(e)})
        return False, 0.0, checks

    # ─── 2. 素材.md must exist (deleted content preserved) ──────────────────
    sucai_candidates = list(workspace_path.rglob("素材.md"))
    if sucai_candidates:
        sucai_text = sucai_candidates[0].read_text(encoding="utf-8")
        checks.append({"name": "素材.md created for deleted content", "passed": True,
                        "detail": f"Found at {sucai_candidates[0]}"})
    else:
        sucai_text = ""
        checks.append({"name": "素材.md created for deleted content", "passed": False,
                        "detail": "素材.md not found anywhere in workspace."})

    # ─── 3. No banned pattern "不是……而是……" ────────────────────────────────
    pattern_bushi = re.search(r'不是.{0,20}而是', article_text)
    if pattern_bushi:
        checks.append({"name": "No '不是……而是……' AI-flavor pattern", "passed": False,
                        "detail": f"Found: '{pattern_bushi.group()}'"})
    else:
        checks.append({"name": "No '不是……而是……' AI-flavor pattern", "passed": True,
                        "detail": "Pattern not present."})

    # ─── 4. No quoted "humor" (Chinese 「...」quotes used as irony/humor markers) ─
    # Check for quoted single-word humor clichés like 「哲学式」「和平共处」inside running prose
    quoted_humor = re.findall(r'「[^」]{2,8}」', article_text)
    if quoted_humor:
        checks.append({"name": "No quoted 'humor' expressions with 「」", "passed": False,
                        "detail": f"Found quoted expressions: {quoted_humor}"})
    else:
        checks.append({"name": "No quoted 'humor' expressions with 「」", "passed": True,
                        "detail": "No problematic quoted expressions."})

    # ─── 5. Bold count per heading section ≤ 3 ──────────────────────────────
    # Split article into sections by H2/H3 headings
    sections = re.split(r'(?m)^#{2,3} .+', article_text)
    heading_matches = re.findall(r'(?m)^(#{2,3} .+)', article_text)
    all_sections_ok = True
    bad_sections = []
    for i, section_body in enumerate(sections[1:], start=0):
        bold_count = len(re.findall(r'\*\*[^*]+\*\*', section_body))
        if bold_count > 3:
            all_sections_ok = False
            heading_name = heading_matches[i] if i < len(heading_matches) else f"section {i}"
            bad_sections.append(f"'{heading_name}' has {bold_count} bold(s)")
    if all_sections_ok:
        checks.append({"name": "Bold count ≤ 3 per heading section", "passed": True,
                        "detail": "All sections comply."})
    else:
        checks.append({"name": "Bold count ≤ 3 per heading section", "passed": False,
                        "detail": "; ".join(bad_sections)})

    # ─── 6. No skipped heading levels (H2 → H4 without H3) ─────────────────
    headings = re.findall(r'(?m)^(#{1,6})\s', article_text)
    heading_levels = [len(h) for h in headings]
    skip_found = False
    for i in range(1, len(heading_levels)):
        if heading_levels[i] - heading_levels[i-1] > 1:
            skip_found = True
            break
    if skip_found:
        checks.append({"name": "No skipped heading levels", "passed": False,
                        "detail": f"Heading levels sequence: {heading_levels} — a jump of >1 detected."})
    else:
        checks.append({"name": "No skipped heading levels", "passed": True,
                        "detail": f"Heading levels: {heading_levels}"})

    # ─── 7. Consistent list markers (all '-' or all '*', not mixed) ─────────
    dash_items = re.findall(r'(?m)^- ', article_text)
    star_items = re.findall(r'(?m)^\* ', article_text)
    if dash_items and star_items:
        checks.append({"name": "Consistent list markers (no mixing - and *)", "passed": False,
                        "detail": f"Found {len(dash_items)} '-' items and {len(star_items)} '*' items."})
    else:
        checks.append({"name": "Consistent list markers (no mixing - and *)", "passed": True,
                        "detail": "Only one list marker type used."})

    # ─── 8. Language: no redundant phrase "基于这个原因" ────────────────────
    if "基于这个原因" in article_text:
        checks.append({"name": "Redundant phrase '基于这个原因' removed", "passed": False,
                        "detail": "'基于这个原因' still present — should be replaced with '因此' or similar."})
    else:
        checks.append({"name": "Redundant phrase '基于这个原因' removed", "passed": True,
                        "detail": "Phrase removed."})

    # ─── 9. Language: no weak verb "作出努力" ───────────────────────────────
    if "作出努力" in article_text:
        checks.append({"name": "Weak verb '作出努力' replaced", "passed": False,
                        "detail": "'作出努力' still present — should be condensed to '努力' or stronger verb."})
    else:
        checks.append({"name": "Weak verb '作出努力' replaced", "passed": True,
                        "detail": "Weak verb removed."})

    # ─── 10. Language: passive voice "被解决了" removed ─────────────────────
    if "被解决了" in article_text:
        checks.append({"name": "Passive voice '被解决了' fixed", "passed": False,
                        "detail": "'被解决了' still present — passive voice should be converted to active."})
    else:
        checks.append({"name": "Passive voice '被解决了' fixed", "passed": True,
                        "detail": "Passive voice removed."})

    # ─── 11. No numbered list (1. 2. 3.) in the article (replaced with -) ──
    # The original had "1. 噪音消除耳机..." which is a numbered list that should be consistent
    # Actually we check if numbered ordered lists remain (they may be valid but original mixing was issue)
    # Let's check that the original mixed section was fixed (either all - or all numbered, no hybrid)
    # We already check mixing of - and * above; numbered lists are separate but valid if consistent
    # Skip this check as not directly in SKILL.md

    # ─── 12. Article is not empty or trivially short ────────────────────────
    if len(article_text.strip()) < 200:
        checks.append({"name": "Article has substantial content", "passed": False,
                        "detail": f"Article only has {len(article_text.strip())} chars — too short."})
    else:
        checks.append({"name": "Article has substantial content", "passed": True,
                        "detail": f"Article has {len(article_text.strip())} chars."})

    # ─── Compute score ───────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall = passed_count >= (total * 0.75)  # must pass at least 75% of checks

    return overall, score, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        overall, score, checks = run_checks(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    result = {"passed": overall, "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()