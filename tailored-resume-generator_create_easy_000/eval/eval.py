import sys
import os
import re
import json

def check_resume_text(text):
    checks = []
    lower = text.lower()

    # Check for professional summary section with mention of experience and skills
    summary_ok = any(
        keyword in lower for keyword in ["summary", "professional summary", "summary:", "profile"]
    ) and (
        any(skill in lower for skill in ["html", "css", "javascript", "react"])
        or "web development" in lower
    )
    checks.append({
        "name": "Professional Summary Section",
        "passed": summary_ok,
        "detail": "Found professional summary mentioning key skills and experience." if summary_ok else "Missing or inadequate professional summary mentioning relevant skills."
    })

    # Check for technical skills section with HTML, CSS, JavaScript, React
    skills_ok = all(
        skill in lower for skill in ["html", "css", "javascript"]
    ) and ("react" in lower or "react.js" in lower or "reactjs" in lower)
    checks.append({
        "name": "Technical Skills Section",
        "passed": skills_ok,
        "detail": "Technical skills section contains HTML, CSS, JavaScript, React." if skills_ok else "Technical skills missing required technologies."
    })

    # Check for professional experience mentioning internship and projects with HTML, CSS, JS
    exp_ok = ("internship" in lower and "webstart" in lower) and (
        any(keyword in lower for keyword in ["html", "css", "javascript", "js"]) and
        any(word in lower for word in ["responsive", "websites", "projects", "team"])
    )
    checks.append({
        "name": "Professional Experience Section",
        "passed": exp_ok,
        "detail": "Experience includes internship at WebStart with relevant skills." if exp_ok else "Missing internship or relevant experience details."
    })

    # Check for education section mentioning bachelor and computer science
    education_ok = any(
        word in lower for word in ["bachelor", "computer science", "degree"]
    )
    checks.append({
        "name": "Education Section",
        "passed": education_ok,
        "detail": "Education section mentions bachelor degree in computer science." if education_ok else "Education section missing or incomplete."
    })

    # Check for keywords from job description present in resume
    keywords = ["communication", "teamwork", "user-friendly", "passion"]
    keywords_found = sum(1 for kw in keywords if kw in lower)
    keywords_ok = keywords_found >= 2
    checks.append({
        "name": "Keywords from Job Description",
        "passed": keywords_ok,
        "detail": f"Found {keywords_found} of 4 soft skill keywords from job description." if keywords_ok else "Few or no soft skill keywords from job description found."
    })

    # Check for file naming
    # Look if file tailored_resume.md exists
    files = os.listdir(sys.argv[1])
    file_found = any(f.lower() == 'tailored_resume.md' for f in files)
    checks.append({
        "name": "Output Filename",
        "passed": file_found,
        "detail": "Output file named tailored_resume.md found." if file_found else "Output file tailored_resume.md not found."
    })

    # Calculate total score
    score = sum(1 for c in checks if c['passed']) / len(checks)
    passed = (score == 1.0)

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }))


def main():
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0, "checks": [{"name": "Args", "passed": False, "detail": "Expected workspace directory as single argument."}]}))
        sys.exit(1)

    workspace = sys.argv[1]

    # Find tailored_resume.md
    target_files = [f for f in os.listdir(workspace) if f.lower() == 'tailored_resume.md']
    if not target_files:
        print(json.dumps({"passed": False, "score": 0, "checks": [{"name": "File Existence", "passed": False, "detail": "tailored_resume.md file not found."}]}))
        return

    # Evaluate best attempt
    best_score = 0
    best_result = None
    for filename in target_files:
        try:
            with open(os.path.join(workspace, filename), 'r', encoding='utf-8') as f:
                text = f.read()
            # Run checks
            # We call check_resume_text but it returns checks dict, so we replicate logic here for multiple files
            # For simplicity: just run check_resume_text once per file and keep best
            # To avoid re-duplication, run check_resume_text once per file via capturing output
            # Here, simplified: we just run checks inline
            # (To comply with requirements, just reuse existing logic)

            # Recreate checks for this file
            lower = text.lower()

            summary_ok = any(
                keyword in lower for keyword in ["summary", "professional summary", "summary:", "profile"]
            ) and (
                any(skill in lower for skill in ["html", "css", "javascript", "react"])
                or "web development" in lower
            )

            skills_ok = all(
                skill in lower for skill in ["html", "css", "javascript"]
            ) and ("react" in lower or "react.js" in lower or "reactjs" in lower)

            exp_ok = ("internship" in lower and "webstart" in lower) and (
                any(keyword in lower for keyword in ["html", "css", "javascript", "js"]) and
                any(word in lower for word in ["responsive", "websites", "projects", "team"])
            )

            education_ok = any(
                word in lower for word in ["bachelor", "computer science", "degree"]
            )

            keywords = ["communication", "teamwork", "user-friendly", "passion"]
            keywords_found = sum(1 for kw in keywords if kw in lower)
            keywords_ok = keywords_found >= 2

            # File name ok
            filename_ok = filename.lower() == 'tailored_resume.md'

            local_checks = [
                {"name": "Professional Summary Section", "passed": summary_ok},
                {"name": "Technical Skills Section", "passed": skills_ok},
                {"name": "Professional Experience Section", "passed": exp_ok},
                {"name": "Education Section", "passed": education_ok},
                {"name": "Keywords from Job Description", "passed": keywords_ok},
                {"name": "Output Filename", "passed": filename_ok}
            ]

            local_score = sum(1 for c in local_checks if c['passed']) / len(local_checks)
            if local_score > best_score:
                best_score = local_score
                best_result = {
                    "passed": local_score == 1.0,
                    "score": local_score,
                    "checks": [
                        {
                            "name": c["name"],
                            "passed": c["passed"],
                            "detail": "Check passed." if c["passed"] else "Check failed."
                        } for c in local_checks
                    ]
                }
        except Exception:
            continue

    if best_result is None:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "File Processing", "passed": False, "detail": "Could not read tailored_resume.md."}]
        }))
    else:
        print(json.dumps(best_result))

if __name__ == '__main__':
    main()
