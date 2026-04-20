from pathlib import Path
import json
import re
import sys


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    output_path = workspace / 'output.txt'

    try:
        if output_path.exists():
            text = output_path.read_text(encoding='utf-8', errors='replace')
            norm = re.sub(r'\s+', ' ', text).lower()
            has_marker = 'openseti analysis complete' in norm
            has_result = ('natural signal' in norm) or ('anomaly flagged' in norm) or ('anomaly' in norm)
            checks.append({'name': 'output_exists', 'passed': True, 'detail': 'output.txt found'})
            checks.append({'name': 'marker_phrase', 'passed': has_marker, 'detail': 'marker phrase present' if has_marker else 'missing marker phrase OPENSETI ANALYSIS COMPLETE'})
            checks.append({'name': 'mentions_result', 'passed': has_result, 'detail': 'mentions a classification' if has_result else 'missing natural signal or anomaly wording'})
        else:
            checks.append({'name': 'output_exists', 'passed': False, 'detail': 'output.txt is missing'})
            checks.append({'name': 'marker_phrase', 'passed': False, 'detail': 'not checked because file is missing'})
            checks.append({'name': 'mentions_result', 'passed': False, 'detail': 'not checked because file is missing'})
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking output.txt: {e}'})
        checks.append({'name': 'marker_phrase', 'passed': False, 'detail': 'evaluation failed safely'})
        checks.append({'name': 'mentions_result', 'passed': False, 'detail': 'evaluation failed safely'})

    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks) if checks else 0.0
    result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
