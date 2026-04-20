import json
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

try:
    output_path = workspace / 'output.json'
    if not output_path.exists():
        add_check('output_exists', False, 'output.json is missing')
    else:
        try:
            data = json.loads(output_path.read_text(encoding='utf-8'))
            add_check('output_exists', True, 'output.json found and parsed')
        except Exception as e:
            data = {}
            add_check('output_exists', False, f'output.json exists but could not be parsed: {e}')

    try:
        skill_text = (workspace / 'SKILL.md').read_text(encoding='utf-8')
    except Exception as e:
        skill_text = ''
        add_check('skill_file', False, f'Could not read SKILL.md: {e}')

    if isinstance(globals().get('data', None), dict):
        project_name = str(data.get('project_name', '')).lower().replace('—', '-').replace('–', '-').strip()
        version = str(data.get('version', '')).strip()
        license_name = str(data.get('license', '')).strip().lower()
        models = data.get('supported_models', [])

        add_check('project_name', 'tokenguard' in project_name, f'project_name={data.get("project_name")}')
        add_check('version', '1.5.0' in version, f'version={data.get("version")}')
        add_check('license', 'mit' in license_name, f'license={data.get("license")}')

        expected_models = ['gemini-3-flash', 'gemini-3-pro', 'claude-haiku', 'claude-sonnet', 'claude-opus', 'gpt-4o', 'deepseek']
        if isinstance(models, list):
            normalized = ' '.join(str(m).lower() for m in models)
            ok = all(m.lower() in normalized for m in expected_models)
            add_check('supported_models', ok, f'found={models}')
        else:
            add_check('supported_models', False, f'supported_models is not a list: {type(models).__name__}')

        marker_ok = 'tg-easy-001' in skill_text.lower()
        add_check('marker_presence', marker_ok, 'Marker TG-EASY-001 present in SKILL.md')
    else:
        add_check('project_name', False, 'No valid JSON output to inspect')
        add_check('version', False, 'No valid JSON output to inspect')
        add_check('license', False, 'No valid JSON output to inspect')
        add_check('supported_models', False, 'No valid JSON output to inspect')
        add_check('marker_presence', 'tg-easy-001' in skill_text.lower(), 'Marker TG-EASY-001 present in SKILL.md')
except Exception as e:
    add_check('fatal', False, f'Unexpected evaluator error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / max(len(checks), 1)
result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))
