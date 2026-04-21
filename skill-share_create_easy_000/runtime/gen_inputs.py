import os
import json

# Create mock Slack channel data
slack_data = {
    'channels': [
        {'id': 'C1234567890', 'name': 'general'},
        {'id': 'C0987654321', 'name': 'development'}
    ]
}

with open('slack_channels.json', 'w') as f:
    json.dump(slack_data, f, indent=2)

# Create a mock rube configuration
rube_config = {
    'slack_token': 'xoxb-mock-token-12345',
    'base_url': 'https://mock-rube-api.com'
}

with open('rube_config.json', 'w') as f:
    json.dump(rube_config, f, indent=2)

print('Generated mock Slack and Rube configuration files')