import os
import json

# Create a mock research context file to simulate background information
context_data = {
    "topic": "remote work productivity",
    "target_audience": "remote workers and managers",
    "article_type": "blog post",
    "tone": "practical and engaging",
    "length": "medium-form (1000-1500 words)"
}

with open('context.json', 'w') as f:
    json.dump(context_data, f, indent=2)

print("Context file created for content research writing task")