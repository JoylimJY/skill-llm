import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Simulate the Nima Codex skill-creator toolchain (scripts already "exist") ──
scripts_dir = WORKSPACE / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# init_skill.py  ── realistic scaffolding script
(scripts_dir / "init_skill.py").write_text(textwrap.dedent('''\
    #!/usr/bin/env python3
    """Initialize a new Codex-compatible skill folder."""
    import argparse, os, sys, textwrap
    from pathlib import Path

    FRONTMATTER_TEMPLATE = "---\\nname: {name}\\ndescription: {description}\\n---\\n"
    SKILL_BODY = textwrap.dedent("""
    # {display_name}

    ## Overview
    This skill was scaffolded automatically. Replace this section with procedural guidance.

    ## Steps
    1. Describe step one.
    2. Describe step two.
    """).lstrip()

    def main():
        parser = argparse.ArgumentParser(description="Initialize a Codex skill.")
        parser.add_argument("skill_name", help="Kebab-case skill name")
        parser.add_argument("--path", default=".", help="Parent directory for the skill folder")
        parser.add_argument("--resources", default="", help="Comma-separated: scripts,references,assets")
        parser.add_argument("--examples", action="store_true", help="Add examples/ directory")
        parser.add_argument("--interface", action="append", default=[],
                            help="Key=Value pairs: display_name=\\"...\\" short_description=\\"...\\"")
        args = parser.parse_args()

        interface = {}
        for item in args.interface:
            if "=" in item:
                k, v = item.split("=", 1)
                interface[k.strip()] = v.strip().strip('"').strip("'")

        display_name = interface.get("display_name", args.skill_name)
        short_description = interface.get("short_description", "")

        skill_dir = Path(args.path) / args.skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Write SKILL.md
        description_line = short_description if short_description else f"Use for tasks related to {display_name}."
        frontmatter = FRONTMATTER_TEMPLATE.format(name=args.skill_name, description=description_line)
        body = SKILL_BODY.format(display_name=display_name)
        (skill_dir / "SKILL.md").write_text(frontmatter + body)

        # Write openai.yaml if interface keys provided
        if interface:
            agents_dir = skill_dir / "agents"
            agents_dir.mkdir(exist_ok=True)
            yaml_content = f"display_name: \\"{display_name}\\"\\n"
            if short_description:
                yaml_content += f"short_description: \\"{short_description}\\"\\n"
            (agents_dir / "openai.yaml").write_text(yaml_content)

        # Create optional resource dirs
        resources = [r.strip() for r in args.resources.split(",") if r.strip()]
        for res in resources:
            (skill_dir / res).mkdir(exist_ok=True)
            gitkeep = skill_dir / res / ".gitkeep"
            gitkeep.touch()

        if args.examples:
            (skill_dir / "examples").mkdir(exist_ok=True)

        print(f"[init_skill] Created skill at: {skill_dir}")
        print(f"[init_skill] Resources: {resources}")
        if interface:
            print(f"[init_skill] Interface: {interface}")

    if __name__ == "__main__":
        main()
'''))

# validate_skill.py  ── validates frontmatter + structure
(scripts_dir / "validate_skill.py").write_text(textwrap.dedent('''\
    #!/usr/bin/env python3
    """Validate a Codex-compatible skill folder."""
    import sys, re
    from pathlib import Path

    REQUIRED_FILES = ["SKILL.md"]
    ALLOWED_FRONTMATTER_KEYS = {"name", "description"}

    def parse_frontmatter(text):
        if not text.startswith("---"):
            return None, "Missing opening frontmatter delimiter"
        lines = text.splitlines()
        try:
            end = lines.index("---", 1)
        except ValueError:
            return None, "Missing closing frontmatter delimiter"
        fm_lines = lines[1:end]
        data = {}
        for line in fm_lines:
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip()
        return data, None

    def main():
        if len(sys.argv) < 2:
            print("Usage: validate_skill.py <skill_path>")
            sys.exit(1)

        skill_path = Path(sys.argv[1])
        errors = []
        warnings = []

        # Check required files
        for f in REQUIRED_FILES:
            if not (skill_path / f).exists():
                errors.append(f"Missing required file: {f}")

        skill_md = skill_path / "SKILL.md"
        if skill_md.exists():
            text = skill_md.read_text()
            fm, err = parse_frontmatter(text)
            if err:
                errors.append(f"Frontmatter parse error: {err}")
            elif fm is not None:
                # Only name + description allowed
                extra_keys = set(fm.keys()) - ALLOWED_FRONTMATTER_KEYS
                if extra_keys:
                    errors.append(f"Frontmatter has disallowed keys: {extra_keys}")
                if "name" not in fm or not fm["name"]:
                    errors.append("Frontmatter missing 'name'")
                if "description" not in fm or not fm["description"]:
                    errors.append("Frontmatter missing 'description'")
                # Description should explain trigger scenarios
                if len(fm.get("description", "")) < 40:
                    warnings.append("description is very short; consider expanding trigger scenarios")

            # Body should not start with a project description pattern
            body_lower = text.lower()
            if "## overview" in body_lower and "this skill was scaffolded" in body_lower:
                warnings.append("SKILL.md still contains scaffold placeholder — replace with real procedural guidance")

            # Check no deep reference chains (no relative links more than 1 hop)
            deep_refs = re.findall(r"\\[.*?\\]\\(((?:[^/()]+/){2,}[^()]+)\\)", text)
            if deep_refs:
                warnings.append(f"Possible deep reference chain(s): {deep_refs}")

        # Check scripts are real files (not empty)
        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists():
            for s in scripts_dir.iterdir():
                if s.suffix == ".py" and s.stat().st_size < 20:
                    errors.append(f"Script appears empty or stub: {s.name}")

        # Summary
        if errors:
            print("[validate_skill] FAILED")
            for e in errors:
                print(f"  ERROR: {e}")
            for w in warnings:
                print(f"  WARN:  {w}")
            sys.exit(1)
        else:
            print("[validate_skill] PASSED")
            for w in warnings:
                print(f"  WARN:  {w}")
            sys.exit(0)

    if __name__ == "__main__":
        main()
'''))

# package_skill.py  ── minimal packager
(scripts_dir / "package_skill.py").write_text(textwrap.dedent('''\
    #!/usr/bin/env python3
    """Package a skill folder into a .tar.gz archive."""
    import sys, tarfile
    from pathlib import Path

    def main():
        if len(sys.argv) < 2:
            print("Usage: package_skill.py <skill_path>")
            sys.exit(1)
        skill_path = Path(sys.argv[1])
        if not skill_path.exists():
            print(f"Error: {skill_path} does not exist")
            sys.exit(1)
        out = skill_path.parent / f"{skill_path.name}.tar.gz"
        with tarfile.open(out, "w:gz") as tar:
            tar.add(skill_path, arcname=skill_path.name)
        print(f"[package_skill] Packaged to: {out}")

    if __name__ == "__main__":
        main()
'''))

# ── 2. References for the skill-creator itself ──
refs_dir = WORKSPACE / "references"
refs_dir.mkdir(exist_ok=True)

(refs_dir / "design-patterns.md").write_text(textwrap.dedent("""\
    # Design Patterns

    ## tool-wrapper
    Exposes a single domain tool with curated guidance.

    ## generator
    Produces consistent output shape from variable inputs.

    ## reviewer
    Contains a checklist; evaluates against explicit criteria.

    ## inversion
    Asks clarifying questions before acting (discovery-first).

    ## pipeline
    Chains ordered steps with explicit checkpoints and gates.

    ## Combination Rule
    For most skill-creation work: inversion + generator + reviewer + pipeline.
"""))

(refs_dir / "best-practices.md").write_text(textwrap.dedent("""\
    # Best Practices

    - Frontmatter: only `name` and `description`. Nothing else.
    - `description` must cover both function AND trigger scenarios.
    - SKILL.md body is procedural (steps, decisions) — not documentary.
    - Each reference file is one hop from SKILL.md. No chains.
    - `scripts/` contain real, runnable programs — no stubs.
    - Avoid README.md, PROJECT.md, status files inside the skill folder.
    - Use progressive disclosure: summary in SKILL.md, depth in references/.
"""))

(refs_dir / "workflows.md").write_text(textwrap.dedent("""\
    # Workflows

    ## Staged Skill with Gates
    Phase 1 → Gate (gaps resolved?) → Phase 2 → Phase 3 → Phase 4 → Phase 5 Gate

    ## Gate Criteria
    - Discovery: inputs, outputs, trigger examples, target directory confirmed.
    - Review: validation passes, no scaffold placeholders, procedural body.
"""))

(refs_dir / "interaction-guide.md").write_text(textwrap.dedent("""\
    # Interaction Guide

    Ask in Chinese when the user is exploring requirements.
    Keep questions short and concrete.
    Maximum 3 clarifying questions per round.
    Summarize: primary job, trigger phrases, constraints, target directory.
"""))

(refs_dir / "output-patterns.md").write_text(textwrap.dedent("""\
    # Output Patterns

    Preferred response order:
    1. Discovery summary
    2. Chosen pattern and why
    3. Planned resources
    4. Files created or changed
    5. Validation result
"""))

# ── 3. The messy proto-skill: "ledger-normalizer" ──
# This is a rough draft left by a data engineer — NOT a valid skill yet.
# It has wrong frontmatter, project-description body, no references, no scripts.
proto_dir = WORKSPACE / "draft_submissions" / "ledger-normalizer-DRAFT"
proto_dir.mkdir(parents=True, exist_ok=True)

# BAD SKILL.md: extra frontmatter keys, documentary body, no steps
(proto_dir / "SKILL.md").write_text(textwrap.dedent("""\
    ---
    name: ledger-normalizer
    description: Normalizes brokerage transaction logs.
    author: jdoe
    version: 0.1.0
    tags: [finance, ETL, ledger]
    ---

    # Ledger Normalizer — Project Overview

    This project was started in Q3 to handle the messy CSV exports from our prime broker.
    The goal is to eventually have something that reads raw trade files and spits out
    normalized ledger entries in a canonical JSON format.

    ## Background
    The finance team has been complaining about manual reconciliation since 2022.
    This tool aims to fix that.

    ## Status
    Work in progress. See PROJECT.md for the roadmap.
"""))

# Distractor files that should NOT be inside a skill
(proto_dir / "PROJECT.md").write_text(textwrap.dedent("""\
    # Project Roadmap
    - Q3: prototype
    - Q4: prod rollout
    - Q1 next year: multi-broker support
"""))

(proto_dir / "README.md").write_text(textwrap.dedent("""\
    # ledger-normalizer
    See SKILL.md for details. This file is here for GitHub rendering.
"""))

(proto_dir / "notes.txt").write_text(textwrap.dedent("""\
    Trigger examples from slack conversations:
    - "normalize this trade file"
    - "convert broker CSV to ledger JSON"
    - "run ledger normalizer on today's drop"
    - "clean up the brokerage export"

    Inputs: raw CSV files with columns: trade_id, symbol, side, qty, price, broker_ts
    Outputs: JSON array, each entry: {id, instrument, direction, quantity, price, timestamp_utc}

    The core transformation logic:
    - Parse broker_ts (format: "YYYYMMDD HH:MM:SS.mmm EST") → ISO-8601 UTC
    - Map side: B→buy, S→sell, SS→short_sell
    - Validate qty > 0, price > 0
    - Reject rows where symbol is empty or "TEST"
    - Output sorted by timestamp_utc ascending
"""))

# ── 4. Deep distractor tree — unrelated projects ──
distractor_base = WORKSPACE / "projects"

# Project A: unrelated ML pipeline
ml_dir = distractor_base / "ml-forecasting" / "src"
ml_dir.mkdir(parents=True, exist_ok=True)
(ml_dir / "train.py").write_text("# placeholder training script\n")
(ml_dir / "config.yaml").write_text("model: xgboost\nfeatures: [close, volume]\n")
(ml_dir.parent / "requirements.txt").write_text("xgboost\npandas\nnumpy\n")
(ml_dir.parent / "README.md").write_text("# ML Forecasting\nNot related to skills.\n")

# Project B: data lake ingestion
lake_dir = distractor_base / "data-lake-ingest" / "pipelines"
lake_dir.mkdir(parents=True, exist_ok=True)
(lake_dir / "ingest_s3.py").write_text("# ingest from S3\nimport boto3\n")
(lake_dir / "schema_v2.json").write_text('{"type": "object", "properties": {"id": {"type": "string"}}}\n')
(lake_dir.parent / "Makefile").write_text("run:\n\tpython pipelines/ingest_s3.py\n")

# Project C: another broken proto-skill (different domain — should NOT be touched)
other_proto = WORKSPACE / "draft_submissions" / "email-triage-DRAFT"
other_proto.mkdir(parents=True, exist_ok=True)
(other_proto / "SKILL.md").write_text(textwrap.dedent("""\
    ---
    name: email-triage
    description: Sort and label incoming emails.
    author: asmith
    version: 0.2.0
    ---
    # Email Triage Project
    This is another broken draft. Do not touch this one.
"""))

# Project D: legacy batch scripts
batch_dir = distractor_base / "legacy-batch" / "scripts"
batch_dir.mkdir(parents=True, exist_ok=True)
for i in range(5):
    (batch_dir / f"job_{i:02d}.sh").write_text(f"#!/bin/bash\necho 'running job {i}'\n")
(batch_dir.parent / "cron.txt").write_text("0 2 * * * /scripts/job_00.sh\n")

# Project E: monitoring dashboards
mon_dir = distractor_base / "monitoring" / "dashboards"
mon_dir.mkdir(parents=True, exist_ok=True)
(mon_dir / "latency.json").write_text('{"panels": [], "title": "Latency"}\n')
(mon_dir / "errors.json").write_text('{"panels": [], "title": "Errors"}\n')

# ── 5. Target skills library (where the new skill must land) ──
skills_lib = WORKSPACE / "codex_skills"
skills_lib.mkdir(exist_ok=True)
(skills_lib / ".gitkeep").touch()

print("Workspace initialized.")
print("Draft proto-skill at: draft_submissions/ledger-normalizer-DRAFT/")
print("Skills library target: codex_skills/")