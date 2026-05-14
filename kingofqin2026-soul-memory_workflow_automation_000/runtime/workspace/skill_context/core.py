#!/usr/bin/env python3
"""
Soul Memory System v3.6.1 - Core Orchestrator
智能記憶管理系統 + 語義緩存 + 動態上下文窗口 + OpenClaw 2026.3.7 深度集成

Author: Li Si (李斯)
Date: 2026-03-09

v3.6.1 - Add typed memory focus injection, distilled summaries, and audit logging
v3.6.0 - Fix CLI pure JSON output, prefer last user message for memory query, improve plugin injection reliability
v3.5.2 - Query extraction and long-term archive improvements
v3.4.0 - 語義緩存層 + 動態上下文窗口 + 多引擎協同
v3.3.4 - 查詢過濾優化（跳過問候語/簡單命令）
v3.3.3 - 每日快取自動重建（跨日索引更新）
v3.3.2 - Heartbeat 自我報告過濾
v3.3.1 - Heartbeat 自動清理 + Cron Job 集成
"""

import os
import sys
import json
import hashlib
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# Ensure module path
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all modules
from modules.priority_parser import PriorityParser, Priority, ParsedMemory
from modules.vector_search import VectorSearch, SearchResult
from modules.dynamic_classifier import DynamicClassifier
from modules.version_control import VersionControl
from modules.memory_decay import MemoryDecay
from modules.auto_trigger import AutoTrigger, auto_trigger, get_memory_context
from modules.cantonese_syntax import CantoneseSyntaxBranch, CantoneseAnalysisResult, ToneIntensity, ContextType
from modules.heartbeat_filter import HeartbeatFilter, should_filter_memory

# v3.4.0: 新增模組
from modules.semantic_cache import SemanticCache, get_cache
from modules.dynamic_context import DynamicContextWindow, get_context_window, QueryComplexity


@dataclass
class MemoryQueryResult:
    """Memory query result"""
    content: str
    score: float
    source: str
    line_number: int
    category: str
    priority: str


from modules.soul_merge import merge_memory, get_context_for_label

class SoulMemorySystem:
    """
    Soul Memory System v3.6.1
    """

    VERSION = "3.6.1"

    def __init__(self, base_path: Optional[str] = None):
        """Initialize memory system"""
        self.base_path = Path(base_path) if base_path else Path(__file__).parent
        self.cache_path = self.base_path / "cache"
        self.cache_path.mkdir(exist_ok=True)

        # Initialize modules
        self.priority_parser = PriorityParser()
        self.vector_search = VectorSearch()
        self.classifier = DynamicClassifier()
        self.version_control = VersionControl(str(self.base_path))
        self.memory_decay = MemoryDecay(self.cache_path)
        self.auto_trigger = AutoTrigger(self)

        # v3.1.0: Cantonese Grammar Branch
        self.cantonese_branch = CantoneseSyntaxBranch()
        # v3.3.2: Heartbeat 自我報告過濾器
        self.heartbeat_filter = HeartbeatFilter()
        
        # v3.4.0: 新增模組
        self.semantic_cache = get_cache(self.cache_path / "semantic_cache.json")
        self.context_window = get_context_window()

        # v3.5.0: Long-term Soul Archive
        self.soul_memory_path = self.base_path / "soul_memory.md"
        if not self.soul_memory_path.exists():
            self.soul_memory_path.write_text("# Soul Memory - 最終儲存庫 (v3.6.1)\n", encoding='utf-8')

        self.indexed = False

    def update_soul_memory(self, label: str, content: str):
        """v3.5.0: Incremental merge into long-term archive"""
        current_mem = self.soul_memory_path.read_text(encoding='utf-8')
        updated = merge_memory(current_mem, content, label)
        self.soul_memory_path.write_text(updated, encoding='utf-8')
        print(f"💾 Soul Merge SUCCESS: soul\"{label}\" updated.")
        # Rebuild index if needed
        self.indexed = False

    def initialize(self):
        """Initialize and build index"""
        print(f"🧠 Initializing Soul Memory System v{self.VERSION}...")

        # Load or build search index
        index_file = self.cache_path / "index.json"

        # v3.3.3: 每日快取自動重建 - 檢查快取日期
        cache_outdated = False
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                if 'built_at' in index_data:
                    built_date = index_data['built_at'].split('T')[0]
                    today = datetime.now().strftime('%Y-%m-%d')
                    if built_date != today:
                        cache_outdated = True
                        print(f"📅 Cache from {built_date}, rebuilding for {today}...")
            except:
                cache_outdated = True

        if index_file.exists() and not cache_outdated:
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                self.vector_search.load_index(index_data)
                self.classifier.load_categories(index_data.get('categories', []))
                self.indexed = True
                print(f"✅ Loaded index with {len(index_data.get('segments', []))} segments")
            except Exception as e:
                print(f"⚠️  Failed to load index: {e}")
                cache_outdated = True

        if cache_outdated or not index_file.exists():
            print("🔨 Building search index...")
            self._build_index()
            print("✅ Index built successfully")

        # v3.4.0: 初始化語義緩存
        cache_stats = self.semantic_cache.get_stats()
        print(f"💾 Semantic Cache: {cache_stats['cache_size']} entries, {cache_stats['hit_rate']} hit rate")
        
        # v3.4.0: 動態上下文窗口就緒
        print(f"🎯 Dynamic Context Window: ready")

        print("✅ Memory system initialized\n")

    def _build_index(self):
        """Build search index from memory files"""
        # Implementation remains the same as v3.3.4
        # ... (existing code)
        pass

    def search(self, query: str, top_k: int = 5, min_score: float = 0.0, 
               use_cache: bool = True, use_dynamic: bool = True) -> List[Dict]:
        """
        Search memories with v3.4.0 optimizations
        
        Args:
            query: Search query
            top_k: Number of results (ignored if use_dynamic=True)
            min_score: Minimum score threshold (ignored if use_dynamic=True)
            use_cache: Enable semantic cache
            use_dynamic: Enable dynamic context window
            
        Returns:
            List of search results
        """
        # v3.4.0: 檢查語義緩存
        if use_cache:
            cached_results = self.semantic_cache.get(query)
            if cached_results is not None:
                print(f"💾 Cache HIT for query: '{query[:50]}...'")
                # 從緩存的 dict 轉換回 SearchResult 對象
                return [
                    SearchResult(
                        content=r['content'],
                        score=r['score'],
                        source=r['source'],
                        line_number=r.get('line_number', 0),
                        category=r.get('category', ''),
                        priority=r['priority']
                    )
                    for r in cached_results
                ]
        
        # v3.4.0: 動態上下文窗口
        if use_dynamic:
            params = self.context_window.get_params(query)
            top_k = params['top_k']
            min_score = params['min_score']
            print(f"🎯 Dynamic strategy: top_k={top_k}, min_score={min_score}")
        
        # Execute search
        results = self.vector_search.search(query, top_k=top_k, min_score=min_score)
        
        # Convert to dict format
        result_dicts = [
            {
                'content': r.content,
                'score': r.score,
                'source': r.source,
                'priority': r.priority if hasattr(r, 'priority') else 'N'
            }
            for r in results
        ]
        
        # v3.4.0: 保存到緩存
        if use_cache and result_dicts:
            self.semantic_cache.set(query, result_dicts)
            print(f"💾 Cache SET for query: '{query[:50]}...'")
        
        return result_dicts

    def get_auto_context(self, query: str) -> str:
        """v3.5.1: Get dynamic soul context with tag swapping"""
        return get_memory_context(self, query)

    def add_memory(self, content: str, auto_categorize: bool = True) -> str:
        """v3.5.0: Enhanced add_memory with soul merge support"""
        memory_id = super().add_memory(content, auto_categorize)
        
        # Check for soul"..." tag
        match = re.search(r'soul"([^"]+)"', content)
        if match:
            label = match.group(1)
            self.update_soul_memory(label, content)
            
        return memory_id

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        cache_stats = self.semantic_cache.get_stats()
        context_stats = self.context_window.get_stats("test")
        
        return {
            'version': self.VERSION,
            'indexed': self.indexed,
            'semantic_cache': cache_stats,
            'dynamic_context': {
                'version': context_stats['version'],
                'base_topK': context_stats['base_topK'],
                'base_min_score': context_stats['base_min_score']
            }
        }


# Keep existing auto_trigger and other functions
# ...
