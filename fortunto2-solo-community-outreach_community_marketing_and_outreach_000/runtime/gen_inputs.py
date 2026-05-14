import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")

# --- Create realistic directory structure with distractors ---
dirs = [
    "docs",
    "research",
    "research/reddit",
    "research/hn",
    "research/producthunt",
    "src",
    "src/core",
    "src/migrations",
    "tests",
    "tests/unit",
    "tests/integration",
    ".github/workflows",
    "marketing/assets",
    "marketing/copy",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

(workspace / "src/core/schema_parser.py").write_text("""
# Core schema parsing logic for SchemaDrift
import re

def parse_ddl(ddl_string):
    \"\"\"Parse DDL statements and extract schema objects.\"\"\"
    tables = re.findall(r'CREATE TABLE (\\w+)', ddl_string, re.IGNORECASE)
    return tables

def diff_schemas(old, new):
    \"\"\"Compute diff between two schema snapshots.\"\"\"
    added = set(new) - set(old)
    removed = set(old) - set(new)
    return {'added': list(added), 'removed': list(removed)}
""")

(workspace / "src/migrations/runner.py").write_text("""
# Migration runner - applies diffs to target database
class MigrationRunner:
    def __init__(self, dsn):
        self.dsn = dsn
    
    def apply(self, migration_script):
        # Apply migration script to the database
        pass
    
    def rollback(self, version):
        pass
""")

(workspace / "tests/unit/test_parser.py").write_text("""
import pytest
from src.core.schema_parser import parse_ddl, diff_schemas

def test_parse_simple_ddl():
    ddl = \"CREATE TABLE users (id SERIAL PRIMARY KEY, email TEXT)\"
    result = parse_ddl(ddl)
    assert 'users' in result

def test_diff_schemas_added():
    old = ['users', 'orders']
    new = ['users', 'orders', 'products']
    diff = diff_schemas(old, new)
    assert 'products' in diff['added']
""")

(workspace / "tests/integration/test_runner.py").write_text("""
# Integration tests require a live Postgres instance
# Run with: pytest tests/integration/ --postgres-dsn=postgresql://...
import pytest

@pytest.mark.integration
def test_full_migration_cycle():
    pass
""")

(workspace / ".github/workflows/ci.yml").write_text("""
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: pytest tests/unit/
""")

(workspace / "marketing/assets/logo_notes.txt").write_text("""
Logo: navy blue gear icon with schema tree lines
Colors: #1A2B4A (navy), #00C896 (mint green), #F5F5F5 (light grey)
Tagline options:
  - "Schema changes without the drama"
  - "Know before you break"
  - "Postgres schema drift, caught early"
""")

(workspace / "marketing/copy/email_draft.txt").write_text("""
Subject: Never break prod with a schema change again

Hey {first_name},

If you've ever run ALTER TABLE in production and held your breath...
SchemaDrift is for you.

We detect schema drift before it becomes an incident.

Try it free: https://schemedrift.dev
""")

(workspace / "src/core/config.py").write_text("""
DEFAULT_CONFIG = {
    'poll_interval_seconds': 60,
    'max_connections': 10,
    'alert_channels': ['slack', 'email', 'pagerduty'],
    'supported_databases': ['postgresql', 'aurora_postgresql'],
}
""")

(workspace / "docs/CHANGELOG.md").write_text("""
# Changelog

## v0.9.1 (2024-11-15)
- Fix: race condition in diff computation
- Improve: faster schema snapshot hashing

## v0.9.0 (2024-10-01)
- Initial public beta release
- Support for PostgreSQL 13, 14, 15
- Slack and email alerting
- CLI tool for local diffing

## v0.8.0 (2024-08-20)
- Internal alpha
""")

(workspace / "docs/architecture.md").write_text("""
# SchemaDrift Architecture

## Components
1. **Watcher** — polls target Postgres instances on a configurable interval
2. **Differ** — computes AST-level diffs between snapshots  
3. **Alerter** — dispatches alerts via configured channels
4. **Dashboard** — web UI showing drift history

## Data Flow
Watcher → Postgres → Snapshot Store → Differ → Alert Engine → Channels
""")

# --- The messy PRD (key input for the agent) ---
(workspace / "docs/product-brief.md").write_text("""
# SchemaDrift - Product Brief (DRAFT - messy, needs cleanup)

**Status:** Internal working doc. Not polished.

## What is it??
SchemaDrift is a tool that watches your PostgreSQL databases and tells you when the schema changes unexpectedly. Think of it like "git diff for your database schema" but automated, continuous, and hooked into your alerting stack.

Problem we're solving: Dev pushes an ALTER TABLE to staging, it accidentally gets applied to prod (or someone ran it manually). Entire application breaks. Team spends 3 hrs debugging. We've seen this happen at $50M+ ARR companies.

## Who is it for (ICP):
- Backend engineers at Series A-C startups (5-200 devs)
- Teams running PostgreSQL (not MySQL, not MongoDB)  
- Companies where DB schema changes have caused incidents before
- DevOps/platform teams responsible for DB reliability
- Also useful for: SRE teams, DB administrators at mid-size companies

## Key Features:
1. Continuous schema snapshot comparison (poll every N seconds)
2. AST-level diffing (understands column types, constraints, indexes, not just raw DDL text)
3. Alerting: Slack, PagerDuty, email, webhooks
4. CLI tool: `schemedrift diff` — compare two snapshots locally
5. Time-travel: browse schema history for any DB
6. Access controls: mask sensitive table names in alerts

## Competitors we know of:
- Liquibase (heavyweight migration framework, XML-based, old school)
- Flyway (similar to Liquibase, more popular in Java ecosystem)
- pgaudit (Postgres extension, logs queries not schema changes)
- Bytebase (GUI-heavy, expensive, more of a DBA tool)
- Atlas (Terraform-for-schemas, declarative approach, different angle)

## Pricing (TBD):
- Free tier: 1 database, 1 hour polling interval
- Pro: $49/mo, up to 10 databases, 1 min polling, all alert channels
- Team: $149/mo, unlimited databases, SSO, audit logs

## Technical notes:
Requires read-only access to information_schema and pg_catalog.
No agent installation on DB server needed (external polling).
Open source core, cloud-hosted SaaS version.
GitHub: github.com/schemedrift/schemedrift (12 stars so far lol)

## What we need:
Marketing / community presence. We have zero community footprint right now.
Need to find relevant Reddit/HN discussions and start being helpful there.
""")

# --- Simulate search results (what web searches would return) ---
# These files represent the "found threads" from community searches

# TODAY for reference: use a fixed date so threads can be evaluated as "recent" or "old"
reference_date = datetime(2025, 1, 15)  # Fixed reference date for the task

# Reddit search results - mix of good (recent, active) and bad (old/inactive) threads
reddit_results = [
    {
        "id": "r001",
        "title": "Our team lost 4 hours yesterday because someone altered a prod table without telling anyone - how do you prevent this?",
        "url": "https://www.reddit.com/r/devops/comments/abc123/our_team_lost_4_hours_yesterday/",
        "subreddit": "r/devops",
        "post_date": "2024-11-20",
        "comment_count": 47,
        "upvotes": 312,
        "top_comment": "We use a migration framework but it doesn't catch manual changes. Looking for something that monitors for unexpected drift.",
        "relevance_notes": "Exact pain point. Recent, very active."
    },
    {
        "id": "r002",
        "title": "Best tools for tracking PostgreSQL schema changes in production?",
        "url": "https://www.reddit.com/r/postgresql/comments/def456/best_tools_for_tracking_postgres_schema_changes/",
        "subreddit": "r/postgresql",
        "post_date": "2024-12-01",
        "comment_count": 23,
        "upvotes": 89,
        "top_comment": "Tried Liquibase but it's so heavyweight. Anyone using something lighter?",
        "relevance_notes": "Direct recommendation request. Recent."
    },
    {
        "id": "r003",
        "title": "Liquibase is driving me insane - looking for alternatives",
        "url": "https://www.reddit.com/r/java/comments/ghi789/liquibase_is_driving_me_insane/",
        "subreddit": "r/java",
        "post_date": "2024-10-15",
        "comment_count": 61,
        "upvotes": 203,
        "top_comment": "Flyway is better but still XML config. Is there anything that just *watches* and alerts?",
        "relevance_notes": "Competitor frustration thread. Good engagement."
    },
    {
        "id": "r004",
        "title": "Database schema versioning - what's your workflow in 2024?",
        "url": "https://www.reddit.com/r/programming/comments/jkl012/database_schema_versioning_workflow_2024/",
        "subreddit": "r/programming",
        "post_date": "2024-09-10",
        "comment_count": 38,
        "upvotes": 156,
        "top_comment": "We just use git for DDL files. But catching unplanned changes is still a gap.",
        "relevance_notes": "Workflow discussion. Active. 4+ months old but < 6 months."
    },
    {
        "id": "r005",
        "title": "PSA: Never run ALTER TABLE on prod without a plan - we just had a 6hr incident",
        "url": "https://www.reddit.com/r/sysadmin/comments/mno345/psa_never_run_alter_table_on_prod_without_plan/",
        "subreddit": "r/sysadmin",
        "post_date": "2025-01-02",
        "comment_count": 92,
        "upvotes": 478,
        "top_comment": "The worst is when devs have direct prod access and do stuff manually. Need better monitoring.",
        "relevance_notes": "Very recent, very active, perfect pain point."
    },
    {
        "id": "r006",  # DISTRACTOR: too old
        "title": "How does Flyway compare to Liquibase in 2022?",
        "url": "https://www.reddit.com/r/java/comments/pqr678/flyway_vs_liquibase_2022/",
        "subreddit": "r/java",
        "post_date": "2022-03-15",
        "comment_count": 45,
        "upvotes": 120,
        "relevance_notes": "Too old (2022). Should be filtered out."
    },
    {
        "id": "r007",  # DISTRACTOR: too few comments
        "title": "Has anyone tried Atlas for schema management?",
        "url": "https://www.reddit.com/r/devops/comments/stu901/has_anyone_tried_atlas_schema_management/",
        "subreddit": "r/devops",
        "post_date": "2024-12-20",
        "comment_count": 3,
        "upvotes": 14,
        "relevance_notes": "Too inactive (3 comments). Should be filtered out."
    },
    {
        "id": "r008",
        "title": "Bytebase vs Atlas vs roll-your-own - schema change management comparison",
        "url": "https://www.reddit.com/r/database/comments/vwx234/bytebase_vs_atlas_vs_roll_your_own/",
        "subreddit": "r/database",
        "post_date": "2024-11-05",
        "comment_count": 29,
        "upvotes": 97,
        "relevance_notes": "Competitor comparison. Recent, good engagement."
    }
]

# HN search results
hn_results = [
    {
        "id": "hn001",
        "title": "Ask HN: How do you detect unintended schema changes in production databases?",
        "url": "https://news.ycombinator.com/item?id=38291047",
        "post_date": "2024-11-08",
        "points": 187,
        "comment_count": 63,
        "relevance_notes": "Direct Ask HN matching our exact problem. Very high engagement."
    },
    {
        "id": "hn002",
        "title": "Show HN: Atlas – Declarative schema management for PostgreSQL",
        "url": "https://news.ycombinator.com/item?id=36120893",
        "post_date": "2024-06-15",
        "points": 342,
        "comment_count": 118,
        "relevance_notes": "Competitor launch on HN. Good to understand the space and engage."
    },
    {
        "id": "hn003",  # DISTRACTOR: too old
        "title": "Flyway – Database migration tool",
        "url": "https://news.ycombinator.com/item?id=12398234",
        "post_date": "2019-02-11",
        "points": 289,
        "comment_count": 74,
        "relevance_notes": "Too old (2019). Filter out."
    },
    {
        "id": "hn004",
        "title": "Ask HN: What tools do you use for database DevOps?",
        "url": "https://news.ycombinator.com/item?id=39102847",
        "post_date": "2024-12-30",
        "points": 94,
        "comment_count": 41,
        "relevance_notes": "Recent broad question about DB DevOps tooling."
    }
]

# ProductHunt search results
ph_results = [
    {
        "id": "ph001",
        "product_name": "Atlas",
        "url": "https://www.producthunt.com/posts/atlas-for-databases",
        "launch_date": "2024-06-14",
        "upvotes": 687,
        "tagline": "Declarative database schema management",
        "relevance_notes": "Direct competitor on PH. Shows market exists."
    },
    {
        "id": "ph002",
        "product_name": "Bytebase",
        "url": "https://www.producthunt.com/posts/bytebase",
        "launch_date": "2022-11-30",
        "upvotes": 412,
        "tagline": "Database schema change management for teams",
        "relevance_notes": "Another competitor. Lower upvotes but established."
    },
    {
        "id": "ph003",
        "product_name": "pgMustard",
        "url": "https://www.producthunt.com/posts/pgmustard",
        "launch_date": "2023-08-10",
        "upvotes": 156,
        "tagline": "PostgreSQL query performance insights",
        "relevance_notes": "Adjacent postgres tooling. Different problem."
    }
]

# Save research files
with open(workspace / "research/reddit/search_results.json", "w") as f:
    json.dump(reddit_results, f, indent=2)

with open(workspace / "research/hn/search_results.json", "w") as f:
    json.dump(hn_results, f, indent=2)

with open(workspace / "research/producthunt/search_results.json", "w") as f:
    json.dump(ph_results, f, indent=2)

# Search keywords log (simulating what was searched)
keywords_log = {
    "problem_keywords": [
        {"keyword": "postgresql schema change production incident", "results_count": 47},
        {"keyword": "database drift detection", "results_count": 23},
        {"keyword": "unexpected schema change postgres", "results_count": 18}
    ],
    "solution_keywords": [
        {"keyword": "postgres schema monitoring tool", "results_count": 31},
        {"keyword": "database schema versioning automated", "results_count": 29}
    ],
    "competitor_keywords": [
        {"keyword": "liquibase alternative reddit", "results_count": 61},
        {"keyword": "bytebase vs atlas reddit", "results_count": 29},
        {"keyword": "flyway alternative lightweight", "results_count": 38}
    ],
    "category_keywords": [
        {"keyword": "database devops tools", "results_count": 41},
        {"keyword": "schema management postgresql", "results_count": 34}
    ]
}

with open(workspace / "research/keywords_searched.json", "w") as f:
    json.dump(keywords_log, f, indent=2)

# Additional distractor files
(workspace / "research/notes.txt").write_text("""
Random notes from initial research session:
- Reddit communities to look at: r/devops, r/postgresql, r/database, r/sysadmin, r/programming
- HN has good postgres discussion, especially Ask HN threads
- ProductHunt timing matters a lot - Tuesday-Thursday PST
- Consider Indie Hackers too for B2B dev tools
- Check subreddit rules before posting! r/postgresql has strict no-promo rules
""")

(workspace / "marketing/copy/old_taglines.txt").write_text("""
Rejected taglines:
- "We watch your database so you don't have to" (too passive)
- "Schema drift detector for postgres" (too boring)
- "The smoke detector for your database schema" (maybe?)
- "Schema changes without the drama" (WINNER - use this)
""")

print("Workspace initialized successfully.")
print(f"Created files in: {workspace}")