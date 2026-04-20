import json
import random

random.seed(42)

market_data = {
    "report_date": "2024-Q4",
    "sectors": [
        {
            "name": "Cloud Computing",
            "growth_rate": 34.7,
            "market_size_bn": 623.3,
            "key_players": ["AWS", "Azure", "GCP"],
            "sentiment": "bullish",
            "marker": "CLOUD_SECTOR_ALPHA_42"
        },
        {
            "name": "AI/ML Infrastructure",
            "growth_rate": 52.1,
            "market_size_bn": 184.2,
            "key_players": ["NVIDIA", "AMD", "Intel"],
            "sentiment": "very_bullish",
            "marker": "AIML_SECTOR_BETA_99"
        },
        {
            "name": "Cybersecurity",
            "growth_rate": 18.3,
            "market_size_bn": 211.0,
            "key_players": ["CrowdStrike", "Palo Alto", "Fortinet"],
            "sentiment": "bullish",
            "marker": "CYBER_SECTOR_GAMMA_77"
        },
        {
            "name": "Legacy Hardware",
            "growth_rate": -3.2,
            "market_size_bn": 89.5,
            "key_players": ["IBM", "HP"],
            "sentiment": "bearish",
            "marker": "LEGACY_SECTOR_DELTA_11"
        },
        {
            "name": "Edge Computing",
            "growth_rate": 28.9,
            "market_size_bn": 97.4,
            "key_players": ["Cloudflare", "Fastly", "Akamai"],
            "sentiment": "bullish",
            "marker": "EDGE_SECTOR_EPSILON_55"
        }
    ],
    "overall_market_growth": 26.4,
    "total_market_size_bn": 1205.4,
    "analysis_id": "MKT-2024-Q4-REPORT"
}

with open('raw_market_data.json', 'w') as f:
    json.dump(market_data, f, indent=2)

print('Generated raw_market_data.json')
