#!/usr/bin/env python3
import sys
import os
import json
import re
from pathlib import Path

def main(workspace_dir):
    workspace_path = Path(workspace_dir)
    
    # Load evaluation markers
    markers_file = workspace_path / 'eval_markers.json'
    if not markers_file.exists():
        return {'passed': False, 'score': 0.0, 'checks': [{'name': 'markers_file', 'passed': False, 'detail': 'eval_markers.json not found'}]}
    
    with open(markers_file) as f:
        markers = json.load(f)
    
    checks = []
    score = 0.0
    
    # Look for the RFC document - could be various names
    rfc_files = list(workspace_path.glob('*rfc*.md')) + list(workspace_path.glob('*RFC*.md')) + list(workspace_path.glob('database*.md')) + list(workspace_path.glob('migration*.md'))
    
    if not rfc_files:
        return {
            'passed': False,
            'score': 0.0,
            'checks': [{'name': 'rfc_document_exists', 'passed': False, 'detail': 'No RFC document found (expected .md file with rfc, RFC, database, or migration in name)'}]
        }
    
    # Use the first RFC file found
    rfc_file = rfc_files[0]
    
    try:
        with open(rfc_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        return {
            'passed': False,
            'score': 0.0,
            'checks': [{'name': 'read_rfc_file', 'passed': False, 'detail': f'Could not read RFC file: {e}'}]
        }
    
    # Check 1: Document has substantial content (not just template)
    content_length = len(content.strip())
    substantial_content = content_length > 2000
    checks.append({
        'name': 'substantial_content',
        'passed': substantial_content,
        'detail': f'Document length: {content_length} characters (expected > 2000)'
    })
    if substantial_content:
        score += 0.15
    
    # Check 2: Contains required technical content
    required_content_found = 0
    for term in markers['required_content']:
        if term in content:
            required_content_found += 1
    
    required_content_score = required_content_found / len(markers['required_content'])
    checks.append({
        'name': 'required_technical_content',
        'passed': required_content_score >= 0.7,
        'detail': f'Found {required_content_found}/{len(markers["required_content"])} required technical terms'
    })
    score += required_content_score * 0.25
    
    # Check 3: Mentions stakeholder teams
    teams_mentioned = 0
    for team in markers['stakeholder_teams']:
        if team in content:
            teams_mentioned += 1
    
    teams_score = teams_mentioned / len(markers['stakeholder_teams'])
    checks.append({
        'name': 'stakeholder_teams_mentioned',
        'passed': teams_score >= 0.6,
        'detail': f'Mentioned {teams_mentioned}/{len(markers["stakeholder_teams"])} stakeholder teams'
    })
    score += teams_score * 0.15
    
    # Check 4: Mentions affected services
    services_mentioned = 0
    for service in markers['services']:
        if service in content:
            services_mentioned += 1
    
    services_score = services_mentioned / len(markers['services'])
    checks.append({
        'name': 'affected_services_mentioned',
        'passed': services_score >= 0.6,
        'detail': f'Mentioned {services_mentioned}/{len(markers["services"])} affected services'
    })
    score += services_score * 0.15
    
    # Check 5: Document structure (section headers)
    sections_found = 0
    for section in markers['expected_sections']:
        # Look for section headers (markdown style)
        if re.search(rf'#+\s*{re.escape(section)}|#+\s*{re.escape(section.title())}|#+\s*{re.escape(section.upper())}', content):
            sections_found += 1
    
    structure_score = sections_found / len(markers['expected_sections'])
    checks.append({
        'name': 'document_structure',
        'passed': structure_score >= 0.7,
        'detail': f'Found {sections_found}/{len(markers["expected_sections"])} expected sections'
    })
    score += structure_score * 0.15
    
    # Check 6: Migration-specific content
    migration_terms = ['zero-downtime', 'migration plan', 'rollback', 'cutover', 'dual-write', 'data sync']
    migration_content_found = sum(1 for term in migration_terms if term in content)
    migration_score = min(migration_content_found / 3, 1.0)  # Expect at least 3 migration-related terms
    
    checks.append({
        'name': 'migration_planning_content',
        'passed': migration_score >= 0.5,
        'detail': f'Found {migration_content_found} migration planning terms: {migration_terms}'
    })
    score += migration_score * 0.15
    
    # Bonus points for reader testing indicators
    if any(phrase in content for phrase in ['reader claude', 'fresh claude', 'testing', 'clarification']):
        score += 0.05
        checks.append({
            'name': 'reader_testing_evidence',
            'passed': True,
            'detail': 'Document shows evidence of reader testing or refinement'
        })
    
    # Overall pass/fail
    passed = score >= 0.7
    
    return {
        'passed': passed,
        'score': round(score, 2),
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: eval_script.py <workspace_directory>')
        sys.exit(1)
    
    result = main(sys.argv[1])
    print(json.dumps(result))