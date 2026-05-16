# Changelog

---

## v2.1.1 (2026-03-24)

### 🐛 Bug Fixes

- Fixed: `can_upgrade` returned `True` for already-developers in `check_upgrade`
  - Backend now correctly returns `can_upgrade: False` when user is already a developer
  - Prevents frontend from calling upgrade API and triggering 400 error

### ✨ New Features

- **Lightweight fallback mode**: When Ollama is unavailable, automatically falls back to BM25-only search
  - `_detect_ollama()` probes Ollama availability on startup
  - `bm25_only_search()` provides pure keyword search without vector dependency
  - Search results tagged with `search_type: "bm25_only"`

### 🔧 Improvements

- **Data directory fully separated from code**:
  - Data migrated to `~/.openclaw/memory-workflow-data/`
  - `hot_sessions.json`, `memory_state.json`, `memories/` moved out of skill directory
  - Safer distribution; skill updates never overwrite user data

- **Error handling enhanced**:
  - Rerank service unavailable → silent degradation, no search interruption
  - MiniMax rate limit (429) → warning printed, search continues
  - Ollama connection failure → clear degradation message

- **Documentation improved**:
  - SKILL.md rewritten with clear limitations section
  - RAGAs eval script marked "under development"
  - New bilingual README (Chinese + English)

---

## v2.1.0 (2026-03-23)

### ✨ New Features

- Customizable data directory via `MEMORY_WORKFLOW_DATA` env var
- Two-stage search precision: Stage 1 RRF + Rerank → top 1/3 → Stage 2 secondary RRF fusion
- Query Expansion: HyDE + Query Rewriting with multiple query variants

### 🔧 Improvements

- Milvus demoted to optional dependency; defaults to filesystem when not configured
- SKILL.md external dependencies now clearly labeled as required/recommended/optional

---

## v2.0.0 (2026-03-22)

- Complete refactor, Milvus no longer a hard dependency
- Filesystem storage + background daemon auto-store thread
- Removed `rag_integration.py` dependency
- Simplified installation, ready to use out of the box
