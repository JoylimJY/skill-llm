import os
import json

# Create a mock Rube configuration
rube_config = {
    'slack': {
        'workspace': 'team-workspace',
        'channels': {
            'skills-updates': 'C1234567890'
        },
        'bot_token': 'xoxb-mock-token'
    }
}

with open('rube_config.json', 'w') as f:
    json.dump(rube_config, f, indent=2)

# Create a mock Rube API response
slack_response = {
    'ok': True,
    'channel': 'C1234567890',
    'ts': '1234567890.123',
    'message': {
        'text': 'New skill shared successfully'
    }
}

with open('expected_slack_response.json', 'w') as f:
    json.dump(slack_response, f, indent=2)

print('Mock configuration files created successfully')