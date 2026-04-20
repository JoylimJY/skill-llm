import json
import os
import re
from pathlib import Path


def norm(text):
    return re.sub(r'[^a-z0-9]+', ' ', str(text).lower()).strip()


def fuzzy_contains(text, needles):
    ntext = norm(text)
    return any(norm(n) in ntext for n in needles)


def read_text(path):
    try:
        content = Path(path).read_text(encoding='utf-8', errors='ignore')
        return content, None
    except Exception as e:
        return None, str(e)


def main():
    import sys
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    checks = []

    # Find output file (could be .md, .txt, or .json)
    output_file = None
    for ext in ['.md', '.txt', '.json']:
        candidate = workspace / f'revenue_model{ext}'
        if candidate.exists():
            output_file = candidate
            break
        candidate = workspace / f'revenue_plan{ext}'
        if candidate.exists():
            output_file = candidate
            break
        candidate = workspace / f'monetization{ext}'
        if candidate.exists():
            output_file = candidate
            break

    if not output_file:
        # Check for any markdown file in workspace
        for f in workspace.glob('*.md'):
            if 'revenue' in f.name.lower() or 'model' in f.name.lower() or 'plan' in f.name.lower():
                output_file = f
                break

    if not output_file:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': 'No revenue model output file found'})
    else:
        checks.append({'name': 'output_exists', 'passed': True, 'detail': f'Found output file: {output_file.name}'})

    content = None
    if output_file:
        content, _ = read_text(output_file)

    # Check for primary revenue model (subscription)
    if content:
        has_subscription = fuzzy_contains(content, ['subscription', 'monthly', 'tier', 'plan', 'mrr'])
        checks.append({'name': 'primary_model', 'passed': has_subscription, 'detail': 'Contains subscription/recurring model' if has_subscription else 'Missing primary revenue model'})
    else:
        checks.append({'name': 'primary_model', 'passed': False, 'detail': 'Cannot read content'})

    # Check for secondary revenue stream
    if content:
        has_secondary = fuzzy_contains(content, ['secondary', 'add-on', 'template', 'consulting', 'setup', 'one-time', 'addon'])
        checks.append({'name': 'secondary_stream', 'passed': has_secondary, 'detail': 'Contains secondary revenue stream' if has_secondary else 'Missing secondary revenue stream'})
    else:
        checks.append({'name': 'secondary_stream', 'passed': False, 'detail': 'Cannot read content'})

    # Check for payment flow
    if content:
        has_payment = fuzzy_contains(content, ['payment', 'stripe', 'checkout', 'billing', 'flow', 'gateway'])
        checks.append({'name': 'payment_flow', 'passed': has_payment, 'detail': 'Contains payment flow description' if has_payment else 'Missing payment flow'})
    else:
        checks.append({'name': 'payment_flow', 'passed': False, 'detail': 'Cannot read content'})

    # Check for 12-month projection
    if content:
        has_projection = fuzzy_contains(content, ['12-month', '12 month', 'projection', 'forecast', 'revenue', 'mrr', 'customer', 'growth'])
        checks.append({'name': 'projection', 'passed': has_projection, 'detail': 'Contains revenue projection' if has_projection else 'Missing 12-month projection'})
    else:
        checks.append({'name': 'projection', 'passed': False, 'detail': 'Cannot read content'})

    total = len(checks)
    passed = sum(1 for c in checks if c['passed'])
    score = passed / total if total else 0.0
    result = {'passed': passed == total and total > 0, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()