#!/usr/bin/env python3
import json

# Create a simple data file with Q1 results
q1_data = {
    "title": "Q1 2024 Results Overview",
    "slides": [
        {
            "title": "Revenue Growth",
            "content": "Q1 revenue increased by 25% compared to Q4 2023"
        },
        {
            "title": "Key Metrics",
            "content": "Customer satisfaction: 94%\nNew customers: 1,200\nProduct launches: 3"
        },
        {
            "title": "Next Steps",
            "content": "Focus on Q2 expansion and product development initiatives"
        }
    ]
}

with open('q1_data.json', 'w') as f:
    json.dump(q1_data, f, indent=2)

print("Generated input files: q1_data.json")