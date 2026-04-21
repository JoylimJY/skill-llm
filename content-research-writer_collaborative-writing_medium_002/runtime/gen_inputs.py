import os
import json

# Create a sample existing draft that the user might have
existing_intro = '''# Remote Team Productivity: A New Era

Remote work is becoming more popular. Many companies are adopting remote work policies. This article will discuss some ways to improve productivity when working remotely.

Remote work has benefits and challenges. Teams need to adapt their processes.
'''

with open('existing-intro.md', 'w') as f:
    f.write(existing_intro)

# Create some mock research data that the AI can "find"
mock_research_data = {
    "productivity_stats": [
        {"stat": "77% of remote workers report higher productivity", "source": "Buffer State of Remote Work 2024"},
        {"stat": "Remote workers save 54 minutes daily on commuting", "source": "FlexJobs Remote Work Survey 2024"},
        {"stat": "Companies see 25% less turnover with remote options", "source": "Harvard Business Review Remote Work Study 2024"}
    ],
    "challenges": [
        {"challenge": "Communication gaps", "percentage": "43%", "source": "Gallup Remote Work Report 2024"},
        {"challenge": "Collaboration difficulties", "percentage": "38%", "source": "Slack Future of Work Study 2024"}
    ],
    "expert_quotes": [
        {"quote": "The future of work is not about location, it's about outcomes", "author": "Dr. Sarah Chen", "title": "MIT Work Innovation Lab"}
    ]
}

with open('research-data.json', 'w') as f:
    json.dump(mock_research_data, f, indent=2)

print('Generated input files: existing-intro.md and research-data.json')