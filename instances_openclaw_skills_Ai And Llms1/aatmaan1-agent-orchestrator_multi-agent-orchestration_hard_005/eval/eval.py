import sys
import os
import json
import re

def normalize(text):
    try:
        return re.sub(r'[\s\W]+', '', text).lower()
    except Exception:
        return ''

def fuzzy_contains(text, keyword):
    try:
        return keyword.lower() in text.lower()
    except Exception:
        return False

checks = []

workspace = sys.argv[1] if len(sys.argv) > 1 else '.'

# Check 1: Agent workspaces exist (check both /workspace/agent and /workspace/agents/agent)
agent_names = ['data-collector', 'analyst', 'writer', 'reviewer']
agents_found = []
agent_paths = {}

for agent in agent_names:
    # Try direct path first
    direct_path = os.path.join(workspace, agent)
    nested_path = os.path.join(workspace, 'agents', agent)
    
    if os.path.isdir(direct_path):
        agents_found.append(agent)
        agent_paths[agent] = direct_path
    elif os.path.isdir(nested_path):
        agents_found.append(agent)
        agent_paths[agent] = nested_path

agent_check_passed = len(agents_found) == 4
checks.append({
    'name': 'all_agent_workspaces_exist',
    'passed': agent_check_passed,
    'detail': f'Found agent dirs: {agents_found}. Expected all 4: {agent_names}'
})

# Check 2: Each agent has SKILL.md
skill_files_found = []
for agent in agent_names:
    if agent not in agent_paths:
        continue
    skill_path = os.path.join(agent_paths[agent], 'SKILL.md')
    if os.path.isfile(skill_path):
        skill_files_found.append(agent)

skill_check_passed = len(skill_files_found) == 4
checks.append({
    'name': 'all_agents_have_skill_md',
    'passed': skill_check_passed,
    'detail': f'Agents with SKILL.md: {skill_files_found}'
})

# Check 3: Each agent has inbox/instructions.md
inbox_found = []
for agent in agent_names:
    if agent not in agent_paths:
        continue
    inbox_path = os.path.join(agent_paths[agent], 'inbox', 'instructions.md')
    if os.path.isfile(inbox_path):
        inbox_found.append(agent)

inbox_check_passed = len(inbox_found) == 4
checks.append({
    'name': 'all_agents_have_inbox_instructions',
    'passed': inbox_check_passed,
    'detail': f'Agents with inbox/instructions.md: {inbox_found}'
})

# Check 4: Each agent has status.json with state=completed or status=completed
status_completed = []
for agent in agent_names:
    if agent not in agent_paths:
        continue
    status_path = os.path.join(agent_paths[agent], 'status.json')
    try:
        with open(status_path, 'r') as f:
            status = json.load(f)
        if isinstance(status, dict):
            # Check both 'state' and 'status' fields
            state_val = status.get('state', '').lower()
            status_val = status.get('status', '').lower()
            if state_val == 'completed' or status_val == 'completed':
                status_completed.append(agent)
    except Exception:
        pass

status_check_passed = len(status_completed) == 4
checks.append({
    'name': 'all_agents_status_completed',
    'passed': status_check_passed,
    'detail': f'Agents with completed status: {status_completed}'
})

# Check 5: data-collector outbox has findings
collector_outbox = os.path.join(agent_paths.get('data-collector', 'data-collector'), 'outbox')
collector_findings_found = False
collector_detail = 'data-collector outbox missing or empty'
try:
    if os.path.isdir(collector_outbox):
        files = os.listdir(collector_outbox)
        if files:
            collector_findings_found = True
            collector_detail = f'data-collector outbox contains: {files}'
        else:
            collector_detail = 'data-collector outbox exists but is empty'
except Exception as e:
    collector_detail = f'Error reading data-collector outbox: {e}'

checks.append({
    'name': 'data_collector_produced_output',
    'passed': collector_findings_found,
    'detail': collector_detail
})

# Check 6: analyst outbox has insights
analyst_outbox = os.path.join(agent_paths.get('analyst', 'analyst'), 'outbox')
analyst_found = False
analyst_detail = 'analyst outbox missing or empty'
try:
    if os.path.isdir(analyst_outbox):
        files = os.listdir(analyst_outbox)
        if files:
            analyst_found = True
            analyst_detail = f'analyst outbox contains: {files}'
        else:
            analyst_detail = 'analyst outbox exists but is empty'
except Exception as e:
    analyst_detail = f'Error reading analyst outbox: {e}'

checks.append({
    'name': 'analyst_produced_output',
    'passed': analyst_found,
    'detail': analyst_detail
})

# Check 7: writer outbox has draft
writer_outbox = os.path.join(agent_paths.get('writer', 'writer'), 'outbox')
writer_found = False
writer_detail = 'writer outbox missing or empty'
try:
    if os.path.isdir(writer_outbox):
        files = os.listdir(writer_outbox)
        if files:
            writer_found = True
            writer_detail = f'writer outbox contains: {files}'
        else:
            writer_detail = 'writer outbox exists but is empty'
except Exception as e:
    writer_detail = f'Error reading writer outbox: {e}'

checks.append({
    'name': 'writer_produced_output',
    'passed': writer_found,
    'detail': writer_detail
})

# Check 8: reviewer outbox has approved.json
reviewer_outbox = os.path.join(agent_paths.get('reviewer', 'reviewer'), 'outbox')
reviewer_approved_found = False
reviewer_detail = 'reviewer outbox missing or no approved.json'
try:
    if os.path.isdir(reviewer_outbox):
        files = os.listdir(reviewer_outbox)
        for fname in files:
            if 'approved' in fname.lower() and fname.endswith('.json'):
                reviewer_approved_found = True
                reviewer_detail = f'Found reviewer approval file: {fname}'
                break
        if not reviewer_approved_found:
            reviewer_detail = f'reviewer outbox has files {files} but no approved.json'
except Exception as e:
    reviewer_detail = f'Error reading reviewer outbox: {e}'

checks.append({
    'name': 'reviewer_produced_approved_json',
    'passed': reviewer_approved_found,
    'detail': reviewer_detail
})

# Check 9: final_output/market_report.md exists
final_report_path = os.path.join(workspace, 'final_output', 'market_report.md')
report_exists = False
report_detail = 'final_output/market_report.md not found'
try:
    if os.path.isfile(final_report_path):
        report_exists = True
        report_detail = 'final_output/market_report.md exists'
except Exception as e:
    report_detail = f'Error checking final report: {e}'

checks.append({
    'name': 'final_market_report_exists',
    'passed': report_exists,
    'detail': report_detail
})

# Check 10: market_report.md contains sector and company references
report_content_ok = False
report_content_detail = 'Could not read or validate report content'
try:
    if os.path.isfile(final_report_path):
        with open(final_report_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        hits = []
        for keyword in ['electric', 'vehicle', 'alphamotors', 'betadrive', 'market']:
            if fuzzy_contains(content, keyword):
                hits.append(keyword)
        report_content_ok = len(hits) >= 3
        report_content_detail = f'Keywords found in report: {hits} (need at least 3 of 5)'
except Exception as e:
    report_content_detail = f'Error reading report content: {e}'

checks.append({
    'name': 'report_contains_market_content',
    'passed': report_content_ok,
    'detail': report_content_detail
})

# Check 11: final_output/approved.json exists and shows approved=true
final_approved_path = os.path.join(workspace, 'final_output', 'approved.json')
approved_ok = False
approved_detail = 'final_output/approved.json not found'
try:
    if os.path.isfile(final_approved_path):
        with open(final_approved_path, 'r') as f:
            approved_data = json.load(f)
        if isinstance(approved_data, dict):
            # Check multiple possible field names
            val = approved_data.get('approved', approved_data.get('status', approved_data.get('result', approved_data.get('decision', None))))
            if val is True or (isinstance(val, str) and val.lower() in ('true', 'approved', 'yes', 'pass')):
                approved_ok = True
                approved_detail = f'approved.json shows approved=true (value: {val})'
            else:
                approved_detail = f'approved.json found but approved field is: {val}'
    else:
        approved_detail = 'final_output/approved.json does not exist'
except Exception as e:
    approved_detail = f'Error reading approved.json: {e}'

checks.append({
    'name': 'final_approved_json_shows_approved',
    'passed': approved_ok,
    'detail': approved_detail
})

# Check 12: marker content flowed through pipeline (data-collector read the input)
marker_propagated = False
marker_detail = 'BENCHMARK_MARKER_EV_2024 not found in any agent outbox'
try:
    for agent in agent_names:
        if agent not in agent_paths:
            continue
        outbox_path = os.path.join(agent_paths[agent], 'outbox')
        if not os.path.isdir(outbox_path):
            continue
        for fname in os.listdir(outbox_path):
            fpath = os.path.join(outbox_path, fname)
            if os.path.isfile(fpath):
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
                        text = f.read()
                    if fuzzy_contains(text, 'BENCHMARK_MARKER_EV_2024') or fuzzy_contains(text, 'MKT-2024-Q1') or fuzzy_contains(text, 'EpsilonEV') or fuzzy_contains(text, 'DeltaAuto'):
                        marker_propagated = True
                        marker_detail = f'Marker/unique content found in {agent}/outbox/{fname}'
                        break
                except Exception:
                    pass
        if marker_propagated:
            break
except Exception as e:
    marker_detail = f'Error checking marker propagation: {e}'

checks.append({
    'name': 'input_data_marker_propagated_through_pipeline',
    'passed': marker_propagated,
    'detail': marker_detail
})

total = len(checks)
passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / total if total > 0 else 0.0
overall_passed = passed_count >= 9

result = {
    'passed': overall_passed,
    'score': round(score, 4),
    'checks': checks
}

print(json.dumps(result, indent=2))