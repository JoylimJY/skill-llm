import json
import os
import time
from datetime import datetime, timedelta

# Create .claude directory
os.makedirs('.claude', exist_ok=True)

# Current timestamp in milliseconds
current_time = int(time.time() * 1000)
twenty_four_hours_ago = current_time - (24 * 60 * 60 * 1000)
forty_eight_hours_ago = current_time - (48 * 60 * 60 * 1000)

# Generate realistic chat history entries
chat_entries = [
    {
        'display': 'Help me debug this TypeScript error: Property does not exist on type union',
        'project': 'e-commerce-api',
        'timestamp': current_time - (2 * 60 * 60 * 1000),
        'pastedContents': 'interface User { id: string; name: string; }\ninterface Admin { id: string; permissions: string[]; }\ntype UserOrAdmin = User | Admin;\nfunction processUser(user: UserOrAdmin) { console.log(user.permissions); }'
    },
    {
        'display': 'How do I implement proper error handling in this async function?',
        'project': 'inventory-service', 
        'timestamp': current_time - (4 * 60 * 60 * 1000),
        'pastedContents': 'async function fetchInventory(productId) {\n  const response = await fetch(`/api/products/${productId}`);\n  const data = await response.json();\n  return data;\n}'
    },
    {
        'display': 'Getting race conditions in my React component state updates',
        'project': 'dashboard-ui',
        'timestamp': current_time - (6 * 60 * 60 * 1000),
        'pastedContents': 'const [loading, setLoading] = useState(false);\nconst [data, setData] = useState(null);\nconst handleRefresh = async () => {\n  setLoading(true);\n  const result = await api.getData();\n  setData(result);\n  setLoading(false);\n};'
    },
    {
        'display': 'SQL query optimization - this is running too slowly',
        'project': 'analytics-backend',
        'timestamp': current_time - (10 * 60 * 60 * 1000),
        'pastedContents': 'SELECT u.*, p.* FROM users u JOIN profiles p ON u.id = p.user_id WHERE u.created_at > ? ORDER BY u.created_at DESC'
    },
    {
        'display': 'Help me set up proper authentication middleware for Express',
        'project': 'auth-service',
        'timestamp': current_time - (18 * 60 * 60 * 1000),
        'pastedContents': 'app.use((req, res, next) => {\n  const token = req.headers.authorization;\n  if (!token) return res.status(401).send();\n  // TODO: verify token\n  next();\n});'
    },
    {
        'display': 'Docker deployment failing - container exits immediately',
        'project': 'microservice-deploy',
        'timestamp': current_time - (22 * 60 * 60 * 1000),
        'pastedContents': 'FROM node:18\nCOPY . .\nRUN npm install\nEXPOSE 3000\nCMD npm start'
    },
    {
        'display': 'How to handle null values in this API response properly?',
        'project': 'data-processor',
        'timestamp': current_time - (26 * 60 * 60 * 1000),
        'pastedContents': 'const processApiData = (response) => {\n  return response.items.map(item => ({\n    id: item.id,\n    name: item.name,\n    value: item.metadata.value\n  }));\n};'
    },
    {
        'display': 'React component re-rendering too frequently, performance issues',
        'project': 'dashboard-ui',
        'timestamp': current_time - (30 * 60 * 60 * 1000),
        'pastedContents': 'function DataTable({ data, filters }) {\n  return (\n    <div>\n      {data.filter(item => filters.includes(item.category)).map(item => <Row key={item.id} data={item} />)}\n    </div>\n  );\n}'
    },
    {
        'display': 'Git merge conflicts in package.json, how to resolve cleanly?',
        'project': 'team-collaboration',
        'timestamp': current_time - (35 * 60 * 60 * 1000),
        'pastedContents': '{\n  "dependencies": {\n<<<<<<< HEAD\n    "react": "^18.2.0",\n    "lodash": "^4.17.21"\n=======\n    "react": "^18.1.0",\n    "axios": "^1.2.0"\n>>>>>>> feature-branch\n  }\n}'
    },
    {
        'display': 'TypeScript generic constraints not working as expected',
        'project': 'type-safe-api',
        'timestamp': current_time - (40 * 60 * 60 * 1000),
        'pastedContents': 'function updateEntity<T extends { id: string }>(entity: T, updates: Partial<T>): T {\n  return { ...entity, ...updates };\n}\n// Error: Type does not satisfy constraint'
    }
]

# Write to history.jsonl
with open('.claude/history.jsonl', 'w') as f:
    for entry in chat_entries:
        f.write(json.dumps(entry) + '\n')

print(f'Generated {len(chat_entries)} chat history entries')
print(f'Time range: {forty_eight_hours_ago} to {current_time}')