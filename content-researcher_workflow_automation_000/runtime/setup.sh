#!/bin/bash
set -e

# Ensure mock binaries are executable
chmod +x /usr/local/bin/claw
chmod +x /usr/local/bin/summarize

# Create the actual content-researcher CLI tool (the skill under test)
cat > /usr/local/bin/content-researcher << 'RESEARCHER_EOF'
#!/usr/bin/env python3
import argparse
import subprocess
import json
import sys
import re
from datetime import datetime
from pathlib import Path

def run_web_search(query, count):
    """Call claw tools web_search"""
    try:
        result = subprocess.run(
            ["claw", "tools", "web_search", "--query", query, "--count", str(count)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("results", [])
    except Exception as e:
        print(f"Warning: Search failed for '{query}': {e}", file=sys.stderr)
    return []

def run_summarize(text, model):
    """Call summarize CLI"""
    try:
        result = subprocess.run(
            ["summarize", "--model", model, "--text", text[:500]],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Warning: Summarize failed: {e}", file=sys.stderr)
    return None

def main():
    parser = argparse.ArgumentParser(description="Content Researcher - Batch search and summarize")
    parser.add_argument("--keywords", required=True, help="Comma-separated keywords")
    parser.add_argument("--per-keyword", type=int, default=10, help="Results per keyword")
    parser.add_argument("--max-results", type=int, default=20, help="Max deduplicated results")
    parser.add_argument("--output", default="content_research_report.md", help="Output file path")
    parser.add_argument("--summarize", action="store_true", help="Enable AI summarization")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--model", default="google/gemini-3-flash-preview", help="Model for summarization")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    
    print(f"Searching for keywords: {keywords}", file=sys.stderr)
    
    # Collect results with deduplication by URL
    seen_urls = set()
    all_results = []
    
    for keyword in keywords:
        print(f"  Searching: {keyword} ({args.per_keyword} results)...", file=sys.stderr)
        results = run_web_search(keyword, args.per_keyword)
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                r["keyword"] = keyword
                all_results.append(r)
    
    # Apply max-results cap
    all_results = all_results[:args.max_results]
    
    print(f"Found {len(all_results)} unique results after deduplication.", file=sys.stderr)
    
    # Optionally summarize
    if args.summarize:
        print(f"Generating AI summaries with model: {args.model}...", file=sys.stderr)
        for r in all_results:
            text = f"{r.get('title','')} {r.get('snippet','')}"
            summary = run_summarize(text, args.model)
            r["ai_summary"] = summary or "(summary unavailable)"
    
    # Output
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if args.format == "json":
        output_data = {
            "generated_at": now,
            "keywords": keywords,
            "total_results": len(all_results),
            "results": all_results
        }
        output_str = json.dumps(output_data, ensure_ascii=False, indent=2)
    else:
        lines = [
            "# 内容调研报告",
            f"**生成时间**：{now}",
            f"**关键词**：{', '.join(keywords)}",
            "",
            "## 📊 搜索结果概览",
            f"共找到 {len(all_results)} 条相关结果",
            "",
        ]
        for i, r in enumerate(all_results, 1):
            lines.append(f"### {i}. {r.get('title','(no title)')}")
            source = r.get('source', '')
            if source:
                lines.append(f"**来源**：{source}")
            url = r.get('url', '')
            if url:
                lines.append(f"**链接**：{url}")
            lines.append("")
            snippet = r.get('snippet','')
            if snippet:
                lines.append(f"**摘要**：\n{snippet}")
                lines.append("")
            if args.summarize and "ai_summary" in r:
                lines.append(f"**AI 总结**：\n{r['ai_summary']}")
                lines.append("")
            lines.append("---")
        output_str = "\n".join(lines)
    
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_str, encoding="utf-8")
    print(f"Report saved to: {output_path}", file=sys.stderr)

if __name__ == "__main__":
    main()
RESEARCHER_EOF

chmod +x /usr/local/bin/content-researcher

# Verify tools are accessible
echo "=== Tool verification ==="
which claw && echo "claw: OK"
which summarize && echo "summarize: OK"
which content-researcher && echo "content-researcher: OK"

echo "=== Setup complete ==="