import json
import os
import re
from pathlib import Path

workspace = Path(os.sys.argv[1]) if len(os.sys.argv) > 1 else Path('.')
checks = []

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

try:
    out_dir = workspace / 'output' / 'safety'
    
    # Find all files in output/safety directory
    all_files = []
    if out_dir.exists():
        all_files = list(out_dir.glob('*'))
    
    # Check 1: required output files exist (at least one file should exist)
    has_files = len(all_files) > 0
    add_check(
        'required output files exist',
        has_files,
        f'Found {len(all_files)} file(s)' if has_files else 'No files found in output/safety directory'
    )
    
    # Read all file contents for content checks
    all_content = ''
    for f in all_files:
        if f.is_file():
            try:
                all_content += f.read_text(encoding='utf-8', errors='replace') + '\n'
            except:
                pass
    
    # Check 2: model verification content
    # Look for model-related checks with PASS/FAIL status or model pinning keywords
    norm = re.sub(r'[^a-z0-9]+', ' ', all_content.lower())
    model_ok = (
        ('model' in norm) and 
        (
            ('pinning' in norm) or 
            ('pinned' in norm) or 
            ('model_pinning' in norm) or
            ('model' in norm and 'pass' in norm) or
            ('expected' in norm) or
            ('strict' in norm) or
            ('anthropic' in norm) or
            ('opus' in norm)
        )
    )
    add_check('model verification content', model_ok, 'Found model-related content' if model_ok else 'Model log missing expected keywords or markers')
    
    # Check 3: fallback verification content
    # Look for fallback-related checks with PASS/FAIL status or fallback keywords
    fallback_ok = (
        ('fallback' in norm) and 
        (
            ('declaration' in norm) or 
            ('fallbacks' in norm) or
            ('fallback_declarations' in norm) or
            ('primary' in norm) or
            ('backup' in norm) or
            ('storage' in norm) or
            ('fallback' in norm and 'pass' in norm)
        )
    )
    add_check('fallback verification content', fallback_ok, 'Found fallback-related content' if fallback_ok else 'Fallback log missing expected keywords or markers')
    
    # Check 4: session hygiene content
    session_ok = (
        (('session' in norm) or ('hygiene' in norm) or ('lock' in norm) or ('orphan' in norm)) and 
        (
            ('clean' in norm) or ('stale' in norm) or ('artifact' in norm) or ('pid' in norm) or ('temp' in norm) or
            ('cross_session_hygiene' in norm) or
            ('session' in norm and 'pass' in norm) or
            ('session' in norm and 'fail' in norm)
        )
    )
    add_check('session hygiene content', session_ok, 'Found session-related content' if session_ok else 'Session log missing expected keywords or markers')
    
    # Check 5: cache staleness content
    cache_ok = (
        ('cache' in norm) and 
        (
            ('stale' in norm) or ('fresh' in norm) or ('ttl' in norm) or ('age' in norm) or ('staleness' in norm) or ('seconds' in norm) or
            ('cache_staleness' in norm) or
            ('cache' in norm and 'pass' in norm) or
            ('cache' in norm and 'fail' in norm)
        )
    )
    add_check('cache staleness content', cache_ok, 'Found cache-related content' if cache_ok else 'Cache summary missing expected keywords or markers')
    
except Exception as e:
    add_check('evaluation', False, f'Error during evaluation: {e}')

try:
    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = (passed_count / total) if total else 0.0
    result = {
        'passed': passed_count == total,
        'score': score,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))
except Exception as e:
    fallback = {
        'passed': False,
        'score': 0.0,
        'checks': checks + [{'name': 'finalization', 'passed': False, 'detail': f'Failed to finalize results: {e}'}],
    }
    print(json.dumps(fallback, ensure_ascii=False))