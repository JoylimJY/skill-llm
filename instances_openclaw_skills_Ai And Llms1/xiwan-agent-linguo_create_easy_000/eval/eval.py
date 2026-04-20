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


def normalize(s):
    try:
        return re.sub(r'\s+', '', (s or '').lower())
    except Exception:
        return ''


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    try:
        out_path = ws / 'output.txt'
        if not out_path.exists():
            checks.append({'name': 'output_exists', 'passed': False, 'detail': 'output.txt is missing'})
            result = {'passed': False, 'score': 0.0, 'checks': checks}
            print(json.dumps(result))
            return

        text, err = safe_read(out_path)
        if text is None:
            checks.append({'name': 'output_readable', 'passed': False, 'detail': f'Could not read output.txt: {err}'})
        else:
            ntext = normalize(text)
            sig_ok = '--👽lingua/0.4@agent-lingua' in text.replace('\r\n', '\n')
            checks.append({'name': 'signature_present', 'passed': bool(sig_ok), 'detail': 'Found required protocol signature' if sig_ok else 'Missing required signature line'})

            starts_ok = '👽09' in text
            checks.append({'name': 'handshake_marker', 'passed': bool(starts_ok), 'detail': 'Found handshake domain/action marker' if starts_ok else 'Missing 👽09 handshake marker'})

            base64_like = bool(re.search(r'\$j:[A-Za-z0-9+/=]{8,}', text))
            checks.append({'name': 'base64_payload', 'passed': bool(base64_like), 'detail': 'Found Base64 JSON payload' if base64_like else 'No Base64 JSON payload detected'})

            encryption_hint = any(k in ntext for k in ['"e"', 'security', 'x25519', 'aes-gcm', 'aes-256-gcm'])
            checks.append({'name': 'encryption_negotiation', 'passed': bool(encryption_hint), 'detail': 'Found encryption negotiation cues' if encryption_hint else 'No encryption negotiation cues found'})

        score = sum(1 for c in checks if c['passed']) / max(len(checks), 1)
        passed = len(checks) > 0 and all(c['passed'] for c in checks)
        result = {'passed': passed, 'score': score, 'checks': checks}
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        checks.append({'name': 'eval_exception', 'passed': False, 'detail': str(e)})
        score = sum(1 for c in checks if c['passed']) / max(len(checks), 1)
        print(json.dumps({'passed': False, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()
