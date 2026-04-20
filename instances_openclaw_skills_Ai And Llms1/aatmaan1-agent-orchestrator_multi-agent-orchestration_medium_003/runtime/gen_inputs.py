import json
import random

random.seed(42)

market_data = {
    "market": "cloud_infrastructure",
    "year": 2024,
    "competitors": [
        {
            "name": "AlphaCorp",
            "market_share": 34.2,
            "revenue_growth": 18.5,
            "key_products": ["AlphaCloud", "AlphaDB", "AlphaAI"],
            "strengths": ["enterprise_sales", "global_reach", "brand_recognition"],
            "weaknesses": ["high_pricing", "complex_onboarding"]
        },
        {
            "name": "BetaTech",
            "market_share": 28.7,
            "revenue_growth": 24.1,
            "key_products": ["BetaServe", "BetaML", "BetaEdge"],
            "strengths": ["developer_experience", "competitive_pricing", "fast_innovation"],
            "weaknesses": ["limited_enterprise_support", "regional_gaps"]
        },
        {
            "name": "GammaSystems",
            "market_share": 19.3,
            "revenue_growth": 31.8,
            "key_products": ["GammaOps", "GammaData", "GammaSec"],
            "strengths": ["security_focus", "compliance_certifications", "vertical_specialization"],
            "weaknesses": ["smaller_ecosystem", "limited_ai_offerings"]
        },
        {
            "name": "DeltaCloud",
            "market_share": 11.4,
            "revenue_growth": 42.3,
            "key_products": ["DeltaFlex", "DeltaStream"],
            "strengths": ["fastest_growth", "niche_focus", "cost_efficiency"],
            "weaknesses": ["limited_product_range", "brand_awareness"]
        }
    ],
    "trends": [
        {"id": "T001", "name": "AI_Integration", "growth_rate": 67.4, "adoption_score": 8.9, "description": "Rapid integration of AI and ML capabilities into core cloud services"},
        {"id": "T002", "name": "Edge_Computing", "growth_rate": 43.2, "adoption_score": 7.2, "description": "Shift toward edge computing for latency-sensitive workloads"},
        {"id": "T003", "name": "Security_Compliance", "growth_rate": 38.9, "adoption_score": 9.1, "description": "Increased focus on security and regulatory compliance across all verticals"},
        {"id": "T004", "name": "Cost_Optimization", "growth_rate": 29.5, "adoption_score": 8.3, "description": "Growing demand for cost optimization tools and FinOps practices"},
        {"id": "T005", "name": "Multi_Cloud", "growth_rate": 25.1, "adoption_score": 7.8, "description": "Enterprises adopting multi-cloud strategies to avoid vendor lock-in"}
    ],
    "total_market_size_usd_billion": 583.4,
    "projected_growth_rate": 21.3,
    "MARKER_ID": "BENCHMARK_MARKET_2024_XK9"
}

with open('raw_market_data.json', 'w') as f:
    json.dump(market_data, f, indent=2)

print('Generated raw_market_data.json')
