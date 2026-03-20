#!/usr/bin/env python3
import json
import random
random.seed(42)

# Generate mock cryptocurrency data
crypto_data = {
    'portfolio': {
        'total_value': 125430.50,
        'daily_change': 2340.75,
        'daily_change_percent': 1.9,
        'assets': [
            {'symbol': 'BTC', 'name': 'Bitcoin', 'amount': 2.5, 'price': 43200.00, 'value': 108000.00, 'change_24h': 3.2},
            {'symbol': 'ETH', 'name': 'Ethereum', 'amount': 15.0, 'price': 2450.50, 'value': 36757.50, 'change_24h': -1.8},
            {'symbol': 'SOL', 'name': 'Solana', 'amount': 100.0, 'price': 98.50, 'value': 9850.00, 'change_24h': 5.7},
            {'symbol': 'ADA', 'name': 'Cardano', 'amount': 2000.0, 'price': 0.48, 'value': 960.00, 'change_24h': -2.1}
        ]
    },
    'price_history': {
        'BTC': [42100, 42800, 41900, 43200, 43100, 43200],
        'ETH': [2520, 2480, 2460, 2450, 2445, 2450],
        'SOL': [95, 96, 97, 98, 99, 98],
        'ADA': [0.49, 0.48, 0.47, 0.48, 0.485, 0.48]
    },
    'transactions': [
        {'type': 'buy', 'asset': 'BTC', 'amount': 0.5, 'price': 42000, 'date': '2024-01-15', 'id': 'tx_marker_001'},
        {'type': 'sell', 'asset': 'ETH', 'amount': 2.0, 'price': 2500, 'date': '2024-01-14', 'id': 'tx_marker_002'},
        {'type': 'buy', 'asset': 'SOL', 'amount': 50.0, 'price': 95, 'date': '2024-01-13', 'id': 'tx_marker_003'}
    ]
}

with open('crypto_data.json', 'w') as f:
    json.dump(crypto_data, f, indent=2)

# Create requirements file
requirements = '''{
  "title": "Crypto Portfolio Dashboard",
  "description": "A premium cryptocurrency portfolio tracker with distinctive visual design",
  "required_sections": [
    "Portfolio overview with total value and daily change",
    "Asset allocation visualization (pie/donut chart)",
    "Price trend charts for individual assets",
    "Transaction history table",
    "Interactive hover states and animations"
  ],
  "design_requirements": [
    "Distinctive aesthetic that avoids generic crypto app designs",
    "Premium, trustworthy visual appearance",
    "Smooth animations and transitions",
    "Responsive layout",
    "Creative use of typography and color"
  ],
  "technical_requirements": [
    "React-based implementation preferred",
    "Use provided mock data from crypto_data.json",
    "Include CSS animations and micro-interactions",
    "Functional chart visualizations"
  ],
  "verification_markers": [
    "CRYPTO_DASHBOARD_MARKER_001",
    "PORTFOLIO_SECTION_MARKER",
    "CHART_VISUALIZATION_MARKER",
    "TRANSACTION_MARKER_tx_marker_001"
  ]
}'''

with open('requirements.json', 'w') as f:
    f.write(requirements)

print('Generated crypto_data.json and requirements.json')