import json
import os
import re
import sys
from pathlib import Path


def norm(text):
    return re.sub(r'[^a-z0-9]+', ' ', (text or '').lower()).strip()


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: expected output file exists
    try:
        candidates = [workspace / 'final_article.md', workspace / 'final_article.txt', workspace / 'output.txt']
        out_path = next((p for p in candidates if p.exists()), None)
        if out_path is None:
            checks.append({'name': 'output file exists', 'passed': False, 'detail': 'No expected output file found (final_article.md, final_article.txt, or output.txt).'})
            article_text = ''
        else:
            article_text, err = safe_read(out_path)
            if article_text is None:
                checks.append({'name': 'output file exists', 'passed': False, 'detail': f'Found {out_path.name} but could not read it: {err}'})
                article_text = ''
            else:
                checks.append({'name': 'output file exists', 'passed': True, 'detail': f'Found and read {out_path.name}.'})
    except Exception as e:
        checks.append({'name': 'output file exists', 'passed': False, 'detail': f'Unexpected error: {e}'})
        article_text = ''

    # Check 2: selected headline
    try:
        n = norm(article_text)
        ok = 'aurora launch report editorial review' in n
        checks.append({'name': 'headline chosen', 'passed': ok, 'detail': 'Expected the preferred headline to be present in a normalized form.' if ok else 'Preferred headline not found.'})
    except Exception as e:
        checks.append({'name': 'headline chosen', 'passed': False, 'detail': f'Headline check error: {e}'})

    # Check 3: evaluation criteria section
    try:
        n = norm(article_text)
        ok = ('evaluation criteria' in n) and (re.search(r'\bevaluation criteria\b', n) is not None)
        checks.append({'name': 'evaluation criteria section', 'passed': ok, 'detail': 'Evaluation criteria section appears present.' if ok else 'Missing evaluation criteria section.'})
    except Exception as e:
        checks.append({'name': 'evaluation criteria section', 'passed': False, 'detail': f'Section check error: {e}'})

    # Check 4: correct launch year/Q2 fact
    try:
        n = norm(article_text)
        ok = ('project aurora' in n) and (('q2 2024' in n) or ('2024' in n)) and ('2023' not in n)
        checks.append({'name': 'fact correction', 'passed': ok, 'detail': 'Project Aurora should be described as launched in Q2 2024, not 2023.' if ok else 'Fact correction missing or still contains incorrect 2023 claim.'})
    except Exception as e:
        checks.append({'name': 'fact correction', 'passed': False, 'detail': f'Fact check error: {e}'})

    # Check 5: references at very end
    try:
        raw = article_text or ''
        n = norm(raw)
        ref_pos = n.rfind('references')
        ok = ref_pos != -1 and ref_pos > max(0, len(n) - 200)
        checks.append({'name': 'references at end', 'passed': ok, 'detail': 'References section appears near the end of the document.' if ok else 'References section is missing or not at the end.'})
    except Exception as e:
        checks.append({'name': 'references at end', 'passed': False, 'detail': f'Reference placement check error: {e}'})

    passed_count = sum(1 for c in checks if c.get('passed'))
    total = len(checks) if checks else 1
    result = {
        'passed': passed_count == total,
        'score': passed_count / total,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
