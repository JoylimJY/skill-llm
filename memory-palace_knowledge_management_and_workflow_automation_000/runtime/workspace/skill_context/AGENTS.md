# Memory Palace Knowledge Base

**Generated:** 2026-03-21
**Commit:** ea9f68b
**Branch:** main

## OVERVIEW

OpenClaw Skill for persistent memory management with semantic search, knowledge graphs, and LLM-enhanced cognitive features. TypeScript/Node.js library with optional Python vector service.

## STRUCTURE

```
memory-palace/
├── src/                    # Core library
│   ├── manager.ts          # MemoryPalaceManager (main class)
│   ├── storage.ts          # File-based storage (Markdown + YAML)
│   ├── types.ts            # Type definitions
│   ├── llm/                # LLM integration (Subagent client)
│   ├── background/         # Background tasks (conflict, compress, time)
│   └── cognitive/          # Cognitive modules (cluster, entity, graph)
├── scripts/
│   ├── ab-test/            # A/B testing framework
│   ├── vector-service.py   # Optional Python vector service
│   └── check-vector-deps.cjs  # Postinstall dependency checker
├── tests/                  # Integration tests
├── references/             # Tool docs for SKILL.md
├── bin/                    # CLI executable
└── dist/                   # Compiled output (gitignored)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Store/recall memories | `src/manager.ts` | MemoryPalaceManager class |
| Add new memory fields | `src/types.ts` | Memory, StoreParams interfaces |
| LLM integration | `src/llm/` | SubagentClient calls external LLM |
| Time parsing | `src/background/time-reasoning.ts` | Rule engine + LLM fallback |
| Concept expansion | `src/background/concept-expansion.ts` | Predefined mappings + vector |
| Vector search | `scripts/vector-service.py` | Optional Python service |
| Test patterns | `src/tests/` | Unit tests, `tests/` for integration |
| A/B testing | `scripts/ab-test/` | Validation framework |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `MemoryPalaceManager` | Class | `src/manager.ts` | Main CRUD + search API |
| `Memory` | Interface | `src/types.ts` | Core data structure |
| `FileStorage` | Class | `src/storage.ts` | Markdown file I/O |
| `SubagentClient` | Class | `src/llm/subagent-client.ts` | LLM call orchestration |
| `TimeReasoningEngine` | Class | `src/background/time-reasoning.ts` | Parse temporal expressions |
| `ConceptExpander` | Class | `src/background/concept-expansion.ts` | Query expansion |
| `ExperienceManager` | Class | `src/experience-manager.ts` | Experience CRUD |
| `ConflictDetector` | Class | `src/background/conflict.ts` | Detect memory conflicts |
| `MemoryCompressor` | Class | `src/background/compress.ts` | Compress old memories |

## CONVENTIONS

### ESM with .js Extensions
TypeScript files MUST import with `.js` extensions:
```typescript
// Correct
import { MemoryPalaceManager } from './manager.js';

// Wrong - will fail at runtime
import { MemoryPalaceManager } from './manager';
```

### Memory Defaults
- `importance`: 0.5 (range 0-1)
- `location`: 'default'
- `tags`: [] (empty array)
- `source`: 'user'
- `status`: 'active'

### LLM Tool Timeouts
| Tool | Timeout | Fallback |
|------|---------|----------|
| summarize | 60s | None (returns error) |
| extract_experience | 60s | Rule-based extraction |
| parse_time_llm | 10s | Rule-based time engine |
| expand_concepts_llm | 15s | Predefined mappings |
| compress | 60s | None (returns error) |

### Test Pattern
```typescript
import { describe, it } from 'node:test';
import assert from 'node:assert';

describe('Feature', () => {
  it('should work', () => {
    assert.strictEqual(actual, expected);
  });
});
```

## ANTI-PATTERNS

### Don't Retry on Timeout
`src/llm/subagent-client.ts:240` - When LLM call times out, do NOT retry. Break the retry loop immediately.

### Compression Ratio Always Positive
`src/llm/smart-compressor.ts:163` - Ratio must be >= 0.01, never zero or negative.

### No Auto-Fallback on Vector Failure
When vector search fails, the system throws - it does NOT silently fall back to text search. This is intentional.

### First-Time Vector Setup Required
Users MUST install vector model dependencies before semantic search works:
```bash
pip install sentence-transformers numpy
export HF_ENDPOINT=https://hf-mirror.com  # China users
python scripts/vector-service.py &
```

## COMMANDS

```bash
# Build
npm run build              # tsc -> dist/

# Test
npm test                   # node --test dist/tests/manager.test.js
npm run test:all           # All tests
npm run test:integration   # OpenClaw integration tests

# Lint (warning: no eslint config)
npm run lint               # eslint src/**/*.ts

# CLI
npx memory-palace write "content" '["tag1"]' 0.8
npx memory-palace search "query"
```

## NOTES

### No CI/CD
Project has no `.github/workflows/` or CI configuration. Tests exist but run manually.

### Python Service is Optional
Vector search works without Python (falls back to text matching), but with reduced accuracy.

### Postinstall Modifies Environment
`npm install` runs `scripts/check-vector-deps.cjs` which prompts to install Python packages.

### Storage Format
Memories stored as Markdown with YAML frontmatter:
```markdown
---
id: "uuid"
tags: ["tag1", "tag2"]
importance: 0.8
status: "active"
createdAt: "2026-03-21T10:00:00Z"
---

Memory content here...
```