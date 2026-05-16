#!/usr/bin/env python3
"""Generate the sandbox workspace with deterministic inputs."""

import json
import os
import random
import time
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "reports/q3/raw",
    "reports/q3/processed",
    "reports/q4/drafts",
    "data/feeds/rss",
    "data/feeds/atom",
    "data/archive/2023",
    "data/archive/2024",
    "config/prod",
    "config/staging",
    "tools/parsers",
    "tools/exporters",
    "logs/errors",
    "logs/access",
    "notebooks",
    "tests/unit",
    "tests/integration",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "reports/q3/raw/feed_dump_2024_07.txt": (
        "TITLE: Some Random Article\nSCORE: 45\nURL: https://example.com/a\n\n"
        "TITLE: Another Post\nSCORE: 310\nURL: https://example.com/b\n"
    ),
    "reports/q3/processed/summary.csv": (
        "title,score,url\n"
        "Old AI News,89,https://old.ai/news\n"
        "Rust Release,450,https://rust-lang.org/release\n"
    ),
    "reports/q4/drafts/newsletter_draft.md": (
        "# Weekly Digest Draft\n\nPlaceholder content for next week's digest.\n"
        "TODO: fill in top stories manually.\n"
    ),
    "data/feeds/rss/hn_snapshot_old.xml": (
        '<?xml version="1.0"?><rss><channel>'
        '<item><title>Python 4.0 Released</title><score>22</score></item>'
        '<item><title>OpenAI New Model</title><score>901</score></item>'
        '</channel></rss>'
    ),
    "data/feeds/atom/tech_feed.json": json.dumps({
        "feed": "tech_daily",
        "items": [
            {"title": "Kubernetes v2", "score": 55},
            {"title": "LLM Benchmark", "score": 180},
        ]
    }, indent=2),
    "data/archive/2023/hn_top_2023.json": json.dumps([
        {"id": 11111, "title": "GPT-3 Released", "score": 2100, "url": "https://openai.com/gpt3"},
    ], indent=2),
    "data/archive/2024/hn_top_jan.json": json.dumps([
        {"id": 22222, "title": "Rust 2024 Edition", "score": 670, "url": "https://rust-lang.org/2024"},
    ], indent=2),
    "config/prod/settings.yaml": (
        "fetch_interval: 3600\nmax_stories: 50\noutput_dir: /reports\n"
    ),
    "config/staging/settings.yaml": (
        "fetch_interval: 600\nmax_stories: 10\noutput_dir: /tmp/reports\n"
    ),
    "tools/parsers/rss_parser.py": (
        "# RSS parser stub\ndef parse(feed_url): pass\n"
    ),
    "tools/exporters/csv_export.py": (
        "# CSV exporter stub\ndef export(data, path): pass\n"
    ),
    "logs/errors/fetch_errors.log": (
        "[2024-01-10 08:00:01] ERROR: Connection timeout\n"
        "[2024-01-10 09:15:22] ERROR: Rate limit exceeded\n"
    ),
    "logs/access/access.log": (
        "GET /api/stories 200 45ms\n"
        "GET /api/stories 200 38ms\n"
        "GET /api/stories 429 0ms\n"
    ),
    "notebooks/exploration.ipynb": json.dumps({
        "cells": [{"cell_type": "markdown", "source": ["# HN Exploration\n"]}],
        "metadata": {"kernelspec": {"name": "python3"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }, indent=2),
    "tests/unit/test_parser.py": (
        "import pytest\ndef test_placeholder(): assert True\n"
    ),
    "tests/integration/test_fetch.py": (
        "import pytest\ndef test_integration_placeholder(): assert True\n"
    ),
}

for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── THE PROBLEM: Pre-seed cache with known, deterministic stories ─────────────
# The cache is fresh (timestamp = now), so if agent does NOT use --no-cache
# it will use these. But we ALSO need them available when --no-cache is not used.
# 
# Strategy: Seed the cache with a known set of stories spanning various scores.
# The agent's task is to extract min-score=250, limit=5, format=json.
# 
# Stories in cache (deterministic):
# Some pass the keyword filter AND score >= 250, some don't.

cache_stories = [
    {
        "id": 40000001,
        "title": "OpenAI releases new reasoning model with breakthrough performance",
        "url": "https://openai.com/news/reasoning-model",
        "score": 1423,
        "by": "techreporter",
        "descendants": 534,
        "time": 1720000000,
    },
    {
        "id": 40000002,
        "title": "Python 3.14 alpha: new syntax features and performance improvements",
        "url": "https://python.org/3.14-alpha",
        "score": 876,
        "by": "py_dev",
        "descendants": 201,
        "time": 1720001000,
    },
    {
        "id": 40000003,
        "title": "Rust 2024 edition: what's new and how to migrate",
        "url": "https://rust-lang.org/2024-edition",
        "score": 654,
        "by": "rustacean",
        "descendants": 178,
        "time": 1720002000,
    },
    {
        "id": 40000004,
        "title": "GitHub Copilot now supports multi-file context and agentic workflows",
        "url": "https://github.blog/copilot-multi-file",
        "score": 512,
        "by": "ghuser",
        "descendants": 143,
        "time": 1720003000,
    },
    {
        "id": 40000005,
        "title": "Startup funding drops 40% as AI bubble concerns grow",
        "url": "https://techcrunch.com/startup-funding-drop",
        "score": 389,
        "by": "vcwatcher",
        "descendants": 290,
        "time": 1720004000,
    },
    {
        "id": 40000006,
        "title": "Machine learning model achieves human parity on coding benchmarks",
        "url": "https://arxiv.org/abs/2407.ml-coding",
        "score": 302,
        "by": "mlresearcher",
        "descendants": 88,
        "time": 1720005000,
    },
    {
        "id": 40000007,
        "title": "Claude 3.5 Sonnet outperforms GPT-4 on reasoning tasks",
        "url": "https://anthropic.com/claude-3-5-sonnet",
        "score": 278,
        "by": "aiobserver",
        "descendants": 412,
        "time": 1720006000,
    },
    {
        "id": 40000008,
        "title": "LLM security vulnerabilities discovered in production systems",
        "url": "https://security.blog/llm-vulns",
        "score": 245,
        "by": "securitypro",
        "descendants": 167,
        "time": 1720007000,
    },
    {
        "id": 40000009,
        "title": "Ask HN: Best practices for production ML pipelines",
        "url": "https://news.ycombinator.com/item?id=40000009",
        "score": 211,
        "by": "mleng",
        "descendants": 95,
        "time": 1720008000,
    },
    {
        "id": 40000010,
        "title": "TypeScript 6.0 announced with major type system overhaul",
        "url": "https://devblogs.microsoft.com/ts6",
        "score": 198,
        "by": "tsdev",
        "descendants": 77,
        "time": 1720009000,
    },
    {
        "id": 40000011,
        "title": "GPT-4o fine-tuning now available for enterprise customers",
        "url": "https://openai.com/fine-tuning-gpt4o",
        "score": 344,
        "by": "aibuilder",
        "descendants": 122,
        "time": 1720010000,
    },
    {
        "id": 40000012,
        "title": "Linux kernel 6.10 released with improved GPU support",
        "url": "https://kernel.org/6.10",
        "score": 89,
        "by": "kerneldev",
        "descendants": 45,
        "time": 1720011000,
    },
    {
        "id": 40000013,
        "title": "Show HN: I built a neural network from scratch in Fortran",
        "url": "https://github.com/user/nn-fortran",
        "score": 267,
        "by": "hobbyist",
        "descendants": 33,
        "time": 1720012000,
    },
    {
        "id": 40000014,
        "title": "Deep learning paper: transformers vs. state space models at scale",
        "url": "https://arxiv.org/abs/2407.transformers-ssm",
        "score": 415,
        "by": "dlresearcher",
        "descendants": 204,
        "time": 1720013000,
    },
    {
        "id": 40000015,
        "title": "Local restaurant review aggregator built with open source tools",
        "url": "https://reviews.local/about",
        "score": 34,
        "by": "foodie",
        "descendants": 12,
        "time": 1720014000,
    },
]

# Write the cache file
cache_dir = Path.home() / ".cache" / "hn-daily"
cache_dir.mkdir(parents=True, exist_ok=True)
cache_path = cache_dir / "hn_cache.json"

cache_data = {
    "timestamp": time.time(),  # Fresh cache - within 4 hours
    "stories": cache_stories,
}
cache_path.write_text(json.dumps(cache_data, indent=2))

# Also write a "stale reference" file the agent should NOT use
(workspace / "data/archive/2024/expected_ids.txt").write_text(
    "# This file lists story IDs from a previous manual curation — do not use directly.\n"
    "40000001\n40000003\n40000007\n40000011\n"
)

print(f"Workspace generated at {workspace}")
print(f"Cache seeded at {cache_path} with {len(cache_stories)} stories")
print("Distractor files created:", len(distractors))