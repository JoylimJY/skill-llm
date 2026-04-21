import json
import time
import os
from datetime import datetime, timedelta

# Create .claude directory
os.makedirs('.claude', exist_ok=True)

# Generate realistic chat history for the past 48 hours
current_time = int(time.time() * 1000)
base_time = current_time - (48 * 60 * 60 * 1000)  # 48 hours ago

chat_entries = [
    {
        "display": "Help me debug this TypeScript error with union types in my auth config",
        "project": "showcase-app",
        "timestamp": base_time + (2 * 60 * 60 * 1000),
        "pastedContents": "type AuthConfig = { provider: 'oauth' | 'basic'; credentials: OAuthCreds | BasicCreds }"
    },
    {
        "display": "I'm getting a type error when trying to access auth.credentials.token - how do I handle discriminated unions properly?",
        "project": "showcase-app", 
        "timestamp": base_time + (2.5 * 60 * 60 * 1000),
        "pastedContents": "if (auth.provider === 'oauth') { return auth.credentials.token; }"
    },
    {
        "display": "Create a responsive React component for displaying connection cards in a grid layout",
        "project": "marketplace-ui",
        "timestamp": base_time + (8 * 60 * 60 * 1000),
        "pastedContents": "<div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>"
    },
    {
        "display": "The connection cards are overflowing their container on mobile - how do I fix this CSS issue?",
        "project": "marketplace-ui",
        "timestamp": base_time + (8.5 * 60 * 60 * 1000),
        "pastedContents": ".card { width: 100%; overflow: hidden; }"
    },
    {
        "display": "I noticed my console is logging sensitive auth data - how do I filter this out safely?",
        "project": "showcase-app",
        "timestamp": base_time + (12 * 60 * 60 * 1000),
        "pastedContents": "console.log('Connection data:', connection); // This shows API keys!"
    },
    {
        "display": "Help me implement proper error handling for async database queries",
        "project": "backend-api",
        "timestamp": base_time + (20 * 60 * 60 * 1000),
        "pastedContents": "const result = await db.query('SELECT * FROM connections WHERE user_id = ?', [userId]);"
    },
    {
        "display": "My API is throwing unhandled promise rejections - what's the best way to catch these?",
        "project": "backend-api",
        "timestamp": base_time + (20.5 * 60 * 60 * 1000),
        "pastedContents": "app.get('/connections', async (req, res) => { const data = await fetchConnections(req.user.id); res.json(data); });"
    },
    {
        "display": "Create a deployment configuration for my Node.js app with proper environment variable handling",
        "project": "showcase-app",
        "timestamp": base_time + (30 * 60 * 60 * 1000),
        "pastedContents": "FROM node:18\nCOPY package*.json ./\nRUN npm install\nCOPY . .\nEXPOSE 3000\nCMD ['npm', 'start']"
    },
    {
        "display": "How do I properly validate API request payloads in Express.js?",
        "project": "backend-api",
        "timestamp": base_time + (35 * 60 * 60 * 1000),
        "pastedContents": "app.post('/connections', (req, res) => { // Need validation here })"
    },
    {
        "display": "Debug why my React component re-renders are causing performance issues",
        "project": "marketplace-ui",
        "timestamp": base_time + (40 * 60 * 60 * 1000),
        "pastedContents": "useEffect(() => { fetchConnections(); }, [user]); // This runs too often"
    }
]

# Write chat history to JSONL format
with open('.claude/history.jsonl', 'w') as f:
    for entry in chat_entries:
        f.write(json.dumps(entry) + '\n')

# Create mock HackerNews data file for resource curation
hackernews_data = {
    "typescript_advanced": [
        {
            "title": "TypeScript's Advanced Types: Generics, Utility Types, and Conditional Types",
            "url": "https://news.ycombinator.com/item?id=12345",
            "date": "2024-10-15",
            "score": 156,
            "comments": 42
        },
        {
            "title": "Building Type-Safe APIs in TypeScript", 
            "url": "https://news.ycombinator.com/item?id=12346",
            "date": "2024-09-22",
            "score": 98,
            "comments": 28
        }
    ],
    "security_frontend": [
        {
            "title": "Preventing Information Leakage in Web Applications",
            "url": "https://news.ycombinator.com/item?id=12347", 
            "date": "2024-08-10",
            "score": 203,
            "comments": 67
        },
        {
            "title": "OAuth and API Key Management Best Practices",
            "url": "https://news.ycombinator.com/item?id=12348",
            "date": "2024-07-18",
            "score": 142,
            "comments": 51
        }
    ],
    "error_handling": [
        {
            "title": "Robust Error Handling Patterns in Node.js",
            "url": "https://news.ycombinator.com/item?id=12349",
            "date": "2024-09-05",
            "score": 187,
            "comments": 73
        }
    ]
}

with open('hackernews_mock.json', 'w') as f:
    json.dump(hackernews_data, f, indent=2)

print("Generated chat history and mock data files")