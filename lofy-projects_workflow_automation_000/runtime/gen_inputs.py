import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create realistic directory structure with distractor files
dirs = [
    "data",
    "logs",
    "notes",
    "clients/acme_corp",
    "clients/nova_labs",
    "clients/stealth_startup",
    "research/papers",
    "research/experiments",
    "job_search/applications",
    "job_search/prep",
    "scratch",
    "archives/2023",
    "archives/2024_q1",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "logs/build_errors.log": "ERROR: cuda not found\nWARNING: deprecated API call in model.py:42\n",
    "notes/random_ideas.txt": "- try transformer variant\n- ask about Q3 budget\n- fix docker compose issue\n",
    "clients/acme_corp/contract_v2.txt": "Contract terms: 40h/month, $150/hr. NDA signed 2024-01-15.\n",
    "clients/nova_labs/requirements_draft.txt": "Nova Labs MVP: real-time inference pipeline, latency < 200ms.\n",
    "clients/stealth_startup/nda.txt": "Confidential. Do not distribute.\n",
    "research/papers/reading_list.txt": "1. Attention is All You Need\n2. LoRA: Low-Rank Adaptation\n3. Mamba: Linear-Time SSMs\n",
    "research/experiments/baseline_results.csv": "model,accuracy,latency\ngpt2,0.82,45ms\nbert,0.79,30ms\n",
    "job_search/applications/tracker.txt": "Applied: Anthropic 2024-11-01, OpenAI 2024-10-20, Cohere 2024-11-10\n",
    "job_search/prep/system_design_notes.txt": "Study: distributed training, model serving, MLOps pipelines.\n",
    "scratch/temp_analysis.py": "# WIP analysis script\nimport pandas as pd\n# TODO: finish this\n",
    "archives/2023/old_projects.txt": "Archived: sentiment analyzer, CV pipeline (abandoned).\n",
    "archives/2024_q1/sprint_notes.txt": "Sprint 1: completed data ingestion. Sprint 2: stalled on auth.\n",
}
for path, content in distractor_files.items():
    (workspace / path).write_text(content)

# Compute dates relative to "now" for deterministic scoring
now = datetime(2025, 6, 15, 10, 0, 0)  # Fixed "now" for determinism

# Write the fixed now reference so eval can use it
(workspace / "data" / "eval_reference_time.txt").write_text(now.isoformat())

# Build messy, realistic projects.json
# Project scoring context (for eval):
# nova_inference: deadline in 1 day (urgency=4), job_relevance=high(4), last_updated 2 days ago (momentum=2), energy=2
# acme_dashboard: deadline in 5 days (urgency=3), job_relevance=medium(3), last_updated 10 days ago (momentum=1), energy=1
# research_paper: no deadline (urgency=1), job_relevance=high(4), last_updated 20 days ago (momentum=0), energy=1
# job_portfolio: deadline in 3 days (urgency=3), job_relevance=critical(5), last_updated 1 day ago (momentum=2), energy=2
# stealth_mvp: backlog (urgency=0), job_relevance=none(0), last_updated 30 days ago (momentum=0), energy=0

projects_data = {
    "projects": {
        "nova_inference": {
            "name": "Nova Labs Inference Pipeline",
            "status": "active",
            "phase": "Implementation",
            "description": "Real-time ML inference service for Nova Labs, targeting sub-200ms latency.",
            "stack": ["Python", "FastAPI", "ONNX", "Redis"],
            "milestones": [
                {"name": "Model conversion to ONNX", "status": "completed", "target_date": "2025-06-01"},
                {"name": "API endpoint implementation", "status": "in_progress", "target_date": "2025-06-16"},
                {"name": "Load testing and optimization", "status": "not_started", "target_date": "2025-06-20"},
            ],
            "blockers": ["Redis connection pooling causing memory spikes under load"],
            "next_actions": ["Fix Redis pool config", "Write load test script"],
            "time_log": [
                {"date": "2025-06-13", "hours": 3, "note": "Implemented ONNX conversion pipeline"},
                {"date": "2025-06-12", "hours": 2, "note": "Set up FastAPI skeleton"},
            ],
            "last_updated": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            "job_relevance": "high"
        },
        "acme_dashboard": {
            "name": "Acme Corp Analytics Dashboard",
            "status": "active",
            "phase": "Frontend Integration",
            "description": "Data visualization dashboard for Acme Corp internal metrics.",
            "stack": ["React", "D3.js", "PostgreSQL"],
            "milestones": [
                {"name": "Backend API complete", "status": "completed", "target_date": "2025-05-30"},
                {"name": "Chart components built", "status": "in_progress", "target_date": "2025-06-20"},
                {"name": "Client review session", "status": "not_started", "target_date": "2025-06-25"},
            ],
            "blockers": [],
            "next_actions": ["Complete time-series chart", "Polish UI"],
            "time_log": [
                {"date": "2025-06-04", "hours": 4, "note": "Built bar chart component"},
                {"date": "2025-06-05", "hours": 2, "note": "API integration for dashboard"},
            ],
            "last_updated": (now - timedelta(days=10)).strftime("%Y-%m-%d"),
            "job_relevance": "medium"
        },
        "research_paper": {
            "name": "LoRA Fine-Tuning Research Paper",
            "status": "active",
            "phase": "Writing",
            "description": "Academic paper on efficient LoRA fine-tuning strategies for domain adaptation.",
            "stack": ["Python", "PyTorch", "LaTeX"],
            "milestones": [
                {"name": "Experiments complete", "status": "completed", "target_date": "2025-05-15"},
                {"name": "Draft introduction and related work", "status": "in_progress", "target_date": None},
                {"name": "Submit to arXiv", "status": "not_started", "target_date": None},
            ],
            "blockers": ["Co-author hasn't responded to outline feedback in 2 weeks"],
            "next_actions": ["Write methodology section", "Chase co-author"],
            "time_log": [
                {"date": "2025-05-25", "hours": 5, "note": "Completed ablation experiments"},
                {"date": "2025-05-26", "hours": 2, "note": "Started introduction draft"},
            ],
            "last_updated": (now - timedelta(days=20)).strftime("%Y-%m-%d"),
            "job_relevance": "high"
        },
        "job_portfolio": {
            "name": "ML Engineer Portfolio Site",
            "status": "active",
            "phase": "Content",
            "description": "Personal portfolio site showcasing ML projects for job applications.",
            "stack": ["Next.js", "Tailwind", "Vercel"],
            "milestones": [
                {"name": "Site scaffolding", "status": "completed", "target_date": "2025-06-10"},
                {"name": "Project case studies written", "status": "in_progress", "target_date": "2025-06-18"},
                {"name": "Deploy and share with recruiters", "status": "not_started", "target_date": "2025-06-18"},
            ],
            "blockers": [],
            "next_actions": ["Write Nova Labs case study", "Add resume PDF link"],
            "time_log": [
                {"date": "2025-06-14", "hours": 2, "note": "Finished site scaffolding and layout"},
            ],
            "last_updated": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "job_relevance": "critical"
        },
        "stealth_mvp": {
            "name": "Stealth Startup MVP Prototype",
            "status": "backlog",
            "phase": "Ideation",
            "description": "Exploratory prototype for a stealth startup concept. Deprioritized pending funding confirmation.",
            "stack": [],
            "milestones": [
                {"name": "Define MVP scope", "status": "not_started", "target_date": None},
            ],
            "blockers": ["Waiting for founder to confirm budget"],
            "next_actions": [],
            "time_log": [],
            "last_updated": (now - timedelta(days=30)).strftime("%Y-%m-%d"),
            "job_relevance": "none"
        }
    },
    "academic": {
        "graduation": None,
        "deadlines": [
            {"name": "Portfolio site live", "date": "2025-06-18", "project": "job_portfolio"},
            {"name": "Nova Labs delivery", "date": "2025-06-16", "project": "nova_inference"},
        ],
        "meetings": [
            {"name": "Nova Labs weekly sync", "date": "2025-06-17", "time": "14:00", "project": "nova_inference"},
            {"name": "Acme Corp review", "date": "2025-06-20", "time": "11:00", "project": "acme_dashboard"},
        ]
    }
}

(workspace / "data" / "projects.json").write_text(
    json.dumps(projects_data, indent=2)
)

# Activity notes — messy natural language updates the agent must parse
activity_notes_content = """Project Activity Notes — Week of June 15, 2025
================================================

[June 14, 2025]
- Worked on job_portfolio for 1.5 hours — added project thumbnails and improved mobile layout.
- The "Project case studies written" milestone for job_portfolio is now done, completed it today.

[June 15, 2025 — this morning]
- Spent 2 hours on nova_inference debugging the Redis memory issue — the Redis connection pooling bug is now fixed and resolved.
- Also worked 30 minutes reviewing the load testing approach for nova_inference.

Note: I currently have about 90 minutes of focused energy available for today's main work session.
"""

(workspace / "notes" / "activity_notes.txt").write_text(activity_notes_content)

# Additional distractor: an old stale report from a previous run (wrong format, should NOT be used)
old_report = {
    "generated": "2025-03-01",
    "top_pick": "stealth_mvp",
    "note": "This is an outdated report, ignore."
}
(workspace / "data" / "old_priority_report.json").write_text(json.dumps(old_report, indent=2))

# A misleading scores file with wrong weights (trap for agents that don't read the skill)
wrong_scores = {
    "note": "Draft scoring attempt — weights might be wrong",
    "nova_inference": {"score": 14, "urgency": 4, "job_relevance": 4},
    "job_portfolio": {"score": 12},
}
(workspace / "scratch" / "draft_scores.json").write_text(json.dumps(wrong_scores, indent=2))

print("Workspace generated successfully.")
print(f"Reference time: {now.isoformat()}")