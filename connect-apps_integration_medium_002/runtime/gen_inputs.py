import json
import os

# Create a sample API response template
api_response_template = {
    "status": "success",
    "message": "Email sent successfully",
    "email_id": "mock_email_12345",
    "recipient": "test@example.com",
    "timestamp": "2024-01-15T10:30:00Z"
}

# Create mock plugin structure
os.makedirs("plugins", exist_ok=True)
with open("plugins/composio_toolrouter_info.txt", "w") as f:
    f.write("Plugin: composio-toolrouter\nVersion: 1.0.0\nStatus: Available for installation")

# Create setup instructions file
with open("setup_instructions.txt", "w") as f:
    f.write("To complete setup:\n1. Get API key from platform.composio.dev\n2. Configure OAuth for apps\n3. Test connection")

# Create example API response
with open("mock_api_response.json", "w") as f:
    json.dump(api_response_template, f, indent=2)