import os
import json
import yaml
import hashlib
from pathlib import Path

# Fixed seed for determinism
import random
random.seed(42)

workspace = Path("/workspace")

# ── 1.  Skill directory structure (simulates the AgentBench skill install) ──────

skill_dir = workspace / "agentbench-skill"
skill_dir.mkdir(parents=True, exist_ok=True)

# skill.json  — agent MUST read suite_version from here
skill_json = {
    "name": "agentbench",
    "version": "1.2.0",
    "suite_version": "2.3.1",
    "platform": "openclaw",
    "description": "AgentBench skill for OpenClaw"
}
(skill_dir / "skill.json").write_text(json.dumps(skill_json, indent=2))

# ── 2.  Tasks directory ──────────────────────────────────────────────────────────
tasks_dir = skill_dir / "tasks"

# ---------- Suite: research (3 tasks: easy, medium, hard) ----------
research_dir = tasks_dir / "research"

# research/quick-summary  [easy]
t1 = research_dir / "quick-summary"
(t1 / "inputs").mkdir(parents=True, exist_ok=True)
(t1 / "inputs" / "raw_notes.txt").write_text(
    "Meeting notes from Q3 review:\n"
    "- Revenue up 12% YoY\n"
    "- Customer churn at 4.2%\n"
    "- Three new hires in engineering\n"
    "- Product roadmap delayed by 6 weeks\n"
    "- Marketing spend increased 30%\n"
)
task1_yaml = {
    "id": "research-quick-summary",
    "name": "Quick Research Summary",
    "suite": "research",
    "difficulty": "easy",
    "mode": "sandboxed",
    "user_message": (
        "Read the file raw_notes.txt in the workspace. "
        "Write a summary report to summary.txt that includes: "
        "a section called 'Key Findings', a section called 'Revenue', "
        "and a section called 'Risks'. The report should be between 80 and 200 words."
    ),
    "input_files": ["raw_notes.txt"],
    "expected_outputs": [
        {
            "type": "file-exists",
            "file": "summary.txt",
            "points": 30
        },
        {
            "type": "content-contains",
            "file": "summary.txt",
            "sections": ["Key Findings", "Revenue", "Risks"],
            "points": 40
        },
        {
            "type": "word-count-range",
            "file": "summary.txt",
            "min": 80,
            "max": 200,
            "points": 30
        }
    ],
    "expected_metrics": {
        "tool_calls_range": [2, 8],
        "planning_ratio_range": [0.2, 0.6]
    },
    "scoring_weights": {
        "l0": 0.20,
        "l1": 0.35,
        "l2": 0.20,
        "l3": 0.25
    }
}
(t1 / "task.yaml").write_text(yaml.dump(task1_yaml, default_flow_style=False))

# research/market-analysis  [medium]
t2 = research_dir / "market-analysis"
(t2 / "inputs").mkdir(parents=True, exist_ok=True)
(t2 / "inputs" / "market_data.csv").write_text(
    "region,q1_sales,q2_sales,q3_sales\n"
    "APAC,120000,135000,142000\n"
    "EMEA,98000,102000,99000\n"
    "AMER,210000,225000,231000\n"
    "LATAM,45000,48000,52000\n"
)
task2_yaml = {
    "id": "research-market-analysis",
    "name": "Market Analysis Report",
    "suite": "research",
    "difficulty": "medium",
    "mode": "sandboxed",
    "user_message": (
        "Analyze the market_data.csv file in the workspace. "
        "Produce a markdown report called analysis.md that includes sections: "
        "'Executive Summary', 'Regional Performance', 'Trends', and 'Recommendations'. "
        "The report must be between 150 and 400 words."
    ),
    "input_files": ["market_data.csv"],
    "expected_outputs": [
        {
            "type": "file-exists",
            "file": "analysis.md",
            "points": 30
        },
        {
            "type": "content-contains",
            "file": "analysis.md",
            "sections": ["Executive Summary", "Regional Performance", "Trends", "Recommendations"],
            "points": 40
        },
        {
            "type": "word-count-range",
            "file": "analysis.md",
            "min": 150,
            "max": 400,
            "points": 30
        }
    ],
    "expected_metrics": {
        "tool_calls_range": [3, 10],
        "planning_ratio_range": [0.25, 0.65]
    },
    "scoring_weights": {
        "l0": 0.20,
        "l1": 0.35,
        "l2": 0.20,
        "l3": 0.25
    }
}
(t2 / "task.yaml").write_text(yaml.dump(task2_yaml, default_flow_style=False))

# research/deep-competitive-intel  [hard]  — excluded by --fast
t3 = research_dir / "deep-competitive-intel"
(t3 / "inputs").mkdir(parents=True, exist_ok=True)
(t3 / "inputs" / "competitors.json").write_text(json.dumps({
    "companies": ["AlphaCorp", "BetaSoft", "GammaAI"],
    "metrics": {"AlphaCorp": {"mrr": 2100000}, "BetaSoft": {"mrr": 980000}, "GammaAI": {"mrr": 3400000}}
}, indent=2))
task3_yaml = {
    "id": "research-deep-competitive-intel",
    "name": "Deep Competitive Intelligence",
    "suite": "research",
    "difficulty": "hard",
    "mode": "sandboxed",
    "user_message": (
        "Using competitors.json in the workspace, produce a comprehensive competitive "
        "intelligence brief called competitive_brief.md. Include sections: 'Overview', "
        "'Competitive Landscape', 'Threat Assessment', 'Strategic Recommendations', "
        "and 'Conclusion'. Minimum 400 words."
    ),
    "input_files": ["competitors.json"],
    "expected_outputs": [
        {
            "type": "file-exists",
            "file": "competitive_brief.md",
            "points": 30
        },
        {
            "type": "content-contains",
            "file": "competitive_brief.md",
            "sections": ["Overview", "Competitive Landscape", "Threat Assessment"],
            "points": 40
        },
        {
            "type": "word-count-range",
            "file": "competitive_brief.md",
            "min": 400,
            "max": 2000,
            "points": 30
        }
    ],
    "expected_metrics": {
        "tool_calls_range": [5, 20],
        "planning_ratio_range": [0.3, 0.7]
    },
    "scoring_weights": {
        "l0": 0.20,
        "l1": 0.35,
        "l2": 0.20,
        "l3": 0.25
    }
}
(t3 / "task.yaml").write_text(yaml.dump(task3_yaml, default_flow_style=False))

# ---------- Suite: file-creation (3 tasks: easy, medium, hard) ----------
fc_dir = tasks_dir / "file-creation"

# file-creation/project-scaffold  [easy]
t4 = fc_dir / "project-scaffold"
t4.mkdir(parents=True, exist_ok=True)
task4_yaml = {
    "id": "fc-project-scaffold",
    "name": "Project Scaffold",
    "suite": "file-creation",
    "difficulty": "easy",
    "mode": "sandboxed",
    "user_message": (
        "Create a Python project scaffold in the workspace with the following structure: "
        "src/main.py, src/utils.py, tests/test_main.py, README.md, requirements.txt. "
        "Each file should have basic placeholder content."
    ),
    "input_files": [],
    "expected_outputs": [
        {
            "type": "directory-structure",
            "paths": ["src/main.py", "src/utils.py", "tests/test_main.py", "README.md", "requirements.txt"],
            "points": 30
        },
        {
            "type": "file-exists",
            "file": "README.md",
            "points": 30
        },
        {
            "type": "content-contains",
            "file": "README.md",
            "sections": ["project"],
            "points": 40
        }
    ],
    "expected_metrics": {
        "tool_calls_range": [4, 12],
        "planning_ratio_range": [0.1, 0.4]
    },
    "scoring_weights": {
        "l0": 0.20,
        "l1": 0.35,
        "l2": 0.20,
        "l3": 0.25
    }
}
(t4 / "task.yaml").write_text(yaml.dump(task4_yaml, default_flow_style=False))

# file-creation/project-proposal  [medium]
t5 = fc_dir / "project-proposal"
(t5 / "inputs").mkdir(parents=True, exist_ok=True)
(t5 / "inputs" / "brief.txt").write_text(
    "Project: DataStream Pipeline Modernization\n"
    "Budget: $250,000\n"
    "Timeline: 6 months\n"
    "Stakeholders: CTO, VP Engineering, Data Team\n"
    "Goal: Replace legacy ETL with real-time streaming architecture\n"
)
task5_yaml = {
    "id": "fc-project-proposal",
    "name": "Project Proposal Document",
    "suite": "file-creation",
    "difficulty": "medium",
    "mode": "sandboxed",
    "user_message": (
        "Using brief.txt in the workspace, create a formal project proposal document "
        "called proposal.md. It must include sections: 'Project Overview', 'Objectives', "
        "'Budget Breakdown', 'Timeline', and 'Risk Assessment'. Between 200 and 500 words."
    ),
    "input_files": ["brief.txt"],
    "expected_outputs": [
        {
            "type": "file-exists",
            "file": "proposal.md",
            "points": 30
        },
        {
            "type": "content-contains",
            "file": "proposal.md",
            "sections": ["Project Overview", "Objectives", "Budget", "Timeline", "Risk"],
            "points": 40
        },
        {
            "type": "word-count-range",
            "file": "proposal.md",
            "min": 200,
            "max": 500,
            "points": 30
        }
    ],
    "expected_metrics": {
        "tool_calls_range": [3, 10],
        "planning_ratio_range": [0.2, 0.6]
    },
    "scoring_weights": {
        "l0": 0.20,
        "l1": 0.35,
        "l2": 0.20,
        "l3": 0.25
    }
}
(t5 / "task.yaml").write_text(yaml.dump(task5_yaml, default_flow_style=False))

# file-creation/api-spec  [hard]  — excluded by --fast
t6 = fc_dir / "api-spec"
(t6 / "inputs").mkdir(parents=True, exist_ok=True)
(t6 / "inputs" / "endpoints.txt").write_text(
    "GET /users - List all users\nPOST /users - Create user\nGET /users/{id} - Get user\nDELETE /users/{id} - Delete user\n"
)
task6_yaml = {
    "id": "fc-api-spec",
    "name": "OpenAPI Specification",
    "suite": "file-creation",
    "difficulty": "hard",
    "mode": "sandboxed",
    "user_message": (
        "Based on endpoints.txt, generate a complete OpenAPI 3.0 specification in YAML "
        "format saved as api_spec.yaml. Include all four endpoints with proper request/response schemas."
    ),
    "input_files": ["endpoints.txt"],
    "expected_outputs": [
        {
            "type": "file-exists",
            "file": "api_spec.yaml",
            "points": 30
        },
        {
            "type": "content-contains",
            "file": "api_spec.yaml",
            "sections": ["openapi", "paths", "components"],
            "points": 40
        }
    ],
    "expected_metrics": {
        "tool_calls_range": [4, 15],
        "planning_ratio_range": [0.2, 0.6]
    },
    "scoring_weights": {
        "l0": 0.20,
        "l1": 0.35,
        "l2": 0.20,
        "l3": 0.25
    }
}
(t6 / "task.yaml").write_text(yaml.dump(task6_yaml, default_flow_style=False))

# ---------- Suite: data-analysis (2 tasks, both hard) — all excluded by --fast ----------
da_dir = tasks_dir / "data-analysis"

t7 = da_dir / "sales-forecast"
(t7 / "inputs").mkdir(parents=True, exist_ok=True)
(t7 / "inputs" / "sales.csv").write_text(
    "month,revenue\n2024-01,50000\n2024-02,55000\n2024-03,62000\n2024-04,58000\n2024-05,67000\n2024-06,72000\n"
)
task7_yaml = {
    "id": "da-sales-forecast",
    "name": "Sales Forecast Analysis",
    "suite": "data-analysis",
    "difficulty": "hard",
    "mode": "sandboxed",
    "user_message": (
        "Analyze sales.csv and produce a forecast report forecast.md with sections "
        "'Historical Analysis', 'Trend', 'Forecast', 'Methodology'. Min 300 words."
    ),
    "input_files": ["sales.csv"],
    "expected_outputs": [
        {"type": "file-exists", "file": "forecast.md", "points": 30},
        {"type": "content-contains", "file": "forecast.md",
         "sections": ["Historical Analysis", "Trend", "Forecast", "Methodology"], "points": 40},
        {"type": "word-count-range", "file": "forecast.md", "min": 300, "max": 2000, "points": 30}
    ],
    "expected_metrics": {"tool_calls_range": [5, 20], "planning_ratio_range": [0.3, 0.7]},
    "scoring_weights": {"l0": 0.20, "l1": 0.35, "l2": 0.20, "l3": 0.25}
}
(t7 / "task.yaml").write_text(yaml.dump(task7_yaml, default_flow_style=False))

t8 = da_dir / "anomaly-detection"
(t8 / "inputs").mkdir(parents=True, exist_ok=True)
(t8 / "inputs" / "logs.txt").write_text(
    "\n".join([f"2024-01-{i:02d} INFO normal operation" for i in range(1, 28)]
              + ["2024-01-28 ERROR disk usage 98%", "2024-01-29 CRITICAL memory leak detected",
                 "2024-01-30 INFO normal operation", "2024-01-31 INFO normal operation"])
)
task8_yaml = {
    "id": "da-anomaly-detection",
    "name": "Log Anomaly Detection",
    "suite": "data-analysis",
    "difficulty": "hard",
    "mode": "sandboxed",
    "user_message": (
        "Examine logs.txt and produce anomaly_report.md identifying anomalies. "
        "Include sections 'Summary', 'Anomalies Found', 'Impact Assessment', 'Recommendations'. "
        "Min 200 words."
    ),
    "input_files": ["logs.txt"],
    "expected_outputs": [
        {"type": "file-exists", "file": "anomaly_report.md", "points": 30},
        {"type": "content-contains", "file": "anomaly_report.md",
         "sections": ["Summary", "Anomalies", "Impact", "Recommendations"], "points": 40},
        {"type": "word-count-range", "file": "anomaly_report.md", "min": 200, "max": 2000, "points": 30}
    ],
    "expected_metrics": {"tool_calls_range": [4, 15], "planning_ratio_range": [0.25, 0.65]},
    "scoring_weights": {"l0": 0.20, "l1": 0.35, "l2": 0.20, "l3": 0.25}
}
(t8 / "task.yaml").write_text(yaml.dump(task8_yaml, default_flow_style=False))

# ── 3.  Distractor files (at least 10, realistic project clutter) ──────────────
distractor_base = workspace / "project-docs"
distractor_base.mkdir(parents=True, exist_ok=True)

(distractor_base / "CHANGELOG.md").write_text(
    "# Changelog\n## v1.2.0\n- Fixed memory leak\n- Improved logging\n## v1.1.0\n- Initial release\n"
)
(distractor_base / "architecture.drawio").write_text(
    "<mxfile><diagram>placeholder diagram data</diagram></mxfile>"
)
(distractor_base / "deployment_notes.txt").write_text(
    "Deploy to prod: kubectl apply -f k8s/\nRollback: kubectl rollout undo deployment/app\n"
)

old_results = workspace / "agentbench-results" / "20250101-090000"
old_results.mkdir(parents=True, exist_ok=True)
(old_results / "results.json").write_text(json.dumps({
    "run_id": "20250101-090000",
    "overall_score": 55,
    "suite_version": "1.9.0",
    "profile": "full",
    "task_count": 8,
    "domain_scores": {"research": 52, "file-creation": 58}
}, indent=2))
(old_results / "report.md").write_text("# Old Report\nScore: 55/100\n")

config_dir = workspace / "config"
config_dir.mkdir(parents=True, exist_ok=True)
(config_dir / "agent.yaml").write_text(
    "name: my-agent\nversion: 0.9.0\nmax_tokens: 4096\ntemperature: 0.7\n"
)
(config_dir / "tools.json").write_text(json.dumps({
    "enabled": ["read", "write", "exec", "web_search"],
    "disabled": ["browser"]
}, indent=2))
(config_dir / "logging.conf").write_text(
    "[loggers]\nkeys=root\n[handlers]\nkeys=consoleHandler\n[formatters]\nkeys=simpleFormatter\n"
)

src_dir = workspace / "src"
src_dir.mkdir(parents=True, exist_ok=True)
(src_dir / "agent.py").write_text(
    "#!/usr/bin/env python3\n# Agent core module\nclass Agent:\n    def __init__(self):\n        self.name = 'openclaw'\n"
)
(src_dir / "utils.py").write_text(
    "def format_score(score):\n    return f'{score:.1f}/100'\n"
)
(src_dir / "runner.py").write_text(
    "import subprocess\ndef run_task(task_id, workspace):\n    pass\n"
)

tests_dir = workspace / "tests"
tests_dir.mkdir(parents=True, exist_ok=True)
(tests_dir / "test_agent.py").write_text(
    "import unittest\nclass TestAgent(unittest.TestCase):\n    def test_placeholder(self):\n        pass\n"
)
(tests_dir / "fixtures" / "sample_task.yaml").parent.mkdir(parents=True, exist_ok=True)
(tests_dir / "fixtures" / "sample_task.yaml").write_text(
    "id: test-task\nname: Test Task\nsuite: test\ndifficulty: easy\n"
)

(workspace / "Makefile").write_text(
    "test:\n\tpython3 -m pytest tests/\n\nbenchmark:\n\t./run_benchmark.sh\n\nclean:\n\trm -rf /tmp/agentbench-*\n"
)
(workspace / ".gitignore").write_text(
    "__pycache__/\n*.pyc\nagentbench-results/\n/tmp/\n.env\n"
)
(workspace / "legacy_scores.csv").write_text(
    "run_id,score,date\n20241201-120000,62,2024-12-01\n20241215-093000,68,2024-12-15\n20250101-090000,55,2025-01-01\n"
)

# ── 4.  A deliberately wrong/outdated skill.json in workspace root (trap) ────────
# Agent must read from agentbench-skill/skill.json, NOT this one
(workspace / "skill.json").write_text(json.dumps({
    "name": "agentbench",
    "suite_version": "0.0.1-WRONG",
    "version": "0.1.0"
}, indent=2))

print("Workspace generated successfully.")
print(f"Skill dir: {skill_dir}")
print(f"Tasks: research(3), file-creation(3), data-analysis(2)")
print(f"Distractor files: {len(list(workspace.rglob('*')))} total files")