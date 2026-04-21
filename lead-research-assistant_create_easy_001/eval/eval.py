import os
import sys
import json
import re

def check_markdown_content(text):
    text_lower = text.lower()
    checks = []

    # 1. Summary Section Present
    summary_keywords = ['summary', 'total leads', 'average fit', 'priority', 'qualified leads']
    summary_found = any(k in text_lower for k in summary_keywords)
    checks.append({'name': 'Summary Section Present', 'passed': summary_found, 'detail': 'Checked for summary/metrics keywords'})

    # 2. Total Leads Count (Flexible regex)
    # 匹配 "5 leads", "5 qualified leads", "Total: 5" 等
    total_leads_match = re.search(r'(\d+)\s*(?:qualified\s*)?leads', text_lower)
    total_count = int(total_leads_match.group(1)) if total_leads_match else 0
    checks.append({'name': 'Total Leads Count', 'passed': total_count >= 5, 'detail': f'Found {total_count} leads in text'})

    # 3. Identify Lead Sections
    # 更加灵活：匹配以数字开头的行（1. Company）或者以 ## Lead 开头的行
    lead_sections = re.split(r'\n(?:\d+\.|\s*#+)\s*', text)
    # 过滤掉较短的非潜在段落（如标题）
    actual_sections = [s for s in lead_sections if len(s.strip()) > 50]
    lead_count = len(actual_sections)
    checks.append({'name': 'Five Lead Sections', 'passed': lead_count >= 5, 'detail': f'Found {lead_count} distinct lead entries'})

    # 4. Check fields for each lead (First 5)
    lead_checks_passed = 0
    for section in actual_sections[:5]:
        # 核心字段校验
        has_website = re.search(r'https?://[^\s)]+', section)
        has_score = re.search(r'priority|score|/10', section, re.I)
        has_decision_maker = re.search(r'decision\s*maker|target', section, re.I)
        has_linkedin = re.search(r'linkedin', section, re.I)
        has_strategy = re.search(r'strategy|outreach|proposition', section, re.I)
        
        if all([has_website, has_score, has_decision_maker, has_linkedin, has_strategy]):
            lead_checks_passed += 1

    checks.append({
        'name': 'Fields for Each Lead', 
        'passed': lead_checks_passed >= 5, 
        'detail': f'{lead_checks_passed}/5 leads meet detail requirements'
    })

    # 5. Priority Scores Valid
    scores = re.findall(r'(?:score|priority).*?(\d+)(?:/10)?', text_lower)
    valid_scores = [int(s) for s in scores if 1 <= int(s) <= 10]
    checks.append({
        'name': 'Priority Scores Valid', 
        'passed': len(valid_scores) >= 5, 
        'detail': f'Found {len(valid_scores)} valid 1-10 scores'
    })

    score = sum(1 for c in checks if c['passed']) / len(checks)
    return {'passed': score >= 0.8, 'score': score, 'checks': checks}

def main():
    if len(sys.argv) != 2:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'Args', 'passed': False, 'detail': 'Missing workspace'}]}))
        return

    workspace = sys.argv[1]
    candidates = [os.path.join(workspace, f) for f in os.listdir(workspace) 
                  if f.lower().endswith('.md') and 'lead' in f.lower()]

    if not candidates:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'File Found', 'passed': False, 'detail': 'leads.md not found'}]}))
        return

    # 获取最高分的结果
    results = []
    for path in candidates:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                results.append(check_markdown_content(f.read()))
        except:
            continue

    if not results:
        final_result = {'passed': False, 'score': 0.0, 'checks': [{'name': 'Error', 'passed': False, 'detail': 'Processing failed'}]}
    else:
        final_result = max(results, key=lambda x: x['score'])

    print(json.dumps(final_result))

if __name__ == '__main__':
    main()