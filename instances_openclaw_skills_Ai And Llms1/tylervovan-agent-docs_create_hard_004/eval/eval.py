import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f'failed to read {path}: {e}'


# 1) AGENTS.md exists and contains governance essentials
try:
    agents = workspace / 'AGENTS.md'
    if not agents.exists():
        add_check('agents_exists', False, 'AGENTS.md is missing')
    else:
        text = agents.read_text(encoding='utf-8', errors='ignore')
        norm = re.sub(r'\s+', ' ', text.lower())
        required_bits = ['critical', 'build', 'test', 'docs index', 'do not']
        passed = all(bit in norm for bit in required_bits)
        detail = 'contains required governance markers' if passed else f'missing one or more markers from {required_bits}'
        add_check('agents_governance_content', passed, detail)
except Exception as e:
    add_check('agents_governance_content', False, f'error checking AGENTS.md: {e}')

# 2) llms.txt exists and references expected docs with descriptions
try:
    llms = workspace / 'llms.txt'
    if not llms.exists():
        add_check('llms_exists', False, 'llms.txt is missing')
    else:
        text = llms.read_text(encoding='utf-8', errors='ignore')
        norm = re.sub(r'\s+', ' ', text.lower())
        expected_refs = ['docs/auth/setup.md', 'docs/db/schema.md', 'references/advanced-patterns.md']
        passed = all(ref.lower() in norm for ref in expected_refs)
        detail = 'references expected docs' if passed else 'one or more expected doc paths are absent'
        add_check('llms_references', passed, detail)
except Exception as e:
    add_check('llms_references', False, f'error checking llms.txt: {e}')

# 3) Reference doc exists and includes marker content from generated inputs
try:
    ref = workspace / 'references' / 'advanced-patterns.md'
    if not ref.exists():
        add_check('reference_file_exists', False, 'references/advanced-patterns.md is missing')
    else:
        text = ref.read_text(encoding='utf-8', errors='ignore')
        norm = re.sub(r'\s+', ' ', text.lower())
        marker_ok = 'delta-900' in norm
        title_ok = 'advanced patterns' in norm
        add_check('reference_file_content', marker_ok and title_ok, 'contains title and generated marker DELTA-900' if marker_ok and title_ok else 'missing title or marker')
except Exception as e:
    add_check('reference_file_content', False, f'error checking reference file: {e}')

# 4) AGENTS.md should mention build/test commands and a file map
try:
    agents = workspace / 'AGENTS.md'
    if agents.exists():
        text = agents.read_text(encoding='utf-8', errors='ignore')
        norm = re.sub(r'\s+', ' ', text.lower())
        has_build = 'build' in norm
        has_test = 'test' in norm
        has_map = ('docs/index' in norm) or ('docs:' in norm) or ('doc map' in norm) or ('docs index' in norm)
        passed = has_build and has_test and has_map
        detail = 'includes build/test guidance and documentation map' if passed else 'missing build/test guidance or doc map'
        add_check('agents_commands_and_map', passed, detail)
    else:
        add_check('agents_commands_and_map', False, 'AGENTS.md missing')
except Exception as e:
    add_check('agents_commands_and_map', False, f'error checking AGENTS.md command/map content: {e}')

# 5) Preserve generated marker files from input
try:
    marker_files = [
        (workspace / 'src' / 'app.py', 'alpha-42'),
        (workspace / 'docs' / 'auth' / 'setup.md', 'bravo-17'),
        (workspace / 'docs' / 'db' / 'schema.md', 'charlie-88'),
        (workspace / 'project-metadata.json', 'agent-docs-sandbox'),
    ]
    ok = True
    details = []
    for path, needle in marker_files:
        if not path.exists():
            ok = False
            details.append(f'{path} missing')
            continue
        try:
            text = path.read_text(encoding='utf-8', errors='ignore').lower()
            if needle not in text:
                ok = False
                details.append(f'{path} missing {needle}')
        except Exception as e:
            ok = False
            details.append(f'{path} read error: {e}')
    add_check('input_markers_preserved', ok, '; '.join(details) if details else 'all marker files preserved')
except Exception as e:
    add_check('input_markers_preserved', False, f'error checking marker files: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
print(json.dumps(result, indent=2))
