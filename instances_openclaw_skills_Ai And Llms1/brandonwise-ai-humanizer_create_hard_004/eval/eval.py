import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f'could not read {path.name}: {e}'


def norm(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9\s]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

try:
    out_path = workspace / 'output.txt'
    summary_path = workspace / 'summary.md'
    draft_path = workspace / 'draft.txt'

    out_text = None
    summary_text = None
    draft_text = None

    if out_path.exists():
        try:
            out_text = out_path.read_text(encoding='utf-8')
        except Exception as e:
            add_check('output readable', False, f'output.txt unreadable: {e}')
    else:
        add_check('output exists', False, 'output.txt is missing')

    if summary_path.exists():
        try:
            summary_text = summary_path.read_text(encoding='utf-8')
        except Exception as e:
            add_check('summary readable', False, f'summary.md unreadable: {e}')
    else:
        add_check('summary exists', False, 'summary.md is missing')

    if draft_path.exists():
        try:
            draft_text = draft_path.read_text(encoding='utf-8')
        except Exception as e:
            add_check('draft readable', False, f'draft.txt unreadable: {e}')
    else:
        add_check('draft exists', False, 'draft.txt is missing')

    if out_text is not None and draft_text is not None:
        nout = norm(out_text)
        ndraft = norm(draft_text)
        bad_phrases = [
            'in today s rapidly evolving landscape',
            'serves as a testament',
            'crucial role',
            'it is worth noting',
            'despite challenges',
            'the future looks bright',
            'experts believe',
            'holistic',
            'multifaceted',
            'seamless ecosystem',
        ]
        removed = sum(1 for p in bad_phrases if p not in nout)
        add_check('removed ai-style filler', removed >= 7, f'{removed}/10 target phrases absent from output')

        # Check for marker using regex to handle both underscore and space variations
        marker_pattern = r'marker\s*pilot\s*4821'
        marker_present = bool(re.search(marker_pattern, nout, re.IGNORECASE))
        add_check('kept required statistic marker', marker_present, 'MARKER_PILOT_4821 should be preserved or clearly referenced')

        source_marker_absent = 'marker_summary_4821' not in nout
        add_check('did not copy notes marker', source_marker_absent, 'MARKER_SUMMARY_4821 should not appear in output')

        length_ok = len(out_text.strip()) > 0 and len(out_text) < max(20, len(draft_text) * 2)
        add_check('reasonable output length', length_ok, f'output length={len(out_text.strip()) if out_text else 0}, draft length={len(draft_text)}')
    else:
        if out_text is None:
            add_check('removed ai-style filler', False, 'cannot check without output.txt')
            add_check('kept required statistic marker', False, 'cannot check without output.txt')
            add_check('did not copy notes marker', False, 'cannot check without output.txt')
            add_check('reasonable output length', False, 'cannot check without output.txt')

    if summary_text is not None:
        nsum = norm(summary_text)
        has_changes = any(k in nsum for k in ['changed', 'removed', 'rewrote', 'simplified', 'tone', 'concrete', 'jargon', 'hype', 'filler'])
        add_check('summary describes changes', has_changes, 'summary.md should mention the edits made')
        # Check if summary references the output file OR describes the transformation work
        # More flexible: check for output filename OR evidence of describing the rewrite work
        mentions_output = 'output.txt' in nsum or 'output' in nsum or 'produced' in nsum or 'created' in nsum
        # Also pass if summary clearly describes the rewrite/transformation work (e.g., mentions draft, rewrite, version, text, etc.)
        describes_work = any(k in nsum for k in ['draft', 'rewrite', 'version', 'text', 'original', 'new', 'final', 'result'])
        mentions_output_or_work = mentions_output or describes_work
        add_check('summary references output', mentions_output_or_work, 'summary.md should reference output.txt or describe what was produced')
    else:
        add_check('summary describes changes', False, 'cannot check without summary.md')
        add_check('summary references output', False, 'cannot check without summary.md')

except Exception as e:
    add_check('evaluation harness', False, f'unexpected evaluator error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {"passed": passed_count == len(checks) and len(checks) > 0, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))