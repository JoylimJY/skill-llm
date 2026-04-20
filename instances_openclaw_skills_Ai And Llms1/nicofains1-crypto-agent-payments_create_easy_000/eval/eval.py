import json
import os
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def norm(s):
    if s is None:
        return ''
    return ''.join(ch.lower() for ch in str(s) if ch.isalnum())


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)

    # Check 1: input config exists and contains the expected marker / chain
    try:
        p = ws / 'input_config.json'
        if p.exists():
            data = json.loads(p.read_text(encoding='utf-8'))
            passed = ('chainId' in data and str(data.get('chainId')) == '8453' and norm(data.get('marker')) == norm('ONLYSWAPS_READY_2025_03_01'))
            detail = f"found input_config.json with chainId={data.get('chainId')} marker={data.get('marker')}"
        else:
            passed = False
            detail = 'input_config.json is missing'
    except Exception as e:
        passed = False
        detail = f'could not parse input_config.json: {e}'
    checks.append({'name': 'input_config', 'passed': passed, 'detail': detail})

    # Check 2: README_TASK contains marker text
    try:
        p = ws / 'README_TASK.txt'
        if p.exists():
            text = p.read_text(encoding='utf-8', errors='replace')
            passed = norm('ONLYSWAPS_READY_2025_03_01') in norm(text) and norm('Base') in norm(text)
            detail = 'README_TASK.txt contains required marker and network hint' if passed else 'README_TASK.txt does not contain required marker and network hint'
        else:
            passed = False
            detail = 'README_TASK.txt is missing'
    except Exception as e:
        passed = False
        detail = f'could not read README_TASK.txt: {e}'
    checks.append({'name': 'readme_marker', 'passed': passed, 'detail': detail})

    # Check 3: expected output file exists after task completion
    try:
        p = ws / 'output.txt'
        if p.exists():
            text = p.read_text(encoding='utf-8', errors='replace')
            passed = norm('wallet readiness check') in norm(text) and norm('8453') in norm(text)
            detail = 'output.txt exists and references readiness check on chain 8453' if passed else 'output.txt exists but does not mention expected content'
        else:
            passed = False
            detail = 'output.txt is missing'
    except Exception as e:
        passed = False
        detail = f'could not read output.txt: {e}'
    checks.append({'name': 'output_file', 'passed': passed, 'detail': detail})

    score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
    result = {'passed': all(c['passed'] for c in checks), 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
