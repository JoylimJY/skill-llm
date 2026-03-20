#!/usr/bin/env python3
import os
import json
from datetime import datetime, timedelta
import random

# Set deterministic seed
random.seed(42)

# Create mock news articles about Tesla
news_articles = [
    {
        "title": "Tesla Reports Strong Q4 Earnings, Stock Surges 8%",
        "content": "Tesla Inc. exceeded analyst expectations with Q4 earnings of $2.05 per share. The electric vehicle manufacturer showed robust growth in Model Y deliveries and expanded its Supercharger network globally. CEO Elon Musk expressed optimism about 2024 production targets. MARKER_POSITIVE_NEWS_TESLA_Q4",
        "date": "2024-01-25",
        "source": "MarketWatch",
        "sentiment": "positive"
    },
    {
        "title": "Tesla Faces Production Challenges at Berlin Gigafactory",
        "content": "Tesla's European production facility in Berlin is experiencing supply chain disruptions affecting Model Y output. Industry analysts cite semiconductor shortages and logistics issues. The company maintains it will meet annual delivery guidance despite current headwinds. MARKER_NEGATIVE_NEWS_BERLIN_PRODUCTION",
        "date": "2024-01-20",
        "source": "Reuters",
        "sentiment": "negative"
    },
    {
        "title": "Tesla Stock Analysis: Wall Street Mixed on EV Giant's Future",
        "content": "Financial analysts remain divided on Tesla's valuation with price targets ranging from $180 to $350. While some praise the company's innovation in autonomous driving, others question sustainability of current margins. MARKER_NEUTRAL_NEWS_ANALYST_MIXED",
        "date": "2024-01-22",
        "source": "Bloomberg",
        "sentiment": "neutral"
    }
]

# Create mock financial data
financial_data = {
    "company": "Tesla Inc.",
    "symbol": "TSLA",
    "quarterly_results": {
        "Q4_2023": {
            "revenue": 25167000000,
            "net_income": 7928000000,
            "eps": 2.05,
            "vehicle_deliveries": 484507,
            "marker": "MARKER_Q4_FINANCIAL_DATA_TESLA"
        },
        "Q3_2023": {
            "revenue": 23350000000,
            "net_income": 1853000000,
            "eps": 0.58,
            "vehicle_deliveries": 435059,
            "marker": "MARKER_Q3_FINANCIAL_DATA_TESLA"
        }
    },
    "stock_data": {
        "current_price": 248.50,
        "52_week_high": 299.29,
        "52_week_low": 138.80,
        "market_cap": 788500000000,
        "marker": "MARKER_STOCK_DATA_CURRENT"
    },
    "key_metrics": {
        "pe_ratio": 45.2,
        "debt_to_equity": 0.17,
        "gross_margin": 0.203,
        "marker": "MARKER_KEY_METRICS_TESLA"
    }
}

# Generate historical stock prices (30 days)
stock_prices = []
base_price = 230.0
for i in range(30):
    date = (datetime.now() - timedelta(days=29-i)).strftime('%Y-%m-%d')
    # Add some realistic price movement
    change = random.uniform(-0.05, 0.05)
    base_price = max(base_price * (1 + change), 180.0)  # Floor at $180
    stock_prices.append({
        "date": date,
        "price": round(base_price, 2),
        "volume": random.randint(15000000, 45000000)
    })

stock_prices[-1]["marker"] = "MARKER_HISTORICAL_STOCK_PRICES"

# Write files
with open('tesla_news.json', 'w') as f:
    json.dump({"articles": news_articles, "marker": "MARKER_NEWS_FILE_TESLA"}, f, indent=2)

with open('tesla_financials.json', 'w') as f:
    json.dump(financial_data, f, indent=2)

with open('tesla_stock_history.json', 'w') as f:
    json.dump({"prices": stock_prices, "marker": "MARKER_STOCK_HISTORY_FILE"}, f, indent=2)

# Create a requirements file for the agent
requirements = {
    "task": "tesla_market_analysis",
    "required_outputs": [
        "investment_report.json",
        "market_analysis_report.pdf"
    ],
    "analysis_requirements": {
        "sentiment_analysis": "must analyze news sentiment and provide scores",
        "financial_analysis": "must calculate key financial ratios and trends",
        "visualizations": "must create at least 2 charts (price trends, sentiment)",
        "recommendation": "must provide buy/hold/sell recommendation with confidence score"
    },
    "marker": "MARKER_REQUIREMENTS_FILE"
}

with open('analysis_requirements.json', 'w') as f:
    json.dump(requirements, f, indent=2)

print("Generated input files:")
print("- tesla_news.json (3 news articles with sentiment markers)")
print("- tesla_financials.json (Q4 and Q3 2023 financial data)")
print("- tesla_stock_history.json (30 days of stock prices)")
print("- analysis_requirements.json (task specifications)")