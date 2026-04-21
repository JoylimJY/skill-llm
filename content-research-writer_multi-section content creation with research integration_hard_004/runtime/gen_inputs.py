import json
import os

# Create sample research materials
research_data = {
    'studies': [
        {'title': 'Remote Work Productivity Study 2024', 'author': 'McKinsey Institute', 'finding': '73% of teams report improved productivity with async tools', 'year': 2024},
        {'title': 'The State of Digital Collaboration', 'author': 'Harvard Business Review', 'finding': 'Video fatigue affects 67% of remote workers daily', 'year': 2024},
        {'title': 'Future of Work Technologies', 'author': 'MIT Technology Review', 'finding': 'AI-powered collaboration tools reduce meeting time by 40%', 'year': 2024},
        {'title': 'Remote Team Performance Analysis', 'author': 'Stanford Research', 'finding': 'Asynchronous communication increases innovation by 45%', 'year': 2023},
        {'title': 'Digital Workplace Transformation', 'author': 'Gartner Research', 'finding': '85% of companies plan to adopt new collaboration platforms by 2025', 'year': 2024}
    ],
    'expert_quotes': [
        {'name': 'Dr. Sarah Chen', 'title': 'Digital Workplace Expert, MIT', 'quote': 'The future of collaboration is not about replicating in-person interactions digitally, but creating entirely new paradigms for distributed creativity'},
        {'name': 'Marcus Rodriguez', 'title': 'CTO, TechCorp', 'quote': 'We moved beyond video calls six months ago and saw a 30% increase in project delivery speed'},
        {'name': 'Prof. Lisa Johnson', 'title': 'Organizational Psychology, Stanford', 'quote': 'Asynchronous collaboration allows for deeper thinking and more inclusive participation'}
    ]
}

with open('research_materials.json', 'w') as f:
    json.dump(research_data, f, indent=2)

# Create a sample existing draft snippet for reference
existing_draft = '''# The Future of Remote Team Collaboration: Beyond Video Calls

## Initial Thoughts
- Video calls are becoming less effective
- New tools emerging
- Need better async methods
- AI changing collaboration

## Rough Introduction
Remote work has changed how we collaborate, but most teams are still stuck in the video call trap.
'''

with open('initial_draft.md', 'w') as f:
    f.write(existing_draft)

print('Research materials and initial draft created successfully.')