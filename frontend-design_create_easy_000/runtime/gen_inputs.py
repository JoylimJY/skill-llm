import os
import json

# Create a simple data file with portfolio information
portfolio_data = {
    "artist_name": "Maya Chen",
    "tagline": "Digital Artist & Creative Director",
    "bio": "Maya creates immersive digital experiences that blur the line between reality and imagination. Her work spans from interactive installations to brand identities.",
    "featured_works": [
        {"title": "Neon Dreams", "medium": "Digital Illustration", "year": "2024"},
        {"title": "Urban Synthesis", "medium": "3D Art", "year": "2023"},
        {"title": "Fluid Dynamics", "medium": "Motion Graphics", "year": "2024"}
    ],
    "contact": {
        "email": "maya@example.com",
        "instagram": "@mayachen_art",
        "behance": "mayachen"
    }
}

with open('portfolio_data.json', 'w') as f:
    json.dump(portfolio_data, f, indent=2)

print("Generated portfolio data file")