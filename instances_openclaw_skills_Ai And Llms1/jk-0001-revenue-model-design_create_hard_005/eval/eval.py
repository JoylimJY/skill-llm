import json
import os
import re
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def normalize(s):
    if s is None:
        return ''
    return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()


def main(workspace):
    ws = Path(workspace)
    checks = []
    score = 0.0

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        out = ws / 'revenue_model_plan.md'
        if not out.exists():
            add_check('output_exists', False, 'revenue_model_plan.md is missing')
        else:
            text = out.read_text(encoding='utf-8', errors='ignore')
            ntext = normalize(text)
            required_phrases = [
                'subscription',
                'course',
                'consulting',
                'payment flow',
                '12 month',
                'validation plan',
                'risks and mitigations'
            ]
            missing = [p for p in required_phrases if normalize(p) not in ntext]
            add_check('contains_required_sections', len(missing) == 0, 'missing: ' + ', '.join(missing) if missing else 'all required sections found')

            # Payment-flow table heuristic
            table_hits = sum(1 for pat in ['price', 'billing', 'cancellation', 'upgrade'] if pat in ntext)
            add_check('payment_flow_detail', table_hits >= 3, f'found {table_hits}/4 payment-flow signals')

            # Projection heuristic
            year_hits = sum(1 for m in ['month 1', 'month 3', 'month 6', 'month 12'] if m in ntext)
            add_check('projection_table', year_hits >= 4, f'found {year_hits}/4 month markers')

            # Validation experiments
            val_hits = sum(1 for pat in ['pre-sales', 'fake checkout', 'manual first version', 'founding member'] if pat in ntext)
            add_check('validation_experiments', val_hits >= 3, f'found {val_hits}/4 validation signals')
    except Exception as e:
        add_check('general_error', False, f'evaluator exception: {e}')

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks) if checks else 1
    score = passed_count / total
    passed = passed_count == total and total > 0
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
