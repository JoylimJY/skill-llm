import json
import os
from datetime import datetime, timedelta

# Create mock chat history file
os.makedirs('.claude', exist_ok=True)

# Generate timestamps for last 48 hours
now = datetime.now()
history_entries = [
    {
        "display": "Help me debug this React component that's not rendering properly",
        "project": "ecommerce-frontend",
        "timestamp": int((now - timedelta(hours=2)).timestamp() * 1000),
        "pastedContents": "function ProductCard({ product }) { return <div>{product.name}</div>; }"
    },
    {
        "display": "I'm getting TypeScript errors with this API response type",
        "project": "ecommerce-frontend", 
        "timestamp": int((now - timedelta(hours=4)).timestamp() * 1000),
        "pastedContents": "interface ApiResponse { data: any; error?: string; }"
    },
    {
        "display": "How do I handle async/await in this database query?",
        "project": "backend-service",
        "timestamp": int((now - timedelta(hours=6)).timestamp() * 1000),
        "pastedContents": "async function getUser(id) { return db.users.findById(id); }"
    },
    {
        "display": "My authentication middleware keeps failing",
        "project": "backend-service",
        "timestamp": int((now - timedelta(hours=8)).timestamp() * 1000), 
        "pastedContents": "function authMiddleware(req, res, next) { if (!req.headers.authorization) { return res.status(401); } }"
    },
    {
        "display": "CSS grid layout is breaking on mobile devices",
        "project": "portfolio-site",
        "timestamp": int((now - timedelta(hours=12)).timestamp() * 1000),
        "pastedContents": ".grid { display: grid; grid-template-columns: repeat(3, 1fr); }"
    },
    {
        "display": "Need help optimizing this SQL query performance",
        "project": "analytics-dashboard",
        "timestamp": int((now - timedelta(hours=24)).timestamp() * 1000),
        "pastedContents": "SELECT * FROM users JOIN orders ON users.id = orders.user_id WHERE orders.created_at > '2024-01-01'"
    }
]

# Write chat history as JSONL
with open('.claude/history.jsonl', 'w') as f:
    for entry in history_entries:
        f.write(json.dumps(entry) + '\n')

print("Generated mock chat history with 6 entries spanning 24 hours")