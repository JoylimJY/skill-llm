import os
import json

# Create mock plugin directory structure
os.makedirs('.claude/plugins', exist_ok=True)

# Create mock composio plugin config
plugin_config = {
    'name': 'composio-toolrouter',
    'version': '1.0.0',
    'status': 'installed',
    'api_key': 'mock_api_key_12345'
}

with open('.claude/plugins/composio-toolrouter.json', 'w') as f:
    json.dump(plugin_config, f, indent=2)

# Create mock API responses directory
os.makedirs('mock_responses', exist_ok=True)

# Mock successful email response
email_response = {
    'success': True,
    'message_id': 'msg_abc123',
    'recipient': 'dev-notifications@example.com',
    'subject': 'Setup Test',
    'status': 'sent'
}

with open('mock_responses/email_response.json', 'w') as f:
    json.dump(email_response, f, indent=2)

# Mock successful GitHub issue response
github_response = {
    'success': True,
    'issue_number': 42,
    'repository': 'myorg/test-repo',
    'title': 'Automated notification setup complete',
    'url': 'https://github.com/myorg/test-repo/issues/42',
    'status': 'created'
}

with open('mock_responses/github_response.json', 'w') as f:
    json.dump(github_response, f, indent=2)

# Mock successful Slack response
slack_response = {
    'success': True,
    'channel': '#dev-updates',
    'message': 'Composio integration is now live and ready for automated workflows',
    'timestamp': '1640995200.123456',
    'status': 'posted'
}

with open('mock_responses/slack_response.json', 'w') as f:
    json.dump(slack_response, f, indent=2)

# Create setup verification markers
setup_markers = {
    'plugin_installed': True,
    'api_configured': True,
    'oauth_completed': True,
    'test_connections': True
}

with open('setup_status.json', 'w') as f:
    json.dump(setup_markers, f, indent=2)