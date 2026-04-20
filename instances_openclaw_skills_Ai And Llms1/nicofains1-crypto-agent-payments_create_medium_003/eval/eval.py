import json
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        return None, str(e)

# Check 1: summary file exists and mentions the required core facts
summary_path = workspace / 'payment_summary.txt'
try:
    if not summary_path.exists():
        add_check('summary_exists', False, 'payment_summary.txt is missing')
        summary = ''
    else:
        summary = summary_path.read_text(encoding='utf-8', errors='replace')
        lowered = summary.lower()
        ok = all(term in lowered for term in ['base', 'q a-runner'.replace(' ', ''), 'usdc', '125.50', 'bounty-alpha-2048'])
        # tolerate formatting differences for QA-Runner
        ok = ok and ('qa-runner' in lowered or 'qa runner' in lowered)
        add_check('summary_contains_key_fields', ok, 'Checked for chain, recipient, asset, amount, and reference marker')
except Exception as e:
    add_check('summary_contains_key_fields', False, f'Could not read summary: {e}')

# Check 2: receipt json exists and is parseable
receipt_path = workspace / 'payment_receipt.json'
try:
    if not receipt_path.exists():
        add_check('receipt_exists', False, 'payment_receipt.json is missing')
        receipt = {}
    else:
        try:
            receipt = json.loads(receipt_path.read_text(encoding='utf-8', errors='replace'))
            add_check('receipt_parseable', True, 'JSON parsed successfully')
        except Exception as e:
            receipt = {}
            add_check('receipt_parseable', False, f'JSON parse failed: {e}')
except Exception as e:
    receipt = {}
    add_check('receipt_parseable', False, f'Unexpected error: {e}')

# Check 3: receipt contains expected keys/values fuzzily
try:
    chain_ok = str(receipt.get('chain', '')).strip().lower() in {'base', '8453'}
    token_ok = str(receipt.get('token', '')).strip().lower() == 'usdc'
    amt = str(receipt.get('amount', '')).strip()
    amt_ok = amt.startswith('125.5') or amt == '125.50' or amt == '125.500'
    ref_ok = 'bounty-alpha-2048' in str(receipt.get('reference', '')).lower()
    address = str(receipt.get('recipient_address', '')).lower()
    addr_ok = address.startswith('0x') and len(address) >= 10
    add_check('receipt_fields', chain_ok and token_ok and amt_ok and ref_ok and addr_ok,
              f'chain_ok={chain_ok}, token_ok={token_ok}, amt_ok={amt_ok}, ref_ok={ref_ok}, addr_ok={addr_ok}')
except Exception as e:
    add_check('receipt_fields', False, f'Error checking receipt fields: {e}')

# Check 4: output files are non-empty
try:
    summary_nonempty = summary_path.exists() and summary_path.stat().st_size > 0
    receipt_nonempty = receipt_path.exists() and receipt_path.stat().st_size > 0
    add_check('outputs_nonempty', summary_nonempty and receipt_nonempty,
              f'summary_nonempty={summary_nonempty}, receipt_nonempty={receipt_nonempty}')
except Exception as e:
    add_check('outputs_nonempty', False, f'Error checking sizes: {e}')

score = (sum(1 for c in checks if c['passed'])) / max(len(checks), 1)
passed = all(c['passed'] for c in checks)
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result))
