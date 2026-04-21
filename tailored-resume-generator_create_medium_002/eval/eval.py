import sys
import os
import re
import json

def check_resume_content(text, contact_lines):
    tests = []
    text_lower = text.lower()

    # Check contact info included
    contact_pass = all(any(cl.strip().lower() in line.lower() for line in text_lower.splitlines()) for cl in contact_lines)
    tests.append({"name": "Contact Information Included", "passed": contact_pass, "detail": "Contact info presence check."})

    # Check for professional summary containing: product management, agile, saas, leadership
    summary_pass = all(keyword in text_lower for keyword in ["product management", "agile", "saas", "leadership"])
    tests.append({"name": "Professional Summary Keywords", "passed": summary_pass, "detail": "Summary should include key skills and roles."})

    # Check for skills section with keywords: jira, confluence, roadmap, stakeholder
    skills_keywords = ["jira", "confluence", "roadmap", "stakeholder"]
    skills_pass = any(all(k in block.lower() for k in skills_keywords) for block in re.split(r'\n#*\s*skills', text_lower))
    # If no explicit skills heading, check anywhere
    if not skills_pass:
        skills_pass = all(k in text_lower for k in skills_keywords)
    tests.append({"name": "Skills Section Keywords", "passed": skills_pass, "detail": "Skills keywords presence check."})

    # Check experience section includes Agile, cross-functional team, product features
    exp_pass = all(keyword in text_lower for keyword in ["agile", "cross-functional", "product feature"])
    tests.append({"name": "Experience Section Content", "passed": exp_pass, "detail": "Relevant experience details check."})

    # Check achievements include metrics or quantitative impact (look for % or numbers)
    metrics_pass = bool(re.search(r'(\d+%|\b\d+\b)', text))
    tests.append({"name": "Quantified Achievements", "passed": metrics_pass, "detail": "Presence of quantifiable metrics."})

    # Check education section includes Bachelor degree and PMP cert
    edu_pass = all(kw in text_lower for kw in ["bachelor", "computer science", "pmp"])
    tests.append({"name": "Education and Certifications", "passed": edu_pass, "detail": "Education and certification mention."})

    # Check output is markdown with filename tailored_resume.md present
    file_exists = any(fname.lower() == "tailored_resume.md" for fname in os.listdir(sys.argv[1]))
    tests.append({"name": "Output File Presence (tailored_resume.md)", "passed": file_exists, "detail": "File presence check."})

    # Final score
    passed_checks = sum(1 for t in tests if t['passed'])
    score = passed_checks / len(tests) if tests else 0.0
    passed = score == 1.0

    return {"passed": passed, "score": score, "checks": tests}


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Input Argument", "passed": False, "detail": "Workspace directory arg missing"}]}))
        return

    workspace = sys.argv[1]

    # Look for tailored_resume.md file
    candidate_files = [f for f in os.listdir(workspace) if f.lower() == "tailored_resume.md"]
    if not candidate_files:
        # Check any .md file containing "product manager"
        md_files = [f for f in os.listdir(workspace) if f.endswith('.md')]
        if not md_files:
            print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Output File", "passed": False, "detail": "No Markdown file found in workspace."}]}))
            return
        # Pick all md files and score highest
    else:
        md_files = candidate_files

    best_score = 0.0
    best_checks = None
    best_passed = False

    # Contact info must be found
    contact_lines = ["John Smith", "john.smith@example.com", "(555) 987-6543", "linkedin.com/in/johnsmithpm"]

    for filename in md_files:
        try:
            with open(os.path.join(workspace, filename), 'r', encoding='utf-8') as f:
                text = f.read()
            result = check_resume_content(text, contact_lines)
            if result["score"] > best_score:
                best_score = result["score"]
                best_checks = result["checks"]
                best_passed = result["passed"]
        except Exception as e:
            continue

    if best_checks is None:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Evaluation", "passed": False, "detail": "No valid resume files read."}]}))
        return

    print(json.dumps({"passed": best_passed, "score": best_score, "checks": best_checks}))


if __name__ == '__main__':
    main()
