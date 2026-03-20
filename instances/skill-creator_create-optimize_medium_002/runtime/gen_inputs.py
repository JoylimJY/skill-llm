#!/usr/bin/env python3
import json
import os
from pathlib import Path

# Create test schemas for different types of forms
schemas = {
    'employee_onboarding.json': {
        "title": "Employee Onboarding Form",
        "description": "New employee information collection",
        "fields": [
            {
                "name": "full_name",
                "type": "text",
                "label": "Full Name",
                "required": True,
                "max_length": 100
            },
            {
                "name": "email",
                "type": "email",
                "label": "Email Address",
                "required": True,
                "validation": "email"
            },
            {
                "name": "department",
                "type": "dropdown",
                "label": "Department",
                "required": True,
                "options": ["Engineering", "Marketing", "Sales", "HR", "Finance"]
            },
            {
                "name": "start_date",
                "type": "date",
                "label": "Start Date",
                "required": True
            },
            {
                "name": "remote_work",
                "type": "checkbox",
                "label": "Remote Work Eligible",
                "required": False
            }
        ],
        "layout": {
            "orientation": "portrait",
            "margin": 50,
            "font_size": 12
        }
    },
    'customer_feedback.json': {
        "title": "Customer Satisfaction Survey",
        "description": "Help us improve our services",
        "fields": [
            {
                "name": "customer_id",
                "type": "text",
                "label": "Customer ID",
                "required": True,
                "max_length": 20
            },
            {
                "name": "rating",
                "type": "dropdown",
                "label": "Overall Rating",
                "required": True,
                "options": ["Excellent", "Good", "Average", "Poor", "Very Poor"]
            },
            {
                "name": "recommend",
                "type": "checkbox",
                "label": "Would recommend to others",
                "required": False
            },
            {
                "name": "comments",
                "type": "textarea",
                "label": "Additional Comments",
                "required": False,
                "max_length": 500
            },
            {
                "name": "follow_up",
                "type": "checkbox",
                "label": "Contact me for follow-up",
                "required": False
            }
        ],
        "layout": {
            "orientation": "portrait",
            "margin": 40,
            "font_size": 11
        }
    },
    'event_registration.json': {
        "title": "Conference Registration Form",
        "description": "Register for TechCon 2024",
        "fields": [
            {
                "name": "attendee_name",
                "type": "text",
                "label": "Attendee Name",
                "required": True,
                "max_length": 80
            },
            {
                "name": "company",
                "type": "text",
                "label": "Company/Organization",
                "required": False,
                "max_length": 100
            },
            {
                "name": "ticket_type",
                "type": "dropdown",
                "label": "Ticket Type",
                "required": True,
                "options": ["Early Bird", "Regular", "Student", "VIP"]
            },
            {
                "name": "dietary_restrictions",
                "type": "textarea",
                "label": "Dietary Restrictions",
                "required": False,
                "max_length": 200
            },
            {
                "name": "networking_dinner",
                "type": "checkbox",
                "label": "Attend networking dinner",
                "required": False
            },
            {
                "name": "workshop_sessions",
                "type": "checkbox",
                "label": "Interested in workshop sessions",
                "required": False
            }
        ],
        "layout": {
            "orientation": "portrait",
            "margin": 45,
            "font_size": 10
        }
    }
}

# Write schema files
for filename, schema in schemas.items():
    with open(filename, 'w') as f:
        json.dump(schema, f, indent=2)
    print(f'Generated {filename}')

# Create a requirements file for the skill
with open('skill_requirements.txt', 'w') as f:
    f.write('reportlab>=4.0.0\n')
    f.write('PyPDF2>=3.0.0\n')
    f.write('jsonschema>=4.0.0\n')
    f.write('pydantic>=2.0.0\n')

print('All test files generated successfully')