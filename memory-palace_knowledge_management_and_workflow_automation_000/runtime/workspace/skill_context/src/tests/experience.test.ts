/**
 * Experience Manager Tests
 */

import { describe, it, before, after } from 'node:test';
import assert from 'node:assert';
import * as fs from 'fs/promises';
import { MemoryPalaceManager } from '../manager.js';
import { ExperienceManager, createExperienceManager } from '../experience-manager.js';
import type { Memory } from '../types.js';

const TEST_DIR = '/tmp/memory-palace-experience-test-' + Date.now();

describe('ExperienceManager', () => {
  let manager: MemoryPalaceManager;
  let experienceManager: ExperienceManager;

  before(async () => {
    await fs.mkdir(TEST_DIR, { recursive: true });
    manager = new MemoryPalaceManager({ workspaceDir: TEST_DIR });
    experienceManager = createExperienceManager(manager);
  });

  after(async () => {
    await fs.rm(TEST_DIR, { recursive: true, force: true });
  });

  describe('recordExperience()', () => {
    it('should record an experience with default values', async () => {
      const memory = await experienceManager.recordExperience({
        content: '使用 TypeScript 的 as const 可以让类型推断更精确',
        applicability: '需要精确类型推断的场景',
        source: 'test-task-1',
      });

      assert.ok(memory.id, 'Experience should have an ID');
      assert.strictEqual(memory.type, 'experience');
      assert.strictEqual(memory.location, 'experiences');
      assert.ok(memory.tags.includes('experience'), 'Should have experience tag');
      assert.strictEqual(memory.importance, 0.7, 'Default importance should be 0.7');
      assert.ok(memory.experienceMeta, 'Should have experienceMeta');
      assert.strictEqual(memory.experienceMeta?.category, 'general');
      assert.strictEqual(memory.experienceMeta?.verified, false);
      assert.strictEqual(memory.experienceMeta?.verifiedCount, 0);
    });

    it('should record an experience with custom category and tags', async () => {
      const memory = await experienceManager.recordExperience({
        content: 'Docker 构建时使用 --no-cache 可以避免缓存问题',
        category: 'operations',
        applicability: 'Docker 构建出现缓存问题时',
        source: 'test-task-2',
        tags: ['docker', 'cache'],
        importance: 0.8,
      });

      assert.strictEqual(memory.type, 'experience');
      assert.strictEqual(memory.experienceMeta?.category, 'operations');
      assert.ok(memory.tags.includes('docker'));
      assert.ok(memory.tags.includes('cache'));
      assert.ok(memory.tags.includes('experience'));
      assert.strictEqual(memory.importance, 0.8);
    });

    it('should ensure unique tags', async () => {
      const memory = await experienceManager.recordExperience({
        content: 'Test experience with duplicate tags',
        applicability: 'test',
        source: 'test-task-3',
        tags: ['experience', 'experience', 'test'],
      });

      const experienceTagCount = memory.tags.filter(t => t === 'experience').length;
      assert.strictEqual(experienceTagCount, 1, 'Should not have duplicate experience tag');
    });
  });

  describe('getExperiences()', () => {
    it('should get all experiences', async () => {
      // Create some experiences first
      await experienceManager.recordExperience({
        content: 'Test experience for get all',
        category: 'development',
        applicability: 'TypeScript development',
        source: 'test',
      });
      
      const experiences = await experienceManager.getExperiences();
      assert.ok(experiences.length >= 1, 'Should have at least 1 experience');
      assert.ok(experiences.every(e => e.type === 'experience'));
    });

    it('should filter by category', async () => {
      // Create experiences with specific categories
      await experienceManager.recordExperience({
        content: 'Dev category experience',
        category: 'development',
        applicability: 'Development work',
        source: 'test-cat',
      });

      await experienceManager.recordExperience({
        content: 'Ops category experience',
        category: 'operations',
        applicability: 'Operations work',
        source: 'test-cat',
      });

      const devExperiences = await experienceManager.getExperiences({ 
        category: 'development' 
      });
      assert.ok(devExperiences.length > 0, 'Should have development experiences');
      assert.ok(devExperiences.every(e => e.experienceMeta?.category === 'development'));

      const opsExperiences = await experienceManager.getExperiences({ 
        category: 'operations' 
      });
      assert.ok(opsExperiences.length > 0, 'Should have operations experiences');
      assert.ok(opsExperiences.every(e => e.experienceMeta?.category === 'operations'));
    });

    it('should filter by applicability', async () => {
      // Create experience with specific applicability
      await experienceManager.recordExperience({
        content: 'Applicability test experience',
        category: 'development',
        applicability: 'Special applicability scenario',
        source: 'test-app',
      });

      const experiences = await experienceManager.getExperiences({
        applicability: 'Special',
      });
      assert.ok(experiences.length > 0, 'Should find experiences matching applicability');
    });

    it('should respect limit', async () => {
      // Create multiple experiences
      for (let i = 0; i < 5; i++) {
        await experienceManager.recordExperience({
          content: `Limit test experience ${i}`,
          category: 'general',
          applicability: 'Limit test',
          source: 'test-limit',
        });
      }

      const experiences = await experienceManager.getExperiences({ limit: 2 });
      assert.ok(experiences.length <= 2);
    });
  });

  describe('verifyExperience()', () => {
    it('should verify an experience as effective', async () => {
      const memory = await experienceManager.recordExperience({
        content: 'Test verification experience',
        applicability: 'test',
        source: 'verify-test',
      });

      // First verification
      const updated1 = await experienceManager.verifyExperience({
        id: memory.id,
        effective: true,
      });

      assert.ok(updated1, 'Should return updated memory');
      assert.strictEqual(updated1?.experienceMeta?.verifiedCount, 1);
      // Not verified yet (need 2 verifications)
      assert.strictEqual(updated1?.experienceMeta?.verified, false);

      // Second verification
      const updated2 = await experienceManager.verifyExperience({
        id: memory.id,
        effective: true,
      });

      assert.strictEqual(updated2?.experienceMeta?.verifiedCount, 2);
      assert.strictEqual(updated2?.experienceMeta?.verified, true);
      assert.ok(updated2?.experienceMeta?.lastVerifiedAt, 'Should have lastVerifiedAt');
    });

    it('should handle ineffective verification', async () => {
      const memory = await experienceManager.recordExperience({
        content: 'Ineffective experience test',
        applicability: 'test',
        source: 'verify-test-2',
        importance: 0.8,
      });

      const updated = await experienceManager.verifyExperience({
        id: memory.id,
        effective: false,
      });

      assert.ok(updated, 'Should return updated memory');
      assert.strictEqual(updated?.experienceMeta?.verified, false);
      // Importance should be reduced
      assert.ok(updated?.importance < 0.8, 'Importance should be reduced');
    });

    it('should return null for non-experience memory', async () => {
      const regularMemory = await manager.store({
        content: 'Not an experience',
      });

      const result = await experienceManager.verifyExperience({
        id: regularMemory.id,
        effective: true,
      });

      assert.strictEqual(result, null);
    });

    it('should return null for non-existent memory', async () => {
      const result = await experienceManager.verifyExperience({
        id: 'non-existent-id',
        effective: true,
      });

      assert.strictEqual(result, null);
    });
  });

  describe('getRelevantExperiences()', () => {
    it('should return relevant experiences for a context', async () => {
      // Create some experiences for relevance testing
      await experienceManager.recordExperience({
        content: 'TypeScript 类型优化技巧：使用 as const',
        category: 'development',
        applicability: 'TypeScript 类型定义',
        source: 'test-rel',
        tags: ['typescript', 'types'],
      });

      await experienceManager.recordExperience({
        content: 'Docker 多阶段构建减小镜像体积',
        category: 'operations',
        applicability: 'Docker 镜像优化',
        source: 'test-rel',
        tags: ['docker'],
      });

      const experiences = await experienceManager.getRelevantExperiences(
        '如何优化 TypeScript 类型定义',
        5
      );

      assert.ok(experiences.length > 0);
      assert.ok(experiences.some(e => 
        e.content.toLowerCase().includes('typescript') ||
        e.tags.includes('typescript')
      ));
    });

    it('should boost verified experiences', async () => {
      // Create and verify an experience
      const verified = await experienceManager.recordExperience({
        content: 'Verified TypeScript tip for boosting',
        applicability: 'TypeScript',
        source: 'test-boost',
      });

      await experienceManager.verifyExperience({ id: verified.id, effective: true });
      await experienceManager.verifyExperience({ id: verified.id, effective: true });

      const experiences = await experienceManager.getRelevantExperiences('TypeScript', 5);
      
      // Verified experience should rank higher
      const verifiedExp = experiences.find(e => e.id === verified.id);
      assert.ok(verifiedExp, 'Verified experience should be in results');
    });
  });

  describe('getExperienceStats()', () => {
    it('should return experience statistics', async () => {
      const stats = await experienceManager.getExperienceStats();

      assert.ok(typeof stats.total === 'number');
      assert.ok(typeof stats.verified === 'number');
      assert.ok(typeof stats.avgVerifiedCount === 'number');
      assert.ok(typeof stats.byCategory === 'object');
    });
  });
});

describe('Manager Experience Methods', () => {
  let manager: MemoryPalaceManager;

  before(async () => {
    await fs.mkdir(TEST_DIR + '-manager', { recursive: true });
    manager = new MemoryPalaceManager({ workspaceDir: TEST_DIR + '-manager' });
  });

  after(async () => {
    await fs.rm(TEST_DIR + '-manager', { recursive: true, force: true });
  });

  it('should record experience via manager', async () => {
    const memory = await manager.recordExperience({
      content: 'Manager test experience',
      applicability: 'test',
      source: 'manager-test',
    });

    assert.strictEqual(memory.type, 'experience');
    assert.strictEqual(memory.location, 'experiences');
  });

  it('should get experiences via manager', async () => {
    const experiences = await manager.getExperiences();
    assert.ok(Array.isArray(experiences));
  });

  it('should verify experience via manager', async () => {
    const memory = await manager.recordExperience({
      content: 'Manager verify test',
      applicability: 'test',
      source: 'manager-verify',
    });

    const updated = await manager.verifyExperience({
      id: memory.id,
      effective: true,
    });

    assert.strictEqual(updated?.experienceMeta?.verifiedCount, 1);
  });

  it('should get relevant experiences via manager', async () => {
    const experiences = await manager.getRelevantExperiences('test context');
    assert.ok(Array.isArray(experiences));
  });

  it('should get experience stats via manager', async () => {
    const stats = await manager.getExperienceStats();
    assert.ok(typeof stats.total === 'number');
  });
});

console.log('Experience Manager tests complete!');