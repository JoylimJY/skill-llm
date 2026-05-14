#!/bin/bash
set -e

# Start the mock open-notebook API server as a background process
cat > /tmp/mock_open_notebook_server.py << 'PYEOF'
import json
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory state
notebooks = {}
sources = {}
request_log = []

@app.route('/api/notebooks', methods=['POST'])
def create_notebook():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "missing name"}), 400
    nb_id = str(uuid.uuid4()).replace('-', '')[:16]
    notebook = {
        "id": nb_id,
        "name": data.get("name"),
        "description": data.get("description", ""),
        "created_at": "2024-03-15T10:00:00Z"
    }
    notebooks[nb_id] = notebook
    request_log.append({"endpoint": "/api/notebooks", "method": "POST", "body": data, "response_id": nb_id})
    return jsonify(notebook), 201

@app.route('/api/sources/json', methods=['POST'])
def add_source():
    data = request.get_json()
    if not data:
        return jsonify({"error": "no body"}), 400
    
    # Validate required fields per SKILL.md schema
    missing = []
    for field in ['content', 'notebook_id', 'type']:
        if field not in data:
            missing.append(field)
    
    if missing:
        return jsonify({"error": f"missing fields: {missing}"}), 400
    
    if data.get('type') != 'text':
        return jsonify({"error": "type must be 'text'"}), 400
    
    src_id = str(uuid.uuid4()).replace('-', '')[:12]
    source = {
        "id": src_id,
        "notebook_id": data.get("notebook_id"),
        "content": data.get("content"),
        "type": data.get("type"),
    }
    nb_id_raw = data.get("notebook_id", "").replace("notebook:", "")
    if nb_id_raw not in sources:
        sources[nb_id_raw] = []
    sources[nb_id_raw].append(source)
    request_log.append({"endpoint": "/api/sources/json", "method": "POST", "body": data})
    return jsonify(source), 201

@app.route('/api/search/ask', methods=['POST'])
def search_ask():
    data = request.get_json()
    if not data:
        return jsonify({"error": "no body"}), 400
    
    # Validate required fields per SKILL.md schema
    required = ['question', 'notebook_ids', 'strategy_model', 'answer_model', 'final_answer_model']
    missing = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"missing fields: {missing}"}), 400
    
    # notebook_ids must be an array
    if not isinstance(data.get('notebook_ids'), list):
        return jsonify({"error": "notebook_ids must be an array/list"}), 400
    
    # model fields must have 'model:' prefix
    for model_field in ['strategy_model', 'answer_model', 'final_answer_model']:
        val = data.get(model_field, "")
        if not val.startswith("model:"):
            return jsonify({"error": f"{model_field} must have 'model:' prefix"}), 400
    
    request_log.append({"endpoint": "/api/search/ask", "method": "POST", "body": data})
    
    answer = {
        "answer": "During cellular stress response, cells exhibit upregulation of HSP70 chaperone proteins and mitochondrial complex I subunits. Metabolic rewiring includes TCA cycle alterations with succinate and itaconate accumulation, alongside chromatin remodeling at AP-1 motifs in immune activation contexts.",
        "sources": [],
        "question": data.get("question")
    }
    return jsonify(answer), 200

@app.route('/api/debug/log', methods=['GET'])
def get_log():
    return jsonify(request_log), 200

@app.route('/api/debug/notebooks', methods=['GET'])
def get_notebooks():
    return jsonify(list(notebooks.values())), 200

@app.route('/api/debug/sources', methods=['GET'])
def get_sources():
    return jsonify(sources), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5055, debug=False)
PYEOF

python /tmp/mock_open_notebook_server.py &
MOCK_PID=$!
echo "Mock open-notebook server started with PID $MOCK_PID"

# Wait for server to be ready
for i in $(seq 1 15); do
    if curl -s http://localhost:5055/api/debug/log > /dev/null 2>&1; then
        echo "Mock server is ready."
        break
    fi
    echo "Waiting for server... attempt $i"
    sleep 1
done

# Write the SKILL.md to the workspace
mkdir -p /workspace
cat > /workspace/SKILL.md << 'MDEOF'
# Open Notebook Integration

A skill for integrating OpenClaw agents with open-notebook, a local AI research assistant (NotebookLM alternative).

## What It Does

- Connects your agent to open-notebook running locally
- Creates thematic notebooks for research, agent discovery, and personal knowledge
- Enables saving and querying knowledge across sessions (second brain for agents)
- Supports local Ollama models (free, no API costs)

## Prerequisites

1. **Install Docker Desktop** (required for open-notebook)
2. **Install Ollama** with a model (e.g., qwen3-4b-thinking-32k)
3. **Run open-notebook:**
   ```powershell
   docker compose -f docker-compose-host-ollama.yml up -d
   ```
   
   Or use the default compose:
   ```powershell
   docker compose up -d
   ```

## Setup

The skill expects open-notebook at:
- UI: http://localhost:8502
- API: http://localhost:5055

## Functions (INCLUDED)

This skill provides these PowerShell functions directly:

### Add-ToNotebook
```powershell
function Add-ToNotebook {
    param(
        [string]$Content,
        [string]$NotebookId = "YOUR_NOTEBOOK_ID"
    )
    $body = @{
        content = $Content
        notebook_id = $NotebookId
        type = "text"
    } | ConvertTo-Json
    Invoke-RestMethod -Uri "http://localhost:5055/api/sources/json" -Method Post -ContentType "application/json" -Body $body
}
```

### Search-Notebook
```powershell
function Search-Notebook {
    param(
        [string]$Query,
        [string]$NotebookId = "YOUR_NOTEBOOK_ID"
    )
    $body = @{
        question = $Query
        notebook_ids = @($NotebookId)
        strategy_model = "model:YOUR_MODEL_ID"
        answer_model = "model:YOUR_MODEL_ID"
        final_answer_model = "model:YOUR_MODEL_ID"
    } | ConvertTo-Json
    Invoke-RestMethod -Uri "http://localhost:5055/api/search/ask" -Method Post -ContentType "application/json" -Body $body
}
```

### New-Notebook
```powershell
function New-Notebook {
    param(
        [string]$Name,
        [string]$Description = ""
    )
    $body = @{
        name = $Name
        description = $Description
    } | ConvertTo-Json
    Invoke-RestMethod -Uri "http://localhost:5055/api/notebooks" -Method Post -ContentType "application/json" -Body $body
}
```

## Notebook IDs

After creating notebooks, update these variables in your scripts:

```powershell
$SIMULATION = "notebook:YOUR_SIMULATION_ID"
$CONSCIOUSNESS = "notebook:YOUR_CONSCIOUSNESS_ID"
$ENJAMBRE = "notebook:YOUR_ENJAMBRE_ID"
$OSIRIS = "notebook:YOUR_OSIRIS_ID"
$RESEARCH = "notebook:YOUR_RESEARCH_ID"
```

## Example Usage

```powershell
# Create a new notebook
New-Notebook -Name "My Research" -Description "Research notes"

# Save content
Add-ToNotebook -Content "This is my insight" -NotebookId "notebook:xxx"

# Query knowledge
$result = Search-Notebook -Query "What did I learn about X?" -NotebookId "notebook:xxx"
```

## Configuration Required

Before using, you MUST:
1. Run open-notebook with Docker
2. Create notebooks via the UI (http://localhost:8502) or API
3. Get your notebook IDs from the API response
4. Update the $NotebookId parameters in the functions

## Requirements

- Docker Desktop running
- Ollama with at least one model installed
- open-notebook containers running (SurrealDB + app)

## Troubleshooting

- If API fails, check containers: `docker ps`
- Check open-notebook logs: `docker compose logs`
- Verify Ollama is running: `curl http://localhost:11434/api/tags`

## Version

1.0.1 - Improved documentation, included function examples
MDEOF

echo "Setup complete."