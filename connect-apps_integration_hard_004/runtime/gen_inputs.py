import os
import json

# Create mock API responses for testing
mock_responses = {
    'email_response': {
        'success': True,
        'email_id': 'email_12345',
        'message': 'Email sent successfully'
    },
    'github_response': {
        'success': True,
        'issue_id': 'issue_67890',
        'issue_number': 42,
        'message': 'Issue created successfully'
    },
    'slack_response': {
        'success': True,
        'message_id': 'msg_abcdef',
        'channel': '#general',
        'message': 'Message posted successfully'
    }
}

with open('mock_api_responses.json', 'w') as f:
    json.dump(mock_responses, f, indent=2)

# Create a sample configuration file
config = {
    'composio_api_key': 'test_api_key_xyz123',
    'apps_configured': ['gmail', 'github', 'slack'],
    'setup_complete': True
}

with open('composio_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print('Generated mock API responses and configuration files')