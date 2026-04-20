from pathlib import Path
import json

workspace = Path('.')

marker = {
    "task_id": "mcp-demo-001",
    "marker_text": "OPENCLAW_MARKER_7f3c2a",
    "expected_server_id": "filesystem",
    "expected_mount_path": "/tmp"
}

(workspace / 'mcp_config.json').write_text(json.dumps({
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            "status": "active"
        }
    }
}, indent=2), encoding='utf-8')

(workspace / 'marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')

(workspace / 'notes.txt').write_text(
    "This workspace contains a deterministic marker for MCP setup verification.\n"
    "Marker: OPENCLAW_MARKER_7f3c2a\n"
    "Server: filesystem\n",
    encoding='utf-8'
)
