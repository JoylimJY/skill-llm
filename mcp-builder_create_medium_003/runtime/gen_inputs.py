#!/usr/bin/env python3
import json
import os

os.makedirs('src', exist_ok=True)

# Create package.json
package_json = {
    "name": "tasks-mcp-server",
    "version": "1.0.0",
    "description": "MCP server for task management API",
    "type": "module",
    "main": "dist/index.js",
    "scripts": {
        "build": "tsc",
        "start": "node dist/index.js",
        "dev": "tsx watch src/index.ts"
    },
    "engines": {"node": ">=18"},
    "dependencies": {
        "@modelcontextprotocol/sdk": "^1.6.1",
        "axios": "^1.7.9",
        "zod": "^3.23.8"
    },
    "devDependencies": {
        "@types/node": "^22.10.0",
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
        "sourceMap": True,
        "allowSyntheticDefaultImports": True
    },
    "include": ["src/**/*"],
    "exclude": ["node_modules", "dist"]
}

with open('tsconfig.json', 'w') as f:
    json.dump(tsconfig, f, indent=2)

# Create mock task data file
mock_tasks = {
    "tasks": [
        {"id": "T001", "title": "MARKER-TASK-001", "description": "First task", "status": "open", "priority": "high"},
        {"id": "T002", "title": "MARKER-TASK-002", "description": "Second task", "status": "closed", "priority": "low"},
        {"id": "T003", "title": "MARKER-TASK-003", "description": "Third task", "status": "open", "priority": "medium"},
        {"id": "T004", "title": "MARKER-TASK-004", "description": "Fourth task", "status": "open", "priority": "high"},
        {"id": "T005", "title": "MARKER-TASK-005", "description": "Fifth task", "status": "closed", "priority": "medium"}
    ]
}

with open('mock_tasks.json', 'w') as f:
    json.dump(mock_tasks, f, indent=2)

print("Generated input files: package.json, tsconfig.json, mock_tasks.json")
