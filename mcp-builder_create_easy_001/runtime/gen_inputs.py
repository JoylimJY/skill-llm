import json

users = [
    {"id": "U1001", "name": "Alice Smith", "email": "alice@example.com"},
    {"id": "U1002", "name": "Bob Johnson", "email": "bob@example.com"},
    {"id": "U1003", "name": "Carol Williams", "email": "carol@example.com"},
    {"id": "U1004", "name": "David Brown", "email": "david@example.com"},
    {"id": "U1005", "name": "Eve Davis", "email": "eve@example.com"},
    {"id": "U1006", "name": "Frank Miller", "email": "frank@example.com"},
    {"id": "U1007", "name": "Grace Wilson", "email": "grace@example.com"},
    {"id": "U1008", "name": "Heidi Moore", "email": "heidi@example.com"},
    {"id": "U1009", "name": "Ivan Taylor", "email": "ivan@example.com"},
    {"id": "U1010", "name": "Judy Anderson", "email": "judy@example.com"}
]

with open('users.json', 'w') as f:
    json.dump({"total": len(users), "users": users}, f, indent=2)
