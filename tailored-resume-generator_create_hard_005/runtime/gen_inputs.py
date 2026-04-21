import os

# Deterministic seed used for generating text (though mostly fixed text here)

job_description = '''
Job Title: DevOps Engineer
Location: Remote

Responsibilities:
- Design, implement, and maintain CI/CD pipelines
- Manage cloud infrastructure on AWS and Azure
- Automate configuration management using tools like Ansible, Terraform
- Monitor system performance and troubleshoot issues
- Collaborate with development teams to improve deployment efficiency

Requirements:
- 4+ years experience in DevOps or related engineering role
- Strong knowledge of AWS, Azure, Docker, Kubernetes
- Expertise in infrastructure-as-code tools (Terraform, Ansible)
- Proficient with scripting languages (Python, Bash)
- Experience with monitoring tools (Prometheus, Grafana)
- Excellent communication and teamwork skills

Preferred Qualifications:
- Certifications: AWS Certified DevOps Engineer, Azure Solutions Architect
- Background in software development
'''

background_info = '''
- 5 years as system administrator at DataSys
- Built Docker and Kubernetes clusters for production
- Developed Terraform modules to automate cloud resources
- Automated server deployments with Ansible
- Wrote Python and Bash scripts for monitoring and backups
- Collaborated with software teams using Agile methods
- AWS Certified Solutions Architect - Associate
- Bachelor’s degree in Computer Science
'''

# Write inputs to files
with open('job_description.txt', 'w', encoding='utf-8') as f:
    f.write(job_description.strip())

with open('background.txt', 'w', encoding='utf-8') as f:
    f.write(background_info.strip())

# Write user prompt file with explicit details
prompt_text = (
    'I am applying for a mid-level DevOps Engineer role at CloudScale Inc. Please tailor my resume accordingly. ' 
    'Here is the full job description in job_description.txt and my background info in background.txt.\n'
    'Output exactly one well-formatted markdown resume file named "Tailored_Resume_DevOps.md" with:\n'
    '- A professional summary highlighting 5+ years DevOps experience and key skills matching the job description.\n'
    '- Dedicated Technical Skills section with cloud platforms, tools, scripting languages, monitoring tools as stated.\n'
    '- Professional Experience section describing relevant projects, technologies, and quantified achievements.\n'
    '- Education and Certifications including AWS cert listed explicitly.\n'
    '- Clean, ATS-optimized markdown formatting with proper headings: Professional Summary, Technical Skills, Professional Experience, Education, Certifications.\n'
    '- Use action verbs and quantify results.\n'
    '- Avoid personal pronouns and unrelated jobs.'
)

with open('user_prompt.txt', 'w', encoding='utf-8') as f:
    f.write(prompt_text)