import os

def gen_input_files():
    # Write Job Description file
    job_description = '''Title: Senior Cybersecurity Analyst
Company: SecureNet Inc.
Description:
- Minimum 7 years cybersecurity experience with focus on threat detection and incident response
- Expertise with SIEM tools (Splunk preferred), intrusion detection systems, vulnerability assessments
- Strong knowledge of network protocols, firewalls, endpoint security technologies
- Experience conducting forensic investigations and malware analysis
- Familiarity with compliance standards (NIST, ISO 27001, HIPAA)
- Excellent communication skills for reporting findings to technical and non-technical audiences
- Leadership experience preferred
'''
    with open('job_description.txt', 'w', encoding='utf-8') as f:
        f.write(job_description)

    # Write current resume input
    current_resume = '''Jane Doe
Email: jane.doe@email.com | Phone: (555) 654-3210 | LinkedIn: linkedin.com/in/janedoe

Summary
Cybersecurity professional with 6 years experience in network security and risk management.

Experience
Network Security Analyst | TechGuard LLC | 2016 - 2022
- Monitored network traffic and conducted vulnerability assessments
- Assisted incident response team with malware containment and eradication
- Managed firewall configurations and access controls
- Created security awareness training for staff

Junior Cybersecurity Specialist | InfoSecure Co. | 2014 - 2016
- Supported security operations center with real-time threat monitoring
- Performed log analysis and contributed to compliance audits

Education
Bachelor of Science in Information Technology, State University, 2014

Certifications
CompTIA Security+, CEH
'''
    with open('current_resume.txt', 'w', encoding='utf-8') as f:
        f.write(current_resume)

if __name__ == '__main__':
    gen_input_files()
