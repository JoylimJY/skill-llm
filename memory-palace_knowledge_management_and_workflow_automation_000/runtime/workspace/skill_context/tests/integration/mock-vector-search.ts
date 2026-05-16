/**
 * Mock Vector Search Provider
 * 
 * A mock implementation for testing the VectorSearchProvider integration.
 * Simulates vector search behavior without requiring actual embeddings.
 */

import type { VectorSearchProvider, VectorSearchResult } from '../../src/types.js';

/**
 * Simple in-memory mock for vector search
 */
export class MockVectorSearchProvider implements VectorSearchProvider {
  private indexMap: Map<string, { content: string; metadata: Record<string, unknown> }> = new Map();
  
  /**
   * Search for similar content using simple text matching
   * In real implementation, this would use vector similarity
   */
  async search(
    query: string, 
    topK: number, 
    filter?: Record<string, unknown>
  ): Promise<VectorSearchResult[]> {
    const results: VectorSearchResult[] = [];
    const queryLower = query.toLowerCase();
    const queryTerms = queryLower.split(/\s+/).filter(t => t.length > 1);
    
    for (const [id, data] of this.indexMap) {
      // Apply filters
      if (filter) {
        if (filter.location && data.metadata.location !== filter.location) {
          continue;
        }
        if (filter.tags && Array.isArray(filter.tags)) {
          const hasAllTags = (filter.tags as string[]).every(
            tag => (data.metadata.tags as string[]).includes(tag)
          );
          if (!hasAllTags) continue;
        }
      }
      
      // Simple text similarity scoring (mock for vector similarity)
      const contentLower = data.content.toLowerCase();
      let score = 0;
      
      for (const term of queryTerms) {
        if (contentLower.includes(term)) {
          score += 0.3;
        }
      }
      
      // Boost by importance if present
      if (typeof data.metadata.importance === 'number') {
        score *= (0.5 + data.metadata.importance * 0.5);
      }
      
      if (score > 0) {
        results.push({
          id,
          score: Math.min(1, score),
          metadata: data.metadata,
        });
      }
    }
    
    // Sort by score and return top K
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, topK);
  }
  
  /**
   * Index a document
   */
  async index(
    id: string, 
    content: string, 
    metadata?: Record<string, unknown>
  ): Promise<void> {
    this.indexMap.set(id, {
      content,
      metadata: metadata || {},
    });
  }
  
  /**
   * Remove from index
   */
  async remove(id: string): Promise<void> {
    this.indexMap.delete(id);
  }
  
  /**
   * Get indexed document count (for testing)
   */
  getIndexSize(): number {
    return this.indexMap.size;
  }
  
  /**
   * Clear all indexed documents
   */
  async clear(): Promise<void> {
    this.indexMap.clear();
  }
}

/**
 * OpenClaw-style MemoryIndexManager wrapper
 * 
 * This wraps the OpenClaw MemoryIndexManager to implement VectorSearchProvider.
 * In production, OpenClaw automatically indexes memory/*.md files.
 */
export class OpenClawVectorSearchProvider implements VectorSearchProvider {
  private indexMap: Map<string, { content: string; metadata: Record<string, unknown> }> = new Map();
  private searchBehavior: 'vector' | 'text' | 'hybrid' = 'hybrid';
  
  /**
   * Create provider with configurable search behavior
   */
  constructor(options?: { 
    searchBehavior?: 'vector' | 'text' | 'hybrid';
  }) {
    if (options?.searchBehavior) {
      this.searchBehavior = options.searchBehavior;
    }
  }
  
  /**
   * Simulate OpenClaw's search method
   * Returns results similar to MemoryIndexManager.search()
   */
  async search(
    query: string, 
    topK: number, 
    filter?: Record<string, unknown>
  ): Promise<VectorSearchResult[]> {
    // In FTS-only mode (no vector), behave like text search
    if (this.searchBehavior === 'text') {
      return this.textSearch(query, topK, filter);
    }
    
    // In vector-only mode, simulate vector similarity
    if (this.searchBehavior === 'vector') {
      return this.vectorSearch(query, topK, filter);
    }
    
    // Hybrid: combine both (like OpenClaw's default behavior)
    const textResults = await this.textSearch(query, Math.ceil(topK * 1.5), filter);
    const vectorResults = await this.vectorSearch(query, Math.ceil(topK * 1.5), filter);
    
    return this.mergeResults(textResults, vectorResults, topK);
  }
  
  /**
   * Text-based search (simulates OpenClaw's FTS)
   */
  private async textSearch(
    query: string, 
    topK: number, 
    filter?: Record<string, unknown>
  ): Promise<VectorSearchResult[]> {
    const results: VectorSearchResult[] = [];
    const queryTerms = query.toLowerCase().split(/\s+/).filter(t => t.length > 1);
    
    for (const [id, data] of this.indexMap) {
      if (!this.matchesFilter(data.metadata, filter)) continue;
      
      const contentLower = data.content.toLowerCase();
      let score = 0;
      
      for (const term of queryTerms) {
        const count = (contentLower.match(new RegExp(term, 'g')) || []).length;
        score += count * 0.1;
      }
      
      if (score > 0) {
        results.push({
          id,
          score: Math.min(0.5, score), // Text matches capped at 0.5
          metadata: data.metadata,
        });
      }
    }
    
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, topK);
  }
  
  /**
   * Simulated vector search
   */
  private async vectorSearch(
    query: string, 
    topK: number, 
    filter?: Record<string, unknown>
  ): Promise<VectorSearchResult[]> {
    const results: VectorSearchResult[] = [];
    const queryTerms = query.toLowerCase().split(/\s+/).filter(t => t.length > 1);
    
    for (const [id, data] of this.indexMap) {
      if (!this.matchesFilter(data.metadata, filter)) continue;
      
      const contentLower = data.content.toLowerCase();
      let exactMatches = 0;
      let partialMatches = 0;
      
      for (const term of queryTerms) {
        if (contentLower.includes(term)) {
          exactMatches++;
        } else if (contentLower.includes(term.slice(0, 4))) {
          partialMatches++;
        }
      }
      
      // Simulate vector similarity scoring
      const exactScore = exactMatches / queryTerms.length;
      const partialScore = partialMatches * 0.1 / queryTerms.length;
      let score = exactScore * 0.7 + partialScore;
      
      // Apply importance boost
      if (typeof data.metadata.importance === 'number') {
        score = score * (0.5 + data.metadata.importance * 0.5);
      }
      
      if (score > 0.1) {
        results.push({
          id,
          score: Math.min(1, score),
          metadata: data.metadata,
        });
      }
    }
    
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, topK);
  }
  
  /**
   * Merge hybrid results
   */
  private mergeResults(
    textResults: VectorSearchResult[],
    vectorResults: VectorSearchResult[],
    topK: number
  ): VectorSearchResult[] {
    const merged = new Map<string, VectorSearchResult>();
    
    // Text results with weight 0.3
    for (const r of textResults) {
      merged.set(r.id, {
        id: r.id,
        score: r.score * 0.3,
        metadata: r.metadata,
      });
    }
    
    // Vector results with weight 0.7
    for (const r of vectorResults) {
      const existing = merged.get(r.id);
      if (existing) {
        existing.score += r.score * 0.7;
      } else {
        merged.set(r.id, {
          id: r.id,
          score: r.score * 0.7,
          metadata: r.metadata,
        });
      }
    }
    
    const results = [...merged.values()];
    results.sort((a, b) => b.score - a.score);
    return results.slice(0, topK);
  }
  
  /**
   * Check if metadata matches filter
   */
  private matchesFilter(metadata: Record<string, unknown>, filter?: Record<string, unknown>): boolean {
    if (!filter) return true;
    
    if (filter.location && metadata.location !== filter.location) {
      return false;
    }
    
    if (filter.tags && Array.isArray(filter.tags)) {
      const metaTags = metadata.tags as string[] || [];
      const hasAllTags = (filter.tags as string[]).every(tag => metaTags.includes(tag));
      if (!hasAllTags) return false;
    }
    
    return true;
  }
  
  /**
   * Index content (simulates OpenClaw auto-indexing)
   */
  async index(
    id: string, 
    content: string, 
    metadata?: Record<string, unknown>
  ): Promise<void> {
    this.indexMap.set(id, {
      content,
      metadata: metadata || {},
    });
  }
  
  /**
   * Remove from index
   */
  async remove(id: string): Promise<void> {
    this.indexMap.delete(id);
  }
  
  /**
   * Get indexed count (for testing)
   */
  getIndexSize(): number {
    return this.indexMap.size;
  }
  
  /**
   * Set search behavior
   */
  setSearchBehavior(behavior: 'vector' | 'text' | 'hybrid'): void {
    this.searchBehavior = behavior;
  }
}