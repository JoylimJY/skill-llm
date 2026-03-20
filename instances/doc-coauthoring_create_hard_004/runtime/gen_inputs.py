#!/usr/bin/env python3
import os
import json

# Create context files that simulate a real migration scenario
with open('incident_log.md', 'w') as f:
    f.write('''# Recent Production Incidents

## 2024-01-15: Database Connection Pool Exhaustion
- Order processing queue backed up for 3 hours
- Root cause: Monolithic app consuming all DB connections during peak traffic
- Impact: $45K revenue loss, customer complaints
- MARKER_INCIDENT_DB_CONNECTIONS

## 2024-01-08: Deployment Rollback
- Payment service bug required full application rollback
- Rollback affected inventory and user management (unrelated services)
- Downtime: 47 minutes
- MARKER_INCIDENT_DEPLOYMENT_COUPLING

## 2023-12-22: Black Friday Performance Issues
- Response times exceeded 10s during peak traffic
- Unable to scale individual components
- Lost approximately 15% of potential sales
- MARKER_INCIDENT_SCALABILITY_WALL
''')

with open('team_capacity.json', 'w') as f:
    json.dump({
        'teams': {
            'backend': {'size': 8, 'experience_microservices': 3, 'availability_q1q2': 0.7},
            'platform': {'size': 4, 'experience_microservices': 4, 'availability_q1q2': 0.9},
            'frontend': {'size': 6, 'experience_microservices': 1, 'availability_q1q2': 0.8}
        },
        'current_velocity': '23 story_points_per_sprint',
        'migration_estimate': '6_month_minimum',
        'marker_content': 'MARKER_TEAM_CAPACITY_DATA'
    }, f, indent=2)

with open('architecture_constraints.txt', 'w') as f:
    f.write('''ARCHITECTURE CONSTRAINTS AND DEPENDENCIES

1. Current Tech Stack:
   - Monolithic Rails application (350K+ LOC)
   - PostgreSQL primary database (2TB+)
   - Redis for session management
   - Elasticsearch for product search
   - MARKER_CURRENT_STACK_COMPLEXITY

2. Compliance Requirements:
   - PCI DSS Level 1 compliance mandatory
   - SOX reporting requirements
   - GDPR data residency constraints
   - MARKER_COMPLIANCE_CONSTRAINTS

3. Infrastructure Limitations:
   - Legacy data center contracts until Q3 2024
   - Network latency requirements <100ms
   - Existing monitoring tooling (DataDog, PagerDuty)
   - MARKER_INFRASTRUCTURE_CONSTRAINTS

4. Business Constraints:
   - No downtime during holiday seasons (Nov-Jan)
   - Must maintain backward compatibility for mobile apps
   - Budget cap: $500K for Q1-Q2
   - MARKER_BUSINESS_CONSTRAINTS
''')

with open('proposed_services.yaml', 'w') as f:
    f.write('''# Proposed Service Boundaries
services:
  user_service:
    responsibilities: [authentication, profile_management, preferences]
    data: [users, profiles, auth_tokens]
    complexity: medium
    
  order_service:
    responsibilities: [order_processing, order_history, fulfillment]
    data: [orders, order_items, shipping_info]
    complexity: high
    
  payment_service:
    responsibilities: [payment_processing, refunds, billing]
    data: [payment_methods, transactions, invoices]
    complexity: high
    compliance: [PCI_DSS]
    
  inventory_service:
    responsibilities: [stock_management, product_catalog, pricing]
    data: [products, inventory_levels, pricing_rules]
    complexity: medium
    
  notification_service:
    responsibilities: [email, sms, push_notifications]
    data: [notification_templates, delivery_logs]
    complexity: low

# MARKER_SERVICE_BOUNDARIES_PROPOSED
migration_phases:
  phase1: [notification_service, user_service]
  phase2: [inventory_service]
  phase3: [payment_service, order_service]
''')

print('Generated input files with embedded markers for evaluation')