# A/B Testing Framework

Validates memory search accuracy with 50 test memories and 20 queries across difficulty levels.

## STRUCTURE

| File | Role |
|------|------|
| `run-test.ts` | Main ABTestRunner class - stores memories, runs queries, calculates hit rate/precision/recall |
| `test-data.ts` | 50 test memories (preference, work, schedule, person, project, knowledge, habit, goal) |
| `test-queries.ts` | 20 test queries (7 easy, 8 medium, 5 hard) with expected memory IDs and keywords |
| `final-test.ts` | Comprehensive validation with detailed reporting |
| `report.ts` | Generate test result reports |
| `verify-hits.ts` | Debug failed queries with detailed analysis |
| `test-time-reasoning.ts` | Time reasoning engine validation |
| `debug-wednesday.ts` | Time-sensitive test case |

## HOW TO RUN

```bash
# Build first
npm run build

# Run with mock client (dry run)
node dist/scripts/ab-test/run-test.js

# Run full test against MemoryPalaceManager
node dist/scripts/ab-test/final-test.js

# Debug specific queries
node dist/scripts/ab-test/verify-hits.js

# Test time reasoning engine
node dist/scripts/ab-test/test-time-reasoning.js
```

## HOW TO ADD TESTS

### Add Memory (test-data.ts)
```typescript
{
  id: 'mem-XXX',
  content: 'Memory content here',
  category: 'preference' | 'work' | 'schedule' | 'person' | 'project' | 'knowledge' | 'habit' | 'goal',
  tags: ['tag1', 'tag2'],
  importance: 'high' | 'medium' | 'low',
  createdAt: '2026-03-01T10:00:00Z'
}
```

### Add Query (test-queries.ts)
```typescript
{
  id: 'query-XXX',
  query: 'Query string to test',
  expectedKeywords: ['keyword1', 'keyword2'],
  difficulty: 'easy' | 'medium' | 'hard',
  expectedMemoryIds: ['mem-001', 'mem-002'],
  description: 'What this query tests'
}
```

### Difficulty Guidelines
- **Easy**: Direct keyword match, single memory
- **Medium**: Semantic understanding, 2-3 memories
- **Hard**: Inference, time reasoning, multi-hop

## METRICS

- **Hit Rate**: % queries returning at least one expected memory
- **Precision@K**: % relevant in top K results
- **Recall@K**: % expected memories found in top K
- **By Difficulty**: Easy/medium/hard breakdown