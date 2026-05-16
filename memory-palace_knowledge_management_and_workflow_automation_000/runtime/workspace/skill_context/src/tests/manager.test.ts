/**
 * Memory Palace Manager Tests
 */

import { describe, it, before, after } from 'node:test';
import assert from 'node:assert';
import * as fs from 'fs/promises';
import * as path from 'path';
import { MemoryPalaceManager } from '../manager.js';
import type { Memory } from '../types.js';

const TEST_DIR = '/tmp/memory-palace-test-' + Date.now();

describe('MemoryPalaceManager', () => {
  let manager: MemoryPalaceManager;

  before(async () => {
    await fs.mkdir(TEST_DIR, { recursive: true });
    manager = new MemoryPalaceManager({ workspaceDir: TEST_DIR });
  });

  after(async () => {
    await fs.rm(TEST_DIR, { recursive: true, force: true });
  });

  describe('store()', () => {
    it('should store a memory with default values', async () => {
      const memory = await manager.store({
        content: 'Test memory content',
      });

      assert.ok(memory.id, 'Memory should have an ID');
      assert.strictEqual(memory.content, 'Test memory content');
      assert.strictEqual(memory.status, 'active');
      assert.strictEqual(memory.location, 'default');
      assert.deepStrictEqual(memory.tags, []);
      assert.strictEqual(memory.importance, 0.5);
      assert.strictEqual(memory.source, 'user');
    });

    it('should store a memory with custom values', async () => {
      const memory = await manager.store({
        content: 'Custom memory',
        location: 'projects',
        tags: ['important', 'work'],
        importance: 0.9,
        source: 'conversation',
        summary: 'A custom memory entry',
      });

      assert.strictEqual(memory.location, 'projects');
      assert.deepStrictEqual(memory.tags, ['important', 'work']);
      assert.strictEqual(memory.importance, 0.9);
      assert.strictEqual(memory.source, 'conversation');
      assert.strictEqual(memory.summary, 'A custom memory entry');
    });
  });

  describe('get()', () => {
    it('should retrieve a stored memory', async () => {
      const stored = await manager.store({
        content: 'Memory to retrieve',
        tags: ['test'],
      });

      const retrieved = await manager.get(stored.id);

      assert.ok(retrieved, 'Memory should be found');
      assert.strictEqual(retrieved.id, stored.id);
      assert.strictEqual(retrieved.content, 'Memory to retrieve');
      assert.deepStrictEqual(retrieved.tags, ['test']);
    });

    it('should return null for non-existent memory', async () => {
      const retrieved = await manager.get('non-existent-id');
      assert.strictEqual(retrieved, null);
    });
  });

  describe('update()', () => {
    it('should update memory content', async () => {
      const stored = await manager.store({
        content: 'Original content',
      });

      const updated = await manager.update({
        id: stored.id,
        content: 'Updated content',
      });

      assert.ok(updated, 'Memory should be updated');
      assert.strictEqual(updated.content, 'Updated content');
    });

    it('should update tags', async () => {
      const stored = await manager.store({
        content: 'Tag test',
        tags: ['a', 'b'],
      });

      const updated = await manager.update({
        id: stored.id,
        tags: ['c', 'd'],
      });

      assert.ok(updated, 'Memory should be updated');
      assert.deepStrictEqual(updated.tags, ['c', 'd']);
    });

    it('should append tags', async () => {
      const stored = await manager.store({
        content: 'Tag append test',
        tags: ['a'],
      });

      const updated = await manager.update({
        id: stored.id,
        tags: ['b'],
        appendTags: true,
      });

      assert.ok(updated, 'Memory should be updated');
      assert.deepStrictEqual(updated.tags.sort(), ['a', 'b']);
    });

    it('should return null for non-existent memory', async () => {
      const updated = await manager.update({
        id: 'non-existent',
        content: 'Updated',
      });

      assert.strictEqual(updated, null);
    });
  });

  describe('delete()', () => {
    it('should soft delete a memory', async () => {
      const stored = await manager.store({
        content: 'To be deleted',
      });

      await manager.delete(stored.id);

      // Should not be found in normal list
      const memories = await manager.list({ status: 'active' });
      assert.ok(!memories.find(m => m.id === stored.id));

      // Should be in trash
      const trash = await manager.listTrash();
      assert.ok(trash.find(m => m.id === stored.id));
    });

    it('should permanently delete a memory', async () => {
      const stored = await manager.store({
        content: 'To be permanently deleted',
      });

      await manager.delete(stored.id, true);

      // Should not be in trash
      const trash = await manager.listTrash();
      assert.ok(!trash.find(m => m.id === stored.id));
    });
  });

  describe('restore()', () => {
    it('should restore a deleted memory', async () => {
      const stored = await manager.store({
        content: 'To be restored',
      });

      await manager.delete(stored.id);

      const restored = await manager.restore(stored.id);

      assert.ok(restored, 'Memory should be restored');
      assert.strictEqual(restored.status, 'active');

      // Should be in active list
      const memories = await manager.list({ status: 'active' });
      assert.ok(memories.find(m => m.id === stored.id));
    });
  });

  describe('list()', () => {
    before(async () => {
      // Clear and create test data
      const existing = await manager.list({ limit: 1000 });
      for (const m of existing) {
        await manager.delete(m.id, true);
      }
      await manager.emptyTrash();

      // Create test memories
      await manager.store({ content: 'List test 1', location: 'loc1', tags: ['tag1'], importance: 0.8 });
      await manager.store({ content: 'List test 2', location: 'loc1', tags: ['tag1', 'tag2'], importance: 0.6 });
      await manager.store({ content: 'List test 3', location: 'loc2', tags: ['tag2'], importance: 0.4 });
    });

    it('should list all memories', async () => {
      const memories = await manager.list();
      assert.ok(memories.length >= 3, 'Should have at least 3 memories');
    });

    it('should filter by location', async () => {
      const memories = await manager.list({ location: 'loc1' });
      assert.strictEqual(memories.length, 2);
    });

    it('should filter by tags', async () => {
      const memories = await manager.list({ tags: ['tag1'] });
      assert.strictEqual(memories.length, 2);

      const memories2 = await manager.list({ tags: ['tag2'] });
      assert.strictEqual(memories2.length, 2);

      const memories3 = await manager.list({ tags: ['tag1', 'tag2'] });
      assert.strictEqual(memories3.length, 1);
    });

    it('should sort by importance', async () => {
      const memories = await manager.list({ sortBy: 'importance', sortOrder: 'desc' });
      assert.ok(memories[0].importance >= memories[memories.length - 1].importance);
    });

    it('should paginate', async () => {
      const page1 = await manager.list({ limit: 2 });
      const page2 = await manager.list({ limit: 2, offset: 2 });

      assert.strictEqual(page1.length, 2);
      assert.ok(page2.length <= 2);

      // No overlap
      const ids1 = new Set(page1.map(m => m.id));
      const ids2 = new Set(page2.map(m => m.id));
      for (const id of ids2) {
        assert.ok(!ids1.has(id), 'Pages should not overlap');
      }
    });
  });

  describe('recall()', () => {
    before(async () => {
      // Clear and create searchable test data
      const existing = await manager.list({ limit: 1000 });
      for (const m of existing) {
        await manager.delete(m.id, true);
      }
      await manager.emptyTrash();

      await manager.store({
        content: 'The quick brown fox jumps over the lazy dog',
        tags: ['animals', 'test'],
        importance: 0.8,
      });
      await manager.store({
        content: 'Python is a great programming language for AI',
        tags: ['tech', 'python'],
        importance: 0.7,
      });
      await manager.store({
        content: 'TypeScript adds type safety to JavaScript',
        tags: ['tech', 'typescript'],
        importance: 0.6,
      });
    });

    it('should find memories by keyword', async () => {
      const results = await manager.recall('python');
      assert.ok(results.length > 0, 'Should find results');
      assert.ok(results[0].memory.content.toLowerCase().includes('python'));
    });

    it('should return results with scores', async () => {
      const results = await manager.recall('programming');
      assert.ok(results.length > 0);
      assert.ok(results[0].score >= 0, 'Should have a score');
    });

    it('should filter by tags', async () => {
      const results = await manager.recall('test', { tags: ['animals'] });
      assert.ok(results.length > 0);
      assert.ok(results.every(r => r.memory.tags.includes('animals')));
    });

    it('should respect topK limit', async () => {
      const results = await manager.recall('test', { topK: 1 });
      assert.ok(results.length <= 1);
    });
  });

  describe('stats()', () => {
    it('should return statistics', async () => {
      const stats = await manager.stats();

      assert.ok(typeof stats.total === 'number');
      assert.ok(typeof stats.active === 'number');
      assert.ok(typeof stats.archived === 'number');
      assert.ok(typeof stats.deleted === 'number');
      assert.ok(typeof stats.avgImportance === 'number');
      assert.ok(typeof stats.byLocation === 'object');
      assert.ok(typeof stats.byTag === 'object');
      assert.ok(stats.storagePath.includes('memory/palace'));
    });
  });

  describe('batch operations', () => {
    it('should store multiple memories', async () => {
      const memories = await manager.storeBatch([
        { content: 'Batch 1' },
        { content: 'Batch 2' },
        { content: 'Batch 3' },
      ]);

      assert.strictEqual(memories.length, 3);
      assert.ok(memories.every(m => m.id));
    });

    it('should get multiple memories', async () => {
      const stored = await manager.storeBatch([
        { content: 'Get batch 1' },
        { content: 'Get batch 2' },
      ]);

      const retrieved = await manager.getBatch(stored.map(m => m.id));

      assert.strictEqual(retrieved.length, 2);
      assert.ok(retrieved.every(m => m !== null));
    });
  });
});

describe('File Storage', () => {
  it('should persist and load memories', async () => {
    const testDir = '/tmp/memory-palace-storage-test';
    await fs.mkdir(testDir, { recursive: true });

    const mgr = new MemoryPalaceManager({ workspaceDir: testDir });

    const stored = await mgr.store({
      content: 'Persistent memory',
      tags: ['test'],
      importance: 0.75,
    });

    // Create new manager to test persistence
    const mgr2 = new MemoryPalaceManager({ workspaceDir: testDir });
    const loaded = await mgr2.get(stored.id);

    assert.ok(loaded, 'Memory should persist');
    assert.strictEqual(loaded.content, 'Persistent memory');
    assert.deepStrictEqual(loaded.tags, ['test']);
    assert.strictEqual(loaded.importance, 0.75);

    await fs.rm(testDir, { recursive: true, force: true });
  });
});

console.log('All tests passed!');