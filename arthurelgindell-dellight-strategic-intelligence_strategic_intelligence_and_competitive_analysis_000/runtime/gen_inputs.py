import os
import random
import json
import yaml

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure ---
dirs = [
    "intel/raw_feeds",
    "intel/processed",
    "intel/archive/2024_q1",
    "intel/archive/2024_q2",
    "competitors/profiles",
    "competitors/raw_mentions",
    "market/trends",
    "market/sizing",
    "internal/product_roadmap",
    "internal/pricing",
    "reports/weekly",
    "reports/alerts",
    "reports/daily",
    "config",
    "logs",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "config/db_config.yaml": "host: localhost\nport: 5432\ndb: intel_db\n",
    "logs/pipeline.log": "[2024-06-01 08:00] Feed ingestion started\n[2024-06-01 08:05] 14 signals ingested\n[2024-06-01 08:06] Classification pending\n",
    "intel/archive/2024_q1/summary.txt": "Q1 archive: 142 signals processed, 3 alerts issued, 12 weekly reports generated.\n",
    "intel/archive/2024_q2/summary.txt": "Q2 archive: 198 signals processed, 5 alerts issued, 13 weekly reports generated.\n",
    "competitors/raw_mentions/lexai_twitter.txt": "LexAI trending on Twitter after Series B announcement. 2000 mentions in 24h.\n",
    "competitors/raw_mentions/clausebot_reddit.txt": "ClauseBot users complaining about API rate limits on r/legaltech. Some switching to alternatives.\n",
    "market/sizing/legaltech_2024.txt": "Global legal tech market: $22.4B in 2024, projected $37.1B by 2028. CAGR 13.4%.\nContract analysis segment: $4.1B, fastest growing sub-segment.\n",
    "market/trends/ai_contract_review.txt": "AI contract review adoption up 67% YoY among mid-market law firms.\nKey drivers: cost reduction, associate shortage, remote work normalization.\n",
    "internal/product_roadmap/q3_2024.txt": "Q3 Focus: Multi-jurisdiction clause detection, SOC2 compliance module, Salesforce integration.\n",
    "internal/pricing/current_tiers.txt": "Starter: $299/mo (5 users, 100 contracts/mo)\nProfessional: $799/mo (25 users, 500 contracts/mo)\nEnterprise: Custom\n",
    "config/signal_weights.json": json.dumps({"competitor_launch": 0.9, "model_release": 0.7, "market_trend": 0.5, "horizon": 0.3}, indent=2),
    "intel/processed/.gitkeep": "",
    "reports/weekly/.gitkeep": "",
    "reports/alerts/.gitkeep": "",
    "reports/daily/.gitkeep": "",
}

for path, content in distractor_files.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# --- PRIMARY INPUT: Raw messy signal feed ---
raw_signals = [
    {
        "id": "SIG-001",
        "timestamp": "2024-07-15T09:14:00Z",
        "source": "TechCrunch",
        "raw_text": "LexAI just launched 'LexAI Contract Pro' — direct competition to your core contract analysis product. Pricing: $749/mo for 20 users. They claim 40% faster review time. Press release went live 2 hours ago.",
        "tags": ["competitor", "product_launch", "pricing"],
        "notes": "URGENT - from CEO inbox"
    },
    {
        "id": "SIG-002",
        "timestamp": "2024-07-15T11:30:00Z",
        "source": "Anthropic Blog",
        "raw_text": "Claude 3.5 Sonnet released with 200K context window and improved legal document comprehension benchmarks. The model handles complex multi-party contract structures significantly better than previous versions.",
        "tags": ["model_release", "ai_capability"],
        "notes": "Could be a product enabler or threat"
    },
    {
        "id": "SIG-003",
        "timestamp": "2024-07-14T16:00:00Z",
        "source": "LinkedIn + Glassdoor",
        "raw_text": "ClauseBot hiring surge: 14 new job postings in the last 30 days — 6 ML engineers, 4 sales reps targeting enterprise accounts, 2 legal domain experts. Series A close rumored ($18M).",
        "tags": ["competitor", "hiring", "funding"],
        "notes": "Momentum signal"
    },
    {
        "id": "SIG-004",
        "timestamp": "2024-07-13T10:00:00Z",
        "source": "EU Official Journal",
        "raw_text": "EU AI Act implementation timeline confirmed: High-risk AI systems used in legal contexts must comply by August 2026. Legal AI tools processing employment contracts classified as high-risk.",
        "tags": ["regulatory", "eu_ai_act", "compliance"],
        "notes": "Strategic impact uncertain"
    },
    {
        "id": "SIG-005",
        "timestamp": "2024-07-10T08:00:00Z",
        "source": "Internal sales CRM",
        "raw_text": "3 enterprise prospects (2000+ employee firms) asked about multi-jurisdiction support in discovery calls this week. All 3 referenced a Gartner report on AI legal tools. Possible indicator of emerging enterprise demand pattern.",
        "tags": ["customer_signal", "demand", "enterprise"],
        "notes": "Revenue relevant?"
    },
    {
        "id": "SIG-006",
        "timestamp": "2024-07-08T12:00:00Z",
        "source": "Bloomberg Law",
        "raw_text": "NLP-based due diligence tools seeing 3x adoption in M&A practices. Firms report 60% reduction in junior associate hours for contract review. Investment banks now requiring AI-augmented legal review for deals over $500M.",
        "tags": ["market_trend", "adoption", "due_diligence"],
        "notes": "Market expansion signal"
    },
    {
        "id": "SIG-007",
        "timestamp": "2024-07-01T09:00:00Z",
        "source": "Research paper - arXiv",
        "raw_text": "New multimodal legal reasoning benchmark shows LLMs can now interpret scanned handwritten contract amendments with 94% accuracy when combined with vision encoders. Previously required human review.",
        "tags": ["emerging_capability", "multimodal", "research"],
        "notes": "Horizon scanning"
    },
]

with open(os.path.join(WORKSPACE, "intel/raw_feeds/signals_2024_07_15.json"), "w") as f:
    json.dump(raw_signals, f, indent=2)

# --- Partial/incomplete competitor profile stubs (agent must complete per template) ---
competitor_stubs = {
    "LexAI": {
        "founded": 2021,
        "hq": "San Francisco, CA",
        "funding": "Series B - $42M",
        "partial_notes": "Strong NLP team, ex-Palantir engineers. Previously focused on eDiscovery only.",
    },
    "ClauseBot": {
        "founded": 2022,
        "hq": "New York, NY",
        "funding": "Pre-Series A (rumored $18M close)",
        "partial_notes": "SMB focused, aggressive pricing, API-first approach.",
    },
}

with open(os.path.join(WORKSPACE, "competitors/profiles/stubs.json"), "w") as f:
    json.dump(competitor_stubs, f, indent=2)

# --- Context file: Our company ---
our_company = {
    "name": "ContractMind",
    "product_categories": [
        "AI contract analysis",
        "Clause detection and flagging",
        "Contract risk scoring",
        "Multi-jurisdiction compliance checking"
    ],
    "current_customers": "Mid-market law firms (50-500 attorneys), in-house legal teams at F500",
    "differentiators": "Highest accuracy on governing law clauses, SOC2 certified, Salesforce integration (Q3)",
    "pricing_summary": "Starter $299/mo, Pro $799/mo, Enterprise custom"
}

with open(os.path.join(WORKSPACE, "internal/company_context.json"), "w") as f:
    json.dump(our_company, f, indent=2)

print("Workspace initialized successfully.")
print(f"Generated {len(raw_signals)} raw signals in intel/raw_feeds/signals_2024_07_15.json")
print(f"Generated competitor stubs in competitors/profiles/stubs.json")
print(f"Generated company context in internal/company_context.json")