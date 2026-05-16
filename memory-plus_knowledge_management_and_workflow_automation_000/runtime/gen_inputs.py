import os
import random
import json
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

BASE_SKILL_DIR = Path("/root/.openclaw/workspace/skills/memory-workflow")
DATA_DIR = Path("/root/.openclaw/workspace/memory-workflow-data")
WORKSPACE = Path("/root/.openclaw/workspace")

# Create directory structure
(BASE_SKILL_DIR / "scripts").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "memories").mkdir(parents=True, exist_ok=True)
(DATA_DIR / "knowledge-graph").mkdir(parents=True, exist_ok=True)

# Create distractor files in workspace
distractor_dirs = [
    WORKSPACE / "projects" / "alpha",
    WORKSPACE / "projects" / "beta" / "src",
    WORKSPACE / "logs" / "2024",
    WORKSPACE / "config" / "backup",
    WORKSPACE / "temp" / "cache",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    WORKSPACE / "projects" / "alpha" / "notes.txt": "Random project notes for alpha team.\nSome optimization work.",
    WORKSPACE / "projects" / "alpha" / "config.json": '{"project": "alpha", "version": "1.0"}',
    WORKSPACE / "projects" / "beta" / "src" / "main.py": "# placeholder main\nprint('hello')",
    WORKSPACE / "projects" / "beta" / "README_old.txt": "Old readme, ignore.",
    WORKSPACE / "logs" / "2024" / "errors.log": "2024-01-01 ERROR: Something failed\n2024-01-02 ERROR: Another issue",
    WORKSPACE / "logs" / "2024" / "access.log": "192.168.1.1 GET /api/data 200",
    WORKSPACE / "config" / "backup" / "settings.bak": "[settings]\ntheme=dark\nlang=zh",
    WORKSPACE / "config" / "app.conf": "debug=false\nport=8080",
    WORKSPACE / "temp" / "cache" / "tmp_001.dat": "binary-like-data-placeholder-001",
    WORKSPACE / "temp" / "cache" / "tmp_002.dat": "binary-like-data-placeholder-002",
    WORKSPACE / "temp" / "scratch.txt": "temporary scratch notes",
}
for fpath, content in distractor_files.items():
    fpath.write_text(content, encoding="utf-8")

# === Create the actual memory-workflow skill scripts ===

# config.py
config_py = '''
import os
from pathlib import Path

HOME = Path.home()
OPENCLAW_HOME = HOME / ".openclaw" / "workspace"
DATA_DIR = OPENCLAW_HOME / "memory-workflow-data"
MEMORIES_DIR = DATA_DIR / "memories"
FTS5_DB = DATA_DIR / "fts5_index.db"
KG_DIR = DATA_DIR / "knowledge-graph"
KG_DB = KG_DIR / "kg.db"

MILVUS_HOST = "localhost"
MILVUS_PORT = 18779
OLLAMA_HOST = "localhost"
OLLAMA_PORT = 11434

for d in [MEMORIES_DIR, KG_DIR]:
    d.mkdir(parents=True, exist_ok=True)
'''
(BASE_SKILL_DIR / "scripts" / "config.py").write_text(config_py)

# fts5.py
fts5_py = '''
import sqlite3
import re
from pathlib import Path
from scripts.config import FTS5_DB


def get_conn():
    conn = sqlite3.connect(str(FTS5_DB))
    conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
            id, content, tags, date,
            tokenize='unicode61'
        )
    """)
    conn.commit()
    return conn


def index_memory(memory_id: str, content: str, tags: str, date: str):
    conn = get_conn()
    # Remove existing entry
    conn.execute("DELETE FROM memories_fts WHERE id = ?", (memory_id,))
    conn.execute(
        "INSERT INTO memories_fts(id, content, tags, date) VALUES (?, ?, ?, ?)",
        (memory_id, content, tags, date)
    )
    conn.commit()
    conn.close()


def fts5_search(query: str, limit: int = 10):
    conn = get_conn()
    try:
        # Escape special FTS5 characters
        safe_query = re.sub(r\'[^\\w\\s\\u4e00-\\u9fff]\', \' \', query).strip()
        if not safe_query:
            return []
        rows = conn.execute(
            "SELECT id, content, tags, date, rank FROM memories_fts WHERE memories_fts MATCH ? ORDER BY rank LIMIT ?",
            (safe_query, limit)
        ).fetchall()
        return rows
    except Exception:
        return []
    finally:
        conn.close()


def delete_from_index(memory_id: str):
    conn = get_conn()
    conn.execute("DELETE FROM memories_fts WHERE id = ?", (memory_id,))
    conn.commit()
    conn.close()


def list_all_indexed():
    conn = get_conn()
    rows = conn.execute("SELECT id, content, tags, date FROM memories_fts").fetchall()
    conn.close()
    return rows
'''
(BASE_SKILL_DIR / "scripts" / "fts5.py").write_text(fts5_py)

# search.py
search_py = '''
import re
import math
from datetime import datetime
from scripts.fts5 import fts5_search, list_all_indexed


def ngram_set(text: str, n: int = 2):
    """Character-level N-gram set for Jaccard similarity (handles Chinese without tokenizer)."""
    text = re.sub(r\'\\s+\', \'\', text)
    if len(text) < n:
        return set(text)
    return set(text[i:i+n] for i in range(len(text) - n + 1))


def jaccard(a: str, b: str, n: int = 2) -> float:
    sa = ngram_set(a, n)
    sb = ngram_set(b, n)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def time_decay(date_str: str, decay_days: int = 30) -> float:
    """Exponential time decay factor based on age."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        age = (datetime.now() - dt).days
        return math.exp(-age / decay_days)
    except Exception:
        return 0.5


def search_memories(query: str, limit: int = 5) -> list:
    """
    Search flow: Jaccard recall -> FTS5 BM25 rerank -> time decay rerank
    Returns list of dicts with id, content, tags, date, score
    """
    all_entries = list_all_indexed()
    
    # Step 1: Jaccard recall
    scored = []
    for row in all_entries:
        mid, content, tags, date = row[0], row[1], row[2], row[3]
        j_score = jaccard(query, content)
        scored.append({\'id\': mid, \'content\': content, \'tags\': tags, \'date\': date, \'jaccard\': j_score})
    
    scored.sort(key=lambda x: x[\'jaccard\'], reverse=True)
    candidates = scored[:max(limit * 3, 15)]
    
    # Step 2: FTS5 BM25 rerank
    fts_results = fts5_search(query, limit=limit * 3)
    fts_ids = {r[0]: idx for idx, r in enumerate(fts_results)}
    
    for c in candidates:
        fts_boost = 1.0 - (fts_ids.get(c[\'id\'], len(fts_results)) / max(len(fts_results), 1)) * 0.3
        c[\'combined\'] = c[\'jaccard\'] * 0.6 + fts_boost * 0.4
    
    candidates.sort(key=lambda x: x[\'combined\'], reverse=True)
    
    # Step 3: Time decay rerank
    for c in candidates:
        decay = time_decay(c[\'date\'])
        c[\'final_score\'] = c[\'combined\'] * 0.7 + decay * 0.3
    
    candidates.sort(key=lambda x: x[\'final_score\'], reverse=True)
    return candidates[:limit]
'''
(BASE_SKILL_DIR / "scripts" / "search.py").write_text(search_py)

# store.py
store_py = '''
import hashlib
import json
import sqlite3
import re
from datetime import datetime
from pathlib import Path
from scripts.config import MEMORIES_DIR, KG_DB
from scripts.fts5 import index_memory


def generate_id(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def store_to_file(content: str, tags: str, date: str) -> str:
    """Write memory to daily markdown file."""
    fpath = MEMORIES_DIR / f"{date}.md"
    memory_id = generate_id(content)
    
    entry = f"""
## {memory_id}
- **时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **标签**: {tags}
- **内容**: {content}
"""
    with open(fpath, \'a\', encoding=\'utf-8\') as f:
        f.write(entry)
    return memory_id


def store_to_kg(memory_id: str, content: str, tags: str, date: str):
    """Store to KG SQLite with rule-based triple extraction (no Ollama required)."""
    conn = sqlite3.connect(str(KG_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories_meta (
            id TEXT PRIMARY KEY,
            content TEXT,
            tags TEXT,
            date TEXT,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS triples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            predicate TEXT,
            object TEXT,
            memory_id TEXT
        )
    """)
    conn.execute(
        "INSERT OR REPLACE INTO memories_meta(id, content, tags, date, created_at) VALUES (?,?,?,?,?)",
        (memory_id, content, tags, date, datetime.now().isoformat())
    )
    # Rule-based triple: (memory_id, has_tag, tag)
    for tag in tags.split(\',\'):
        tag = tag.strip()
        if tag:
            conn.execute(
                "INSERT INTO triples(subject, predicate, object, memory_id) VALUES (?,?,?,?)",
                (memory_id, \'has_tag\', tag, memory_id)
            )
    conn.commit()
    conn.close()


def is_duplicate(content: str, threshold: float = 0.85) -> bool:
    """Check for near-duplicate using Jaccard before storing."""
    from scripts.search import jaccard
    from scripts.fts5 import list_all_indexed
    
    existing = list_all_indexed()
    for row in existing:
        existing_content = row[1]
        if jaccard(content, existing_content) >= threshold:
            return True
    return False


def store_memory(content: str, tags: str = "general") -> dict:
    """Full three-layer store with auto-dedup."""
    if is_duplicate(content):
        return {"status": "duplicate", "message": "Near-duplicate detected, skipping."}
    
    date = datetime.now().strftime("%Y-%m-%d")
    memory_id = store_to_file(content, tags, date)
    index_memory(memory_id, content, tags, date)
    store_to_kg(memory_id, content, tags, date)
    
    return {"status": "stored", "id": memory_id, "date": date}
'''
(BASE_SKILL_DIR / "scripts" / "store.py").write_text(store_py)

# tools.py
tools_py = '''
import json
import re
import sqlite3
from datetime import datetime, timedelta
from scripts.search import search_memories, jaccard
from scripts.store import store_memory
from scripts.fts5 import list_all_indexed, delete_from_index
from scripts.config import MEMORIES_DIR, KG_DB


class MemorySearch:
    name = "MemorySearch"
    
    def run(self, query: str, limit: int = 5, llm_answer: bool = False) -> dict:
        results = search_memories(query, limit=limit)
        return {
            "query": query,
            "count": len(results),
            "results": results,
            "llm_answer": llm_answer
        }


class MemoryStore:
    name = "MemoryStore"
    
    def run(self, content: str, tag: str = "general") -> dict:
        return store_memory(content, tags=tag)


class MemoryDedup:
    name = "MemoryDedup"
    THRESHOLD = 0.85
    
    def run(self) -> dict:
        """Remove near-duplicate memories using Jaccard >= 0.85 threshold."""
        all_entries = list_all_indexed()
        removed = []
        kept = []
        
        for i, row_i in enumerate(all_entries):
            mid_i, content_i = row_i[0], row_i[1]
            is_dup = False
            for kept_row in kept:
                if jaccard(content_i, kept_row[1]) >= self.THRESHOLD:
                    is_dup = True
                    break
            if is_dup:
                removed.append(mid_i)
                delete_from_index(mid_i)
                # Also remove from KG
                try:
                    conn = sqlite3.connect(str(KG_DB))
                    conn.execute("DELETE FROM memories_meta WHERE id = ?", (mid_i,))
                    conn.execute("DELETE FROM triples WHERE memory_id = ?", (mid_i,))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass
            else:
                kept.append(row_i)
        
        return {"status": "done", "removed_count": len(removed), "removed_ids": removed, "kept_count": len(kept)}


class MemoryConsolidate:
    name = "MemoryConsolidate"
    THRESHOLD = 0.7
    
    def run(self) -> dict:
        """Merge similar memories with Jaccard > 0.7."""
        all_entries = list_all_indexed()
        merged_count = 0
        groups = []
        used = set()
        
        for i, row_i in enumerate(all_entries):
            if row_i[0] in used:
                continue
            group = [row_i]
            used.add(row_i[0])
            for j, row_j in enumerate(all_entries):
                if row_j[0] in used:
                    continue
                if jaccard(row_i[1], row_j[1]) > self.THRESHOLD:
                    group.append(row_j)
                    used.add(row_j[0])
            if len(group) > 1:
                # Merge: combine contents
                merged_content = " | ".join(set(r[1] for r in group))
                merged_tags = ",".join(set(",".join(r[2] for r in group).split(",")))
                # Remove old, store merged
                for r in group:
                    delete_from_index(r[0])
                store_memory(merged_content, tags=merged_tags)
                merged_count += len(group)
                groups.append([r[0] for r in group])
        
        return {"status": "done", "merged_groups": len(groups), "total_merged": merged_count}


class MemoryPrune:
    name = "MemoryPrune"
    
    def run(self, days: int = 30) -> dict:
        """Remove memories older than N days."""
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        all_entries = list_all_indexed()
        removed = []
        for row in all_entries:
            if row[3] < cutoff:
                delete_from_index(row[0])
                removed.append(row[0])
        return {"status": "done", "removed_count": len(removed), "cutoff_date": cutoff}


class MemoryList:
    name = "MemoryList"
    
    def run(self) -> dict:
        files = sorted(MEMORIES_DIR.glob("*.md"), reverse=True)
        return {
            "count": len(files),
            "files": [str(f.name) for f in files]
        }
'''
(BASE_SKILL_DIR / "scripts" / "tools.py").write_text(tools_py)

# save_session.py
save_session_py = '''
#!/usr/bin/env python3
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.store import store_memory


def main():
    data_str = sys.stdin.read().strip() if not sys.argv[1:] else sys.argv[1]
    try:
        data = json.loads(data_str)
    except Exception:
        print(json.dumps({"error": "Invalid JSON"}))
        return
    
    messages = data.get("messages", [])
    combined = " ".join(m.get("content", "") for m in messages)
    if combined.strip():
        result = store_memory(combined, tags="session")
        print(json.dumps(result))
    else:
        print(json.dumps({"status": "empty", "message": "No content to save"}))


if __name__ == "__main__":
    main()
'''
(BASE_SKILL_DIR / "scripts" / "save_session.py").write_text(save_session_py)

# Create __init__.py files
(BASE_SKILL_DIR / "scripts" / "__init__.py").write_text("")

# memory_ops.py - main CLI entry point
memory_ops_py = '''#!/usr/bin/env python3
"""
Memory Workflow CLI Entry Point
"""
import sys
import json
import argparse
from pathlib import Path

# Ensure skill dir is in path
skill_dir = Path(__file__).parent
sys.path.insert(0, str(skill_dir))

from scripts.tools import (
    MemorySearch, MemoryStore, MemoryDedup,
    MemoryConsolidate, MemoryPrune, MemoryList
)


def cmd_search(args):
    tool = MemorySearch()
    result = tool.run(query=args.query, limit=args.limit, llm_answer=args.llm_answer)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_store(args):
    tool = MemoryStore()
    result = tool.run(content=args.content, tag=args.tag)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_dedup(args):
    tool = MemoryDedup()
    result = tool.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_consolidate(args):
    tool = MemoryConsolidate()
    result = tool.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_prune(args):
    tool = MemoryPrune()
    result = tool.run(days=args.days)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_list(args):
    tool = MemoryList()
    result = tool.run()
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_register(args):
    tools = [MemorySearch, MemoryStore, MemoryDedup, MemoryConsolidate, MemoryPrune, MemoryList]
    definitions = [{"name": t.name, "description": t.__doc__ or ""} for t in tools]
    print(json.dumps(definitions, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Memory Workflow CLI")
    subparsers = parser.add_subparsers(dest="command")

    # search
    p_search = subparsers.add_parser("search")
    p_search.add_argument("--query", required=True)
    p_search.add_argument("--limit", type=int, default=5)
    p_search.add_argument("--llm-answer", action="store_true")
    p_search.set_defaults(func=cmd_search)

    # store
    p_store = subparsers.add_parser("store")
    p_store.add_argument("--content", required=True)
    p_store.add_argument("--tag", default="general")
    p_store.set_defaults(func=cmd_store)

    # dedup
    p_dedup = subparsers.add_parser("dedup")
    p_dedup.set_defaults(func=cmd_dedup)

    # consolidate
    p_consol = subparsers.add_parser("consolidate")
    p_consol.set_defaults(func=cmd_consolidate)

    # prune
    p_prune = subparsers.add_parser("prune")
    p_prune.add_argument("--days", type=int, default=30)
    p_prune.set_defaults(func=cmd_prune)

    # list
    p_list = subparsers.add_parser("list")
    p_list.set_defaults(func=cmd_list)

    # register
    p_reg = subparsers.add_parser("register")
    p_reg.set_defaults(func=cmd_register)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
'''
(BASE_SKILL_DIR / "memory_ops.py").write_text(memory_ops_py)

# Create the AGENTS.md (without the memory-workflow installation marker — agent must add it)
agents_md_content = """# Workspace Agent Configuration

This file configures the behavior of AI agents operating in this workspace.

## General Rules
- Always verify file paths before operating
- Prefer incremental changes over bulk rewrites
- Log all significant operations

## Project Conventions
- Python files use 4-space indentation
- JSON outputs should be pretty-printed
- All dates in ISO 8601 format (YYYY-MM-DD)
"""
(WORKSPACE / "AGENTS.md").write_text(agents_md_content)

# Create a raw notes file — the messy input the agent must process
raw_notes_content = """# Research Notes - ML Optimization Techniques
(Unstructured — needs to be entered into our knowledge base)

NOTE 1:
梯度下降法是深度学习中最基本的优化算法，通过计算损失函数对参数的梯度来更新模型权重。
Tags: ml, optimization, gradient

NOTE 2:
Adam优化器结合了动量法和RMSProp的优点，能够自适应地调整学习率，在实践中表现优秀。
Tags: ml, optimization, adam

NOTE 3 (NEAR-DUPLICATE of NOTE 1 — should be removed):
梯度下降算法是深度学习中最基础的优化方法，通过计算损失函数梯度来更新神经网络参数。
Tags: ml, optimization, gradient

NOTE 4:
批量归一化（Batch Normalization）通过标准化每层的输入分布，加速训练并提高模型稳定性。
Tags: ml, normalization, training

NOTE 5:
Dropout正则化技术在训练过程中随机丢弃神经元，有效防止过拟合，提高模型泛化能力。
Tags: ml, regularization, dropout

NOTE 6 (NEAR-DUPLICATE of NOTE 2 — should be removed):
Adam优化器综合了动量和RMSProp优势，自适应调整学习速率，在深度学习实践中广泛使用。
Tags: ml, optimization, adam

NOTE 7:
学习率调度策略（如余弦退火、阶梯衰减）对模型最终性能影响显著，需要仔细调参。
Tags: ml, optimization, learning-rate

NOTE 8:
权重初始化方法（Xavier、He初始化）对深度网络训练的稳定性至关重要。
Tags: ml, initialization, deep-learning
"""
(WORKSPACE / "raw_research_notes.txt").write_text(raw_notes_content, encoding="utf-8")

# Create the target output file spec (empty placeholder for the agent to fill)
# The agent must create: search_results.json
# (We do NOT create it — the agent must create it)

print("Workspace generation complete.")
print(f"Skill dir: {BASE_SKILL_DIR}")
print(f"Data dir: {DATA_DIR}")
print(f"Raw notes: {WORKSPACE}/raw_research_notes.txt")