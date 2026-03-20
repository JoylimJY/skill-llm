#!/usr/bin/env python3
import json
import os

# Create a mock GitHub API responses file for testing
mock_responses = {
    "search_repos_python": {
        "total_count": 2,
        "items": [
            {
                "id": 12345,
                "name": "python-demo",
                "full_name": "testuser/python-demo",
                "description": "A demo Python project",
                "html_url": "https://github.com/testuser/python-demo",
                "stargazers_count": 42,
                "language": "Python"
            },
            {
                "id": 67890,
                "name": "py-utils",
                "full_name": "devuser/py-utils",
                "description": "Python utilities collection",
                "html_url": "https://github.com/devuser/py-utils",
                "stargazers_count": 15,
                "language": "Python"
            }
        ]
    },
    "user_testuser": {
        "login": "testuser",
        "id": 123,
        "name": "Test User",
        "email": "test@example.com",
        "bio": "Software developer",
        "public_repos": 5,
        "followers": 10,
        "following": 8,
        "html_url": "https://github.com/testuser"
    }
}

with open('mock_github_responses.json', 'w') as f:
    json.dump(mock_responses, f, indent=2)

# Create requirements file
with open('requirements.txt', 'w') as f:
    f.write('fastmcp\npydantic\nhttpx\n')

print("Generated input files for GitHub MCP server task")