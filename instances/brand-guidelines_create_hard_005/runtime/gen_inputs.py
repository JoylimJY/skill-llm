#!/usr/bin/env python3
import os
import json
from datetime import datetime

# Create requirements file for the presentation
requirements = {
    'title': 'Q4 2024 Board Presentation - Anthropic Vision',
    'slides': [
        {
            'title': 'Company Overview',
            'content': [
                'Leading AI safety research company',
                'Founded with mission to develop safe, beneficial AI',
                'VERIFICATION_MARKER_OVERVIEW: Core focus on Constitutional AI'
            ]
        },
        {
            'title': 'Market Position',
            'content': [
                'Competitive landscape analysis',
                'VERIFICATION_MARKER_MARKET: Strategic positioning in enterprise AI',
                'Key differentiators in safety-first approach'
            ]
        },
        {
            'title': 'Financial Highlights',
            'content': [
                'Revenue growth trajectory',
                'Investment in R&D capabilities',
                'VERIFICATION_MARKER_FINANCE: Sustainable growth model established'
            ]
        },
        {
            'title': 'Product Roadmap',
            'content': [
                'Claude model improvements',
                'VERIFICATION_MARKER_PRODUCT: Next-generation capabilities timeline',
                'Enterprise integration features'
            ]
        },
        {
            'title': 'Team Updates',
            'content': [
                'Key hiring achievements',
                'VERIFICATION_MARKER_TEAM: Research talent acquisition success',
                'Organizational scaling initiatives'
            ]
        },
        {
            'title': 'Strategic Partnerships',
            'content': [
                'Industry collaboration framework',
                'VERIFICATION_MARKER_PARTNERSHIPS: Enterprise deployment alliances',
                'Academic research partnerships'
            ]
        },
        {
            'title': 'Current Challenges',
            'content': [
                'Regulatory landscape navigation',
                'VERIFICATION_MARKER_CHALLENGES: Scaling infrastructure requirements',
                'Competitive market dynamics'
            ]
        },
        {
            'title': 'Future Outlook',
            'content': [
                'Vision for responsible AI development',
                'VERIFICATION_MARKER_FUTURE: Long-term impact objectives',
                'Commitment to safety leadership'
            ]
        }
    ],
    'brand_requirements': {
        'colors': {
            'dark': '#141413',
            'light': '#faf9f5',
            'mid_gray': '#b0aea5',
            'light_gray': '#e8e6dc',
            'orange': '#d97757',
            'blue': '#6a9bcc',
            'green': '#788c5d'
        },
        'fonts': {
            'headings': 'Poppins',
            'body': 'Lora'
        }
    },
    'verification_markers': [
        'VERIFICATION_MARKER_OVERVIEW',
        'VERIFICATION_MARKER_MARKET',
        'VERIFICATION_MARKER_FINANCE',
        'VERIFICATION_MARKER_PRODUCT',
        'VERIFICATION_MARKER_TEAM',
        'VERIFICATION_MARKER_PARTNERSHIPS',
        'VERIFICATION_MARKER_CHALLENGES',
        'VERIFICATION_MARKER_FUTURE'
    ]
}

with open('presentation_requirements.json', 'w') as f:
    json.dump(requirements, f, indent=2)

print('Generated presentation requirements with embedded verification markers')