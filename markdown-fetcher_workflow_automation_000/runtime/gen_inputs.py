import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create deeply nested directory structure with distractor files
dirs = [
    "research/biology/papers",
    "research/biology/notes",
    "research/chemistry/papers",
    "research/physics/drafts",
    "archive/2023/Q1",
    "archive/2023/Q2",
    "archive/2024/Q1",
    "tools/scripts",
    "tools/config",
    "output/markdown",
    "output/raw",
    "logs",
    "tmp/cache",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant
distractor_files = {
    "research/biology/notes/reading_list.txt": "Papers to read:\n- Nature 2024\n- Science 2023\n- Cell 2024\n",
    "research/biology/papers/index.json": json.dumps({"papers": ["paper1", "paper2"], "count": 2}),
    "research/chemistry/papers/todo.md": "# TODO\n- [ ] Read electrochemistry paper\n- [ ] Summarize findings\n",
    "research/physics/drafts/outline.txt": "Draft outline for quantum computing review\n1. Intro\n2. Methods\n",
    "archive/2023/Q1/summary.txt": "Q1 2023 archive summary: 12 papers archived\n",
    "archive/2023/Q2/summary.txt": "Q2 2023 archive summary: 8 papers archived\n",
    "archive/2024/Q1/summary.txt": "Q1 2024 archive summary: 15 papers archived\n",
    "tools/scripts/old_fetcher.py": "# Deprecated fetcher\nimport urllib\n# This script is no longer maintained\n",
    "tools/config/settings.json": json.dumps({"timeout": 30, "retries": 3, "format": "html"}),
    "logs/fetch_errors_2023.log": "2023-01-15 ERROR: Connection timeout for https://example.com\n2023-02-20 ERROR: 404 Not Found\n",
    "logs/fetch_errors_2024.log": "2024-03-01 ERROR: SSL certificate error\n2024-04-10 ERROR: Rate limit exceeded\n",
    "tmp/cache/stale_data.json": json.dumps({"cached_at": "2023-01-01", "url": "https://old-url.com", "status": "stale"}),
    "output/raw/failed_attempt.html": "<html><body>Failed to parse</body></html>",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content)

# THE PROBLEM: A list of URLs to fetch and convert to Markdown
# The agent must fetch these and save as markdown files
urls_to_fetch = [
    {
        "url": "https://example-research.org/articles/neural-plasticity-2024",
        "expected_filename": "neural_plasticity_2024.md",
        "description": "Neural plasticity research article from 2024"
    },
    {
        "url": "https://scijournal.net/papers/quantum-entanglement-review",
        "expected_filename": "quantum_entanglement_review.md",
        "description": "Quantum entanglement comprehensive review paper"
    },
    {
        "url": "https://biotech-weekly.com/crispr-advances-2024",
        "expected_filename": "crispr_advances_2024.md",
        "description": "CRISPR technology advances article"
    }
]

fetch_task = {
    "task": "Convert the following research article URLs to Markdown format and save them as individual files",
    "urls": urls_to_fetch,
    "output_note": "Each URL should be saved as the filename specified in expected_filename"
}

(workspace / "fetch_tasks.json").write_text(json.dumps(fetch_task, indent=2))

# Write a mock server config so the setup script knows what to serve
mock_config = {
    "urls": [item["url"] for item in urls_to_fetch],
    "port": 18765
}
(workspace / "mock_server_config.json").write_text(json.dumps(mock_config, indent=2))

print("Workspace generated successfully.")
print(f"Task file: {workspace}/fetch_tasks.json")
print(f"URLs to fetch: {[item['url'] for item in urls_to_fetch]}")