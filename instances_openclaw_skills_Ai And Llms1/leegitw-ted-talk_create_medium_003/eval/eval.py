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
        return path.read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)

try:
    out_path = workspace / 'output.txt'
    if not out_path.exists():
        add_check('output_exists', False, 'output.txt is missing')
        content = None
    else:
        content, err = safe_read(out_path)
        if content is None:
            add_check('output_exists', False, f'could not read output.txt: {err}')
        else:
            add_check('output_exists', True, 'output.txt found and readable')

    if content:
        lowered = content.lower()
        
        # TED-style title check - look for compelling headline structure
        # Accept titles that are catchy, have a hook, or mention TED explicitly
        title_patterns = [
            r'(?i)(ted\s*talk|ted-style\s*talk)',
            r'(?i)(the\s+real\s+|the\s+secret\s+|why\s+|how\s+|what\s+)',
            r'(?i)(\([^)]+\))',  # Has parenthetical subtitle
            r'(?i)(it\'s\s+not|it\s+is\s+not)',  # Has contrast structure
        ]
        title_match = any(re.search(p, content) for p in title_patterns)
        add_check('has_ted_title', title_match, 'contains a TED Talk style heading')
        
        # Flexible section checks using fuzzy matching
        add_check('has_opening_section', bool(re.search(r'(?i)(opening|hook|introduction|imagine\s+this)', lowered)), 'mentions an Opening/Hook section')
        add_check('has_problem_section', bool(re.search(r'(?i)(problem|challenge|issue|bottleneck|what\s+we\s+discovered)', lowered)), 'mentions a Problem section')
        # Check for insight content rather than section label
        insight_patterns = [
            r'(?i)(insight|breakthrough|realization|key\s*idea)',
            r'(?i)(the\s+real\s+bottleneck|the\s+real\s+speed\s+killer)',
            r'(?i)(decision\s+latency)',
        ]
        insight_match = any(re.search(p, lowered) for p in insight_patterns)
        add_check('has_insight_section', insight_match, 'mentions an Insight section')
        # Check for examples content rather than section label
        example_patterns = [
            r'(?i)(example|illustration|case\s*study)',
            r'(?i)(release\s+reviews|incident\s+retrospectives|small-scale\s+pilots)',
            r'(?i)(first:|second:|third:)',  # Numbered examples
        ]
        example_match = any(re.search(p, lowered) for p in example_patterns)
        add_check('has_examples_section', example_match, 'mentions an Examples section')
        add_check('has_qa_section', bool(re.search(r'(?i)(q\s*&\s*a|questions?\s*and\s*answers?|q[&]?a)', lowered)), 'mentions a Q&A section')
        add_check('has_closing_section', bool(re.search(r'(?i)(closing|conclusion|summary|final|end\s*of\s*talk|thank\s+you)', lowered)), 'mentions a Closing section')

        # Check for key concepts from input
        marker_hits = 0
        markers = ['decision latency', 'learning loops', 'three-stage rhythm', 'capture uncertainty', 'validate assumptions', 'codify the pattern']
        for marker in markers:
            if marker.lower() in lowered:
                marker_hits += 1
        add_check('uses_input_markers', marker_hits >= 3, f'found {marker_hits} expected context markers')

        # Check for concrete examples
        example_hits = 0
        examples = ['release reviews', 'incident retrospectives', 'small-scale pilots', 'retrospective', 'review']
        for ex in examples:
            if ex.lower() in lowered:
                example_hits += 1
        add_check('has_concrete_examples', example_hits >= 1, f'found {example_hits} concrete examples')

        word_count = len(re.findall(r'\w+', content))
        add_check('reasonable_length', word_count >= 300, f'word count is {word_count}, expected at least 300')
    else:
        for name in ['has_ted_title','has_opening_section','has_problem_section','has_insight_section','has_examples_section','has_qa_section','has_closing_section','uses_input_markers','has_concrete_examples','reasonable_length']:
            add_check(name, False, 'not evaluated because output.txt was missing or unreadable')
except Exception as e:
    add_check('eval_exception', False, f'unexpected evaluator error: {e}')

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))