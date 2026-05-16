import os
import random
import stat

random.seed(42)

workspace = "/workspace"

# ── 1. Create the init_skill.py script (the real tool the agent must use) ──────
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

init_skill_content = '''\
#!/usr/bin/env python3
"""Initializes a new skill directory with template files."""
import argparse
import os
import sys

SKILL_MD_TEMPLATE = """---
name: {skill_name}
description: TODO: Describe what this skill does and when to use it. Include specific triggers and use cases.
---

# {skill_title}

TODO: Add instructions for using this skill.

## Overview

TODO: Describe the skill's purpose and capabilities.

## Usage

TODO: Add usage examples and workflow guidance.
"""

EXAMPLE_SCRIPT = """\
#!/usr/bin/env python3
"""Example script - customize or delete if not needed."""
import sys

def main():
    print("Example script - replace with actual implementation")

if __name__ == "__main__":
    main()
"""

EXAMPLE_REFERENCE = """\
# Reference Documentation

TODO: Add reference material here, or delete this file if not needed.
"""

EXAMPLE_ASSET_NOTE = """\
# Assets Directory

Place asset files here (templates, images, fonts, etc.) or delete this directory if not needed.
"""

def to_title(skill_name: str) -> str:
    return " ".join(word.capitalize() for word in skill_name.replace("-", " ").split())

def init_skill(skill_name: str, output_path: str) -> None:
    skill_dir = os.path.join(output_path, skill_name)
    if os.path.exists(skill_dir):
        print(f"Error: Skill directory already exists: {skill_dir}", file=sys.stderr)
        sys.exit(1)

    # Create directory structure
    os.makedirs(skill_dir)
    os.makedirs(os.path.join(skill_dir, "scripts"))
    os.makedirs(os.path.join(skill_dir, "references"))
    os.makedirs(os.path.join(skill_dir, "assets"))

    # Write SKILL.md
    skill_md = SKILL_MD_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=to_title(skill_name)
    )
    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write(skill_md)

    # Write example files
    with open(os.path.join(skill_dir, "scripts", "example_script.py"), "w") as f:
        f.write(EXAMPLE_SCRIPT)

    with open(os.path.join(skill_dir, "references", "example_reference.md"), "w") as f:
        f.write(EXAMPLE_REFERENCE)

    with open(os.path.join(skill_dir, "assets", "README_ASSETS.txt"), "w") as f:
        f.write(EXAMPLE_ASSET_NOTE)

    print(f"Skill initialized at: {skill_dir}")
    print(f"Next steps:")
    print(f"  1. Edit {skill_dir}/SKILL.md")
    print(f"  2. Add scripts to {skill_dir}/scripts/")
    print(f"  3. Add references to {skill_dir}/references/")
    print(f"  4. Validate with: scripts/quick_validate.py {skill_dir}")

def main():
    parser = argparse.ArgumentParser(description="Initialize a new skill directory")
    parser.add_argument("skill_name", help="Name of the skill (use hyphen-case, e.g., my-skill)")
    parser.add_argument("--path", required=True, help="Output directory for the skill")
    args = parser.parse_args()

    if not os.path.isdir(args.path):
        os.makedirs(args.path, exist_ok=True)

    init_skill(args.skill_name, args.path)

if __name__ == "__main__":
    main()
'''

with open(os.path.join(scripts_dir, "init_skill.py"), "w") as f:
    f.write(init_skill_content)

# ── 2. Create quick_validate.py ─────────────────────────────────────────────
quick_validate_content = '''\
#!/usr/bin/env python3
"""Validates a skill directory structure and SKILL.md format."""
import argparse
import os
import re
import sys
import yaml

ALLOWED_FRONTMATTER_FIELDS = {"name", "description", "license", "allowed-tools", "metadata"}
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
HYPHEN_CASE_PATTERN = re.compile(r'^[a-z][a-z0-9]*(-[a-z0-9]+)*$')

def parse_frontmatter(content: str):
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return None, content
    end = content.find("---", 3)
    if end == -1:
        return None, content
    fm_str = content[3:end].strip()
    try:
        fm = yaml.safe_load(fm_str)
        body = content[end+3:].strip()
        return fm, body
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")

def validate_skill(skill_path: str) -> list:
    errors = []
    warnings = []

    # Check SKILL.md exists
    skill_md_path = os.path.join(skill_path, "SKILL.md")
    if not os.path.isfile(skill_md_path):
        errors.append("SKILL.md not found")
        return errors

    with open(skill_md_path, "r") as f:
        content = f.read()

    # Parse frontmatter
    try:
        fm, body = parse_frontmatter(content)
    except ValueError as e:
        errors.append(str(e))
        return errors

    if fm is None:
        errors.append("Missing YAML frontmatter (must start with ---)")
        return errors

    # Check required fields
    if "name" not in fm:
        errors.append("Missing required frontmatter field: name")
    else:
        name = str(fm["name"])
        if not HYPHEN_CASE_PATTERN.match(name):
            errors.append(f"name must be hyphen-case (e.g., my-skill), got: {name!r}")
        if len(name) > MAX_NAME_LENGTH:
            errors.append(f"name exceeds max length of {MAX_NAME_LENGTH} chars: {len(name)}")

    if "description" not in fm:
        errors.append("Missing required frontmatter field: description")
    else:
        desc = str(fm["description"])
        if len(desc) > MAX_DESCRIPTION_LENGTH:
            errors.append(f"description exceeds max length of {MAX_DESCRIPTION_LENGTH} chars: {len(desc)}")
        if "<" in desc or ">" in desc:
            errors.append("description must not contain angle brackets (< or >)")

    # Check for disallowed frontmatter fields
    if isinstance(fm, dict):
        for field in fm:
            if field not in ALLOWED_FRONTMATTER_FIELDS:
                errors.append(f"Disallowed frontmatter field: {field!r}. Allowed: {sorted(ALLOWED_FRONTMATTER_FIELDS)}")

    # Check body is not empty
    if not body or len(body.strip()) < 10:
        errors.append("SKILL.md body is empty or too short")

    return errors

def main():
    parser = argparse.ArgumentParser(description="Validate a skill directory")
    parser.add_argument("skill_path", help="Path to the skill directory")
    args = parser.parse_args()

    if not os.path.isdir(args.skill_path):
        print(f"Error: Not a directory: {args.skill_path}", file=sys.stderr)
        sys.exit(1)

    errors = validate_skill(args.skill_path)

    if errors:
        print(f"Validation FAILED for: {args.skill_path}")
        for err in errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    else:
        print(f"Validation PASSED for: {args.skill_path}")
        print("  ✓ All checks passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
'''

with open(os.path.join(scripts_dir, "quick_validate.py"), "w") as f:
    f.write(quick_validate_content)

# ── 3. Create deeply nested distractor structure ──────────────────────────────
# Simulate a real project workspace with many unrelated files

dirs_to_create = [
    "projects/data-platform/etl",
    "projects/data-platform/tests",
    "projects/data-platform/config",
    "projects/legacy/fhir-v1/mappings",
    "projects/legacy/fhir-v1/docs",
    "archive/old-scripts",
    "archive/old-skills/broken-attempt",
    "docs/internal",
    "tools/linting",
    "tools/ci",
    "tmp/scratch",
]

for d in dirs_to_create:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "projects/data-platform/etl/pipeline.py": """\
# ETL pipeline for FHIR data
import json

def transform_patient(raw: dict) -> dict:
    return {"id": raw.get("id"), "name": raw.get("name", {}).get("text")}
""",
    "projects/data-platform/etl/fhir_utils.py": """\
# FHIR utility functions
RESOURCE_TYPES = ["Patient", "Observation", "Encounter", "Condition", "Medication"]

def validate_resource_type(rt: str) -> bool:
    return rt in RESOURCE_TYPES
""",
    "projects/data-platform/tests/test_pipeline.py": """\
import pytest
def test_transform():
    assert True
""",
    "projects/data-platform/config/pipeline.yaml": """\
source: fhir-r4
destination: bigquery
batch_size: 100
""",
    "projects/legacy/fhir-v1/mappings/patient_map.json": """\
{"Patient": {"id": "$.id", "name": "$.name[0].text", "dob": "$.birthDate"}}
""",
    "projects/legacy/fhir-v1/docs/migration_notes.txt": """\
Migration from FHIR R3 to R4:
- Patient.name changed from string to HumanName
- Observation.value[x] polymorphic field updated
""",
    "archive/old-scripts/convert_hl7.py": """\
#!/usr/bin/env python3
# OLD - do not use
print("HL7 v2 to FHIR converter - deprecated")
""",
    "archive/old-skills/broken-attempt/SKILL.md": """\
---
name: fhir transformer
version: 0.1
author: devteam
description: <Skill for transforming FHIR resources> - use when working with FHIR data
---
# FHIR Transformer

This is an old broken attempt at the skill.

## Usage
See README.md for details.
""",
    "archive/old-skills/broken-attempt/README.md": """\
# FHIR Transformer Skill

This skill was never finished. Do not use.
""",
    "docs/internal/fhir_r4_schema.md": """\
# FHIR R4 Schema Reference

## Patient Resource
- id: string
- name: HumanName[]
- birthDate: date
- gender: code

## Observation Resource
- id: string
- status: code
- code: CodeableConcept
- subject: Reference(Patient)
- value[x]: Quantity | string | boolean

## Encounter Resource
- id: string
- status: code
- class: Coding
- subject: Reference(Patient)
- period: Period
""",
    "docs/internal/coding_standards.md": """\
# Coding Standards

Use PEP8 for Python.
Use hyphen-case for directory names.
Document all public functions.
""",
    "tools/linting/config.json": '{"rules": {"max-line-length": 120}}',
    "tools/ci/run_tests.sh": "#!/bin/bash\npytest projects/ -v\n",
    "tmp/scratch/notes.txt": "FHIR transformer skill - need to create this properly using the skill framework",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# ── 4. Create a skills directory with an existing (unrelated) skill ────────────
skills_dir = os.path.expanduser("~/.deepagents/agent/skills")
os.makedirs(skills_dir, exist_ok=True)

# An existing skill to show what a valid skill looks like (distractor)
existing_skill_dir = os.path.join(skills_dir, "csv-exporter")
os.makedirs(existing_skill_dir, exist_ok=True)
with open(os.path.join(existing_skill_dir, "SKILL.md"), "w") as f:
    f.write("""\
---
name: csv-exporter
description: Exports data tables to CSV format. Use when the user asks to export data, download a spreadsheet, or save tabular data as CSV.
---

# CSV Exporter

Export data to CSV using the pandas library.

## Quick Start

```python
import pandas as pd
df.to_csv("output.csv", index=False)
```
""")

print("Workspace initialized successfully.")
print(f"Scripts available: {scripts_dir}")
print(f"Skills directory: {skills_dir}")