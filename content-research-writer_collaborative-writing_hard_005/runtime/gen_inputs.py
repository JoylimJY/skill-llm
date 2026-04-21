import os
import json

# Create sample research data that the AI can reference
research_data = {
    "productivity_stats": [
        "Stanford study shows 13% productivity increase in remote workers (Bloom, 2015)",
        "GitLab survey: 82% report same or higher productivity when remote (GitLab, 2023)",
        "Microsoft found 66% struggle with collaboration in hybrid model (Microsoft, 2022)"
    ],
    "expert_quotes": [
        "Remote work isn't just about location flexibility—it's about reimagining how we measure and achieve productivity - Dr. Sarah Chen, MIT",
        "The key is intentional communication, not constant communication - Marcus Rodriguez, Harvard Business Review"
    ],
    "case_studies": [
        "Basecamp: 4-day work week with full remote resulted in 20% revenue growth",
        "Buffer: Async-first culture led to 95% employee satisfaction scores",
        "Automattic: 1,200+ fully distributed employees, $7.5B valuation"
    ]
}

# Create a mock research file
with open('available-research.json', 'w') as f:
    json.dump(research_data, f, indent=2)

# Create some sample industry reports
reports = {
    "remote_work_trends_2023.txt": "MARKER_TREND_DATA: 42% of companies plan permanent remote options. Productivity metrics show mixed results across industries.",
    "collaboration_study.txt": "MARKER_COLLAB_STUDY: Teams using structured async communication tools report 28% better project completion rates.",
    "employee_satisfaction.txt": "MARKER_SATISFACTION: Remote workers show 22% higher job satisfaction but 15% report feeling disconnected from company culture."
}

for filename, content in reports.items():
    with open(filename, 'w') as f:
        f.write(content)

print("Research files created successfully")