#!/usr/bin/env python3
import json
import os

# Create sample Hacker News API responses for testing
sample_stories = [
    {
        "by": "dang",
        "descendants": 42,
        "id": 123456,
        "kids": [123457, 123458, 123459],
        "score": 125,
        "time": 1640995200,
        "title": "Show HN: AI-Powered Code Review Tool",
        "type": "story",
        "url": "https://example.com/ai-review"
    },
    {
        "by": "techuser",
        "descendants": 18,
        "id": 123460,
        "kids": [123461, 123462],
        "score": 67,
        "time": 1640908800,
        "title": "The Future of Web Development",
        "type": "story",
        "url": "https://example.com/web-future"
    }
]

sample_comments = [
    {
        "by": "reviewer1",
        "id": 123457,
        "kids": [123464],
        "parent": 123456,
        "text": "This looks really promising! The AI suggestions are quite accurate.",
        "time": 1640996400,
        "type": "comment"
    },
    {
        "by": "developer2",
        "id": 123458,
        "parent": 123456,
        "text": "How does this compare to existing tools like SonarQube?",
        "time": 1640997600,
        "type": "comment"
    }
]

# Create test data directory
os.makedirs('test_data', exist_ok=True)

# Write sample data files
with open('test_data/sample_stories.json', 'w') as f:
    json.dump(sample_stories, f, indent=2)

with open('test_data/sample_comments.json', 'w') as f:
    json.dump(sample_comments, f, indent=2)

# Create package.json with proper configuration
package_json = {
    "name": "hackernews-mcp-server",
    "version": "1.0.0",
    "description": "MCP server for Hacker News API integration",
    "type": "module",
    "main": "dist/index.js",
    "scripts": {
        "start": "node dist/index.js",
        "build": "tsc",
        "dev": "tsx watch src/index.ts"
    },
    "engines": {
        "node": ">=18"
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

print("Generated input files for HackerNews MCP server task")