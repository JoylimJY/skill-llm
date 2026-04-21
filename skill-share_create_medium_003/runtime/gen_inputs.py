#!/usr/bin/env python3

import os
import json

# Create mock Rube API responses directory
os.makedirs('rube_responses', exist_ok=True)

# Mock Slack channel discovery response
slack_channels = {
    'channels': [
        {'id': 'C123456', 'name': 'dev-tools', 'is_member': True},
        {'id': 'C789012', 'name': 'general', 'is_member': True}
    ]
}
with open('rube_responses/slack_channels.json', 'w') as f:
    json.dump(slack_channels, f)

# Mock successful message post response
post_response = {
    'ok': True,
    'channel': 'C123456',
    'ts': '1234567890.123456',
    'message': {
        'text': 'New Skill Created: json-validator',
        'user': 'U123456789'
    }
}
with open('rube_responses/message_post.json', 'w') as f:
    json.dump(post_response, f)

# Create a simple test JSON file for validation examples
test_json = {
    'name': 'test-data',
    'version': '1.0.0',
    'items': ['apple', 'banana', 'cherry']
}
with open('test_data.json', 'w') as f:
    json.dump(test_json, f, indent=2)

print('Generated input files for skill creation task')