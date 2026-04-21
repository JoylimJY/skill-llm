import json

def main():
    job_description = (
        "Junior Web Developer at CreativeApps Inc.\n"
        "Requirements:\n"
        "- 1-2 years experience in web development\n"
        "- Proficiency with HTML, CSS, JavaScript\n"
        "- Familiarity with React framework is a plus\n"
        "- Good communication and teamwork skills\n"
        "- Passion for creating user-friendly websites"
    )

    background = (
        "- Recently completed internship at WebStart where I built responsive websites using HTML, CSS, and JS\n"
        "- Basic experience with React through online projects\n"
        "- Bachelor degree in Computer Science\n"
        "- Strong collaborator in team projects"
    )

    with open('job_description.txt', 'w', encoding='utf-8') as f:
        f.write(job_description)

    with open('candidate_background.txt', 'w', encoding='utf-8') as f:
        f.write(background)

if __name__ == '__main__':
    main()
