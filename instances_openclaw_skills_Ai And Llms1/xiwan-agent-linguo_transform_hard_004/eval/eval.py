import json
import os
import re
import sys
from pathlib import Path


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)


def norm(s):
    try:
        s = s.lower()
        s = re.sub(r'\s+', ' ', s)
        return s
    except Exception:
        return ''


def main():
    checks = []
    try:
        ws = Path(sys.argv[1])
    except Exception:
        ws = Path('.')

    md_path = ws / 'agent_lingua_reference.md'
    summary_path = ws / 'summary.json'

    # Check 1: markdown exists and contains canonical URL
    try:
        if md_path.exists():
            text = md_path.read_text(encoding='utf-8', errors='replace')
            ok = 'clawhub.ai/xiwan/agent-linguo' in text.lower()
            checks.append({'name': 'markdown_exists_and_has_canonical_url', 'passed': ok, 'detail': 'canonical url found' if ok else 'canonical url missing'})
        else:
            checks.append({'name': 'markdown_exists_and_has_canonical_url', 'passed': False, 'detail': 'agent_lingua_reference.md missing'})
    except Exception as e:
        checks.append({'name': 'markdown_exists_and_has_canonical_url', 'passed': False, 'detail': f'error: {e}'})

    # Check 2: known markers preserved
    try:
        if md_path.exists():
            text = md_path.read_text(encoding='utf-8', errors='replace')
            markers = ['marker_alpha_742', 'marker_beta_913', 'marker_gamma_118']
            found = [m for m in markers if m in text.lower()]
            ok = len(found) == 3
            checks.append({'name': 'known_markers_preserved', 'passed': ok, 'detail': f'found {len(found)}/3 markers'})
        else:
            checks.append({'name': 'known_markers_preserved', 'passed': False, 'detail': 'markdown missing'})
    except Exception as e:
        checks.append({'name': 'known_markers_preserved', 'passed': False, 'detail': f'error: {e}'})

    # Check 3: summary json exists and has required fields
    try:
        if summary_path.exists():
            obj = json.loads(summary_path.read_text(encoding='utf-8', errors='replace'))
            url = str(obj.get('canonical_url', '')).lower()
            version = str(obj.get('version', '')).strip()
            sec = obj.get('security_levels', [])
            ok = ('clawhub.ai/xiwan/agent-linguo' in url) and (version.startswith('0.4')) and isinstance(sec, list) and any(str(x).upper() == 'E' for x in sec)
            detail = f"url={'yes' if 'clawhub.ai/xiwan/agent-linguo' in url else 'no'}, version={version or 'missing'}, security_count={len(sec) if isinstance(sec, list) else 'n/a'}"
            checks.append({'name': 'summary_json_content', 'passed': ok, 'detail': detail})
        else:
            checks.append({'name': 'summary_json_content', 'passed': False, 'detail': 'summary.json missing'})
    except Exception as e:
        checks.append({'name': 'summary_json_content', 'passed': False, 'detail': f'error: {e}'})

    # Check 4: markdown mentions handshake and signature in a forgiving way
    try:
        if md_path.exists():
            text = norm(md_path.read_text(encoding='utf-8', errors='replace'))
            ok = ('handshake' in text) and ('signature' in text) and ('09' in text)
            checks.append({'name': 'markdown_mentions_handshake_and_signature', 'passed': ok, 'detail': 'handshake/signature references present' if ok else 'missing handshake or signature references'})
        else:
            checks.append({'name': 'markdown_mentions_handshake_and_signature', 'passed': False, 'detail': 'markdown missing'})
    except Exception as e:
        checks.append({'name': 'markdown_mentions_handshake_and_signature', 'passed': False, 'detail': f'error: {e}'})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    score = passed / total if total else 0.0
    result = {'passed': passed == total, 'score': score, 'checks': checks}
    try:
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        print('{"passed":false,"score":0.0,"checks":[]}')


if __name__ == '__main__':
    main()
