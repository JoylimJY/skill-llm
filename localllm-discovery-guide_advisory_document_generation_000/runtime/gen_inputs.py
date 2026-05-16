import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create deeply nested distractor files ---

dirs = [
    "clients/indie_studio_zephyr/intake",
    "clients/indie_studio_zephyr/contracts",
    "clients/mobile_startup_nexus/intake",
    "clients/enterprise_logics/reports",
    "internal/templates/deprecated",
    "internal/templates/current",
    "internal/benchmarks/2023",
    "internal/benchmarks/2024_draft",
    "hardware_profiles/laptops",
    "hardware_profiles/workstations",
    "meeting_notes",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor 1: An old, unrelated client report
(workspace / "clients/enterprise_logics/reports/ai_strategy_q4.txt").write_text(
    "Q4 AI Strategy for Enterprise Logics\n"
    "Focus: cloud-based LLM APIs only.\n"
    "No local deployment considered at this stage.\n"
    "Budget: $200k/year for API calls.\n"
)

# Distractor 2: An internal deprecated template
(workspace / "internal/templates/deprecated/old_recommendation_format.md").write_text(
    "# Recommendation Format v0.2 (DEPRECATED)\n"
    "1. Executive Summary\n"
    "2. Technical Assessment\n"
    "3. Cost Analysis\n"
    "4. Do NOT use this template for local LLM clients.\n"
)

# Distractor 3: A competitor analysis file
(workspace / "internal/benchmarks/2024_draft/competitor_cloud_models.csv").write_text(
    "model,provider,cost_per_1M_tokens,latency_ms\n"
    "gpt-4o,openai,5.00,320\n"
    "claude-3-5-sonnet,anthropic,3.00,280\n"
    "gemini-1.5-pro,google,3.50,310\n"
)

# Distractor 4: A hardware profile for a different client
(workspace / "hardware_profiles/workstations/nexus_dev_rig.json").write_text(
    json.dumps({
        "client": "mobile_startup_nexus",
        "gpu": "RTX 4090",
        "vram_gb": 24,
        "ram_gb": 64,
        "cpu_cores": 24,
        "os": "Ubuntu 22.04",
        "notes": "High-end rig, already assessed."
    }, indent=2)
)

# Distractor 5: A laptop spec sheet
(workspace / "hardware_profiles/laptops/generic_ultrabook_spec.txt").write_text(
    "Generic Ultrabook Reference\n"
    "GPU: Intel Iris Xe (shared memory)\n"
    "RAM: 16GB LPDDR5\n"
    "CPU: 10 cores\n"
    "This config is CPU-only for local LLM purposes.\n"
)

# Distractor 6: Meeting notes
(workspace / "meeting_notes/2024_11_kickoff.txt").write_text(
    "Kickoff meeting - Zephyr Games Studio\n"
    "Attendees: Priya (lead dev), Marcus (AI advisor)\n"
    "Topics: local AI for code assist + NPC dialogue generation\n"
    "Action: Marcus to deliver written recommendation report.\n"
    "Next meeting: TBD after report delivery.\n"
)

# Distractor 7: A contracts placeholder
(workspace / "clients/indie_studio_zephyr/contracts/service_agreement_draft.txt").write_text(
    "SERVICE AGREEMENT - DRAFT\n"
    "Client: Zephyr Games Studio\n"
    "Scope: AI advisory services for local model deployment.\n"
    "Deliverable: One written hardware-specific recommendation report.\n"
    "[Signature blocks pending]\n"
)

# Distractor 8: An old benchmark doc
(workspace / "internal/benchmarks/2023/llm_perf_notes.txt").write_text(
    "2023 benchmark notes (OUTDATED)\n"
    "Models tested: llama-2-7b, mistral-7b\n"
    "These numbers are from mid-2023, do not cite in client reports.\n"
    "No benchmark numbers should be invented for reports.\n"
)

# Distractor 9: A current template note (deliberately incomplete/generic)
(workspace / "internal/templates/current/report_guidelines_stub.txt").write_text(
    "Report Guidelines - stub\n"
    "Author: internal team\n"
    "Status: INCOMPLETE - refer to skill documentation for full structure.\n"
    "Do not use this as the sole reference.\n"
)

# Distractor 10: Another client intake form (different client)
(workspace / "clients/mobile_startup_nexus/intake/hardware_form.json").write_text(
    json.dumps({
        "client": "mobile_startup_nexus",
        "primary_task": "mobile app code generation",
        "priority": "speed",
        "hardware_submitted": True
    }, indent=2)
)

# Distractor 11: A vague internal note
(workspace / "internal/benchmarks/2024_draft/notes_for_team.txt").write_text(
    "Reminder: always include final verification instructions in local LLM reports.\n"
    "Never guarantee compatibility without external check.\n"
    "Site to use: see skill documentation.\n"
)

# --- THE ACTUAL PROBLEM INPUT ---
# The real client intake file for Zephyr Games Studio
# This is the messy, real-world input the agent must process.
(workspace / "clients/indie_studio_zephyr/intake/zephyr_hardware_intake.json").write_text(
    json.dumps({
        "client_name": "Zephyr Games Studio",
        "contact": "Priya Nair (Lead Developer)",
        "submission_date": "2024-12-01",
        "hardware": {
            "gpu": "NVIDIA RTX 3060",
            "vram_gb": 12,
            "system_ram_gb": 32,
            "cpu_cores": 8,
            "os": "Windows 11"
        },
        "primary_tasks": ["coding assistance", "NPC dialogue writing"],
        "priorities": ["quality", "privacy"],
        "notes": "Priya wants to avoid cloud APIs for IP protection reasons. "
                 "She is not sure whether to start with a small model or go straight "
                 "to the largest model her hardware can handle. "
                 "Budget is limited so no hardware upgrades are planned right now."
    }, indent=2)
)

# The required output file location instruction is in the prompt only.
print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")