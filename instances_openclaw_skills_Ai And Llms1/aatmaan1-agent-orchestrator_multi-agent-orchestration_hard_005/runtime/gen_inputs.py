import json
import os
import random

random.seed(42)

os.makedirs('input_data', exist_ok=True)

market_data = {
    'report_id': 'MKT-2024-Q1',
    'sector': 'Electric Vehicles',
    'marker': 'BENCHMARK_MARKER_EV_2024',
    'companies': [
        {'name': 'AlphaMotors', 'market_share': 34.2, 'revenue_bn': 82.5, 'yoy_growth': 18.3},
        {'name': 'BetaDrive', 'market_share': 21.7, 'revenue_bn': 52.1, 'yoy_growth': 31.2},
        {'name': 'GammaCars', 'market_share': 15.4, 'revenue_bn': 37.0, 'yoy_growth': 9.8},
        {'name': 'DeltaAuto', 'market_share': 11.1, 'revenue_bn': 26.6, 'yoy_growth': 44.5},
        {'name': 'EpsilonEV', 'market_share': 8.9, 'revenue_bn': 21.3, 'yoy_growth': 67.1}
    ],
    'total_market_size_bn': 239.8,
    'forecast_2025_bn': 312.4,
    'key_trends': [
        'Battery cost reduction accelerating',
        'Government subsidies expanding in EU and Asia',
        'Charging infrastructure growing 42% YoY',
        'Consumer adoption crossing mainstream threshold'
    ],
    'risks': [
        'Supply chain constraints for lithium',
        'Regulatory uncertainty in North America',
        'Incumbent automaker competition intensifying'
    ]
}

with open('input_data/raw_market_data.json', 'w') as f:
    json.dump(market_data, f, indent=2)

print('Generated input_data/raw_market_data.json')
