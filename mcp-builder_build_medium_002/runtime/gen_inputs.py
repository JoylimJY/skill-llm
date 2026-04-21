import json

# Fixed deterministic sample user data mimicking API response
sample_user_data = {
    "total": 3,
    "users": [
        {
            "id": "U001",
            "name": "Alice Smith",
            "email": "alice@example.com",
            "team": "Marketing",
            "active": True
        },
        {
            "id": "U002",
            "name": "Bob Johnson",
            "email": "bob.johnson@example.com",
            "team": "Engineering",
            "active": True
        },
        {
            "id": "U003",
            "name": "Carol Chen",
            "email": "carolc@example.com",
            "team": "Sales",
            "active": False
        }
    ]
}

# Write deterministic input JSON file simulating API data for tests
with open('test_api_users.json', 'w', encoding='utf-8') as f:
    json.dump(sample_user_data, f, indent=2)

# Also write input parameters for testing search queries
search_input = {
    "query": "alice",
    "limit": 2,
    "offset": 0,
    "response_format": "markdown"
}

with open('test_search_params.json', 'w', encoding='utf-8') as f:
    json.dump(search_input, f, indent=2)

# Variant input JSON for JSON output format
search_input_json = {
    "query": "bob",
    "limit": 1,
    "offset": 0,
    "response_format": "json"
}

with open('test_search_params_json.json', 'w', encoding='utf-8') as f:
    json.dump(search_input_json, f, indent=2)
