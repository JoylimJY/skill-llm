#!/bin/bash
set -e

echo "=== Setting up arxiv skill workspace ==="

# Ensure the arxiv Python package is importable
python -c "import arxiv; print('arxiv package version:', arxiv.__version__)" || {
    echo "arxiv package not found, installing..."
    pip install arxiv -i https://pypi.tuna.tsinghua.edu.cn/simple
}

# Create the arxiv.ps1 PowerShell-style wrapper as a Python script
# (since we're in Linux, we provide the Python API variant the skill references)
cat > /workspace/arxiv_tool.py << 'PYEOF'
#!/usr/bin/env python3
"""
ArXiv skill helper - wraps the arxiv Python package with the interface
described in SKILL.md
"""
import arxiv as _arxiv
import os
import sys

def search(query, max_results=10, categories=None):
    """Search arXiv papers."""
    search_query = query
    if categories:
        cats = [c.strip() for c in categories.split(",")]
        cat_filter = " OR ".join([f"cat:{c}.*" for c in cats])
        search_query = f"({query}) AND ({cat_filter})"
    
    client = _arxiv.Client()
    s = _arxiv.Search(
        query=search_query,
        max_results=max_results,
        sort_by=_arxiv.SortCriterion.Relevance
    )
    return list(client.results(s))

def download(paper, directory="."):
    """Download a paper PDF to the given directory."""
    os.makedirs(directory, exist_ok=True)
    paper.download_pdf(dirpath=directory)
    return directory

PYEOF

chmod +x /workspace/arxiv_tool.py

echo "=== Setup complete ==="
echo "Workspace contents:"
ls -la /workspace/