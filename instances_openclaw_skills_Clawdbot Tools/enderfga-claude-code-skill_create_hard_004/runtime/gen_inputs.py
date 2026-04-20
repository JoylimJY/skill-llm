from pathlib import Path
import json
import random

random.seed(1337)

workspace = Path('.')

# Marker files for deterministic evaluation
(workspace / 'mcp_config.json').write_text(json.dumps({
    'mcpServers': {
        'filesystem': {
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-filesystem', '/tmp'],
            'status': 'active'
        },
        'github': {
            'command': 'npx',
            'args': ['-y', '@modelcontextprotocol/server-github'],
            'env': {'GITHUB_TOKEN': 'your-token'},
            'status': 'active'
        }
    }
}, indent=2), encoding='utf-8')

(workspace / 'local_sessions.json').write_text(json.dumps([
    {'id': 'local-001', 'updatedAt': 1700000000, 'messages': [{'role': 'user', 'content': 'local marker alpha'}]},
    {'id': 'local-002', 'updatedAt': 1700000100, 'messages': [{'role': 'assistant', 'content': 'local marker beta'}]}
], indent=2), encoding='utf-8')

(workspace / 'remote_sessions.json').write_text(json.dumps([
    {'id': 'remote-001', 'updatedAt': 1700000050, 'messages': [{'role': 'user', 'content': 'remote marker gamma'}]},
    {'id': 'local-002', 'updatedAt': 1700000200, 'messages': [{'role': 'assistant', 'content': 'remote override delta'}]}
], indent=2), encoding='utf-8')

(workspace / 'state_seed.txt').write_text(
    'MCP_MARKER=OPENCLAW-CLAUDE-CODE-SKILL\nSESSION_MARKER=MERGE_TEST_42\nRANDOM_SEED=1337\n',
    encoding='utf-8'
)

(workspace / 'expected_tools.json').write_text(json.dumps({
    'expected_servers': ['filesystem', 'github'],
    'expected_markers': ['OPENCLAW-CLAUDE-CODE-SKILL', 'MERGE_TEST_42']
}, indent=2), encoding='utf-8')
