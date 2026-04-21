import json
import os
from datetime import datetime, timedelta
import random

random.seed(42)

# Create .claude directory
os.makedirs('.claude', exist_ok=True)

# Generate realistic chat history with coding patterns
current_time = datetime.now()
base_timestamp = int((current_time - timedelta(hours=30)).timestamp() * 1000)

chat_entries = [
    {
        "display": "Help me debug this TypeScript error: Property 'id' does not exist on type 'Connection | undefined'",
        "project": "api-connector",
        "timestamp": base_timestamp + 1000000,
        "pastedContents": "interface Connection { id: string; name: string; auth?: AuthConfig; }\nconst conn = connections.find(c => c.name === 'slack');\nconsole.log(conn.id); // Error here"
    },
    {
        "display": "I'm getting a race condition in my async function. The data sometimes comes back undefined",
        "project": "api-connector", 
        "timestamp": base_timestamp + 2000000,
        "pastedContents": "async function fetchUserData(userId) {\n  const user = await getUser(userId);\n  const profile = await getProfile(user.id);\n  return { ...user, profile };\n}"
    },
    {
        "display": "How do I properly handle authentication tokens in React components without exposing them?",
        "project": "dashboard-ui",
        "timestamp": base_timestamp + 3000000,
        "pastedContents": "const Dashboard = () => {\n  const [connections, setConnections] = useState([]);\n  \n  useEffect(() => {\n    // This shows full auth config in console\n    console.log('Connections:', connections);\n  }, [connections]);\n};"
    },
    {
        "display": "My CSS layout is breaking on mobile. The sidebar overflows the container",
        "project": "dashboard-ui",
        "timestamp": base_timestamp + 4000000,
        "pastedContents": ".sidebar { position: fixed; width: 300px; height: 100vh; }\n.main-content { margin-left: 300px; padding: 20px; }"
    },
    {
        "display": "I need to optimize this database query. It's taking 2+ seconds with large datasets",
        "project": "api-connector",
        "timestamp": base_timestamp + 5000000,
        "pastedContents": "SELECT * FROM connections c\nJOIN auth_configs a ON c.id = a.connection_id\nWHERE c.user_id = ? AND c.status = 'active'\nORDER BY c.created_at DESC;"
    },
    {
        "display": "Help me implement proper error boundaries in React for better error handling",
        "project": "dashboard-ui",
        "timestamp": base_timestamp + 6000000,
        "pastedContents": "class ErrorBoundary extends React.Component {\n  constructor(props) {\n    super(props);\n    this.state = { hasError: false };\n  }\n  // Need help with componentDidCatch\n}"
    },
    {
        "display": "I keep getting 'Cannot read property of null' errors. How do I add better null checks?",
        "project": "api-connector",
        "timestamp": base_timestamp + 7000000,
        "pastedContents": "function processConnection(conn) {\n  return {\n    id: conn.id,\n    name: conn.name.toUpperCase(),\n    authType: conn.auth.type\n  };\n}"
    },
    {
        "display": "My TypeScript interfaces are getting complex. How do I use utility types to simplify them?",
        "project": "api-connector",
        "timestamp": base_timestamp + 8000000,
        "pastedContents": "interface CreateConnectionRequest {\n  name: string;\n  type: 'slack' | 'github' | 'notion';\n  auth: AuthConfig;\n  settings: ConnectionSettings;\n}\n\ninterface UpdateConnectionRequest {\n  // Almost identical to CreateConnectionRequest but id required, some fields optional\n}"
    }
]

# Write chat history
with open('.claude/history.jsonl', 'w') as f:
    for entry in chat_entries:
        f.write(json.dumps(entry) + '\n')

print("Generated chat history with coding patterns and improvement opportunities")