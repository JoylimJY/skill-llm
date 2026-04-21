import os

# Fixed seed deterministic content
job_description = """
Product Manager at InnovateX

Job Description:
- 4+ years experience in product management or related roles
- Proven experience leading cross-functional teams
- Strong skills in Agile methodologies and roadmap planning
- Excellent communication and stakeholder management
- Experience with SaaS products and data-driven decision making
- MBA or relevant business degree preferred
"""

candidate_background = """
5 years as Project Lead at DigiSolutions, managing software development teams
Led Agile transformation initiatives, coached Scrum teams
Worked closely with sales and marketing teams to define product features
Proficient in Jira, Confluence, and data analytics tools
Bachelor’s degree in Computer Science
PMP certified
"""

with open('job_description.txt', 'w') as f:
    f.write(job_description)

with open('candidate_background.txt', 'w') as f:
    f.write(candidate_background)

# Include minimal contact info per instructions
contact_info = """
John Smith
john.smith@example.com
(555) 987-6543
linkedin.com/in/johnsmithpm
"""
with open('contact_info.txt', 'w') as f:
    f.write(contact_info)
