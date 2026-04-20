import sys
import os
import json
import re
from pathlib import Path

def normalize(text):
    return re.sub(r'[\s\W]+', ' ', text.lower()).strip()

def fuzzy_contains(text, keyword):
    return normalize(keyword) in normalize(text)

checks = []

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")

# Check 1: agent workspace directories exist
try:
    agent_dirs = []
    for d in workspace.iterdir():
        if d.is_dir():
            # Check for agent-like structure (has inbox, outbox, or workspace, and SKILL.md)
            has_skill = (d / 'SKILL.md').exists()
            has_inbox = (d / 'inbox').exists()
            has_outbox = (d / 'outbox').exists()
            has_workspace = (d / 'workspace').exists()
            
            if has_skill and (has_inbox or has_outbox or has_workspace):
                agent_dirs.append(d.name)
    passed = len(agent_dirs) >= 3
    checks.append({
        'name': 'agent_workspaces_created',
        'passed': passed,
        'detail': f'Found agent-like dirs: {agent_dirs}' if passed else f'Expected at least 3 agent workspaces, found: {agent_dirs}'
    })
except Exception as e:
    checks.append({'name': 'agent_workspaces_created', 'passed': False, 'detail': f'Error scanning workspace: {e}'})

# Check 2: each agent has a SKILL.md
try:
    skill_count = 0
    skill_dirs = []
    for d in workspace.iterdir():
        if d.is_dir():
            skill_path = d / 'SKILL.md'
            if skill_path.exists():
                skill_count += 1
                skill_dirs.append(d.name)
    passed = skill_count >= 3
    checks.append({
        'name': 'skill_md_files_exist',
        'passed': passed,
        'detail': f'Found SKILL.md in: {skill_dirs}'
    })
except Exception as e:
    checks.append({'name': 'skill_md_files_exist', 'passed': False, 'detail': f'Error: {e}'})

# Check 3: each agent has inbox/instructions.md
try:
    inbox_count = 0
    inbox_dirs = []
    for d in workspace.iterdir():
        if d.is_dir():
            instr = d / 'inbox' / 'instructions.md'
            if instr.exists():
                inbox_count += 1
                inbox_dirs.append(d.name)
    passed = inbox_count >= 3
    checks.append({
        'name': 'inbox_instructions_exist',
        'passed': passed,
        'detail': f'Found inbox/instructions.md in: {inbox_dirs}'
    })
except Exception as e:
    checks.append({'name': 'inbox_instructions_exist', 'passed': False, 'detail': f'Error: {e}'})

# Check 4: status.json files exist and at least some are completed
try:
    completed_agents = []
    for d in workspace.iterdir():
        if d.is_dir():
            status_path = d / 'status.json'
            if status_path.exists():
                try:
                    with open(status_path) as f:
                        status = json.load(f)
                    # Accept both 'status' and 'state' fields
                    status_value = status.get('status', '').lower() or status.get('state', '').lower()
                    if status_value in ('completed', 'done', 'finished', 'success'):
                        completed_agents.append(d.name)
                except Exception:
                    pass
    passed = len(completed_agents) >= 2
    checks.append({
        'name': 'agents_completed_status',
        'passed': passed,
        'detail': f'Agents with completed status: {completed_agents}'
    })
except Exception as e:
    checks.append({'name': 'agents_completed_status', 'passed': False, 'detail': f'Error: {e}'})

# Check 5: data-collector-like agent has outbox with metrics/findings
try:
    collector_outbox_ok = False
    collector_detail = 'No data-collector outbox found'
    for d in workspace.iterdir():
        if d.is_dir() and any(kw in d.name.lower() for kw in ('collect', 'data', 'gather')):
            # Check both outbox and workspace directories
            for output_dir in ['outbox', 'workspace']:
                outbox = d / output_dir
                if outbox.exists():
                    files = list(outbox.iterdir())
                    if files:
                        for f in files:
                            if f.is_file():
                                try:
                                    content = f.read_text(errors='ignore')
                                    if any(fuzzy_contains(content, kw) for kw in ['cloud', 'growth', 'market', 'sector', 'metric']):
                                        collector_outbox_ok = True
                                        collector_detail = f'Found relevant content in {d.name}/{output_dir}/{f.name}'
                                        break
                                except Exception:
                                    pass
                    if collector_outbox_ok:
                        break
    checks.append({
        'name': 'data_collector_outbox_has_metrics',
        'passed': collector_outbox_ok,
        'detail': collector_detail
    })
except Exception as e:
    checks.append({'name': 'data_collector_outbox_has_metrics', 'passed': False, 'detail': f'Error: {e}'})

# Check 6: analyst-like agent has outbox with trends
try:
    analyst_ok = False
    analyst_detail = 'No analyst outbox found'
    for d in workspace.iterdir():
        if d.is_dir() and any(kw in d.name.lower() for kw in ('analyst', 'analysis', 'analyze')):
            # Check both outbox and workspace directories
            for output_dir in ['outbox', 'workspace']:
                outbox = d / output_dir
                if outbox.exists():
                    for f in outbox.iterdir():
                        if f.is_file():
                            try:
                                content = f.read_text(errors='ignore')
                                if any(fuzzy_contains(content, kw) for kw in ['trend', 'insight', 'pattern', 'growth', 'top']):
                                    analyst_ok = True
                                    analyst_detail = f'Found trend content in {d.name}/{output_dir}/{f.name}'
                                    break
                            except Exception:
                                pass
                    if analyst_ok:
                        break
    checks.append({
        'name': 'analyst_outbox_has_trends',
        'passed': analyst_ok,
        'detail': analyst_detail
    })
except Exception as e:
    checks.append({'name': 'analyst_outbox_has_trends', 'passed': False, 'detail': f'Error: {e}'})

# Check 7: final_report.md exists in workspace root
try:
    report_path = workspace / 'final_report.md'
    exists = report_path.exists()
    if exists:
        content = report_path.read_text(errors='ignore')
        has_content = len(content.strip()) > 100
        passed = has_content
        detail = f'final_report.md exists with {len(content)} chars'
    else:
        passed = False
        detail = 'final_report.md not found in workspace root'
    checks.append({
        'name': 'final_report_exists',
        'passed': passed,
        'detail': detail
    })
except Exception as e:
    checks.append({'name': 'final_report_exists', 'passed': False, 'detail': f'Error: {e}'})

# Check 8: final_report.md references key market sectors
try:
    report_path = workspace / 'final_report.md'
    if report_path.exists():
        content = report_path.read_text(errors='ignore')
        sectors_found = []
        for sector in ['cloud', 'ai', 'cybersecurity', 'edge']:
            if fuzzy_contains(content, sector):
                sectors_found.append(sector)
        passed = len(sectors_found) >= 2
        checks.append({
            'name': 'final_report_mentions_sectors',
            'passed': passed,
            'detail': f'Sectors mentioned in report: {sectors_found}'
        })
    else:
        checks.append({
            'name': 'final_report_mentions_sectors',
            'passed': False,
            'detail': 'final_report.md missing'
        })
except Exception as e:
    checks.append({'name': 'final_report_mentions_sectors', 'passed': False, 'detail': f'Error: {e}'})

# Check 9: final_report.md mentions top trends (at least 3 trend-like items)
try:
    report_path = workspace / 'final_report.md'
    if report_path.exists():
        content = report_path.read_text(errors='ignore')
        trend_matches = re.findall(r'trend|growth|opportunit|insight|forecast|increas|expand', content, re.IGNORECASE)
        passed = len(trend_matches) >= 3
        checks.append({
            'name': 'final_report_contains_trends',
            'passed': passed,
            'detail': f'Found {len(trend_matches)} trend-related terms in final report'
        })
    else:
        checks.append({
            'name': 'final_report_contains_trends',
            'passed': False,
            'detail': 'final_report.md missing'
        })
except Exception as e:
    checks.append({'name': 'final_report_contains_trends', 'passed': False, 'detail': f'Error: {e}'})

# Check 10: writer-like agent has outbox with report content
try:
    writer_ok = False
    writer_detail = 'No writer outbox found'
    for d in workspace.iterdir():
        if d.is_dir() and any(kw in d.name.lower() for kw in ('writer', 'write', 'report', 'doc')):
            # Check both outbox and workspace directories
            for output_dir in ['outbox', 'workspace']:
                outbox = d / output_dir
                if outbox.exists():
                    for f in outbox.iterdir():
                        if f.is_file():
                            try:
                                content = f.read_text(errors='ignore')
                                if len(content.strip()) > 50:
                                    writer_ok = True
                                    writer_detail = f'Writer output found: {d.name}/{output_dir}/{f.name}'
                                    break
                            except Exception:
                                pass
                    if writer_ok:
                        break
    checks.append({
        'name': 'writer_agent_produced_output',
        'passed': writer_ok,
        'detail': writer_detail
    })
except Exception as e:
    checks.append({'name': 'writer_agent_produced_output', 'passed': False, 'detail': f'Error: {e}'})

total = len(checks)
passed_count = sum(1 for c in checks if c['passed'])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = score >= 0.7

result = {
    'passed': overall_passed,
    'score': score,
    'checks': checks
}

print(json.dumps(result, indent=2))