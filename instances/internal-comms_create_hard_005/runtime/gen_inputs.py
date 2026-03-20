#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta

# Create mock company data files
company_updates = {
    "funding": {
        "amount": "$120M",
        "lead_investor": "Sequoia Capital",
        "date": "2024-09-15",
        "series": "C",
        "marker": "FUNDING_MARKER_2024"
    },
    "product_launch": {
        "product": "NeoCard Credit Card",
        "launch_date": "2024-10-01",
        "features": ["2% cashback", "no annual fee", "real-time spending alerts"],
        "marker": "PRODUCT_LAUNCH_MARKER"
    },
    "metrics": {
        "active_users": 500000,
        "growth_rate": "35%",
        "milestone_date": "2024-11-20",
        "marker": "METRICS_MILESTONE_MARKER"
    },
    "hiring": {
        "new_cto": "Sarah Chen",
        "previous_company": "Stripe",
        "start_date": "2024-10-15",
        "marker": "EXECUTIVE_HIRE_MARKER"
    },
    "challenges": {
        "eu_expansion_delay": {
            "reason": "regulatory approval delays",
            "new_timeline": "Q2 2025",
            "marker": "REGULATORY_CHALLENGE_MARKER"
        }
    },
    "policy_updates": {
        "hybrid_work": {
            "policy": "3 days in office, 2 days remote",
            "effective_date": "2024-12-01",
            "marker": "HYBRID_POLICY_MARKER"
        },
        "performance_reviews": {
            "cycle_start": "2025-01-15",
            "new_process": "360-degree feedback",
            "marker": "PERFORMANCE_REVIEW_MARKER"
        }
    }
}

# Write company updates file
with open('company_updates_q4_2024.json', 'w') as f:
    json.dump(company_updates, f, indent=2)

# Create mock Slack messages file
slack_messages = [
    {
        "channel": "#general",
        "author": "CEO Mike Rodriguez",
        "message": "Excited to announce our Series C! FUNDING_MARKER_2024 This will accelerate our growth.",
        "reactions": 127,
        "date": "2024-09-15"
    },
    {
        "channel": "#product-announcements",
        "author": "Product Team",
        "message": "NeoCard is live! PRODUCT_LAUNCH_MARKER Our new credit card with amazing benefits.",
        "reactions": 89,
        "date": "2024-10-01"
    },
    {
        "channel": "#ask-leadership",
        "author": "employee_sarah_k",
        "message": "Can someone clarify the new hybrid work policy? HYBRID_POLICY_MARKER I'm confused about the requirements.",
        "replies": 34,
        "date": "2024-11-18"
    },
    {
        "channel": "#ask-leadership", 
        "author": "employee_james_m",
        "message": "When do performance reviews start? PERFORMANCE_REVIEW_MARKER The timeline wasn't clear.",
        "replies": 28,
        "date": "2024-11-22"
    }
]

with open('slack_messages.json', 'w') as f:
    json.dump(slack_messages, f, indent=2)

# Create company info file
company_info = {
    "name": "NeoBank",
    "employee_count": 800,
    "industry": "fintech",
    "ceo": "Mike Rodriguez",
    "founded": "2019",
    "marker": "COMPANY_INFO_MARKER"
}

with open('company_info.json', 'w') as f:
    json.dump(company_info, f, indent=2)

print('Generated company data files with embedded markers for verification')