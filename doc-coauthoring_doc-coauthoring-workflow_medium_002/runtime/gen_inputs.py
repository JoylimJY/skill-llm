#!/usr/bin/env python3
import os
import json

os.makedirs('inputs', exist_ok=True)

# Create a sample context dump file that simulates user input
context_data = {
    "doc_type": "decision_doc",
    "audience": "engineering team and tech leads",
    "desired_impact": "align team on migration strategy and get buy-in for next steps",
    "background": "Our monolithic API has grown to 50k LOC. Deployment times are 45min, and team velocity is slowing. We've had 3 incidents in the past 6 months related to tight coupling.",
    "alternatives_considered": "1) Keep monolith and refactor internally, 2) Migrate to microservices, 3) Hybrid approach",
    "constraints": "6 month timeline, limited DevOps resources, must maintain backward compatibility",
    "stakeholders": "CTO wants cost efficiency, product team wants faster releases, ops team concerned about complexity"
}

with open('inputs/context.json', 'w') as f:
    json.dump(context_data, f, indent=2)

# Create a template file for decision docs
template = """# Decision Document: [Title]

## Problem Statement
[Describe the problem being solved]

## Options Considered
[List and compare options]

## Recommendation
[State the recommended path]

## Rationale
[Explain why this option was chosen]

## Implementation Plan
[Outline next steps]

## Risks and Mitigations
[Identify risks and how to address them]
"""

with open('inputs/decision_doc_template.md', 'w') as f:
    f.write(template)

print("Generated input files: context.json, decision_doc_template.md")
