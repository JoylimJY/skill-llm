#!/usr/bin/env python3
"""
Generate a messy, realistic multi-agent workspace that violates governance rules.
The agent must reorganize everything and produce a governance_decisions.json.
"""

import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─────────────────────────────────────────────
# Directory structure (intentionally chaotic)
# ─────────────────────────────────────────────
dirs = [
    # Agent areas (private workspaces for agent-alpha and agent-beta)
    "agents/agent-alpha/workspace",
    "agents/agent-alpha/skills",
    "agents/agent-beta/workspace",
    "agents/agent-beta/skills",
    # Shared resources
    "shared/skills",
    "shared/scripts",
    "shared/knowledge",
    # Archive
    "archive/2023-q4",
    "archive/2024-q1",
    # Downloads (supposed to be intake)
    "downloads",
    # Projects
    "projects/nlp-pipeline",
    "projects/vision-eval",
    # Temp
    "tmp",
    # CHAOS: files dumped in wrong places (these are distractor/violation dirs)
    "shared/knowledge/downloads_dumped_here",
    "archive/2024-q1/active_edits",       # violation: editing inside archive
    "agents/agent-alpha/workspace/random_scripts",
]

for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# File definitions — each has intended metadata
# stored in a sidecar "mess_manifest.json" for
# the eval script to reference, but NOT exposed
# to the agent directly.
# ─────────────────────────────────────────────

files = []

# 1. A reusable utility script dumped in downloads (should → shared/scripts)
f = WORKSPACE / "downloads" / "normalize_text.sh"
f.write_text("#!/bin/bash\n# Normalize text files across agents\nsed 's/[[:space:]]*$//' \"$1\"\n")
files.append({
    "original_path": "downloads/normalize_text.sh",
    "description": "Reusable text normalization utility script intended for all agents",
    "correct_scope": "shared",
    "correct_lifecycle": "active",
    "correct_location_type": "shared scripts location",
    "shared_impact": "Yes — used by multiple agents"
})

# 2. Agent-alpha's private draft notes dumped in shared/knowledge (should → agents/agent-alpha/workspace)
f = WORKSPACE / "shared" / "knowledge" / "alpha_task_scratchpad.txt"
f.write_text("TODO: fix embedding pipeline\nNote to self: check vector dim mismatch\nTemp calc: 0.91 > 0.87 threshold\n")
files.append({
    "original_path": "shared/knowledge/alpha_task_scratchpad.txt",
    "description": "Agent-alpha's rough task notes, not yet worth sharing",
    "correct_scope": "agent-private",
    "correct_lifecycle": "active",
    "correct_location_type": "agent-alpha private workspace",
    "shared_impact": "No — private to agent-alpha"
})

# 3. A completed research report sitting in agent-beta's workspace (should → archive)
f = WORKSPACE / "agents" / "agent-beta" / "workspace" / "q1_benchmark_report_FINAL.md"
f.write_text("# Q1 Benchmark Report\n\nStatus: COMPLETED\nAll benchmarks concluded. No further edits expected.\n\nResults: Model A outperformed Model B by 12%.\n")
files.append({
    "original_path": "agents/agent-beta/workspace/q1_benchmark_report_FINAL.md",
    "description": "Completed, frozen benchmark report — no further edits expected",
    "correct_scope": "archive",
    "correct_lifecycle": "archived",
    "correct_location_type": "archive area",
    "shared_impact": "No — historical record only"
})

# 4. A shared skill file in agent-alpha's private skills (duplicate exists in shared/skills — private takes precedence)
f = WORKSPACE / "agents" / "agent-alpha" / "skills" / "data_loader.py"
f.write_text("# Agent-alpha override of data_loader\n# Uses custom batch size=16 for alpha's GPU config\ndef load(path): pass\n")
files.append({
    "original_path": "agents/agent-alpha/skills/data_loader.py",
    "description": "Agent-alpha-specific override skill — should stay agent-private, not be moved to shared",
    "correct_scope": "agent-private",
    "correct_lifecycle": "active",
    "correct_location_type": "agent-alpha private skills location",
    "shared_impact": "No — private override, collision precedence: agent-private wins"
})

# 5. A shared base skill dumped in downloads (should → shared/skills after intake)
f = WORKSPACE / "downloads" / "data_loader.py"
f.write_text("# Shared base data_loader skill\n# Default batch size=32\ndef load(path): pass\n")
files.append({
    "original_path": "downloads/data_loader.py",
    "description": "Shared base data_loader skill downloaded but not yet classified — must go through intake first, then to shared/skills",
    "correct_scope": "shared",
    "correct_lifecycle": "active",
    "correct_location_type": "shared skills location",
    "shared_impact": "Yes — used by multiple agents; agent-alpha has a private override"
})

# 6. A temporary scratch file in shared/knowledge (should → tmp or agent-private, not knowledge vault)
f = WORKSPACE / "shared" / "knowledge" / "downloads_dumped_here" / "temp_calc_scratch.txt"
f.write_text("scratch: 3*4=12, ignore\ntemp working numbers\nDELETE AFTER USE\n")
files.append({
    "original_path": "shared/knowledge/downloads_dumped_here/temp_calc_scratch.txt",
    "description": "Temporary scratch file incorrectly placed in knowledge vault",
    "correct_scope": "agent-private",
    "correct_lifecycle": "temporary",
    "correct_location_type": "agent private workspace or tmp — not knowledge vault",
    "shared_impact": "No"
})

# 7. A durable curated reference note in agent-alpha's workspace (should → shared/knowledge)
f = WORKSPACE / "agents" / "agent-alpha" / "workspace" / "llm_evaluation_guide.md"
f.write_text("# LLM Evaluation Best Practices\n\nCurated reference for all agents.\n\n- Use BLEU, ROUGE, BERTScore\n- Always normalize by length\n- Cross-validate on 3 seeds\n\nStatus: STABLE REFERENCE — do not delete\n")
files.append({
    "original_path": "agents/agent-alpha/workspace/llm_evaluation_guide.md",
    "description": "Durable curated reference guide meant for all agents — should be in knowledge vault",
    "correct_scope": "shared",
    "correct_lifecycle": "active",
    "correct_location_type": "shared knowledge/vault location",
    "shared_impact": "Yes — intended for all agents"
})

# 8. An archived project clone in projects/ being actively edited (should stay in projects but flag lifecycle)
f = WORKSPACE / "archive" / "2024-q1" / "active_edits" / "retrain_model.py"
f.write_text("# Retrain script — being edited INSIDE archive (violation!)\nimport torch\n# TODO: update learning rate\n")
files.append({
    "original_path": "archive/2024-q1/active_edits/retrain_model.py",
    "description": "Active script being edited inside archive — must be moved to active area before editing",
    "correct_scope": "agent-private",
    "correct_lifecycle": "active",
    "correct_location_type": "agent private workspace or projects — NOT archive",
    "shared_impact": "No — single agent task"
})

# 9. A throwaway repo clone in projects/ (should be in /tmp for throwaway work)
f = WORKSPACE / "projects" / "vision-eval" / "throwaway_clone" 
(WORKSPACE / "projects" / "vision-eval" / "throwaway_clone").mkdir(exist_ok=True)
g = WORKSPACE / "projects" / "vision-eval" / "throwaway_clone" / "main.py"
g.write_text("# Throwaway validation clone — DELETE AFTER TESTING\n# Not intended to persist\nprint('quick test')\n")
files.append({
    "original_path": "projects/vision-eval/throwaway_clone/main.py",
    "description": "Temporary throwaway clone for quick validation — should be in /tmp, not projects/",
    "correct_scope": "agent-private",
    "correct_lifecycle": "temporary",
    "correct_location_type": "tmp location — not projects root",
    "shared_impact": "No"
})

# 10. A download sitting in a project folder (should have been routed to intake/downloads first)
f = WORKSPACE / "projects" / "nlp-pipeline" / "pretrained_bert_weights.bin"
f.write_text("FAKE_BINARY_WEIGHTS_DATA_v2\n# Downloaded directly into project — violates intake rule\n")
files.append({
    "original_path": "projects/nlp-pipeline/pretrained_bert_weights.bin",
    "description": "Downloaded asset placed directly in project folder — should have been routed to downloads/intake first",
    "correct_scope": "shared",
    "correct_lifecycle": "active",
    "correct_location_type": "downloads/intake first, then appropriate long-term location",
    "shared_impact": "Yes — pretrained weights may be used by multiple agents"
})

# 11. Distractor: a perfectly placed shared script (already correct — agent should recognize it)
f = WORKSPACE / "shared" / "scripts" / "run_eval.sh"
f.write_text("#!/bin/bash\n# Shared evaluation runner\npython evaluate.py \"$@\"\n")
files.append({
    "original_path": "shared/scripts/run_eval.sh",
    "description": "Already correctly placed shared utility script — no move needed",
    "correct_scope": "shared",
    "correct_lifecycle": "active",
    "correct_location_type": "shared scripts location (already correct)",
    "shared_impact": "Yes — used by all agents"
})

# 12. Distractor: agent-beta's own task file correctly in their workspace
f = WORKSPACE / "agents" / "agent-beta" / "workspace" / "beta_current_task.txt"
f.write_text("Current task: evaluate GPT-4o on summarization\nStatus: IN PROGRESS\n")
files.append({
    "original_path": "agents/agent-beta/workspace/beta_current_task.txt",
    "description": "Agent-beta's own active task file — already correctly placed",
    "correct_scope": "agent-private",
    "correct_lifecycle": "active",
    "correct_location_type": "agent-beta private workspace (already correct)",
    "shared_impact": "No — private to agent-beta"
})

# 13. A random script scattered in alpha's workspace (should be in private scripts or project)
f = WORKSPACE / "agents" / "agent-alpha" / "workspace" / "random_scripts" / "fix_json.py"
f.write_text("import json, sys\n# Agent-alpha one-off fix script for a specific task\ndata = json.load(open(sys.argv[1]))\nprint(json.dumps(data, indent=2))\n")
files.append({
    "original_path": "agents/agent-alpha/workspace/random_scripts/fix_json.py",
    "description": "Agent-alpha task-specific one-off script — should stay in agent-alpha private area",
    "correct_scope": "agent-private",
    "correct_lifecycle": "active",
    "correct_location_type": "agent-alpha private scripts location",
    "shared_impact": "No — task-specific to agent-alpha"
})

# Save mess_manifest for eval script (hidden from agent view)
manifest = {
    "files": files,
    "workspace_root": str(WORKSPACE)
}
manifest_path = WORKSPACE / ".eval_manifest.json"
manifest_path.write_text(json.dumps(manifest, indent=2))
print(f"Generated {len(files)} files in messy workspace.")
print(f"Manifest saved to {manifest_path}")

# Print tree summary
for f_info in files:
    print(f"  [{f_info['correct_scope'].upper()}] {f_info['original_path']}")