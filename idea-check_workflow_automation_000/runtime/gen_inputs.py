import os
import random
import json

random.seed(42)

workspace = "/workspace"

# --- Create deeply nested distractor directory structure ---
dirs = [
    "src/api/v1",
    "src/api/v2",
    "src/core/analysis",
    "src/core/parsers",
    "src/utils/network",
    "src/utils/cache",
    "tests/unit",
    "tests/integration",
    "config/environments",
    "config/schemas",
    "docs/internal",
    "docs/external",
    "scripts/deploy",
    "scripts/ci",
    ".github/workflows",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "src/api/v1/routes.py": "# API routes for v1\nfrom flask import Blueprint\n\nv1 = Blueprint('v1', __name__)\n\n@v1.route('/health')\ndef health():\n    return {'status': 'ok'}\n",
    "src/api/v2/routes.py": "# API routes for v2\nfrom flask import Blueprint\n\nv2 = Blueprint('v2', __name__)\n\n@v2.route('/health')\ndef health():\n    return {'status': 'ok', 'version': '2'}\n",
    "src/core/analysis/market.py": "# Market analysis module\n\ndef analyze(data):\n    return {}\n",
    "src/core/parsers/json_parser.py": "import json\n\ndef parse(raw):\n    return json.loads(raw)\n",
    "src/utils/network/fetcher.py": "import requests\n\ndef fetch(url):\n    return requests.get(url).json()\n",
    "src/utils/cache/lru.py": "from collections import OrderedDict\n\nclass LRUCache:\n    def __init__(self, capacity):\n        self.cache = OrderedDict()\n        self.capacity = capacity\n",
    "tests/unit/test_parser.py": "import pytest\n\ndef test_parse():\n    assert True\n",
    "tests/integration/test_api.py": "import pytest\n\ndef test_health():\n    assert True\n",
    "config/environments/dev.json": json.dumps({"env": "development", "debug": True, "port": 5000}, indent=2),
    "config/environments/prod.json": json.dumps({"env": "production", "debug": False, "port": 8080}, indent=2),
    "config/schemas/idea_schema.json": json.dumps({
        "type": "object",
        "properties": {
            "idea_text": {"type": "string"},
            "depth": {"type": "string", "enum": ["quick", "deep"]}
        }
    }, indent=2),
    "docs/internal/architecture.md": "# Architecture\n\nThis document describes the internal architecture.\n\n## Components\n- API Layer\n- Core Engine\n- Storage\n",
    "docs/external/onboarding.md": "# Onboarding Guide\n\nWelcome to the platform.\n",
    "scripts/deploy/deploy.sh": "#!/bin/bash\necho 'Deploying...'\n",
    "scripts/ci/lint.sh": "#!/bin/bash\necho 'Running lint...'\n",
    ".github/workflows/ci.yml": "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n",
    "src/core/analysis/competitors.py": "# Competitor analysis - stub\n# TODO: integrate with external sources\n\ndef get_competitors(idea):\n    raise NotImplementedError('Not yet implemented')\n",
    "config/schemas/response_schema.json": json.dumps({
        "type": "object",
        "required": ["reality_signal", "evidence", "top_similars", "pivot_hints"],
        "properties": {
            "reality_signal": {"type": "number"},
            "evidence": {"type": "array"},
            "top_similars": {"type": "array"},
            "pivot_hints": {"type": "array"}
        }
    }, indent=2),
    "src/utils/network/mock_data.py": "# Old mock data - DO NOT USE\n# This file is deprecated\nMOCK_SIGNAL = 55\nMOCK_COMPETITORS = []\n",
    "docs/internal/signal_notes.txt": "# Internal notes on signal scoring\n# Values above 70 indicate high market saturation\n# Values 30-70 indicate moderate competition\n# Values below 30 indicate open space\n# NOTE: These are rough guidelines only, not final thresholds\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- Create the task input file ---
# This is the "business brief" the agent receives
task_brief = {
    "request_id": "PROD-2024-0847",
    "submitted_by": "sarah.chen@startupco.io",
    "timestamp": "2024-11-14T09:32:00Z",
    "idea": "Deep check: a CLI tool that automatically generates OpenAPI specifications from existing Python codebase comments and type hints",
    "context": "We are considering committing a full sprint to this. Need thorough scan before we invest engineering time.",
    "output_file": "idea_check_result.md"
}

with open(os.path.join(workspace, "task_brief.json"), "w") as f:
    json.dump(task_brief, f, indent=2)

print("Workspace generated successfully.")
print(f"Task brief written to {workspace}/task_brief.json")