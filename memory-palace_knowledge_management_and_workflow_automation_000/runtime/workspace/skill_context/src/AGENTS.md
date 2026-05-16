# Memory Palace Source Directory

Core TypeScript library for Memory Palace. Entry point: `index.ts`.

## STRUCTURE

```
src/
├── manager.ts           # MemoryPalaceManager (main API)
├── storage.ts           # FileStorage + Markdown/YAML I/O
├── types.ts             # All type definitions (Memory, StoreParams, etc.)
├── experience-manager.ts # Experience CRUD operations
├── llm/                 # LLM integration via SubagentClient
│   ├── subagent-client.ts  # Core LLM wrapper with retry/timeout
│   ├── summarizer.ts       # Memory summarization
│   ├── experience-extractor.ts  # Extract experiences from memories
│   ├── time-parser.ts      # Complex time parsing via LLM
│   ├── concept-expander.ts # Dynamic query expansion
│   └── smart-compressor.ts # Intelligent memory compression
├── background/          # Background tasks
│   ├── time-reasoning.ts   # Rule-based + LLM time parsing
│   ├── concept-expansion.ts # Predefined mappings + vector
│   ├── conflict.ts         # Detect contradictory memories
│   ├── compress.ts         # Memory compression strategies
│   └── vector-search.ts    # Python service integration
├── cognitive/           # Cognitive modules
│   ├── cluster.ts      # Topic clustering by tags/keywords
│   ├── entity.ts       # Entity extraction and tracking
│   └── graph.ts        # Knowledge graph builder
└── tests/              # Unit tests (run via npm test)
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add new API method | `manager.ts` | MemoryPalaceManager class |
| Add new type/interface | `types.ts` | Export from `index.ts` |
| Change storage format | `storage.ts` | serializeMemory/deserializeMemory |
| New LLM tool | `llm/*.ts` | Export via `llm/index.ts` |
| New background task | `background/*.ts` | Export via main `index.ts` |
| Cognitive analysis | `cognitive/*.ts` | Standalone modules |
| Unit test for X | `tests/X.test.ts` | Node:test pattern |

## CONVENTIONS

### Factory Functions
Background modules use factory functions: `createTimeReasoning()`, `createConceptExpander()`. Prefer these over direct class imports.

### Default Instance Exports
LLM modules export `defaultX` instances: `defaultSummarizer`, `defaultExtractor`. Use convenience functions (`summarizeMemory()`) directly.

### Export Chain
Public APIs flow through `index.ts`. New module: subdirectory index → `src/index.ts`.

### FileLock Scope
`storage.ts` uses in-memory locks. Single-process only.

## ANTI-PATTERNS

- **LLM modules without fallback**: All LLM tools need fallback. See `callLLMWithFallback()` pattern.
- **Config reading outside SubagentClient**: OpenClaw config loading is centralized in `SubagentClient.loadOpenClawConfig()`.