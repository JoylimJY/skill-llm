import os
import json

# Create a mock Slack configuration for testing
slack_config = {
    "webhook_url": "https://hooks.slack.com/services/mock/webhook/url",
    "channel": "#general",
    "token": "xoxb-mock-token-12345"
}

with open('slack_config.json', 'w') as f:
    json.dump(slack_config, f, indent=2)

# Create a sample existing skill directory for reference
os.makedirs('existing-skills/sample-skill', exist_ok=True)
with open('existing-skills/sample-skill/SKILL.md', 'w') as f:
    f.write('''---
name: sample-skill
description: A sample skill for testing
license: MIT
---

# Sample Skill

This is a sample skill for reference.
''')

print('Mock environment created successfully')