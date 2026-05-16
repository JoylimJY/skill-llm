import os
import json
import stat
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ─── Project source tree (distractor files to test contextual awareness) ────
source_dirs = [
    "src/fraud_detection",
    "src/fraud_detection/models",
    "src/fraud_detection/pipeline",
    "src/fraud_detection/api",
    "src/fraud_detection/utils",
    "src/fraud_detection/config",
    "tests/unit",
    "tests/integration",
    "tests/fixtures",
    "infra/docker",
    "infra/k8s",
    "infra/terraform",
    "ci",
    "data/samples",
    "notebooks",
]
for d in source_dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Realistic source files (distractors) ────────────────────────────────────
source_files = {
    "src/fraud_detection/__init__.py": '"""Fraud Detection Package v0.1.0"""',
    "src/fraud_detection/models/transaction.py": textwrap.dedent("""\
        from dataclasses import dataclass
        from datetime import datetime

        @dataclass
        class Transaction:
            id: str
            amount: float
            currency: str
            merchant_id: str
            user_id: str
            timestamp: datetime
            risk_score: float = 0.0
    """),
    "src/fraud_detection/models/risk_model.py": textwrap.dedent("""\
        class RiskModel:
            def __init__(self, threshold: float = 0.85):
                self.threshold = threshold

            def predict(self, features: dict) -> float:
                # Placeholder: replace with trained model
                return 0.0

            def is_fraudulent(self, score: float) -> bool:
                return score >= self.threshold
    """),
    "src/fraud_detection/pipeline/feature_extractor.py": textwrap.dedent("""\
        class FeatureExtractor:
            VELOCITY_WINDOW = 3600  # seconds

            def extract(self, transaction, history):
                return {
                    'amount_zscore': 0.0,
                    'velocity_1h': len(history),
                    'merchant_risk': 0.5,
                }
    """),
    "src/fraud_detection/pipeline/detector.py": textwrap.dedent("""\
        from .feature_extractor import FeatureExtractor
        from ..models.risk_model import RiskModel

        class FraudDetector:
            def __init__(self):
                self.extractor = FeatureExtractor()
                self.model = RiskModel()

            def evaluate(self, transaction, history):
                features = self.extractor.extract(transaction, history)
                score = self.model.predict(features)
                return score, self.model.is_fraudulent(score)
    """),
    "src/fraud_detection/api/routes.py": textwrap.dedent("""\
        # FastAPI routes — stub
        from fastapi import APIRouter
        router = APIRouter()

        @router.post('/evaluate')
        async def evaluate_transaction(payload: dict):
            return {'risk_score': 0.0, 'is_fraud': False}
    """),
    "src/fraud_detection/api/main.py": textwrap.dedent("""\
        from fastapi import FastAPI
        from .routes import router

        app = FastAPI(title='Fraud Detection API')
        app.include_router(router, prefix='/api/v1')
    """),
    "src/fraud_detection/utils/logger.py": "import logging\nlogger = logging.getLogger('fraud_detection')\n",
    "src/fraud_detection/config/settings.py": textwrap.dedent("""\
        import os
        RISK_THRESHOLD = float(os.getenv('RISK_THRESHOLD', '0.85'))
        DB_URI = os.getenv('DB_URI', 'postgresql://localhost/fraud')
        KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
    """),
    "tests/unit/test_risk_model.py": textwrap.dedent("""\
        import pytest
        from src.fraud_detection.models.risk_model import RiskModel

        def test_threshold():
            m = RiskModel(threshold=0.9)
            assert m.is_fraudulent(0.95)
            assert not m.is_fraudulent(0.5)
    """),
    "tests/integration/test_detector.py": "# TODO: integration tests\n",
    "tests/fixtures/sample_transactions.json": json.dumps([
        {"id": "tx001", "amount": 4500.0, "currency": "USD", "merchant_id": "m42", "user_id": "u99"},
        {"id": "tx002", "amount": 12.5,   "currency": "EUR", "merchant_id": "m11", "user_id": "u01"},
    ], indent=2),
    "infra/docker/Dockerfile.fraud": "FROM python:3.11-slim\nCOPY src/ /app/src/\n",
    "infra/k8s/deployment.yaml": textwrap.dedent("""\
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: fraud-detection
        spec:
          replicas: 2
    """),
    "infra/terraform/main.tf": '# Terraform stub for RDS and MSK\n',
    "ci/pipeline.yml": textwrap.dedent("""\
        stages:
          - lint
          - test
          - build
          - deploy
    """),
    "data/samples/transactions_sample.csv": "tx_id,amount,currency,label\ntx001,4500,USD,fraud\ntx002,12.5,EUR,legit\n",
    "notebooks/eda.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
    "pyproject.toml": textwrap.dedent("""\
        [tool.poetry]
        name = "fraud-detection"
        version = "0.1.0"
        description = "Payment fraud detection microservice"

        [tool.poetry.dependencies]
        python = "^3.11"
        fastapi = "*"
        scikit-learn = "*"
    """),
    ".gitignore": "__pycache__/\n*.pyc\n.env\ndist/\n",
}

for rel_path, content in source_files.items():
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# ─── Create scripts/ directory and tool scripts ───────────────────────────────
scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(exist_ok=True)

# ── trae_agent_dispatch.py ────────────────────────────────────────────────────
trae_dispatch = r'''#!/usr/bin/env python3
"""
Trae Multi-Agent Dispatcher
Dispatches tasks to appropriate agent roles and manages multi-agent collaboration.
"""
import argparse
import json
import sys
import os
import re
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent

ROLE_KEYWORDS = {
    "architect":        ["architecture", "design", "selection", "review", "performance",
                         "bottleneck", "module", "interface", "deployment",
                         "架构", "设计", "选型", "审查", "性能", "瓶颈", "模块", "接口", "部署"],
    "product_manager":  ["requirement", "prd", "user story", "competitive", "market",
                         "research", "acceptance", "uat", "experience",
                         "需求", "prd", "用户故事", "竞品", "市场", "调研", "验收", "uat", "体验"],
    "test_expert":      ["test", "quality", "acceptance", "automation", "performance test",
                         "defect", "review", "gate",
                         "测试", "质量", "验收", "自动化", "性能测试", "缺陷", "评审", "门禁"],
    "solo_coder":       ["implement", "develop", "code", "fix", "optimize", "refactor",
                         "unit test", "documentation",
                         "实现", "开发", "代码", "修复", "优化", "重构", "单元测试", "文档"],
}

ROLE_DISPLAY = {
    "architect":       "Architect",
    "product_manager": "Product Manager",
    "test_expert":     "Test Expert",
    "solo_coder":      "Solo Coder",
}

DOCS_MAP = {
    "architect":       "docs/architect",
    "product_manager": "docs/product-manager",
    "test_expert":     "docs/test-expert",
    "solo_coder":      "docs/solo-coder",
}

STAGES = [
    ("product_manager", "requirements_analysis",  "Requirements Analysis"),
    ("architect",       "architecture_design",    "Architecture Design"),
    ("test_expert",     "test_design",            "Test Design"),
    ("solo_coder",      "task_decomposition",     "Task Decomposition"),
    ("solo_coder",      "development",            "Development Implementation"),
    ("test_expert",     "test_verification",      "Test Verification"),
    ("all",             "release_review",         "Release Review"),
]

AUDIT_FILE = WORKSPACE / ".dispatch_audit.jsonl"


def detect_language(text: str) -> str:
    chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
    return "zh" if chinese > len(text) * 0.1 else "en"


def analyze_task(task: str) -> str:
    task_lower = task.lower()
    scores = {role: 0 for role in ROLE_KEYWORDS}
    for role, kws in ROLE_KEYWORDS.items():
        for kw in kws:
            if kw in task_lower:
                scores[role] += 1
    best = max(scores, key=lambda r: scores[r])
    if scores[best] == 0:
        return "solo_coder"
    return best


def record_audit(entry: dict):
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def ensure_docs(role: str):
    doc_dir = WORKSPACE / DOCS_MAP[role]
    doc_dir.mkdir(parents=True, exist_ok=True)
    return doc_dir


def run_stage(stage_role: str, stage_slug: str, stage_name: str, task: str,
              lang: str, stage_num: int, consensus: bool = False):
    roles = list(ROLE_DISPLAY.keys()) if stage_role == "all" else [stage_role]
    for role in roles:
        doc_dir = ensure_docs(role)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
        filename = f"stage{stage_num:02d}_{stage_slug}_{ts}.md"
        doc_path = doc_dir / filename

        if lang == "zh":
            content = f"# 阶段 {stage_num}: {stage_name}\n\n"
            content += f"**角色**: {ROLE_DISPLAY[role]}\n\n"
            content += f"**任务**: {task}\n\n"
            content += f"**时间**: {ts}\n\n"
            content += f"## 输出\n\n此阶段由 {ROLE_DISPLAY[role]} 完成。\n"
        else:
            content = f"# Stage {stage_num}: {stage_name}\n\n"
            content += f"**Role**: {ROLE_DISPLAY[role]}\n\n"
            content += f"**Task**: {task}\n\n"
            content += f"**Timestamp**: {ts}\n\n"
            content += f"## Output\n\nThis stage was completed by {ROLE_DISPLAY[role]}.\n"

        if consensus and stage_num == 7:
            content += "\n## Consensus Review\n\nAll roles participated in the release review.\n"

        doc_path.write_text(content, encoding="utf-8")

        record_audit({
            "event":      "stage_completed",
            "stage":      stage_num,
            "stage_slug": stage_slug,
            "role":       role,
            "doc":        str(doc_path.relative_to(WORKSPACE)),
            "lang":       lang,
            "ts":         ts,
        })

        if lang == "zh":
            print(f"  ✅ 阶段 {stage_num} [{stage_name}] ({ROLE_DISPLAY[role]}) 完成 → {doc_path.name}")
        else:
            print(f"  ✅ Stage {stage_num} [{stage_name}] ({ROLE_DISPLAY[role]}) done → {doc_path.name}")


def run_lifecycle(task: str, lang: str, consensus: bool):
    if lang == "zh":
        print(f"\n🚀 启动完整项目生命周期（7个阶段）\n任务: {task}\n")
    else:
        print(f"\n🚀 Starting full project lifecycle (7 stages)\nTask: {task}\n")

    for i, (role, slug, name) in enumerate(STAGES, 1):
        run_stage(role, slug, name, task, lang, i,
                  consensus=(consensus or i == 7))

    record_audit({"event": "lifecycle_completed", "task": task, "lang": lang,
                  "stages": len(STAGES), "ts": datetime.utcnow().isoformat()})

    if lang == "zh":
        print(f"\n🎉 项目生命周期完成！所有 {len(STAGES)} 个阶段已执行。")
    else:
        print(f"\n🎉 Project lifecycle complete! All {len(STAGES)} stages executed.")


def run_single(task: str, agent: str, lang: str, consensus: bool):
    role = agent if agent else analyze_task(task)
    doc_dir = ensure_docs(role)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    filename = f"dispatch_{ts}.md"
    doc_path = doc_dir / filename

    if lang == "zh":
        content = f"# 调度报告\n\n**角色**: {ROLE_DISPLAY[role]}\n**任务**: {task}\n**时间**: {ts}\n"
    else:
        content = f"# Dispatch Report\n\n**Role**: {ROLE_DISPLAY[role]}\n**Task**: {task}\n**Timestamp**: {ts}\n"

    if consensus:
        if lang == "zh":
            content += "\n## 共识评审\n\n多角色参与了本次评审。\n"
        else:
            content += "\n## Consensus Review\n\nMultiple roles participated in this review.\n"

    doc_path.write_text(content, encoding="utf-8")
    record_audit({
        "event":     "dispatch",
        "role":      role,
        "task":      task,
        "consensus": consensus,
        "lang":      lang,
        "doc":       str(doc_path.relative_to(WORKSPACE)),
        "ts":        ts,
    })

    if lang == "zh":
        print(f"📋 已分配至 {ROLE_DISPLAY[role]} → {doc_path.name}")
    else:
        print(f"📋 Dispatched to {ROLE_DISPLAY[role]} → {doc_path.name}")

    if consensus:
        consensus_roles = [r for r in ROLE_DISPLAY if r != role]
        for cr in consensus_roles:
            cdir = ensure_docs(cr)
            cfile = cdir / f"consensus_{ts}.md"
            if lang == "zh":
                c = f"# 共识输入\n\n**来自**: {ROLE_DISPLAY[cr]}\n**任务**: {task}\n"
            else:
                c = f"# Consensus Input\n\n**From**: {ROLE_DISPLAY[cr]}\n**Task**: {task}\n"
            cfile.write_text(c, encoding="utf-8")
            record_audit({"event": "consensus", "role": cr, "ts": ts})


def main():
    parser = argparse.ArgumentParser(description="Trae Multi-Agent Dispatcher")
    parser.add_argument("--task",    required=True,  help="Task description")
    parser.add_argument("--agent",   default=None,   help="Force specific agent role")
    parser.add_argument("--consensus", default="false",
                        help="Enable multi-role consensus (true/false)")
    parser.add_argument("--project-full-lifecycle", action="store_true",
                        help="Run the complete 7-stage project lifecycle")
    args = parser.parse_args()

    lang      = detect_language(args.task)
    consensus = args.consensus.lower() == "true"

    if args.project_full_lifecycle:
        run_lifecycle(args.task, lang, consensus)
    else:
        run_single(args.task, args.agent, lang, consensus)


if __name__ == "__main__":
    main()
'''

# ── code_map_generator.py ─────────────────────────────────────────────────────
code_map_gen = r'''#!/usr/bin/env python3
"""
Code Map Generator
Generates a structured code map for a project directory.
"""
import argparse
import json
import os
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
AUDIT_FILE = WORKSPACE / ".dispatch_audit.jsonl"


def build_tree(base: Path, rel: Path = None, depth: int = 0, max_depth: int = 6):
    if rel is None:
        rel = Path(".")
    current = base / rel
    result = {"name": current.name or str(base), "type": "dir", "children": []}
    try:
        entries = sorted(current.iterdir(), key=lambda p: (p.is_file(), p.name))
    except PermissionError:
        return result
    for entry in entries:
        if entry.name.startswith(".") or entry.name in ("__pycache__", "node_modules", ".git"):
            continue
        if entry.is_dir() and depth < max_depth:
            result["children"].append(
                build_tree(base, rel / entry.name, depth + 1, max_depth)
            )
        elif entry.is_file():
            result["children"].append({
                "name":  entry.name,
                "type":  "file",
                "size":  entry.stat().st_size,
                "ext":   entry.suffix,
            })
    return result


def main():
    parser = argparse.ArgumentParser(description="Code Map Generator")
    parser.add_argument("project_path", help="Path to the project directory")
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    if not project_path.is_dir():
        print(f"ERROR: {project_path} is not a directory")
        raise SystemExit(1)

    tree = build_tree(project_path)
    ts   = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    # Save to docs/project-understanding/
    out_dir = WORKSPACE / "docs" / "project-understanding"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"code_map_{ts}.json"

    data = {
        "generated_at":  ts,
        "project_path":  str(project_path),
        "tree":          tree,
    }
    out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"event": "code_map_generated", "path": str(project_path),
                             "output": str(out_file.relative_to(WORKSPACE)), "ts": ts}) + "\n")

    print(f"✅ Code map generated → {out_file}")


if __name__ == "__main__":
    main()
'''

# ── project_understanding.py ──────────────────────────────────────────────────
proj_understanding = r'''#!/usr/bin/env python3
"""
Project Understanding Generator
Reads project files and generates a project understanding document.
"""
import argparse
import json
import os
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
AUDIT_FILE = WORKSPACE / ".dispatch_audit.jsonl"

READABLE_EXTS = {".py", ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".cfg", ".ini"}


def summarize_project(project_path: Path) -> dict:
    summary = {
        "total_files": 0,
        "languages":   {},
        "key_files":   [],
        "description": "",
    }
    for p in sorted(project_path.rglob("*")):
        if p.is_file() and not any(part.startswith(".") for part in p.parts):
            if "__pycache__" in str(p):
                continue
            summary["total_files"] += 1
            ext = p.suffix
            summary["languages"][ext] = summary["languages"].get(ext, 0) + 1
            if p.name in ("pyproject.toml", "setup.py", "requirements.txt",
                           "README.md", "Dockerfile", "main.py", "app.py"):
                summary["key_files"].append(str(p.relative_to(project_path)))

    summary["description"] = (
        f"Project at {project_path.name} contains {summary['total_files']} files "
        f"across {len(summary['languages'])} file types."
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Project Understanding Generator")
    parser.add_argument("project_path", help="Path to the project directory")
    args = parser.parse_args()

    project_path = Path(args.project_path).resolve()
    if not project_path.is_dir():
        print(f"ERROR: {project_path} is not a directory")
        raise SystemExit(1)

    summary = summarize_project(project_path)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    out_dir = WORKSPACE / "docs" / "project-understanding"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"project_understanding_{ts}.md"

    content = f"""# Project Understanding Document

Generated: {ts}
Project: {project_path}

## Summary

{summary['description']}

## Statistics

- Total Files: {summary['total_files']}
- File Types: {json.dumps(summary['languages'], ensure_ascii=False)}

## Key Files

{chr(10).join(f'- {f}' for f in summary['key_files']) or '(none identified)'}

## Project Structure Analysis

This document was auto-generated by project_understanding.py.
It provides a baseline understanding for the multi-agent team.
"""
    out_file.write_text(content, encoding="utf-8")

    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"event": "project_understanding_generated",
                             "path": str(project_path),
                             "output": str(out_file.relative_to(WORKSPACE)),
                             "ts": ts}) + "\n")

    print(f"✅ Project understanding document → {out_file}")


if __name__ == "__main__":
    main()
'''

# ── spec_tools.py ─────────────────────────────────────────────────────────────
spec_tools = r'''#!/usr/bin/env python3
"""
Spec Tools - Specification-driven development utilities
Usage:
  spec_tools.py init
  spec_tools.py analyze
  spec_tools.py update --spec-file <SPEC.md>
"""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).parent.parent
AUDIT_FILE = WORKSPACE / ".dispatch_audit.jsonl"
SPEC_STATE  = WORKSPACE / ".spec_state.json"


def record_audit(entry: dict):
    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def load_state() -> dict:
    if SPEC_STATE.exists():
        return json.loads(SPEC_STATE.read_text())
    return {}


def save_state(state: dict):
    SPEC_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def cmd_init():
    spec_dir = WORKSPACE / "docs" / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    init_file = spec_dir / f"spec_init_{ts}.json"
    data = {"initialized_at": ts, "version": "1.0", "status": "initialized"}
    init_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    state = load_state()
    state["initialized_at"] = ts
    state["init_file"] = str(init_file.relative_to(WORKSPACE))
    save_state(state)

    record_audit({"event": "spec_init", "ts": ts, "file": str(init_file.relative_to(WORKSPACE))})
    print(f"✅ Spec initialized → {init_file.name}")


def cmd_analyze():
    state = load_state()
    if "initialized_at" not in state:
        print("ERROR: Spec not initialized. Run 'spec_tools.py init' first.")
        raise SystemExit(1)

    spec_dir = WORKSPACE / "docs" / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    analysis_file = spec_dir / f"spec_analysis_{ts}.json"

    # Analyze existing source files
    src_dir = WORKSPACE / "src"
    py_files = list(src_dir.rglob("*.py")) if src_dir.exists() else []
    analysis = {
        "analyzed_at":  ts,
        "source_files": len(py_files),
        "gaps":         ["Missing API documentation", "No error handling spec",
                         "Performance targets undefined"],
        "recommendations": ["Define SLAs", "Add OpenAPI spec", "Document data contracts"],
    }
    analysis_file.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    state["analyzed_at"] = ts
    state["analysis_file"] = str(analysis_file.relative_to(WORKSPACE))
    save_state(state)

    record_audit({"event": "spec_analyze", "ts": ts,
                  "file": str(analysis_file.relative_to(WORKSPACE))})
    print(f"✅ Spec analysis complete → {analysis_file.name}")
    print(f"   Source files scanned: {len(py_files)}")
    print(f"   Gaps identified: {len(analysis['gaps'])}")


def cmd_update(spec_file: str):
    state = load_state()
    if "analyzed_at" not in state:
        print("ERROR: Spec not analyzed. Run 'spec_tools.py analyze' first.")
        raise SystemExit(1)

    if not spec_file:
        print("ERROR: --spec-file is required for 'update' command.")
        raise SystemExit(1)

    spec_path = Path(spec_file)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    # Write or update the SPEC.md
    spec_dir = WORKSPACE / "docs" / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)

    # Also write to workspace root if relative path given
    target = WORKSPACE / spec_path if not spec_path.is_absolute() else spec_path
    content = f"""# Specification Document

Updated: {ts}

## Project Overview

Payment Fraud Detection Microservice

## Functional Requirements

1. Real-time transaction risk scoring (< 50ms P99)
2. Configurable risk thresholds per merchant category
3. Kafka event streaming for fraud alerts
4. REST API conforming to OpenAPI 3.1

## Non-Functional Requirements

- Availability: 99.95% SLA
- Throughput: 10,000 TPS sustained
- Data retention: 90 days

## Quality Gates

- Unit test coverage ≥ 85%
- Zero critical security vulnerabilities
- Performance regression < 5%

## Generated By

spec_tools.py update --spec-file {spec_file}
State: {json.dumps(state)}
"""
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

    # Also copy to docs/spec/
    versioned = spec_dir / f"SPEC_{ts}.md"
    versioned.write_text(content, encoding="utf-8")

    state["updated_at"] = ts
    state["spec_file"] = str(target.relative_to(WORKSPACE))
    save_state(state)

    record_audit({"event": "spec_update", "ts": ts,
                  "spec_file": str(target.relative_to(WORKSPACE)),
                  "flag_used": f"--spec-file {spec_file}"})
    print(f"✅ Spec updated → {target}")
    print(f"   Versioned copy → {versioned.name}")


def main():
    parser = argparse.ArgumentParser(description="Spec Tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init",    help="Initialize spec")
    subparsers.add_parser("analyze", help="Analyze project for spec gaps")
    update_p = subparsers.add_parser("update", help="Update spec file")
    update_p.add_argument("--spec-file", required=True, help="Path to SPEC.md")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init()
    elif args.command == "analyze":
        cmd_analyze()
    elif args.command == "update":
        cmd_update(args.spec_file)


if __name__ == "__main__":
    main()
'''

scripts = {
    "scripts/trae_agent_dispatch.py":  trae_dispatch,
    "scripts/code_map_generator.py":   code_map_gen,
    "scripts/project_understanding.py": proj_understanding,
    "scripts/spec_tools.py":           spec_tools,
}

for rel, content in scripts.items():
    p = WORKSPACE / rel
    p.write_text(content, encoding="utf-8")
    p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

# ─── roles.json (referenced in SKILL.md extension section) ────────────────────
roles_json = {
    "roles": [
        {"id": "architect",       "display_en": "Architect",       "display_zh": "架构师"},
        {"id": "product_manager", "display_en": "Product Manager", "display_zh": "产品经理"},
        {"id": "test_expert",     "display_en": "Test Expert",     "display_zh": "测试专家"},
        {"id": "solo_coder",      "display_en": "Solo Coder",      "display_zh": "独立开发者"},
    ]
}
(WORKSPACE / "roles.json").write_text(
    json.dumps(roles_json, indent=2, ensure_ascii=False), encoding="utf-8"
)

# ─── Create docs/ skeleton (empty — agent must populate) ─────────────────────
for d in ["docs/project-understanding", "docs/spec",
          "docs/architect", "docs/product-manager",
          "docs/test-expert", "docs/solo-coder"]:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)
    gitkeep = WORKSPACE / d / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()

print("✅ Workspace generated successfully.")
print(f"   Source files: {len(source_files)}")
print(f"   Scripts:      {len(scripts)}")