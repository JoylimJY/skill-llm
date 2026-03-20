"""CLI entry point for SkillBench: synthesize / build / evaluate."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .synthesizer import synthesize_skill, load_skill, write_instance_dir
from .sandbox import Sandbox, BuildFailedError
from .evaluator import evaluate, evaluate_in_container
from .schema import InstanceSpec, RunSummary


def resolve_run_dir(args) -> Path:
    """Resolve the run output directory from --run-dir or generate a default."""
    if hasattr(args, "run_dir") and args.run_dir:
        return Path(args.run_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path("results") / f"run_{ts}"


def save_result_to_run(result, instance_dir: str, run_dir: Path):
    """Save evaluation result to the run directory."""
    instance_id = Path(instance_dir).name
    out = run_dir / instance_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(result.to_json())
    return out


def cmd_synthesize(args):
    """Synthesize task instances from a skill directory."""
    print(f"Synthesizing {args.num} instances from {args.skill_dir}...")
    paths = synthesize_skill(args.skill_dir, args.num, args.output_dir)
    print(f"\nDone. Generated {len(paths)} instances:")
    for p in paths:
        print(f"  {p}")


def cmd_build(args):
    """Build Docker image and create sandbox for an instance (with LLM retry)."""
    sandbox = Sandbox()
    instance_dir = args.instance

    print(f"Building Docker image for {instance_dir}...")
    try:
        tag, container_id = sandbox.build_with_retry(instance_dir)
        print(f"  Image: {tag}")
        print(f"  Container: {container_id}")

        # Mark success in task.json
        task_json_path = Path(instance_dir) / "task.json"
        if task_json_path.exists():
            task_data = json.loads(task_json_path.read_text())
            task_data["build_status"] = "success"
            task_json_path.write_text(json.dumps(task_data, indent=2))

        # Save container ID for later use
        meta_path = Path(instance_dir) / "container.json"
        meta_path.write_text(json.dumps({"container_id": container_id, "image_tag": tag}))
        print(f"  Container info saved to {meta_path}")

    except BuildFailedError as e:
        print(f"  BUILD FAILED after retries: {e}")
        sys.exit(1)


def cmd_evaluate(args):
    """Run evaluation on a completed instance."""
    instance_dir = args.instance
    run_dir = resolve_run_dir(args)

    # Check build_status — skip failed instances
    task_json_path = Path(instance_dir) / "task.json"
    if task_json_path.exists():
        task_data = json.loads(task_json_path.read_text())
        if task_data.get("build_status") == "failed":
            print(f"Skipping {instance_dir}: build_status is 'failed'")
            return

    # Check if there's a running container
    meta_path = Path(instance_dir) / "container.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        container_id = meta["container_id"]
        sandbox = Sandbox()
        print(f"Evaluating in container {container_id[:12]}...")
        result = evaluate_in_container(instance_dir, container_id, sandbox)
    elif args.workspace:
        print(f"Evaluating workspace {args.workspace}...")
        result = evaluate(instance_dir, args.workspace)
    else:
        print("Error: No container found and no --workspace specified.", file=sys.stderr)
        sys.exit(1)

    print(f"\nResults for {result.instance_id}:")
    print(f"  Passed: {result.passed}")
    print(f"  Score:  {result.score:.2f}")
    if result.details:
        print("  Checks:")
        for check in result.details:
            status = "PASS" if check.get("passed") else "FAIL"
            print(f"    [{status}] {check.get('name', '?')}: {check.get('detail', '')}")

    # Save result to run directory
    out = save_result_to_run(result, instance_dir, run_dir)
    print(f"\n  Result saved to {out / 'result.json'}")


def cmd_destroy(args):
    """Destroy a container for an instance."""
    instance_dir = args.instance
    meta_path = Path(instance_dir) / "container.json"

    if not meta_path.exists():
        print("No container found for this instance.", file=sys.stderr)
        sys.exit(1)

    meta = json.loads(meta_path.read_text())
    container_id = meta["container_id"]

    sandbox = Sandbox()
    print(f"Destroying container {container_id[:12]}...")
    sandbox.destroy(container_id)
    meta_path.unlink()
    print("Done.")


def cmd_cleanup(args):
    """Clean up all skillbench containers."""
    sandbox = Sandbox()
    containers = sandbox.list_containers(all=True)

    if not containers:
        print("No skillbench containers found.")
        return

    print(f"Found {len(containers)} skillbench container(s):")
    for c in containers:
        print(f"  {c['id'][:12]}  {c['name']}  [{c['status']}]  {c['image']}")

    count = sandbox.cleanup_all()
    print(f"\nCleaned up {count} container(s).")

    # Also clean up stale container.json files in instances/
    instances_dir = Path("instances")
    if instances_dir.exists():
        for meta in instances_dir.glob("*/container.json"):
            meta.unlink()
            print(f"  Removed {meta}")


def cmd_all(args):
    """Full pipeline: synthesize + build + evaluate all instances."""
    run_dir = resolve_run_dir(args)
    run_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Synthesize
    print(f"=== Step 1: Synthesize {args.num} instances from {args.skill_dir} ===")
    paths = synthesize_skill(args.skill_dir, args.num, args.output_dir)
    print(f"Generated {len(paths)} instances.\n")

    sandbox = Sandbox()
    summary = RunSummary(run_name=run_dir.name, model="eval-only")

    for instance_path in paths:
        instance_name = Path(instance_path).name
        print(f"=== Processing: {instance_name} ===")

        # Skip instances with failed build_status
        task_json_path = Path(instance_path) / "task.json"
        if task_json_path.exists():
            task_data = json.loads(task_json_path.read_text())
            if task_data.get("build_status") == "failed":
                print(f"  Skipping: build_status is 'failed'")
                print()
                continue

        # Step 2: Build with retry
        try:
            print("  Building (with LLM retry)...")
            tag, container_id = sandbox.build_with_retry(instance_path)

            # Mark success
            if task_json_path.exists():
                task_data = json.loads(task_json_path.read_text())
            else:
                task_data = {}
            task_data["build_status"] = "success"
            task_json_path.write_text(json.dumps(task_data, indent=2))

            # Save container info (ephemeral, in instance dir)
            meta_path = Path(instance_path) / "container.json"
            meta_path.write_text(json.dumps({"container_id": container_id, "image_tag": tag}))

            # Step 3: Evaluate
            print("  Evaluating...")
            result = evaluate_in_container(instance_path, container_id, sandbox)

            status = "PASS" if result.passed else "FAIL"
            print(f"  Result: [{status}] score={result.score:.2f}")

            # Save result to run directory
            save_result_to_run(result, instance_path, run_dir)
            summary.update_from_result(result)

            # Cleanup
            sandbox.destroy(container_id)
            meta_path.unlink(missing_ok=True)

        except Exception as e:
            print(f"  ERROR: {e}")

        print()

    # Save and print summary
    summary.save(str(run_dir / "summary.json"))
    print(f"=== Summary ({run_dir}) ===")
    print(f"Total: {summary.total}  Passed: {summary.passed}  Failed: {summary.failed}  Avg Score: {summary.avg_score:.2f}")


def main():
    parser = argparse.ArgumentParser(description="SkillBench: Skill Task Synthesis + Evaluation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # synthesize
    p_syn = subparsers.add_parser("synthesize", help="Synthesize task instances from a skill")
    p_syn.add_argument("--skill-dir", required=True, help="Path to skill directory")
    p_syn.add_argument("--num", type=int, default=10, help="Number of instances to generate")
    p_syn.add_argument("--output-dir", default="instances", help="Output directory")

    # build
    p_build = subparsers.add_parser("build", help="Build Docker sandbox for an instance")
    p_build.add_argument("--instance", required=True, help="Path to instance directory")

    # evaluate
    p_eval = subparsers.add_parser("evaluate", help="Evaluate a completed instance")
    p_eval.add_argument("--instance", required=True, help="Path to instance directory")
    p_eval.add_argument("--workspace", help="Path to workspace directory (if not using container)")
    p_eval.add_argument("--run-dir", help="Directory to save results (default: results/run_{timestamp})")

    # destroy
    p_destroy = subparsers.add_parser("destroy", help="Destroy container for an instance")
    p_destroy.add_argument("--instance", required=True, help="Path to instance directory")

    # cleanup
    subparsers.add_parser("cleanup", help="Remove all skillbench containers and stale container.json files")

    # all
    p_all = subparsers.add_parser("all", help="Full pipeline: synthesize + build + evaluate")
    p_all.add_argument("--skill-dir", required=True, help="Path to skill directory")
    p_all.add_argument("--num", type=int, default=10, help="Number of instances to generate")
    p_all.add_argument("--output-dir", default="instances", help="Output directory")
    p_all.add_argument("--run-dir", help="Directory to save results (default: results/run_{timestamp})")

    args = parser.parse_args()

    commands = {
        "synthesize": cmd_synthesize,
        "build": cmd_build,
        "evaluate": cmd_evaluate,
        "destroy": cmd_destroy,
        "cleanup": cmd_cleanup,
        "all": cmd_all,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
