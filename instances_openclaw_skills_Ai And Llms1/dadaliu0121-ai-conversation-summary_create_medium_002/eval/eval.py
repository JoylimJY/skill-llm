import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def normalize(s):
    if not isinstance(s, str):
        return ''
    s = s.lower()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'[\W_]+', ' ', s)
    return s.strip()


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    checks = []

    def add_check(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        out_path = workspace / 'summary.json'
        if not out_path.exists():
            add_check('output_exists', False, 'summary.json is missing')
            result = {'passed': False, 'score': 0.0, 'checks': checks}
            print(json.dumps(result, ensure_ascii=False))
            return

        try:
            data = json.loads(out_path.read_text(encoding='utf-8'))
            add_check('valid_json', True, 'summary.json parsed successfully')
        except Exception as e:
            add_check('valid_json', False, f'Could not parse summary.json: {e}')
            data = {}

        # Extract fields from the summary - use correct field names
        main_topics = data.get('main_topics', []) if isinstance(data, dict) else []
        decisions = data.get('decisions', []) if isinstance(data, dict) else []
        action_items = data.get('action_items', []) if isinstance(data, dict) else []
        incremental = data.get('incremental', {}) if isinstance(data, dict) else {}

        chat_text, chat_err = safe_read_text(workspace / 'chat.json')
        history_text, hist_err = safe_read_text(workspace / 'history_summary.txt')

        if chat_text is None:
            add_check('input_chat_present', False, f'chat.json missing or unreadable: {chat_err}')
        else:
            add_check('input_chat_present', True, 'chat.json found')

        if history_text is None:
            add_check('input_history_present', False, f'history_summary.txt missing or unreadable: {hist_err}')
        else:
            add_check('input_history_present', True, 'history_summary.txt found')

        # Normalize all text for comparison
        ntopics = [normalize(t) for t in main_topics] if isinstance(main_topics, list) else []
        ndecisions = [normalize(d) for d in decisions] if isinstance(decisions, list) else []
        nactions = [normalize(a) for a in action_items] if isinstance(action_items, list) else []

        # Combine all text content for topic checking
        all_text = ' '.join(ntopics + ndecisions + nactions)
        if isinstance(incremental, dict):
            all_text += ' ' + ' '.join(str(v) for v in incremental.values())
        nall = normalize(all_text)

        # Check for required topics
        topic_hits = 0
        for needle in ['kyoto', 'budget', 'itinerary']:
            if needle in nall:
                topic_hits += 1
        add_check('summary_topics', topic_hits >= 2, f'topic hits: {topic_hits}/3')

        # Check for action items
        action_hit = any(('book' in a and 'friday' in a) or ('hotel' in a and 'friday' in a) for a in nactions)
        add_check('action_items', action_hit, 'found reminder to book hotels before Friday' if action_hit else 'missing booking reminder')

        # Check incremental field
        incremental_hit = False
        if isinstance(incremental, dict):
            inc_text = ' '.join(str(v) for v in incremental.values())
            ninc = normalize(inc_text)
            incremental_hit = 'budget' in ninc and 'kyoto' in ninc
        add_check('incremental_update', incremental_hit, 'incremental field references previous Kyoto budget context' if incremental_hit else 'incremental field does not reflect prior context')

        # Check marker - handle the actual format MARKER:KYOTO_SUMMARY_TASK_v1
        marker_ok = False
        try:
            marker = (workspace / 'marker.txt').read_text(encoding='utf-8')
            # Check for the task identifier in the marker (case-insensitive)
            marker_ok = 'kyoto_summary_task_v1' in normalize(marker) or 'kyoto' in normalize(marker) and 'summary' in normalize(marker) and 'task' in normalize(marker)
        except Exception as e:
            marker_ok = False
        add_check('marker_present', marker_ok, 'marker content verified' if marker_ok else 'marker missing or mismatched')

    except Exception as e:
        add_check('eval_internal_error', False, f'Unexpected evaluator error: {e}')

    passed_count = sum(1 for c in checks if c['passed'])
    total = len(checks) if checks else 1
    score = passed_count / total
    passed = passed_count == total
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()