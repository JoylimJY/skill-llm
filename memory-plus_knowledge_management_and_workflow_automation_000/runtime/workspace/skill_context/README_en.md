# 🧠 Memory Workflow

> Intelligent memory workflow for AI agents — zero external DB dependency, data separates from code, graceful degradation.

## ✨ Features

- **Zero external DB dependency** — filesystem storage, skill updates never overwrite user data
- **Two-stage hybrid retrieval** — vector + BM25 + RRF + Rerank precision reranking
- **Query Expansion** — HyDE hypothetical doc + Query Rewriting with multiple variants
- **Graceful degradation** — automatically falls back when Ollama / Rerank / MiniMax is unavailable
- **Auto background storage** — daemon thread stores every 10 minutes, no external cron needed
- **Long-session chunking** — automatic text chunking (50 token overlap) prevents truncation

## 📦 Installation

```bash
# Light mode (Python only)
pip install scikit-learn

# Full mode (recommended)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull bge-m3:latest
ollama pull qwen3.5:latest

# Rerank service (recommended)
docker run -d -p 18778:8000 \
  --gpus all \
  -e MODEL_NAME=BAAI/bge-reranker-v2-m3 \
  ghcr.io/chgaowei/rerank_openai:latest

# Install skill
claw use memory-workflow
```

## 🚀 Quick Start

```bash
# Check status
python3 memory_ops.py check

# Store a memory
python3 memory_ops.py store --content "Discussed lobster platform v2.0 with user" --topic "lobster-platform"

# Search memories
python3 memory_ops.py search --query "lobster platform" --limit 5
```

## 🔧 Configuration

```bash
export OLLAMA_URL=http://localhost:11434
export RERANK_SERVICE_URL=http://localhost:18778
export MEMORY_WORKFLOW_DATA=~/.openclaw/memory-workflow-data
```

See [SKILL.md](SKILL.md) for full configuration reference.

## 📁 Data Directory

```
~/.openclaw/memory-workflow-data/
├── memories/            # Memory files (JSON)
├── memory_state.json    # State (last store time etc.)
└── hot_sessions.json   # Hot session tracking
```

> This directory is **never overwritten** when updating the skill.

## ⚠️ Limitations

| Limitation | Note |
|------------|------|
| Vector search requires Ollama | Falls back to BM25 if unavailable |
| Single-node filesystem | No multi-instance shared memory |
| RAGAs eval script | `ragas_eval.py` is still under development |

## 📄 Docs

- [SKILL.md](SKILL.md) — Full documentation (recommended)
- [CHANGELOG_en.md](CHANGELOG_en.md) — Changelog (English)
