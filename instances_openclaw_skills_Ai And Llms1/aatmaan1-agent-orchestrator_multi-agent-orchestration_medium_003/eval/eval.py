import sys
import os
import json
import re

def load_json_safe(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        return None

def read_file_safe(path):
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            return f.read()
    except Exception:
        return None

def find_file_recursive(base_dir, filename_pattern):
    """Search recursively for files matching a pattern."""
    matches = []
    try:
        for root, dirs, files in os.walk(base_dir):
            for fname in files:
                if re.search(filename_pattern, fname, re.IGNORECASE):
                    matches.append(os.path.join(root, fname))
    except Exception:
        pass
    return matches

def fuzzy_contains(text, keyword):
    if text is None:
        return False
    return keyword.lower().strip() in text.lower().strip()

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    checks = []

    # --- Check 1: data-collector outbox has competitor extraction output ---
    try:
        collector_outbox = os.path.join(workspace, 'agents', 'data-collector', 'outbox')
        collector_files = os.listdir(collector_outbox) if os.path.isdir(collector_outbox) else []
        has_collector_output = len(collector_files) > 0
        if has_collector_output:
            # look for any file with competitor data
            found_competitor = False
            for fname in collector_files:
                content = read_file_safe(os.path.join(collector_outbox, fname))
                if content and (fuzzy_contains(content, 'AlphaCorp') or fuzzy_contains(content, 'BetaTech') or fuzzy_contains(content, 'GammaSystems')):
                    found_competitor = True
                    break
            checks.append({
                'name': 'data_collector_extracted_competitors',
                'passed': found_competitor,
                'detail': f'Collector outbox has {len(collector_files)} file(s); competitor names found: {found_competitor}'
            })
        else:
            checks.append({
                'name': 'data_collector_extracted_competitors',
                'passed': False,
                'detail': 'data-collector outbox is empty or missing'
            })
    except Exception as e:
        checks.append({'name': 'data_collector_extracted_competitors', 'passed': False, 'detail': str(e)})

    # --- Check 2: data-collector status.json shows completed ---
    try:
        status_path = os.path.join(workspace, 'agents', 'data-collector', 'status.json')
        status = load_json_safe(status_path)
        if status is None:
            # also search recursively
            found = find_file_recursive(os.path.join(workspace, 'agents', 'data-collector'), r'status\.json')
            if found:
                status = load_json_safe(found[0])
        passed = status is not None and str(status.get('state', '')).lower() == 'completed'
        checks.append({
            'name': 'data_collector_status_completed',
            'passed': passed,
            'detail': f'status.json state: {status.get("state") if status else "file missing"}'
        })
    except Exception as e:
        checks.append({'name': 'data_collector_status_completed', 'passed': False, 'detail': str(e)})

    # --- Check 3: analyst outbox has trend analysis with at least 3 trends ---
    try:
        analyst_outbox = os.path.join(workspace, 'agents', 'analyst', 'outbox')
        analyst_files = os.listdir(analyst_outbox) if os.path.isdir(analyst_outbox) else []
        trend_keywords = ['ai_integration', 'edge_computing', 'security', 'cost_optim', 'multi_cloud', 'ai integration', 'edge computing', 'cost optimization', 'multi cloud']
        trends_found = 0
        for fname in analyst_files:
            content = read_file_safe(os.path.join(analyst_outbox, fname))
            if content:
                for kw in trend_keywords:
                    if fuzzy_contains(content, kw):
                        trends_found += 1
        # deduplicate by checking unique trend mentions
        all_content = ''
        for fname in analyst_files:
            c = read_file_safe(os.path.join(analyst_outbox, fname))
            if c:
                all_content += c.lower()
        unique_trends = sum(1 for kw in ['ai', 'edge', 'security', 'cost', 'multi'] if kw in all_content)
        passed = len(analyst_files) > 0 and unique_trends >= 3
        checks.append({
            'name': 'analyst_identified_top_trends',
            'passed': passed,
            'detail': f'Analyst outbox has {len(analyst_files)} file(s); unique trend categories found: {unique_trends}'
        })
    except Exception as e:
        checks.append({'name': 'analyst_identified_top_trends', 'passed': False, 'detail': str(e)})

    # --- Check 4: analyst status.json shows completed ---
    try:
        status_path = os.path.join(workspace, 'agents', 'analyst', 'status.json')
        status = load_json_safe(status_path)
        if status is None:
            found = find_file_recursive(os.path.join(workspace, 'agents', 'analyst'), r'status\.json')
            if found:
                status = load_json_safe(found[0])
        passed = status is not None and str(status.get('state', '')).lower() == 'completed'
        checks.append({
            'name': 'analyst_status_completed',
            'passed': passed,
            'detail': f'status.json state: {status.get("state") if status else "file missing"}'
        })
    except Exception as e:
        checks.append({'name': 'analyst_status_completed', 'passed': False, 'detail': str(e)})

    # --- Check 5: writer outbox has a draft/report ---
    try:
        writer_outbox = os.path.join(workspace, 'agents', 'writer', 'outbox')
        writer_files = os.listdir(writer_outbox) if os.path.isdir(writer_outbox) else []
        has_report = any(re.search(r'(report|draft|analysis)', f, re.IGNORECASE) for f in writer_files)
        if not has_report and len(writer_files) > 0:
            has_report = True  # any output counts
        checks.append({
            'name': 'writer_produced_draft',
            'passed': has_report,
            'detail': f'Writer outbox files: {writer_files}'
        })
    except Exception as e:
        checks.append({'name': 'writer_produced_draft', 'passed': False, 'detail': str(e)})

    # --- Check 6: final_report.md exists and has meaningful content ---
    try:
        # search in workspace root and subdirs
        candidates = find_file_recursive(workspace, r'final_report\.md')
        if not candidates:
            # also check for any *report*.md
            candidates = find_file_recursive(workspace, r'.*report.*\.md')
        found_report = None
        for c in candidates:
            content = read_file_safe(c)
            if content and len(content.strip()) > 100:
                found_report = content
                break
        passed = found_report is not None
        checks.append({
            'name': 'final_report_exists',
            'passed': passed,
            'detail': f'final_report.md found: {passed}; candidates: {candidates[:3]}'
        })
    except Exception as e:
        checks.append({'name': 'final_report_exists', 'passed': False, 'detail': str(e)})

    # --- Check 7: final_report.md references competitor names ---
    try:
        candidates = find_file_recursive(workspace, r'final_report\.md')
        if not candidates:
            candidates = find_file_recursive(workspace, r'.*report.*\.md')
        report_content = ''
        for c in candidates:
            content = read_file_safe(c)
            if content and len(content.strip()) > 100:
                report_content = content
                break
        competitors_mentioned = sum(1 for name in ['AlphaCorp', 'BetaTech', 'GammaSystems', 'DeltaCloud'] if fuzzy_contains(report_content, name))
        passed = competitors_mentioned >= 2
        checks.append({
            'name': 'final_report_mentions_competitors',
            'passed': passed,
            'detail': f'Competitor names found in report: {competitors_mentioned}/4'
        })
    except Exception as e:
        checks.append({'name': 'final_report_mentions_competitors', 'passed': False, 'detail': str(e)})

    # --- Check 8: final_report.md mentions trends ---
    try:
        candidates = find_file_recursive(workspace, r'final_report\.md')
        if not candidates:
            candidates = find_file_recursive(workspace, r'.*report.*\.md')
        report_content = ''
        for c in candidates:
            content = read_file_safe(c)
            if content and len(content.strip()) > 100:
                report_content = content
                break
        trend_hits = sum(1 for kw in ['trend', 'ai', 'edge', 'security', 'growth'] if fuzzy_contains(report_content, kw))
        passed = trend_hits >= 3
        checks.append({
            'name': 'final_report_mentions_trends',
            'passed': passed,
            'detail': f'Trend-related keywords found: {trend_hits}'
        })
    except Exception as e:
        checks.append({'name': 'final_report_mentions_trends', 'passed': False, 'detail': str(e)})

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total > 0 else 0.0

    result = {
        'passed': score >= 0.75,
        'score': round(score, 4),
        'checks': checks
    }
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
