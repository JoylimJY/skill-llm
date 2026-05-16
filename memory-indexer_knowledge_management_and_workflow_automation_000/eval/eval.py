import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ──────────────────────────────────────────────────────────────
    home = Path.home()
    memory_index_dir = home / ".memory-indexer"
    index_file = memory_index_dir / "index.json"
    stars_file = memory_index_dir / "stars.json"

    # ── CHECK 1: index.json exists and contains expected Chinese keywords ──
    try:
        index_data = json.loads(index_file.read_text(encoding="utf-8"))
        # The index maps keywords to file lists
        all_keywords = set(index_data.keys()) if isinstance(index_data, dict) else set()
        
        # Key Chinese terms that MUST appear after jieba segmentation of the 6 notes
        required_keywords_samples = ["蛋白质", "深度学习", "NLP", "模型", "折叠"]
        found_keywords = []
        for kw in required_keywords_samples:
            # Check if any index key contains this term (jieba may produce sub-tokens)
            matched = any(kw in k or k in kw for k in all_keywords)
            if matched:
                found_keywords.append(kw)
        
        passed_1 = len(found_keywords) >= 3
        checks.append({
            "name": "index.json contains expected keywords from added notes",
            "passed": passed_1,
            "detail": f"Found {len(found_keywords)}/{len(required_keywords_samples)} expected keywords: {found_keywords}. Total index keys: {len(all_keywords)}"
        })
        if passed_1:
            total_score += 0.20
    except Exception as e:
        checks.append({
            "name": "index.json contains expected keywords from added notes",
            "passed": False,
            "detail": f"Error reading index.json: {e}"
        })

    # ── CHECK 2: At least 6 memory files were created ─────────────────────
    try:
        # Memory files are stored relative to the memory-indexer install or in ~/.memory-indexer
        # The tool stores memories in the memories/ dir relative to memory-indexer.py
        mem_dirs_to_check = [
            Path("/opt/memory-indexer/memories"),
            home / ".memory-indexer" / "memories",
            home / "memories",
        ]
        
        md_files = []
        for mem_dir in mem_dirs_to_check:
            if mem_dir.exists():
                md_files.extend(list(mem_dir.glob("*.md")))
        
        # Also check index for number of unique files referenced
        if not md_files:
            try:
                idx = json.loads(index_file.read_text(encoding="utf-8"))
                unique_files = set()
                for v in idx.values():
                    if isinstance(v, list):
                        unique_files.update(v)
                    elif isinstance(v, dict):
                        unique_files.update(v.keys() if hasattr(v, 'keys') else [])
                count = len(unique_files)
            except:
                count = 0
        else:
            count = len(md_files)
        
        passed_2 = count >= 6
        checks.append({
            "name": "At least 6 memory entries were added",
            "passed": passed_2,
            "detail": f"Found {count} memory entries (expected >= 6)"
        })
        if passed_2:
            total_score += 0.20
    except Exception as e:
        checks.append({
            "name": "At least 6 memory entries were added",
            "passed": False,
            "detail": f"Error counting memory files: {e}"
        })

    # ── CHECK 3: stars.json contains exactly 2 starred memories ──────────
    try:
        stars_data = json.loads(stars_file.read_text(encoding="utf-8"))
        
        # stars.json could be a list of filenames or a dict
        if isinstance(stars_data, list):
            starred_items = stars_data
        elif isinstance(stars_data, dict):
            starred_items = list(stars_data.keys()) + list(stars_data.values()) if stars_data else []
            # flatten if needed
            flat = []
            for v in stars_data.values():
                if isinstance(v, list):
                    flat.extend(v)
                else:
                    flat.append(v)
            starred_items = list(stars_data.keys()) + flat
        else:
            starred_items = []
        
        # We expect at least 2 starred entries
        # Check by counting unique .md files referenced
        md_entries = [s for s in starred_items if isinstance(s, str) and '.md' in s]
        # Also count top-level keys if they're filenames
        if isinstance(stars_data, dict):
            md_keys = [k for k in stars_data.keys() if '.md' in k]
            md_entries = list(set(md_entries + md_keys))
        
        passed_3 = len(md_entries) >= 2
        checks.append({
            "name": "stars.json contains at least 2 starred memory entries",
            "passed": passed_3,
            "detail": f"Found {len(md_entries)} starred .md entries: {md_entries[:5]}"
        })
        if passed_3:
            total_score += 0.20
    except Exception as e:
        checks.append({
            "name": "stars.json contains at least 2 starred memory entries",
            "passed": False,
            "detail": f"Error reading stars.json: {e}"
        })

    # ── CHECK 4: search_results.txt exists and contains AND-search results ─
    try:
        results_files = list(workspace.rglob("search_results.txt"))
        if not results_files:
            raise FileNotFoundError("search_results.txt not found anywhere in workspace")
        
        results_file = results_files[0]
        content = results_file.read_text(encoding="utf-8")
        
        # The AND search for "蛋白质" AND "深度学习" should return notes 3 and 5
        # Note 3: "深度学习模型训练完成，使用BERT架构，在蛋白质序列分析任务上表现优异"
        # Note 5: "团队发现蛋白质折叠与基因表达之间存在强相关性，需要进一步研究深度学习方法验证"
        
        content_lower = content.lower()
        has_content = len(content.strip()) > 10
        # Check that the output is not empty and mentions relevant terms or file references
        has_relevant = (
            "蛋白质" in content or
            "深度学习" in content or
            ".md" in content or
            "protein" in content_lower or
            "memory" in content_lower or
            "found" in content_lower or
            "结果" in content or
            "匹配" in content
        )
        
        passed_4 = has_content and has_relevant
        checks.append({
            "name": "search_results.txt exists with AND-search output",
            "passed": passed_4,
            "detail": f"File found at {results_file}, length={len(content)}, has_relevant_content={has_relevant}. Preview: {content[:200]}"
        })
        if passed_4:
            total_score += 0.20
    except Exception as e:
        checks.append({
            "name": "search_results.txt exists with AND-search output",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── CHECK 5: related_output.txt exists and has association content ─────
    try:
        related_files = list(workspace.rglob("related_output.txt"))
        if not related_files:
            raise FileNotFoundError("related_output.txt not found anywhere in workspace")
        
        related_file = related_files[0]
        content = related_file.read_text(encoding="utf-8")
        
        has_content = len(content.strip()) > 5
        checks.append({
            "name": "related_output.txt exists with association discovery output",
            "passed": has_content,
            "detail": f"File found at {related_file}, length={len(content)}. Preview: {content[:200]}"
        })
        if has_content:
            total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "related_output.txt exists with association discovery output",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── CHECK 6: status_output.txt exists and mentions memory count ────────
    try:
        status_files = list(workspace.rglob("status_output.txt"))
        if not status_files:
            raise FileNotFoundError("status_output.txt not found anywhere in workspace")
        
        status_file = status_files[0]
        content = status_file.read_text(encoding="utf-8")
        
        has_content = len(content.strip()) > 5
        # Status output should mention something meaningful about the state
        meaningful = any(term in content for term in [
            "记忆", "索引", "关键词", "memory", "index", "keyword", "星标", "star",
            "条", "个", "files", "count", "total"
        ])
        
        passed_6 = has_content and meaningful
        checks.append({
            "name": "status_output.txt exists with meaningful status information",
            "passed": passed_6,
            "detail": f"File found at {status_file}, length={len(content)}, meaningful={meaningful}. Preview: {content[:200]}"
        })
        if passed_6:
            total_score += 0.10
    except Exception as e:
        checks.append({
            "name": "status_output.txt exists with meaningful status information",
            "passed": False,
            "detail": f"Error: {e}"
        })

    # ── Final scoring ──────────────────────────────────────────────────────
    all_passed = all(c["passed"] for c in checks)
    
    result = {
        "passed": all_passed and total_score >= 0.80,
        "score": round(total_score, 2),
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)