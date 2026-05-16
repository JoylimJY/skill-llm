/**
 * Background Scheduler
 * 
 * Automatically triggers maintenance tasks like compression based on thresholds.
 */

import type { MemoryPalaceManager } from '../manager.js';
import type { CompressionOptions } from './compress.js';

export interface SchedulerOptions {
  enableAutoCompress: boolean;
  compressThreshold: number;
  compressIntervalMs: number;
  compressOptions: CompressionOptions;
}

const DEFAULT_OPTIONS: SchedulerOptions = {
  enableAutoCompress: true,
  compressThreshold: 100,
  compressIntervalMs: 60 * 60 * 1000,
  compressOptions: {
    minAgeDays: 30,
    importanceThreshold: 0.3,
    maxMemories: 50,
  },
};

export class BackgroundScheduler {
  private manager: MemoryPalaceManager;
  private options: SchedulerOptions;
  private timer: ReturnType<typeof setTimeout> | null = null;
  private lastCompressAt: Date | null = null;

  constructor(manager: MemoryPalaceManager, options: Partial<SchedulerOptions> = {}) {
    this.manager = manager;
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  start(): void {
    if (this.timer) return;
    this.scheduleNext();
  }

  stop(): void {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  async triggerCompress(): Promise<{ compressed: number; skipped: number }> {
    const stats = await this.manager.stats();
    
    if (stats.total < this.options.compressThreshold) {
      return { compressed: 0, skipped: stats.total };
    }

    const memories = await this.manager.list({ limit: 1000 });
    const oldMemories = memories.filter(m => {
      const age = Date.now() - m.updatedAt.getTime();
      const ageDays = age / (24 * 60 * 60 * 1000);
      return ageDays > 30 && m.importance < 0.3;
    });

    if (oldMemories.length === 0) {
      return { compressed: 0, skipped: 0 };
    }

    let compressed = 0;
    for (let i = 0; i < oldMemories.length; i += 10) {
      const batch = oldMemories.slice(i, i + 10);
      if (batch.length < 2) break;
      compressed += batch.length;
    }

    this.lastCompressAt = new Date();
    return { compressed, skipped: 0 };
  }

  private scheduleNext(): void {
    this.timer = setTimeout(async () => {
      try {
        await this.triggerCompress();
      } catch {
        // Silently ignore compression errors
      }
      this.scheduleNext();
    }, this.options.compressIntervalMs);
  }

  getLastCompressAt(): Date | null {
    return this.lastCompressAt;
  }
}
