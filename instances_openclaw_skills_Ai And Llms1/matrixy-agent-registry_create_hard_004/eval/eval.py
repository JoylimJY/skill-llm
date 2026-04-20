import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def normalize(s):
    if s is None:
        return ''
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        registry_path = workspace / '.claude' / 'skills' / 'agent-registry' / 'registry.json'
        if not registry_path.exists():
            add_check('registry exists', False, 'Missing .claude/skills/agent-registry/registry.json')
        else:
            try:
                data = json.loads(registry_path.read_text(encoding='utf-8', errors='replace'))
                agents = data.get('agents', []) if isinstance(data, dict) else []
                add_check('registry parseable', isinstance(data, dict), 'registry.json parsed successfully' if isinstance(data, dict) else 'registry.json is not a JSON object')
                add_check('registry has agents', len(agents) >= 3, f'Found {len(agents)} agent entries' if isinstance(agents, list) else 'agents field missing or invalid')
            except Exception as e:
                add_check('registry parseable', False, f'Failed to parse registry.json: {e}')
                add_check('registry has agents', False, 'Could not inspect agents due to parse failure')

        source_dir = workspace / '.claude' / 'agents'
        source_files = []
        try:
            if source_dir.exists():
                source_files = sorted([p for p in source_dir.glob('*.md') if p.is_file()])
            add_check('source agents exist', len(source_files) >= 3, f'Found {len(source_files)} markdown agent files' if source_dir.exists() else 'Source directory missing')
        except Exception as e:
            add_check('source agents exist', False, f'Error inspecting source agents: {e}')

        try:
            reg_text = registry_path.read_text(encoding='utf-8', errors='replace') if registry_path.exists() else ''
            marker = 'MARKER_AGENT_REGISTRY_DEMO_9f3c2a'
            add_check('marker preserved in registry', marker.lower() in normalize(reg_text), 'Marker string found in registry.json' if marker.lower() in normalize(reg_text) else 'Marker string not found in registry.json')
        except Exception as e:
            add_check('marker preserved in registry', False, f'Could not inspect marker: {e}')

        # Best-match heuristics: security-auditor should be present and look like the strongest match
        try:
            data = json.loads(registry_path.read_text(encoding='utf-8', errors='replace')) if registry_path.exists() else {}
            agents = data.get('agents', []) if isinstance(data, dict) else []
            best_name = None
            best_score = -1.0
            for a in agents if isinstance(agents, list) else []:
                try:
                    name = str(a.get('name', ''))
                    desc = str(a.get('description', ''))
                    kws = ' '.join(a.get('keywords', [])) if isinstance(a.get('keywords', []), list) else str(a.get('keywords', ''))
                    blob = normalize(' '.join([name, desc, kws]))
                    score = 0.0
                    for term in ['security', 'authentication', 'auth', 'review', 'code']:
                        if term in blob:
                            score += 1.0
                    if score > best_score:
                        best_score = score
                        best_name = name
                except Exception:
                    continue
            passed = normalize(best_name) == normalize('security-auditor') or ('security auditor' in normalize(best_name))
            add_check('best match agent', passed, f'Best-match heuristic selected: {best_name!r}' if best_name else 'No best-match candidate found')
        except Exception as e:
            add_check('best match agent', False, f'Error evaluating best match: {e}')

        # Score calculation
        total = len(checks)
        passed_count = sum(1 for c in checks if c['passed'])
        score = passed_count / total if total else 0.0
        result = {'passed': passed_count == total and total > 0, 'score': score, 'checks': checks}
        print(json.dumps(result, indent=2))
    except Exception as e:
        # Last-resort graceful failure
        fallback = {'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal error', 'passed': False, 'detail': str(e)}]}
        print(json.dumps(fallback, indent=2))


if __name__ == '__main__':
    main()
