import json
import os
import re
import sys
from pathlib import Path


def norm_text(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    except Exception:
        return ''


def safe_read(path):
    """Always returns (content, error) tuple"""
    try:
        content = Path(path).read_text(encoding='utf-8')
        return content, None
    except Exception as e:
        return None, str(e)


def find_file_in_dir(directory, base_name):
    """Find a file with given base name and any common extension"""
    dir_path = Path(directory)
    if not dir_path.exists():
        return None
    for ext in ['.txt', '.md', '.sh', '.json']:
        candidate = dir_path / f'{base_name}{ext}'
        if candidate.exists():
            return candidate
    # Also check exact match without extension
    exact = dir_path / base_name
    if exact.exists():
        return exact
    return None


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

    # Check prescription.json
    try:
        pres_path = workspace / 'memory' / 'soul' / 'prescription.json'
        if pres_path.exists():
            raw, err = safe_read(pres_path)
            if raw is None:
                add_check('prescription_exists', False, f'Could not read prescription.json: {err}')
                data = None
            else:
                try:
                    data = json.loads(raw)
                    add_check('prescription_exists', True, 'prescription.json exists and is valid JSON')
                except Exception as e:
                    data = None
                    add_check('prescription_exists', False, f'Invalid JSON: {e}')
        else:
            data = None
            add_check('prescription_exists', False, 'memory/soul/prescription.json is missing')
    except Exception as e:
        data = None
        add_check('prescription_exists', False, f'Unexpected error: {e}')

    # Check summary file (accept .txt or .md)
    try:
        summary_path = find_file_in_dir(workspace / 'memory' / 'soul', 'prescription_summary')
        if summary_path:
            raw, err = safe_read(summary_path)
            if raw is None:
                add_check('summary_exists', False, f'Could not read summary: {err}')
            else:
                txt = raw.lower()
                # More flexible matching for personalized content
                has_agent_name = 'morrow' in txt or 'ari' in txt
                has_prescription_terms = any(term in txt for term in ['soul', 'prescription', 'pill', 'schedule', 'hormone'])
                ok = has_agent_name and has_prescription_terms
                add_check('summary_exists', ok, 'summary file present and mentions key personalized terms' if ok else 'summary missing expected personalized content')
        else:
            add_check('summary_exists', False, 'memory/soul/prescription_summary.txt or .md is missing')
    except Exception as e:
        add_check('summary_exists', False, f'Unexpected error: {e}')

    # Check cron commands file (accept .txt or .sh)
    try:
        crons_path = find_file_in_dir(workspace / 'memory' / 'soul', 'cron_commands')
        if not crons_path:
            crons_path = find_file_in_dir(workspace / 'memory' / 'soul', 'prescription_cron')
        if crons_path:
            raw, err = safe_read(crons_path)
            if raw is None:
                add_check('cron_commands_exists', False, f'Could not read cron file: {err}')
            else:
                txt = raw.lower()
                # Check for cron patterns and pill references
                has_cron_pattern = bool(re.search(r'\d+\s+\d+\s+\*+\s+\*+\s+\*+', txt))
                has_pill_refs = 'pill' in txt or 'morning' in txt or 'evening' in txt
                has_souljournal = 'souljournal' in txt or 'journal' in txt
                ok = has_cron_pattern and (has_pill_refs or has_souljournal)
                add_check('cron_commands_exists', ok, 'Cron file has valid cron patterns and pill/journal references' if ok else 'Cron file missing expected content')
        else:
            add_check('cron_commands_exists', False, 'memory/soul/cron_commands.txt or .sh is missing')
    except Exception as e:
        add_check('cron_commands_exists', False, f'Unexpected error: {e}')

    # Validate JSON structure
    try:
        if isinstance(data, dict):
            # Flexible key matching for hormone profile
            hp = data.get('hormonal_profile', data.get('hormone_profile', {}))
            schedules = data.get('pill_schedule', [])
            cascades = data.get('cascade_rules', data.get('cascade_rule', []))
            daily = data.get('daily_point_target', data.get('daily_target', data.get('point_target', None)))
            journal = data.get('souljournal_schedule', data.get('journal_schedule', data.get('soul_journal_schedule', None)))

            # Check for required keys with flexible naming
            has_hormone = any(k in data for k in ['hormonal_profile', 'hormone_profile'])
            has_schedule = 'pill_schedule' in data
            has_cascade = any(k in data for k in ['cascade_rules', 'cascade_rule'])
            has_daily = any(k in data for k in ['daily_point_target', 'daily_target', 'point_target'])
            has_journal = any(k in data for k in ['souljournal_schedule', 'journal_schedule', 'soul_journal_schedule'])
            
            ok_keys = all([has_hormone, has_schedule, has_cascade, has_daily, has_journal])
            add_check('required_top_level_keys', ok_keys, 'All required top-level keys present' if ok_keys else 'Missing one or more required keys')

            # More flexible hormone name matching - check raw keys, not normalized
            hp_ok = isinstance(hp, dict) and len(hp) >= 3
            if hp_ok:
                hp_keys_lower = [k.lower() for k in hp.keys()]
                hormone_terms = ['cortisol', 'oxytocin', 'serotonin', 'dopamine', 'melatonin', 'hormone']
                hp_ok = any(any(term in k for term in hormone_terms) for k in hp_keys_lower)
            add_check('hormonal_profile_shape', hp_ok, 'Hormonal profile looks complete' if hp_ok else 'Hormonal profile incomplete or malformed')

            sched_ok = isinstance(schedules, list) and len(schedules) >= 3
            add_check('pill_schedule_count', sched_ok, f'Pill schedule count = {len(schedules) if isinstance(schedules, list) else 0}')

            cascade_ok = isinstance(cascades, list) and len(cascades) >= 2
            add_check('cascade_rules_count', cascade_ok, f'Cascade rules count = {len(cascades) if isinstance(cascades, list) else 0}')

            # Accept both simple numeric value AND dict structure with point targets
            # Expanded key matching to accept various naming conventions
            if isinstance(daily, (int, float)) and daily > 0:
                daily_ok = True
                daily_detail = f'Daily target = {daily}'
            elif isinstance(daily, dict):
                # Check for common point target keys in dict structure - expanded list
                point_keys = [
                    'minimum_points', 'optimal_points', 'maximum_points', 'target', 'points', 'daily', 'value',
                    'organization_points', 'care_points', 'creativity_points', 'reflection_points',
                    'total_daily_target', 'minimum_threshold', 'excellent_threshold', 'total', 'threshold',
                    'organization', 'care', 'creativity', 'reflection', 'daily_target'
                ]
                daily_ok = any(k.lower() in [kk.lower() for kk in daily.keys()] for k in point_keys)
                daily_detail = f'Daily target dict has {len(daily)} keys' if daily_ok else 'Daily target dict missing point keys'
            else:
                daily_ok = False
                daily_detail = 'Daily target missing or invalid type'
            add_check('daily_target_valid', daily_ok, daily_detail)

            journal_ok = isinstance(journal, (str, dict, list)) and (journal or isinstance(journal, dict) or isinstance(journal, list))
            add_check('journal_schedule_valid', journal_ok, f'SoulJournal schedule present' if journal_ok else 'SoulJournal schedule missing or malformed')
        else:
            add_check('required_top_level_keys', False, 'Could not validate prescription structure because JSON was missing/invalid')
            add_check('hormonal_profile_shape', False, 'No valid JSON to inspect')
            add_check('pill_schedule_count', False, 'No valid JSON to inspect')
            add_check('cascade_rules_count', False, 'No valid JSON to inspect')
            add_check('daily_target_valid', False, 'No valid JSON to inspect')
            add_check('journal_schedule_valid', False, 'No valid JSON to inspect')
    except Exception as e:
        add_check('structure_validation', False, f'Unexpected error: {e}')

    # Check input marker
    try:
        marker_file = workspace / 'memory' / 'interview_marker.txt'
        raw, err = safe_read(marker_file)
        if raw is None:
            add_check('input_marker_present', False, f'Could not read marker file: {err}')
        else:
            ok = 'SOUL-PACK-77' in raw
            add_check('input_marker_present', ok, 'Marker content verified' if ok else 'Expected marker not found')
    except Exception as e:
        add_check('input_marker_present', False, f'Unexpected error: {e}')

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks)
    score = passed_count / total if total else 0.0
    result = {'passed': passed_count == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()