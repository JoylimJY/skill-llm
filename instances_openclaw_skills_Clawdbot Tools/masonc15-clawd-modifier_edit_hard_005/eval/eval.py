import json
import re
import sys
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8', errors='ignore'), None
    except Exception as e:
        return None, str(e)


def normalize(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '', (s or '').lower())


def fuzzy_contains(text: str, needles):
    nt = normalize(text)
    return all(normalize(n) in nt for n in needles)


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # Check 1: required workspace marker file exists and contains markers
    try:
        p = workspace / 'workspace' / 'seed_markers.txt'
        if not p.exists():
            add_check('marker file exists', False, f'missing: {p}')
        else:
            txt, err = safe_read(p)
            if err:
                add_check('marker file exists', False, f'read error: {err}')
            else:
                ok = fuzzy_contains(txt, ['CLAWD_SEED_MARKER', 'WINTER_FESTIVAL_2025', 'rgb(100,149,237)'])
                add_check('marker file content', ok, 'found expected seed markers' if ok else 'missing one or more markers')
    except Exception as e:
        add_check('marker file exists', False, f'exception: {e}')

    # Check 2: manifest JSON exists and includes expected hint
    try:
        p = workspace / 'workspace' / 'manifest.json'
        if not p.exists():
            add_check('manifest exists', False, f'missing: {p}')
        else:
            try:
                data = json.loads(p.read_text(encoding='utf-8', errors='ignore'))
                markers = ' '.join(map(str, data.get('markers', [])))
                ok = fuzzy_contains(markers, ['WINTER_FESTIVAL_2025', 'raised arms', 'tiny hat'])
                add_check('manifest markers', ok, 'manifest contains expected markers' if ok else 'expected marker text not found')
            except Exception as e:
                add_check('manifest markers', False, f'json parse/read error: {e}')
    except Exception as e:
        add_check('manifest exists', False, f'exception: {e}')

    # Check 3: PDF exists and contains marker-ish text
    try:
        p = workspace / 'workspace' / 'clawd_notes.pdf'
        if not p.exists():
            add_check('pdf exists', False, f'missing: {p}')
        else:
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(p))
                text = ''
                for page in reader.pages:
                    try:
                        text += page.extract_text() or ''
                    except Exception:
                        pass
                ok = fuzzy_contains(text, ['WINTER_FESTIVAL_2025', 'target color', 'raised arms'])
                add_check('pdf marker text', ok, 'expected PDF text found' if ok else 'PDF text missing expected markers')
            except Exception as e:
                add_check('pdf marker text', False, f'pdf read/extract error: {e}')
    except Exception as e:
        add_check('pdf exists', False, f'exception: {e}')

    # Check 4: output changelog exists and mentions the requested modifications
    try:
        # Support both .txt and .md extensions, case-insensitive
        candidates = [
            workspace / 'CHANGELOG.md',
            workspace / 'changelog.md',
            workspace / 'CHANGELOG.txt',
            workspace / 'changelog.txt',
            workspace / 'CHANGES.md',
            workspace / 'changes.md',
            workspace / 'CHANGES.txt',
            workspace / 'changes.txt',
            workspace / 'workspace' / 'CHANGELOG.md',
            workspace / 'workspace' / 'changelog.md',
            workspace / 'workspace' / 'CHANGELOG.txt',
            workspace / 'workspace' / 'changelog.txt',
            workspace / 'workspace' / 'CHANGES.md',
            workspace / 'workspace' / 'changes.md',
            workspace / 'workspace' / 'CHANGES.txt',
            workspace / 'workspace' / 'changes.txt',
            workspace / 'assets' / 'CHANGELOG.md',
            workspace / 'assets' / 'changelog.md',
            workspace / 'assets' / 'CHANGELOG.txt',
            workspace / 'assets' / 'changelog.txt',
            workspace / 'assets' / 'CHANGES.md',
            workspace / 'assets' / 'changes.md',
            workspace / 'assets' / 'CHANGES.txt',
            workspace / 'assets' / 'changes.txt',
            workspace / 'assets' / 'clawd_changelog.md',
            workspace / 'assets' / 'clawd_changelog.txt',
            workspace / 'output' / 'CHANGELOG.md',
            workspace / 'output' / 'changelog.md',
            workspace / 'output' / 'CHANGELOG.txt',
            workspace / 'output' / 'changelog.txt',
        ]
        found = None
        for c in candidates:
            if c.exists():
                found = c
                break
        
        # Also search for any file with "changelog" or "changes" in the name (case-insensitive)
        if not found:
            for f in workspace.rglob('*'):
                if f.is_file() and ('changelog' in f.name.lower() or 'changes' in f.name.lower()):
                    found = f
                    break
        
        if not found:
            add_check('changelog exists', False, 'no changelog file found in expected locations')
        else:
            txt, err = safe_read(found)
            if err:
                add_check('changelog exists', False, f'read error: {err}')
            else:
                ok = fuzzy_contains(txt, ['clawd', 'ocean blue', 'tiny hat', 'raised arms'])
                add_check('changelog content', ok, f'found {found.name}' if ok else 'changelog missing key modification notes')
    except Exception as e:
        add_check('changelog exists', False, f'exception: {e}')

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total else 0.0
    passed = passed_count == total
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "fatal", "passed": False, "detail": str(e)}]}, ensure_ascii=False))