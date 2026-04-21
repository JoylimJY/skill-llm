import json
import os
from datetime import datetime, timedelta
import random

random.seed(42)

# Create mock Claude Code chat history
history_dir = os.path.expanduser('~/.claude')
os.makedirs(history_dir, exist_ok=True)

# Generate realistic chat entries for the past 48 hours
base_time = datetime.now() - timedelta(hours=48)
chat_entries = []

# Entry 1: TypeScript debugging session
chat_entries.append({
    'display': 'I\'m having trouble with TypeScript types in my auth config. The connection object has optional fields but I keep getting type errors when accessing them.',
    'project': 'showcase-app',
    'timestamp': int((base_time + timedelta(hours=2)).timestamp() * 1000),
    'pastedContents': 'interface ConnectionConfig {\n  id: string;\n  name: string;\n  auth?: {\n    token?: string;\n    apiKey?: string;\n  };\n}\n\nfunction validateConnection(conn: ConnectionConfig) {\n  // Error: Object is possibly undefined\n  if (conn.auth.token) {\n    return true;\n  }\n  return false;\n}'
})

# Entry 2: Security concern with data display
chat_entries.append({
    'display': 'I just noticed that my "Your Apps" page is showing the full connection data including auth configs in the console. This is a security issue - users shouldn\'t see API keys and tokens. How do I filter this sensitive data before displaying?',
    'project': 'showcase-app',
    'timestamp': int((base_time + timedelta(hours=8)).timestamp() * 1000),
    'pastedContents': 'const ConnectionCard = ({ connection }) => {\n  console.log("Full connection:", connection); // PROBLEM: Shows auth tokens\n  return (\n    <div className="connection-card">\n      <h3>{connection.name}</h3>\n      <pre>{JSON.stringify(connection, null, 2)}</pre>\n    </div>\n  );\n};'
})

# Entry 3: React component architecture question
chat_entries.append({
    'display': 'Working on the Marketplace UI component. I have a design mockup and need to recreate it. The layout needs to be responsive and handle different screen sizes. Currently having issues with content overflowing containers.',
    'project': 'marketplace-ui',
    'timestamp': int((base_time + timedelta(hours=16)).timestamp() * 1000),
    'pastedContents': 'const MarketplaceGrid = () => {\n  return (\n    <div className="marketplace-container">\n      {tools.map(tool => (\n        <div className="tool-card">\n          <h3>{tool.name}</h3>\n          <p>{tool.description}</p>\n          // Content is overflowing on mobile\n        </div>\n      ))}\n    </div>\n  );\n};\n\n.marketplace-container {\n  display: flex;\n  flex-wrap: wrap;\n  gap: 1rem;\n}\n\n.tool-card {\n  width: 300px; // Fixed width causing overflow\n  padding: 1rem;\n  border: 1px solid #ccc;\n}'
})

# Entry 4: Database query optimization
chat_entries.append({
    'display': 'This database query is running slowly. I\'ve rewritten it three times but still having performance issues. Need help optimizing the joins and indexes.',
    'project': 'api-backend',
    'timestamp': int((base_time + timedelta(hours=24)).timestamp() * 1000),
    'pastedContents': 'SELECT u.*, c.*, a.* \nFROM users u\nJOIN connections c ON u.id = c.user_id\nJOIN auth_configs a ON c.id = a.connection_id\nWHERE u.status = "active"\nAND c.created_at > "2024-01-01"\nORDER BY c.created_at DESC;\n\n-- This query takes 2+ seconds with 10k users'
})

# Entry 5: Async/await patterns and race conditions
chat_entries.append({
    'display': 'Having timing issues with my API calls. Sometimes the auth token expires before the main request completes, causing race conditions. How should I handle token refresh properly with async/await?',
    'project': 'api-client',
    'timestamp': int((base_time + timedelta(hours=32)).timestamp() * 1000),
    'pastedContents': 'async function makeAuthenticatedRequest(url, options) {\n  let token = await getToken();\n  \n  // Problem: token might expire between these calls\n  const response = await fetch(url, {\n    ...options,\n    headers: {\n      Authorization: `Bearer ${token}`,\n      ...options.headers\n    }\n  });\n  \n  if (response.status === 401) {\n    // Token expired, need to refresh and retry\n    token = await refreshToken();\n    // But this creates a race condition...\n  }\n  \n  return response;\n}'
})

# Entry 6: Error handling patterns
chat_entries.append({
    'display': 'I keep finding bugs where my app crashes on null values. Need better error handling and validation patterns. What\'s the best way to handle edge cases gracefully?',
    'project': 'showcase-app',
    'timestamp': int((base_time + timedelta(hours=40)).timestamp() * 1000),
    'pastedContents': 'function processUserData(userData) {\n  // These all crash if userData is null/undefined\n  const name = userData.profile.name.toUpperCase();\n  const email = userData.contact.email.toLowerCase();\n  const lastLogin = new Date(userData.activity.lastLogin);\n  \n  return {\n    displayName: name,\n    email: email,\n    lastActive: lastLogin\n  };\n}\n\n// Called with: processUserData(null) -> CRASH'
})

# Write the history file
with open(os.path.join(history_dir, 'history.jsonl'), 'w') as f:
    for entry in chat_entries:
        f.write(json.dumps(entry) + '\n')

# Create a mock HackerNews search response for testing
mock_articles = [
    {
        'title': 'TypeScript Advanced Patterns: Discriminated Unions and Type Guards',
        'url': 'https://example.com/typescript-patterns',
        'score': 245,
        'comments': 67,
        'date': '2024-10-15',
        'summary': 'Comprehensive guide to advanced TypeScript patterns'
    },
    {
        'title': 'Securing Frontend Applications: Data Filtering and Information Hiding',
        'url': 'https://example.com/frontend-security',
        'score': 312,
        'comments': 89,
        'date': '2024-10-12',
        'summary': 'Best practices for handling sensitive data in web apps'
    },
    {
        'title': 'React Component Architecture: Composition Over Configuration',
        'url': 'https://example.com/react-composition',
        'score': 198,
        'comments': 45,
        'date': '2024-10-08',
        'summary': 'Scalable component patterns for modern React apps'
    },
    {
        'title': 'Database Query Optimization Techniques',
        'url': 'https://example.com/db-optimization',
        'score': 276,
        'comments': 92,
        'date': '2024-10-05',
        'summary': 'Practical approaches to query performance tuning'
    }
]

# Save mock articles for the tool to find
with open('mock_hackernews_data.json', 'w') as f:
    json.dump(mock_articles, f, indent=2)

print('Generated mock chat history and HackerNews data')