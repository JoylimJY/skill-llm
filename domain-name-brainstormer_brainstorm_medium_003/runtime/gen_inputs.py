import json
import random
random.seed(42)

# Create mock domain availability data
available_domains = [
    'leadforge.com', 'growthcrm.io', 'bizpulse.app', 'salesbridge.dev',
    'clientflow.co', 'leadnest.com', 'bizconnect.io', 'growthlab.app',
    'salesvault.dev', 'crmsimple.co', 'leadhub.com', 'bizboost.io'
]

taken_domains = [
    'salesforce.com', 'hubspot.com', 'pipedrive.com', 'zoho.com',
    'leadgen.com', 'crm.com', 'sales.io', 'business.app'
]

# Mock API responses for domain checking
with open('mock_domain_data.json', 'w') as f:
    json.dump({
        'available': available_domains,
        'taken': taken_domains,
        'premium': ['leads.com', 'crm.io', 'sales.com']
    }, f, indent=2)

print('Mock domain data generated successfully')