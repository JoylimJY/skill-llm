import sys
import os
import json
import re
from pathlib import Path

def normalize(text):
    return re.sub(r'[\s\W]+', '', text).lower()

def find_agent_workspace(ws, agent_name):
    """Search for agent workspace in multiple possible locations"""
    possible_paths = [
        ws / agent_name,
        ws / 'agents' / agent_name,
        ws / 'agent' / agent_name,
        ws / 'sub_agents' / agent_name,
        ws / 'subagents' / agent_name,
    ]
    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path
    return None

def find_final_output(ws):
    """Search for final_output directory in multiple possible locations"""
    possible_paths = [
        ws / 'final_output',
        ws / 'output',
        ws / 'results',
        Path(workspace).parent / 'final_output',
        Path('/') / 'final_output',
    ]
    for path in possible_paths:
        if path.exists() and path.is_dir():
            return path
    return None

def run_eval(workspace):
    checks = []
    ws = Path(workspace)

    # Check 1: All 4 agent workspaces exist
    try:
        agents = ['data-collector', 'analyst', 'writer', 'reviewer']
        agent_paths = {}
        missing = []
        for agent in agents:
            path = find_agent_workspace(ws, agent)
            if path:
                agent_paths[agent] = path
            else:
                missing.append(agent)
        checks.append({
            'name': 'agent_workspaces_exist',
            'passed': len(missing) == 0,
            'detail': f'Missing agents: {missing}' if missing else f'All 4 agent workspaces found at: {list(agent_paths.keys())}'
        })
    except Exception as e:
        checks.append({'name': 'agent_workspaces_exist', 'passed': False, 'detail': str(e)})

    # Check 2: Each agent has SKILL.md
    try:
        missing_skills = []
        for agent in ['data-collector', 'analyst', 'writer', 'reviewer']:
            agent_path = find_agent_workspace(ws, agent)
            if agent_path:
                skill_path = agent_path / 'SKILL.md'
                if not skill_path.exists():
                    missing_skills.append(agent)
            else:
                missing_skills.append(agent)
        checks.append({
            'name': 'agent_skill_files',
            'passed': len(missing_skills) == 0,
            'detail': f'Missing SKILL.md for: {missing_skills}' if missing_skills else 'All agents have SKILL.md'
        })
    except Exception as e:
        checks.append({'name': 'agent_skill_files', 'passed': False, 'detail': str(e)})

    # Check 3: Each agent has inbox/instructions.md
    try:
        missing_inbox = []
        for agent in ['data-collector', 'analyst', 'writer', 'reviewer']:
            agent_path = find_agent_workspace(ws, agent)
            if agent_path:
                instr_path = agent_path / 'inbox' / 'instructions.md'
                if not instr_path.exists():
                    missing_inbox.append(agent)
            else:
                missing_inbox.append(agent)
        checks.append({
            'name': 'agent_inbox_instructions',
            'passed': len(missing_inbox) == 0,
            'detail': f'Missing inbox/instructions.md for: {missing_inbox}' if missing_inbox else 'All agents have inbox/instructions.md'
        })
    except Exception as e:
        checks.append({'name': 'agent_inbox_instructions', 'passed': False, 'detail': str(e)})

    # Check 4: All agents have status.json with state=completed
    try:
        not_completed = []
        for agent in ['data-collector', 'analyst', 'writer', 'reviewer']:
            agent_path = find_agent_workspace(ws, agent)
            if agent_path:
                status_path = agent_path / 'status.json'
                try:
                    with open(status_path) as f:
                        status = json.load(f)
                    # Check for various status field names
                    state = status.get('state', '').lower() or status.get('status', '').lower()
                    if state != 'completed':
                        not_completed.append(f"{agent}:{state or 'missing'}")
                except Exception:
                    not_completed.append(f"{agent}:unreadable")
            else:
                not_completed.append(f"{agent}:workspace_not_found")
        checks.append({
            'name': 'all_agents_completed',
            'passed': len(not_completed) == 0,
            'detail': f'Not completed: {not_completed}' if not_completed else 'All agents in completed state'
        })
    except Exception as e:
        checks.append({'name': 'all_agents_completed', 'passed': False, 'detail': str(e)})

    # Check 5: data-collector outbox has findings file
    try:
        agent_path = find_agent_workspace(ws, 'data-collector')
        if agent_path:
            outbox = agent_path / 'outbox'
            files = list(outbox.glob('*')) if outbox.exists() else []
            has_findings = any('finding' in f.name.lower() or 'data' in f.name.lower() or 'result' in f.name.lower() or f.suffix in ['.md', '.json', '.txt'] for f in files)
            checks.append({
                'name': 'data_collector_outbox',
                'passed': has_findings and len(files) > 0,
                'detail': f'Outbox files: {[f.name for f in files]}' if files else 'data-collector outbox is empty or missing'
            })
        else:
            checks.append({'name': 'data_collector_outbox', 'passed': False, 'detail': 'data-collector workspace not found'})
    except Exception as e:
        checks.append({'name': 'data_collector_outbox', 'passed': False, 'detail': str(e)})

    # Check 6: analyst outbox has insights file
    try:
        agent_path = find_agent_workspace(ws, 'analyst')
        if agent_path:
            outbox = agent_path / 'outbox'
            files = list(outbox.glob('*')) if outbox.exists() else []
            has_insights = any('insight' in f.name.lower() or 'analysis' in f.name.lower() or f.suffix in ['.md', '.json', '.txt'] for f in files)
            checks.append({
                'name': 'analyst_outbox',
                'passed': has_insights and len(files) > 0,
                'detail': f'Outbox files: {[f.name for f in files]}' if files else 'analyst outbox is empty or missing'
            })
        else:
            checks.append({'name': 'analyst_outbox', 'passed': False, 'detail': 'analyst workspace not found'})
    except Exception as e:
        checks.append({'name': 'analyst_outbox', 'passed': False, 'detail': str(e)})

    # Check 7: writer outbox has draft/report file
    try:
        agent_path = find_agent_workspace(ws, 'writer')
        if agent_path:
            outbox = agent_path / 'outbox'
            files = list(outbox.glob('*')) if outbox.exists() else []
            has_draft = any('draft' in f.name.lower() or 'report' in f.name.lower() or f.suffix in ['.md', '.txt'] for f in files)
            checks.append({
                'name': 'writer_outbox',
                'passed': has_draft and len(files) > 0,
                'detail': f'Outbox files: {[f.name for f in files]}' if files else 'writer outbox is empty or missing'
            })
        else:
            checks.append({'name': 'writer_outbox', 'passed': False, 'detail': 'writer workspace not found'})
    except Exception as e:
        checks.append({'name': 'writer_outbox', 'passed': False, 'detail': str(e)})

    # Check 8: reviewer outbox has approved.json
    try:
        agent_path = find_agent_workspace(ws, 'reviewer')
        if agent_path:
            outbox = agent_path / 'outbox'
            approved_path = outbox / 'approved.json'
            if approved_path.exists():
                with open(approved_path) as f:
                    approved_data = json.load(f)
                is_approved = approved_data.get('approved', False) or approved_data.get('approval_status', '').lower() == 'approved'
                checks.append({
                    'name': 'reviewer_approved_json',
                    'passed': is_approved is True,
                    'detail': f'approved.json content: {approved_data}'
                })
            else:
                # also check for any json with approved key
                found = False
                detail = 'approved.json not found in reviewer/outbox'
                if outbox.exists():
                    for jf in outbox.glob('*.json'):
                        try:
                            with open(jf) as f:
                                d = json.load(f)
                            if 'approved' in d or 'approval_status' in d:
                                found = d.get('approved', False) is True or d.get('approval_status', '').lower() == 'approved'
                                detail = f'Found {jf.name}: {d}'
                                break
                        except Exception:
                            pass
                checks.append({'name': 'reviewer_approved_json', 'passed': found, 'detail': detail})
        else:
            checks.append({'name': 'reviewer_approved_json', 'passed': False, 'detail': 'reviewer workspace not found'})
    except Exception as e:
        checks.append({'name': 'reviewer_approved_json', 'passed': False, 'detail': str(e)})

    # Check 9: final_output/market_report.md exists
    try:
        final_output = find_final_output(ws)
        if final_output:
            report_path = final_output / 'market_report.md'
            exists = report_path.exists()
            checks.append({
                'name': 'final_report_exists',
                'passed': exists,
                'detail': f'market_report.md found at {report_path}' if exists else 'final_output/market_report.md not found'
            })
        else:
            checks.append({'name': 'final_report_exists', 'passed': False, 'detail': 'final_output directory not found'})
    except Exception as e:
        checks.append({'name': 'final_report_exists', 'passed': False, 'detail': str(e)})

    # Check 10: final report contains EV sector content and marker references
    try:
        final_output = find_final_output(ws)
        if final_output:
            report_path = final_output / 'market_report.md'
            if report_path.exists():
                content = report_path.read_text(errors='replace').lower()
                ev_terms = ['electric vehicle', 'ev ', 'tesla', 'byd', 'market']
                found_terms = [t for t in ev_terms if t in content]
                passed = len(found_terms) >= 3
                checks.append({
                    'name': 'final_report_content',
                    'passed': passed,
                    'detail': f'Found EV terms: {found_terms} ({len(found_terms)}/5 required 3+)'
                })
            else:
                checks.append({'name': 'final_report_content', 'passed': False, 'detail': 'Report file not found, cannot check content'})
        else:
            checks.append({'name': 'final_report_content', 'passed': False, 'detail': 'final_output directory not found'})
    except Exception as e:
        checks.append({'name': 'final_report_content', 'passed': False, 'detail': str(e)})

    # Check 11: final_output/approved.json exists and shows approved
    try:
        final_output = find_final_output(ws)
        if final_output:
            approved_path = final_output / 'approved.json'
            if approved_path.exists():
                with open(approved_path) as f:
                    data = json.load(f)
                is_approved = data.get('approved', False) is True or data.get('approval_status', '').lower() == 'approved'
                checks.append({
                    'name': 'final_approved_json',
                    'passed': is_approved,
                    'detail': f'final_output/approved.json: {data}'
                })
            else:
                checks.append({'name': 'final_approved_json', 'passed': False, 'detail': 'final_output/approved.json not found'})
        else:
            checks.append({'name': 'final_approved_json', 'passed': False, 'detail': 'final_output directory not found'})
    except Exception as e:
        checks.append({'name': 'final_approved_json', 'passed': False, 'detail': str(e)})

    # Check 12: dependency chain evidence - analyst inbox has data-collector output
    try:
        agent_path = find_agent_workspace(ws, 'analyst')
        if agent_path:
            analyst_inbox = agent_path / 'inbox'
            files = list(analyst_inbox.glob('**/*')) if analyst_inbox.exists() else []
            non_instr = [f for f in files if f.is_file() and f.name != 'instructions.md']
            has_dependency_files = len(non_instr) > 0
            checks.append({
                'name': 'dependency_chain_analyst',
                'passed': has_dependency_files,
                'detail': f'Analyst inbox extra files: {[f.name for f in non_instr]}' if non_instr else 'No dependency files found in analyst/inbox (expected data-collector outputs)'
            })
        else:
            checks.append({'name': 'dependency_chain_analyst', 'passed': False, 'detail': 'analyst workspace not found'})
    except Exception as e:
        checks.append({'name': 'dependency_chain_analyst', 'passed': False, 'detail': str(e)})

    total = len(checks)
    passed_count = sum(1 for c in checks if c['passed'])
    score = passed_count / total if total > 0 else 0.0
    overall_passed = score >= 0.75

    result = {
        'passed': overall_passed,
        'score': round(score, 4),
        'checks': checks
    }
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    workspace = sys.argv[1] if len(sys.argv) > 1 else '.'
    run_eval(workspace)