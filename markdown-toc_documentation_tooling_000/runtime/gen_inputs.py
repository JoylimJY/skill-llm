import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── distractor directory tree ──────────────────────────────────────────────
dirs = [
    "docs/api",
    "docs/guides",
    "docs/internal",
    "src/core",
    "src/plugins",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "scripts",
    "configs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files (plain text, json, python) — no hints
distractor_files = {
    "docs/guides/quickstart.txt": "Follow steps 1-3 to get started.\nStep 1: Install.\nStep 2: Configure.\nStep 3: Run.",
    "docs/internal/meeting_notes.txt": "Q3 planning meeting notes.\nAction items: update wiki, review PRs.",
    "src/core/engine.py": "class Engine:\n    def run(self):\n        pass\n",
    "src/plugins/loader.py": "def load_plugin(name):\n    return None\n",
    "src/utils/helpers.py": "def slugify(s):\n    return s.lower().replace(' ', '-')\n",
    "tests/unit/test_engine.py": "def test_run():\n    assert True\n",
    "tests/integration/test_api.py": "def test_endpoint():\n    pass\n",
    "scripts/deploy.sh": "#!/bin/bash\necho 'deploying...'\n",
    "configs/settings.json": '{"version": "1.0", "debug": false}\n',
    "configs/logging.yaml": "level: INFO\nformat: json\n",
    "docs/api/changelog.txt": "v2.0.0 - breaking changes\nv1.9.0 - minor fixes\n",
}

for rel_path, content in distractor_files.items():
    (workspace / rel_path).write_text(content, encoding="utf-8")

# ── THE PRIMARY INPUT: a messy, realistic API reference doc ───────────────
api_reference = """\
# DataPulse API Reference

Some introductory prose about the DataPulse platform.

## Authentication

All requests require a bearer token.

### Token Endpoint

POST /auth/token

#### Request Parameters

| Field    | Type   | Required |
|----------|--------|----------|
| client_id | string | yes |
| secret    | string | yes |

#### Response Schema

```json
{
  "access_token": "...",
  "expires_in": 3600
}
```

### Refresh Tokens

Use the refresh endpoint to renew expiring tokens.

#### Refresh Request

POST /auth/refresh

## Endpoints

### Data Ingestion

Send telemetry data to the ingestion pipeline.

#### Request Body

```
## Example ingestion payload
POST /ingest
Content-Type: application/json

### Fields
- timestamp: ISO-8601
- value: float
```

#### Rate Limits

Requests are throttled at 1000/min per client.

### Data Retrieval

Query stored telemetry data.

#### Query Parameters

| Param  | Type   | Description        |
|--------|--------|--------------------|
| start  | string | Start timestamp    |
| end    | string | End timestamp      |
| metric | string | Metric name filter |

#### Response Format

```markdown
## Response Fields
### data (array)
#### items
##### timestamp
###### value
```

### Configuration

Manage runtime configuration via the Config API.

#### Get Configuration

GET /config/{key}

#### Update Configuration

PUT /config/{key}

### Configuration

A second section also named Configuration covering advanced options.

#### Advanced Options

Timeout, retry policies, and circuit-breaker settings.

##### Timeout Settings

Set per-request timeout in milliseconds.

###### Default Values

Default timeout is 5000ms.

## Webhooks

Register webhooks to receive push notifications.

### Webhook Registration

POST /webhooks

#### Payload Schema

```
# This is inside a code block
## Webhook fields
### event_type: string
```

### Webhook Events

List of supported event types.

#### Event Types Table

| Event         | Description              |
|---------------|--------------------------|
| data.received | New data point ingested  |
| config.updated| Configuration changed    |

## Error Codes

### Standard Errors

#### 4xx Client Errors

##### 400 Bad Request

Malformed JSON or missing required fields.

##### 401 Unauthorized

Invalid or expired token.

##### 429 Too Many Requests

Rate limit exceeded.

#### 5xx Server Errors

##### 500 Internal Server Error

Unexpected server failure.

## SDKs and Libraries

### Python SDK

Install via pip.

### JavaScript SDK

Install via npm.

### Go SDK

Available on pkg.go.dev.
"""

(workspace / "docs" / "api" / "api_reference.md").write_text(api_reference, encoding="utf-8")

# Also write a small decoy markdown file elsewhere to test contextual awareness
decoy_md = """\
# Old Notes

## Deprecated

This file is no longer maintained.

### Archive

See new docs.
"""
(workspace / "docs" / "internal" / "old_notes.md").write_text(decoy_md, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Primary file: {workspace / 'docs' / 'api' / 'api_reference.md'}")