"""Helpers for loading, snapshotting, and resolving skill context files."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

SKILL_PLACEHOLDER_TEXT = "(Original SKILL.md content is available at runtime.)"
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DIRECT_SKILL_ROOTS = ("anthropic-skills",)
_RECURSIVE_SKILL_ROOTS = ("agent_skills", "awesome-claude-skills-master")


def load_skill(skill_dir: str | Path) -> dict:
    """Load SKILL.md and selectively load referenced sub-files."""
    skill_dir = Path(skill_dir).resolve()
    skill_md_path = skill_dir / "SKILL.md"

    if not skill_md_path.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    skill_md = skill_md_path.read_text(encoding="utf-8")

    ref_patterns = [
        r'(?:see|read|consult|check|refer to|follow)\s+([A-Z][A-Z0-9_-]*\.(?:md|txt|py|sh))',
        r'\[.*?\]\(\.?/?([^)]+\.(?:md|txt|py|sh|ts|js))\)',
        r'`([A-Za-z0-9_/.-]+\.(?:md|txt|py|sh|ts|js))`',
    ]

    referenced_files = set()
    for pattern in ref_patterns:
        matches = re.findall(pattern, skill_md, re.IGNORECASE)
        referenced_files.update(matches)

    actual_files: dict[str, Path] = {}
    for path in skill_dir.rglob("*"):
        if path.is_file():
            rel = str(path.relative_to(skill_dir))
            actual_files[rel.lower()] = path

    references: dict[str, str] = {}
    for ref_file in sorted(referenced_files):
        ref_path = skill_dir / ref_file
        if not ref_path.exists():
            matched = actual_files.get(ref_file.lower())
            if matched:
                ref_path = matched
            else:
                continue
        if ref_path.is_file():
            try:
                references[ref_file] = ref_path.read_text(encoding="utf-8")
            except Exception:
                pass

    return {
        "skill_dir": str(skill_dir),
        "skill_md": skill_md,
        "references": references,
    }


def resolve_skill_source_dir(skill_name: str, repo_root: Path | None = None) -> Path | None:
    """Resolve the source skill directory by skill name."""
    repo_root = repo_root or _REPO_ROOT
    skill_name = skill_name.strip()
    if not skill_name:
        return None

    for root_name in _DIRECT_SKILL_ROOTS:
        direct_skill = repo_root / root_name / skill_name
        if (direct_skill / "SKILL.md").exists():
            return direct_skill

    for root_name in _RECURSIVE_SKILL_ROOTS:
        root = repo_root / root_name
        if not root.exists():
            continue
        matches = sorted(
            path.parent for path in root.rglob("SKILL.md")
            if path.parent.name == skill_name
        )
        if len(matches) == 1:
            return matches[0]

    return None


def materialize_skill_context(
    skill_dir: str | Path,
    dest_dir: str | Path,
    skill_data: dict | None = None,
) -> list[str]:
    """Write a skill context snapshot preserving relative reference paths."""
    skill_dir = Path(skill_dir).resolve()
    dest_dir = Path(dest_dir)
    skill_data = skill_data or load_skill(skill_dir)

    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    written_files = ["SKILL.md"]
    (dest_dir / "SKILL.md").write_text(skill_data["skill_md"], encoding="utf-8")

    for rel_path, content in sorted(skill_data["references"].items()):
        out_path = dest_dir / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        written_files.append(rel_path)

    try:
        source_display = str(skill_dir.relative_to(_REPO_ROOT))
    except ValueError:
        source_display = str(skill_dir)

    manifest = {
        "skill_name": skill_dir.name,
        "source_dir": source_display,
        "files": written_files,
        "reference_files": sorted(skill_data["references"].keys()),
    }
    (dest_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return written_files


def write_runtime_skill_files(
    runtime_dir: str | Path,
    skill_dir: str | Path,
    skill_data: dict | None = None,
) -> None:
    """Persist runtime skill files for an instance."""
    runtime_dir = Path(runtime_dir)
    skill_dir = Path(skill_dir).resolve()
    skill_data = skill_data or load_skill(skill_dir)

    (runtime_dir / "skill.md").write_text(skill_data["skill_md"], encoding="utf-8")
    materialize_skill_context(skill_dir, runtime_dir / "skill_context", skill_data)
