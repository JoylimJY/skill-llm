import json
import os

# Create a mock composio API key file
api_key_data = {
    "api_key": "comp_test_key_12345",
    "workspace_id": "ws_test_67890"
}

with open('.composio_config.json', 'w') as f:
    json.dump(api_key_data, f, indent=2)

# Create a mock plugin registry file
plugin_registry = {
    "available_plugins": [
        {
            "name": "composio-toolrouter",
            "version": "1.0.0",
            "description": "Connect to 1000+ apps",
            "status": "available"
        }
    ],
    "installed_plugins": []
}

with open('plugin_registry.json', 'w') as f:
    json.dump(plugin_registry, f, indent=2)

# Create mock email service responses
email_responses = {
    "send_email_success": {
        "status": "success",
        "message_id": "msg_test_abc123",
        "to": "test@example.com",
        "subject": "Plugin Test",
        "timestamp": "2024-01-15T10:30:00Z"
    }
}

with open('email_mock_responses.json', 'w') as f:
    json.dump(email_responses, f, indent=2)

print("Generated input files for Composio setup simulation")