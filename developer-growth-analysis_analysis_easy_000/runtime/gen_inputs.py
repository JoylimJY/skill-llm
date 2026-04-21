import json
import os
from datetime import datetime, timedelta

# Create mock Claude Code chat history
current_time = int(datetime.now().timestamp() * 1000)
day_ago = current_time - (24 * 60 * 60 * 1000)

# Create .claude directory
os.makedirs('.claude', exist_ok=True)

# Generate chat history with realistic developer patterns
chat_entries = [
    {
        "display": "Help me debug this TypeScript error with my React component props",
        "project": "e-commerce-frontend", 
        "timestamp": day_ago + (2 * 60 * 60 * 1000),
        "pastedContents": "interface Props { user?: User; onLogin: () => void; } const LoginButton = ({ user, onLogin }: Props) => { return user ? <span>Welcome {user.name}</span> : <button onClick={onLogin}>Login</button>; };"
    },
    {
        "display": "How do I properly handle async/await in this API call?",
        "project": "e-commerce-backend",
        "timestamp": day_ago + (4 * 60 * 60 * 1000),
        "pastedContents": "const fetchUserData = async (userId) => { const response = fetch(`/api/users/${userId}`); return response.json(); };"
    },
    {
        "display": "My database query is really slow, can you help optimize it?",
        "project": "e-commerce-backend",
        "timestamp": day_ago + (6 * 60 * 60 * 1000),
        "pastedContents": "SELECT * FROM orders o JOIN users u ON o.user_id = u.id JOIN products p ON o.product_id = p.id WHERE o.created_at > '2024-01-01';"
    },
    {
        "display": "Getting null pointer errors in my React component, what's wrong?",
        "project": "e-commerce-frontend",
        "timestamp": day_ago + (8 * 60 * 60 * 1000),
        "pastedContents": "const UserProfile = ({ user }) => { return <div>{user.name} - {user.email}</div>; };"
    },
    {
        "display": "Help me set up error handling for this Express.js route",
        "project": "e-commerce-backend",
        "timestamp": day_ago + (10 * 60 * 60 * 1000),
        "pastedContents": "app.get('/api/orders/:id', (req, res) => { const order = getOrderById(req.params.id); res.json(order); });"
    },
    {
        "display": "How can I make this component responsive for mobile?",
        "project": "e-commerce-frontend",
        "timestamp": day_ago + (12 * 60 * 60 * 1000),
        "pastedContents": "<div className='product-grid'><ProductCard /><ProductCard /><ProductCard /></div>"
    }
]

# Write chat history to JSONL format
with open('.claude/history.jsonl', 'w') as f:
    for entry in chat_entries:
        f.write(json.dumps(entry) + '\n')

print("Generated mock chat history with TypeScript, React, Node.js, and database work patterns")