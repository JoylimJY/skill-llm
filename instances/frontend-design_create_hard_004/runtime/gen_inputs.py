import json
import random
from datetime import datetime, timedelta

random.seed(42)

# Generate mock portfolio data
coins = [
    {'symbol': 'BTC', 'name': 'Bitcoin', 'holdings': 2.5},
    {'symbol': 'ETH', 'name': 'Ethereum', 'holdings': 15.2},
    {'symbol': 'SOL', 'name': 'Solana', 'holdings': 100.8},
    {'symbol': 'ADA', 'name': 'Cardano', 'holdings': 5000.0},
    {'symbol': 'DOT', 'name': 'Polkadot', 'holdings': 250.5}
]

# Generate price history for each coin
base_prices = {'BTC': 45000, 'ETH': 2800, 'SOL': 95, 'ADA': 0.45, 'DOT': 7.2}
historical_data = {}

for coin in coins:
    symbol = coin['symbol']
    base_price = base_prices[symbol]
    history = []
    current_price = base_price
    
    # Generate 30 days of price history
    for i in range(30):
        date = (datetime.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
        # Add some realistic price volatility
        change = random.uniform(-0.08, 0.08)
        current_price = current_price * (1 + change)
        history.append({
            'date': date,
            'price': round(current_price, 4),
            'volume': random.randint(1000000, 50000000)
        })
    
    historical_data[symbol] = history

# Create requirements file
requirements = {
    'portfolio': coins,
    'historical_data': historical_data,
    'total_portfolio_value_usd': 250000,
    'required_features': [
        'Portfolio overview with total value',
        'Individual coin cards with current prices',
        'Price charts for each cryptocurrency', 
        'Performance metrics (24h change, 7d change)',
        'Holdings display with USD values',
        'Responsive design for desktop and mobile',
        'Real-time price updates simulation'
    ],
    'design_requirements': {
        'aesthetic': 'Premium fintech - sophisticated, data-dense, elegant',
        'target_audience': 'Professional traders and hedge fund managers',
        'mood': 'Serious money, high-end, trustworthy',
        'must_avoid': 'Generic crypto app aesthetics, amateur styling'
    },
    'technical_requirements': {
        'framework': 'React with TypeScript preferred',
        'responsiveness': 'Mobile and desktop optimized',
        'interactivity': 'Hover states, smooth transitions',
        'data_visualization': 'Price charts with historical data'
    },
    'marker_content': 'CRYPTO_DASHBOARD_FINTECH_2024'
}

with open('dashboard_requirements.json', 'w') as f:
    json.dump(requirements, f, indent=2)

print('Generated dashboard requirements and mock data files')