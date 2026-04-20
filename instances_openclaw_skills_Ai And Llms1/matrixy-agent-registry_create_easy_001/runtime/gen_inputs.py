from pathlib import Path
import json

agents = [
    {
        "name": "security-auditor",
        "description": "Analyzes code for security vulnerabilities",
        "keywords": ["security", "audit", "auth"],
        "marker": "AGENT_MARKER_SECURITY_7F3A"
    },
    {
        "name": "code-reviewer",
        "description": "General code review and best practices",
        "keywords": ["review", "quality", "style"],
        "marker": "AGENT_MARKER_REVIEW_19C2"
    },
    {
        "name": "test-writer",
        "description": "Creates tests and test plans",
        "keywords": ["tests", "qa", "coverage"],
        "marker": "AGENT_MARKER_TEST_4B81"
    }
]

Path("agents_input.json").write_text(json.dumps(agents, indent=2), encoding="utf-8")
Path("README.txt").write_text(
    "This workspace contains sample agent metadata.\n"
    "Each record includes a unique marker for verification.\n",
    encoding="utf-8"
)
