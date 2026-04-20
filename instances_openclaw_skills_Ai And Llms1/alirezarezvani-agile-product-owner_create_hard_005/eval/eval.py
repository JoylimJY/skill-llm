import json
import os
import re
import sys
from pathlib import Path


def norm(s):
    try:
        return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()
    except Exception:
        return ''


def safe_read(path):
    """Always returns a tuple (text, error)"""
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore'), None
    except Exception as e:
        return None, str(e)


def find_json_package(ws):
    """Find any JSON package file in workspace"""
    json_files = list(ws.glob('*.json'))
    for f in json_files:
        if 'backlog' in f.name.lower() or 'sprint' in f.name.lower() or 'package' in f.name.lower():
            return f
    return ws / 'backlog_package.json'


def find_sprint_plan(ws):
    """Find sprint plan file"""
    candidates = [
        ws / 'sprint_plan.md',
        ws / 'sprint_planning_package.json',
        ws / 'sprint.md',
    ]
    for c in candidates:
        if c.exists():
            return c
    return ws / 'sprint_plan.md'


def find_epic_breakdown(ws):
    """Find epic breakdown file"""
    candidates = [
        ws / 'epic_breakdown.md',
        ws / 'epic.md',
        ws / 'backlog_package.json',
    ]
    for c in candidates:
        if c.exists():
            return c
    return ws / 'epic_breakdown.md'


def main():
    checks = []
    ws = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    # Find files flexibly
    package_file = find_json_package(ws)
    sprint_file = find_sprint_plan(ws)
    epic_file = find_epic_breakdown(ws)

    # Check if any relevant files exist
    json_exists = package_file.exists()
    sprint_exists = sprint_file.exists()
    epic_exists = epic_file.exists()

    add('file_exists::backlog_package.json', json_exists, f"{'found' if json_exists else 'missing'}")
    add('file_exists::sprint_plan.md', sprint_exists, f"{'found' if sprint_exists else 'missing'}")
    add('file_exists::epic_breakdown.md', epic_exists, f"{'found' if epic_exists else 'missing'}")

    package = {}
    try:
        text, err = safe_read(package_file)
        if text is None:
            add('package_parse', False, f'read failed: {err}')
        else:
            try:
                package = json.loads(text)
                add('package_parse', True, 'json parsed')
            except Exception as e:
                add('package_parse', False, f'json error: {e}')
    except Exception as e:
        add('package_parse_outer', False, f'exception: {e}')

    marker_found = False
    try:
        marker = 'po-marker-7f3a'
        marker_alt = 'po marker 7f3a'
        blob = ''
        
        # Check all files for marker
        for f in [package_file, sprint_file, epic_file]:
            if f.exists():
                text, _ = safe_read(f)
                if text:
                    blob += '\n' + text.lower()
        
        # Also check package dict if parsed
        if package:
            blob += '\n' + json.dumps(package).lower()
        
        marker_found = marker in norm(blob) or marker_alt in norm(blob) or 'po-marker-7f3a' in blob.lower()
        add('marker_preserved', marker_found, 'marker present' if marker_found else 'marker missing')
    except Exception as e:
        add('marker_preserved', False, f'exception: {e}')

    try:
        # Look for stories in various possible keys
        stories = []
        if isinstance(package, dict):
            for key in ['stories', 'user_stories', 'backlog', 'items', 'story_list']:
                if key in package and isinstance(package[key], list):
                    stories = package[key]
                    break
            # Also check if stories is a direct list
            if not stories and isinstance(package.get('stories'), list):
                stories = package['stories']
        
        story_ok = isinstance(stories, list) and len(stories) >= 4
        add('story_count', story_ok, f'count={len(stories) if isinstance(stories, list) else "n/a"}')
    except Exception as e:
        add('story_count', False, f'exception: {e}')
        stories = []

    try:
        point_sum = 0
        bad_points = []
        for s in stories if isinstance(stories, list) else []:
            pts = None
            if isinstance(s, dict):
                for key in ['points', 'story_points', 'estimate', 'estimation']:
                    if key in s:
                        pts = s[key]
                        break
            try:
                if pts is not None:
                    p = int(pts)
                    point_sum += p
                    if p > 8:
                        bad_points.append(p)
            except Exception:
                if pts is not None:
                    bad_points.append(str(pts))
        add('points_cap', len(bad_points) == 0, f"{'all stories <=8' if not bad_points else 'invalid points: ' + ','.join(map(str,bad_points))}")
    except Exception as e:
        add('points_cap', False, f'exception: {e}')
        point_sum = 0

    try:
        # Look for sprint/capacity info in various keys - FIXED to include sprint_capacity
        sprint = {}
        if isinstance(package, dict):
            for key in ['sprint', 'sprint_plan', 'capacity', 'team_capacity', 'sprint_capacity', 'capacity_info']:
                if key in package and isinstance(package[key], dict):
                    sprint = package[key]
                    break
        
        committed = 0
        capacity = 0
        for key in ['committed_points', 'committed', 'points_committed', 'committed_capacity']:
            if key in sprint:
                try:
                    committed = int(sprint[key])
                except:
                    pass
                break
        
        for key in ['capacity_points', 'effective_capacity_points', 'capacity', 'total_capacity', 'effective_capacity']:
            if key in sprint:
                try:
                    capacity = int(sprint[key])
                except:
                    pass
                break
        
        threshold = int(capacity * 0.85) if capacity else 0
        ok = capacity > 0 and committed <= threshold
        add('capacity_rule', ok, f'capacity={capacity}, committed={committed}, threshold={threshold}')
    except Exception as e:
        add('capacity_rule', False, f'exception: {e}')

    try:
        plan_text, err = safe_read(sprint_file)
        if plan_text is None:
            add('sprint_plan_content', False, f'read failed: {err}')
        else:
            nt = norm(plan_text)
            has_goal = 'sprint goal' in nt or 'goal' in nt or 'objective' in nt
            has_committed = 'committed' in nt or 'commit' in nt
            has_stretch = 'stretch' in nt or 'buffer' in nt or 'remaining' in nt
            add('sprint_plan_content', has_goal and has_committed and has_stretch, f'goal={has_goal}, committed={has_committed}, stretch={has_stretch}')
    except Exception as e:
        add('sprint_plan_content', False, f'exception: {e}')

    try:
        epic_text, err = safe_read(epic_file)
        if epic_text is None:
            add('epic_breakdown_content', False, f'read failed: {err}')
        else:
            nt = norm(epic_text)
            has_individual = 'standalone' in nt or 'independent' in nt or 'invest' in nt
            has_value = 'value' in nt or 'benefit' in nt
            has_sequence = 'dependency' in nt or 'sequence' in nt or 'order' in nt or 'priority' in nt
            add('epic_breakdown_content', has_individual and has_value and has_sequence, f'independent={has_individual}, value={has_value}, sequence={has_sequence}')
    except Exception as e:
        add('epic_breakdown_content', False, f'exception: {e}')

    passed = all(c['passed'] for c in checks)
    score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
    result = {'passed': passed, 'score': score, 'checks': checks}
    print(json.dumps(result))

if __name__ == '__main__':
    main()