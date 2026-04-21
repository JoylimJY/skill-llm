#!/usr/bin/env python3
import os
import json

os.makedirs('context', exist_ok=True)

# Create mock team context files
context_data = {
    'current_state': 'Monolithic API handles 500+ endpoints, 50+ services internally coupled',
    'pain_points': [
        'Deployment takes 2 hours, blocks all teams',
        'One service bug can crash entire system',
        'Scaling one component requires scaling entire monolith',
        'Team velocity reduced due to merge conflicts'
    ],
    'alternatives_considered': [
        'Strangler pattern (rejected: too slow)',
        'Modular monolith (rejected: doesn\'t solve deployment issue)',
        'Full rewrite (rejected: too risky)'
    ],
    'proposed_approach': 'Strangler fig pattern with event-driven architecture',
    'timeline': '12 months in 3 phases',
    'risks': [
        'Increased operational complexity',
        'Network latency between services',
        'Data consistency challenges'
    ]
}

with open('context/migration_context.json', 'w') as f:
    json.dump(context_data, f, indent=2)

# Create a template file
template = """# Technical Decision Document: [TITLE]

## Problem Statement
[To be written]

## Proposed Solution
[To be written]

## Alternatives Considered
[To be written]

## Implementation Plan
[To be written]

## Risks and Mitigations
[To be written]

## Success Criteria
[To be written]
"""

with open('context/tdd_template.md', 'w') as f:
    f.write(template)

print('Context files created successfully')
