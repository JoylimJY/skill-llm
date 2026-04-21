import json

# Generate input job description and candidate background in separate text files

def main():
    job_description = '''Software Engineer at Innovatech
Responsibilities:
- Develop scalable backend services using Python and Django
- Collaborate with frontend teams building React applications
- Write unit and integration tests
- Optimize performance and scalability
- Familiarity with AWS cloud infrastructure preferred
- Strong problem-solving and communication skills required
Qualifications:
- 3+ years professional software engineering experience
- Proficient in Python, Django, and React
- Experience with CI/CD pipelines and testing frameworks
- Bachelor’s degree in Computer Science or related field'''

    background = '''Software Engineer at DevSolutions since 2020 (3 years)
- Developed backend REST APIs using Python and Flask
- Worked with React frontend developers to integrate APIs
- Built automated tests increasing code coverage to 80%
- Familiar with AWS EC2, S3 services
- Bachelor of Science in Computer Science from State University'''

    # Write to files
    with open('job_description.txt', 'w') as f:
        f.write(job_description)

    with open('background.txt', 'w') as f:
        f.write(background)

if __name__ == '__main__':
    main()