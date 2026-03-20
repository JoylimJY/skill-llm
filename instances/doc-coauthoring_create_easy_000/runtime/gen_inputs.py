#!/usr/bin/env python3

import os
import json

# Create team context file
team_context = {
    "team": "Backend Platform Team",
    "current_api": "REST API with 15 endpoints",
    "pain_points": [
        "Over-fetching data in mobile apps",
        "Multiple API calls needed for dashboard views",
        "Frontend teams complaining about rigid data structure"
    ],
    "stakeholders": ["Frontend teams", "Mobile team", "DevOps", "Product managers"],
    "timeline": "Need decision by Q2 planning",
    "constraints": "Must maintain backwards compatibility for 6 months"
}

with open('team_context.json', 'w') as f:
    json.dump(team_context, f, indent=2)

# Create decision doc template
template_content = '''# Decision Document Template

## Summary
[Brief summary of the decision]

## Context
[Background and problem statement]

## Decision
[The decision being made]

## Rationale
[Why this decision was made]

## Alternatives Considered
[Other options that were evaluated]

## Implementation Plan
[How this will be executed]

## Risks and Mitigations
[Potential risks and how to address them]

## Success Metrics
[How success will be measured]
'''

with open('decision_doc_template.md', 'w') as f:
    f.write(template_content)

# Create marker file to verify workflow was followed
markers = {
    "workflow_marker": "DOC_COAUTH_WORKFLOW_2024",
    "expected_sections": ["Summary", "Context", "Decision", "Rationale", "Alternatives Considered", "Implementation Plan", "Risks and Mitigations", "Success Metrics"],
    "topic_keywords": ["GraphQL", "REST", "API", "Backend Platform Team"]
}

with open('expected_markers.json', 'w') as f:
    json.dump(markers, f, indent=2)

print("Generated input files for decision document workflow")