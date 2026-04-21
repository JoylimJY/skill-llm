import sys
import os
import re
import json


def read_all_md_files(path):
    md_texts = []
    for fname in os.listdir(path):
        if fname.lower().endswith('.md'):
            with open(os.path.join(path, fname), 'r', encoding='utf-8') as f:
                md_texts.append(f.read())
    return md_texts


def check_presence(text, keywords, name):
    present = any(k.lower() in text.lower() for k in keywords)
    detail = f'Required keywords {keywords}' if present else f'Missing keywords {keywords}'
    return {'name': name, 'passed': present, 'detail': detail}


def check_heading_presence(text, headings, section_name):
    """Check if any of the given headings appear in the text (flexible heading levels)"""
    for heading in headings:
        # match heading with optional markdown hashes, ignore case
        pattern = re.compile(r'#+\s*' + re.escape(heading), re.IGNORECASE)
        if pattern.search(text):
            return True
    return False


def quantify_achievements_check(text):
    """Check if resume has quantification like percentages, years, numbers"""
    patterns = [r'\d+%', r'\d+\+? years?', r'\d+\s+servers?', r'\breduced\b', r'\bautomated\b']
    found = any(re.search(pat, text, re.IGNORECASE) for pat in patterns)
    detail = "Found quantifications or measurable impact" if found else "No quantifications or measurable impact found"
    return {'name': 'Quantify achievements', 'passed': found, 'detail': detail}


def check_action_verbs(text):
    verbs = ['designed', 'implemented', 'maintained', 'automated', 'developed', 'built', 'managed', 'collaborated', 'wrote', 'created']
    present = any(v in text.lower() for v in verbs)
    detail = "Action verbs present" if present else "No action verbs found"
    return {'name': 'Action verbs usage', 'passed': present, 'detail': detail}


def check_no_personal_pronouns(text):
    pronouns = [' i ', ' me ', ' my ', ' mine ', ' myself ']
    found = any(p in text.lower() for p in pronouns)
    detail = "No personal pronouns found" if not found else "Personal pronouns used"
    return {'name': 'No personal pronouns', 'passed': not found, 'detail': detail}


def check_filename_presence(path, filename):
    for fname in os.listdir(path):
        if fname == filename:
            return {'name': 'Output filename', 'passed': True, 'detail': f'Found required file {filename}'}
    return {'name': 'Output filename', 'passed': False, 'detail': f'Required file {filename} not found'}


# Main evaluation
if __name__ == '__main__':
    workspace = sys.argv[1]

    # Check for required output file
    filename_check = check_filename_presence(workspace, 'Tailored_Resume_DevOps.md')

    # If file not found, fail early with minimal checks
    if not filename_check['passed']:
        print(json.dumps({
            'passed': False,
            'score': 0.0,
            'checks': [filename_check]
        }))
        sys.exit(0)

    # Read all markdown contents
    md_texts = read_all_md_files(workspace)

    # We score over highest-scoring text (in case multiple .md files)
    best_score = 0
    best_checks_result = None

    for text in md_texts:
        checks = []

        ## Check required headings
        headings_required = [
            ['Professional Summary', 'Summary'],
            ['Technical Skills', 'Skills'],
            ['Professional Experience', 'Experience'],
            ['Education'],
            ['Certifications']
        ]

        headings_passed = 0
        for heads in headings_required:
            found = check_heading_presence(text, heads, heads[0])
            checks.append({'name': f'Heading presence: {heads[0]}', 'passed': found, 'detail': f'Found heading variants {heads}' if found else f'Missing heading variants {heads}'})
            if found:
                headings_passed += 1

        ## Check presence of key skill keywords (to match job description and requested skills)
        keywords = [
            'AWS', 'Azure', 'Docker', 'Kubernetes', 'Terraform',
            'Ansible', 'Python', 'Bash', 'Prometheus', 'Grafana'
        ]
        checks.append(check_presence(text, keywords, 'Technical skills keywords'))

        ## Check professional summary references duration and key skills
        summary_ok = False
        # Look for 5+ years, DevOps and some key tools mentioned early
        if re.search(r'5\+? years?', text, re.IGNORECASE) and 'devops' in text.lower():
            # Also check for presence of any of core tools in summary vicinity
            # Split by sections and find summary section
            summaries = re.split(r'#+\s*professional summary', text, flags=re.IGNORECASE)
            if len(summaries) > 1:
                summary_text = summaries[1][:1000].lower() # first 1k chars after header
                tools_found = any(tool.lower() in summary_text for tool in ['aws', 'azure', 'docker', 'kubernetes', 'terraform', 'ansible', 'python', 'bash'])
                if tools_found:
                    summary_ok = True
        checks.append({'name': 'Professional summary relevance', 'passed': summary_ok, 'detail': 'Summary mentions 5+ years DevOps and relevant skills' if summary_ok else 'Summary missing 5+ years DevOps or key skills'})

        ## Check action verbs presence
        checks.append(check_action_verbs(text))

        ## Check quantification of impact
        checks.append(quantify_achievements_check(text))

        ## Check no personal pronouns
        checks.append(check_no_personal_pronouns(text))

        score = sum(1 for c in checks if c['passed']) / len(checks)

        if score > best_score:
            best_score = score
            best_checks_result = checks

    # Overall pass if score >= 0.8
    passed = best_score >= 0.8

    print(json.dumps({
        'passed': passed,
        'score': best_score,
        'checks': best_checks_result
    }))
