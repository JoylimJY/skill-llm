import os
import random
import json
import yaml

random.seed(42)

workspace = "/workspace"

# --- Create realistic bioinformatics project directory structure ---
dirs = [
    "scripts",
    "data/raw/sample_001",
    "data/raw/sample_002",
    "data/processed",
    "data/qc_reports",
    "pipelines/legacy",
    "pipelines/experimental",
    "configs/agents",
    "configs/pipelines",
    "notebooks",
    "tests/unit",
    "tests/integration",
    "docs/api",
    "docs/guides",
    "outputs/runs",
    "outputs/metrics",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files (realistic but irrelevant) ---

# 1. Legacy pipeline config
with open(os.path.join(workspace, "configs/pipelines/legacy_qc.yaml"), "w") as f:
    yaml.dump({
        "pipeline": "LegacyQC",
        "version": "0.3.1",
        "steps": ["trim", "align", "call_variants"],
        "thresholds": {"min_quality": 20, "min_coverage": 10},
    }, f)

# 2. Raw sequencing metadata
with open(os.path.join(workspace, "data/raw/sample_001/metadata.json"), "w") as f:
    json.dump({
        "sample_id": "GEN-2024-001",
        "organism": "H. sapiens",
        "platform": "Illumina NovaSeq",
        "run_date": "2024-03-15",
        "reads": 45_000_000,
        "mean_quality": 32.4,
    }, f, indent=2)

# 3. Raw sequencing metadata #2
with open(os.path.join(workspace, "data/raw/sample_002/metadata.json"), "w") as f:
    json.dump({
        "sample_id": "GEN-2024-002",
        "organism": "H. sapiens",
        "platform": "Illumina HiSeq",
        "run_date": "2024-03-16",
        "reads": 38_000_000,
        "mean_quality": 28.1,
    }, f, indent=2)

# 4. Existing (broken) experimental pipeline
with open(os.path.join(workspace, "pipelines/experimental/proto_workflow.py"), "w") as f:
    f.write("""\
# Experimental - DO NOT USE IN PRODUCTION
# This workflow is incomplete and abandoned

class ProtoWorkflow:
    def run(self, data):
        # TODO: implement quality check logic
        pass

    def _score(self):
        return None
""")

# 5. QC report template (distractor)
with open(os.path.join(workspace, "data/qc_reports/template.txt"), "w") as f:
    f.write("""\
QC REPORT TEMPLATE
==================
Sample: {sample_id}
Date: {date}
Status: {status}
Notes: {notes}
""")

# 6. Agent config (distractor)
with open(os.path.join(workspace, "configs/agents/base_agent.yaml"), "w") as f:
    yaml.dump({
        "agent": {
            "name": "BaseQCAgent",
            "model": "gpt-4",
            "temperature": 0.7,
            "tools": ["file_io", "stats"],
        }
    }, f)

# 7. Notebook distractor
with open(os.path.join(workspace, "notebooks/exploratory_analysis.py"), "w") as f:
    f.write("""\
# Jupyter-style exploratory script
import json, os

samples = ['sample_001', 'sample_002']
for s in samples:
    path = f'data/raw/{s}/metadata.json'
    if os.path.exists(path):
        with open(path) as fh:
            meta = json.load(fh)
        print(f"{s}: quality={meta['mean_quality']}")
""")

# 8. Test stubs
with open(os.path.join(workspace, "tests/unit/test_qc.py"), "w") as f:
    f.write("""\
import pytest

def test_quality_threshold():
    assert 32.4 > 30, "Quality should exceed threshold"

def test_coverage():
    assert 10 > 5, "Coverage should exceed minimum"
""")

# 9. Integration test stub
with open(os.path.join(workspace, "tests/integration/test_pipeline.py"), "w") as f:
    f.write("""\
# Integration tests - requires full pipeline
# Run with: pytest tests/integration/ --slow

def test_end_to_end():
    # TODO: wire up
    pass
""")

# 10. Docs distractor
with open(os.path.join(workspace, "docs/guides/getting_started.md"), "w") as f:
    f.write("""\
# Getting Started with Genomics QC Pipeline

## Prerequisites
- Python 3.11+
- 32GB RAM
- Access to sequencing data

## Steps
1. Configure your sample manifest
2. Run the QC pipeline
3. Review reports in data/qc_reports/
""")

# 11. Metrics output (distractor)
with open(os.path.join(workspace, "outputs/metrics/baseline_metrics.json"), "w") as f:
    json.dump({
        "pipeline": "legacy_qc",
        "run_id": "run_20240315_001",
        "accuracy": 0.81,
        "precision": 0.79,
        "recall": 0.83,
        "f1": 0.81,
    }, f, indent=2)

# 12. Legacy pipeline python (distractor)
with open(os.path.join(workspace, "pipelines/legacy/qc_pipeline_v1.py"), "w") as f:
    f.write("""\
# Legacy QC Pipeline v1 - static, non-evolving
# Deprecated: replaced by self-evolving workflows

def run_qc(sample_path, min_quality=20):
    import json
    with open(sample_path) as f:
        meta = json.load(f)
    return meta.get('mean_quality', 0) >= min_quality

if __name__ == '__main__':
    import sys
    result = run_qc(sys.argv[1])
    print('PASS' if result else 'FAIL')
""")

# 13. requirements stub
with open(os.path.join(workspace, "configs/agents/evolution_targets.json"), "w") as f:
    json.dump({
        "targets": [
            {"metric": "accuracy", "threshold": 0.95},
            {"metric": "f1_score", "threshold": 0.92},
            {"metric": "throughput", "threshold": 1000},
        ],
        "strategy": "unknown",
        "notes": "Strategy TBD - consult framework docs"
    }, f, indent=2)

# --- Create the SKILL's CLI script (already part of skill infrastructure) ---
# This is the evoagentx_cli.py referenced in the SKILL.md
evoagentx_cli_content = r'''#!/usr/bin/env python3
"""EvoAgentX CLI - OpenClaw Bridge Interface"""
import argparse
import sys
import os
import json

# Marker written to files created via create-workflow
CLI_STAMP = "# Generated by evoagentx_cli.py create-workflow"
GENOME_FIELDS = ["task_type_classification", "approach_methodology", "outcome_metrics", "context_requirements"]

def cmd_status(args):
    try:
        import evoagentx
        version = getattr(evoagentx, '__version__', 'unknown')
        print(f"EvoAgentX status: INSTALLED (version {version})")
        print("OpenClaw bridge: ACTIVE")
        return 0
    except ImportError:
        print("EvoAgentX status: NOT INSTALLED")
        print("Run: pip install evoagentx")
        return 1

def cmd_check(args):
    return cmd_status(args)

def cmd_install(args):
    print("Installation instructions:")
    print("  pip install evoagentx")
    print("  python3 -c \"import evoagentx; print(evoagentx.__version__)\"")
    return 0

def cmd_examples(args):
    print("EvoAgentX workflow examples:")
    print("  - ResearchWorkflow: automated literature research")
    print("  - DataQualityWorkflow: data validation and quality assessment")
    print("  - OptimizationWorkflow: parameter search and tuning")
    print("\nEvolution strategies: TextGrad, AFlow, MIPRO")
    print("GEP genome fields:", ", ".join(GENOME_FIELDS))
    return 0

def cmd_create_workflow(args):
    name = args.name
    description = args.description or f"Workflow: {name}"
    # Output filename: snake_case of name
    filename = name[0].lower()
    for ch in name[1:]:
        if ch.isupper():
            filename += '_' + ch.lower()
        else:
            filename += ch
    if not filename.endswith('_workflow'):
        filename += '_workflow'
    filename += '.py'

    content = f'''{CLI_STAMP}
# Workflow: {name}
# Description: {description}
# Created via: evoagentx_cli.py create-workflow

from evoagentx import Agent, Workflow

class {name}(Workflow):
    """
    {description}
    
    TODO: Implement workflow logic below.
    Configure evolution strategy and genome before use.
    """
    
    async def execute(self, context):
        # TODO: implement your multi-agent workflow logic here
        result = await self.run_agents(context)
        return result

# --- Evolution Configuration (TODO: fill in) ---
# genome = {{
#     "task_type_classification": "",
#     "approach_methodology": "",
#     "outcome_metrics": {{}},
#     "context_requirements": [],
# }}
#
# from evoagentx.evolution import EvolutionEngine
# engine = EvolutionEngine()
# optimized = await engine.evolve(workflow={name}(), iterations=10, evaluation_criteria={{}})
'''
    with open(filename, 'w') as f:
        f.write(content)
    print(f"Created workflow template: {filename}")
    print(f"Next steps:")
    print(f"  1. Edit {filename} to implement your workflow logic")
    print(f"  2. Configure the genome with GEP fields: {', '.join(GENOME_FIELDS)}")
    print(f"  3. Choose an evolution strategy: TextGrad, AFlow, or MIPRO")
    return 0

def main():
    parser = argparse.ArgumentParser(description='EvoAgentX CLI - OpenClaw Bridge')
    subparsers = parser.add_subparsers(dest='command')

    subparsers.add_parser('status', help='Check EvoAgentX installation status')
    subparsers.add_parser('check', help='Check EvoAgentX installation status')
    subparsers.add_parser('install', help='Show installation instructions')
    subparsers.add_parser('examples', help='Show usage examples')

    cw = subparsers.add_parser('create-workflow', help='Create a workflow template')
    cw.add_argument('--name', required=True, help='Workflow class name (PascalCase)')
    cw.add_argument('--description', default='', help='Workflow description')

    args = parser.parse_args()

    if args.command == 'status':
        sys.exit(cmd_status(args))
    elif args.command == 'check':
        sys.exit(cmd_check(args))
    elif args.command == 'install':
        sys.exit(cmd_install(args))
    elif args.command == 'examples':
        sys.exit(cmd_examples(args))
    elif args.command == 'create-workflow':
        sys.exit(cmd_create_workflow(args))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()
'''

with open(os.path.join(workspace, "scripts/evoagentx_cli.py"), "w") as f:
    f.write(evoagentx_cli_content)

print("Workspace scaffold complete.")
print(f"Files created in {workspace}")