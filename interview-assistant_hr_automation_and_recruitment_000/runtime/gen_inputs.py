import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a realistic HR department directory structure with distractor files
dirs = [
    "hr_department/job_postings/2024",
    "hr_department/job_postings/2023_archive",
    "hr_department/candidates/shortlisted",
    "hr_department/candidates/rejected",
    "hr_department/interview_templates/engineering",
    "hr_department/interview_templates/product",
    "hr_department/offer_letters",
    "hr_department/onboarding/documents",
    "hr_department/policies",
    "recruitment_pipeline/pipeline_tracker",
    "recruitment_pipeline/sourcing_channels",
    "recruitment_pipeline/metrics",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic HR artifacts
distractor_files = {
    "hr_department/job_postings/2024/senior_backend_engineer_jd_v1.txt": """Senior Backend Engineer (Draft v1)
Location: Shanghai / Remote
Department: Core Infrastructure

Requirements:
- 5+ years backend development experience
- Proficiency in Java or Go
- Microservices architecture experience
- SQL and NoSQL database expertise
- Experience with payment systems preferred
""",
    "hr_department/job_postings/2024/senior_backend_engineer_jd_FINAL.txt": """Senior Backend Engineer - Fintech Core Platform
Company: FinBridge Technologies
Location: Beijing / Hybrid
Department: Payment Infrastructure

Key Responsibilities:
- Design and develop high-concurrency payment processing systems
- Architect microservices using Java/Spring Boot and Go
- Ensure 99.99% system availability for transaction-critical services
- Lead technical design reviews and mentor junior engineers
- Collaborate with risk and compliance teams on regulatory requirements

Requirements:
- 6+ years of backend development experience
- Expert-level Java (Spring Boot, Spring Cloud) or Go
- Deep understanding of distributed systems and microservices
- Experience with Kafka, Redis, MySQL, and MongoDB
- Fintech domain knowledge (payment gateways, clearing systems) is a strong plus
- Bachelor's degree in Computer Science or related field
- Strong problem-solving skills and ownership mindset
""",
    "hr_department/job_postings/2023_archive/junior_backend_engineer.txt": """Junior Backend Engineer (2023)
Archived position - filled on 2023-08-15
""",
    "hr_department/candidates/shortlisted/candidate_profile_template.txt": """CANDIDATE PROFILE TEMPLATE
Name: [FULL NAME]
Applied Position: [POSITION]
Source: [LinkedIn / Referral / Job Board]
Interview Stage: [Phone Screen / Technical / Final]
""",
    "hr_department/candidates/shortlisted/li_wei_resume_raw.txt": """Li Wei
Email: liwei.dev@gmail.com | Phone: +86-138-xxxx-xxxx | GitHub: github.com/liwei-dev

EXPERIENCE:
Software Engineer, Alibaba Cloud (2019-2023) - 4 years
  - Built distributed data pipelines using Java and Apache Flink
  - Developed REST APIs for cloud storage services (Spring Boot)
  - Worked with MySQL, Redis caching layer for high-traffic services
  - Participated in code reviews, wrote unit and integration tests

Software Engineer, Startup XYZ (2017-2019) - 2 years
  - Full-stack development using Python Flask and Vue.js
  - Basic microservices architecture

EDUCATION:
Bachelor of Science, Software Engineering - Nanjing University (2013-2017)

SKILLS:
Languages: Java (proficient), Python (familiar), Go (basic learning)
Frameworks: Spring Boot, Flask
Databases: MySQL, Redis
Tools: Git, Docker, Jenkins
Certifications: None

NOTES:
- No direct fintech/payment systems experience
- Limited Kafka experience (only academic projects)
- Strong Java fundamentals, but Go is self-described as basic
""",
    "hr_department/candidates/rejected/previous_candidates_log.csv": """candidate_id,name,position,outcome,date
001,Wang Fang,Senior Backend Engineer,Rejected - insufficient experience,2024-01-10
002,Chen Ming,Senior Backend Engineer,Rejected - failed technical assessment,2024-02-05
003,Liu Yang,Senior Backend Engineer,Offer declined,2024-03-01
""",
    "hr_department/interview_templates/engineering/generic_tech_interview.md": """# Generic Technical Interview Template

## Round 1: Phone Screen (30 min)
- Background and motivation
- Basic technical knowledge check

## Round 2: Technical Assessment (90 min)
- Coding challenge
- System design question

## Round 3: Final Interview (60 min)
- Culture fit
- Leadership and soft skills
""",
    "hr_department/interview_templates/product/pm_interview_questions.md": """# Product Manager Interview Questions
1. Tell me about a product you launched from 0 to 1.
2. How do you prioritize features with conflicting stakeholder demands?
3. Describe a time you used data to make a product decision.
""",
    "hr_department/offer_letters/offer_template_2024.docx.txt": """[OFFER LETTER TEMPLATE - TEXT PREVIEW]
Dear [CANDIDATE_NAME],
We are pleased to extend an offer for the position of [POSITION] at FinBridge Technologies...
""",
    "hr_department/onboarding/documents/new_hire_checklist.md": """# New Hire Checklist
- [ ] Sign employment contract
- [ ] Set up company email
- [ ] Complete compliance training
- [ ] Meet with manager for 30-60-90 day plan
""",
    "hr_department/policies/interview_scoring_policy.txt": """Interview Scoring Policy v2.3
All interviewers must submit scores within 24 hours of the interview.
Use the standardized scoring rubric provided by HR.
Scores are on a 1-5 scale per competency.
""",
    "recruitment_pipeline/pipeline_tracker/q2_2024_pipeline.csv": """stage,count,conversion_rate
Applications,245,100%
Phone Screen,87,35.5%
Technical Round,32,36.8%
Final Interview,12,37.5%
Offers Extended,5,41.7%
Offers Accepted,3,60.0%
""",
    "recruitment_pipeline/sourcing_channels/channel_effectiveness.txt": """Q1 2024 Sourcing Analysis:
- LinkedIn: 45% of applications, 60% of hires
- Employee Referrals: 20% of applications, 30% of hires
- Job Boards: 35% of applications, 10% of hires
""",
    "recruitment_pipeline/metrics/time_to_hire_2024.txt": """Average Time to Hire (2024 YTD):
Engineering roles: 42 days
Product roles: 35 days
Operations roles: 28 days
Target: <30 days for all roles
""",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")

print("Workspace initialized with HR department structure and distractor files.")
print(f"Files created: {len(distractor_files)}")
print("\nKey files for the task:")
print("  JD: hr_department/job_postings/2024/senior_backend_engineer_jd_FINAL.txt")
print("  Resume: hr_department/candidates/shortlisted/li_wei_resume_raw.txt")