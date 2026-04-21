import os
import sys
import json
import re


def find_resume_files(workspace):
    candidates = []
    for fname in os.listdir(workspace):
        if fname.lower().endswith('.md') or fname.lower().endswith('.markdown'):
            candidates.append(os.path.join(workspace, fname))
    return candidates


def check_section_present(text, section_name):
    # Section header detection (e.g., ## Professional Summary) case insensitive
    pattern = re.compile(r'#+\s*' + re.escape(section_name), flags=re.IGNORECASE)
    return bool(pattern.search(text))


def contains_keywords(text, keywords):
    # Checks if at least one keyword or phrase from list is present in text (case-insensitive)
    lower_text = text.lower()
    for kw in keywords:
        if kw.lower() in lower_text:
            return True
    return False


def score_resume(content):
    checks = []

    # Check 1: Mandatory sections present
    sections = ["Professional Summary", "Technical Skills", "Professional Experience", "Education", "Key Achievements"]
    sections_found = [check_section_present(content, s) for s in sections]
    checks.append({
        "name": "All Required Sections Present",
        "passed": all(sections_found),
        "detail": f"Sections found: {[(s, f) for s,f in zip(sections, sections_found)]}"
    })

    # Check 2: ATS keywords present in summary and skills
    # Important keywords based on job description
    ats_keywords = ["product management", "agile", "roadmap planning", "cross-functional teams", "user research", "data-driven", "communication", "saas", "jira", "confluence", "trello"]
    summary_found = False
    skills_found = False

    # Simple split content into sections by headers
    # We'll do a rough split: markdown headers starting with ## or #
    sections_content = {}
    current_section = None
    lines = content.splitlines()
    for line in lines:
        h = re.match(r'#+\s*(.+)', line)
        if h:
            current_section = h.group(1).strip().lower()
            sections_content[current_section] = []
        elif current_section:
            sections_content[current_section].append(line)

    summary_text = " ".join(sections_content.get('professional summary', [])).lower()
    tech_skills_text = " ".join(sections_content.get('technical skills', [])).lower()

    summary_found = any(kw.lower() in summary_text for kw in ats_keywords)
    skills_found = any(kw.lower() in tech_skills_text for kw in ats_keywords)

    checks.append({
        "name": "ATS Keywords in Professional Summary",
        "passed": summary_found,
        "detail": f"Keywords present in summary: {summary_found}"
    })
    checks.append({
        "name": "ATS Keywords in Technical Skills",
        "passed": skills_found,
        "detail": f"Keywords present in skills: {skills_found}"
    })

    # Check 3: Professional Experience contains action verbs + metrics + keywords
    # We look for verbs like Led, Managed, Conducted, Delivered etc.
    action_verbs = ['led', 'managed', 'conducted', 'delivered', 'planned', 'organized', 'developed', 'implemented']
    experience_text = " ".join(sections_content.get('professional experience', [])).lower()

    verbs_found = any(verb in experience_text for verb in action_verbs)
    metrics_found = bool(re.search(r'\b\d{1,3}%|\d+\s+(years|months|team members|projects)\b', experience_text))

    # Also check for keywords
    keywords_in_exp = any(kw.lower() in experience_text for kw in ats_keywords)

    checks.append({
        "name": "Action Verbs in Professional Experience",
        "passed": verbs_found,
        "detail": f"Action verbs found: {verbs_found}"
    })
    checks.append({
        "name": "Quantified Achievements in Professional Experience",
        "passed": metrics_found,
        "detail": f"Metrics or numbers found: {metrics_found}"
    })
    checks.append({
        "name": "ATS Keywords in Professional Experience",
        "passed": keywords_in_exp,
        "detail": f"Keywords found in experience: {keywords_in_exp}"
    })

    # Check 4: Education section lists bachelor's degree
    education_text = " ".join(sections_content.get('education', [])).lower()
    degree_found = any(x in education_text for x in ['bachelor', 'b.sc', 'bachelor of science', 'bachelor degree'])

    checks.append({
        "name": "Education Section Lists Bachelor Degree",
        "passed": degree_found,
        "detail": f"Bachelor degree mention found: {degree_found}"
    })

    # Check 5: Key Achievements are specific and relevant
    achievements_text = " ".join(sections_content.get('key achievements', [])).lower()
    achievements_relevance = any(['agile' in achievements_text,
                                  'user research' in achievements_text,
                                  'jira' in achievements_text,
                                  'led' in achievements_text])

    checks.append({
        "name": "Relevant Key Achievements Section",
        "passed": achievements_relevance,
        "detail": f"Relevant achievements keywords found: {achievements_relevance}"
    })

    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = score >= 0.8

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Argument Check", "passed": False, "detail": "Workspace directory argument missing."}]}))
        return

    workspace = sys.argv[1]
    resume_files = find_resume_files(workspace)

    if not resume_files:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Resume File Found", "passed": False, "detail": "No markdown resume file found in workspace."}]}))
        return

    best_result = None
    for f in resume_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
                result = score_resume(content)
                if (best_result is None) or (result['score'] > best_result['score']):
                    best_result = result
        except Exception as e:
            continue

    if best_result is None:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Resume Parsing", "passed": False, "detail": "Could not parse any resume files."}]}))
        return

    print(json.dumps(best_result))


if __name__ == '__main__':
    main()
