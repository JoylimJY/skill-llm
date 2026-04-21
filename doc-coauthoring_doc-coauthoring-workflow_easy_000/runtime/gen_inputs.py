#!/usr/bin/env python3
import os
import json

os.makedirs('context', exist_ok=True)

context_data = {
    'current_api': 'REST API built with Express.js',
    'team_size': '8 engineers',
    'client_types': ['web', 'mobile', 'third-party integrations'],
    'pain_points': ['over-fetching data', 'multiple round trips', 'versioning complexity'],
    'graphql_benefits': ['precise data fetching', 'single endpoint', 'strong typing'],
    'graphql_concerns': ['learning curve', 'caching complexity', 'monitoring overhead'],
    'timeline': '6 months for migration',
    'stakeholders': ['backend team', 'frontend team', 'devops', 'product']
}

with open('context/api_context.json', 'w') as f:
    json.dump(context_data, f, indent=2)

with open('context/notes.txt', 'w') as f:
    f.write('API Migration Context\n')
    f.write('====================\n\n')
    f.write('Current State:\n')
    f.write('- REST API with 50+ endpoints\n')
    f.write('- Clients often need data from multiple endpoints\n')
    f.write('- Mobile clients suffer from bandwidth constraints\n\n')
    f.write('Proposal:\n')
    f.write('- Migrate to GraphQL for better efficiency\n')
    f.write('- Maintain REST API during transition period\n')
    f.write('- Gradual client migration\n')

print('Context files created successfully')
