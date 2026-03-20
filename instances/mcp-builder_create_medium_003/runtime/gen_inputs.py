#!/usr/bin/env python3
import json
import os

# Create package.json
package_json = {
    "name": "todoist-mcp-server",
    "version": "1.0.0",
    "description": "MCP server for Todoist API integration",
    "type": "module",
    "main": "dist/index.js",
    "scripts": {
        "start": "node dist/index.js",
        "dev": "tsx watch src/index.ts",
        "build": "tsc",
        "clean": "rm -rf dist"
    },
    "engines": {
        "node": ">=18"
    },
    "dependencies": {
        "@modelcontextprotocol/sdk": "^1.6.1",
        "axios": "^1.7.9",
        "zod": "^3.23.8",
        "express": "^4.18.2"
    },
    "devDependencies": {
        "@types/node": "^22.10.0",
        "@types/express": "^4.17.21",
        "tsx": "^4.19.2",
        "typescript": "^5.7.2"
    }
}

with open('package.json', 'w') as f:
    json.dump(package_json, f, indent=2)

# Create tsconfig.json
tsconfig = {
    "compilerOptions": {
        "target": "ES2022",
        "module": "Node16",
        "moduleResolution": "Node16",
        "lib": ["ES2022"],
        "outDir": "./dist",
        "rootDir": "./src",
        "strict": True,
        "esModuleInterop": True,
        "skipLibCheck": True,
        "forceConsistentCasingInFileNames": True,
        "declaration": True,
        "declarationMap": True,
        "sourceMap": True,
        "allowSyntheticDefaultImports": True
    },
    "include": ["src/**/*"],
    "exclude": ["node_modules", "dist"]
}

with open('tsconfig.json', 'w') as f:
    json.dump(tsconfig, f, indent=2)

# Create requirements.txt for evaluation
requirements = '''anthropic>=0.35.0
mcp>=1.4.1
httpx>=0.27.0
'''

with open('requirements.txt', 'w') as f:
    f.write(requirements)

# Create mock Todoist API responses for testing
mock_data = {
    "projects": [
        {
            "id": "2203306141",
            "name": "Work Projects",
            "comment_count": 0,
            "order": 1,
            "color": "blue",
            "is_shared": False,
            "is_favorite": False,
            "is_inbox_project": False,
            "is_team_inbox": False,
            "view_style": "list",
            "url": "https://todoist.com/showProject?id=2203306141"
        },
        {
            "id": "2203306142",
            "name": "Personal Tasks",
            "comment_count": 5,
            "order": 2,
            "color": "green",
            "is_shared": False,
            "is_favorite": True,
            "is_inbox_project": False,
            "is_team_inbox": False,
            "view_style": "list",
            "url": "https://todoist.com/showProject?id=2203306142"
        }
    ],
    "tasks": [
        {
            "id": "2995104339",
            "assigner_id": None,
            "assignee_id": None,
            "project_id": "2203306141",
            "section_id": None,
            "parent_id": None,
            "order": 1,
            "content": "Complete quarterly report analysis",
            "description": "Analyze Q3 performance metrics and prepare executive summary",
            "is_completed": False,
            "labels": ["urgent", "work"],
            "priority": 4,
            "comment_count": 2,
            "creator_id": "2671355",
            "created_at": "2024-01-15T09:30:00Z",
            "due": {
                "date": "2024-01-20",
                "string": "Jan 20",
                "lang": "en",
                "is_recurring": False
            },
            "url": "https://todoist.com/showTask?id=2995104339"
        },
        {
            "id": "2995104340",
            "assigner_id": None,
            "assignee_id": None,
            "project_id": "2203306142",
            "section_id": None,
            "parent_id": None,
            "order": 2,
            "content": "Buy groceries for dinner party",
            "description": "Get ingredients for pasta dish and wine",
            "is_completed": False,
            "labels": ["personal", "shopping"],
            "priority": 2,
            "comment_count": 0,
            "creator_id": "2671355",
            "created_at": "2024-01-16T14:20:00Z",
            "due": {
                "date": "2024-01-18",
                "string": "Jan 18",
                "lang": "en",
                "is_recurring": False
            },
            "url": "https://todoist.com/showTask?id=2995104340"
        },
        {
            "id": "2995104341",
            "assigner_id": None,
            "assignee_id": None,
            "project_id": "2203306141",
            "section_id": None,
            "parent_id": None,
            "order": 3,
            "content": "Review team performance metrics",
            "description": "Monthly review of team KPIs and productivity scores",
            "is_completed": True,
            "labels": ["work", "management"],
            "priority": 3,
            "comment_count": 1,
            "creator_id": "2671355",
            "created_at": "2024-01-10T11:15:00Z",
            "due": None,
            "url": "https://todoist.com/showTask?id=2995104341"
        }
    ]
}

with open('mock_todoist_data.json', 'w') as f:
    json.dump(mock_data, f, indent=2)

# Create evaluation template - this will be used to verify the generated evaluation
eval_template = {
    "expected_questions": 10,
    "required_elements": [
        "multi-hop questions requiring deep exploration",
        "questions requiring understanding context without keyword matching", 
        "complex aggregation requiring multiple steps",
        "questions requiring synthesis across multiple data types"
    ],
    "answer_requirements": [
        "single verifiable values",
        "human-readable formats preferred",
        "stable/stationary answers", 
        "clear and unambiguous",
        "diverse modalities"
    ]
}

with open('eval_template.json', 'w') as f:
    json.dump(eval_template, f, indent=2)

print("Generated input files with embedded verification markers")