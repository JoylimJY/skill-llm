"""Read a skill directory and call Claude API to synthesize benchmark instances."""

import json
import os
import re
from pathlib import Path

import anthropic

from .schema import InstanceSpec

SYNTHESIS_PROMPT = """You are a benchmark task synthesizer. Given a skill definition
(used by an AI coding assistant), generate a complete task instance.

## Skill Content

### SKILL.md (entry point)
{skill_md}

### Referenced Files
{references}

## Your Task

Generate a {difficulty} difficulty task for this skill. Output a JSON object with:

1. "category": what type of operation this task tests (e.g., "merge", "extract", "create")
2. "prompt": a realistic user request (as if typed in a terminal). Vary tone and detail level.
3. "dockerfile": a Dockerfile with all dependencies needed. Base image: python:3.11-slim or node:20-slim.
   Must include everything needed to run the task AND the eval.
4. "gen_inputs_script": a Python script that, when executed, creates input files in the
   current directory. Must be DETERMINISTIC (use fixed seeds). Embed known marker content
   in generated files so eval can verify correctness.
5. "setup_script": bash script to run after container starts (install extra tools, etc.)
6. "eval_script": a Python script that takes one argument (workspace directory path),
   checks if the task was completed correctly, and prints a JSON result:
   {{"passed": bool, "score": float, "checks": [{{"name": str, "passed": bool, "detail": str}}]}}
   The script must be self-contained (only use packages installed via the Dockerfile or pip-installable packages).
7. "expected": metadata about expected outputs (filenames, key properties)

## Difficulty Guidelines
- easy: single straightforward operation, clear inputs/outputs
- medium: multi-step operation, requires combining techniques or handling edge cases
- hard: complex workflow, multiple tools, nuanced requirements, or unusual edge cases

## Constraints
- gen_inputs_script must produce files with verifiable marker content
- eval_script must test concrete, objectively verifiable properties (file exists, page count,
  text contains, data matches, etc.)
- Dockerfile must include everything needed to run the task AND the eval
- All output in English
- Return ONLY the JSON object, no markdown fences or explanation"""


def load_skill(skill_dir: str) -> dict:
    """Load SKILL.md and selectively load referenced sub-files.

    1. Read SKILL.md (the entry point)
    2. Parse for references to sub-files:
       - Explicit references like "see REFERENCE.md", "read FORMS.md"
       - Relative links like [Guide](./reference/python_mcp_server.md)
       - Script references like "scripts/recalc.py"
    3. Load only referenced files (not everything in the directory)
    4. Return {"skill_md": str, "references": {filename: content}}
    """
    skill_dir = Path(skill_dir).resolve()
    skill_md_path = skill_dir / "SKILL.md"

    if not skill_md_path.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    skill_md = skill_md_path.read_text()

    # Find referenced files in SKILL.md
    ref_patterns = [
        # "see REFERENCE.md", "read FORMS.md", "consult GUIDE.md"
        r'(?:see|read|consult|check|refer to|follow)\s+([A-Z][A-Z0-9_-]*\.(?:md|txt|py|sh))',
        # Markdown links: [text](./path/to/file.md) or [text](path/to/file.md)
        r'\[.*?\]\(\.?/?([^)]+\.(?:md|txt|py|sh|ts|js))\)',
        # Backtick references: `REFERENCE.md`, `scripts/foo.py`
        r'`([A-Za-z0-9_/.-]+\.(?:md|txt|py|sh|ts|js))`',
    ]

    referenced_files = set()
    for pattern in ref_patterns:
        matches = re.findall(pattern, skill_md, re.IGNORECASE)
        referenced_files.update(matches)

    # Load referenced files (case-insensitive matching)
    # Build a map of lowercase filename -> actual path for all files in skill_dir
    actual_files = {}
    for p in skill_dir.rglob("*"):
        if p.is_file():
            rel = str(p.relative_to(skill_dir))
            actual_files[rel.lower()] = p

    references = {}
    for ref_file in sorted(referenced_files):
        # Try exact match first, then case-insensitive
        ref_path = skill_dir / ref_file
        if not ref_path.exists():
            matched = actual_files.get(ref_file.lower())
            if matched:
                ref_path = matched
            else:
                continue
        if ref_path.is_file():
            try:
                content = ref_path.read_text()
                references[ref_file] = content
            except Exception:
                pass  # Skip unreadable files

    return {"skill_md": skill_md, "references": references}


def _format_references(references: dict) -> str:
    """Format referenced files for the synthesis prompt."""
    if not references:
        return "(No additional referenced files)"
    parts = []
    for filename, content in references.items():
        parts.append(f"#### {filename}\n```\n{content}\n```")
    return "\n\n".join(parts)


def synthesize_instance(
    skill_data: dict,
    skill_name: str,
    difficulty: str,
    index: int,
) -> InstanceSpec:
    """Call Claude API with the synthesis prompt, parse JSON response."""
    client = anthropic.Anthropic()

    prompt = SYNTHESIS_PROMPT.format(
        skill_md=skill_data["skill_md"],
        references=_format_references(skill_data["references"]),
        difficulty=difficulty,
    )

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        # Remove first and last fence lines
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response_text = "\n".join(lines)

    data = json.loads(response_text)

    instance_id = f"{skill_name}_{data['category']}_{difficulty}_{index:03d}"

    return InstanceSpec(
        instance_id=instance_id,
        skill_name=skill_name,
        category=data["category"],
        difficulty=difficulty,
        prompt=data["prompt"],
        dockerfile=data["dockerfile"],
        gen_inputs_script=data["gen_inputs_script"],
        setup_script=data["setup_script"],
        eval_script=data["eval_script"],
        expected=data.get("expected", {}),
    )


def write_instance_dir(spec: InstanceSpec, output_dir: str = "instances") -> str:
    """Write an InstanceSpec to disk as a complete instance directory."""
    base = Path(output_dir) / spec.instance_id
    runtime_dir = base / "runtime"
    workspace_dir = runtime_dir / "workspace"
    eval_dir = base / "eval"

    # Create directories
    workspace_dir.mkdir(parents=True, exist_ok=True)
    eval_dir.mkdir(parents=True, exist_ok=True)

    # task.json
    task_meta = {
        "instance_id": spec.instance_id,
        "skill_name": spec.skill_name,
        "prompt": spec.prompt,
        "difficulty": spec.difficulty,
        "category": spec.category,
    }
    (base / "task.json").write_text(json.dumps(task_meta, indent=2))

    # runtime files
    (runtime_dir / "Dockerfile").write_text(spec.dockerfile)
    (runtime_dir / "gen_inputs.py").write_text(spec.gen_inputs_script)
    (runtime_dir / "setup.sh").write_text(spec.setup_script)

    # Copy skill.md into runtime for injection into system prompt
    (runtime_dir / "skill.md").write_text(
        f"# Skill: {spec.skill_name}\n\n"
        "This is the skill definition that should guide the AI assistant.\n\n"
        f"(Original SKILL.md content is available at runtime.)\n"
    )

    # eval files
    (eval_dir / "eval.py").write_text(spec.eval_script)
    (eval_dir / "expected.json").write_text(json.dumps(spec.expected, indent=2))

    return str(base)


def synthesize_skill(
    skill_dir: str,
    num_instances: int = 10,
    output_dir: str = "instances",
) -> list[str]:
    """Synthesize multiple instances for one skill across difficulty levels."""
    skill_data = load_skill(skill_dir)
    skill_name = Path(skill_dir).name

    # Distribute instances across difficulty levels
    difficulties = ["easy", "medium", "hard"]
    per_difficulty = num_instances // len(difficulties)
    remainder = num_instances % len(difficulties)

    instances = []
    global_index = 0

    for diff_idx, difficulty in enumerate(difficulties):
        count = per_difficulty + (1 if diff_idx < remainder else 0)
        for i in range(count):
            print(f"Synthesizing {skill_name} [{difficulty}] instance {i+1}/{count}...")
            spec = synthesize_instance(skill_data, skill_name, difficulty, global_index)
            path = write_instance_dir(spec, output_dir)
            instances.append(path)
            global_index += 1
            print(f"  → {spec.instance_id}")

    return instances
