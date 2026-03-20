#!/usr/bin/env python3
import os
import json

# Create a simple project context file
project_context = {
    "project_name": "UserService API",
    "team": "Backend Platform",
    "existing_endpoints": ["/users/create", "/users/list", "/users/{id}"],
    "tech_stack": "Python Flask, PostgreSQL",
    "marker_content": "EVAL_MARKER_PROJECT_CONTEXT_12345"
}

with open('project_context.json', 'w') as f:
    json.dump(project_context, f, indent=2)

# Create a requirements file with marker content
requirements = """# API Design Requirements - EVAL_MARKER_REQUIREMENTS_67890

1. New endpoint: POST /users/{id}/preferences
2. Accept JSON payload with user preferences
3. Validate input data
4. Store in database
5. Return updated user object

Security: Require authentication token
Performance: Response time < 200ms
Compatibility: Maintain backward compatibility
"""

with open('requirements.txt', 'w') as f:
    f.write(requirements)

print("Generated input files with marker content for evaluation")