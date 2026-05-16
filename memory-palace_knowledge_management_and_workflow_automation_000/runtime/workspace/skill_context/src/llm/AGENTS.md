# LLM Integration Module

**Parent:** `/data/memory-palace/AGENTS.md`

## OVERVIEW

LLM integration layer with SubagentClient orchestration and specialized modules for summarization, extraction, parsing, and compression.

## STRUCTURE

```
src/llm/
├── subagent-client.ts    # Core LLM call client with retry/timeout/fallback
├── types.ts              # LLMOptions, LLMResult, response types
├── index.ts              # Public exports
├── summarizer.ts         # Memory summarization (summary, tags, importance)
├── experience-extractor.ts  # Extract reusable experiences from memories
├── time-parser.ts        # Parse complex temporal expressions
├── concept-expander.ts   # Dynamic concept/keyword expansion
└── smart-compressor.ts   # Intelligent memory compression
```

## WHERE TO LOOK

| Task | File | Key Export |
|------|------|------------|
| Call LLM with JSON response | `subagent-client.ts` | `SubagentClient.callJSON()` |
| Add LLM timeout config | `subagent-client.ts:74` | `defaultTimeout` |
| Modify retry behavior | `subagent-client.ts:212` | `callJSON()` retry loop |
| Add new response type | `types.ts` | Add interface, export in `index.ts` |
| Customize summarization | `summarizer.ts` | `LLMSummarizer.summarize()` |
| Compression ratio logic | `smart-compressor.ts:158` | `calculateRatio()` |

## CONVENTIONS

### Timeout Values (seconds)
| Module | Timeout | Fallback |
|--------|---------|----------|
| summarize | 30s | Rule-based extraction |
| extract_experience | 60s | Rule-based extraction |
| parse_time_llm | 10s | TimeReasoningEngine |
| expand_concepts_llm | 15s | Predefined mappings |
| compress | 60s | Concatenation + dedup |

### Fallback Pattern
All modules use `callJSONWithFallback()` with rule-based fallbacks:
```typescript
await client.callJSONWithFallback<ResponseType>(
  { task: prompt, timeoutSeconds: 30 },
  () => this.fallbackMethod()  // Always implemented
);
```

### Default Client
Import `defaultClient` for convenience:
```typescript
import { defaultClient } from './subagent-client.js';
const result = await defaultClient.callJSON<MyType>({ task: '...' });
```

## ANTI-PATTERNS

### Don't Retry on Timeout (CRITICAL)
`subagent-client.ts:240-243`
```typescript
// WRONG: Letting retry continue on timeout
// The code MUST break the loop on timeout
if (lastError.includes('timeout')) {
  break;  // REQUIRED: exit retry loop immediately
}
```

### Compression Ratio Always Positive
`smart-compressor.ts:163-164`
```typescript
// WRONG: Returning 0 or negative ratio
// Ratio must be >= 0.01
return Math.max(0.01, ratio);
```

### No Silent Failure on LLM Error
All modules return `LLMResult<T>` with `success: false` and error message. Never throw silently or return null.

## ENVIRONMENT

- `MEMORY_PALACE_TEST_MODE=true` - Use simulated LLM responses
- `MEMORY_PALACE_DISABLE_LLM=true` - Force fallback mode (no LLM calls)
- OpenClaw config loaded from `~/.openclaw/openclaw.json`