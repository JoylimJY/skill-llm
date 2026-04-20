import json
import os
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def safe_read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except Exception as e:
        return None, str(e)


def normalize(s):
    return ''.join(ch.lower() for ch in s if ch.isalnum()) if isinstance(s, str) else ''


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)

    try:
        out_path = ws / 'output.json'
        if not out_path.exists():
            checks.append({'name': 'output_exists', 'passed': False, 'detail': 'output.json is missing'})
        else:
            data, err = safe_read_json(out_path)
            if data is None:
                checks.append({'name': 'output_valid_json', 'passed': False, 'detail': f'Could not parse output.json: {err}'})
            else:
                checks.append({'name': 'output_valid_json', 'passed': True, 'detail': 'output.json parsed successfully'})

                marker_ok = False
                try:
                    txt = json.dumps(data)
                    marker_ok = 'NEAR_BATCH_MARKER_7F3A'.lower() in txt.lower()
                except Exception as e:
                    marker_ok = False
                    txt = str(e)
                checks.append({'name': 'marker_present', 'passed': marker_ok, 'detail': 'Campaign marker found in output' if marker_ok else 'Campaign marker missing from output'})

                recipients_ok = False
                try:
                    recipients = data.get('recipients', []) if isinstance(data, dict) else []
                    recipients_ok = isinstance(recipients, list) and len(recipients) == 3
                except Exception as e:
                    recipients_ok = False
                checks.append({'name': 'recipient_count', 'passed': recipients_ok, 'detail': 'Expected 3 recipients' if recipients_ok else 'Expected exactly 3 recipients'})

                nft_ok = False
                try:
                    transfers = data.get('transfers', []) if isinstance(data, dict) else []
                    nft_ok = isinstance(transfers, list) and len(transfers) == 2
                except Exception:
                    nft_ok = False
                checks.append({'name': 'nft_count', 'passed': nft_ok, 'detail': 'Expected 2 NFT transfers' if nft_ok else 'Expected exactly 2 NFT transfers'})

                order_ok = False
                try:
                    recipients = data.get('recipients', []) if isinstance(data, dict) else []
                    accounts = [r.get('account', '') for r in recipients if isinstance(r, dict)]
                    order_ok = len(accounts) >= 3 and [normalize(a) for a in accounts[:3]] == [normalize('alice.near'), normalize('bob.near'), normalize('carol.near')]
                except Exception:
                    order_ok = False
                checks.append({'name': 'recipient_order', 'passed': order_ok, 'detail': 'Recipient order matches input' if order_ok else 'Recipient order does not match input'})

                summary_path = ws / 'summary.txt'
                if not summary_path.exists():
                    checks.append({'name': 'summary_exists', 'passed': False, 'detail': 'summary.txt is missing'})
                else:
                    summary, err2 = safe_read_text(summary_path)
                    if summary is None:
                        checks.append({'name': 'summary_exists', 'passed': False, 'detail': f'Could not read summary.txt: {err2}'})
                    else:
                        summary_norm = normalize(summary)
                        summary_ok = ('3' in summary_norm) and ('2' in summary_norm) and ('recipient' in summary_norm) and ('transfer' in summary_norm)
                        checks.append({'name': 'summary_content', 'passed': summary_ok, 'detail': 'Summary mentions recipient and transfer counts' if summary_ok else 'Summary does not mention the expected counts'})
    except Exception as e:
        checks.append({'name': 'unexpected_error', 'passed': False, 'detail': str(e)})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    score = (passed / total) if total else 0.0
    result = {'passed': passed == total and total > 0, 'score': score, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
