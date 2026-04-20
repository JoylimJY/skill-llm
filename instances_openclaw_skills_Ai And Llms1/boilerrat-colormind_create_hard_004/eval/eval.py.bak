from pathlib import Path
import json
import re
import sys

workspace = Path(sys.argv[1])
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, f'failed to read {path}: {e}'


def normalize(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower())

# Check 1: models.json exists and is valid JSON with some model-like content
try:
    models_path = workspace / 'output' / 'models.json'
    if not models_path.exists():
        add_check('models_json_exists', False, 'output/models.json is missing')
    else:
        try:
            data = json.loads(models_path.read_text(encoding='utf-8'))
            if isinstance(data, dict):
                text = json.dumps(data).lower()
                passed = 'default' in text or 'ui' in text or 'models' in text
                add_check('models_json_content', passed, 'models.json is valid JSON and contains model-related content' if passed else 'models.json does not appear to contain model entries')
            elif isinstance(data, list):
                text = json.dumps(data).lower()
                passed = any('default' in str(x).lower() or 'ui' in str(x).lower() for x in data)
                add_check('models_json_content', passed, 'models.json is valid JSON list with model-related entries' if passed else 'models.json list lacks expected model names')
            else:
                add_check('models_json_content', False, 'models.json is valid JSON but not a list or dict')
        except Exception as e:
            add_check('models_json_content', False, f'models.json is malformed: {e}')
except Exception as e:
    add_check('models_json_exists', False, f'error checking models.json: {e}')

# Check 2: palette.json exists and has 5 colors
try:
    palette_path = workspace / 'output' / 'palette.json'
    if not palette_path.exists():
        add_check('palette_json_exists', False, 'output/palette.json is missing')
    else:
        try:
            palette = json.loads(palette_path.read_text(encoding='utf-8'))
            colors = None
            if isinstance(palette, dict):
                for k in ['palette', 'colors', 'result', 'data']:
                    if k in palette:
                        colors = palette[k]
                        break
                if colors is None and isinstance(palette.get('output'), list):
                    colors = palette.get('output')
            elif isinstance(palette, list):
                colors = palette
            passed = isinstance(colors, list) and len(colors) == 5
            add_check('palette_has_five_colors', passed, f'found {len(colors)} colors' if isinstance(colors, list) else 'could not locate color list in palette.json')
        except Exception as e:
            add_check('palette_has_five_colors', False, f'palette.json is malformed: {e}')
except Exception as e:
    add_check('palette_json_exists', False, f'error checking palette.json: {e}')

# Check 3: locked colors are present in order somewhere in palette.json text
expected_locked = ['18,18,30', '92,88,184', '34,193,195']
try:
    palette_text = None
    if (workspace / 'output' / 'palette.json').exists():
        try:
            palette_text = (workspace / 'output' / 'palette.json').read_text(encoding='utf-8')
        except Exception as e:
            add_check('locked_colors_in_order', False, f'cannot read palette.json text: {e}')
    if palette_text is not None:
        norm = normalize(palette_text)
        idxs = []
        last = -1
        ok = True
        for color in expected_locked:
            needle = normalize(color)
            pos = norm.find(needle, last + 1)
            if pos == -1:
                ok = False
                break
            idxs.append(pos)
            last = pos
        add_check('locked_colors_in_order', ok, 'locked colors appear in order' if ok else 'locked colors not found in required order')
except Exception as e:
    add_check('locked_colors_in_order', False, f'error checking locked colors: {e}')

# Check 4: summary markdown exists and mentions hex/rgb-style output
try:
    summary_path = workspace / 'output' / 'palette_summary.md'
    if not summary_path.exists():
        add_check('summary_exists', False, 'output/palette_summary.md is missing')
    else:
        try:
            text = summary_path.read_text(encoding='utf-8')
            ntext = text.lower()
            passed = ('rgb' in ntext) and ('#' in text)
            add_check('summary_mentions_formats', passed, 'summary includes RGB and hex markers' if passed else 'summary does not clearly mention RGB and hex')
        except Exception as e:
            add_check('summary_mentions_formats', False, f'failed to read summary: {e}')
except Exception as e:
    add_check('summary_exists', False, f'error checking summary: {e}')

# Check 5: no image sampling artifact required; ensure outputs are in output/ directory
try:
    outdir = workspace / 'output'
    passed = outdir.exists() and any(outdir.iterdir())
    add_check('output_directory_populated', passed, 'output directory exists and is populated' if passed else 'output directory missing or empty')
except Exception as e:
    add_check('output_directory_populated', False, f'error checking output directory: {e}')

passed_total = sum(1 for c in checks if c['passed'])
score = passed_total / len(checks) if checks else 0.0
result = {
    'passed': passed_total == len(checks),
    'score': score,
    'checks': checks,
}
print(json.dumps(result))
