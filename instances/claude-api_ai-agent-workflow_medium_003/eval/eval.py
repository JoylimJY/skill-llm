import sys
import os
import json

def evaluate_task(workspace_path):
    checks = []
    score = 0.0
    
    # Check if the main script exists
    script_path = os.path.join(workspace_path, 'research_agent.py')
    if os.path.exists(script_path):
        checks.append({'name': 'Script exists', 'passed': True, 'detail': 'research_agent.py found'})
        score += 0.2
    else:
        checks.append({'name': 'Script exists', 'passed': False, 'detail': 'research_agent.py not found'})
        return {'passed': False, 'score': 0.0, 'checks': checks}
    
    # Read and analyze the script
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Check for Claude API integration
    if 'anthropic' in content and 'messages.create' in content:
        checks.append({'name': 'Uses Claude API', 'passed': True, 'detail': 'Anthropic SDK integration found'})
        score += 0.2
    else:
        checks.append({'name': 'Uses Claude API', 'passed': False, 'detail': 'No Claude API integration found'})
    
    # Check for streaming implementation
    if '.stream(' in content or 'stream=True' in content:
        checks.append({'name': 'Implements streaming', 'passed': True, 'detail': 'Streaming functionality found'})
        score += 0.2
    else:
        checks.append({'name': 'Implements streaming', 'passed': False, 'detail': 'No streaming implementation found'})
    
    # Check for document processing capabilities
    doc_processing = False
    if any(lib in content for lib in ['python-docx', 'pypdf', 'docx', 'Document']):
        doc_processing = True
        checks.append({'name': 'Document processing', 'passed': True, 'detail': 'Document processing libraries used'})
        score += 0.15
    else:
        checks.append({'name': 'Document processing', 'passed': False, 'detail': 'No document processing found'})
    
    # Check for structured output/summary generation
    if 'summary' in content.lower() or 'report' in content.lower():
        checks.append({'name': 'Summary generation', 'passed': True, 'detail': 'Summary/report generation logic found'})
        score += 0.15
    else:
        checks.append({'name': 'Summary generation', 'passed': False, 'detail': 'No summary generation found'})
    
    # Check for tool use or function calling (advanced)
    if 'tools' in content or 'tool_use' in content:
        checks.append({'name': 'Tool use implementation', 'passed': True, 'detail': 'Tool use functionality found'})
        score += 0.1
    else:
        checks.append({'name': 'Tool use implementation', 'passed': False, 'detail': 'No tool use found (optional)'})
    
    # Final pass determination
    passed = score >= 0.6
    
    return {
        'passed': passed,
        'score': round(score, 2),
        'checks': checks
    }

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'Usage', 'passed': False, 'detail': 'Usage: python eval_script.py <workspace_path>'}]}))
        sys.exit(1)
    
    result = evaluate_task(sys.argv[1])
    print(json.dumps(result))