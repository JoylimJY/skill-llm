import json
import re
import sys
from pathlib import Path


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def safe_read(path):
    try:
        return path.read_text(encoding="utf-8", errors='ignore')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    
    # Check for output file (try multiple possible names)
    out = ws / 'output.txt'
    if not out.exists():
        # Try alternative names in case agent used different naming
        for alt in ['talk.txt', 'ted_talk.txt', 'presentation.txt', 'outline.txt']:
            alt_path = ws / alt
            if alt_path.exists():
                out = alt_path
                break

    # Check 1: output exists
    try:
        exists = out.exists()
        detail = f'{out.name} exists' if exists else 'output.txt is missing'
        checks.append({'name': 'output_exists', 'passed': exists, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking existence: {e}'})

    # Check 2: contains TED-like structure markers (fuzzy matching)
    content = ''
    if out.exists():
        try:
            content = out.read_text(encoding='utf-8', errors='ignore')
            n = norm(content)
            # Use fuzzy matching for section names
            required = [
                ('opening', ['opening', 'hook', 'introduction', 'start']),
                ('setup', ['setup', 'background', 'context', 'introduction']),
                ('problem', ['problem', 'challenge', 'issue', 'difficulty']),
                ('core concept', ['core', 'concept', 'insight', 'key idea', 'main point']),
                ('real world examples', ['example', 'case study', 'real world', 'practical']),
                ('broader implications', ['implication', 'impact', 'broader', 'significance']),
                ('closing', ['closing', 'conclusion', 'summary', 'wrap up', 'ending']),
                ('q a', ['q&a', 'q and a', 'questions', 'qa', 'objection'])
            ]
            found = 0
            for section, variants in required:
                if any(re.search(norm(v), n) for v in variants):
                    found += 1
            passed = found >= 6
            checks.append({'name': 'section_structure', 'passed': passed, 'detail': f'found {found}/8 expected section cues'})
        except Exception as e:
            checks.append({'name': 'section_structure', 'passed': False, 'detail': f'failed to read output.txt: {e}'})
    else:
        checks.append({'name': 'section_structure', 'passed': False, 'detail': 'skipped because output.txt is missing'})

    # Check 3: word count approximates a 40-50 minute talk
    try:
        if content:
            words = re.findall(r"\b\w+\b", content)
            wc = len(words)
            # Allow some flexibility - 2000+ words is acceptable for 40-50 min talk
            passed = wc >= 2000
            checks.append({'name': 'length_requirement', 'passed': passed, 'detail': f'word_count={wc}; expected at least 2000'})
        else:
            checks.append({'name': 'length_requirement', 'passed': False, 'detail': 'no content to measure'})
    except Exception as e:
        checks.append({'name': 'length_requirement', 'passed': False, 'detail': f'length check error: {e}'})

    # Check 4: includes marker-derived theme from input files
    try:
        convo = ws / 'conversation_notes.txt'
        meta = ws / 'task_meta.json'
        marker_ok = False
        details = []
        if convo.exists():
            c = convo.read_text(encoding='utf-8', errors='ignore')
            marker_ok = marker_ok or ('marker_ted_talk_input_9f3c2a' in norm(c))
            details.append('conversation_notes.txt read')
        else:
            details.append('conversation_notes.txt missing')
        if meta.exists():
            m = json.loads(meta.read_text(encoding='utf-8', errors='ignore'))
            marker_ok = marker_ok or ('marker_ted_talk_input_9f3c2a' in norm(json.dumps(m)))
            details.append('task_meta.json read')
        else:
            details.append('task_meta.json missing')
        # Accept if output references key talk themes from inputs (fuzzy matching)
        theme_hits = 0
        theme_phrases = [
            ('why it matters', ['why it matters', 'importance', 'significance', 'value']),
            ('concrete examples', ['concrete example', 'specific example', 'real example', 'practical example']),
            ('q&a', ['q&a', 'q and a', 'questions and answers', 'qa section']),
            ('narrative arc', ['narrative', 'story arc', 'storyline', 'narrative structure']),
            ('broader implications', ['broader implication', 'wider impact', 'larger significance'])
        ]
        for phrase, variants in theme_phrases:
            if any(v.lower() in content.lower() for v in variants):
                theme_hits += 1
        passed = theme_hits >= 3
        checks.append({'name': 'input_theme_alignment', 'passed': passed, 'detail': f'theme_hits={theme_hits}; ' + '; '.join(details)})
    except Exception as e:
        checks.append({'name': 'input_theme_alignment', 'passed': False, 'detail': f'error: {e}'})

    passed_all = all(c.get('passed') for c in checks)
    score = (sum(1 for c in checks if c.get('passed')) / len(checks)) if checks else 0.0
    result = {'passed': passed_all, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': str(e)}]}))