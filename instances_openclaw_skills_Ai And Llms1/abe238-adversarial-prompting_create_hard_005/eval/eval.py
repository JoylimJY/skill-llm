import json
import re
import sys
from pathlib import Path


def main():
    checks = []
    workspace = Path(sys.argv[1]).resolve()

    # Check 1: expected markdown file exists - search multiple locations
    md_path = None
    try:
        # Search in workspace and subdirectories
        candidates = list(workspace.rglob('*.md'))
        # Also check for specific naming patterns
        candidates += list(workspace.rglob('*analysis*.md'))
        candidates += list(workspace.rglob('*adversarial*.md'))
        candidates += list(workspace.rglob('*deployment*.md'))
        
        # Filter out empty files
        candidates = [c for c in candidates if c.exists() and c.stat().st_size > 0]
        
        md_path = candidates[0] if candidates else None
        passed = md_path is not None
        checks.append({
            'name': 'markdown_output_exists',
            'passed': passed,
            'detail': f'found={md_path.name if md_path else None}'
        })
    except Exception as e:
        checks.append({'name': 'markdown_output_exists', 'passed': False, 'detail': f'error: {e}'})

    content = ''
    if md_path is not None:
        try:
            content = md_path.read_text(encoding='utf-8')
            checks.append({'name': 'markdown_readable', 'passed': True, 'detail': 'read successfully'})
        except Exception as e:
            content = ''
            checks.append({'name': 'markdown_readable', 'passed': False, 'detail': f'error: {e}'})
    else:
        checks.append({'name': 'markdown_readable', 'passed': False, 'detail': 'markdown file missing'})

    # Flexible regex patterns for content validation
    patterns = {
        'three_approaches': [
            r'\bthree\s+approach',
            r'\bapproach\s+\d',
            r'\bapproaches?\s*\d',
            r'\bapproach\s+1\b',
            r'\bapproach\s+2\b',
            r'\bapproach\s+3\b',
            r'\boption\s+\d',
            r'\bstrategy\s+\d',
            r'\b1\.\s*\w',
            r'\b2\.\s*\w',
            r'\b3\.\s*\w',
            r'\bblue-green',
            r'\bcanary',
            r'\bshadow'
        ],
        'adversarial_critique': [
            r'\badversarial\b',
            r'\bcritique\b',
            r'\battack\b',
            r'\bvulnerability\b',
            r'\bweakness\b',
            r'\brisk\b',
            r'\bthreat\b',
            r'\bfailure\s+mode\b',
            r'\bproblem\b',
            r'\bdownside\b',
            r'\bdrawback\b'
        ],
        'fix_development': [
            r'\bfix\b',
            r'\bmitigation\b',
            r'\bremediation\b',
            r'\bsolution\b',
            r'\baddress\b',
            r'\bresolve\b',
            r'\bimprovement\b',
            r'\brecommendation\b',
            r'\bmitigate\b',
            r'\bprevent\b'
        ],
        'validation_check': [
            r'\bvalidation\b',
            r'\btest\b',
            r'\bverify\b',
            r'\bcheck\b',
            r'\bmeasure\b',
            r'\bcriteria\b',
            r'\bmetric\b',
            r'\bmonitor\b',
            r'\bverify\b',
            r'\bconfirm\b'
        ],
        'consolidation': [
            r'\bconsolidation\b',
            r'\bsummary\b',
            r'\bconclusion\b',
            r'\boverview\b',
            r'\bsynthesis\b',
            r'\bexecutive\s+summary\b',
            r'\bkey\s+findings\b',
            r'\bhighlights\b'
        ],
        'ranked_options': [
            r'\brank\b',
            r'\bpriority\b',
            r'\boption\s+\d',
            r'\bchoice\s+\d',
            r'\b1\.\s*\w',
            r'\b2\.\s*\w',
            r'\b3\.\s*\w',
            r'\btop\s+choice\b',
            r'\bpreferred\b',
            r'\b1st\b',
            r'\b2nd\b',
            r'\b3rd\b'
        ],
        'final_recommendation': [
            r'\brecommendation\b',
            r'\brecommend\b',
            r'\bfinal\s+choice\b',
            r'\bconclusion\b',
            r'\bselected\b',
            r'\bchosen\b',
            r'\bwe\s+recommend\b',
            r'\bshould\s+use\b',
            r'\bgo\s+with\b',
            r'\bbest\s+option\b'
        ],
        'atlas_marker': [
            r'\batlas\s*[-\s]*delta\b',
            r'\batlas\s*[-\s]*77\b',
            r'\bATLAS-DELTA-77\b',
            r'\bATLAS\s+DELTA\b',
            r'\bmarker\b',
            r'\bAtlas\s+Delta\b'
        ]
    }

    passed_count = 0
    total_checks = len(checks)  # Start with file existence checks
    
    for name, pattern_list in patterns.items():
        try:
            # Check if ANY pattern matches (more flexible than requiring ALL)
            ok = any(re.search(p, content, re.IGNORECASE) for p in pattern_list)
            checks.append({'name': name, 'passed': ok, 'detail': f'patterns={len(pattern_list)}'})
            if ok:
                passed_count += 1
        except Exception as e:
            checks.append({'name': name, 'passed': False, 'detail': f'error: {e}'})

    total = len(checks)
    score = passed_count / total if total else 0.0
    
    # Pass if at least 70% of checks pass (more lenient)
    passed = total > 0 and passed_count >= (total * 0.7)

    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}))


if __name__ == '__main__':
    main()