import json
from pathlib import Path

root = Path('.')

sample = {
    "marker": "OPENCLAW_DETERMINISTIC_MARKER_7F3A",
    "workspace_name": "openclaw-demo",
    "session_seed": 1729,
    "servers": [
        {"id": "filesystem", "status": "active", "path": "/tmp"},
        {"id": "github", "status": "active", "path": "github-token-needed"}
    ],
    "notes": [
        "Use local filesystem MCP for file operations.",
        "Use timestamp-based merge semantics for sessions and configs."
    ]
}

(root / 'seed_data.json').write_text(json.dumps(sample, indent=2, sort_keys=True), encoding='utf-8')
(root / 'source_note.txt').write_text(
    'MARKER: OPENCLAW_DETERMINISTIC_MARKER_7F3A\n'
    'This workspace is for MCP configuration and session persistence demos.\n',
    encoding='utf-8'
)
(root / 'expected_config_template.json').write_text(
    json.dumps({
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                "status": "active"
            },
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_TOKEN": "your-token"},
                "status": "active"
            }
        }
    }, indent=2, sort_keys=True),
    encoding='utf-8'
)
