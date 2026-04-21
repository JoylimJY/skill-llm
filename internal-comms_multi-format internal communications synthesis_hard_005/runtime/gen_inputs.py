#!/usr/bin/env python3
import os
import json

os.makedirs('inputs', exist_ok=True)

# Create a reference document with the skill guidelines
reference = """# Internal Communications Skill Reference

## 3P Update Format
The 3P update format is:
[emoji] [Team Name] (Date Range)
Progress: [1-3 sentences]
Plans: [1-3 sentences]
Problems: [1-3 sentences]

## Key Requirements
- Very succinct and to-the-point (30-60 seconds to read)
- Data-driven with metrics where possible
- Matter-of-fact tone, not prose-heavy
- Exactly three sections
- Pick an emoji that captures the team vibe
"""

with open('inputs/skill_reference.md', 'w') as f:
    f.write(reference)

# Create sample input data
input_data = {
    "team_name": "Platform Infrastructure",
    "date_range": "January 15-19, 2024",
    "progress": [
        "Deployed database migration to production (reduced query latency by 23%)",
        "Completed code review process improvements (now 2-hour SLA)",
        "Fixed 8 critical bugs in the API gateway",
        "Onboarded 2 new engineers to the team"
    ],
    "plans": [
        "Begin work on caching layer optimization",
        "Schedule architecture review with leadership",
        "Complete documentation for new deployment pipeline",
        "Investigate performance issues in the message queue"
    ],
    "problems": [
        "One engineer out on medical leave (team at 80% capacity)",
        "Dependency upgrade blocked by incompatible third-party library",
        "Staging environment has been unstable (3 outages this week)"
    ]
}

with open('inputs/team_data.json', 'w') as f:
    json.dump(input_data, f, indent=2)

print("Input files created successfully")
