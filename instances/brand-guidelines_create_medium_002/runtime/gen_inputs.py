import json
import os

# Create a requirements file for the presentation content
requirements = {
    "title": "Anthropic Q4 Product Roadmap",
    "slides": [
        {
            "title": "Q4 Product Roadmap",
            "subtitle": "Anthropic Innovation Pipeline",
            "type": "title"
        },
        {
            "title": "Market Overview",
            "content": "AI assistant market growing 45% YoY\nEnterprise adoption accelerating\nSafety-first approach differentiates",
            "type": "content"
        },
        {
            "title": "Key Features",
            "content": "Enhanced reasoning capabilities\nImproved safety mechanisms\nExpanded context windows\nBetter multilingual support",
            "type": "content"
        },
        {
            "title": "Technical Architecture",
            "content": "Constitutional AI framework\nScalable infrastructure\nRobust safety monitoring\nReal-time performance optimization",
            "type": "content"
        },
        {
            "title": "Next Steps",
            "content": "Beta testing begins December\nPartner feedback integration\nPublic release Q1 2024\nContinuous safety evaluation",
            "type": "content"
        }
    ],
    "brand_verification_marker": "ANTHROPIC_BRAND_APPLIED_XYZ789"
}

with open('presentation_requirements.json', 'w') as f:
    json.dump(requirements, f, indent=2)

print("Generated presentation requirements with brand verification marker")