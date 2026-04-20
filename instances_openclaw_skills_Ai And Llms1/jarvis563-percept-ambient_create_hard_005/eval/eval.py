import json
import os
import re
from pathlib import Path


def norm(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum() or ch.isspace())
    except Exception:
        return ''


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def find_file_by_pattern(directory, patterns):
    """Find a file matching any of the given patterns (case-insensitive)."""
    if not directory.exists():
        return None
    for f in directory.iterdir():
        if f.is_file():
            fname = f.name.lower()
            for pattern in patterns:
                if pattern.lower() in fname:
                    return f
    return None


def main(workspace_dir):
    checks = []
    ws = Path(workspace_dir)
    out = ws / 'output'

    # Check 1: context packet exists and is valid JSON with expected project focus
    passed = False
    detail = ''
    try:
        candidates = [
            out / 'context_packet.json',
            out / 'context.json',
            out / 'context_packet_northstar.json',
            out / 'context_packet_Northstar.json',
            out / 'northstar_context.json'
        ]
        found = None
        for c in candidates:
            if c.exists():
                found = c
                break
        
        # Fallback: search for any file with "context" and "packet" or "northstar" in name
        if not found:
            found = find_file_by_pattern(out, ['context', 'packet', 'northstar'])
        
        if not found:
            detail = 'No context packet file found in output/'
        else:
            try:
                data = json.loads(found.read_text(encoding='utf-8'))
                blob = norm(json.dumps(data))
                passed = ('northstar' in blob) and ('orionlabs' in blob)
                detail = f'Loaded {found.name}; northstar/orion labs present={passed}'
            except Exception as e:
                detail = f'Invalid JSON in context packet: {e}'
    except Exception as e:
        detail = str(e)
    checks.append({'name': 'context packet generated', 'passed': passed, 'detail': detail})

    # Check 2: graph file exists and contains required edge types
    passed = False
    detail = ''
    try:
        candidates = [
            out / 'graph.json',
            out / 'relationship_graph.json',
            out / 'relationships.json',
            out / 'entity_graph.json'
        ]
        found = None
        for c in candidates:
            if c.exists():
                found = c
                break
        
        # Fallback: search for any file with "graph" or "relationship" in name
        if not found:
            found = find_file_by_pattern(out, ['graph', 'relationship'])
        
        if not found:
            detail = 'graph.json missing'
        else:
            try:
                graph = json.loads(found.read_text(encoding='utf-8'))
                blob = norm(json.dumps(graph))
                ok_edges = all(t in blob for t in ['workson', 'clientof', 'mentionedwith'])
                passed = ok_edges
                detail = f'{found.name} loaded; required edge types present={ok_edges}'
            except Exception as e:
                detail = f'Could not parse {found.name}: {e}'
    except Exception as e:
        detail = str(e)
    checks.append({'name': 'relationship graph contains required edges', 'passed': passed, 'detail': detail})

    # Check 3: summary file references most recent issue markers
    passed = False
    detail = ''
    try:
        candidates = [
            out / 'summary.txt',
            out / 'searchable_summary.json',
            out / 'summary.json',
            out / 'index_summary.json'
        ]
        found = None
        for c in candidates:
            if c.exists():
                found = c
                break
        
        # Fallback: search for any file with "summary" in name
        if not found:
            found = find_file_by_pattern(out, ['summary'])
        
        if not found:
            detail = 'summary file missing'
        else:
            try:
                text = found.read_text(encoding='utf-8')
                n = norm(text)
                passed = ('deadlineshift' in n or 'deadline shift' in n) and \
                         ('onboardingissue' in n or 'onboarding issue' in n or 'clientonboarding' in n) and \
                         ('northstar' in n)
                detail = f'{found.name} length={len(text)}; key phrases present={passed}'
            except Exception as e:
                detail = f'Could not read {found.name}: {e}'
    except Exception as e:
        detail = str(e)
    checks.append({'name': 'summary references recent issues', 'passed': passed, 'detail': detail})

    # Check 4: marker content was propagated somewhere in output
    passed = False
    detail = ''
    try:
        found_markers = []
        expected_markers = ['CONV-ALPHA-17', 'CONV-BETA-42', 'CONV-GAMMA-88']
        
        # Scan all files in output directory
        if out.exists():
            for f in out.iterdir():
                if f.is_file():
                    try:
                        content = f.read_text(encoding='utf-8').lower()
                        for marker in expected_markers:
                            if marker.lower() in content:
                                if marker not in found_markers:
                                    found_markers.append(marker)
                    except Exception:
                        continue
        
        passed = len(found_markers) >= 2
        detail = f'markers found in outputs: {found_markers}'
    except Exception as e:
        detail = str(e)
    checks.append({'name': 'markers propagated', 'passed': passed, 'detail': detail})

    score = (sum(1 for c in checks if c['passed'])) / (len(checks) or 1)
    passed = all(c['passed'] for c in checks)
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')