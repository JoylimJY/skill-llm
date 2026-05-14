#!/usr/bin/env python3
"""
Generate the fintech workspace sandbox for the persistent-memory skill task.
"""
import os
import json
import stat
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── Directory skeleton ────────────────────────────────────────────────────────
dirs = [
    "skills/persistent-memory/scripts",
    "skills/persistent-memory/docs",
    "src/gateway",
    "src/settlement",
    "src/compliance",
    "tests/unit",
    "tests/integration",
    "docs/architecture",
    "docs/runbooks",
    "infra/terraform",
    "infra/k8s",
    "scripts",
    "notes",       # raw unstructured notes the agent must read
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
(WORKSPACE / "src/gateway/main.py").write_text("""\
# Payment Gateway - main entrypoint
import fastapi
app = fastapi.FastAPI()

@app.get("/health")
def health(): return {"status": "ok"}
""")

(WORKSPACE / "src/gateway/processor.py").write_text("""\
# Stripe -> internal ledger bridge
class PaymentProcessor:
    def charge(self, amount, currency): ...
    def refund(self, txn_id): ...
""")

(WORKSPACE / "src/settlement/batch.py").write_text("""\
# Daily settlement batch runner
import datetime

def run_batch(date=None):
    date = date or datetime.date.today()
    print(f"Running settlement for {date}")
""")

(WORKSPACE / "src/compliance/kyc.py").write_text("""\
# KYC verification module
def verify_identity(user_id: str) -> bool:
    # placeholder
    return True
""")

(WORKSPACE / "tests/unit/test_processor.py").write_text("""\
import pytest
def test_charge_returns_txn_id(): pass
def test_refund_requires_valid_id(): pass
""")

(WORKSPACE / "tests/integration/test_settlement.py").write_text("""\
import pytest
def test_batch_runs_without_error(): pass
""")

(WORKSPACE / "docs/architecture/overview.md").write_text("""\
# Architecture Overview
The platform uses a microservices approach with Kafka for event streaming.
Payment flow: Client → Gateway → Processor → Ledger → Settlement.
""")

(WORKSPACE / "docs/architecture/adr-001-kafka.md").write_text("""\
# ADR-001: Use Kafka for Event Streaming
Status: Accepted
Date: 2024-01-15
Context: Need reliable async message passing between services.
Decision: Use Kafka (MSK on AWS).
""")

(WORKSPACE / "docs/runbooks/incident-response.md").write_text("""\
# Incident Response Runbook
1. Page on-call via PagerDuty.
2. Check Datadog dashboards.
3. Roll back deployment if latency > 2s.
""")

(WORKSPACE / "infra/terraform/main.tf").write_text("""\
provider "aws" { region = "us-east-1" }
resource "aws_eks_cluster" "payments" { name = "payments-prod" }
""")

(WORKSPACE / "infra/k8s/gateway-deployment.yaml").write_text("""\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
spec:
  replicas: 3
""")

(WORKSPACE / "scripts/migrate_db.sh").write_text("""\
#!/bin/bash
# Run Alembic migrations
alembic upgrade head
""")

# ── The critical raw notes the agent must curate ──────────────────────────────
(WORKSPACE / "notes/project_notes.txt").write_text("""\
=== PAYMENT GATEWAY MIGRATION NOTES ===
Written by: Sarah Chen (Engineering Lead)

DECISIONS MADE (week of 2026-05-12):
- We decided to migrate from legacy FIS gateway to Stripe Connect by 2026-Q3.
  Reason: FIS has 340ms average latency; Stripe averages 90ms. Cost savings ~$180k/yr.
- Architecture decision: all gateway calls must go through the new PaymentProcessor
  abstraction layer (src/gateway/processor.py). No direct Stripe SDK calls from
  business logic. This was contentious but final.
- Rollback strategy: feature flags via LaunchDarkly. Flag name: "use_stripe_gateway".
  If error rate exceeds 0.5%, auto-rollback to FIS.

LESSONS LEARNED:
- KYC verification must be completed BEFORE any payment attempt. We had an incident
  on 2026-04-30 where unverified users were charged. Added pre-flight check.
- Settlement batch MUST run between 02:00-03:00 UTC to avoid overlap with reporting.

TEAM CONTACTS:
- Sarah Chen | Engineering Lead | sarah.chen@paycorp.io | Slack: @sarah-chen
- Marcus Webb | Backend Engineer | marcus.webb@paycorp.io | Slack: @marcus-webb
- Priya Nair | Compliance Officer | priya.nair@paycorp.io | Slack: @priya-nair
- DevOps on-call rotation: devops-oncall@paycorp.io (PagerDuty P1)

EXTERNAL SERVICES:
- Stripe Dashboard: https://dashboard.stripe.com (account: paycorp_prod)
- LaunchDarkly: https://app.launchdarkly.com (project: payments-platform)
- Internal ledger API: https://ledger.internal.paycorp.io/v2
""")

(WORKSPACE / "notes/architecture_notes.txt").write_text("""\
Additional context from Arch Review 2026-05-14:

The new gateway MUST support idempotency keys (Stripe requirement). All POST /charge
calls include X-Idempotency-Key header. Key format: {user_id}-{timestamp}-{amount}.

Database: We're using PostgreSQL 15 on RDS. Connection pool size set to 20 per pod.
Redis used for session cache and idempotency key dedup (TTL: 24h).

Do NOT use synchronous HTTP calls in the settlement batch — use async/await throughout.
""")

# ── Skill scripts (must exist per SKILL.md "already exist" rule) ──────────────
# unified_setup.sh — bootstraps the entire system
unified_setup = r"""#!/usr/bin/env bash
set -e
WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$WORKSPACE_ROOT"

echo "=== Persistent Memory Setup v3.0.0 ==="

# Create directory structure
mkdir -p vector_memory memory reference

# Create venv and install deps (reuse system-level packages for speed)
if [ ! -d "vector_memory/venv" ]; then
    python3 -m venv vector_memory/venv --system-site-packages
fi

# Install any missing deps into venv
vector_memory/venv/bin/pip install --quiet \
    chromadb==0.4.24 \
    networkx==3.2.1 \
    sentence-transformers==2.7.0 \
    -i https://pypi.tuna.tsinghua.edu.cn/simple 2>/dev/null || true

# Create indexer.py
cat > vector_memory/indexer.py << 'PYEOF'
#!/usr/bin/env python3
"""
Persistent Memory Indexer v3.0.0
Indexes MEMORY.md + reference/*.md + memory/*.md into ChromaDB vectors and NetworkX graph.
"""
import sys, os, json, hashlib, re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
CHROMA_DIR = Path(__file__).parent / "chroma_db"
GRAPH_FILE = Path(__file__).parent / "memory_graph.json"
STATE_FILE = WORKSPACE / "memory" / "heartbeat-state.json"

def parse_markdown_chunks(filepath: Path) -> list[dict]:
    """Parse markdown into sections (split on ## headings)."""
    text = filepath.read_text(encoding="utf-8")
    chunks = []
    current_section = "root"
    current_lines = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_lines:
                chunks.append({
                    "section": current_section,
                    "content": "\n".join(current_lines).strip(),
                    "source": str(filepath.relative_to(WORKSPACE))
                })
                current_lines = []
            current_section = line[3:].strip()
        else:
            current_lines.append(line)
    if current_lines:
        chunks.append({
            "section": current_section,
            "content": "\n".join(current_lines).strip(),
            "source": str(filepath.relative_to(WORKSPACE))
        })
    return [c for c in chunks if c["content"]]

def collect_files() -> list[Path]:
    files = []
    for pattern in ["MEMORY.md", "reference/*.md", "memory/*.md"]:
        files.extend(sorted(WORKSPACE.glob(pattern)))
    return files

def build_graph(chunks: list[dict]) -> dict:
    """Build a simple keyword co-occurrence graph."""
    import networkx as nx
    G = nx.Graph()
    for chunk in chunks:
        words = set(re.findall(r'\b[A-Za-z][a-z]{3,}\b', chunk["content"]))
        words = {w.lower() for w in words if len(w) > 4}
        for w in words:
            G.add_node(w)
        words = list(words)
        for i in range(len(words)):
            for j in range(i+1, min(i+4, len(words))):
                if G.has_edge(words[i], words[j]):
                    G[words[i]][words[j]]['weight'] += 1
                else:
                    G.add_edge(words[i], words[j], weight=1)
    return nx.node_link_data(G)

def main():
    import chromadb
    from chromadb.utils import embedding_functions

    print(f"[indexer] Collecting files from {WORKSPACE}")
    files = collect_files()
    if not files:
        print("[indexer] WARNING: No memory files found. Create MEMORY.md first.")
        sys.exit(1)

    all_chunks = []
    for f in files:
        chunks = parse_markdown_chunks(f)
        print(f"  {f.relative_to(WORKSPACE)}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    print(f"[indexer] Total chunks: {len(all_chunks)}")

    # Vector indexing
    CHROMA_DIR.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    try:
        client.delete_collection("memory")
    except Exception:
        pass
    col = client.create_collection("memory", embedding_function=ef)

    ids = [f"chunk_{i}" for i in range(len(all_chunks))]
    docs = [f"{c['section']}: {c['content']}" for c in all_chunks]
    metas = [{"source": c["source"], "section": c["section"]} for c in all_chunks]
    col.add(ids=ids, documents=docs, metadatas=metas)
    print(f"[indexer] Indexed {len(all_chunks)} chunks into ChromaDB")

    # Graph indexing
    graph_data = build_graph(all_chunks)
    GRAPH_FILE.write_text(json.dumps(graph_data, indent=2))
    print(f"[indexer] Knowledge graph saved: {len(graph_data.get('nodes',[]))} nodes")

    # Update state
    memory_md = WORKSPACE / "MEMORY.md"
    md_hash = hashlib.md5(memory_md.read_bytes()).hexdigest() if memory_md.exists() else ""
    state = {
        "last_indexed": datetime.utcnow().isoformat(),
        "memory_md_hash": md_hash,
        "chunk_count": len(all_chunks),
        "graph_nodes": len(graph_data.get("nodes", [])),
        "status": "IN_SYNC"
    }
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))
    print("[indexer] Done. Status: IN_SYNC")

if __name__ == "__main__":
    main()
PYEOF

# Create search.py
cat > vector_memory/search.py << 'PYEOF'
#!/usr/bin/env python3
"""Semantic search CLI — returns top-3 similar chunks."""
import sys, json
from pathlib import Path

CHROMA_DIR = Path(__file__).parent / "chroma_db"
GRAPH_FILE = Path(__file__).parent / "memory_graph.json"

def search(query: str, top_k: int = 3):
    import chromadb
    from chromadb.utils import embedding_functions

    if not CHROMA_DIR.exists():
        print("ERROR: No index found. Run indexer.py first.")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    col = client.get_collection("memory", embedding_function=ef)
    results = col.query(query_texts=[query], n_results=top_k)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    print(f"=== Memory Search: '{query}' ===")
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
        score = round(1 - dist, 4)
        print(f"\n[{i+1}] Source: {meta['source']} | Section: {meta['section']} | Score: {score}")
        print(doc[:400])
    return docs, metas

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: search.py <query>")
        sys.exit(1)
    search(" ".join(sys.argv[1:]))
PYEOF

# Create auto_retrieve.py
cat > vector_memory/auto_retrieve.py << 'PYEOF'
#!/usr/bin/env python3
"""Sync status checker and auto-retrieval tool."""
import sys, json, hashlib
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
STATE_FILE = WORKSPACE / "memory" / "heartbeat-state.json"
MEMORY_MD = WORKSPACE / "MEMORY.md"
CHROMA_DIR = Path(__file__).parent / "chroma_db"

def check_status():
    if not STATE_FILE.exists():
        print("STATUS: OUT_OF_SYNC (no heartbeat state found)")
        return "OUT_OF_SYNC"

    state = json.loads(STATE_FILE.read_text())
    current_hash = hashlib.md5(MEMORY_MD.read_bytes()).hexdigest() if MEMORY_MD.exists() else ""

    if state.get("memory_md_hash") != current_hash:
        print("STATUS: OUT_OF_SYNC (MEMORY.md has changed since last index)")
        return "OUT_OF_SYNC"

    if not CHROMA_DIR.exists() or not any(CHROMA_DIR.iterdir()):
        print("STATUS: OUT_OF_SYNC (ChromaDB not populated)")
        return "OUT_OF_SYNC"

    chunk_count = state.get("chunk_count", 0)
    graph_nodes = state.get("graph_nodes", 0)
    last_indexed = state.get("last_indexed", "unknown")
    print(f"STATUS: IN_SYNC")
    print(f"  Last indexed: {last_indexed}")
    print(f"  Chunks: {chunk_count}")
    print(f"  Graph nodes: {graph_nodes}")
    return "IN_SYNC"

if __name__ == "__main__":
    if "--status" in sys.argv:
        status = check_status()
        sys.exit(0 if status == "IN_SYNC" else 1)
    else:
        print("Usage: auto_retrieve.py --status")
PYEOF

chmod +x vector_memory/indexer.py vector_memory/search.py vector_memory/auto_retrieve.py

echo "=== Setup Complete ==="
echo "Next steps:"
echo "  1. Edit MEMORY.md with curated knowledge"
echo "  2. Run: vector_memory/venv/bin/python vector_memory/indexer.py"
echo "  3. Search: vector_memory/venv/bin/python vector_memory/search.py 'your query'"
"""

(WORKSPACE / "skills/persistent-memory/scripts/unified_setup.sh").write_text(unified_setup)
(WORKSPACE / "skills/persistent-memory/scripts/unified_setup.sh").chmod(
    (WORKSPACE / "skills/persistent-memory/scripts/unified_setup.sh").stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
)

# configure_openclaw.py stub
(WORKSPACE / "skills/persistent-memory/scripts/configure_openclaw.py").write_text("""\
#!/usr/bin/env python3
\"\"\"OpenClaw memorySearch configurator (stub for this environment).\"\"\"
print("OpenClaw integration configured (stub mode).")
""")

# ── Placeholder that must NOT exist yet ──────────────────────────────────────
# MEMORY.md should NOT exist — the agent must create it
# reference/ should NOT exist — the agent must create it
# vector_memory/ should NOT be set up yet

# ── A stale partial attempt (distractor) — wrong structure ──────────────────
(WORKSPACE / "notes/old_memory_attempt.md").write_text("""\
# Old attempt at memory file - DO NOT USE
This file was a rough draft and is not in the correct format.
Some stuff about Stripe migration maybe?
""")

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in WORKSPACE.rglob('*') if _.is_file())}")