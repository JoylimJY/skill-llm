import json
import os
import re
import sys
from pathlib import Path


def normalize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    # Check input marker exists
    try:
        input_path = workspace / 'input.txt'
        if not input_path.exists():
            add_check('input file exists', False, 'input.txt is missing')
        else:
            content = input_path.read_text(encoding='utf-8', errors='replace')
            marker_ok = 'SMART_CONTEXT_TASK' in content
            add_check('input marker present', marker_ok, 'marker found' if marker_ok else 'marker missing')
    except Exception as e:
        add_check('input marker present', False, f'error reading input.txt: {e}')

    # Check output file exists
    try:
        output_path = workspace / 'output.txt'
        if not output_path.exists():
            add_check('output file exists', False, 'output.txt is missing')
            output_text = ''
        else:
            output_text = output_path.read_text(encoding='utf-8', errors='replace')
            add_check('output file exists', True, 'output.txt found')
    except Exception as e:
        output_text = ''
        add_check('output file exists', False, f'error reading output.txt: {e}')

    # Check summary mentions key ideas
    try:
        norm = normalize(output_text)
        required_phrases = [
            'token efficiency',
            'batch tool calls',
            'unnecessary file reads',
        ]
        matched = [phrase for phrase in required_phrases if all(token in norm for token in normalize(phrase).split())]
        passed = len(matched) == len(required_phrases)
        detail = 'matched: ' + ', '.join(matched) if matched else 'none of the required ideas were clearly present'
        add_check('summary includes key ideas', passed, detail)
    except Exception as e:
        add_check('summary includes key ideas', False, f'error checking output content: {e}')

    # Check brevity: not overly long
    try:
        word_count = len(re.findall(r'\b\w+\b', output_text))
        passed = word_count <= 80 and word_count > 0
        detail = f'word count = {word_count}'
        add_check('output is concise', passed, detail)
    except Exception as e:
        add_check('output is concise', False, f'error counting words: {e}')

    score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
    passed = all(c['passed'] for c in checks)
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()
