#!/usr/bin/env python3
"""
Memory Plus - 增强记忆系统
==========================

依赖：
- pymilvus
- requests
- rank-bm25

环境变量：
- MILVUS_URI: Milvus 连接地址 (默认: http://host.docker.internal:19530)
- RAG_COLLECTION: 集合名 (默认: openclaw_memory)
- OLLAMA_URL: Ollama 地址 (默认: http://host.docker.internal:11434)
- OLLAMA_MODEL: 嵌入模型 (默认: bge-m3)

用法：
    python3 rag_integration.py <command> [options]

命令：
    test           - 运行自检测试
    status         - 查看系统状态
    store          - 存储记忆
    search         - 搜索记忆
    hybrid-test    - 对比混合搜索效果
"""

import os, sys, json, requests, logging, argparse
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, Counter
import math
import re

# ═══════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════

def load_config():
    defaults = {
        "MILVUS_URI": os.getenv("MILVUS_URI", "http://host.docker.internal:19530"),
        "RAG_COLLECTION": os.getenv("RAG_COLLECTION", "openclaw_memory"),
        "OLLAMA_URL": os.getenv("OLLAMA_URL", "http://host.docker.internal:11434"),
        "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL", "bge-m3"),
        "OLLAMA_SUMMARY_MODEL": os.getenv("OLLAMA_SUMMARY_MODEL", "qwen3.5"),
        "WORKSPACE": os.getenv("WORKSPACE", "/home/node/.openclaw/workspace"),
        "SEARCH_LIMIT": 5,
        "SEARCH_DAYS": 7,
        "MIN_SCORE": 0.0,
        "ARCHIVE_THRESHOLD": 0.3,
        "BM25_WEIGHT": 0.3,
        "VECTOR_WEIGHT": 0.5,
        "RERANK_ENABLED": False,
    }
    return defaults

CONFIG = load_config()

# ═══════════════════════════════════════════════════════
# BM25
# ═══════════════════════════════════════════════════════

class BM25:
    def __init__(self):
        self.documents = []
        self._index_ready = False
        self._k1 = 1.5
        self._b = 0.75
        self._avgdl = 0
        self._idf = {}
    
    def add_document(self, doc_id: str, content: str):
        tokens = self._tokenize(content)
        self.documents.append((doc_id, content, tokens))
        self._index_ready = False
    
    def build(self):
        if not self.documents:
            return
        total_len = sum(len(doc[2]) for doc in self.documents)
        self._avgdl = total_len / len(self.documents)
        N = len(self.documents)
        doc_freq = defaultdict(int)
        for doc_id, content, tokens in self.documents:
            for token in set(tokens):
                doc_freq[token] += 1
        for token, df in doc_freq.items():
            self._idf[token] = math.log((N - df + 0.5) / (df + 0.5) + 1)
        self._index_ready = True
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        if not self._index_ready:
            self.build()
        query_tokens = self._tokenize(query)
        scores = defaultdict(float)
        for doc_id, content, doc_tokens in self.documents:
            dl = len(doc_tokens)
            freq = defaultdict(int)
            for token in doc_tokens:
                freq[token] += 1
            score = 0.0
            for token in query_tokens:
                if token not in self._idf:
                    continue
                tf = freq.get(token, 0)
                idf = self._idf[token]
                score += idf * (tf * (self._k1 + 1)) / (tf + self._k1 * (1 - self._b + self._b * dl / max(self._avgdl, 1)))
            scores[doc_id] = score
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        tokens = []
        english_pattern = re.compile(r'[a-z0-9]+', re.IGNORECASE)
        for match in english_pattern.finditer(text.lower()):
            token = match.group()
            if len(token) > 1:
                tokens.append(token)
        chinese_chars = [c for c in text if '\u4e00' <= c <= '\u9fff']
        for char in chinese_chars:
            tokens.append(char)
        for i in range(len(chinese_chars) - 1):
            tokens.append(chinese_chars[i] + chinese_chars[i+1])
        return tokens

# ═══════════════════════════════════════════════════════
# RRF 融合
# ═══════════════════════════════════════════════════════

def reciprocal_rank_fusion(vector_results: List[Dict], bm25_results: List[Tuple], k: int = 60) -> List[Dict]:
    scores = defaultdict(float)
    for rank, result in enumerate(vector_results):
        doc_id = str(result.get("id", ""))
        scores[doc_id] += 1.0 / (k + rank + 1) + result.get("score", 0) * CONFIG.get("VECTOR_WEIGHT", 0.5)
    for rank, (doc_id, bm25_score) in enumerate(bm25_results):
        scores[doc_id] += 1.0 / (k + rank + 1) + bm25_score * CONFIG.get("BM25_WEIGHT", 0.3)
    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    doc_map = {str(r.get("id", "")): r for r in vector_results}
    fused_results = []
    for doc_id, fused_score in sorted_docs:
        if doc_id in doc_map:
            result = doc_map[doc_id].copy()
            result["fused_score"] = fused_score
            result["bm25_score"] = next((s for d, s in bm25_results if str(d) == doc_id), 0)
            fused_results.append(result)
    return fused_results

# ═══════════════════════════════════════════════════════
# 关键词重叠
# ═══════════════════════════════════════════════════════

def keyword_overlap(query: str, document: str) -> float:
    def tokenize(text):
        text = text.lower()
        tokens = []
        english_pattern = re.compile(r'[a-z0-9]+', re.IGNORECASE)
        for match in english_pattern.finditer(text):
            token = match.group()
            if len(token) > 1:
                tokens.append(token.lower())
        chinese_chars = [c for c in text if '\u4e00' <= c <= '\u9fff']
        for char in chinese_chars:
            tokens.append(char)
        for i in range(len(chinese_chars) - 1):
            tokens.append(chinese_chars[i] + chinese_chars[i+1])
        return tokens
    stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "这", "那", "么"}
    query_tokens = {t for t in tokenize(query) if t not in stopwords and len(t) > 1}
    doc_tokens = {t for t in tokenize(document) if t not in stopwords and len(t) > 1}
    if not query_tokens:
        return 0.0
    intersection = query_tokens & doc_tokens
    union = query_tokens | doc_tokens
    return len(intersection) / len(union) if union else 0.0

# ═══════════════════════════════════════════════════════
# BM25 分数
# ═══════════════════════════════════════════════════════

def bm25_score(query: str, document: str, avg_dl: float = 100, k1: float = 1.5, b: float = 0.75) -> float:
    def tokenize(text):
        text = text.lower()
        tokens = []
        english_pattern = re.compile(r'[a-z0-9]+', re.IGNORECASE)
        for match in english_pattern.finditer(text):
            token = match.group()
            if len(token) > 1:
                tokens.append(token.lower())
        chinese_chars = [c for c in text if '\u4e00' <= c <= '\u9fff']
        for char in chinese_chars:
            tokens.append(char)
        for i in range(len(chinese_chars) - 1):
            tokens.append(chinese_chars[i] + chinese_chars[i+1])
        return tokens
    doc_tokens = tokenize(document)
    query_tokens = tokenize(query)
    if not doc_tokens or not query_tokens:
        return 0.0
    dl = len(doc_tokens)
    freq = Counter(doc_tokens)
    idf_base = 1.0
    score = 0.0
    for token in query_tokens:
        tf = freq.get(token, 0)
        if tf == 0:
            continue
        score += idf_base * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / max(avg_dl, 1)))
    return score

# ═══════════════════════════════════════════════════════
# 多信号重排
# ═══════════════════════════════════════════════════════

def rerank_with_signals(query: str, results: List[Dict], weights: Dict = None) -> List[Dict]:
    if not results:
        return results
    if weights is None:
        weights = {"fused": 0.4, "overlap": 0.3, "bm25": 0.3}
    for r in results:
        content = r.get("content", "")
        summary = r.get("summary", "")
        text = (summary + " " + content)[:2000]
        fused = r.get("fused_score", 0)
        r["signal_fused"] = min(fused / 5.0, 1.0)
        r["signal_overlap"] = keyword_overlap(query, text)
        r["signal_bm25"] = min(bm25_score(query, text) / 10.0, 1.0)
        r["final_score"] = (
            weights.get("fused", 0.4) * r["signal_fused"] +
            weights.get("overlap", 0.3) * r["signal_overlap"] +
            weights.get("bm25", 0.3) * r["signal_bm25"]
        )
    results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    return results

# ═══════════════════════════════════════════════════════
# Ollama 嵌入
# ═══════════════════════════════════════════════════════

def get_embedding(text: str) -> Optional[List[float]]:
    try:
        resp = requests.post(
            f"{CONFIG['OLLAMA_URL']}/api/embeddings",
            json={"model": CONFIG["OLLAMA_MODEL"], "prompt": text},
            timeout=30,
        )
        resp.raise_for_status()
        emb = resp.json().get("embedding")
        if emb and len(emb) == 1024:
            return emb
        return None
    except Exception as e:
        print(f"[ERROR] Embedding failed: {e}")
        return None

# ═══════════════════════════════════════════════════════
# Milvus 操作
# ═══════════════════════════════════════════════════════

def _get_milvus():
    from pymilvus import MilvusClient
    return MilvusClient(uri=CONFIG["MILVUS_URI"])

def ensure_collection():
    client = _get_milvus()
    if not client.has_collection(CONFIG["RAG_COLLECTION"]):
        client.create_collection(
            collection_name=CONFIG["RAG_COLLECTION"],
            dimension=1024,
            auto_id=True,
            metric_type="COSINE",
        )
    return client

def search_vectors(query_embedding: List[float], limit: int = 5, days: int = 7) -> List[Dict]:
    client = ensure_collection()
    from datetime import timedelta
    results = client.search(
        collection_name=CONFIG["RAG_COLLECTION"],
        data=[query_embedding],
        limit=limit * 2,
        output_fields=["content", "timestamp", "metadata", "source", "topic", "summary"]
    )
    cutoff = datetime.now() - timedelta(days=days)
    out = []
    if results and results[0]:
        for hit in results[0]:
            entity = hit["entity"]
            try:
                ts = datetime.fromisoformat(entity.get("timestamp", "9999"))
                if ts > cutoff:
                    out.append({
                        "id": hit["id"],
                        "content": entity.get("content", ""),
                        "summary": entity.get("summary", ""),
                        "timestamp": entity.get("timestamp", ""),
                        "metadata": json.loads(entity.get("metadata", "{}")),
                        "source": entity.get("source", ""),
                        "topic": entity.get("topic", ""),
                        "score": hit["distance"],
                    })
            except:
                pass
    return out

def store_vectors(data: List[Dict]):
    if not data:
        return []
    client = ensure_collection()
    result = client.insert(collection_name=CONFIG["RAG_COLLECTION"], data=data)
    client.flush(CONFIG["RAG_COLLECTION"])
    ids = result.get("ids", [])
    return list(ids) if ids else []

# ═══════════════════════════════════════════════════════
# 混合搜索
# ═══════════════════════════════════════════════════════

def hybrid_search(query: str, limit: int = 5, min_score: float = 0.0) -> List[Dict]:
    query_emb = get_embedding(query)
    if not query_emb:
        return []
    vector_results = search_vectors(query_emb, limit=10)
    bm25 = BM25()
    for r in vector_results:
        bm25.add_document(str(r["id"]), r.get("content", "") + " " + r.get("summary", ""))
    bm25.build()
    bm25_results = bm25.search(query, top_k=limit * 2)
    fused_results = reciprocal_rank_fusion(vector_results, bm25_results)
    fused_results = rerank_with_signals(query, fused_results)
    return [r for r in fused_results if r.get("final_score", 0) >= min_score][:limit]

# ═══════════════════════════════════════════════════════
# 存储记忆
# ═══════════════════════════════════════════════════════

def generate_summary(content: str, max_length: int = 50) -> str:
    try:
        prompt = f"请为以下内容生成一个简短的摘要（不超过{max_length}个字符）：\n\n{content[:500]}\n\n摘要："
        response = requests.post(
            f"{CONFIG['OLLAMA_URL']}/api/generate",
            json={
                "model": CONFIG.get("OLLAMA_SUMMARY_MODEL", "qwen3.5"),
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 50}
            },
            timeout=30
        )
        if response.status_code == 200:
            summary = response.json().get("response", "").strip()
            return summary.strip().split("\n")[0][:max_length] if summary else content[:max_length]
    except:
        pass
    return content[:max_length]

def store_memory(content: str, source: str = "", topic: str = "", metadata: Dict = None) -> Optional[int]:
    if not content or len(content.strip()) < 5:
        return None
    emb = get_embedding(content)
    if not emb:
        return None
    summary = generate_summary(content)
    ids = store_vectors([{
        "vector": emb,
        "content": content[:2000],
        "summary": summary,
        "timestamp": datetime.now().isoformat(),
        "metadata": json.dumps(metadata or {}, ensure_ascii=False),
        "source": source or "manual",
        "topic": topic or "general",
    }])
    return ids[0] if ids else None

# ═══════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Memory Plus - Enhanced Memory System")
    parser.add_argument("action", choices=["test", "store", "search", "status", "hybrid-test"])
    parser.add_argument("--content", help="Content to store")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--source", default="", help="Source")
    parser.add_argument("--topic", default="", help="Topic")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--min-score", type=float, default=0.0)
    args = parser.parse_args()

    if args.action == "test":
        print("[TEST] Memory Plus system test...")
        test_content = "这是一条测试记忆，用于验证系统功能是否正常"
        mid = store_memory(test_content, source="test", topic="test")
        if mid:
            print(f"[OK] Stored test memory: ID {mid}")
            results = hybrid_search("测试记忆", limit=3)
            print(f"[OK] Search returned {len(results)} results")
            for r in results:
                print(f"  [{r.get('final_score', 0):.3f}] {r.get('content', '')[:50]}...")
        else:
            print("[FAIL] Test failed")

    elif args.action == "store":
        if not args.content:
            print("Error: --content required")
            sys.exit(1)
        mid = store_memory(args.content, source=args.source, topic=args.topic)
        print(f"[OK] Stored: ID {mid}" if mid else "[FAIL] Store failed")

    elif args.action == "search":
        if not args.query:
            print("Error: --query required")
            sys.exit(1)
        results = hybrid_search(args.query, limit=args.limit, min_score=args.min_score)
        print(f"[RESULT] Found {len(results)} results:")
        for i, r in enumerate(results, 1):
            print(f"\n{i}. [Score: {r.get('final_score', 0):.3f}]")
            print(f"   Summary: {r.get('summary', 'N/A')}")
            print(f"   Content: {r.get('content', '')[:100]}...")

    elif args.action == "status":
        client = _get_milvus()
        stats = client.get_collection_stats(CONFIG["RAG_COLLECTION"])
        print(json.dumps({
            "collection": CONFIG["RAG_COLLECTION"],
            "total_records": stats.get("row_count", 0),
            "milvus_uri": CONFIG["MILVUS_URI"],
            "ollama_url": CONFIG["OLLAMA_URL"],
            "ollama_model": CONFIG["OLLAMA_MODEL"],
        }, indent=2))

    elif args.action == "hybrid-test":
        print("[HYBRID TEST] Comparing search quality...\n")
        queries = ["深度学习", "RAG 系统", "飞书 配置"]
        for q in queries:
            results = hybrid_search(q, limit=3)
            print(f"Query: {q}")
            print(f"  Results: {len(results)}")
            if results:
                print(f"  Top: [{results[0].get('final_score', 0):.3f}] {results[0].get('content', '')[:40]}...")
            print()

if __name__ == "__main__":
    main()
