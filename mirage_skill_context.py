import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "src"))

from skill_context import load_skill, resolve_skill_source_dir, write_runtime_skill_files


def collect_instance_dirs(root: Path) -> list[Path]:
    return sorted(task_json.parent for task_json in root.rglob("task.json"))


def migrate_instance(instance_dir: Path, overwrite: bool = False) -> str:
    runtime_dir = instance_dir / "runtime"
    if not runtime_dir.exists():
        return "skip:no_runtime"

    skill_context_dir = runtime_dir / "skill_context"
    if skill_context_dir.exists() and not overwrite:
        return "skip:already_has_skill_context"

    task_json_path = instance_dir / "task.json"
    task_data = json.loads(task_json_path.read_text(encoding="utf-8"))
    skill_name = task_data.get("skill_name", "").strip()
    if not skill_name:
        return "skip:no_skill_name"

    skill_source_dir = resolve_skill_source_dir(skill_name)
    if skill_source_dir is None:
        return "skip:missing_skill_source"

    skill_data = load_skill(skill_source_dir)
    write_runtime_skill_files(runtime_dir, skill_source_dir, skill_data)
    return "migrated"


def main():
    parser = argparse.ArgumentParser(description="Backfill runtime skill context for existing instances")
    parser.add_argument("--instances-dir", default="instances_stage1-final", help="Root directory containing instances")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing runtime/skill_context")
    args = parser.parse_args()

    instances_dir = Path(args.instances_dir)
    if not instances_dir.exists():
        raise SystemExit(f"Instances directory not found: {instances_dir}")

    counts: dict[str, int] = {}
    instance_dirs = collect_instance_dirs(instances_dir)

    for instance_dir in instance_dirs:
        result = migrate_instance(instance_dir, overwrite=args.overwrite)
        counts[result] = counts.get(result, 0) + 1
        print(f"{result:<30} {instance_dir}")

    print("\n=== Migration Summary ===")
    print(f"instances scanned: {len(instance_dirs)}")
    for key in sorted(counts):
        print(f"{key}: {counts[key]}")


if __name__ == "__main__":
    main()
