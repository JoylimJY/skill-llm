#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta

# Set deterministic seed
import random
random.seed(12345)

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
        "@types/express": "^4.17.17",
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

# Create src directory
os.makedirs('src', exist_ok=True)

# Create mock Todoist API data for evaluations
mock_projects = [
    {"id": "proj_001", "name": "Work Projects", "color": "blue", "is_favorite": True, "url": "https://todoist.com/showProject?id=proj_001"},
    {"id": "proj_002", "name": "Personal Tasks", "color": "green", "is_favorite": False, "url": "https://todoist.com/showProject?id=proj_002"},
    {"id": "proj_003", "name": "Shopping List", "color": "red", "is_favorite": True, "url": "https://todoist.com/showProject?id=proj_003"},
    {"id": "proj_004", "name": "Home Improvements", "color": "yellow", "is_favorite": False, "url": "https://todoist.com/showProject?id=proj_004"},
    {"id": "proj_005", "name": "Learning Goals", "color": "purple", "is_favorite": True, "url": "https://todoist.com/showProject?id=proj_005"}
]

# Generate realistic tasks with marker content
tasks = []
task_counter = 1
for project in mock_projects:
    for i in range(random.randint(3, 8)):
        task_id = f"task_{task_counter:03d}"
        
        # Embed marker content that evaluation can verify
        if project['name'] == 'Work Projects':
            contents = [
                "Review quarterly budget reports EVAL_MARKER_Q4_2024",
                "Schedule team meeting for project kickoff EVAL_MARKER_KICKOFF",
                "Update client presentation slides EVAL_MARKER_SLIDES",
                "Prepare performance review documentation EVAL_MARKER_PERF_REVIEW",
                "Submit expense reports for December EVAL_MARKER_EXPENSES"
            ]
        elif project['name'] == 'Personal Tasks':
            contents = [
                "Book dentist appointment for next month EVAL_MARKER_DENTIST",
                "Organize photo album from vacation EVAL_MARKER_PHOTOS",
                "Call insurance company about policy EVAL_MARKER_INSURANCE",
                "Plan birthday party for next weekend EVAL_MARKER_BIRTHDAY",
                "Renew driver's license before expiration EVAL_MARKER_LICENSE"
            ]
        elif project['name'] == 'Shopping List':
            contents = [
                "Buy organic vegetables from farmer's market EVAL_MARKER_VEGETABLES",
                "Purchase new running shoes size 10 EVAL_MARKER_SHOES",
                "Get batteries for remote control EVAL_MARKER_BATTERIES",
                "Buy gift for wedding anniversary EVAL_MARKER_ANNIVERSARY"
            ]
        elif project['name'] == 'Home Improvements':
            contents = [
                "Install new light fixtures in kitchen EVAL_MARKER_LIGHTS",
                "Paint bedroom walls with neutral colors EVAL_MARKER_PAINT",
                "Fix leaky faucet in bathroom EVAL_MARKER_FAUCET",
                "Replace air filter in HVAC system EVAL_MARKER_FILTER"
            ]
        else:  # Learning Goals
            contents = [
                "Complete TypeScript advanced course EVAL_MARKER_TYPESCRIPT",
                "Read book about machine learning algorithms EVAL_MARKER_ML_BOOK",
                "Practice Spanish conversation skills EVAL_MARKER_SPANISH",
                "Learn basics of blockchain technology EVAL_MARKER_BLOCKCHAIN"
            ]
        
        task = {
            "id": task_id,
            "project_id": project['id'],
            "content": contents[i % len(contents)],
            "is_completed": random.choice([True, False, False, False]),  # 25% completed
            "priority": random.randint(1, 4),
            "due_date": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat() if random.random() > 0.3 else None,
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 90))).isoformat(),
            "url": f"https://todoist.com/showTask?id={task_id}"
        }
        tasks.append(task)
        task_counter += 1

# Save mock data
with open('mock_todoist_data.json', 'w') as f:
    json.dump({
        'projects': mock_projects,
        'tasks': tasks
    }, f, indent=2)

# Create README.md
readme_content = '''# Todoist MCP Server

An MCP server for integrating with Todoist API to manage tasks and projects.

## Features

- Create new tasks
- Search tasks by content or project
- List all projects
- Mark tasks as complete
- Support for both JSON and Markdown response formats
- Proper pagination and error handling

## Setup

1. Install dependencies: `npm install`
2. Build the project: `npm run build`
3. Set environment variable: `TODOIST_API_TOKEN=your_token_here`
4. Run the server: `npm start`

## Tools

- `todoist_create_task`: Create a new task
- `todoist_search_tasks`: Search for tasks
- `todoist_list_projects`: List all projects
- `todoist_complete_task`: Mark a task as complete

EVAL_MARKER_README_TODOIST
'''

with open('README.md', 'w') as f:
    f.write(readme_content)

print("Generated Todoist MCP server project structure with marker content for evaluation.")
