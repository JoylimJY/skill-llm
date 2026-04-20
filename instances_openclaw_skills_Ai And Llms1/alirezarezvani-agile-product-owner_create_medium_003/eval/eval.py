from pathlib import Path
import json
import os
import re
import sys


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8'), None
    except Exception as e:
        return None, f'Could not read {path.name}: {e}'


def normalize(text: str) -> str:
    try:
        return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()
    except Exception:
        return ''


def fuzzy_contains(text: str, needles):
    nt = normalize(text)
    return all(normalize(n) in nt for n in needles)


def find_file(workspace: Path, base_name: str) -> Path:
    """Find a file with given base name, checking both .txt and .md extensions."""
    for ext in ['.txt', '.md']:
        path = workspace / f'{base_name}{ext}'
        if path.exists():
            return path
    return None


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    expected_base_names = [
        'epic_breakdown',
        'prioritized_backlog',
        'sprint_plan',
    ]

    for base_name in expected_base_names:
        path = find_file(workspace, base_name)
        if path:
            detail = f'exists ({path.name})'
            checks.append({'name': f'file_exists_{base_name}.txt', 'passed': True, 'detail': detail})
        else:
            detail = 'missing'
            checks.append({'name': f'file_exists_{base_name}.txt', 'passed': False, 'detail': detail})

    # Epic breakdown content
    try:
        path = find_file(workspace, 'epic_breakdown')
        if path:
            text, err = safe_read(path)
            if err:
                checks.append({'name': 'epic_breakdown_readable', 'passed': False, 'detail': err})
            else:
                ntext = normalize(text)
                has_epic = 'epic' in ntext
                has_export = 'export' in ntext
                has_persona = 'persona' in ntext or 'end user' in ntext or 'administrator' in ntext
                has_acceptance = 'acceptance criteria' in ntext or 'given when then' in ntext
                passed = has_epic and has_export and has_persona and has_acceptance
                checks.append({'name': 'epic_breakdown_content', 'passed': passed, 'detail': 'contains epic/export/persona and acceptance criteria' if passed else 'missing required elements'})
        else:
            checks.append({'name': 'epic_breakdown_readable', 'passed': False, 'detail': 'file not found'})
            checks.append({'name': 'epic_breakdown_content', 'passed': False, 'detail': 'file not found'})
    except Exception as e:
        checks.append({'name': 'epic_breakdown_content', 'passed': False, 'detail': f'exception: {e}'})

    # Backlog content - check for priority levels and story points
    try:
        path = find_file(workspace, 'prioritized_backlog')
        if path:
            text, err = safe_read(path)
            if err:
                checks.append({'name': 'prioritized_backlog_readable', 'passed': False, 'detail': err})
            else:
                ntext = normalize(text)
                # Check for priority levels - support both traditional and MoSCoW
                has_priority = any(p in ntext for p in ['critical', 'high', 'medium', 'low', 'must', 'should', 'could', 'wont'])
                # Check for story points - more flexible pattern
                has_story_points = bool(re.search(r'\b(?:1|2|3|5|8|13)\s*(?:pts?|points?)?\b', text, flags=re.I))
                passed = has_priority and has_story_points
                checks.append({'name': 'prioritized_backlog_content', 'passed': passed, 'detail': 'includes priority levels and story points' if passed else 'missing priority or points'})
        else:
            checks.append({'name': 'prioritized_backlog_readable', 'passed': False, 'detail': 'file not found'})
            checks.append({'name': 'prioritized_backlog_content', 'passed': False, 'detail': 'file not found'})
    except Exception as e:
        checks.append({'name': 'prioritized_backlog_content', 'passed': False, 'detail': f'exception: {e}'})

    # Sprint plan content
    try:
        path = find_file(workspace, 'sprint_plan')
        if path:
            text, err = safe_read(path)
            if err:
                checks.append({'name': 'sprint_plan_readable', 'passed': False, 'detail': err})
            else:
                ntext = normalize(text)
                has_capacity = '28' in ntext and ('pto' in ntext or 'availability' in ntext)
                has_two_week = '2 week' in ntext or 'two week' in ntext or 'sprint' in ntext
                has_committed = 'committed' in ntext or 'commitment' in ntext
                has_stretch = 'stretch' in ntext
                passed = has_capacity and has_two_week and has_committed and has_stretch
                checks.append({'name': 'sprint_plan_content', 'passed': passed, 'detail': 'mentions capacity, 2-week sprint, committed and stretch work' if passed else 'missing planning details'})
        else:
            checks.append({'name': 'sprint_plan_readable', 'passed': False, 'detail': 'file not found'})
            checks.append({'name': 'sprint_plan_content', 'passed': False, 'detail': 'file not found'})
    except Exception as e:
        checks.append({'name': 'sprint_plan_content', 'passed': False, 'detail': f'exception: {e}'})

    # Marker usage in at least one produced file
    try:
        any_marker = False
        for base_name in expected_base_names:
            path = find_file(workspace, base_name)
            if path:
                try:
                    content = path.read_text(encoding='utf-8')
                    if 'report export' in content.lower() or 'export' in content.lower():
                        any_marker = True
                        break
                except Exception:
                    pass
        checks.append({'name': 'semantic_alignment', 'passed': any_marker, 'detail': 'output references export initiative' if any_marker else 'output does not clearly reference initiative'})
    except Exception as e:
        checks.append({'name': 'semantic_alignment', 'passed': False, 'detail': f'exception: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': f'unhandled exception: {e}'}]}, ensure_ascii=False))