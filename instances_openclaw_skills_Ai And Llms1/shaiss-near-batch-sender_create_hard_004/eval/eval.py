import json
import os
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def normalize(s):
    import re
    if s is None:
        return ""
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '', s)
    return s


def check_file_contains(path, needles):
    try:
        text = Path(path).read_text(encoding='utf-8', errors='ignore')
        ntext = normalize(text)
        missing = []
        for needle in needles:
            if normalize(needle) not in ntext:
                missing.append(needle)
        if missing:
            return False, f"missing markers: {missing}"
        return True, "all markers present"
    except Exception as e:
        return False, f"error reading {path}: {e}"


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    # Check 1: send batch file exists and has expected entries
    try:
        p = workspace / 'send_batch.json'
        if not p.exists():
            checks.append({"name": "send_batch_exists", "passed": False, "detail": "send_batch.json is missing"})
        else:
            data = json.loads(p.read_text(encoding='utf-8'))
            recipients = data.get('recipients', [])
            accounts = sorted([str(r.get('account', '')).lower() for r in recipients if isinstance(r, dict)])
            amounts = sorted([str(r.get('amount', '')) for r in recipients if isinstance(r, dict)])
            ok = (
                len(recipients) == 4 and
                all(x in accounts for x in ['alice.near', 'bob.near', 'carol.near', 'dave.near']) and
                all(x in amounts for x in ['1.25', '0.75', '2.5', '0.4']) and
                normalize(data.get('batch_tag', '')) == normalize('NEAR-QA-2025-04') and
                normalize(data.get('note', '')) == normalize('dry-run-before-execution')
            )
            detail = f"recipients={len(recipients)}, accounts={accounts}, amounts={amounts}"
            checks.append({"name": "send_batch_content", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "send_batch_content", "passed": False, "detail": f"error: {e}"})

    # Check 2: NFT batch file exists and has expected transfers
    try:
        p = workspace / 'nft_batch.json'
        if not p.exists():
            checks.append({"name": "nft_batch_exists", "passed": False, "detail": "nft_batch.json is missing"})
        else:
            data = json.loads(p.read_text(encoding='utf-8'))
            transfers = data.get('transfers', [])
            token_ids = sorted([str(t.get('token_id', '')) for t in transfers if isinstance(t, dict)])
            receivers = sorted([str(t.get('receiver', '')).lower() for t in transfers if isinstance(t, dict)])
            contracts = sorted([str(t.get('contract', '')).lower() for t in transfers if isinstance(t, dict)])
            ok = (
                len(transfers) == 3 and
                token_ids == ['101', '102', '103'] and
                all(x in receivers for x in ['alice.near', 'bob.near', 'carol.near']) and
                all(normalize(c) == normalize('collectibles.example.near') for c in contracts) and
                normalize(data.get('marker_contract', '')) == normalize('collectibles.example.near')
            )
            detail = f"transfers={len(transfers)}, token_ids={token_ids}, receivers={receivers}"
            checks.append({"name": "nft_batch_content", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "nft_batch_content", "passed": False, "detail": f"error: {e}"})

    # Check 3: claim batch file exists and has expected claims
    try:
        p = workspace / 'claim_batch.json'
        if not p.exists():
            checks.append({"name": "claim_batch_exists", "passed": False, "detail": "claim_batch.json is missing"})
        else:
            data = json.loads(p.read_text(encoding='utf-8'))
            claims = data.get('claims', [])
            claim_accounts = sorted([str(c.get('account', '')).lower() for c in claims if isinstance(c, dict)])
            ok = (
                len(claims) == 2 and
                claim_accounts == ['alice.near', 'dave.near'] and
                normalize(data.get('campaign', '')) == normalize('spring-airdrop-7')
            )
            detail = f"claims={len(claims)}, accounts={claim_accounts}"
            checks.append({"name": "claim_batch_content", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "claim_batch_content", "passed": False, "detail": f"error: {e}"})

    # Check 4: marker file contains all markers
    try:
        p = workspace / 'README_MARKERS.txt'
        if not p.exists():
            checks.append({"name": "marker_file_exists", "passed": False, "detail": "README_MARKERS.txt is missing"})
        else:
            ok, detail = check_file_contains(p, ['NEAR-QA-2025-04', 'dry-run-before-execution', 'collectibles.example.near', 'spring-airdrop-7'])
            checks.append({"name": "marker_file_content", "passed": ok, "detail": detail})
    except Exception as e:
        checks.append({"name": "marker_file_content", "passed": False, "detail": f"error: {e}"})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = (passed_count / total) if total else 0.0
    result = {
        "passed": passed_count == total,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
