import sys
import os
import json
import re

def check_case_insensitive_contains(text, keywords):
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in text_lower:
            return True
    return False

def extract_section(content, heading_keywords):
    # 修复：正确识别 Markdown 的层级。遇到同级或更高级的标题才停止，兼容 ### 子标题
    lines = content.splitlines()
    capture = False
    capture_level = 0
    section_lines = []
    heading_pattern = re.compile(r'^(#+)\s*(.+)$')
    for line in lines:
        m = heading_pattern.match(line)
        if m:
            level = len(m.group(1))
            header = m.group(2).lower()
            if not capture:
                if any(k.lower() in header for k in heading_keywords):
                    capture = True
                    capture_level = level
                    section_lines = []
            else:
                if level <= capture_level:
                    break
                else:
                    section_lines.append(line)
        elif capture:
            section_lines.append(line)
    return '\n'.join(section_lines).strip()

def find_relevant_file(workspace, exts, keywords=None):
    # 找回丢失的函数！
    candidates = [f for f in os.listdir(workspace) if any(f.lower().endswith(e) for e in exts)]
    if not candidates:
        return None
    if keywords is None:
        return candidates[0]
    scores = []
    for fname in candidates:
        score = sum(1 for kw in keywords if kw.lower() in fname.lower())
        scores.append((score, fname))
    scores.sort(reverse=True)
    return scores[0][1] if scores else candidates[0]

def load_file(path):
    # 找回丢失的函数！
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return ''

def check_professional_summary(md_text):
    summary = extract_section(md_text, ['professional summary', 'summary'])
    passed_len = len(summary.split()) >= 15
    passed_exp = re.search(r'\b(6\+|six|6|7\+|seven|7)\s*(years?|yrs?)', summary, re.IGNORECASE) is not None
    keywords = ['SIEM', 'Splunk', 'incident response', 'forensic', 'malware analysis', 'NIST', 'ISO 27001', 'HIPAA', 'cybersecurity']
    passed_kw = check_case_insensitive_contains(summary, keywords)
    detail = f'Summary length adequate: {passed_len}; Experience mention (6/7+ years): {passed_exp}; Important keywords present: {passed_kw}'
    passed = passed_len and passed_exp and passed_kw
    return passed, detail

def check_technical_skills(md_text):
    skills_section = extract_section(md_text, ['technical skills', 'skills'])
    required_skills = ['SIEM', 'Splunk', 'intrusion detection', 'vulnerability assessments',
                       'network protocols', 'firewalls', 'endpoint security',
                       'forensic investigations', 'malware analysis', 'NIST', 'ISO 27001', 'HIPAA']
    found = [kw for kw in required_skills if kw.lower() in skills_section.lower()]
    passed = len(found) >= len(required_skills)*0.7 
    detail = f'Found technical skills matched: {found}'
    return passed, detail

def check_professional_experience(md_text):
    exp_section = extract_section(md_text, ['professional experience', 'experience', 'work experience'])
    required_actions = ['threat detection', 'incident response', 'SIEM', 'splunk', 'forensic', 'malware',
                        'vulnerability', 'firewall', 'compliance', 'NIST', 'ISO 27001', 'HIPAA', 'leadership']
    matches = [a for a in required_actions if a.lower() in exp_section.lower()]
    quant_match = re.search(r'\b(\d+%|\d+\s+incidents|\d+\s+malware|reduced|improved|increased)\b', exp_section, re.IGNORECASE) is not None
    passed = len(matches) >= 7 and quant_match
    detail = f'Matched key actions: {matches}; Quantification present: {quant_match}'
    return passed, detail

def check_education(md_text):
    edu_section = extract_section(md_text, ['education'])
    passed_degree = bool(re.search(r'bachelor|b\.sc|bachelor of science', edu_section, re.IGNORECASE))
    passed_cert = bool(re.search(r'CompTIA Security\+|CEH|Certified Ethical Hacker', md_text, re.IGNORECASE))
    detail = f'Degree mentioned: {passed_degree}; Certifications present: {passed_cert}'
    passed = passed_degree and passed_cert
    return passed, detail

def check_recommendations(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    passed_num = len(lines) >= 3
    keywords = ['gap', 'suggest', 'recommend', 'improve', 'certification', 'course', 'experience']
    kw_found = [kw for kw in keywords if any(kw in l.lower() for l in lines)]
    passed_kw = len(kw_found) >= 2
    detail = f'Number of lines >=3: {passed_num}; Keywords present: {kw_found}'
    passed = passed_num and passed_kw
    return passed, detail

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "."
    results = []

    resume_path = find_relevant_file(workspace, ['.md'], keywords=['tailored', 'resume'])
    rec_path = find_relevant_file(workspace, ['.txt'], keywords=['recommend'])

    if resume_path is None:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "resume file found", "passed": False, "detail": "No markdown resume file found."}]}))
        return

    resume_text = load_file(os.path.join(workspace, resume_path))
    rec_text = load_file(os.path.join(workspace, rec_path)) if rec_path else ""

    checks = []
    passed, detail = check_professional_summary(resume_text)
    checks.append({"name": "Professional Summary Quality", "passed": passed, "detail": detail})

    passed, detail = check_technical_skills(resume_text)
    checks.append({"name": "Technical Skills Completeness", "passed": passed, "detail": detail})

    passed, detail = check_professional_experience(resume_text)
    checks.append({"name": "Professional Experience Alignment", "passed": passed, "detail": detail})

    passed, detail = check_education(resume_text)
    checks.append({"name": "Education and Certifications", "passed": passed, "detail": detail})

    passed, detail = check_recommendations(rec_text)
    checks.append({"name": "Strategic Recommendations Content", "passed": passed, "detail": detail})

    score = sum(1 for c in checks if c["passed"]) / len(checks)
    passed = score == 1.0

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result))

if __name__ == '__main__':
    main()