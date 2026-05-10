"""Helpers for loading, snapshotting, and resolving skill context files."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

SKILL_PLACEHOLDER_TEXT = "(Original SKILL.md content is available at runtime.)"
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DIRECT_SKILL_ROOTS = ("anthropic-skills",)
_RECURSIVE_SKILL_ROOTS = ("agent_skills", "awesome-claude-skills-master", "openclaw_skills")


def load_skill(skill_dir: str | Path) -> dict:
    """Load SKILL.md. (Regex parsing removed: we now copy everything)."""
    skill_dir = Path(skill_dir).resolve()
    skill_md_path = skill_dir / "SKILL.md"

    if not skill_md_path.exists():
        raise FileNotFoundError(f"SKILL.md not found in {skill_dir}")

    skill_md = skill_md_path.read_text(encoding="utf-8")

    return {
        "skill_dir": str(skill_dir),
        "skill_md": skill_md,
        "references": {},  # 保留空字典以兼容外部旧代码结构
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
    """Copy the ENTIRE skill directory to preserve all tools, scripts, and binaries."""
    skill_dir = Path(skill_dir).resolve()
    dest_dir = Path(dest_dir)
    
    # 1. 确保目标文件夹是干净的
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
        
    # 2. 核心改动：全量拷贝目录树（这会自动保留所有的文件权限和二进制文件）
    shutil.copytree(skill_dir, dest_dir)

    # 3. 统计被拷贝过来的所有文件，用于生成清单
    written_files = []
    for path in dest_dir.rglob("*"):
        if path.is_file():
            written_files.append(str(path.relative_to(dest_dir)))

    try:
        source_display = str(skill_dir.relative_to(_REPO_ROOT))
    except ValueError:
        source_display = str(skill_dir)

    # 4. 生成或覆盖 manifest.json
    manifest = {
        "skill_name": skill_dir.name,
        "source_dir": source_display,
        "files": sorted(written_files),
        "reference_files": sorted([f for f in written_files if f not in ("SKILL.md", "manifest.json")]),
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

