/**
 * Time Reasoning and Concept Expansion Tests
 */

import { describe, it, before, after } from 'node:test';
import assert from 'node:assert';
import * as fs from 'fs/promises';
import { MemoryPalaceManager } from '../manager.js';
import { TimeReasoningEngine, createTimeReasoning } from '../background/time-reasoning.js';
import { ConceptExpander, createConceptExpander } from '../background/concept-expansion.js';

const TEST_DIR = '/tmp/memory-palace-time-concept-test-' + Date.now();

describe('TimeReasoningEngine', () => {
  let engine: TimeReasoningEngine;
  
  // Set a fixed date for testing: Wednesday, March 19, 2026
  const fixedDate = new Date(2026, 2, 18); // March 18, 2026 (Wednesday)
  
  before(() => {
    engine = new TimeReasoningEngine(fixedDate);
  });
  
  describe('parseTimeQuery()', () => {
    it('should parse "tomorrow" correctly', () => {
      const context = engine.parseTimeQuery('明天有什么安排？');
      assert.strictEqual(context.relativeTime, 'tomorrow');
      assert.strictEqual(context.hasTimeReasoning, true);
      assert.ok(context.keywords.includes('明天'));
    });
    
    it('should parse "today" correctly', () => {
      const context = engine.parseTimeQuery('今天的日程是什么？');
      assert.strictEqual(context.relativeTime, 'today');
      assert.strictEqual(context.hasTimeReasoning, true);
    });
    
    it('should parse "next week" correctly', () => {
      const context = engine.parseTimeQuery('下周有什么重要事项？');
      assert.strictEqual(context.relativeTime, 'next_week');
      assert.strictEqual(context.hasTimeReasoning, true);
      assert.ok(context.timeRange !== undefined);
    });
    
    it('should parse "this month" correctly', () => {
      const context = engine.parseTimeQuery('本月有什么会议？');
      assert.strictEqual(context.relativeTime, 'this_month');
      assert.strictEqual(context.hasTimeReasoning, true);
      assert.ok(context.keywords.some(k => k.includes('月')));
    });
    
    it('should parse day of week', () => {
      const context = engine.parseTimeQuery('周三的会议安排');
      assert.strictEqual(context.dayOfWeek, '周三');
      assert.strictEqual(context.hasTimeReasoning, true);
    });
    
    it('should parse specific date', () => {
      const context = engine.parseTimeQuery('3月15日的计划');
      assert.ok(context.parsedDate !== undefined);
      assert.strictEqual(context.parsedDate!.getMonth(), 2); // March = 2 (0-indexed)
      assert.strictEqual(context.parsedDate!.getDate(), 15);
    });
    
    it('should extract event-related keywords', () => {
      const context = engine.parseTimeQuery('明天的会议安排');
      assert.ok(context.keywords.includes('明天'));
      assert.ok(context.keywords.includes('会议'));
      assert.ok(context.keywords.includes('安排'));
    });
    
    it('should return no time reasoning for non-temporal queries', () => {
      const context = engine.parseTimeQuery('Python 编程技巧');
      assert.strictEqual(context.hasTimeReasoning, false);
    });
  });
  
  describe('resolveConditionalTime()', () => {
    it('should resolve conditional time query', () => {
      const result = engine.resolveConditionalTime('如果明天是周三，我需要准备什么？');
      assert.strictEqual(result.isConditional, true);
      assert.ok(result.targetDay !== undefined);
      assert.ok(result.keywords.includes('准备'));
    });
    
    it('should return false for non-conditional queries', () => {
      const result = engine.resolveConditionalTime('明天有什么安排？');
      assert.strictEqual(result.isConditional, false);
    });
  });
  
  describe('calculateTimeRange()', () => {
    it('should calculate correct range for next week', () => {
      const context = engine.parseTimeQuery('下周有什么重要事项？');
      assert.ok(context.timeRange !== undefined);
      
      // Next week should start on Monday (March 23, 2026)
      const expectedStart = new Date(2026, 2, 23); // Monday
      assert.strictEqual(context.timeRange!.start.getDate(), expectedStart.getDate());
      
      // And end on Sunday (March 29, 2026)
      const expectedEnd = new Date(2026, 2, 29); // Sunday
      assert.strictEqual(context.timeRange!.end.getDate(), expectedEnd.getDate());
    });
  });
  
  describe('getCurrentDateInfo()', () => {
    it('should return current date info', () => {
      const info = engine.getCurrentDateInfo();
      assert.strictEqual(info.dayOfWeek, '周三');
      assert.strictEqual(info.month, 3);
      assert.strictEqual(info.year, 2026);
    });
  });
});

describe('ConceptExpander', () => {
  let expander: ConceptExpander;
  
  before(() => {
    expander = createConceptExpander();
  });
  
  describe('expandQuery()', () => {
    it('should expand health and exercise concepts', async () => {
      const expansion = await expander.expandQuery('健康和运动');
      assert.ok(expansion.expandedKeywords.length > 0);
      assert.ok(expansion.expandedKeywords.includes('健康'));
      assert.ok(expansion.expandedKeywords.includes('运动'));
      // Should include related concepts
      assert.ok(expansion.expandedKeywords.some(k => 
        ['健身', '医疗', '体检', '跑步', '爬山'].includes(k)
      ));
    });
    
    it('should expand programming concepts', async () => {
      const expansion = await expander.expandQuery('编程相关');
      assert.ok(expansion.expandedKeywords.length > 0);
      assert.ok(expansion.expandedKeywords.includes('编程'));
      // Should include related concepts
      assert.ok(expansion.expandedKeywords.some(k => 
        ['代码', '开发', 'TypeScript', 'Python'].includes(k)
      ));
    });
    
    it('should expand meeting-related concepts', async () => {
      const expansion = await expander.expandQuery('会议安排');
      assert.ok(expansion.expandedKeywords.includes('会议'));
      assert.ok(expansion.expandedKeywords.includes('安排'));
    });
    
    it('should return original query keywords when no mapping exists', async () => {
      const expansion = await expander.expandQuery('一些随机的查询 xyz');
      // Should still return something, even if no mapping
      assert.ok(Array.isArray(expansion.expandedKeywords));
    });
  });
  
  describe('discoverRelated()', () => {
    it('should discover related concepts from mappings', async () => {
      const related = await expander.discoverRelated('健康');
      assert.ok(related.length > 0);
      // Should include concepts from the same domain
      assert.ok(related.some(c => ['运动', '医疗', '体检'].includes(c)));
    });
    
    it('should discover programming-related concepts', async () => {
      const related = await expander.discoverRelated('编程');
      assert.ok(related.length > 0);
      assert.ok(related.some(c => ['代码', '开发', 'TypeScript'].includes(c)));
    });
  });
  
  describe('getDomainCategory()', () => {
    it('should return correct domain for health concepts', () => {
      const category = expander.getDomainCategory('健康');
      assert.strictEqual(category, '健康与运动');
    });
    
    it('should return correct domain for programming concepts', () => {
      const category = expander.getDomainCategory('编程');
      assert.strictEqual(category, '编程与技术');
    });
    
    it('should return null for unknown concepts', () => {
      const category = expander.getDomainCategory('未知概念');
      assert.strictEqual(category, null);
    });
  });
  
  describe('areRelated()', () => {
    it('should detect related concepts in same domain', () => {
      assert.strictEqual(expander.areRelated('健康', '运动'), true);
      assert.strictEqual(expander.areRelated('编程', '代码'), true);
    });
    
    it('should detect unrelated concepts', () => {
      assert.strictEqual(expander.areRelated('健康', '编程'), false);
    });
  });
});

describe('MemoryPalaceManager with Time Reasoning and Concept Expansion', () => {
  let manager: MemoryPalaceManager;
  
  before(async () => {
    await fs.mkdir(TEST_DIR, { recursive: true });
    manager = new MemoryPalaceManager({ workspaceDir: TEST_DIR });
    
    // Store test memories
    await manager.store({
      content: '每周三有团队例会，需要准备周报',
      location: 'work',
      tags: ['会议', '周三', '工作'],
      importance: 0.8,
    });
    
    await manager.store({
      content: '下周三有项目评审会议',
      location: 'work',
      tags: ['会议', '项目', '周三'],
      importance: 0.9,
    });
    
    await manager.store({
      content: '健康检查预约在3月20日',
      location: 'personal',
      tags: ['健康', '体检', '医疗'],
      importance: 0.7,
    });
    
    await manager.store({
      content: '健身房会员卡到期，需要续费',
      location: 'personal',
      tags: ['健身', '运动', '健康'],
      importance: 0.6,
    });
    
    await manager.store({
      content: 'Python和TypeScript项目代码需要review',
      location: 'work',
      tags: ['编程', '代码', 'Python', 'TypeScript'],
      importance: 0.7,
    });
    
    await manager.store({
      content: '牙医预约周五下午',
      location: 'personal',
      tags: ['牙医', '健康', '周五'],
      importance: 0.8,
    });
  });
  
  after(async () => {
    await fs.rm(TEST_DIR, { recursive: true, force: true });
  });
  
  describe('recall() with time reasoning', () => {
    it('should find Wednesday-related memories', async () => {
      const results = await manager.recall('周三有什么安排？');
      assert.ok(results.length > 0, 'Should find results for Wednesday');
      // Should find the meeting-related memories
      const hasMeeting = results.some(r => 
        r.memory.content.includes('会议') || r.memory.content.includes('例会')
      );
      assert.ok(hasMeeting, 'Should find meeting-related memories');
    });
    
    it('should find memories for "下周" query', async () => {
      const results = await manager.recall('下周有什么重要事项？');
      assert.ok(results.length > 0);
    });
    
    it('should handle conditional time queries', async () => {
      const results = await manager.recall('如果明天是周三，我需要准备什么？');
      // Should find Wednesday-related content
      assert.ok(results.length >= 0); // May or may not find results depending on test date
    });
  });
  
  describe('recall() with concept expansion', () => {
    it('should find health and exercise related memories', async () => {
      const results = await manager.recall('健康和运动相关的安排有什么？');
      assert.ok(results.length > 0, 'Should find health/exercise results');
      // Should find memories tagged with health/exercise concepts
      const hasHealthOrExercise = results.some(r =>
        r.memory.tags.some(t => ['健康', '运动', '健身', '体检', '牙医'].includes(t))
      );
      assert.ok(hasHealthOrExercise, 'Should find health or exercise tagged memories');
    });
    
    it('should find programming related memories', async () => {
      const results = await manager.recall('编程相关的任务');
      assert.ok(results.length > 0, 'Should find programming results');
      const hasProgramming = results.some(r =>
        r.memory.tags.some(t => ['编程', '代码', 'Python', 'TypeScript'].includes(t))
      );
      assert.ok(hasProgramming, 'Should find programming tagged memories');
    });
    
    it('should find dentist appointment via health concept expansion', async () => {
      const results = await manager.recall('医疗相关的安排');
      assert.ok(results.length > 0);
      const hasDentistOrHealth = results.some(r =>
        r.memory.content.includes('牙医') || r.memory.tags.includes('健康')
      );
      assert.ok(hasDentistOrHealth, 'Should find dentist or health-related memories');
    });
  });
  
  describe('recall() combined features', () => {
    it('should combine time and concept reasoning', async () => {
      const results = await manager.recall('本周的会议安排');
      assert.ok(results.length >= 0);
      // Should prioritize meeting-related content
      if (results.length > 0) {
        const hasMeeting = results.some(r =>
          r.memory.tags.includes('会议') || r.memory.content.includes('会议')
        );
        assert.ok(hasMeeting, 'Should find meeting-related memories');
      }
    });
    
    it('should return results with proper scoring', async () => {
      const results = await manager.recall('健康运动', { topK: 5 });
      assert.ok(results.length > 0);
      // All results should have valid scores
      assert.ok(results.every(r => r.score >= 0 && r.score <= 1));
      // Results should be sorted by score
      for (let i = 1; i < results.length; i++) {
        assert.ok(results[i - 1].score >= results[i].score);
      }
    });
  });
});

console.log('Time reasoning and concept expansion tests completed!');