import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ─── Directory structure ───────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "logs",
    "cache",
    "cache/exa",
    "cache/tavily",
    "cache/binance",
    "data/raw",
    "data/processed",
    "config",
    "archive",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "config/providers.yaml": textwrap.dedent("""\
        providers:
          exa:
            endpoint: https://api.exa.ai/search
          tavily:
            endpoint: https://api.tavily.com/search
          alpha_vantage:
            endpoint: https://www.alphavantage.co/query
          binance:
            endpoint: https://api.binance.com/api/v3/ticker/price
        """),
    "config/weights_old.json": json.dumps({
        "factual": {"exa": 0.6, "tavily": 0.4},
        "news": {"tavily": 0.7, "exa": 0.3},
    }, indent=2),
    "logs/search_2024_01_15.log": "\n".join([
        "[INFO] Query: BTC price",
        "[INFO] Sources: binance, alpha-vantage",
        "[INFO] Results: 8",
        "[WARN] alpha-vantage rate limit hit",
    ]),
    "logs/search_2024_01_16.log": "\n".join([
        "[INFO] Query: Solana vs Ethereum",
        "[INFO] mode: deep, intent: comparison",
        "[INFO] Results: 12",
    ]),
    "cache/exa/cache_index.json": json.dumps({"entries": [], "version": "1.2.0"}),
    "cache/tavily/cache_index.json": json.dumps({"entries": [], "version": "1.1.3"}),
    "cache/binance/btc_snapshot.json": json.dumps({
        "symbol": "BTCUSDT",
        "price": "67234.00",
        "timestamp": "2024-01-16T10:00:00Z"
    }, indent=2),
    "data/raw/eth_historical.csv": "date,open,high,low,close\n2024-01-01,2200,2350,2180,2310\n2024-01-02,2310,2400,2290,2380\n",
    "data/processed/comparison_notes.txt": "Solana: high TPS, lower fees\nEthereum: mature ecosystem, PoS since 2022\n",
    "archive/old_report_v1.json": json.dumps({
        "title": "Old ETH report",
        "findings": ["ETH 2.0 launched", "Gas fees reduced"],
        "generated_at": "2023-06-01"
    }, indent=2),
    "archive/old_report_v2.json": json.dumps({
        "title": "Old Solana report",
        "findings": ["Solana recovered from outages"],
        "generated_at": "2023-09-15"
    }, indent=2),
}
for rel_path, content in distractors.items():
    p = workspace / rel_path
    p.write_text(content)

# ─── references/intent-guide.md ───────────────────────────────────────────────
intent_guide = textwrap.dedent("""\
# Intent Guide

## Intent types and cues

| Intent | Trigger phrases | Recommended mode |
|---|---|---|
| factual | "what is", "define", "explain" | answer |
| status | "latest", "current", "now", "realtime", "price" | fast (quote only) or deep (quote+context) |
| comparison | "vs", "compare", "difference between", "versus" | deep |
| tutorial | "how to", "guide", "step by step" | answer |
| exploratory | "overview of", "landscape", "survey", "research" | deep |
| news | "recent news", "updates", "latest developments" | deep |
| resource | "find me", "list of", "tools for", "libraries" | fast |

## Multi-intent queries

When a query spans multiple intents (e.g., comparison + status/realtime), split into sub-queries:
- One or more comparison sub-queries using `--queries`
- A dedicated realtime/status sub-query using `--source` to activate finance-aware path

For finance-aware realtime prioritization with broader context, use:
  --mode deep --intent status --source alpha-vantage,binance,gemini,kimi,tavily

For pure quote lookup only, use:
  --mode fast --intent status --source alpha-vantage,binance

## Chinese-query notes

- If the query contains CJK characters, the aggregator applies CJK-aware keyword matching
- Chinese-friendly sources (kimi, gemini) get a modest boost automatically
- No special flag is needed — detection is automatic

## Synthesis rules

After retrieval:
1. Group findings by **theme** (not by provider)
2. Answer first, cite sources inline
3. Explicitly call out conflicting claims between sources
4. Treat single-source or older claims (> 30 days) with lower confidence
5. For finance realtime data, always note the timestamp and source

## Finance-aware path details

Triggered when intent == "status" AND source list includes alpha-vantage or binance.
- alpha-vantage gets priority boost for: stocks, ETFs, forex, index proxies
- binance gets priority boost for: crypto spot prices (BTC, ETH, SOL, etc.)
- If both sources are in the list, binance leads for crypto, alpha-vantage leads for tradfi
""")
(workspace / "references" / "intent-guide.md").write_text(intent_guide)

# ─── references/authority-domains.json ────────────────────────────────────────
authority_domains = {
    "high": ["coindesk.com", "bloomberg.com", "reuters.com", "docs.etherscan.io", "ethereum.org"],
    "medium": ["medium.com", "substack.com", "github.com"],
    "low": ["reddit.com", "twitter.com", "forum.unknown.io"],
    "finance_realtime": ["alphavantage.co", "binance.com", "coingecko.com"],
    "chinese_friendly": ["kimi.moonshot.cn", "gemini.google.com"]
}
(workspace / "references" / "authority-domains.json").write_text(
    json.dumps(authority_domains, indent=2, ensure_ascii=False)
)

# ─── references/research-light-regression-samples.md ─────────────────────────
regression_samples = textwrap.dedent("""\
# Research-light regression samples

## Sample 1: Factual query
Query: "What is Ethereum proof of stake?"
Mode: answer, Intent: factual
Expected: single-pass retrieval, no thread-pulling

## Sample 2: Comparison query
Query: "Solana vs Ethereum TPS"
Mode: deep, Intent: comparison
Expected: multi-query split into ["Solana TPS", "Ethereum TPS", "Solana vs Ethereum"]

## Sample 3: Finance realtime
Query: "ETH current price"
Mode: fast, Intent: status, Sources: alpha-vantage,binance
Expected: finance-aware boost applied, binance leads for ETH

## Sample 4: Mixed comparison + finance
Query: "Compare Solana and Ethereum and get ETH price"
Mode: deep for comparison part, fast for price part
Expected: separate invocations or combined deep+status with full source list
""")
(workspace / "references" / "research-light-regression-samples.md").write_text(regression_samples)

# ─── scripts/search.py — mock implementation ──────────────────────────────────
search_py_clean = '''\
#!/usr/bin/env python3
"""
Multi-source retrieval and reranking entrypoint (mock implementation).
Records invocation arguments for evaluation.
Outputs structured results as JSON to stdout.
"""
import sys
import json
import argparse
import time
from pathlib import Path

INVOCATION_LOG = Path("/workspace/logs/search_invocations.jsonl")

def parse_args():
    parser = argparse.ArgumentParser(description="OpenClaw Glasses search aggregator")
    parser.add_argument("query", nargs="?", default=None, help="Single search query")
    parser.add_argument("--queries", nargs="+", default=None, help="Multiple search queries")
    parser.add_argument("--mode", choices=["fast", "deep", "answer"], default="fast")
    parser.add_argument("--intent", default="factual",
                        choices=["factual", "status", "comparison", "tutorial",
                                 "exploratory", "news", "resource"])
    parser.add_argument("--num", type=int, default=5)
    parser.add_argument("--source", default=None, help="Comma-separated list of sources")
    return parser.parse_args()

def make_fake_results(query, mode, intent, sources, num):
    base = {
        "comparison": [
            {"title": "Solana vs Ethereum: Performance Deep Dive",
             "url": "https://coindesk.com/solana-eth-perf",
             "snippet": "Solana achieves ~65k TPS theoretical vs Ethereum ~30 TPS post-Merge.",
             "source": "coindesk", "score": 0.92, "timestamp": "2024-01-10"},
            {"title": "Ethereum Ecosystem Maturity vs Solana Speed",
             "url": "https://ethereum.org/compare",
             "snippet": "Ethereum has broader DeFi liquidity; Solana leads in raw throughput.",
             "source": "ethereum.org", "score": 0.89, "timestamp": "2024-01-08"},
            {"title": "Solana advantages for DeFi",
             "url": "https://medium.com/solana-defi",
             "snippet": "Low fees and fast finality make Solana attractive for high-frequency DeFi.",
             "source": "medium", "score": 0.74, "timestamp": "2024-01-05"},
            {"title": "Ethereum advantages: security and decentralization",
             "url": "https://medium.com/eth-security",
             "snippet": "Ethereum validator count and audit history remain industry benchmarks.",
             "source": "medium", "score": 0.71, "timestamp": "2024-01-03"},
        ],
        "status": [
            {"title": "ETH/USDT Realtime Price",
             "url": "https://binance.com/eth",
             "snippet": "ETH current price: $3,412.55 (+1.8% 24h)",
             "source": "binance", "score": 0.98,
             "timestamp": "2024-01-16T09:55:00Z", "realtime": True},
            {"title": "Ethereum Price Today - Alpha Vantage",
             "url": "https://alphavantage.co/eth",
             "snippet": "ETH: $3,411.20 as of market open. 24h high: $3,450.",
             "source": "alpha-vantage", "score": 0.96,
             "timestamp": "2024-01-16T09:50:00Z", "realtime": True},
        ],
    }
    chosen = base.get(intent, base["comparison"])
    if sources and ("binance" in sources or "alpha-vantage" in sources):
        for r in chosen:
            if r.get("source") in ["binance", "alpha-vantage"]:
                r["score"] = min(r["score"] + 0.05, 1.0)
                r["finance_boosted"] = True
    return chosen[:num]

def main():
    args = parse_args()
    invocation = {
        "timestamp": time.time(),
        "query": args.query,
        "queries": args.queries,
        "mode": args.mode,
        "intent": args.intent,
        "num": args.num,
        "source": args.source,
    }
    INVOCATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(INVOCATION_LOG, "a") as f:
        f.write(json.dumps(invocation) + "\\n")

    if args.queries:
        all_queries = args.queries
    elif args.query:
        all_queries = [args.query]
    else:
        print(json.dumps({"error": "No query provided"}))
        sys.exit(1)

    all_results = []
    for q in all_queries:
        r = make_fake_results(q, args.mode, args.intent, args.source, args.num)
        all_results.extend(r)

    seen = set()
    deduped = []
    for item in all_results:
        if item["url"] not in seen:
            seen.add(item["url"])
            deduped.append(item)

    output = {
        "query": args.query,
        "queries": args.queries,
        "mode": args.mode,
        "intent": args.intent,
        "source": args.source,
        "results": deduped,
        "result_count": len(deduped),
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
'''

(workspace / "scripts" / "search.py").write_text(search_py_clean)

# ─── scripts/fetch_thread.py ──────────────────────────────────────────────────
fetch_thread_py = '''\
#!/usr/bin/env python3
"""
Deep-fetch GitHub issues/PRs or generic pages to extract structured references.
"""
import sys
import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL to fetch thread from")
    parser.add_argument("--extract-refs", action="store_true")
    args = parser.parse_args()
    result = {
        "url": args.url,
        "title": "Mock thread title",
        "references": ["https://github.com/example/issue/1", "https://github.com/example/pr/42"],
        "extract_refs": args.extract_refs
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "fetch_thread.py").write_text(fetch_thread_py)

# ─── scripts/chain_tracker.py ─────────────────────────────────────────────────
chain_tracker_py = '''\
#!/usr/bin/env python3
"""
Recursive thread-pulling / follow-up exploration with relevance gating.
"""
import sys
import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("seed_url", help="Seed URL to start chain tracking")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--relevance-threshold", type=float, default=0.5)
    args = parser.parse_args()
    result = {
        "seed": args.seed_url,
        "depth": args.depth,
        "chain": [args.seed_url, "https://github.com/related/1", "https://docs.example.com/ref"]
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "chain_tracker.py").write_text(chain_tracker_py)

# ─── scripts/relevance_gate.py ────────────────────────────────────────────────
relevance_gate_py = '''\
#!/usr/bin/env python3
"""
Batch relevance filtering for candidate links.
"""
import sys
import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--links", nargs="+", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--threshold", type=float, default=0.5)
    args = parser.parse_args()
    filtered = [{"url": l, "score": 0.75, "kept": True} for l in args.links]
    print(json.dumps({"query": args.query, "filtered": filtered}, indent=2))

if __name__ == "__main__":
    main()
'''
(workspace / "scripts" / "relevance_gate.py").write_text(relevance_gate_py)

print("Workspace generated successfully.")
print("Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")