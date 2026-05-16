#!/usr/bin/env python3
import os
import json
import random
from pathlib import Path

random.seed(42)

# Define workspace root
workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create the .openclaw directory structure (without news-sources.json - agent must create it)
openclaw_dir = workspace / ".openclaw"
workspace_dir = openclaw_dir / "workspace"
memory_dir = workspace_dir / "memory"
refs_dir = workspace_dir / "skills" / "news-source-manager" / "references"
logs_dir = workspace_dir / "logs"
cache_dir = workspace_dir / "cache"

for d in [memory_dir, refs_dir, logs_dir, cache_dir]:
    d.mkdir(parents=True, exist_ok=True)

# Create keyword-templates.json (the reference file the skill uses)
keyword_templates = {
    "AI/Tech": {
        "keywords": ["AI", "machine learning", "LLM", "GPT", "tech trends", "AI agents", "semiconductor", "robotics", "AI safety"],
        "sources": [
            {"name": "TechCrunch", "url": "techcrunch.com", "priority": 1},
            {"name": "MIT Technology Review", "url": "technologyreview.com", "priority": 1},
            {"name": "The Verge", "url": "theverge.com", "priority": 2},
            {"name": "Ars Technica", "url": "arstechnica.com", "priority": 2}
        ],
        "search_params": {"freshness": "day", "count": 5},
        "search_hints": ["latest AI technology news", "LLM agents breakthroughs", "semiconductor industry update"]
    },
    "Business Strategy": {
        "keywords": ["M&A", "disruption", "SaaS", "digital transformation", "startup", "corporate strategy", "competitive advantage"],
        "sources": [
            {"name": "McKinsey Insights", "url": "mckinsey.com/insights", "priority": 1},
            {"name": "Harvard Business Review", "url": "hbr.org", "priority": 1},
            {"name": "WSJ", "url": "wsj.com", "priority": 1},
            {"name": "Bloomberg", "url": "bloomberg.com", "priority": 2}
        ],
        "search_params": {"freshness": "week", "count": 5},
        "search_hints": ["business strategy trends", "corporate disruption news", "SaaS startup analysis"]
    },
    "Finance/Crypto": {
        "keywords": ["VC", "IPO", "bitcoin", "DeFi", "macroeconomics", "fintech", "hedge fund", "market volatility"],
        "sources": [
            {"name": "Bloomberg", "url": "bloomberg.com", "priority": 1},
            {"name": "CoinDesk", "url": "coindesk.com", "priority": 1},
            {"name": "Financial Times", "url": "ft.com", "priority": 1},
            {"name": "Reuters", "url": "reuters.com", "priority": 2}
        ],
        "search_params": {"freshness": "day", "count": 7},
        "search_hints": ["crypto market analysis", "VC funding trends", "macroeconomics weekly"]
    },
    "Health/Bio": {
        "keywords": ["biotech", "clinical trials", "CRISPR", "digital health", "medical AI", "pharma", "genomics"],
        "sources": [
            {"name": "STAT News", "url": "statnews.com", "priority": 1},
            {"name": "Nature", "url": "nature.com", "priority": 1},
            {"name": "NEJM", "url": "nejm.org", "priority": 1},
            {"name": "Fierce Biotech", "url": "fiercebiotech.com", "priority": 2}
        ],
        "search_params": {"freshness": "week", "count": 5},
        "search_hints": ["biotech breakthrough news", "clinical trial results", "medical AI applications"]
    },
    "Energy/Climate": {
        "keywords": ["renewable", "battery", "EV", "carbon capture", "hydrogen", "nuclear", "solar", "wind energy"],
        "sources": [
            {"name": "Canary Media", "url": "canarymedia.com", "priority": 1},
            {"name": "CleanTechnica", "url": "cleantechnica.com", "priority": 1},
            {"name": "Carbon Brief", "url": "carbonbrief.org", "priority": 2}
        ],
        "search_params": {"freshness": "week", "count": 5},
        "search_hints": ["clean energy transition news", "EV battery technology", "carbon capture innovation"]
    },
    "Policy/Regulation": {
        "keywords": ["AI regulation", "antitrust", "GDPR", "AI Act", "cybersecurity", "data privacy", "tech policy"],
        "sources": [
            {"name": "Politico", "url": "politico.com", "priority": 1},
            {"name": "Bloomberg Government", "url": "bgov.com", "priority": 1},
            {"name": "Lawfare", "url": "lawfaremedia.org", "priority": 2}
        ],
        "search_params": {"freshness": "day", "count": 5},
        "search_hints": ["AI regulation updates", "antitrust tech policy", "GDPR enforcement news"]
    },
    "Product Design": {
        "keywords": ["UX", "UI", "design system", "accessibility", "Figma", "user research", "design thinking"],
        "sources": [
            {"name": "Nielsen Norman Group", "url": "nngroup.com", "priority": 1},
            {"name": "Smashing Magazine", "url": "smashingmagazine.com", "priority": 1}
        ],
        "search_params": {"freshness": "week", "count": 5},
        "search_hints": ["UX design trends", "design system best practices", "accessibility guidelines update"]
    }
}

(refs_dir / "keyword-templates.json").write_text(
    json.dumps(keyword_templates, indent=2, ensure_ascii=False)
)

# Create distractor files to simulate a realistic workspace

# 1. Old/stale cache files
stale_cache = {
    "last_fetch": "2025-11-01T10:00:00+08:00",
    "results_count": 42,
    "query": "AI news"
}
(cache_dir / "insight-radar-cache.json").write_text(json.dumps(stale_cache, indent=2))

# 2. Logs
(logs_dir / "insight-radar-2026-01-15.log").write_text(
    "[INFO] Starting insight-radar...\n[ERROR] news-sources.json not found\n[INFO] Exiting.\n"
)
(logs_dir / "insight-radar-2026-02-10.log").write_text(
    "[INFO] Loaded 3 categories\n[INFO] Fetched 15 articles\n[INFO] Done.\n"
)

# 3. An OLD/INVALID news-sources.json in the WRONG location (distractor)
old_config_dir = workspace / ".openclaw" / "workspace" / "old_backups"
old_config_dir.mkdir(parents=True, exist_ok=True)
old_invalid_config = {
    "categories": [
        {
            "name": "Tech",
            "active": True
            # Missing required fields - invalid
        }
    ]
}
(old_config_dir / "news-sources.json.bak").write_text(json.dumps(old_invalid_config, indent=2))

# 4. A partial skills manifest
skills_manifest = {
    "skills": [
        {"name": "news-source-manager", "version": "1.2.0", "status": "active"},
        {"name": "insight-radar", "version": "2.0.1", "status": "active"},
        {"name": "web-search", "version": "1.0.0", "status": "active"}
    ]
}
(workspace_dir / "skills" / "manifest.json").write_text(json.dumps(skills_manifest, indent=2))

# 5. insight-radar skill directory with its own config
insight_radar_dir = workspace_dir / "skills" / "insight-radar"
insight_radar_dir.mkdir(parents=True, exist_ok=True)
(insight_radar_dir / "config.json").write_text(json.dumps({
    "max_articles_per_run": 50,
    "dedup_window_hours": 24,
    "coverage_threshold": 0.7
}, indent=2))

# 6. User preferences file (unrelated distractor)
(memory_dir / "user-preferences.json").write_text(json.dumps({
    "language": "zh-CN",
    "timezone": "Asia/Shanghai",
    "notifications": True
}, indent=2))

# 7. A search-history file
(memory_dir / "search-history.json").write_text(json.dumps({
    "history": [
        {"query": "AI chip stocks", "timestamp": "2026-03-01T09:00:00+08:00"},
        {"query": "bitcoin ETF approval", "timestamp": "2026-03-02T14:30:00+08:00"}
    ]
}, indent=2))

# 8. A sessions directory
sessions_dir = workspace_dir / "sessions"
sessions_dir.mkdir(parents=True, exist_ok=True)
for i in range(3):
    (sessions_dir / f"session-2026-03-{20+i:02d}.json").write_text(json.dumps({
        "session_id": f"sess_{1000+i}",
        "duration_seconds": random.randint(30, 300),
        "skills_used": ["insight-radar", "news-source-manager"]
    }, indent=2))

# 9. A corrupted/partial export file (distractor - agent should overwrite/create fresh)
export_dir = workspace_dir / "exports"
export_dir.mkdir(parents=True, exist_ok=True)
(export_dir / "active-news-config.json").write_text('{"active_categories": null, "error": "incomplete export"}')

# 10. Skills README (no hints for this task)
(workspace_dir / "skills" / "news-source-manager" / "ABOUT.txt").write_text(
    "News Source Manager v1.2.0\nManages news category preferences.\nSee references/ for templates.\n"
)

print("Workspace initialized successfully.")
print(f"Structure created under: {workspace}")
print("Note: news-sources.json does NOT exist yet (agent must create it).")