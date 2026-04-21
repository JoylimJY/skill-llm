import os
import json

# Create sample component requirements
with open('component_requirements.json', 'w') as f:
    json.dump({
        'components': [
            {'name': 'Button', 'props': ['variant', 'size', 'disabled']},
            {'name': 'Input', 'props': ['type', 'placeholder', 'value']}
        ],
        'theme': 'modern',
        'typescript': True
    }, f, indent=2)

# Create existing partial skill structure for testing iteration
os.makedirs('partial-skill', exist_ok=True)
with open('partial-skill/SKILL.md', 'w') as f:
    f.write('''---
name: incomplete-skill
description: This is a partial skill for testing
---

# Incomplete Skill

This skill needs to be completed.
''')

print('Generated component requirements and partial skill structure')