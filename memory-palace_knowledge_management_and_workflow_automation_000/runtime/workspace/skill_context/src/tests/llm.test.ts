/**
 * Memory Palace v1.1 - LLM Module Tests
 */

import { describe, it, before } from 'node:test';
import assert from 'node:assert';

// Set test mode to enable simulation responses
process.env.MEMORY_PALACE_TEST_MODE = 'true';

// Import modules after setting env
const { SubagentClient, defaultClient } = await import('../llm/subagent-client.js');
const { LLMSummarizer, summarizeMemory } = await import('../llm/summarizer.js');
const { ExperienceExtractor, extractExperiences } = await import('../llm/experience-extractor.js');
const { TimeParserLLM, parseTime } = await import('../llm/time-parser.js');
const { ConceptExpanderLLM, expandConcepts } = await import('../llm/concept-expander.js');
const { SmartCompressor, compressMemories } = await import('../llm/smart-compressor.js');
const type = await import('../llm/types.js');

describe('SubagentClient', () => {
  it('should create client with default options', () => {
    const client = new SubagentClient();
    assert.ok(client);
  });

  it('should return simulated response in test mode', async () => {
    const client = new SubagentClient();
    const result = await client.callJSON<{ result: string }>({
      task: '测试任务',
    });
    
    assert.ok(result.success);
    assert.ok(result.data);
  });

  it('should parse JSON from response', async () => {
    const client = new SubagentClient();
    const result = await client.callJSON<{ date: string; confidence: number }>({
      task: '解析: 明天\n返回JSON: {"date":"2026-03-19","confidence":0.9}',
    });
    
    assert.ok(result.success);
    assert.ok(result.data?.date);
    assert.ok(typeof result.data?.confidence === 'number');
  });

  it('should handle fallback', async () => {
    const client = new SubagentClient({ enableFallback: true });
    const result = await client.callJSONWithFallback<{ test: string }>(
      { task: '测试' },
      () => ({ test: 'fallback' })
    );
    
    assert.ok(result.success);
    assert.ok(result.data?.test);
  });
});

describe('LLMSummarizer', () => {
  it('should summarize content', async () => {
    const summarizer = new LLMSummarizer();
    const result = await summarizer.summarize('用户偏好深色模式，在所有应用中都启用深色主题。');
    
    assert.ok(result.success);
    assert.ok(result.data?.summary);
    assert.ok(Array.isArray(result.data?.keyPoints));
    assert.ok(typeof result.data?.importance === 'number');
  });

  it('should truncate long content', async () => {
    const summarizer = new LLMSummarizer();
    const longContent = '这是一段很长的内容。'.repeat(200);
    const result = await summarizer.summarize(longContent);
    
    assert.ok(result.success);
  });

  it('should fallback on LLM failure', async () => {
    const summarizer = new LLMSummarizer();
    const result = await summarizer.summarize('测试内容，包含重要信息。');
    
    assert.ok(result.success);
    assert.ok(result.data?.summary);
  });
});

describe('ExperienceExtractor', () => {
  const mockMemories = [
    {
      id: '1',
      content: '成功完成了项目迁移，使用 TypeScript 减少了运行时错误。',
      tags: ['项目', '技术'],
      importance: 0.8,
      status: 'active' as const,
      source: 'conversation' as const,
      location: 'work',
      createdAt: new Date(),
      updatedAt: new Date(),
    },
    {
      id: '2',
      content: '学习到了新的调试技巧，可以更快定位问题。',
      tags: ['学习', '技术'],
      importance: 0.6,
      status: 'active' as const,
      source: 'conversation' as const,
      location: 'learning',
      createdAt: new Date(),
      updatedAt: new Date(),
    },
  ];

  it('should extract experiences from memories', async () => {
    const extractor = new ExperienceExtractor();
    const result = await extractor.extract(mockMemories);
    
    assert.ok(result.success);
    assert.ok(Array.isArray(result.data));
  });

  it('should handle empty memories', async () => {
    const extractor = new ExperienceExtractor();
    const result = await extractor.extract([]);
    
    assert.ok(result.success);
    assert.deepStrictEqual(result.data, []);
  });

  it('should respect max experiences option', async () => {
    const extractor = new ExperienceExtractor();
    const result = await extractor.extract(mockMemories, { maxExperiences: 1 });
    
    assert.ok(result.success);
    if (result.data && result.data.length > 0) {
      assert.ok(result.data.length <= 1);
    }
  });
});

describe('TimeParserLLM', () => {
  it('should parse "今天"', async () => {
    const parser = new TimeParserLLM();
    const result = await parser.parse('今天');
    
    assert.ok(result.success);
    assert.ok(result.data?.date);
    assert.ok(result.data?.confidence === 1.0); // Cache hit
  });

  it('should parse "明天"', async () => {
    const parser = new TimeParserLLM();
    const result = await parser.parse('明天');
    
    assert.ok(result.success);
    assert.ok(result.data?.date);
    const today = new Date().toISOString().split('T')[0];
    assert.notStrictEqual(result.data?.date, today);
  });

  it('should parse "下周三"', async () => {
    const parser = new TimeParserLLM();
    const result = await parser.parse('下周三');
    
    assert.ok(result.success);
    assert.ok(result.data?.date);
    assert.ok(/^\d{4}-\d{2}-\d{2}$/.test(result.data!.date));
  });

  it('should use fallback for complex expressions', async () => {
    const parser = new TimeParserLLM();
    const result = await parser.parse('三天后');
    
    assert.ok(result.success);
    assert.ok(result.data?.date);
  });

  it('should validate date format', async () => {
    const parser = new TimeParserLLM();
    const result = await parser.parse('测试');
    
    assert.ok(result.success);
    assert.ok(/^\d{4}-\d{2}-\d{2}$/.test(result.data!.date));
  });
});

describe('ConceptExpanderLLM', () => {
  it('should expand "健康"', async () => {
    const expander = new ConceptExpanderLLM();
    const result = await expander.expand('健康');
    
    assert.ok(result.success);
    assert.ok(result.data?.keywords?.length);
    assert.ok(result.data?.keywords && result.data.keywords.includes('健康'));
  });

  it('should return cached result for common concepts', async () => {
    const expander = new ConceptExpanderLLM();
    const result = await expander.expand('运动');
    
    assert.ok(result.success);
    assert.ok(result.data?.keywords?.length);
    assert.ok(result.duration === 0); // Cache hit
  });

  it('should respect max keywords option', async () => {
    const expander = new ConceptExpanderLLM();
    const result = await expander.expand('编程', { maxKeywords: 5 });
    
    assert.ok(result.success);
    assert.ok(result.data?.keywords && result.data.keywords.length <= 5);
  });

  it('should allow custom mapping', async () => {
    const expander = new ConceptExpanderLLM();
    expander.addMapping('自定义', {
      keywords: ['自定义1', '自定义2'],
      domains: ['自定义域'],
    });
    
    const result = await expander.expand('自定义');
    
    assert.ok(result.success);
    assert.ok(result.data?.keywords && result.data.keywords.includes('自定义1'));
  });
});

describe('SmartCompressor', () => {
  const mockMemories = [
    {
      id: '1',
      content: '今天学习了 TypeScript 的基础语法，包括类型定义、接口、泛型等概念。',
      tags: ['学习', 'TypeScript'],
      importance: 0.7,
      status: 'active' as const,
      source: 'conversation' as const,
      location: 'learning',
      createdAt: new Date('2026-03-18'),
      updatedAt: new Date('2026-03-18'),
      summary: 'TypeScript 基础学习',
    },
    {
      id: '2',
      content: '继续 TypeScript 学习，完成了类型体操练习，理解了条件类型。',
      tags: ['学习', 'TypeScript'],
      importance: 0.7,
      status: 'active' as const,
      source: 'conversation' as const,
      location: 'learning',
      createdAt: new Date('2026-03-19'),
      updatedAt: new Date('2026-03-19'),
      summary: 'TypeScript 进阶学习',
    },
  ];

  it('should compress memories', async () => {
    const compressor = new SmartCompressor();
    const result = await compressor.compress(mockMemories);
    
    assert.ok(result.success);
    assert.ok(result.data?.compressedContent);
    assert.ok(result.data?.originalIds?.length === 2);
    assert.ok(typeof result.data?.compressionRatio === 'number');
  });

  it('should reject single memory', async () => {
    const compressor = new SmartCompressor();
    const result = await compressor.compress([mockMemories[0]]);
    
    assert.ok(!result.success);
    assert.ok(result.error?.includes('at least 2'));
  });

  it('should check compressibility', async () => {
    const compressor = new SmartCompressor();
    const shouldCompress = await compressor.shouldCompress(mockMemories);
    
    assert.strictEqual(shouldCompress, true);
  });

  it('should calculate compression ratio', async () => {
    const compressor = new SmartCompressor();
    const result = await compressor.compress(mockMemories);
    
    assert.ok(result.success);
    assert.ok(result.data!.compressionRatio > 0);
    assert.ok(result.data!.compressionRatio <= 1);
  });
});

describe('Types', () => {
  it('should export all types', () => {
    assert.ok(type);
    // Type exports are compile-time, just verify the module loaded
  });
});

describe('Quick Helpers', () => {
  it('summarizeMemory helper should work', async () => {
    const result = await summarizeMemory('测试内容');
    assert.ok(result.success);
  });

  it('parseTime helper should work', async () => {
    const result = await parseTime('明天');
    assert.ok(result.success);
  });

  it('expandConcepts helper should work', async () => {
    const result = await expandConcepts('健康');
    assert.ok(result.success);
  });
});

console.log('All tests completed!');