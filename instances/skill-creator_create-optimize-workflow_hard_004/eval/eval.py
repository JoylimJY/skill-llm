import os
import sys
import json
import pandas as pd
from pathlib import Path
import re

def evaluate_skill_creation(workspace_path):
    checks = []
    score = 0.0
    
    workspace = Path(workspace_path)
    
    # Load test metadata
    try:
        with open('.test_metadata.json', 'r') as f:
            metadata = json.load(f)
    except:
        return {"passed": False, "score": 0.0, "checks": [{"name": "metadata_load", "passed": False, "detail": "Could not load test metadata"}]}
    
    # Check 1: Skill directory and structure created
    skill_dirs = [d for d in workspace.iterdir() if d.is_dir() and 'skill' in d.name.lower()]
    skill_created = len(skill_dirs) > 0
    checks.append({"name": "skill_directory_created", "passed": skill_created, "detail": f"Found {len(skill_dirs)} skill directories"})
    if skill_created:
        score += 1.0
        skill_dir = skill_dirs[0]
        
        # Check 2: SKILL.md exists with proper structure
        skill_md = skill_dir / 'SKILL.md'
        skill_md_valid = False
        if skill_md.exists():
            content = skill_md.read_text()
            has_frontmatter = content.startswith('---') and '---' in content[3:]
            has_description = 'description:' in content
            has_name = 'name:' in content
            skill_md_valid = has_frontmatter and has_description and has_name
        checks.append({"name": "skill_md_structure", "passed": skill_md_valid, "detail": f"SKILL.md exists and has proper YAML frontmatter: {skill_md_valid}"})
        if skill_md_valid:
            score += 1.5
    
    # Check 3: Test cases created and executed
    eval_files = list(workspace.glob('**/evals.json')) + list(workspace.glob('**/eval*.json'))
    test_cases_created = len(eval_files) > 0
    checks.append({"name": "test_cases_created", "passed": test_cases_created, "detail": f"Found {len(eval_files)} evaluation files"})
    if test_cases_created:
        score += 1.0
    
    # Check 4: Workspace with iterations exists
    workspace_dirs = [d for d in workspace.iterdir() if d.is_dir() and 'workspace' in d.name.lower()]
    iterations_exist = any(list(d.glob('iteration-*')) for d in workspace_dirs)
    checks.append({"name": "iterations_created", "passed": iterations_exist, "detail": f"Found iteration directories: {iterations_exist}"})
    if iterations_exist:
        score += 1.0
    
    # Check 5: Evaluation viewer artifacts
    html_files = list(workspace.glob('**/*.html'))
    viewer_created = len(html_files) > 0 or any('feedback' in str(f) for f in workspace.glob('**/*.json'))
    checks.append({"name": "evaluation_viewer_used", "passed": viewer_created, "detail": f"Found evaluation viewer artifacts: {viewer_created}"})
    if viewer_created:
        score += 1.0
    
    # Check 6: Scripts directory with automation scripts
    script_dirs = []
    for skill_dir in skill_dirs:
        script_dir = skill_dir / 'scripts'
        if script_dir.exists():
            script_dirs.append(script_dir)
    
    scripts_created = len(script_dirs) > 0
    if scripts_created:
        script_files = []
        for script_dir in script_dirs:
            script_files.extend(list(script_dir.glob('*.py')))
        scripts_created = len(script_files) > 0
    
    checks.append({"name": "automation_scripts_created", "passed": scripts_created, "detail": f"Found automation scripts: {scripts_created}"})
    if scripts_created:
        score += 1.5
    
    # Check 7: Data processing capability validation
    data_processing_validated = False
    for workspace_dir in workspace_dirs:
        for iteration_dir in workspace_dir.glob('iteration-*'):
            for eval_dir in iteration_dir.glob('eval-*'):
                outputs_dir = eval_dir / 'outputs'
                if outputs_dir.exists():
                    # Look for evidence of data processing
                    output_files = list(outputs_dir.glob('*'))
                    csv_processed = any('csv' in f.name.lower() or 'data' in f.name.lower() for f in output_files)
                    charts_created = any('chart' in f.name.lower() or 'plot' in f.name.lower() or '.png' in f.name.lower() for f in output_files)
                    data_processing_validated = csv_processed or charts_created
                    if data_processing_validated:
                        break
    
    checks.append({"name": "data_processing_validated", "passed": data_processing_validated, "detail": f"Evidence of data processing in outputs: {data_processing_validated}"})
    if data_processing_validated:
        score += 1.5
    
    # Check 8: Benchmark or comparison results
    benchmark_files = list(workspace.glob('**/benchmark*.json'))
    comparison_files = list(workspace.glob('**/comparison*.json'))
    performance_measured = len(benchmark_files) > 0 or len(comparison_files) > 0
    checks.append({"name": "performance_measurement", "passed": performance_measured, "detail": f"Found benchmark/comparison files: {len(benchmark_files) + len(comparison_files)}"})
    if performance_measured:
        score += 1.0
    
    # Check 9: Skill packaging
    skill_files = list(workspace.glob('**/*.skill'))
    packaged = len(skill_files) > 0
    checks.append({"name": "skill_packaged", "passed": packaged, "detail": f"Found packaged .skill files: {len(skill_files)}"})
    if packaged:
        score += 0.5
    
    # Normalize score to 0-100
    max_possible_score = 10.0
    normalized_score = min(100.0, (score / max_possible_score) * 100)
    
    # Pass if score >= 60
    passed = normalized_score >= 60.0
    
    return {
        "passed": passed,
        "score": normalized_score, 
        "checks": checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "usage", "passed": False, "detail": "Usage: eval_script.py <workspace_path>"}]}))
        sys.exit(1)
    
    result = evaluate_skill_creation(sys.argv[1])
    print(json.dumps(result, indent=2))