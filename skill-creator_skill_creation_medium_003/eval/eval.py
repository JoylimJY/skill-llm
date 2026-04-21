import os
import sys
import json
import re
from pathlib import Path

def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": false, "score": 0.0, "checks": [{"name": "usage", "passed": false, "detail": "Usage: python eval_script.py <workspace_dir>"}]}))
        return
    
    workspace = Path(sys.argv[1])
    checks = []
    
    # Check 1: SKILL.md exists and has proper frontmatter
    skill_md = None
    skill_dirs = [d for d in workspace.glob('*') if d.is_dir() and (d / 'SKILL.md').exists()]
    if skill_dirs:
        skill_md = skill_dirs[0] / 'SKILL.md'
        try:
            content = skill_md.read_text().lower()
            if 'name:' in content and 'research' in content:
                checks.append({"name": "skill_md_exists", "passed": True, "detail": "SKILL.md found with proper frontmatter"})
            else:
                checks.append({"name": "skill_md_exists", "passed": False, "detail": "SKILL.md missing proper frontmatter or research context"})
        except:
            checks.append({"name": "skill_md_exists", "passed": False, "detail": "Could not read SKILL.md"})
    else:
        checks.append({"name": "skill_md_exists", "passed": False, "detail": "SKILL.md not found"})
    
    # Check 2: Python script for PDF processing exists
    script_found = False
    for skill_dir in skill_dirs:
        script_files = list(skill_dir.rglob('*.py'))
        for script in script_files:
            content = script.read_text().lower()
            if any(keyword in content for keyword in ['pdf', 'extract', 'pypdf', 'text']):
                script_found = True
                break
        if script_found:
            break
    
    if script_found:
        checks.append({"name": "pdf_script_exists", "passed": True, "detail": "PDF processing script found"})
    else:
        checks.append({"name": "pdf_script_exists", "passed": False, "detail": "No PDF processing script found"})
    
    # Check 3: Evals directory and JSON file exist
    evals_found = False
    for skill_dir in skill_dirs:
        evals_path = skill_dir / 'evals' / 'evals.json'
        if evals_path.exists():
            try:
                evals_data = json.loads(evals_path.read_text())
                # Accept 'evals', 'tests', 'cases' keys or a top-level array
                test_cases = None
                if isinstance(evals_data, list):
                    test_cases = evals_data
                elif 'evals' in evals_data:
                    test_cases = evals_data.get('evals', [])
                elif 'tests' in evals_data:
                    test_cases = evals_data.get('tests', [])
                elif 'cases' in evals_data:
                    test_cases = evals_data.get('cases', [])
                if test_cases and len(test_cases) >= 3:
                    evals_found = True
                    break
            except:
                pass
    
    if evals_found:
        checks.append({"name": "evals_json_exists", "passed": True, "detail": "evals.json found with 3+ test cases"})
    else:
        checks.append({"name": "evals_json_exists", "passed": False, "detail": "evals.json not found or insufficient test cases"})
    
    # Check 4: Skill mentions key research concepts
    research_concepts_found = False
    if skill_md and skill_md.exists():
        content = skill_md.read_text().lower()
        # Expanded keywords to include more variations
        research_keywords = ['abstract', 'methodology', 'citation', 'academic', 'research', 'paper', 'apa', 'biblio', 'references', 'findings', 'journal', 'publication', 'scientific']
        if sum(1 for keyword in research_keywords if keyword in content) >= 3:
            research_concepts_found = True
    
    if research_concepts_found:
        checks.append({"name": "research_concepts", "passed": True, "detail": "Skill contains relevant research concepts"})
    else:
        checks.append({"name": "research_concepts", "passed": False, "detail": "Skill lacks sufficient research-related concepts"})
    
    # Check 5: .skill package file created
    skill_files = list(workspace.glob('*.skill'))
    if skill_files and any('research' in f.name.lower() for f in skill_files):
        checks.append({"name": "skill_package", "passed": True, "detail": "research-assistant.skill package created"})
    else:
        checks.append({"name": "skill_package", "passed": False, "detail": "No .skill package file found with research name"})
    
    # Check 6: Skill description mentions triggering conditions
    trigger_conditions_found = False
    if skill_md and skill_md.exists():
        content = skill_md.read_text().lower()
        if any(phrase in content for phrase in ['trigger', 'when', 'use this skill', 'academic papers', 'citation']):
            trigger_conditions_found = True
    
    if trigger_conditions_found:
        checks.append({"name": "trigger_conditions", "passed": True, "detail": "Skill description includes triggering conditions"})
    else:
        checks.append({"name": "trigger_conditions", "passed": False, "detail": "Skill lacks clear triggering conditions"})
    
    # Calculate score and overall pass
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8  # Allow for minor imperfections
    
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()