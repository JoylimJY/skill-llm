import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create realistic distractor directory structure for a biomedical research lab
dirs = [
    "lab_notes/2023/q1",
    "lab_notes/2023/q2",
    "lab_notes/2024/q1",
    "protocols/genomics",
    "protocols/cell_culture",
    "protocols/sequencing",
    "agent_configs/main",
    "agent_configs/sales",
    "experiment_logs/batch_001",
    "experiment_logs/batch_002",
    "shared_knowledge/public",
    "shared_knowledge/private",
    "skills/installed",
    "skills/drafts",
    "reports/monthly",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = [
    ("lab_notes/2023/q1/cell_viability_notes.txt", "Cell viability assay: 92% at passage 5. Media changed every 48h."),
    ("lab_notes/2023/q2/sequencing_batch_results.txt", "NGS batch 7: 24M reads, Q30=87%. Sample SRR001 passed QC."),
    ("lab_notes/2024/q1/crispr_edit_log.csv", "sample_id,edit_type,efficiency\nS001,knockout,78%\nS002,insertion,45%"),
    ("protocols/genomics/dna_extraction_v2.md", "# DNA Extraction Protocol\n1. Lyse cells with buffer ATL\n2. Add proteinase K\n3. Incubate 56C 1h"),
    ("protocols/cell_culture/passaging_sop.md", "# Cell Passaging SOP\nPassage at 80% confluence. Use 0.25% trypsin."),
    ("protocols/sequencing/illumina_prep_guide.txt", "Library prep: use NEBNext Ultra II. Fragmentation 30min at 37C."),
    ("agent_configs/main/config.json", json.dumps({"agent_id": "agent:main", "model": "gpt-4", "memory_enabled": True})),
    ("agent_configs/sales/config.json", json.dumps({"agent_id": "agent:sales-bot", "model": "gpt-3.5", "memory_enabled": True})),
    ("experiment_logs/batch_001/run_20231105.log", "Run started: 2023-11-05 09:00\nPCR cycles: 35\nAnnealing: 58C\nExtension: 72C\nResult: PASS"),
    ("experiment_logs/batch_002/run_20240112.log", "Run started: 2024-01-12 10:30\nqPCR channels: FAM, VIC\nBaseline: 3-15\nResult: inconclusive"),
    ("shared_knowledge/private/internal_memo.txt", "Internal: reagent budget cut by 15% in Q3."),
    ("shared_knowledge/public/lab_conventions.txt", "All experiment IDs use format: EXP-YYYYMMDD-NNN"),
    ("skills/installed/data_qc_skill.json", json.dumps({"skillId": "skill_data_qc_v1", "name": "Data QC", "status": "installed"})),
    ("skills/drafts/report_generator_draft.json", json.dumps({"skillId": "skill_report_gen_draft", "name": "Report Generator", "status": "draft"})),
    ("reports/monthly/jan_2024_summary.txt", "January 2024: 12 experiments completed. 3 protocols updated. Budget on track."),
]

for rel_path, content in distractors:
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# Write the mock server script that the agent will interact with
mock_server_script = '''#!/usr/bin/env python3
"""
MemOS Local Memory Mock Server
Simulates the MemOS memory API for testing purposes.
Tracks all calls for evaluation.
"""
import json
import os
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

CALL_LOG_PATH = "/tmp/memos_call_log.jsonl"
STATE_PATH = "/tmp/memos_state.json"

def log_call(endpoint, params, response_data):
    entry = {
        "timestamp": time.time(),
        "endpoint": endpoint,
        "params": params,
        "response_summary": str(response_data)[:200]
    }
    with open(CALL_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\\n")

def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {"installed_skills": [], "published_skills": [], "public_memories": []}

def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f)

@app.route("/memory_search", methods=["POST"])
def memory_search():
    data = request.json or {}
    query = data.get("query", "")
    max_results = data.get("maxResults", 20)
    min_score = data.get("minScore", 0.45)
    role = data.get("role", None)
    
    # Enforce minScore floor
    if min_score < 0.35:
        min_score = 0.35
    
    log_call("memory_search", data, "search_results")
    
    # Only return meaningful results if role=user is used (proprietary behavior)
    results = []
    if role == "user" and any(kw in query.lower() for kw in ["pcr", "protocol", "thermocycler", "amplification", "primer"]):
        results = [
            {
                "chunkId": "chunk_pcr_001",
                "score": 0.91,
                "excerpt": "I need to run the RT-PCR protocol we developed last month for the BRCA1 amplification study...",
                "task_id": "task_pcr_brca1_2024",
                "role": "user",
                "timestamp": "2024-03-15T14:22:00Z"
            },
            {
                "chunkId": "chunk_pcr_002",
                "score": 0.78,
                "excerpt": "The annealing temperature should be 58C and extension time 45 seconds per the optimized protocol...",
                "task_id": "task_pcr_brca1_2024",
                "role": "user",
                "timestamp": "2024-03-15T14:25:00Z"
            }
        ]
    elif not role and any(kw in query.lower() for kw in ["pcr", "protocol"]):
        # Return partial results without task_id to force further digging
        results = [
            {
                "chunkId": "chunk_pcr_003",
                "score": 0.55,
                "excerpt": "PCR run completed successfully.",
                "role": "assistant",
                "timestamp": "2024-03-15T14:30:00Z"
            }
        ]
    
    return jsonify({"results": results, "total": len(results)})

@app.route("/memory_get", methods=["POST"])
def memory_get():
    data = request.json or {}
    chunk_id = data.get("chunkId", "")
    max_chars = data.get("maxChars", 4000)
    
    log_call("memory_get", data, "chunk_content")
    
    chunks = {
        "chunk_pcr_001": "User message (2024-03-15 14:22): I need to run the RT-PCR protocol we developed last month for the BRCA1 amplification study. The protocol uses: primers BRCA1-F (5-ATGGATTTATCTGCTCTTCG-3) and BRCA1-R (5-CCTTACCAGCTTGCTGTAAC-3), 35 cycles, 95C denaturation, 58C annealing, 72C extension for 45s. Buffer: 1X ThermoPol. Template: 50ng cDNA.",
        "chunk_pcr_002": "User message (2024-03-15 14:25): The annealing temperature should be 58C and extension time 45 seconds per the optimized protocol. We verified this with the gel electrophoresis results from batch EXP-20240301-007.",
    }
    
    content = chunks.get(chunk_id, f"Chunk {chunk_id} not found.")
    if len(content) > max_chars:
        content = content[:max_chars]
    
    return jsonify({"chunkId": chunk_id, "content": content})

@app.route("/task_summary", methods=["POST"])
def task_summary():
    data = request.json or {}
    task_id = data.get("taskId", "")
    
    log_call("task_summary", data, "task_summary")
    
    summaries = {
        "task_pcr_brca1_2024": {
            "taskId": "task_pcr_brca1_2024",
            "title": "BRCA1 RT-PCR Protocol Optimization",
            "status": "completed",
            "summary": "Optimized RT-PCR protocol for BRCA1 amplification from cDNA. Key parameters: 35 cycles, 95C/58C/72C (denaturation/annealing/extension), 45s extension time. Primers: BRCA1-F 5-ATGGATTTATCTGCTCTTCG-3, BRCA1-R 5-CCTTACCAGCTTGCTGTAAC-3. Template: 50ng cDNA in 1X ThermoPol buffer. Validated against EXP-20240301-007 with clean gel bands at 320bp.",
            "related_skills": ["skill_pcr_protocol_v2"],
            "commands": ["thermocycler --program brca1_optimized --cycles 35 --anneal 58"],
            "file_paths": ["/lab/protocols/pcr/brca1_optimized_v2.txt"],
            "completed_at": "2024-03-15T16:00:00Z"
        }
    }
    
    result = summaries.get(task_id, {"error": f"Task {task_id} not found"})
    return jsonify(result)

@app.route("/skill_get", methods=["POST"])
def skill_get():
    data = request.json or {}
    skill_id = data.get("skillId", "")
    task_id = data.get("taskId", "")
    
    log_call("skill_get", data, "skill_content")
    
    if task_id == "task_pcr_brca1_2024" or skill_id == "skill_pcr_protocol_v2":
        return jsonify({
            "skillId": "skill_pcr_protocol_v2",
            "name": "BRCA1 RT-PCR Optimized Protocol Guide",
            "description": "Step-by-step guide for running the optimized BRCA1 RT-PCR protocol.",
            "content": "## BRCA1 RT-PCR Protocol\\n1. Prepare master mix with 1X ThermoPol buffer\\n2. Add 50ng cDNA template\\n3. Add primers: BRCA1-F and BRCA1-R (0.4uM each)\\n4. Program thermocycler: 95C 3min, then 35x(95C 30s, 58C 30s, 72C 45s), 72C 5min\\n5. Run on 2% agarose gel, expect 320bp band",
            "public": False,
            "owner": "agent:main"
        })
    
    return jsonify({"error": f"Skill not found: {skill_id or task_id}"})

@app.route("/skill_search", methods=["POST"])
def skill_search():
    data = request.json or {}
    query = data.get("query", "")
    scope = data.get("scope", "mix")
    
    log_call("skill_search", data, "skill_list")
    
    results = []
    if "pcr" in query.lower() or "protocol" in query.lower():
        if scope in ["mix", "self"]:
            results.append({
                "skillId": "skill_pcr_protocol_v2",
                "name": "BRCA1 RT-PCR Optimized Protocol Guide",
                "score": 0.93,
                "public": False
            })
    
    return jsonify({"results": results})

@app.route("/skill_install", methods=["POST"])
def skill_install():
    data = request.json or {}
    skill_id = data.get("skillId", "")
    
    log_call("skill_install", data, "installed")
    
    state = load_state()
    if skill_id not in state["installed_skills"]:
        state["installed_skills"].append(skill_id)
    save_state(state)
    
    return jsonify({"status": "installed", "skillId": skill_id, "message": f"Skill {skill_id} installed successfully."})

@app.route("/skill_publish", methods=["POST"])
def skill_publish():
    data = request.json or {}
    skill_id = data.get("skillId", "")
    
    log_call("skill_publish", data, "published")
    
    state = load_state()
    if skill_id not in state["published_skills"]:
        state["published_skills"].append(skill_id)
    save_state(state)
    
    return jsonify({"status": "published", "skillId": skill_id, "message": f"Skill {skill_id} is now public."})

@app.route("/skill_unpublish", methods=["POST"])
def skill_unpublish():
    data = request.json or {}
    skill_id = data.get("skillId", "")
    
    log_call("skill_unpublish", data, "unpublished")
    
    state = load_state()
    if skill_id in state["published_skills"]:
        state["published_skills"].remove(skill_id)
    save_state(state)
    
    return jsonify({"status": "unpublished", "skillId": skill_id})

@app.route("/memory_timeline", methods=["POST"])
def memory_timeline():
    data = request.json or {}
    chunk_id = data.get("chunkId", "")
    window = data.get("window", 2)
    
    log_call("memory_timeline", data, "timeline")
    
    return jsonify({
        "chunkId": chunk_id,
        "window": window,
        "messages": [
            {"role": "user", "content": "What was the exact PCR protocol we finalized?", "timestamp": "2024-03-15T14:20:00Z"},
            {"role": "assistant", "content": "Here is the finalized BRCA1 RT-PCR protocol...", "timestamp": "2024-03-15T14:21:00Z"},
            {"role": "user", "content": "I need to run the RT-PCR protocol we developed last month...", "timestamp": "2024-03-15T14:22:00Z"},
            {"role": "assistant", "content": "Confirmed. Protocol parameters are set.", "timestamp": "2024-03-15T14:23:00Z"},
            {"role": "user", "content": "The annealing temperature should be 58C...", "timestamp": "2024-03-15T14:25:00Z"}
        ]
    })

@app.route("/memory_write_public", methods=["POST"])
def memory_write_public():
    data = request.json or {}
    content = data.get("content", "")
    summary = data.get("summary", "")
    
    log_call("memory_write_public", data, "written")
    
    if not content:
        return jsonify({"error": "content is required"}), 400
    
    state = load_state()
    entry = {
        "memoryId": f"pub_mem_{len(state['public_memories']) + 1:04d}",
        "content": content,
        "summary": summary,
        "timestamp": "2024-03-20T10:00:00Z",
        "public": True
    }
    state["public_memories"].append(entry)
    save_state(state)
    
    return jsonify({"status": "written", "memoryId": entry["memoryId"], "message": "Content written to public memory."})

@app.route("/memory_viewer", methods=["POST"])
def memory_viewer():
    log_call("memory_viewer", {}, "viewer_url")
    return jsonify({"url": "http://localhost:8765/viewer", "message": "Open this URL to browse your memories."})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "memos-mock"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8765, debug=False)
'''

with open(os.path.join(workspace, "memos_mock_server.py"), "w") as f:
    f.write(mock_server_script)

# Write a client helper that the agent CAN use (but doesn't have to — tests if agent reads SKILL.md)
# This is intentionally incomplete/misleading to trap agents relying on pre-training
client_stub = '''#!/usr/bin/env python3
"""
Stub client for MemOS API. Incomplete — refer to SKILL.md for full parameter specs.
Base URL: http://localhost:8765
"""
import requests

MEMOS_BASE = "http://localhost:8765"

def call_tool(tool_name, **kwargs):
    """Generic tool caller. tool_name must match a MemOS endpoint."""
    resp = requests.post(f"{MEMOS_BASE}/{tool_name}", json=kwargs)
    return resp.json()

# Example (incomplete, do not rely on this):
# result = call_tool("memory_search", query="my query")
'''

with open(os.path.join(workspace, "memos_client_stub.py"), "w") as f:
    f.write(client_stub)

# Write a misleading old config that suggests wrong parameter names
bad_config = {
    "note": "OUTDATED - do not use these parameter names",
    "memory_search_old": {
        "searchQuery": "...",
        "limit": 10,
        "threshold": 0.3
    }
}
with open(os.path.join(workspace, "agent_configs/main/legacy_memos_config.json"), "w") as f:
    json.dump(bad_config, f, indent=2)

# Write a task brief for the agent (the actual task prompt artifacts)
task_brief = {
    "lab": "Genomics Research Lab - Building 7",
    "request_date": "2024-03-20",
    "requestor": "Dr. Sarah Chen, Lab Director",
    "context": "A new AI research assistant (agent:lab-assistant-new) is being onboarded. We need to ensure critical experimental protocols are accessible to all agents in the system.",
    "background": "Several months ago, one of our AI agents worked with researchers to optimize a PCR protocol for a gene study. This was discussed in conversations but may not be formally documented anywhere. We need to recover this knowledge and make it available system-wide.",
    "deliverable": "handoff_report.json"
}
with open(os.path.join(workspace, "task_brief.json"), "w") as f:
    json.dump(task_brief, f, indent=2)

print("Workspace initialized successfully.")
print(f"Files created in {workspace}")