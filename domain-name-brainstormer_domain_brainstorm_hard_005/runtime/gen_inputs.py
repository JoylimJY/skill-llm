import json
import random

# Set deterministic seed
random.seed(42)

# Create mock domain availability data for realistic testing
available_domains = [
    'cryptoyield.com', 'defitrack.io', 'yieldbot.ai', 'portfolioai.com',
    'cryptoflow.io', 'yieldsmart.ai', 'defiwise.com', 'trackchain.io',
    'cryptonest.com', 'yieldmax.io', 'defipilot.ai', 'chaintrack.com',
    'smartyield.io', 'cryptopulse.ai', 'portfoliopro.com', 'yieldgenie.io',
    'defidash.com', 'cryptobeam.ai', 'yieldhub.io', 'trackdefi.com'
]

taken_domains = [
    'crypto.com', 'defi.io', 'yield.ai', 'portfolio.com', 'trading.io',
    'bitcoin.com', 'ethereum.io', 'blockchain.ai', 'finance.com'
]

# Create availability mock data
availability_data = {
    'available': available_domains,
    'taken': taken_domains,
    'pricing': {
        '.com': 12.99,
        '.io': 39.99, 
        '.ai': 89.99,
        '.finance': 49.99,
        '.crypto': 69.99
    }
}

with open('mock_availability.json', 'w') as f:
    json.dump(availability_data, f, indent=2)

print('Mock domain availability data created successfully')