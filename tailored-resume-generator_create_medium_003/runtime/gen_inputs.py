import os

job_description = """
Product Manager at InnovateX

Job Description:
- Minimum 4 years of product management experience in tech
- Strong skills in Agile methodologies and roadmap planning
- Ability to lead cross-functional teams
- Experience with user research and data-driven decision making
- Excellent communication skills
- Experience with SaaS products preferred
"""

background = """
- 5 years as a project manager at SoftSolutions
- Led Agile teams delivering web applications
- Conducted user interviews and surveys to refine features
- Skilled in Jira, Confluence, and Trello
- Bachelor's in Computer Science
"""

with open("job_description.txt", "w") as f:
    f.write(job_description + "\n[MARKER-JOB-DESC]\n")

with open("background.txt", "w") as f:
    f.write(background + "\n[MARKER-BACKGROUND]\n")
