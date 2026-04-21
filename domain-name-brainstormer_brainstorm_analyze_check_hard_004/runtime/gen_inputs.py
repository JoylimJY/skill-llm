import json
import os

# Create a mock WHOIS database for consistent testing
whois_data = {
    'wastewise.com': 'available',
    'foodsmart.com': 'taken',
    'greenplate.com': 'taken', 
    'ecoeat.com': 'available',
    'smartkitchen.com': 'taken',
    'wastezero.com': 'available',
    'aiplate.com': 'available',
    'greentech.com': 'taken',
    'foodflow.com': 'available',
    'sustainaplate.com': 'available',
    'kitcheniq.com': 'available',
    'foodpredict.com': 'available',
    'wastewatch.com': 'available',
    'smartserve.com': 'taken',
    'ecoserve.com': 'available',
    'plateai.com': 'available',
    'greenbyte.com': 'available',
    'foodsync.com': 'available',
    'wasteless.io': 'available',
    'foodai.io': 'available', 
    'greentech.io': 'available',
    'smartplate.io': 'available',
    'ecoflow.io': 'available',
    'wasteiq.io': 'available',
    'kitchenai.dev': 'available',
    'foodtech.dev': 'available',
    'greencode.dev': 'available',
    'smartfood.dev': 'available',
    'wasteflow.dev': 'available',
    'platetech.ai': 'available',
    'foodbrain.ai': 'available',
    'wastesmart.ai': 'available',
    'kitchenmind.ai': 'available',
    'greenmind.ai': 'available',
    'foodwise.eco': 'available',
    'greenkitchen.eco': 'available',
    'sustainfood.eco': 'available',
    'ecoplate.eco': 'available',
    'zerowaste.eco': 'taken'
}

with open('mock_whois.json', 'w') as f:
    json.dump(whois_data, f, indent=2)

print('Mock WHOIS database created for testing')