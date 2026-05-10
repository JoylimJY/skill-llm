"""Read a skill directory and call Claude API to synthesize benchmark instances."""

import json
import os
import re
from pathlib import Path
import shutil
import anthropic

from .prompts import load_prompt
from .schema import InstanceSpec


def load_skill(skill_dir: str) -> dict:
    """Load SKILL.md and selectively load referenced sub-files.

    1. Read SKILL.md (the entry point)
    2. Parse for references to sub-files:
       - Explicit references like "see REFERENCE.md", "read FORMS.md"
       - Relative links like [Guide](./reference/python_mcp_server.md)
       - Script references like "scripts/recalc.py"
    3. Load only referenced files (not everything in the directory)
    4. Return {"skill_md": str, "references": {filename: content}, "file_tree": [str]}
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

    # Generate complete file tree for the prompt
    file_tree = []
    for p in sorted(skill_dir.rglob("*")):
        if p.is_file():
            rel = str(p.relative_to(skill_dir))
            file_tree.append(rel)

    return {"skill_md": skill_md, "references": references, "file_tree": file_tree}


def _format_references(references: dict) -> str:
    """Format referenced files for the synthesis prompt."""
    if not references:
        return "(No additional referenced files)"
    parts = []
    for filename, content in references.items():
        parts.append(f"#### {filename}\n```\n{content}\n```")
    return "\n\n".join(parts)


def _format_file_tree(file_tree: list) -> str:
    """Format the file tree for the synthesis prompt."""
    if not file_tree:
        return "(No files in skill context)"
    lines = ["```"]
    for f in file_tree:
        lines.append(f)
    lines.append("```")
    return "\n".join(lines)


def _extract_xml_tag(text: str, tag: str) -> str:
    """Helper function to extract content inside XML-style tags with high robustness."""
    pattern = f"<{tag}[^>]*>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if not match:
        raise ValueError(f"Missing required XML tag: <{tag}>")
        
    content = match.group(1).strip()
    
    if content.startswith("```"):
        lines = content.split('\n')
        
        if len(lines) > 0 and lines[0].strip().startswith("```"):
            lines = lines[1:]
            
        if len(lines) > 0 and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
            
        content = "\n".join(lines).strip()
        
    return content


def _parse_llm_response(response_text: str) -> dict:
    """Parse the response from Claude, supporting both XML tags and pure JSON fallbacks."""
    
    try:
        dockerfile = _extract_xml_tag(response_text, "dockerfile")
        gen_inputs_script = _extract_xml_tag(response_text, "gen_inputs_script")
        setup_script = _extract_xml_tag(response_text, "setup_script")
        eval_script = _extract_xml_tag(response_text, "eval_script")
        try:
            solution_script = _extract_xml_tag(response_text, "solution_script")
        except ValueError:
            solution_script = ""
        
        metadata_str = _extract_xml_tag(response_text, "metadata")
        if metadata_str.startswith("```json"):
            metadata_str = metadata_str.replace("```json", "", 1).rstrip("```").strip()
        metadata = json.loads(metadata_str)
        
        return {
            "dockerfile": dockerfile,
            "gen_inputs_script": gen_inputs_script,
            "setup_script": setup_script,
            "eval_script": eval_script,
            "solution_script": solution_script,
            "category": metadata.get("category", "unknown"),
            "prompt": metadata.get("prompt", ""),
            "expected": metadata.get("expected", {})
        }
    except ValueError:
        print("  XML tags not found. Attempting to parse as raw JSON...")
        
        clean_json_text = response_text
        if "```json" in response_text:
            clean_json_text = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL).group(1)
        elif "```" in response_text:
            clean_json_text = re.search(r"```\s*(.*?)\s*```", response_text, re.DOTALL).group(1)
            
        try:
            data = json.loads(clean_json_text)
            return {
                "dockerfile": data.get("dockerfile", ""),
                "gen_inputs_script": data.get("gen_inputs_script", ""),
                "setup_script": data.get("setup_script", ""),
                "eval_script": data.get("eval_script", ""),
                "solution_script": data.get("solution_script", ""),
                "category": data.get("metadata", {}).get("category") or data.get("category", "unknown"),
                "prompt": data.get("metadata", {}).get("prompt") or data.get("prompt", ""),
                "expected": data.get("metadata", {}).get("expected") or data.get("expected", {})
            }
        except json.JSONDecodeError:
            raise ValueError("Failed to parse LLM response as either XML or JSON.")


def synthesize_instance(
    skill_data: dict,
    skill_name: str,
    difficulty: str,
    index: int,
) -> InstanceSpec:
    """Call Claude API with the synthesis prompt, parse XML/JSON response."""
    client = anthropic.Anthropic()

    prompt = load_prompt(
        "synthesis",
        skill_md=skill_data["skill_md"],
        references=_format_references(skill_data["references"]),
        file_tree=_format_file_tree(skill_data["file_tree"]),
        difficulty=difficulty,
    )

    def _call_claude():
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=16384,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    response_text = _call_claude()

    try:
        parsed_data = _parse_llm_response(response_text)
    except ValueError as e:
        debug_file = f"debug_failed_{skill_name}_{difficulty}_{index}.txt"
        with open(debug_file, "w", encoding="utf-8") as f:
            f.write(response_text)
        
        print(f"  Parse error: {e}")
        print(f"  Full response saved to {debug_file} for debugging.")

        print(f"  Retrying Claude API call...")
        response_text = _call_claude()
        
        try:
            parsed_data = _parse_llm_response(response_text)
        except ValueError as e2:
            retry_debug_file = f"debug_failed_retry_{skill_name}_{difficulty}_{index}.txt"
            with open(retry_debug_file, "w", encoding="utf-8") as f:
                f.write(response_text)
            print(f"  Retry failed. Response saved to {retry_debug_file}")
            raise e2

    instance_id = f"{skill_name}_{parsed_data['category']}_{difficulty}_{index:03d}"

    return InstanceSpec(
        instance_id=instance_id,
        skill_name=skill_name,
        category=parsed_data["category"],
        difficulty=difficulty,
        prompt=parsed_data["prompt"],
        dockerfile=parsed_data["dockerfile"],
        gen_inputs_script=parsed_data["gen_inputs_script"],
        setup_script=parsed_data["setup_script"],
        eval_script=parsed_data["eval_script"],
        solution_script=parsed_data.get("solution_script", ""),
        expected=parsed_data["expected"],
    )


def write_instance_dir(spec: InstanceSpec, skill_dir: str, output_dir: str = "instances") -> str:
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
    if spec.solution_script:
        (runtime_dir / "solution.sh").write_text(spec.solution_script)

    skill_context_dir = workspace_dir / "skill_context"

    shutil.copytree(skill_dir, skill_context_dir, dirs_exist_ok=True)

    (runtime_dir / "skill.md").write_text(
        f"# Skill: {spec.skill_name}\n\n"
        "This is the skill definition that should guide the AI assistant.\n\n"
        f"(The complete and original SKILL.md and all references are available in your workspace at ./skill_context/)\n"
    )

    # eval files
    (eval_dir / "eval.py").write_text(spec.eval_script)
    (eval_dir / "expected.json").write_text(json.dumps(spec.expected, indent=2))

    return str(base)


def fix_environment(
    dockerfile: str,
    error_log: str,
    gen_inputs_script: str = "",
    setup_script: str = "",
) -> dict:
    """调用 Claude 诊断并修复环境，仅更新需要修改的文件。"""
    client = anthropic.Anthropic()

    prompt = load_prompt(
        "fix_environment",
        dockerfile=dockerfile,
        error_log=error_log,
        gen_inputs_script=gen_inputs_script or "(not available)",
        setup_script=setup_script or "(not available)",
    )

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()

    def safe_extract(text, tag):
        try:
            return _extract_xml_tag(text, tag)
        except ValueError:
            return None

    fixed_docker = safe_extract(response_text, "dockerfile")
    fixed_gen = safe_extract(response_text, "gen_inputs_script")
    fixed_setup = safe_extract(response_text, "setup_script")

    return {
        "dockerfile": fixed_docker if fixed_docker is not None else dockerfile,
        "gen_inputs_script": fixed_gen if fixed_gen is not None else gen_inputs_script,
        "setup_script": fixed_setup if fixed_setup is not None else setup_script,
        "changed": [tag for tag, val in [("dockerfile", fixed_docker), 
                                        ("gen_inputs", fixed_gen), 
                                        ("setup", fixed_setup)] if val is not None]
    }


def synthesize_skill(
    skill_dir: str,
    num_instances: int = 10,
    output_dir: str = "instances",
) -> list[str]:
    """Synthesize multiple instances for one skill across difficulty levels."""
    skill_data = load_skill(skill_dir)
    skill_name = Path(skill_dir).name

    # Distribute instances across difficulty levels
    # difficulties = ["easy", "medium", "hard"]
    difficulties = ["hard"]
    per_difficulty = num_instances // len(difficulties)
    remainder = num_instances % len(difficulties)

    instances = []
    global_index = 0

    for diff_idx, difficulty in enumerate(difficulties):
        count = per_difficulty + (1 if diff_idx < remainder else 0)
        for i in range(count):
            print(f"Synthesizing {skill_name} [{difficulty}] instance {i+1}/{count}...")
            spec = synthesize_instance(skill_data, skill_name, difficulty, global_index)
            path = write_instance_dir(spec, skill_dir, output_dir)
            instances.append(path)
            global_index += 1
            print(f"  → {spec.instance_id}")

    return instances