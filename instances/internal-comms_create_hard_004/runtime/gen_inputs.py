#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta

# Create mock company context files
context_data = {
    'company_info': {
        'name': 'TechFlow',
        'size': 150,
        'funding_round': 'Series B',
        'funding_amount': '$25M',
        'lead_investor': 'Accel'
    },
    'recent_announcements': [
        {
            'type': 'funding',
            'details': 'Closed Series B funding of $25M led by Accel',
            'author': 'Sarah (CEO)',
            'reactions': 47,
            'marker': 'FUNDING_MARKER_2024'
        },
        {
            'type': 'product',
            'details': 'New onboarding flow shipped with 15% better conversion',
            'team': 'Marketing',
            'metric': '15% improvement',
            'marker': 'ONBOARDING_MARKER_2024'
        },
        {
            'type': 'engineering',
            'details': 'API rewrite project 80% complete',
            'team': 'Engineering',
            'progress': '80%',
            'marker': 'API_REWRITE_MARKER_2024'
        },
        {
            'type': 'sales',
            'details': '3 enterprise deals signed including Salesforce',
            'team': 'Sales',
            'author': 'Mike',
            'key_client': 'Salesforce',
            'marker': 'SALES_DEALS_MARKER_2024'
        },
        {
            'type': 'hiring',
            'details': '12 new hires this week including VP of Product',
            'count': 12,
            'key_hire': 'VP of Product',
            'marker': 'HIRING_MARKER_2024'
        },
        {
            'type': 'press',
            'details': 'TechCrunch coverage of Series B funding',
            'publication': 'TechCrunch',
            'topic': 'Series B funding',
            'marker': 'TECHCRUNCH_MARKER_2024'
        }
    ]
}

# Write context file
with open('company_context.json', 'w') as f:
    json.dump(context_data, f, indent=2)

# Create a sample Slack messages file
slack_messages = [
    {
        'channel': '#general',
        'author': 'Sarah',
        'message': 'Excited to announce we\'ve closed our Series B! 🎉 FUNDING_MARKER_2024',
        'reactions': 47,
        'replies': 23
    },
    {
        'channel': '#product',
        'author': 'Marketing Team',
        'message': 'New onboarding is live and crushing it! ONBOARDING_MARKER_2024',
        'reactions': 15
    }
]

with open('slack_activity.json', 'w') as f:
    json.dump(slack_messages, f, indent=2)

print('Generated company context files with verification markers')