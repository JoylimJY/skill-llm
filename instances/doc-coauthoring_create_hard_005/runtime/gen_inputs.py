#!/usr/bin/env python3
import os
import json

# Create RFC template file
rfc_template = '''# RFC Template

## Title
[RFC Title Here]

## Summary
[Brief summary of the proposal]

## Background
[Context and motivation for this change]

## Proposal
[Detailed description of the proposed solution]

## Technical Details
[Implementation specifics]

## Migration Plan
[Step-by-step migration approach]

## Risks and Mitigation
[Potential risks and how to address them]

## Alternatives Considered
[Other options that were evaluated]

## Impact Assessment
[Effects on teams, systems, and users]

## Timeline
[Project milestones and deadlines]

## Success Metrics
[How to measure success]
'''

with open('rfc_template.md', 'w') as f:
    f.write(rfc_template)

# Create current system architecture document
arch_doc = '''# Current Database Architecture

## Services Using MySQL
- user-service: handles authentication and user profiles
- order-service: processes e-commerce transactions
- inventory-service: manages product catalog and stock
- analytics-service: generates business reports
- notification-service: sends emails and push notifications

## Database Schemas
- users: 50M records, heavy read/write patterns
- orders: 200M records, append-heavy with complex joins
- products: 2M records, read-heavy with full-text search needs
- analytics: 500M records, batch processing workloads

## Current Pain Points
- MySQL full-text search limitations affecting product discovery
- JSON column performance issues in analytics workloads
- Licensing costs scaling with replica count
- Limited window functions impacting report generation
- Replication lag affecting read consistency

## Infrastructure
- Primary: MySQL 8.0 on AWS RDS r5.2xlarge
- Read replicas: 3x r5.xlarge instances
- Backup: Daily snapshots + binlog archival
- Monitoring: CloudWatch + DataDog integration
'''

with open('current_architecture.md', 'w') as f:
    f.write(arch_doc)

# Create team context file
team_context = '''# Team and Organizational Context

## Stakeholder Teams
- Platform Engineering: owns database infrastructure
- Backend Engineering: maintains the 5 affected services  
- Data Engineering: runs analytics pipelines
- DevOps: handles deployments and monitoring
- Product: concerned about search functionality improvements

## Recent Incidents
- Last month: 4-hour outage due to MySQL deadlock in order processing
- Q3: Performance degradation from analytics queries affecting OLTP workload
- Ongoing: Customer complaints about slow product search

## Business Context
- Black Friday approaching in 6 weeks (traffic spikes 10x)
- New product search features planned for Q1 next year
- Cost optimization initiative targeting 20% infrastructure savings
- Compliance audit requiring better audit logging capabilities

## Technical Constraints
- Zero-downtime migration required
- Must maintain backwards compatibility during transition
- Limited maintenance windows (Sunday 2-6 AM only)
- Team bandwidth: 2 senior engineers can work on this full-time
'''

with open('team_context.md', 'w') as f:
    f.write(team_context)

# Create evaluation markers file for verification
markers = {
    'expected_sections': [
        'title', 'summary', 'background', 'proposal', 'technical details',
        'migration plan', 'risks and mitigation', 'alternatives considered',
        'impact assessment', 'timeline', 'success metrics'
    ],
    'required_content': [
        'mysql', 'postgresql', 'migration', 'zero-downtime', 'black friday',
        'full-text search', 'json', 'licensing costs', 'replication lag',
        'deadlock', 'performance', '50m records', '200m records'
    ],
    'stakeholder_teams': ['platform engineering', 'backend engineering', 'data engineering', 'devops', 'product'],
    'services': ['user-service', 'order-service', 'inventory-service', 'analytics-service', 'notification-service']
}

with open('eval_markers.json', 'w') as f:
    json.dump(markers, f, indent=2)

print('Generated input files: rfc_template.md, current_architecture.md, team_context.md, eval_markers.json')