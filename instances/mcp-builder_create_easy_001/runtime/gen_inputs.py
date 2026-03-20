#!/usr/bin/env python3

import os
import json

# Create a sample API response file for testing
api_responses = {
    "current_weather_london": {
        "city": "London",
        "temperature": 15,
        "condition": "Cloudy",
        "humidity": 68,
        "wind_speed": 12,
        "timestamp": "2024-01-15T10:30:00Z"
    },
    "current_weather_paris": {
        "city": "Paris", 
        "temperature": 18,
        "condition": "Sunny",
        "humidity": 45,
        "wind_speed": 8,
        "timestamp": "2024-01-15T10:30:00Z"
    },
    "cities_list": [
        {"id": "london", "name": "London", "country": "UK"},
        {"id": "paris", "name": "Paris", "country": "France"},
        {"id": "tokyo", "name": "Tokyo", "country": "Japan"},
        {"id": "newyork", "name": "New York", "country": "USA"}
    ]
}

# Write test data
with open('test_api_data.json', 'w') as f:
    json.dump(api_responses, f, indent=2)

# Create a requirements file marker
with open('weather_requirements.txt', 'w') as f:
    f.write("# MARKER_WEATHER_REQ_12345\n")
    f.write("mcp>=1.1.0\n")
    f.write("pydantic>=2.10.0\n")
    f.write("httpx>=0.28.0\n")

print("Generated test input files successfully")