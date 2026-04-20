from __future__ import annotations
import json
import re
import sys
from pathlib import Path


def load_text(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f"read error: {e}"


def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    try:
        out_txt = ws / 'output.txt'
        out_json = ws / 'output.json'
        add('output.txt exists', out_txt.exists(), 'present' if out_txt.exists() else 'missing')
        add('output.json exists', out_json.exists(), 'present' if out_json.exists() else 'missing')

        txt = ''
        if out_txt.exists():
            try:
                txt = out_txt.read_text(encoding='utf-8')
            except Exception as e:
                add('read output.txt', False, f'read error: {e}')
            else:
                need = ['signal board', 'composite risk light', 'actionable notes', 'data gaps']
                hits = sum(1 for n in need if n in normalize(txt))
                add('report sections', hits >= 4, f'{hits}/4 sections found')
                add('mentions marker-based asof', '2025-05-14' in txt, 'asof date present' if '2025-05-14' in txt else 'missing asof date')
        try:
            obj = json.loads(out_json.read_text(encoding='utf-8')) if out_json.exists() else None
            if obj is None:
                add('parse output.json', False, 'missing file')
            else:
                add('json top-level keys', set(obj.keys()) == {'asOf', 'signals', 'composite', 'confidence', 'gaps', 'notes'}, f'keys={list(obj.keys())}')
                add('signals length', isinstance(obj.get('signals'), list) and len(obj.get('signals')) == 10, f'len={len(obj.get("signals", [])) if isinstance(obj.get("signals"), list) else "n/a"}')
                add('composite format', isinstance(obj.get('composite'), str) and obj['composite'].upper() in {'GREEN','YELLOW','ORANGE','RED'}, f"value={obj.get('composite')}")
                add('gaps present', isinstance(obj.get('gaps'), list), 'list' if isinstance(obj.get('gaps'), list) else 'not list')
                add('notes present', isinstance(obj.get('notes'), list) and len(obj.get('notes')) >= 1, f'len={len(obj.get("notes", [])) if isinstance(obj.get("notes"), list) else "n/a"}')
                # fuzzy marker/content checks
                sig_text = ' '.join(str(x) for x in obj.get('signals', []))
                add('contains A1/A2/A3/C1 references', all(k in sig_text for k in ['A1', 'A2', 'A3', 'C1']), 'some core ids present')
        except Exception as e:
            add('parse output.json', False, f'json error: {e}')
    except Exception as e:
        add('overall execution', False, f'unhandled: {e}')

    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / len(checks) if checks else 0.0
    result = {"passed": passed_count == len(checks), "score": score, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
