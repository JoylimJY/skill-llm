/**
 * Memory Palace Manager
 * 
 * Core manager class for the Memory Palace system.
 * Provides CRUD operations, search, and cognitive enhancement features.
 */

import * as path from 'path';
import * as fs from 'fs/promises';
import { v4 as uuidv4 } from 'uuid';
import { FileStorage, serializeMemory, deserializeMemory } from './storage.js';
import type {
  Memory,
  StoreParams,
  UpdateParams,
  RecallOptions,
  SearchResult,
  ListOptions,
  Stats,
  VectorSearchProvider,
} from './types.js';
import { TimeReasoningEngine, createTimeReasoning, type TimeContext } from './background/time-reasoning.js';
import { ConceptExpander, createConceptExpander, type ConceptExpansion } from './background/concept-expansion.js';
import { ExperienceManager, createExperienceManager } from './experience-manager.js';
import type {
  RecordExperienceOptions,
  GetExperiencesOptions,
  VerifyExperienceOptions,
} from './types.js';

/**
 * Escape special regex characters in a string
 * Prevents regex injection attacks
 */
function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Options for MemoryPalaceManager
 */
export interface MemoryPalaceManagerOptions {
  /** Workspace directory */
  workspaceDir: string;
  
  /** Optional vector search provider */
  vectorSearch?: VectorSearchProvider;
}

/**
 * Memory Palace Manager
 * 
 * Main class for managing memories with CRUD operations,
 * semantic search, and cognitive features.
 */
export class MemoryPalaceManager {
  private workspaceDir: string;
  private storagePath: string;
  private storage: FileStorage;
  private vectorSearch?: VectorSearchProvider;
  private timeReasoning: TimeReasoningEngine;
  private conceptExpander: ConceptExpander;
  private experienceManager: ExperienceManager;
  
  constructor(options: MemoryPalaceManagerOptions) {
    this.workspaceDir = options.workspaceDir;
    this.storagePath = path.join(options.workspaceDir, 'memory/palace');
    this.storage = new FileStorage(this.storagePath);
    this.vectorSearch = options.vectorSearch;
    this.timeReasoning = createTimeReasoning();
    this.conceptExpander = createConceptExpander(options.vectorSearch);
    this.experienceManager = createExperienceManager(this);
  }
  
  /** Get storage path (needed by ExperienceManager) */
  getStoragePath(): string {
    return this.storagePath;
  }
  
  // ==================== CRUD Operations ====================
  
  /**
   * Store a new memory
   */
  async store(params: StoreParams): Promise<Memory> {
    const now = new Date();
    const id = uuidv4();
    
    const memory: Memory = {
      id,
      content: params.content,
      summary: params.summary,
      tags: params.tags || [],
      importance: params.importance ?? 0.5,
      status: 'active',
      source: params.source || 'user',
      location: params.location || 'default',
      createdAt: now,
      updatedAt: now,
      type: params.type,
      experienceMeta: params.experienceMeta,
    };
    
    await this.storage.save(memory);
    
    // Index in vector search if available
    if (this.vectorSearch) {
      const textToIndex = memory.summary 
        ? `${memory.content}\n\nSummary: ${memory.summary}`
        : memory.content;
      await this.vectorSearch.index(id, textToIndex, {
        tags: memory.tags,
        location: memory.location,
        importance: memory.importance,
        type: memory.type,
      });
    }
    
    return memory;
  }
  
  /**
   * Get a memory by ID
   */
  async get(id: string): Promise<Memory | null> {
    return this.storage.load(id);
  }
  
  /**
   * Update a memory
   */
  async update(params: UpdateParams): Promise<Memory | null> {
    const memory = await this.storage.load(params.id);
    if (!memory) {
      return null;
    }
    
    // Apply updates
    if (params.content !== undefined) {
      memory.content = params.content;
    }
    
    if (params.tags !== undefined) {
      if (params.appendTags) {
        memory.tags = [...new Set([...memory.tags, ...params.tags])];
      } else {
        memory.tags = params.tags;
      }
    }
    
    if (params.importance !== undefined) {
      memory.importance = Math.max(0, Math.min(1, params.importance));
    }
    
    if (params.status !== undefined) {
      memory.status = params.status;
    }
    
    if (params.summary !== undefined) {
      memory.summary = params.summary;
    }
    
    memory.updatedAt = new Date();
    
    await this.storage.save(memory);
    
    // Update vector index
    if (this.vectorSearch) {
      const textToIndex = memory.summary 
        ? `${memory.content}\n\nSummary: ${memory.summary}`
        : memory.content;
      await this.vectorSearch.index(params.id, textToIndex, {
        tags: memory.tags,
        location: memory.location,
        importance: memory.importance,
      });
    }
    
    return memory;
  }
  
  /**
   * Delete a memory (soft delete by default)
   */
  async delete(id: string, permanent: boolean = false): Promise<void> {
    const memory = await this.storage.load(id);
    if (!memory) {
      return;
    }
    
    if (permanent) {
      await this.storage.permanentDelete(id);
      if (this.vectorSearch) {
        await this.vectorSearch.remove(id);
      }
    } else {
      await this.storage.moveToTrash(memory);
      if (this.vectorSearch) {
        await this.vectorSearch.remove(id);
      }
    }
  }
  
  // ==================== Search Operations ====================
  
  /**
   * Search/recall memories with time reasoning and concept expansion
   */
  async recall(query: string, options: RecallOptions = {}): Promise<SearchResult[]> {
    const topK = options.topK || 10;
    
    // Step 1: Parse time expressions in the query
    const timeContext = this.timeReasoning.parseTimeQuery(query);
    
    // Step 2: Expand concepts for better retrieval
    let conceptExpansion: ConceptExpansion;
    try {
      conceptExpansion = await this.conceptExpander.expandQuery(query);
    } catch {
      // If expansion fails, use original query keywords
      conceptExpansion = {
        originalQuery: query,
        expandedKeywords: [],
        relatedConcepts: [],
        method: 'mapping',
      };
    }
    
    // Step 3: Build enhanced search query
    const enhancedKeywords = this.buildEnhancedKeywords(
      query, 
      timeContext, 
      conceptExpansion
    );
    
    // Step 4: Use vector search if available
    if (this.vectorSearch) {
      const filter: Record<string, unknown> = {};
      if (options.location) {
        filter.location = options.location;
      }
      if (options.tags && options.tags.length > 0) {
        filter.tags = options.tags;
      }
      
      // Search with original query for semantic matching
      const results = await this.vectorSearch.search(query, topK * 2, filter);
      
      const searchResults: SearchResult[] = [];
      for (const result of results) {
        const memory = await this.storage.load(result.id);
        if (memory && memory.status === 'active') {
          if (options.minImportance && memory.importance < options.minImportance) {
            continue;
          }
          
          // Boost score if keywords match
          const keywordBoost = this.calculateKeywordBoost(memory, enhancedKeywords);
          
          searchResults.push({
            memory,
            score: Math.min(1, result.score + keywordBoost),
            highlights: this.extractHighlights(memory.content, query),
          });
        }
      }
      
      // Sort by boosted score and return top K
      searchResults.sort((a, b) => b.score - a.score);
      return searchResults.slice(0, topK);
    }
    
    // Fallback to text search with enhanced keywords
    return this.textSearch(query, { ...options, enhancedKeywords });
  }
  
  /**
   * Build enhanced keywords from time context and concept expansion
   */
  private buildEnhancedKeywords(
    query: string,
    timeContext: TimeContext,
    conceptExpansion: ConceptExpansion
  ): string[] {
    const keywords: string[] = [];
    
    // Add time-based keywords
    if (timeContext.hasTimeReasoning) {
      keywords.push(...timeContext.keywords);
      
      // Handle conditional time queries like "如果明天是周三"
      const conditional = this.timeReasoning.resolveConditionalTime(query);
      if (conditional.isConditional && conditional.targetDay) {
        keywords.push(conditional.targetDay);
        keywords.push(...conditional.keywords);
      }
    }
    
    // Add concept expansion keywords
    keywords.push(...conceptExpansion.expandedKeywords);
    
    return [...new Set(keywords)];
  }
  
  /**
   * Calculate keyword boost score for a memory
   */
  private calculateKeywordBoost(memory: Memory, keywords: string[]): number {
    if (keywords.length === 0) return 0;
    
    const contentLower = memory.content.toLowerCase();
    const summaryLower = (memory.summary || '').toLowerCase();
    const tagMatches = keywords.filter(k => memory.tags.includes(k)).length;
    const contentMatches = keywords.filter(k => 
      contentLower.includes(k.toLowerCase()) || 
      summaryLower.includes(k.toLowerCase())
    ).length;
    
    // Boost based on matches
    const tagBoost = tagMatches * 0.1;
    const contentBoost = contentMatches * 0.05;
    
    return Math.min(0.3, tagBoost + contentBoost);
  }
  
  /**
   * Text-based search (fallback when vector search is unavailable)
   * Enhanced with time reasoning and concept expansion
   */
  private async textSearch(
    query: string, 
    options: RecallOptions & { enhancedKeywords?: string[] } = {}
  ): Promise<SearchResult[]> {
    const topK = options.topK || 10;
    const queryLower = query.toLowerCase();
    
    // For Chinese text, use character-level matching for better results
    const queryTerms: string[] = [];
    
    // Check if query contains Chinese characters
    const hasChinese = /[\u4e00-\u9fa5]/.test(query);
    
    if (hasChinese) {
      // For Chinese: extract Chinese phrases and use sliding window for matching
      const chineseMatches = query.match(/[\u4e00-\u9fa5]+/g) || [];
      for (const match of chineseMatches) {
        if (match.length >= 2) {
          // Add the whole phrase (highest priority)
          queryTerms.push(match.toLowerCase());
          // Add 2-char sliding windows for partial matching
          for (let i = 0; i < match.length - 1; i++) {
            queryTerms.push(match.substring(i, i + 2).toLowerCase());
          }
        } else {
          queryTerms.push(match.toLowerCase());
        }
      }
      // Also add non-Chinese words
      const nonChineseMatches = query.match(/[a-zA-Z0-9]+/g) || [];
      queryTerms.push(...nonChineseMatches.map(t => t.toLowerCase()));
    } else {
      // For non-Chinese: split by whitespace
      queryTerms.push(...queryLower.split(/\s+/).filter(t => t.length > 1));
    }
    
    // Add enhanced keywords from time reasoning and concept expansion
    if (options.enhancedKeywords && options.enhancedKeywords.length > 0) {
      queryTerms.push(...options.enhancedKeywords.map(k => k.toLowerCase()));
    }
    
    if (queryTerms.length === 0) {
      return [];
    }
    
    // Get all memories
    const ids = await this.storage.listFiles();
    const memories: Memory[] = [];
    
    for (const id of ids) {
      const memory = await this.storage.load(id);
      if (memory) {
        // Filter by status
        if (memory.status !== 'active' && !options.includeArchived) {
          continue;
        }
        if (memory.status === 'archived' && !options.includeArchived) {
          continue;
        }
        
        // Filter by location
        if (options.location && memory.location !== options.location) {
          continue;
        }
        
        // Filter by tags
        if (options.tags && options.tags.length > 0) {
          const hasAllTags = options.tags.every(tag => memory.tags.includes(tag));
          if (!hasAllTags) {
            continue;
          }
        }
        
        // Filter by importance
        if (options.minImportance && memory.importance < options.minImportance) {
          continue;
        }
        
        memories.push(memory);
      }
    }
    
    // Score and rank with enhanced matching
    const results: SearchResult[] = memories.map(memory => {
      const contentLower = memory.content.toLowerCase();
      const summaryLower = (memory.summary || '').toLowerCase();
      
      // Calculate relevance score with better weighting
      let matchCount = 0;
      let totalTerms = queryTerms.length;
      let enhancedMatchCount = 0;
      
      // Separate original terms from enhanced terms
      const originalTermCount = hasChinese 
        ? (query.match(/[\u4e00-\u9fa5]+/g) || []).length
        : queryLower.split(/\s+/).filter(t => t.length > 1).length;
      
      for (let i = 0; i < queryTerms.length; i++) {
        const term = queryTerms[i];
        // Count occurrences - escape regex special chars to prevent injection
        const escapedTerm = escapeRegExp(term);
        const regex = new RegExp(escapedTerm, 'gi');
        const contentMatches = (memory.content.match(regex) || []).length;
        const summaryMatches = (memory.summary?.match(regex) || []).length;
        
        // Check if this is an original term or enhanced term
        const isOriginalTerm = i < originalTermCount;
        
        if (contentMatches > 0 || summaryMatches > 0) {
          if (isOriginalTerm) {
            matchCount++;
          } else {
            enhancedMatchCount++;
          }
        }
        
        // Also check tags for enhanced keywords
        if (!isOriginalTerm && memory.tags.includes(term)) {
          enhancedMatchCount += 0.5;
        }
      }
      
      // Base score: ratio of matched original terms
      let score = totalTerms > 0 ? matchCount / Math.max(1, originalTermCount) : 0;
      
      // Add bonus for enhanced keyword matches (lower weight)
      score += enhancedMatchCount * 0.1;
      
      // Boost by importance
      score *= (0.5 + memory.importance * 0.5);
      
      // Cap at 1.0
      score = Math.min(1, score);
      
      return {
        memory,
        score,
        highlights: this.extractHighlights(memory.content, query),
      };
    });
    
    // Sort by score and return top K
    results.sort((a, b) => b.score - a.score);
    // Only return results with positive scores
    return results.filter(r => r.score > 0).slice(0, topK);
  }
  
  /**
   * Extract text highlights matching query
   */
  private extractHighlights(content: string, query: string): string[] {
    const highlights: string[] = [];
    const terms = query.toLowerCase().split(/\s+/).filter(t => t.length > 1);
    const lines = content.split('\n');
    
    for (const line of lines) {
      const lineLower = line.toLowerCase();
      if (terms.some(term => lineLower.includes(term))) {
        // Truncate long lines
        const highlight = line.length > 100 ? line.slice(0, 100) + '...' : line;
        highlights.push(highlight);
        if (highlights.length >= 3) break;
      }
    }
    
    return highlights;
  }
  
  // ==================== List Operations ====================
  
  /**
   * List memories with filters
   */
  async list(options: ListOptions = {}): Promise<Memory[]> {
    const ids = await this.storage.listFiles();
    const memories: Memory[] = [];
    
    for (const id of ids) {
      const memory = await this.storage.load(id);
      if (!memory) continue;
      
      // Filter by status
      if (options.status && memory.status !== options.status) {
        continue;
      }
      
      // Filter by location
      if (options.location && memory.location !== options.location) {
        continue;
      }
      
      // Filter by tags
      if (options.tags && options.tags.length > 0) {
        const hasAllTags = options.tags.every(tag => memory.tags.includes(tag));
        if (!hasAllTags) {
          continue;
        }
      }
      
      memories.push(memory);
    }
    
    // Sort
    const sortBy = options.sortBy || 'updatedAt';
    const sortOrder = options.sortOrder || 'desc';
    
    memories.sort((a, b) => {
      let cmp = 0;
      if (sortBy === 'createdAt') {
        cmp = a.createdAt.getTime() - b.createdAt.getTime();
      } else if (sortBy === 'updatedAt') {
        cmp = a.updatedAt.getTime() - b.updatedAt.getTime();
      } else if (sortBy === 'importance') {
        cmp = a.importance - b.importance;
      }
      return sortOrder === 'desc' ? -cmp : cmp;
    });
    
    // Paginate
    const offset = options.offset || 0;
    const limit = options.limit || memories.length;
    
    return memories.slice(offset, offset + limit);
  }
  
  // ==================== Statistics ====================
  
  /**
   * Get statistics about the memory palace
   */
  async stats(): Promise<Stats> {
    const ids = await this.storage.listFiles();
    const trashIds = await this.storage.listTrashFiles();
    
    let active = 0;
    let archived = 0;
    const byLocation: Record<string, number> = {};
    const byTag: Record<string, number> = {};
    let totalImportance = 0;
    
    for (const id of ids) {
      const memory = await this.storage.load(id);
      if (!memory) continue;
      
      if (memory.status === 'active') active++;
      else if (memory.status === 'archived') archived++;
      
      byLocation[memory.location] = (byLocation[memory.location] || 0) + 1;
      
      for (const tag of memory.tags) {
        byTag[tag] = (byTag[tag] || 0) + 1;
      }
      
      totalImportance += memory.importance;
    }
    
    return {
      total: ids.length,
      active,
      archived,
      deleted: trashIds.length,
      byLocation,
      byTag,
      avgImportance: ids.length > 0 ? totalImportance / ids.length : 0,
      storagePath: this.storagePath,
    };
  }
  
  // ==================== Trash Operations ====================
  
  /**
   * Restore a deleted memory
   */
  async restore(id: string): Promise<Memory | null> {
    return this.storage.restoreFromTrash(id);
  }
  
  /**
   * List memories in trash
   */
  async listTrash(): Promise<Memory[]> {
    const ids = await this.storage.listTrashFiles();
    const memories: Memory[] = [];
    
    for (const id of ids) {
      const memory = await this.storage.loadFromTrash(id);
      if (memory) {
        memories.push(memory);
      }
    }
    
    return memories;
  }
  
  /**
   * Empty the trash
   */
  async emptyTrash(): Promise<void> {
    await this.storage.emptyTrash();
  }
  
  // ==================== Bulk Operations ====================
  
  /**
   * Store multiple memories at once
   */
  async storeBatch(items: StoreParams[]): Promise<Memory[]> {
    const memories: Memory[] = [];
    for (const item of items) {
      const memory = await this.store(item);
      memories.push(memory);
    }
    return memories;
  }
  
  /**
   * Get multiple memories by IDs
   */
  async getBatch(ids: string[]): Promise<(Memory | null)[]> {
    return Promise.all(ids.map(id => this.get(id)));
  }
  
  // ==================== Experience Operations ====================
  
  /**
   * Record a new experience
   */
  async recordExperience(options: RecordExperienceOptions): Promise<Memory> {
    return this.experienceManager.recordExperience(options);
  }
  
  /**
   * Get experiences matching criteria
   */
  async getExperiences(options?: GetExperiencesOptions): Promise<Memory[]> {
    return this.experienceManager.getExperiences(options);
  }
  
  /**
   * Verify an experience's effectiveness
   */
  async verifyExperience(options: VerifyExperienceOptions): Promise<Memory | null> {
    return this.experienceManager.verifyExperience(options);
  }
  
  /**
   * Get relevant experiences for a context
   */
  async getRelevantExperiences(context: string, limit?: number): Promise<Memory[]> {
    return this.experienceManager.getRelevantExperiences(context, limit);
  }
  
  /**
   * Get experience statistics
   */
  async getExperienceStats(): Promise<{
    total: number;
    byCategory: Record<string, number>;
    verified: number;
    avgVerifiedCount: number;
  }> {
    return this.experienceManager.getExperienceStats();
  }

  async recordAccess(ids: string[]): Promise<void> {
    const now = new Date();
    for (const id of ids) {
      const memory = await this.storage.load(id);
      if (memory) {
        memory.lastAccessedAt = now;
        await this.storage.save(memory);
      }
    }
  }

  async getFrequentlyAccessed(limit: number = 10): Promise<Memory[]> {
    const memories = await this.list({ limit: 1000 });
    return memories
      .filter(m => m.lastAccessedAt)
      .sort((a, b) => (b.lastAccessedAt?.getTime() || 0) - (a.lastAccessedAt?.getTime() || 0))
      .slice(0, limit);
  }
}